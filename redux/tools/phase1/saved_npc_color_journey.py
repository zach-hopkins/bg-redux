"""External normal-loop color characterization: explicit builds/owned serial runs.

No engine edits or fixed original-color assumptions. Each selected case uses
three fresh processes and ordinary saves, not an in-process reload surrogate.
"""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import shutil
import time

import saved_npc_color_fixtures as fixtures
import weapon_query_observer as shared
import weapon_query_validation as evidence

KIND = 'bg-redux-color-journey-host/1'
STAGES = ('create', 'reload-1', 'reload-2')
SCOPE = ('Native created/saved/reloaded NPC color characterization only. Original behavior is unobserved; '
         'no production fix, visual equivalence, replay or hidden-state purity is inferred.')


def sources(project):
    tool=Path(__file__).resolve().parent
    if Path(fixtures.__file__).resolve()!=tool/'saved_npc_color_fixtures.py': raise ValueError('Color fixture helper escaped tool directory')
    shared.required_sources() # includes private_game import identity check
    local=['saved_npc_color_journey.py','saved_npc_color_fixtures.py','weapon_query_observer.py',
           'weapon_query_validation.py','weapon_oracle_fixtures.py','private_game.py',
           'native/phase0_gui_probe_snapshot.cpp','native/phase0_save_probe_snapshot.cpp','native/color_save_after_clock.h']
    phase0=['native/gui_probe.cpp','native/save_probe.cpp','gui/ReduxStart.py','baseline_runner.py','query_side_effects.py',
            'harness.py','save_harness.py','legacy_oracle.py','equipped_defenses.py','script_query_probe.py','probe_ui_resources.py']
    return [tool/p for p in local]+[project/'tools/phase0'/p for p in phase0]


def instrument_gui(raw):
    replacements=[(b'#include "save_probe.cpp"',b'#include "phase0_save_probe_snapshot.cpp"'),
        (b'static Window* WindowIn',b'#include "color_save_after_clock.h"\n\nstatic Window* WindowIn'),
        (b'    const int runningSamples=',b'    if (args["--mode"] != "live-clock" || args["--save-after-clock"] != "1") return 64;\n    const int runningSamples='),
        (b'                        Write(out+"/clock-after.state.json",Snapshot(core->GetGame()));',
         b'                        Write(out+"/clock-after.state.json",Snapshot(core->GetGame()));\n                        ColorSaveAfterClock(out);')]
    for old,new in replacements:
        if raw.count(old)!=1: raise ValueError('Frozen GUI hook anchor missing/ambiguous')
        raw=raw.replace(old,new)
    return raw


def output_manifest(root):
    root=Path(root); rows={}
    # Prune every stage wrapper before walking Windows junctions/shared assets.
    for parent,dirs,files in os.walk(root,followlinks=False):
        for name in list(dirs):
            if name!='private-game': continue
            wrapper=Path(parent)/name;dirs.remove(name)
            for path in wrapper.iterdir():
                if path.is_file() and not path.is_symlink():
                    rows[path.relative_to(root).as_posix()]=dict(bytes=path.stat().st_size,sha256=evidence.sha(path))
        for name in files:
            path=Path(parent)/name
            rows[path.relative_to(root).as_posix()]=dict(bytes=path.stat().st_size,sha256=evidence.sha(path))
    return dict(sorted(rows.items()))


def check_sources(receipt,project):
    if set(receipt.get('sources',{}))!={str(p) for p in sources(project)}: raise ValueError('Color host required source closure differs')
    for name,row in receipt['sources'].items():
        if evidence.sha(name)!=row['sha256'] or evidence.sha(row['frozen'])!=row['sha256']:
            raise ValueError('Color host source/frozen input changed: '+name)


def finish_guards(result,out,project,source,build,api,before,candidate):
    if before is not None:
        after=api.baseline_runner.protected(project);shared.write(out/'phase0-after.json',after)
        result['phase0_preservation']={k:before[k]==after[k] for k in before}
        if not all(result['phase0_preservation'].values()): raise ValueError('Phase0 protected inventory changed')
    if candidate is not None:
        after=shared.candidate_inventory(source,build);shared.write(out/'candidate-after.json',after)
        result['candidate_preserved']=candidate==after
        if not result['candidate_preserved']: raise ValueError('Candidate source/headers/binaries changed')


def build_host(args):
    project,source,build=args.project_root.resolve(),args.engine_source_root.resolve(),args.engine_build_root.resolve()
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=False)
    result=dict(schema=KIND,verdict='failed',project=str(project),source=str(source),build=str(build))
    before=candidate=None
    try:
        api=shared.phase0(project);result['phase0_preflight']=api.baseline_runner.preflight(project)
        before=api.baseline_runner.protected(project);shared.write(out/'phase0-before.json',before)
        candidate=shared.candidate_inventory(source,build);shared.write(out/'candidate-before.json',candidate)
        tool=Path(__file__).resolve().parent
        for copy,original in [('phase0_gui_probe_snapshot.cpp','gui_probe.cpp'),('phase0_save_probe_snapshot.cpp','save_probe.cpp')]:
            if evidence.sha(tool/'native'/copy)!=evidence.sha(project/'tools/phase0/native'/original):
                raise ValueError('Frozen Phase0 host/serializer differs from origin')
        result['sources']={str(p):shared.frozen_copy(p,out/'sources'/evidence.sha(p)/p.name) for p in sources(project)}
        compiled=out/'compiled-sources';compiled.mkdir()
        generated=compiled/'color_gui_probe.cpp'
        generated.write_bytes(instrument_gui((tool/'native/phase0_gui_probe_snapshot.cpp').read_bytes()))
        for name in ('phase0_save_probe_snapshot.cpp','color_save_after_clock.h'):
            shared.frozen_copy(tool/'native'/name,compiled/name)
        result['compiled_sources']=evidence.manifest(compiled)
        prefix=project/'phase0-local/toolchain/msys64/ucrt64';compiler=prefix/'bin/g++.exe';binary=out/'Redux_color_gui.exe'
        command=[str(compiler),'-std=gnu++17','-g','-O0','-DHAVE_CONFIG_H','-DUSE_OPENGL_API','-D_USE_MATH_DEFINES',
                 '-DFMT_HEADER_ONLY','-DFMT_USE_CONSTEVAL=0','-DFMT_EXCEPTIONS=0','-DFMT_UNICODE=1','-fno-strict-aliasing']
        for path in [build,source/'gemrb/includes',source/'gemrb/core',source/'platforms/Windows',build/'gemrb/includes',
                     prefix/'include/SDL2',prefix/'include/python3.14',source/'includes/fmt']:
            command+=['-I',str(path)]
        command += [str(generated),str(build/'gemrb/core/libgemrb_core.dll.a'),str(prefix/'lib/libiconv.dll.a'),'-lshlwapi','-o',str(binary)]
        env=os.environ.copy();env['PATH']=str(prefix/'bin')+os.pathsep+env.get('PATH','')
        result['process']=api.baseline_runner.execute(command,build,env,out/'build.log',args.timeout)
        shared.require_process(result['process'])
        result.update(binary=str(binary),binary_sha256=evidence.sha(binary),compiler=str(compiler),compiler_sha256=evidence.sha(compiler),
                      candidate_inventory=candidate,command=command,verdict='built-not-executed')
        check_sources(result,project)
    except Exception as error: result.update(verdict='failed',error=str(error))
    finally:
        try: finish_guards(result,out,project,source,build,api,before,candidate)
        except Exception as error: result.update(verdict='failed',preservation_error=str(error))
        shared.write(out/'build.json',result);shared.write(out/'artifact-manifest.json',dict(files=output_manifest(out)))
    print(out/'build.json',result['verdict'],flush=True)
    return 0 if result['verdict']=='built-not-executed' else 1


def check_build(path,project,source,build):
    receipt=evidence.read(path)
    if (receipt.get('schema')!=KIND or receipt.get('verdict')!='built-not-executed'
            or [Path(receipt[k]).resolve() for k in ('project','source','build')]!=[project,source,build]
            or receipt.get('phase0_preservation')!=dict(source=True,binaries=True,fixture=True)
            or receipt.get('candidate_preserved')is not True): raise ValueError('Color build receipt failed or wrong roots')
    shared.require_process(receipt['process']);check_sources(receipt,project)
    if evidence.sha(receipt['binary'])!=receipt['binary_sha256'] or evidence.sha(receipt['compiler'])!=receipt['compiler_sha256']:
        raise ValueError('Color driver/compiler drift')
    if shared.candidate_inventory(source,build)!=receipt['candidate_inventory']: raise ValueError('Color host candidate drift')
    compiled=Path(path).parent/'compiled-sources'
    if evidence.manifest(compiled)!=receipt['compiled_sources']: raise ValueError('Generated color host source drift')
    expected=instrument_gui((Path(__file__).parent/'native/phase0_gui_probe_snapshot.cpp').read_bytes())
    if (compiled/'color_gui_probe.cpp').read_bytes()!=expected: raise ValueError('Generated GUI hook differs')
    return receipt


def wire_count(sav):
    areas=[r for r in fixtures.sav_records(sav) if r['name'].casefold()=='ar0602.are']
    if len(areas)!=1: raise ValueError('Color area absent/ambiguous')
    area=fixtures.inflate(areas[0])
    if fixtures.block(area,0,8)!=b'AREAV1.0': raise ValueError('Expected AREAV1.0')
    at,count=fixtures.u32(area,0x54),fixtures.u16(area,0x58)
    if count>1000 or at<0x11c: raise ValueError('Invalid color actor table')
    fixtures.block(area,at,count*272);found=0
    for i in range(count):
        row=at+i*272
        if fixtures.u32(area,row+40)&1: continue
        cre=fixtures.block(area,fixtures.u32(area,row+136),fixtures.u32(area,row+140));fixtures.validate_cre(cre)
        found+=fixtures.block(cre,0x280,32).split(b'\0')[0].lower()==b'rdxcolor'
    return found


def save_manifest(folder):
    rows=fixtures.manifest(folder); names={n.casefold() for n in rows}
    required={'baldur.gam','baldur.sav','baldur.bmp','portrt0.bmp','portrt1.bmp'}
    if len(names)!=len(rows) or not required<=names or names-required not in (set(),{'save_000000033-gemrb.cloud.meta'}) or any(r['bytes']==0 for r in rows.values()):
        raise ValueError('Exact ordinary save file inventory differs')
    return rows


def member(folder,ext):
    names=[p for p in Path(folder).iterdir() if p.name.casefold()=='baldur.'+ext]
    if len(names)!=1: raise ValueError('Save member absent/ambiguous')
    return names[0]


def npc(state,row,required=True,ready=True):
    evidence.require_state(state)
    actors=[a for a in state['current_area_actors'] if a['script_name'].casefold()=='rdxcolor']
    if any(a['script_name'].casefold()=='rdxcolor' for group in ('party','stored_npcs') for a in state[group]):
        raise ValueError('Color NPC is in an unexpected actor collection')
    if not actors and not required: return None
    if len(actors)!=1: raise ValueError('Exactly one runtime color NPC required')
    globals_={k.upper():v for k,v in state['globals'].items()}
    if ready and any(type(globals_.get(k))is not int or globals_[k]!=v for k,v in row['expected_ready_globals'].items()):
        raise ValueError('Color case/nonce/stage/readiness differs')
    a=actors[0]
    if len(a['base_stats'])<=212 or len(a['modified_stats'])<=212: raise ValueError('Color stats absent')
    if (type(a['runtime_id'])is not int or a['runtime_id']<=0
            or any(type(a[k][212])is not int or not 0<=a[k][212]<=0xffffffff for k in ('base_stats','modified_stats'))
            or a['base_stats'][205]!=0x6100 or a['base_stats'][231]!=1 or a['base_stats'][234]!=128):
        raise ValueError('Runtime color NPC palette/race/allegiance/stat guard differs')
    if any(x['runtime_id']==a['runtime_id'] for group in ('party','stored_npcs') for x in state[group]):
        raise ValueError('Color NPC runtime identity overlaps another actor')
    return dict(runtime_id=a['runtime_id'],identity=a['script_name'],position=a['position'],
                base_color212=a['base_stats'][212],modified_color212=a['modified_stats'][212],
                base_leather_byte=a['base_stats'][212]&255,modified_leather_byte=a['modified_stats'][212]&255,
                effects=len(a['effects']),effect_records=a['effects'],inventory=a['inventory'])


def validate_stage(folder,row,running,reload,started_ns=None):
    folder=Path(folder)
    names=['clock-before.state.json','clock-after.state.json','clock-samples.json','gui-result.json',
           'color-before-save.state.json','color-after-save.state.json','color-save-result.json']
    data={name:evidence.read(folder/name) for name in names}
    if started_ns is not None and any((folder/n).stat().st_mtime_ns<started_ns for n in names): raise ValueError('Stale color host evidence')
    clock=data['clock-samples.json'];samples=clock['samples'];expected=['paused-initial']*5+['running']*running+['paused-final']*4
    if (clock.get('schema')!='bg-redux-live-clock/1' or type(clock.get('ticks_per_second'))is not int or clock['ticks_per_second']<=0
            or len(samples)!=running+9 or any(type(s.get('sample'))is not int for s in samples)
            or [s.get('sample') for s in samples]!=list(range(running+9)) or [s.get('phase') for s in samples]!=expected):
        raise ValueError('Color clock coverage/phases incomplete')
    for key in ('game_time','elapsed_ms'):
        values=[s.get(key) for s in samples]
        if any(type(v)is not int for v in values) or values!=sorted(values): raise ValueError('Color clock monotonicity/type differs')
    if len({s['game_time'] for s in samples[:5]})!=1 or len({s['game_time'] for s in samples[-4:]})!=1 or samples[running+4]['game_time']<=samples[4]['game_time']:
        raise ValueError('Color pause/progression not observed')
    before,after=data[names[0]],data[names[1]]
    if before['game_time']!=samples[0]['game_time'] or after['game_time']!=samples[-1]['game_time']: raise ValueError('Color snapshot clock boundary differs')
    native=data['gui-result.json'];events=['ReduxStart.PopulateLoad','press:load.baseline-row','ReduxStart.Ready','clock:resume','clock:pause']
    if native.get('completed')is not True or native.get('steps')!=running+9 or native.get('events')!=events: raise ValueError('Normal-loop color host incomplete')
    saved=data['color-save-result.json']
    if (saved.get('schema')!='bg-redux-color-save-native/1' or type(saved.get('save_return_code'))is not int
            or saved['save_return_code']!=0 or saved.get('forced')is not False or len(saved.get('directories',[]))!=1):
        raise ValueError('Ordinary color save failed/forced/ambiguous')
    post_save=npc(data['color-after-save.state.json'],row)
    post_clock=npc(after,row);pre_save=npc(data['color-before-save.state.json'],row)
    if data['color-before-save.state.json']!=after: raise ValueError('Clock/save state continuity differs')
    first=npc(before,row,required=reload,ready=reload)
    ids=[x['runtime_id'] for x in (first,post_clock,pre_save,post_save) if x is not None]
    if len(set(ids))!=1: raise ValueError('Color NPC runtime identity changed within process')
    return dict(before=first,after_clock=post_clock,before_save=pre_save,after_save=post_save,
                save_changes=evidence.diff(data['color-before-save.state.json'],data['color-after-save.state.json']),
                samples=len(samples),running_samples=running,ticks_per_second=clock['ticks_per_second'],
                game_time_before=before['game_time'],game_time_after=after['game_time'],
                output_save=saved['directories'][0],save_return_code=0,forced=False)


def preparation(path,selected,api=None):
    prep=evidence.read(path)
    if (prep.get('schema')!='bg-redux-phase1-color-preparation/1' or prep.get('phase')!='prepared-not-executed'
            or prep.get('executed')is not False or prep.get('source_unchanged')is not True
            or prep.get('original_behavior_observed')is not False): raise ValueError('Color preparation failed/executed/changed')
    if prep['generator_sha256']!=evidence.sha(Path(fixtures.__file__)): raise ValueError('Color generator source drift')
    ids=[r['id'] for r in prep['cases']]
    if ids!=[r[0] for r in fixtures.CASES] or selected and (len(selected)!=len(set(selected)) or set(selected)-set(ids)):
        raise ValueError('Color selected case identity differs')
    rows=[r for r in prep['cases'] if not selected or r['id'] in selected]
    for row in rows:
        number=ids.index(row['id'])+1; _,color,controlled=fixtures.CASES[number-1]
        if row['nonce']!=prep['nonce'] or row['save_or_reload_executed']is not False or row['fresh_creation_required']is not True:
            raise ValueError('Color input nonce/execution identity differs')
        expected=dict(RDXCCASE=number,RDXCNONCE=prep['nonce'],RDXCSTAGE=2,RDXCREADY=1)
        if (type(row['number'])is not int or row['number']!=number or row['expected_ready_globals']!=expected
                or any(type(v)is not int for v in row['expected_ready_globals'].values()) or row['resource']!='RDXCOLOR'
                or row['npc_script_name']!='RDXCOLOR' or row['raw_leather_color']!=color or row['controlled_randcolr']is not controlled):
            raise ValueError('Declared color case controls differ')
        if save_manifest(row['fixture'])!=row['fixture_files'] or fixtures.manifest(row['override'])!=row['override_files']:
            raise ValueError('Color fixture/override drift')
        override=Path(row['override']);required={'rdxcolor.cre','randcolr.2da',row['script'].casefold()+'.bcs'}
        if {n.casefold() for n in row['override_files']}!=required or len(row['override_files'])!=3:
            raise ValueError('Color override inventory differs')
        cre=(override/'RDXCOLOR.cre').read_bytes()
        if cre!=fixtures.inert_cre(cre,color) or cre[0x30]!=color: raise ValueError('Color resource is not declared inert input')
        table=(override/'RANDCOLR.2da').read_bytes();_,_,values=fixtures.parse_table(table)
        expected_hash=prep['table_control']['override_sha256' if controlled else 'source_sha256']
        if fixtures.digest(table)!=expected_hash: raise ValueError('Color table binding differs')
        if controlled and any(row_[values[0].index(228)]!=237 or row_[values[0].index(237)]!=46 for row_ in values[1:]):
            raise ValueError('Deterministic color column outcomes differ')
        if api is not None and (override/(row['script']+'.bcs')).read_bytes()!=fixtures.script(api,number,row['nonce'],row['spawn_position']):
            raise ValueError('Fresh creation script differs')
        if wire_count(member(row['fixture'],'sav').read_bytes())!=0: raise ValueError('Initial input already embeds RDXCOLOR')
    return prep,rows


def run(args):
    project,source,build=args.project_root.resolve(),args.engine_source_root.resolve(),args.engine_build_root.resolve()
    out=shared.new_output(args.results_root.resolve(),'native-color-journey')
    result=dict(schema='bg-redux-phase1-native-color-journey/1',directory=str(out),verdict='failed',execution='not-run',
                original_behavior_observed=False,scope=SCOPE,cases=[])
    before=candidate=receipt=None
    try:
        api=shared.phase0(project);result['phase0_preflight']=api.baseline_runner.preflight(project)
        before=api.baseline_runner.protected(project);shared.write(out/'phase0-before.json',before)
        candidate=shared.candidate_inventory(source,build);shared.write(out/'candidate-before.json',candidate)
        receipt=check_build(args.build_receipt.resolve(),project,source,build)
        prep,rows=preparation(args.preparation,args.cases,api)
        result.update(selected_cases=[r['id'] for r in rows],unselected_cases=[r['id'] for r in prep['cases'] if r not in rows],
                      declared_stages=list(STAGES),process_budget_seconds_per_case=3*args.timeout,running_samples=args.running_samples)
        result['preparation_sha256']=evidence.sha(args.preparation);shared.frozen_copy(args.preparation,out/'preparation.json')
        driver=out/'driver';driver.mkdir();binary=driver/Path(receipt['binary']).name
        shared.frozen_copy(Path(receipt['binary']),binary);shared.frozen_copy(args.build_receipt,driver/'build.json')
        for name,row in receipt['sources'].items(): shared.frozen_copy(Path(row['frozen']),driver/'sources'/row['sha256']/Path(name).name)
        startup=driver/'startup';startup.mkdir();shared.frozen_copy(project/'tools/phase0/gui/ReduxStart.py',startup/'ReduxStart.py')
        for row in rows:
            case=dict(id=row['id'],nonce=row['nonce'],verdict='failed',stages=[]);result['cases'].append(case)
            case_out=out/row['id'];case_out.mkdir();incoming=Path(row['fixture']);frozen_saves=[]
            try:
                override=case_out/'override';shutil.copytree(row['override'],override)
                for index,name in enumerate(STAGES):
                    stage=case_out/name;stage.mkdir();entry=dict(id=name,execution='not-run');case['stages'].append(entry)
                    private=None
                    try:
                        if fixtures.manifest(override)!=row['override_files']: raise ValueError('Private color override drift')
                        if fixtures.manifest(row['override'])!=row['override_files']: raise ValueError('Source color override drift')
                        input_files=save_manifest(incoming);count=wire_count(member(incoming,'sav').read_bytes())
                        if count!=(1 if index else 0): raise ValueError('Color input presence/count violates fresh/reload boundary')
                        entry['input_files']=input_files
                        entry['input_wire_observation']=fixtures.inspect_npc_wire(member(incoming,'sav').read_bytes()) if index else None
                        profile=stage/'profile';copied=profile/'save/000000007-HarnessInput';shutil.copytree(incoming,copied)
                        if save_manifest(copied)!=input_files: raise ValueError('Color copied input differs')
                        private=shared.prepare_private_game(project,stage)
                        for directory in ('cache','capture'): (stage/directory).mkdir()
                        config=dict(GameType='bg2ee',GamePath=private['game'],GemRBPath=source/'gemrb',PluginsPath=build/'gemrb/plugins',
                            CachePath=stage/'cache',SavePath=profile,ModPath=override,UseAsLibrary=0,SaveAsOriginal=1,
                            Width=1024,Height=768,FullScreen=0,CapFPS=30,AudioDriver='none',GameLanguagePath='lang/en_US',
                            SkipIntroVideos=1,Logging=1,LogColor=0,PathfinderThreadsCount=0,PathfinderMainThreadMode='immediate')
                        cfg=stage/'probe.cfg';cfg.write_text(''.join(f'{k}={str(v).replace(chr(92),chr(47))}\n' for k,v in config.items()),encoding='utf-8')
                        entry['config_sha256']=evidence.sha(cfg)
                        command=[str(binary),'--config',str(cfg),'--output',str(stage/'capture'),'--scripts',str(startup),
                                 '--mode','live-clock','--clock-running-samples',str(args.running_samples),'--save-after-clock','1']
                        env=api.harness.environment(stage);prefix=project/'phase0-local/toolchain/msys64/ucrt64'
                        env['PATH']=os.pathsep.join([str(build/'gemrb'),str(prefix/'bin'),env.get('PATH','')]);env['PYTHONDONTWRITEBYTECODE']='1'
                        check_sources(receipt,project);shared.validate_private_game(private,stage)
                        started=time.time_ns();entry['process']=api.baseline_runner.execute(command,build,env,stage/'process.log',args.timeout)
                        entry['execution']='passed' if entry['process'].get('exit_code')==0 and entry['process'].get('timed_out')is False else 'failed'
                        if (stage/'capture/color-save-result.json').is_file():
                            entry['native_save_receipt']=evidence.read(stage/'capture/color-save-result.json')
                        shared.require_process(entry['process'])
                        if 'Traceback (most recent call last)' in (stage/'process.log').read_text(encoding='utf-8',errors='replace'):
                            raise ValueError('Native color Python callback traceback')
                        observed=validate_stage(stage/'capture',row,args.running_samples,bool(index),started)
                        entry['observation']=observed
                        saved=Path(observed['output_save']).resolve()
                        if not saved.is_relative_to((profile/'save').resolve()) or saved==copied.resolve(): raise ValueError('Color save output escaped owned profile or overwrote input')
                        output_files=save_manifest(saved);frozen=stage/'frozen-save';shutil.copytree(saved,frozen)
                        if save_manifest(frozen)!=output_files or wire_count(member(frozen,'sav').read_bytes())!=1:
                            raise ValueError('Frozen color save differs or NPC absent/duplicated')
                        wire=fixtures.inspect_npc_wire(member(frozen,'sav').read_bytes())
                        globals_={k.upper():v for k,v in api.legacy_oracle.read_wire(member(frozen,'gam'))['globals'].items()}
                        if any(type(globals_.get(k))is not int or globals_[k]!=v for k,v in row['expected_ready_globals'].items()):
                            raise ValueError('Persisted color case/nonce/readiness differs')
                        entry.update(wire_observation=wire,frozen_save=str(frozen),frozen_save_files=output_files)
                        if save_manifest(copied)!=input_files or save_manifest(incoming)!=input_files or evidence.sha(cfg)!=entry['config_sha256']:
                            raise ValueError('Color immutable input/config changed')
                        frozen_saves.extend([(frozen,output_files),(saved,output_files)]);incoming=frozen
                    finally:
                        if private is not None: entry['private_game_validation']=shared.validate_private_game(private,stage)
                case['verdict']='native-color-journey-characterized'
            except Exception as error: case['error']=str(error)
            case['actual_sequence']=[dict(stage=s['id'],base=s['observation']['after_clock']['base_color212'],
                modified=s['observation']['after_clock']['modified_color212'],wire=s['wire_observation']['leather_wire_byte'])
                for s in case['stages'] if 'observation'in s and 'wire_observation'in s]
            case['fresh_reload_color_differences']=[]
            for prior,current in zip(case['stages'],case['stages'][1:]):
                if 'observation'not in prior or 'observation'not in current:continue
                previous=prior['observation']['after_save'];loaded=current['observation']['before']
                for key in ('base_color212','modified_color212'):
                    if previous[key]!=loaded[key]:
                        case['fresh_reload_color_differences'].append(dict(stage=current['id'],field=key,
                            before=previous[key],after=loaded[key],classification='observed native difference; original expectation unobserved'))
            for frozen,pins in frozen_saves:
                if save_manifest(frozen)!=pins: case.update(verdict='failed',error='Previous frozen save changed')
            shared.write(case_out/'result.json',case);shared.write(out/'result.json',result)
        result['execution']='passed' if all(len(c['stages'])==3 and all(s['execution']=='passed' for s in c['stages']) for c in result['cases']) else 'failed'
        if result['cases'] and all(c['verdict']=='native-color-journey-characterized' for c in result['cases']):
            result['verdict']='native-color-journeys-characterized'
    except Exception as error: result['error']=str(error)
    finally:
        try:
            finish_guards(result,out,project,source,build,api,before,candidate)
            if receipt is not None: check_sources(receipt,project)
            if 'preparation_sha256'in result:
                if evidence.sha(args.preparation)!=result['preparation_sha256']: raise ValueError('Source color preparation changed')
                preparation(args.preparation,args.cases,api)
                result['preparation_and_inputs_preserved']=True
        except Exception as error: result.update(verdict='failed',preservation_error=str(error))
        shared.write(out/'result.json',result);shared.write(out/'artifact-manifest.json',dict(files=output_manifest(out),scope='Owned outputs/root copies; linked assets excluded'))
    print(out,result['verdict'],flush=True)
    return 0 if result['verdict']=='native-color-journeys-characterized' else 1


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    for mode in ('build','run'):
        item=sub.add_parser(mode)
        for name in ('project-root','engine-source-root','engine-build-root'):item.add_argument('--'+name,type=Path,required=True)
        item.add_argument('--timeout',type=float,default=240 if mode=='build' else 90)
        if mode=='build':item.add_argument('--output-dir',type=Path,required=True)
        else:
            for name in ('build-receipt','preparation','results-root'):item.add_argument('--'+name,type=Path,required=True)
            item.add_argument('--cases',nargs='+',choices=[c[0] for c in fixtures.CASES]);item.add_argument('--running-samples',type=int,default=40)
    args=parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout<=0 or args.mode=='run' and (args.timeout>90 or not 8<=args.running_samples<=80):
        parser.error('Positive finite timeout; runs <=90 seconds each with 8..80 running samples')
    return build_host(args) if args.mode=='build' else run(args)


if __name__=='__main__': raise SystemExit(main())
