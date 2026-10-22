"""Candidate-root paired AI adapter over the exact frozen Phase 0 original inputs.

Coordinator-only owned serial launches; --verify-only performs read-only oracle
validation. Original visual branch/combat attestations are distinct from native
action/target samples. No whole-AI, original-memory, timing or DPR parity claim.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid

HERE=Path(__file__).resolve().parent
PREPARATION_SHA='c9c9a6b3c7040f673463d690d392c39b238352f16dc54fe06cbd3fca4030755e'
REFERENCE_SHA='93d4091c8bdf9ee597e3ed71c931d174f89efdfceea32ded6c2f69658625abed'
REFERENCE_INPUTS_SHA='4487f7f0d53c2bbb8e6004e4aa6147efba87848f31b2aa7c6ab4e32421912eb1'
CASES={'ai-imoen-stock':115,'ai-imoen-noquery':115,'ai-default-stock':307,'ai-default-noquery':307}
OBSERVATION_SHA={
    'ai-imoen-stock':'8d359ec579d9d904dd41bd941ad8a4d264ac7526f6f73f406543063568830ab1',
    'ai-imoen-noquery':'d89b5a325eb25538d61bce58ee3ae082215f1cbcac9870062723635728306e7a',
    'ai-default-stock':'f05c28b4631d6eb5aac8a955609d7c9c72a7f87e10a64045407d801f403c3397',
    'ai-default-noquery':'c46cd5718867a272c707a95bc1bd37244041b526845e867ea34f5bfab8943930'}


def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def manifest(folder):
    folder=Path(folder)
    return {p.relative_to(folder).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p))
            for p in sorted(folder.rglob('*')) if p.is_file()}


def member(root,name):
    name=name.replace('\\','/')
    path=Path(name)
    if path.is_absolute() or ':' in name or '..' in path.parts or not path.parts:
        raise ValueError('Unsafe manifested member')
    target=(Path(root)/path).resolve()
    if not target.is_relative_to(Path(root).resolve()): raise ValueError('Member escaped root')
    return target


def freeze(source,destination,expected=None):
    source,destination=Path(source),Path(destination)
    digest=expected or sha(source)
    if sha(source)!=digest: raise ValueError('Validated input changed before freezing: '+str(source))
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        if sha(destination)!=digest: raise ValueError('Frozen destination collision')
    else:
        shutil.copy2(source,destination)
    if sha(source)!=digest or sha(destination)!=digest:
        raise ValueError('Input changed while freezing: '+str(source))
    return dict(source=str(source.resolve()),frozen=str(destination.resolve()),sha256=digest,bytes=destination.stat().st_size)


def observe_native(folder,spec,expected_branch=None):
    """Strict normal-loop evidence, with no save-only or branch-only fallback."""
    folder=Path(folder)
    result=read(folder/'gui-result.json')
    before,after=read(folder/'clock-before.state.json'),read(folder/'clock-after.state.json')
    clock=read(folder/'clock-samples.json')
    if result.get('completed') is not True or result.get('steps')!=89:
        raise ValueError('Normal-loop bounded run incomplete')
    events=result.get('events',[])
    if events!=['ReduxStart.PopulateLoad','press:load.baseline-row','ReduxStart.Ready','clock:resume','clock:pause']:
        raise ValueError('Ordinary load/readiness/pause boundary evidence differs')
    if before.get('schema')!='bg-redux-state/1' or after.get('schema')!='bg-redux-state/1':
        raise ValueError('Native state schema missing')
    samples=clock.get('samples',[])
    phases=['paused-initial']*5+['running']*80+['paused-final']*4
    if (clock.get('schema')!='bg-redux-live-clock/1' or len(samples)!=89
            or [r.get('sample') for r in samples]!=list(range(89)) or [r.get('phase') for r in samples]!=phases
            or type(clock.get('ticks_per_second')) is not int or clock['ticks_per_second']<=0):
        raise ValueError('Clock phases/count/readiness evidence incomplete')
    for field in ('game_time','elapsed_ms'):
        values=[r.get(field) for r in samples]
        if any(type(v) is not int for v in values) or values!=sorted(values):
            raise ValueError('Clock sample ordering/type differs')
    if (len({r['game_time'] for r in samples[:5]})!=1 or len({r['game_time'] for r in samples[-4:]})!=1
            or samples[84]['game_time']<=samples[4]['game_time'] or after['game_time']!=samples[-1]['game_time']
            or before['game_time']!=samples[0]['game_time']):
        raise ValueError('Paused/running clock boundaries not observed')
    globals_={k.upper():v for k,v in after['globals'].items()}
    branch=globals_.get('RDXBRANCH')
    if (globals_.get('RDXAIDONE')!=1 or globals_.get('RDXFOESEEN')!=1 or type(branch) is not int
            or not spec['first']<=branch<spec['first']+4):
        raise ValueError('Native branch/visibility markers absent or outside prepared tail')
    if len(before['party'])!=2 or len(after['party'])!=2:
        raise ValueError('Exact two-party fixture not observed')
    sender=after['party'][0]
    foes=[r for r in after['current_area_actors'] if r['script_name'].lower()=='rdxfoe']
    before_foes=[r for r in before['current_area_actors'] if r['script_name'].lower()=='rdxfoe']
    if len(foes)!=1 or len(before_foes)!=1:
        raise ValueError('Declared native foe absent/ambiguous')
    foe=foes[0]
    if sender['runtime_id']!=before['party'][0]['runtime_id'] or foe['runtime_id']!=before_foes[0]['runtime_id'] or sender['runtime_id']==foe['runtime_id']:
        raise ValueError('Sender/foe identity changed or overlaps')
    for state in (before,after):
        inv=state['party'][0]['inventory']
        if inv['equipped']!=0 or not any(r['slot']==35 and r['resref'].lower()=='sw1h02' for r in inv['items']):
            raise ValueError('Actual equipped weapon differs from final fixture')
    attacks=[]
    for row in samples:
        trace=row.get('action_trace',[])
        if row['phase']=='running' and any(a.get('runtime_id')==sender['runtime_id'] and a.get('action_id')==105
                and a.get('current_action_target')==foe['runtime_id'] for a in trace):
            if len([a for a in trace if a.get('runtime_id')==foe['runtime_id'] and a.get('name','').lower()=='rdxfoe'])!=1:
                raise ValueError('Attack trace target lacks same-sample declared foe identity')
            attacks.append(row['sample'])
    if not attacks: raise ValueError('Native AttackOneRound against declared foe not sampled')
    return dict(branch=branch,expected_original_branch=expected_branch,
        original_visual_branch_matches=branch==expected_branch if expected_branch is not None else None,
        native_action_target_observed=True,attack_samples=attacks,sender_runtime_id=sender['runtime_id'],
        foe_runtime_id=foe['runtime_id'],foe_hp_before=before_foes[0]['modified_stats'][0],foe_hp_after=foe['modified_stats'][0],
        retained_tail_after_marker=globals_.get('RDXAFTER'),
        state_sha256=sha(folder/'clock-after.state.json'),samples_sha256=sha(folder/'clock-samples.json'),
        original_exact_action_or_target_sample=False,whole_ai_or_dpr_parity=False)


def reference_inputs(reference):
    """Pin retained before-state, driver and historical tool inputs as well as samples."""
    names=['driver/'+n for n in ('build.json','build.log','Redux_gui_probe.exe')]
    names+=['tool-source/'+n for n in ('paired_ai_live.py','ai_fallback.py','harness.py','baseline_runner.py')]
    names+=[case+'/'+n for case in CASES for n in
            ('clock-before.state.json','clock-after.state.json','clock-samples.json','gui-result.json')]
    pins={name:sha(reference/name) for name in names}
    if hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest()!=REFERENCE_INPUTS_SHA:
        raise ValueError('Historical before-state/driver/tool evidence drift')
    if read(reference/'driver/build.json')['binary_sha256']!=pins['driver/Redux_gui_probe.exe']:
        raise ValueError('Historical driver binary differs from retained build receipt')
    return pins


def original_inputs(project,preparation,observations,reference):
    if sha(preparation)!=PREPARATION_SHA: raise ValueError('Not the exact authorized Phase 0 preparation')
    prep=read(preparation)
    if prep.get('run_id')!='20261021T230944Z-original-live-6efa5f54' or prep.get('nonce')!='E1AEF966':
        raise ValueError('Original preparation run/nonce differs')
    if [r['spec']['id'] for r in prep['cases']]!=list(CASES): raise ValueError('Four prepared cases/order differ')
    validator=load(project/'tools/phase0/original_live_capture.py','phase1_paired_original_capture')
    captures={}
    for path in observations:
        obs=read(path);identity=obs.get('case')
        if identity not in CASES or identity in captures or sha(path)!=OBSERVATION_SHA[identity]:
            raise ValueError('Wrong/duplicate/drifted original observation')
        validated=validator.validate_capture(preparation,path)
        if (validated['selected_branch']!=CASES[identity] or validated['phase']!='ENTER'
                or validated['queue_completion_observed'] is not False):
            raise ValueError('Original selected branch/claim differs from frozen oracle')
        captures[identity]=validated
    if set(captures)!=set(CASES): raise ValueError('Four original observations required')
    reference=Path(reference)
    if sha(reference/'result.json')!=REFERENCE_SHA or sha(reference/'preparation.json')!=PREPARATION_SHA:
        raise ValueError('Not the exact prior native paired reference')
    reference_inputs(reference)
    historical=read(reference/'result.json')
    prior={}
    for row in historical['cases']:
        identity=row['id']
        spec=next(r['spec'] for r in prep['cases'] if r['spec']['id']==identity)
        observed=observe_native(reference/identity,spec)
        old_expected=CASES[identity]+(3 if identity.endswith('-stock') else 0)
        if (identity in prior or observed['branch']!=old_expected or row.get('verdict')!='native-ai-observed'
                or row['observation']['state_sha256']!=observed['state_sha256']
                or row['observation']['samples_sha256']!=observed['samples_sha256']):
            raise ValueError('Prior native branch/samples differ from frozen reference')
        prior[identity]=observed
    if set(prior)!=set(CASES): raise ValueError('Prior four-case native evidence missing')
    return prep,captures,prior


def candidate_inventory(source,build):
    names=subprocess.check_output(['git','-C',str(source),'ls-files','--cached','--others','--exclude-standard','-z']).decode().split('\0')
    sources={name:dict(bytes=(source/name).stat().st_size,sha256=sha(source/name)) for name in names
             if name and not name.startswith('redux/') and name!='README_BG_REDUX.md' and (source/name).is_file()}
    binaries=[p for p in (build/'gemrb').rglob('*') if p.is_file() and
              (p.suffix.lower() in ('.exe','.dll') or p.name=='libgemrb_core.dll.a')]+[build/'config.h']
    if not sources or not (build/'gemrb/libgemrb_core.dll').is_file() or not list((build/'gemrb/plugins').glob('*.dll')):
        raise ValueError('Candidate source/core/plugins missing')
    return dict(source=sources,binaries={p.relative_to(build).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(binaries)})


def check_driver(args):
    receipt=read(args.probe_build_receipt)
    process=receipt.get('process',receipt)
    command=receipt.get('command',process.get('command',[]))
    if process.get('exit_code')!=0 or process.get('timed_out',False) is not False:
        raise ValueError('External GUI host build failed/incomplete')
    if not any(Path(a).name.lower()=='gui_probe.cpp' for a in command):
        raise ValueError('Receipt is not the normal-loop GUI host build')
    if (receipt.get('binary_sha256')!=sha(args.probe)
            or receipt.get('engine_dll_sha256')!=sha(args.engine_build_root/'gemrb/libgemrb_core.dll')
            or receipt.get('compiler_sha256')!=sha(args.prefix/'bin/g++.exe')):
        raise ValueError('External GUI binary/core/compiler pin drift')
    rows=receipt.get('sources',receipt.get('source_files',{}))
    if not rows: raise ValueError('External GUI host sources missing')
    pins={}
    for name,value in rows.items():
        path=Path(name)
        if not path.is_absolute(): path=member(args.probe_source_root,name)
        if not path.resolve().is_relative_to(args.probe_source_root.resolve()):
            raise ValueError('External GUI source escaped explicit probe source root')
        digest=value['sha256'] if isinstance(value,dict) else value
        if sha(path)!=digest: raise ValueError('External GUI source pin drift: '+str(path))
        pins[str(path.resolve())]=digest
    if not {'gui_probe.cpp','save_probe.cpp'}<={Path(p).name for p in pins}:
        raise ValueError('GUI host/serializer source pair missing')
    return receipt,pins


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('project-root','preparation','reference'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--observations',nargs=4,type=Path,required=True)
    parser.add_argument('--verify-only',action='store_true')
    for name in ('engine-source-root','engine-build-root','probe-source-root','probe-build-receipt','probe','prefix','results-root'):
        parser.add_argument('--'+name,type=Path)
    args=parser.parse_args()
    for name,value in vars(args).items():
        if isinstance(value,Path): setattr(args,name,value.resolve())
    project=args.project_root
    if args.verify_only:
        prep,captures,prior=original_inputs(project,args.preparation,args.observations,args.reference)
        print(json.dumps(dict(original_branches={k:v['selected_branch'] for k,v in captures.items()},
                              prior_native_branches={k:v['branch'] for k,v in prior.items()},nonce=prep['nonce']),indent=2))
        return 0
    if any(getattr(args,name) is None for name in ('engine_source_root','engine_build_root','probe_source_root','probe_build_receipt','probe','prefix','results_root')):
        parser.error('Run requires all explicit candidate/probe/prefix/result roots')
    source,build=args.engine_source_root,args.engine_build_root
    if source==project/'gemrb' or build==project/'phase0-local/build':
        parser.error('Candidate source/build must be separate from protected Phase 0 roots')
    out=args.results_root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-candidate-paired-ai-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    report=dict(schema='bg-redux-phase1-paired-ai/1',directory=str(out),cases=[],verdict='failed',execution='not-run')
    baseline=load(project/'tools/phase0/baseline_runner.py','phase1_paired_baseline_guard')
    helper=load(HERE/'menu_harness.py','phase1_paired_process_helper')
    phase0_before=candidate_before=game_before=None
    protected_files={}
    try:
        report['phase0_preflight']=baseline.preflight(project)
        phase0_before=baseline.protected(project);write(out/'phase0-before.json',phase0_before)
        candidate_before=candidate_inventory(source,build);write(out/'candidate-before.json',candidate_before)
        prep,captures,prior=original_inputs(project,args.preparation,args.observations,args.reference)
        driver,pins=check_driver(args)
        protected_files.update(pins)
        for path in [Path(__file__),HERE/'menu_harness.py',HERE/'private_game.py',project/'tools/phase0/baseline_runner.py',
                     project/'tools/phase0/original_live_capture.py',args.preparation,args.probe_build_receipt,args.probe,
                     args.reference/'result.json',args.reference/'preparation.json',project/'tools/phase0/gui/ReduxStart.py']+args.observations:
            protected_files[str(path.resolve())]=sha(path)
        for capture in captures.values():
            for entry in list(capture['artifacts'].values())+list(capture['fixture_files'].values()):
                protected_files[entry['source']]=entry['sha256']
        game=Path(prep['game'])
        game_before=helper.private_game.source_inventory(game)
        write(out/'original-game-before.json',game_before)
        frozen={}
        for path,digest in protected_files.items():
            frozen[path]=freeze(path,out/'bound-inputs'/digest/Path(path).name,digest)
        write(out/'frozen-inputs.json',frozen)
        freeze(args.probe,out/'driver/Redux_gui_probe.exe',driver['binary_sha256'])
        freeze(args.probe_build_receipt,out/'driver/build.json',sha(args.probe_build_receipt))
        for name,digest in reference_inputs(args.reference).items():
            path=args.reference/name
            protected_files[str(path)]=digest
            freeze(path,out/'phase0-native-reference'/name,digest)
        report['original_observations']=captures
        report['prior_native_observations']=prior
        write(out/'preparation.json',report)
        for row in prep['cases']:
            identity=row['spec']['id'];folder=out/identity;folder.mkdir()
            case=dict(id=identity,nonce=uuid.uuid4().hex,execution='failed');report['cases'].append(case)
            try:
                fixture=Path(row['fixture'])
                if manifest(fixture)!=row['fixture_files']: raise ValueError('Final row.fixture_files drift (precursor construction manifest is not authority)')
                profile=folder/'engine-profile';copied=profile/'save/000000007-HarnessInput'
                shutil.copytree(fixture,copied)
                private=helper.private_game.prepare(game,folder/'game');write(folder/'private-game-preparation.json',private)
                (folder/'cache').mkdir()
                for relative,digest in [('Baldur.exe',prep['executable_sha256']),('lang/en_US/dialog.tlk',prep['private_tlk_sha256']),
                                        ('engine.lua',prep['engine_lua_sha256']),('override/'+row['script']+'.bcs',row['script_sha256'])]:
                    if sha(folder/'game'/relative)!=digest: raise ValueError('Private candidate exact original input differs: '+relative)
                cfg=folder/'probe.cfg'
                config=dict(GameType='bg2ee',GameName='BG Redux paired AI '+case['nonce'],GamePath=folder/'game',
                    GemRBPath=source/'gemrb',GUIScriptsPath=source/'gemrb',GemRBOverridePath=source/'gemrb',GemRBUnhardcodedPath=source/'gemrb',
                    PluginsPath=build/'gemrb/plugins',CachePath=folder/'cache',SavePath=profile,UseAsLibrary=0,Width=1024,Height=768,
                    FullScreen=0,CapFPS=30,AudioDriver='none',GameLanguagePath='lang/en_US',SkipIntroVideos=1,Logging=1,LogColor=0,
                    PathfinderThreadsCount=0,PathfinderMainThreadMode='immediate')
                cfg.write_text(''.join('%s=%s\n'%(k,str(v).replace('\\','/')) for k,v in config.items()),encoding='utf-8')
                cfg_sha=sha(cfg)
                command=[str(out/'driver/Redux_gui_probe.exe'),'--config',str(cfg),'--output',str(folder),
                    '--scripts',str(project/'tools/phase0/gui'),'--mode','live-clock','--clock-running-samples','80','--trace-actions','1']
                env=os.environ.copy();env['PATH']=os.pathsep.join([str(args.prefix/'bin'),str(build/'gemrb'),env.get('PATH','')])
                env.update(HOME=str(profile),USERPROFILE=str(profile),APPDATA=str(profile/'AppData/Roaming'),PYTHONDONTWRITEBYTECODE='1')
                case['started_utc']=datetime.now(timezone.utc).isoformat();started=time.time_ns()
                case['command']=command;case['config_sha256']=cfg_sha
                case['process']=helper.run_owned(command,build,env,folder/'process.log',90)
                case['private_game_preservation']=helper.private_game.validate(private)
                if case['process']['exit_code']!=0 or case['process']['timed_out'] or not case['process']['cleanup_complete']:
                    raise ValueError('Owned bounded native case failed/timed out')
                if helper.callback_errors(folder/'process.log'): raise ValueError('Native Python callback traceback')
                for name in ('clock-before.state.json','clock-after.state.json','clock-samples.json','gui-result.json'):
                    if (folder/name).stat().st_mtime_ns<started: raise ValueError('Stale native output timestamp')
                observed=observe_native(folder,row['spec'],CASES[identity])
                case.update(observation=observed,prior_native_branch=prior[identity]['branch'],original=captures[identity],
                    execution='observed',compatibility='matches-original-visual-branch' if observed['original_visual_branch_matches'] else 'branch-difference')
                if manifest(copied)!=row['fixture_files'] or manifest(fixture)!=row['fixture_files'] or sha(cfg)!=cfg_sha:
                    raise ValueError('Final fixture/config changed during paired case')
            except (OSError,ValueError,KeyError,TypeError) as error:
                case.update(execution='failed',error=str(error))
            write(folder/'result.json',case);write(out/'result.json',report)
        if len(report['cases'])==4 and all(r['execution']=='observed' for r in report['cases']):
            report['execution']='passed'
            report['verdict']='four-original-branches-matched' if all(r['compatibility']=='matches-original-visual-branch' for r in report['cases']) else 'branch-differences'
    except Exception as error:
        report['error']=str(error)
    finally:
        try:
            if phase0_before is not None:
                after=baseline.protected(project);write(out/'phase0-after.json',after)
                report['phase0_preservation']={k:phase0_before[k]==after[k] for k in phase0_before}
                if not all(report['phase0_preservation'].values()): raise ValueError('Phase 0 protected inputs changed')
            if candidate_before is not None:
                after=candidate_inventory(source,build);write(out/'candidate-after.json',after)
                report['candidate_preserved']=candidate_before==after
                if not report['candidate_preserved']: raise ValueError('Candidate source/binaries changed')
            if game_before is not None and helper.private_game.source_inventory(game)!=game_before:
                raise ValueError('Original private game inventory/root hashes changed')
            if any(sha(p)!=h for p,h in protected_files.items()): raise ValueError('Frozen source/original/driver/reference input drift')
            report['bound_inputs_preserved']=bool(protected_files)
        except Exception as error:
            report.update(verdict='failed',preservation_error=str(error))
        report['scope']=__doc__
        write(out/'result.json',report)
        write(out/'artifact-manifest.json',helper.artifact_manifest(out))
    print(json.dumps(dict(directory=str(out),verdict=report['verdict']),indent=2))
    return 0 if report['verdict']=='four-original-branches-matched' else 1


if __name__=='__main__': raise SystemExit(main())
