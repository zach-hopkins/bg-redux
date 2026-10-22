"""Bounded external stock-container callback journey; never edits engine/game assets."""
from __future__ import annotations
import argparse
from collections import Counter
import os
from pathlib import Path
import re
import shutil
import struct
import time

import saved_npc_color_journey as common
import saved_npc_color_fixtures as binary
import weapon_query_observer as shared
import weapon_query_validation as evidence

KIND='bg-redux-container-loot-host/1'
TARGET='Jailkeep Table'
EXPECTED=['SW1H04','SW1H07','STAF01','BLUN04','AX1H01','SPER01','HALB01','MISC4B','HAMM01','SW2H01','SW1H43']
SCOPE='Actor UseContainer plus shipped GUI callback dispatch; no OS pointer input or original parity observed.'

def sources(project,source):
    tool=Path(__file__).resolve().parent
    return common.sources(project)+[Path(__file__),tool/'native/loot_gui_probe_snapshot.cpp',tool/'native/loot_save_probe_snapshot.cpp',tool/'native/loot_journey.h']+[source/p for p in ['gemrb/GUIScripts/Container.py','gemrb/GUIScripts/GUICommon.py','gemrb/core/GUI/GameControl.cpp','gemrb/core/GameScript/Actions.cpp','gemrb/core/Scriptable/Actor.cpp','gemrb/core/Inventory.h','gemrb/plugins/GUIScript/GUIScript.cpp']]

def instrument(raw):
    changes=[(b'#include "save_probe.cpp"',b'#include "loot_save_probe_snapshot.cpp"'),
      (b'static Window* WindowIn',b'#include "loot_journey.h"\n\nstatic Window* WindowIn'),
      (b'    const int runningSamples=',b'    if (args["--mode"]!="live-clock" || (args["--journey"]!="take" && args["--journey"]!="reload")) return 64;\n    const int runningSamples='),
      (b'                    const int endRunning=4+runningSamples;',b'                    const int endRunning=4+runningSamples;\n                    LootTick(out,index);'),
      (b'                        Write(out+"/clock-after.state.json",Snapshot(core->GetGame()));',b'                        Write(out+"/clock-after.state.json",Snapshot(core->GetGame()));\n                        LootFinish(out);'),
      (b'                        clockStart=GetMilliseconds();sampleClock(0,"paused-initial");',b'                        LootStart(out,args["--journey"]=="reload");\n                        clockStart=GetMilliseconds();sampleClock(0,"paused-initial");')]
    for old,new in changes:
        if raw.count(old)!=1:raise ValueError('Frozen loot host anchor absent/ambiguous')
        raw=raw.replace(old,new)
    return raw

def check_sources(receipt,project,source):
    if set(receipt['sources'])!={str(p) for p in sources(project,source)}:raise ValueError('Loot source closure differs')
    for name,row in receipt['sources'].items():
        if evidence.sha(name)!=row['sha256'] or evidence.sha(row['frozen'])!=row['sha256']:raise ValueError('Loot source/frozen drift: '+name)

def build_host(args):
    project,source,build=args.project_root.resolve(),args.engine_source_root.resolve(),args.engine_build_root.resolve()
    out=args.output_dir.resolve()
    if not out.is_relative_to(project/'phase1-local') or out.is_relative_to(source) or out.is_relative_to(build):raise ValueError('External loot build must use a separate private Phase1 folder')
    if not 1<=args.timeout<=300:raise ValueError('External loot compile timeout must be bounded')
    out.mkdir(parents=True,exist_ok=False)
    result=dict(schema=KIND,verdict='failed',project=str(project),source=str(source),build=str(build));before=candidate=None;api=None
    try:
        api=shared.phase0(project);result['phase0_preflight']=api.baseline_runner.preflight(project)
        before=api.baseline_runner.protected(project);shared.write(out/'phase0-before.json',before)
        candidate=shared.candidate_inventory(source,build);shared.write(out/'candidate-before.json',candidate)
        tool=Path(__file__).resolve().parent
        for copy,origin in [('loot_gui_probe_snapshot.cpp','gui_probe.cpp'),('loot_save_probe_snapshot.cpp','save_probe.cpp')]:
            if evidence.sha(tool/'native'/copy)!=evidence.sha(project/'tools/phase0/native'/origin):raise ValueError('Loot frozen host/serializer differs from Phase0')
        result['sources']={str(p):shared.frozen_copy(p,out/'sources'/evidence.sha(p)/p.name) for p in sources(project,source)}
        compiled=out/'compiled-sources';compiled.mkdir();generated=compiled/'loot_gui_probe.cpp'
        generated.write_bytes(instrument((tool/'native/loot_gui_probe_snapshot.cpp').read_bytes()))
        for name in ('loot_save_probe_snapshot.cpp','loot_journey.h'):shared.frozen_copy(tool/'native'/name,compiled/name)
        result['compiled_sources']=evidence.manifest(compiled)
        prefix=project/'phase0-local/toolchain/msys64/ucrt64';compiler=prefix/'bin/g++.exe';host=out/'Redux_loot_gui.exe'
        command=[str(compiler),'-std=gnu++17','-g','-O0','-DHAVE_CONFIG_H','-DUSE_OPENGL_API','-D_USE_MATH_DEFINES','-DFMT_HEADER_ONLY','-DFMT_USE_CONSTEVAL=0','-DFMT_EXCEPTIONS=0','-DFMT_UNICODE=1','-fno-strict-aliasing']
        for path in [build,source/'gemrb/includes',source/'gemrb/core',source/'platforms/Windows',build/'gemrb/includes',prefix/'include/SDL2',prefix/'include/python3.14',source/'includes/fmt']:command+=['-I',str(path)]
        command += [str(generated),str(build/'gemrb/core/libgemrb_core.dll.a'),str(prefix/'lib/libiconv.dll.a'),'-lshlwapi','-o',str(host)]
        env=os.environ.copy();env['PATH']=str(prefix/'bin')+os.pathsep+env.get('PATH','')
        result['process']=api.baseline_runner.execute(command,build,env,out/'build.log',args.timeout);shared.require_process(result['process'])
        result.update(binary=str(host),binary_sha256=evidence.sha(host),compiler=str(compiler),compiler_sha256=evidence.sha(compiler),candidate_inventory=candidate,command=command,verdict='built-not-executed')
        check_sources(result,project,source)
    except Exception as error:result['error']=str(error);result['verdict']='failed'
    finally:
        try:common.finish_guards(result,out,project,source,build,api,before,candidate)
        except Exception as error:result.update(verdict='failed',preservation_error=str(error))
        shared.write(out/'build.json',result);shared.write(out/'artifact-manifest.json',dict(files=common.output_manifest(out)))
    print(out/'build.json',result['verdict'],flush=True)
    return 0 if result['verdict']=='built-not-executed' else 1

def check_build(path,project,source,build):
    receipt=evidence.read(path)
    if receipt.get('schema')!=KIND or receipt.get('verdict')!='built-not-executed' or [Path(receipt[k]).resolve() for k in ('project','source','build')]!=[project,source,build]:raise ValueError('Wrong/failed loot host build')
    if receipt.get('phase0_preservation')!=dict(source=True,binaries=True,fixture=True) or receipt.get('candidate_preserved')is not True:raise ValueError('Loot build preservation failed')
    shared.require_process(receipt['process']);check_sources(receipt,project,source)
    if evidence.sha(receipt['binary'])!=receipt['binary_sha256'] or evidence.sha(receipt['compiler'])!=receipt['compiler_sha256']:raise ValueError('Loot host/compiler drift')
    if shared.candidate_inventory(source,build)!=receipt['candidate_inventory']:raise ValueError('Loot build candidate mismatch')
    compiled=Path(path).parent/'compiled-sources'
    if evidence.manifest(compiled)!=receipt['compiled_sources'] or (compiled/'loot_gui_probe.cpp').read_bytes()!=instrument((Path(__file__).parent/'native/loot_gui_probe_snapshot.cpp').read_bytes()):raise ValueError('Loot compiled source drift')
    return receipt

def container_wire(sav):
    records=[r for r in binary.sav_records(sav) if r['name'].casefold()=='ar0602.are']
    if len(records)!=1:raise ValueError('Exactly one AR0602 required')
    area=binary.inflate(records[0])
    if binary.block(area,0,8)!=b'AREAV1.0':raise ValueError('ARE V1.0 required')
    start,count,items,nitems=binary.u32(area,0x70),binary.u16(area,0x74),binary.u32(area,0x78),binary.u16(area,0x76)
    if count>1000 or nitems>10000 or start<0x11c or (nitems and items<0x11c):raise ValueError('ARE container/item bounds differ')
    binary.block(area,start,count*192);binary.block(area,items,nitems*20)
    if nitems and start<items+nitems*20 and items<start+count*192:raise ValueError('Overlapping ARE container/item tables')
    found=[]
    for i in range(count):
        at=start+i*192;name=binary.block(area,at,32).split(b'\0')[0].decode('ascii')
        first,length=binary.u32(area,at+64),binary.u32(area,at+68)
        if first>nitems or length>nitems-first:raise ValueError('Container item slice exceeds table')
        if name.casefold()!=TARGET.casefold():continue
        rows=[]
        for j in range(length):
            raw=binary.block(area,items+(first+j)*20,20)
            rows.append(dict(resref=raw[:8].split(b'\0')[0].decode('ascii').upper(),expired=struct.unpack_from('<H',raw,8)[0],usages=list(struct.unpack_from('<HHH',raw,10)),flags=struct.unpack_from('<I',raw,16)[0]))
        found.append(dict(container=name,position=list(struct.unpack_from('<HH',area,at+32)),type=binary.u16(area,at+36),flags=binary.u32(area,at+40),trapped=binary.u16(area,at+48),items=rows))
    if len(found)!=1:raise ValueError('Required stock table absent/ambiguous')
    target=found[0]
    if target['position']!=[3109,2829] or target['type']!=5 or target['flags']!=0 or target['trapped']!=0:raise ValueError('Required safe stock table guard differs')
    return target

def item_key(item,flags=True):
    if not re.fullmatch(r'[A-Za-z0-9_]{1,8}',item.get('resref','')) or type(item.get('expired'))is not int or not 0<=item['expired']<=65535 or type(item.get('flags'))is not int or not 0<=item['flags']<=0xffffffff or len(item.get('usages',[]))!=3 or any(type(x)is not int or not 0<=x<=65535 for x in item['usages']):raise ValueError('Invalid item evidence')
    return (item['resref'].upper(),item['expired'],tuple(item['usages']))+((item['flags']&~0x10,) if flags else ())

def inventory(items,flags=True):return Counter(item_key(x,flags) for x in items)
def raw_items(inv):
    items=inv['items']
    if type(inv.get('slot_count'))is not int or not 0<=inv['slot_count']<=10000 or any(type(x.get('slot'))is not int or not 0<=x['slot']<inv['slot_count'] for x in items) or len({x['slot'] for x in items})!=len(items):raise ValueError('Duplicate/invalid runtime inventory slot')
    return items
def actual_items(inv):
    items=raw_items(inv)
    return [x for x in items if x['slot']!=inv['fist_slot']]

def outcome(before,after,reload=False):
    for state in (before,after):
        if state.get('container_script_name','').casefold()!='jailkeeptable':raise ValueError('Normalized runtime container script name differs')
        if state.get('schema')!='bg-redux-container-loot-state/1' or state.get('container','').casefold()!=TARGET.casefold() or state.get('position')!=[3109,2829] or state.get('type')!=5 or state.get('flags')!=0 or state.get('trapped')!=0 or type(state.get('pc_runtime_id'))is not int or state['pc_runtime_id']<=0 or type(state.get('container_runtime_id'))is not int or state['container_runtime_id']<=0:raise ValueError('Runtime target guard differs')
    if before['pc_runtime_id']!=after['pc_runtime_id'] or before['container_runtime_id']!=after['container_runtime_id']:raise ValueError('Leader/container identity changed within process')
    cb=raw_items(before['container_inventory']);ca=raw_items(after['container_inventory']);pb=actual_items(before['pc_inventory']);pa=actual_items(after['pc_inventory'])
    if reload:
        if inventory(cb)!=inventory(ca) or inventory(pb)!=inventory(pa):raise ValueError('Reload inspection changed inventory')
    else:
        transferred=[x for x in cb if x['resref'].upper()=='SW1H04']
        if len(transferred)!=1 or any(x['resref'].upper()=='SW1H04' for x in pb):raise ValueError('Initial exact transfer precondition differs')
        moved=inventory(transferred)
        if inventory(ca)+moved!=inventory(cb) or inventory(pb)+moved!=inventory(pa):raise ValueError('Conserved stock callback transfer not observed')
    if any(x['resref'].upper()=='SW1H04' for x in ca) or sum(x['resref'].upper()=='SW1H04' for x in pa)!=1:raise ValueError('Final item ownership differs')
    return dict(container_before=len(cb),container_after=len(ca),pc_before=len(pb),pc_after=len(pa),item='SW1H04',acquired_flag_mask_only='0x10',flags_scope='Raw flags retained; only source-grounded transient acquired bit is masked within transfer/reload comparisons.')

def validate_capture(folder,running,reload,action_id,started_ns=None):
    folder=Path(folder);names=['clock-before.state.json','clock-after.state.json','clock-samples.json','gui-result.json','loot-before.json','loot-after.json','loot-before-save.state.json','loot-after-save.state.json','loot-result.json']
    if not reload:names+=['loot-open.json','loot-after-take.json']
    data={n:evidence.read(folder/n) for n in names}
    if started_ns is not None and any((folder/n).stat().st_mtime_ns<started_ns for n in names):raise ValueError('Stale loot evidence')
    for n in ['clock-before.state.json','clock-after.state.json','loot-before-save.state.json','loot-after-save.state.json']:evidence.require_state(data[n])
    for n in ['clock-before.state.json','clock-after.state.json']:
        state=data[n]
        if state['current_area'].upper()!='AR0602' or len(state['party'])!=2 or state['selection']!=1:raise ValueError('Required selected leader/two-party AR0602 state absent')
    clock=data['clock-samples.json'];samples=clock['samples'];phases=['paused-initial']*5+['running']*running+['paused-final']*4
    if clock.get('schema')!='bg-redux-live-clock/1' or type(clock.get('ticks_per_second'))is not int or clock['ticks_per_second']<=0 or len(samples)!=running+9 or [x.get('phase') for x in samples]!=phases or [x.get('sample') for x in samples]!=list(range(running+9)):raise ValueError('Loot clock coverage differs')
    for key in ('game_time','elapsed_ms'):
        values=[x.get(key) for x in samples]
        if any(type(v)is not int for v in values) or values!=sorted(values):raise ValueError('Loot clock monotonicity differs')
    if len({s['game_time'] for s in samples[:5]})!=1 or len({s['game_time'] for s in samples[-4:]})!=1 or samples[-5]['game_time']<=samples[4]['game_time']:raise ValueError('Loot live progression/pause absent')
    if data['clock-before.state.json']['game_time']!=samples[0]['game_time'] or data['clock-after.state.json']['game_time']!=samples[-1]['game_time']:raise ValueError('Loot clock snapshot boundary differs')
    gui=data['gui-result.json']
    if gui.get('completed')is not True or gui.get('steps')!=running+9 or gui.get('events')!=['ReduxStart.PopulateLoad','press:load.baseline-row','ReduxStart.Ready','clock:resume','clock:pause']:raise ValueError('Normal-loop loot host incomplete')
    native=data['loot-result.json']
    if native.get('schema')!='bg-redux-container-loot-native/1' or native.get('completed')is not True or native.get('reload')is not reload or native.get('os_pointer_input')is not False or type(native.get('save_return_code'))is not int or native['save_return_code']!=0 or native.get('forced')is not False or len(native.get('directories',[]))!=1:raise ValueError('Loot completion/save guard differs')
    if native.get('action_id')!=(-1 if reload else action_id) or native.get('callback')!=('none' if reload else 'Container.TakeItemContainer') or native.get('close_callback')!=('none' if reload else 'Container.LeaveContainer') or native.get('ui_left_index')!=(None if reload else 0):raise ValueError('Stock action/callback dispatch evidence differs')
    observed=outcome(data['loot-before.json'],data['loot-after.json'],reload)
    leader_id=data['loot-before.json']['pc_runtime_id'];trace=[]
    for sample in samples:
        matching=[a for a in sample.get('action_trace',[]) if a.get('runtime_id')==leader_id]
        if len(matching)!=1:raise ValueError('Sampled leader action/position trace absent/ambiguous')
        if (matching[0].get('action_id')is not None and type(matching[0]['action_id'])is not int) or not isinstance(matching[0].get('position'),list) or len(matching[0]['position'])!=2 or any(type(v)is not int for v in matching[0]['position']):raise ValueError('Sampled action/position trace malformed')
        trace.append(matching[0])
    if not reload and (not any(t.get('position')!=data['loot-before.json']['pc_position'] for t in trace) or data['loot-before.json']['pc_position']==data['loot-after.json']['pc_position']):raise ValueError('Ordinary approach movement was not observed')
    if not reload:
        outcome(data['loot-open.json'],data['loot-after-take.json'])
        if inventory(data['loot-before.json']['container_inventory']['items'])!=inventory(data['loot-open.json']['container_inventory']['items']):raise ValueError('Container changed before callback')
        if inventory(actual_items(data['loot-before.json']['pc_inventory']))!=inventory(actual_items(data['loot-open.json']['pc_inventory'])):raise ValueError('Destination changed before callback')
    if data['clock-after.state.json']!=data['loot-before-save.state.json']:raise ValueError('Loot clock/save snapshot continuity differs')
    differences=evidence.diff(data['loot-before-save.state.json'],data['loot-after-save.state.json'])
    if differences:raise ValueError('Ordinary save changed captured state')
    for name,state in [('loot-before.json',data['clock-before.state.json']),('loot-after.json',data['clock-after.state.json'])]:
        actual=data[name];leader=state['party'][0]
        if leader['runtime_id']!=actual['pc_runtime_id'] or leader['inventory']!=actual['pc_inventory'] or leader['position']!=actual['pc_position'] or state['game_time']!=actual['game_time']:raise ValueError('Loot focused/full snapshot evidence differs')
    return dict(outcome=observed,output_save=native['directories'][0],native=native,samples=len(samples),sampled_leader_action_ids=sorted({t['action_id'] for t in trace if t.get('action_id')is not None}),sampled_movement_observed=any(t['position']!=trace[0]['position'] for t in trace),game_time_before=samples[0]['game_time'],game_time_after=samples[-1]['game_time'])

def check_wire(folder,api,expected_items,expected_pc):
    target=container_wire(common.member(folder,'sav').read_bytes());pc=api.legacy_oracle.read_wire(common.member(folder,'gam'))['party'][0]
    if inventory(target['items'],False)!=inventory(expected_items,False) or inventory(pc['items'],False)!=inventory(expected_pc,False):raise ValueError('Serialized loot/container ownership differs')
    return dict(container=target,party0_items=pc['items'],scope='Item identity/expiration/charges conserved; raw wire flags retained without asserting engine-extension flag representation equivalence.')

def run(args):
    project,source,build=args.project_root.resolve(),args.engine_source_root.resolve(),args.engine_build_root.resolve()
    if not 40<=args.running_samples<=160 or not 1<=args.timeout<=90:raise ValueError('Loot bounded sample/timeout range differs')
    results=args.results_root.resolve()
    if not results.is_relative_to(project/'phase1-local/results'):raise ValueError('Loot results must stay under private Phase1 results')
    out=shared.new_output(results,'container-loot-journey')
    result=dict(schema='bg-redux-container-loot-journey/1',directory=str(out),execution='not-run',verdict='failed',scope=SCOPE,stages=[],process_budget_seconds=2*args.timeout);before=candidate=None;api=None;preserved=[];configs=[];privates=[]
    try:
        api=shared.phase0(project);result['phase0_preflight']=api.baseline_runner.preflight(project)
        before=api.baseline_runner.protected(project);shared.write(out/'phase0-before.json',before)
        candidate=shared.candidate_inventory(source,build);shared.write(out/'candidate-before.json',candidate)
        receipt=check_build(args.host_build.resolve(),project,source,build)
        driver=out/'driver';driver.mkdir();host=driver/'Redux_loot_gui.exe';shared.frozen_copy(Path(receipt['binary']),host);shared.frozen_copy(args.host_build.resolve(),driver/'build.json')
        for name,row in receipt['sources'].items():shared.frozen_copy(Path(row['frozen']),driver/'sources'/row['sha256']/Path(name).name)
        shutil.copytree(args.host_build.resolve().parent/'compiled-sources',driver/'compiled-sources')
        startup=driver/'startup';startup.mkdir();shared.frozen_copy(project/'tools/phase0/gui/ReduxStart.py',startup/'ReduxStart.py')
        api.probe_ui_resources.TYPES['ids']=0x3f0
        raw_ids,origin=api.probe_ui_resources.read_resource('action','ids')
        if raw_ids is None:raise ValueError('Shipped ACTION.IDS unavailable')
        matches=re.findall(rb'^\s*(\d+)\s+UseContainer\(\)\s*$',raw_ids,re.M|re.I)
        if len(matches)!=1:raise ValueError('Shipped UseContainer action signature absent/ambiguous')
        action_id=int(matches[0]);(driver/'ACTION.IDS').write_bytes(raw_ids)
        result['action_ids']=dict(sha256=binary.digest(raw_ids),origin=origin,use_container_action_id=action_id)
        driver_files=evidence.manifest(driver);result['driver_files']=driver_files
        incoming=args.fixture.resolve()
        if incoming!=(project/'phase0-local/fixtures/original-bg2ee-20261020/GemRB').resolve():raise ValueError('Only the protected stock saved fixture is supported')
        initial=common.save_manifest(incoming);target=container_wire(common.member(incoming,'sav').read_bytes());wire=api.legacy_oracle.read_wire(common.member(incoming,'gam'))
        if [x['resref'] for x in target['items']]!=EXPECTED or len(wire['party'])!=2 or wire['party'][0]['area']!='AR0602' or wire['party'][0]['position']!=[3741,2801] or any(x['resref'].upper()=='SW1H04' for x in wire['party'][0]['items']):raise ValueError('Declared stock fixture/party/item guard differs')
        result['fixture']=dict(path=str(incoming),files=initial,container=target,party0=wire['party'][0]);preserved.append((incoming,initial))
        for index,name in enumerate(('take','reload')):
            stage=out/name;stage.mkdir();entry=dict(id=name,execution='not-run');result['stages'].append(entry);private=None
            try:
                input_files=common.save_manifest(incoming);entry['input_files']=input_files
                copied=stage/'profile/save/000000007-HarnessInput';shutil.copytree(incoming,copied)
                if common.save_manifest(copied)!=input_files:raise ValueError('Loot copied input drift')
                preserved.append((copied,input_files))
                private=shared.prepare_private_game(project,stage)
                privates.append((private,stage))
                for folder in ('capture','cache','override'):(stage/folder).mkdir()
                config=dict(GameType='bg2ee',GamePath=private['game'],GemRBPath=source/'gemrb',PluginsPath=build/'gemrb/plugins',CachePath=stage/'cache',SavePath=stage/'profile',ModPath=stage/'override',UseAsLibrary=0,SaveAsOriginal=1,Width=1024,Height=768,FullScreen=0,CapFPS=30,AudioDriver='none',GameLanguagePath='lang/en_US',SkipIntroVideos=1,Logging=1,LogColor=0,PathfinderThreadsCount=0,PathfinderMainThreadMode='immediate')
                cfg=stage/'probe.cfg';cfg.write_text(''.join(f'{k}={str(v).replace(chr(92),chr(47))}\n' for k,v in config.items()),encoding='utf-8');entry['config_sha256']=evidence.sha(cfg)
                configs.append((cfg,entry['config_sha256']))
                command=[str(host),'--config',str(cfg),'--output',str(stage/'capture'),'--scripts',str(startup),'--mode','live-clock','--clock-running-samples',str(args.running_samples),'--trace-actions','1','--journey',name]
                env=api.harness.environment(stage);prefix=project/'phase0-local/toolchain/msys64/ucrt64';env['PATH']=os.pathsep.join([str(build/'gemrb'),str(prefix/'bin'),env.get('PATH','')]);env['PYTHONDONTWRITEBYTECODE']='1'
                check_sources(receipt,project,source);shared.validate_private_game(private,stage)
                if evidence.manifest(driver)!=driver_files:raise ValueError('Frozen loot driver/source closure drift')
                started=time.time_ns();entry['process']=api.baseline_runner.execute(command,build,env,stage/'process.log',args.timeout)
                if (stage/'capture/loot-result.json').is_file():entry['native_receipt']=evidence.read(stage/'capture/loot-result.json')
                shared.require_process(entry['process'])
                if 'Traceback (most recent call last)' in (stage/'process.log').read_text(encoding='utf-8',errors='replace'):raise ValueError('Stock callback traceback')
                observed=validate_capture(stage/'capture',args.running_samples,bool(index),action_id,started);entry['observation']=observed
                loaded=evidence.read(stage/'capture/loot-before.json')
                entry['loaded_wire_guard']=check_wire(incoming,api,loaded['container_inventory']['items'],actual_items(loaded['pc_inventory']))
                saved=Path(observed['output_save']).resolve()
                if not saved.is_relative_to((stage/'profile/save').resolve()) or saved==copied.resolve():raise ValueError('Loot output escaped private profile or overwrote input')
                output_files=common.save_manifest(saved);frozen=stage/'frozen-save';shutil.copytree(saved,frozen)
                if common.save_manifest(frozen)!=output_files:raise ValueError('Frozen loot save differs')
                focused=evidence.read(stage/'capture/loot-after.json')
                entry['wire']=check_wire(frozen,api,focused['container_inventory']['items'],actual_items(focused['pc_inventory']))
                if index:
                    prior=evidence.read(out/'take/capture/loot-after.json');loaded=evidence.read(stage/'capture/loot-before.json')
                    if inventory(prior['container_inventory']['items'])!=inventory(loaded['container_inventory']['items']) or inventory(actual_items(prior['pc_inventory']))!=inventory(actual_items(loaded['pc_inventory'])):raise ValueError('Fresh-process reload lost/duplicated inventory')
                if common.save_manifest(copied)!=input_files or common.save_manifest(incoming)!=input_files or evidence.sha(cfg)!=entry['config_sha256']:raise ValueError('Immutable loot input/config changed')
                if evidence.manifest(stage/'override')!={}:raise ValueError('Unexpected private loot override appeared')
                entry.update(execution='passed',frozen_save=str(frozen),frozen_save_files=output_files);preserved.extend([(saved,output_files),(frozen,output_files),(copied,input_files)]);incoming=frozen
            except Exception as error:entry.update(execution='failed' if 'process'in entry else 'not-run',error=str(error));raise
            finally:
                if private is not None:entry['private_game_validation']=shared.validate_private_game(private,stage)
        result.update(execution='passed',verdict='stock-container-callback-loot-persisted')
    except Exception as error:
        result['error']=str(error)
        if any('process'in stage for stage in result['stages']):result['execution']='failed'
    finally:
        try:
            for folder,files in preserved:
                if common.save_manifest(folder)!=files:raise ValueError('Frozen/input loot save changed: '+str(folder))
            for cfg,digest in configs:
                if evidence.sha(cfg)!=digest or evidence.manifest(cfg.parent/'override')!={}:raise ValueError('Private loot config/override drift')
            result['private_game_final_validations']=[shared.validate_private_game(private,stage) for private,stage in privates]
            result['inputs_and_outputs_preserved']=True
            if 'receipt'in locals():check_sources(receipt,project,source)
            if 'driver_files'in locals() and evidence.manifest(driver)!=driver_files:raise ValueError('Frozen loot driver/source closure changed')
            common.finish_guards(result,out,project,source,build,api,before,candidate)
        except Exception as error:result.update(execution='failed',verdict='failed',preservation_error=str(error))
        shared.write(out/'result.json',result);shared.write(out/'artifact-manifest.json',dict(files=common.output_manifest(out)))
    print(out/'result.json',result['verdict'],flush=True)
    return 0 if result['execution']=='passed' else 1

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    for command in ('build','run'):
        p=sub.add_parser(command)
        for option in ('project-root','engine-source-root','engine-build-root'):p.add_argument('--'+option,type=Path,required=True)
        p.add_argument('--timeout',type=int,default=180 if command=='build' else 90)
        if command=='build':p.add_argument('--output-dir',type=Path,required=True)
        else:
            p.add_argument('--host-build',type=Path,required=True);p.add_argument('--fixture',type=Path,required=True);p.add_argument('--results-root',type=Path,required=True);p.add_argument('--running-samples',type=int,default=80)
    args=parser.parse_args(argv);return build_host(args) if args.command=='build' else run(args)

if __name__=='__main__':raise SystemExit(main())
