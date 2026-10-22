"""Separate active main/ammo/launcher journey; old offhand validator unchanged.

Build/run are explicit coordinator operations. No original mutation journey or
full AI/combat parity is inferred from equipment-resource pattern similarity.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import math
import os
from pathlib import Path
import shutil
import struct
import sys
import time
import uuid

import weapon_query_observer as observer
import weapon_query_validation as evidence

HERE=Path(__file__).resolve().parent
PREPARATION_SHA='b18bb391c451fb9ace9bdab3a43313c554f82cddf170af0751d95dd06ece1ce4'
RESOURCES=('sw1h01','sw1h02','bow01','bow02','arow01','arow02')
PLANS={
 'main':('02-plus-normal-pfmw',[
    ('00-initial','none','sw1h02',None),
    ('01-create-main-normal','CreateItem explicit-slot','sw1h01',None),
    ('02-ordinary-main-plus','ordinary remove/add/select','sw1h02',None),
    ('03-transform-main-normal','parsed TransformItem','sw1h01',None),
    ('04-create-main-plus','CreateItem explicit-slot','sw1h02',None)]),
 'ranged':('ammo-plus-pfmw',[
    ('00-initial','none','bow01','arow02'),
    ('01-create-ammo-normal','CreateItem explicit-slot','bow01','arow01'),
    ('02-transform-launcher-plus','parsed TransformItem','bow02','arow01'),
    ('03-ordinary-ammo-plus','ordinary remove/add/select','bow02','arow02'),
    ('04-transform-launcher-normal','parsed TransformItem','bow01','arow02'),
    ('05-create-ammo-normal','CreateItem explicit-slot','bow01','arow01'),
    ('06-create-launcher-plus','CreateItem explicit-slot','bow02','arow01'),
    ('07-ordinary-launcher-normal','ordinary remove/add/select','bow01','arow01'),
    ('08-create-ammo-plus','CreateItem explicit-slot','bow01','arow02')])}


def sources(project):
    """Freeze old helpers as inputs, never patch them for this new mode."""
    observer.phase0(project)
    paths=list(observer.required_sources())+[Path(__file__).resolve(),HERE/'native/weapon_slot_journey.cpp']
    folder=project/'tools/phase0'
    for module in tuple(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path and Path(path).resolve().is_relative_to(folder):
            path=Path(path).resolve()
            if path.suffix!='.py': raise ValueError('Non-source Phase0 helper closure')
            paths.append(path)
    paths=sorted(set(paths))
    if len({p.name for p in paths})!=len(paths): raise ValueError('Frozen source basename collision')
    return paths


def raw_resources(api,metadata,source):
    """Independent raw ITM bytes bind resource/header metadata, no asset output."""
    result={};reader=api.probe_ui_resources;reader.TYPES['itm']=0x3ed
    # ITMImporter::GetProficiency uses row index, then converts int to ieByte.
    table=source/'gemrb/unhardcoded/bg2ee/proftype.2da'
    lines=[line.split() for line in table.read_text(encoding='ascii').splitlines() if line.strip()]
    if lines[:3]!=[['2DA','V1.0'],['-1'],['OLD_PROFICIENCY']]: raise ValueError('Unsupported BG2EE proficiency table')
    profs=[]
    for index,cells in enumerate(lines[3:]):
        # Shipped rows include descriptive labels such as 15_BOW. Importer
        # indexes rows, not labels; require that numeric prefix to preserve order.
        if len(cells)!=2 or cells[0].split('_',1)[0]!=str(index):raise ValueError('Proficiency row index differs')
        profs.append(int(cells[1]))
    for ref in RESOURCES:
        raw,origin=reader.read_resource(ref,'itm')
        if raw is None or len(raw)<0x72 or hashlib.sha256(raw).hexdigest()!=metadata[ref]['sha256'] or raw[:8]!=b'ITM V1  ':
            raise ValueError('Prepared stock ITM input/hash differs: '+ref)
        at=struct.unpack_from('<I',raw,0x64)[0];count=struct.unpack_from('<H',raw,0x68)[0]
        if count<1 or count>100 or at+count*56>len(raw): raise ValueError('ITM ability bounds')
        result[ref]=dict(resref=ref,flags=struct.unpack_from('<I',raw,0x18)[0],
            enchantment=struct.unpack_from('<I',raw,0x60)[0],itemtype=struct.unpack_from('<H',raw,0x1c)[0],
            proficiency=raw[0x31],header_index=0,attack_type=raw[at],location=raw[at+2],
            range=struct.unpack_from('<H',raw,at+14)[0],thac0_bonus=struct.unpack_from('<H',raw,at+20)[0],
            dice_sides=struct.unpack_from('<H',raw,at+22)[0],dice_thrown=struct.unpack_from('<H',raw,at+24)[0],
            damage_bonus=struct.unpack_from('<h',raw,at+26)[0],damage_type=struct.unpack_from('<H',raw,at+28)[0],
            charges=struct.unpack_from('<H',raw,at+34)[0],recharge_flags=struct.unpack_from('<I',raw,at+38)[0])
        # ITMImporter applies this fixed header conversion to these two item types.
        if result[ref]['itemtype'] in (0x10,0x13): result[ref]['recharge_flags']^=16
        if not result[ref]['proficiency']:
            kind=result[ref]['itemtype']
            result[ref]['proficiency']=(profs[kind] if kind<len(profs) else 0)&255
    return result


def resource_guard(rows,raw):
    if len(rows)!=6 or {r.get('resref','').lower() for r in rows}!=set(RESOURCES):
        raise ValueError('Retained resource identity missing/duplicate')
    for row in rows:
        ref=row['resref'].lower();expected=raw[ref]
        if row!=expected or any(type(row.get(k)) is not type(v) for k,v in expected.items()):
            raise ValueError('Loaded retained resource differs from raw ITM header: '+ref)


def derived_guard(cache,resources,main,ammo,off):
    """Detect launcher bonus/range cache staleness even when max enchant is same."""
    derived=cache.get('derived_hands',[])
    if len(derived)!=2 or [r.get('hand') for r in derived]!=[1,2]: raise ValueError('Derived cache hand inventory')
    for index,(hand,extra) in enumerate(zip(cache['hands'],derived)):
        ref=(ammo or main) if index==0 else off
        if ref is None: continue # Cleared offhand has no semantic launcher/range fields.
        resource=resources[ref]
        header=hand['header']
        expected_header={key:resource[key] for key in ('attack_type','location','damage_type','dice_sides',
                                                     'dice_thrown','damage_bonus','charges','recharge_flags')}
        if header!=expected_header or any(type(header.get(k)) is not type(v) for k,v in expected_header.items()):
            raise ValueError('Cached selected header differs from exact resource header')
        base=resources[main] if ammo else resource
        expected=dict(hand=index+1,range=base['range']+1,itemtype=base['itemtype'],proficiency=base['proficiency'],
            selected_header_range=resource['range'],selected_header_thac0_bonus=resource['thac0_bonus'],
            launcher_damage_bonus=base['damage_bonus'] if ammo else 0,
            launcher_thac0_bonus=base['thac0_bonus'] if ammo else 0)
        if extra!=expected or any(type(extra.get(k)) is not type(v) for k,v in expected.items()):
            raise ValueError('Derived launcher/range/proficiency cache differs')


def action_guard(data,old,new,sender):
    if (data.get('parsed') is not True or type(data.get('action_id')) is not int or data['action_id']!=356
            or data.get('has_objects') is not False
            or data.get('expression')!='TransformItem("'+old+'","'+new+'")'
            or data.get('old_item','').lower()!=old or data.get('new_item','').lower()!=new
            or type(data.get('flags')) is not int or data['flags']&0x2000
            or type(data.get('target_count')) is not int or data['target_count']<1
            or type(data.get('resolved_runtime_id')) is not int or data['resolved_runtime_id']!=sender
            or type(data.get('matching_inventory_items')) is not int or data['matching_inventory_items']!=1
            or type(data.get('matching_slot')) is not int or data['matching_slot']!=35
            or data.get('charges')!=[0,0,0] or any(type(v) is not int for v in data['charges'])):
        raise ValueError('Actual parsed TransformItem sender/unique slot/resources differ')


def journey_envelope(data,row_id,scenario,repeats,nonce):
    identity,plan=PLANS[scenario]
    if (data.get('schema')!='bg-redux-phase1-active-slot-journey-native/1' or data.get('nonce')!=nonce
            or data.get('scenario')!=scenario or data.get('case_id')!=identity or row_id!=identity
            or type(data.get('repeats')) is not int or data['repeats']!=repeats
            or data.get('completed') is not True or data.get('error')):
        raise ValueError('Incomplete/wrong/stale active-slot journey')
    for key in ('sender_runtime_id','target_runtime_id'):
        if type(data.get(key)) is not int or data[key]<=0:raise ValueError('Missing native actor identity')
    if data['sender_runtime_id']==data['target_runtime_id']:raise ValueError('Sender/target identity overlaps')
    if [(s.get('id'),s.get('route'),s.get('expected_main'),s.get('expected_ammo')) for s in data['steps']]!=plan:
        raise ValueError('Missing/reordered active-slot mutation coverage')
    return identity,plan


def validate_journey(folder,row,metadata,raw,scenario,repeats,nonce,require_rng):
    folder=Path(folder);data=evidence.read(folder/'journey.json')
    identity,plan=journey_envelope(data,row['spec']['id'],scenario,repeats,nonce)
    resource_guard(evidence.read(folder/'resources.json'),raw)
    expected_dirs={s[0] for s in plan}
    if {p.name for p in folder.iterdir() if p.is_dir()}!=expected_dirs or {p.name for p in folder.iterdir() if p.is_file()}!={'journey.json','resources.json'}:
        raise ValueError('Missing/extra journey artifact surface')
    before=cache_before=initial_target=previous_rng=None;results=[]
    for index,((step_id,route,main,ammo),step) in enumerate(zip(plan,data['steps'])):
        location=folder/step_id;q=location/'queries'
        if evidence.read(location/'step.json')!=step or step.get('completed') is not True:
            raise ValueError('Step receipt/completion differs')
        mutation_before=evidence.read(location/'before-mutation.state.json')
        mutation_cache=evidence.read(location/'before-mutation.weapons.json')
        mutation_rng=evidence.require_rng_snapshot(evidence.read(location/'before-mutation.rng.json'))
        evidence.require_state(mutation_before)
        if index and (mutation_before!=before or mutation_cache!=cache_before): raise ValueError('Inter-step mutation continuity')
        if index and mutation_rng!=previous_rng: raise ValueError('Inter-step calling-thread RNG continuity')
        initialized=evidence.read(q/'initialized.state.json');cache=evidence.read(q/'initialized.weapons.json')
        initialized_rng=evidence.require_rng_snapshot(evidence.read(q/'initialized.rng.json'))
        if not index and (mutation_before!=initialized or mutation_cache!=cache or mutation_rng!=initialized_rng):
            raise ValueError('Initial stage mutates')
        spec=copy.deepcopy(row);spec['spec'].update(id=identity+':'+step_id,main=main,ammo=ammo)
        guard=evidence.runtime_guard(spec,metadata,initialized,cache)
        if index==0: initial_target=initialized['party'][1]
        if initialized['party'][1]!=initial_target or mutation_before['party'][1]!=initial_target:
            raise ValueError('Inventory mutation changed diagnostic target state')
        if guard['sender_runtime_id']!=data['sender_runtime_id'] or guard['target_runtime_id']!=data['target_runtime_id']:
            raise ValueError('Actual actor identity differs')
        derived_guard(cache,raw,main,ammo,spec['spec']['off'])
        allowed={'before-mutation.state.json','before-mutation.weapons.json','before-mutation.rng.json','step.json'}
        if route=='parsed TransformItem':
            allowed.add('transform-action.json');action_guard(evidence.read(location/'transform-action.json'),plan[index-1][2],main,data['sender_runtime_id'])
        if {p.name for p in location.iterdir() if p.is_file()}!=allowed or {p.name for p in location.iterdir() if p.is_dir()}!={'queries'}:
            raise ValueError('Unexpected/missing mutation artifact inventory')
        observation=evidence.validate_capture(q,spec,metadata,repeats,require_rng_observed=require_rng)
        if data.get('parsed_queries')!=evidence.read(q/'query-result.json').get('parsed_queries'):
            raise ValueError('Root and per-step parsed query evidence differ')
        if observation['rng_control_draw_call'] is not None: raise ValueError('Unexpected RNG control in mutation journey')
        before=evidence.read(q/'final.state.json');cache_before=evidence.read(q/'final.weapons.json')
        previous_rng=evidence.require_rng_snapshot(evidence.read(q/'final.rng.json'))
        results.append(dict(id=step_id,route=route,main=main,ammo=ammo,observation=observation,
            deliberate_state_changes=evidence.diff(mutation_before,initialized),
            deliberate_cache_changes=evidence.diff(mutation_cache,cache),
            deliberate_rng_changed=(mutation_rng!=initialized_rng) if mutation_rng['observed'] and initialized_rng['observed'] else None,
            original_mutation_parity=None))
    return dict(steps=results,cache_coherent=True,query_noninterference=all(s['observation']['collected_state_unchanged'] for s in results),
        rng_unchanged=all(s['observation']['rng_unchanged'] is True for s in results) if require_rng else None,
        stable_values=all(s['observation']['stable_values'] for s in results),original_mutation_parity=None,magic_slot_covered=False)


def check_build(path,project,source,build):
    receipt=evidence.read(path)
    if (receipt.get('schema')!='bg-redux-active-slot-build/1' or receipt.get('passed') is not True
            or receipt.get('project')!=str(project) or receipt.get('source')!=str(source) or receipt.get('build')!=str(build)
            or receipt.get('process',{}).get('exit_code')!=0 or receipt['process'].get('timed_out') is not False
            or receipt.get('candidate_inventory')!=observer.candidate_inventory(source,build)):
        raise ValueError('Stale/wrong/failed active-slot host build')
    if set(receipt.get('sources',{}))!={str(p) for p in sources(project)}: raise ValueError('Frozen helper closure differs')
    for original,pin in receipt['sources'].items():
        if evidence.sha(original)!=pin['sha256'] or evidence.sha(pin['frozen'])!=pin['sha256']:
            raise ValueError('Active-slot source/frozen helper drift')
    if evidence.sha(receipt['binary'])!=receipt['binary_sha256'] or evidence.sha(receipt['compiler'])!=receipt['compiler_sha256']:
        raise ValueError('Active-slot driver/compiler drift')
    if evidence.sha(build/'CMakeCache.txt')!=receipt.get('cmake_cache_sha256'): raise ValueError('Candidate CMake cache drift')
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('build','run'))
    for name in ('project-root','engine-source-root','engine-build-root','results-root'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--build-receipt',type=Path);parser.add_argument('--preparation',type=Path)
    parser.add_argument('--scenarios',nargs='+',choices=tuple(PLANS),default=list(PLANS))
    parser.add_argument('--repeats',type=int,default=2);parser.add_argument('--timeout',type=float,default=240)
    parser.add_argument('--require-rng-observed',action='store_true')
    args=parser.parse_args()
    if not math.isfinite(args.timeout) or not 0<args.timeout<=600 or not 1<=args.repeats<=8 or len(set(args.scenarios))!=len(args.scenarios):
        parser.error('Timeout must be finite in(0,600], repeats1..8, scenarios unique')
    if args.mode=='run' and (not args.preparation or not args.build_receipt): parser.error('run requires preparation/build-receipt')
    for name,value in vars(args).items():
        if isinstance(value,Path): setattr(args,name,value.resolve())
    project,source,build=args.project_root,args.engine_source_root,args.engine_build_root
    if source==project/'gemrb' or build==project/'phase0-local/build' or any(args.results_root.is_relative_to(p) for p in (source,build)):
        parser.error('Use isolated candidate roots/results outside protected Phase0 or source/build')
    api=observer.phase0(project);baseline=api.baseline_runner
    output=observer.new_output(args.results_root,'active-slot-'+args.mode)
    report=dict(schema='bg-redux-active-slot-'+args.mode+'/1',passed=False,directory=str(output),project=str(project),
        source=str(source),build=str(build),cases=[],original_mutation_parity=None)
    phase0=candidate=None;private_receipts=[];pins={}
    try:
        report['phase0_preflight']=baseline.preflight(project);phase0=baseline.protected(project)
        observer.write(output/'phase0-before.json',phase0)
        candidate=observer.candidate_inventory(source,build);report['candidate_inventory']=candidate
        observer.write(output/'candidate-before.json',candidate)
        compiler=project/'phase0-local/toolchain/msys64/ucrt64/bin/g++.exe'
        pins[str(compiler)]=evidence.sha(compiler)
        pins[str(build/'CMakeCache.txt')]=evidence.sha(build/'CMakeCache.txt')
        report['cmake_cache_sha256']=pins[str(build/'CMakeCache.txt')]
        report['sources']={str(p):observer.frozen_copy(p,output/'sources'/p.name) for p in sources(project)}
        pins.update({p:r['sha256'] for p,r in report['sources'].items()})
        prefix=compiler.parent.parent
        env=os.environ.copy();env['PATH']=os.pathsep.join([str(build/'gemrb'),str(prefix/'bin'),env.get('PATH','')])
        env['PYTHONDONTWRITEBYTECODE']='1'
        if args.mode=='build':
            if evidence.sha(HERE/'native/phase0_save_probe_snapshot.cpp')!=evidence.sha(project/'tools/phase0/native/save_probe.cpp'):
                raise ValueError('Frozen Phase0 serializer differs')
            binary=output/'Redux_active_slot_journey.exe'
            command=[str(compiler),'-std=gnu++17','-g','-O0','-DHAVE_CONFIG_H','-DUSE_OPENGL_API','-D_USE_MATH_DEFINES',
                '-DFMT_HEADER_ONLY','-DFMT_USE_CONSTEVAL=0','-DFMT_EXCEPTIONS=0','-DFMT_UNICODE=1','-fno-strict-aliasing']
            for include in (build,source/'gemrb/includes',source/'gemrb/core',source/'platforms/Windows',build/'gemrb/includes',
                            prefix/'include/SDL2',prefix/'include/python3.14',source/'includes/fmt'):
                command+=['-I',str(include)]
            command+=[str(output/'sources/weapon_slot_journey.cpp'),str(build/'gemrb/core/libgemrb_core.dll.a'),
                      str(prefix/'lib/libiconv.dll.a'),'-lshlwapi','-o',str(binary)]
            report['process']=baseline.execute(command,output,env,output/'build.log',args.timeout)
            observer.require_process(report['process'])
            report.update(binary=str(binary),binary_sha256=evidence.sha(binary),compiler=str(compiler),compiler_sha256=evidence.sha(compiler),passed=True)
        else:
            receipt=check_build(args.build_receipt,project,source,build)
            pins[str(args.build_receipt)]=evidence.sha(args.build_receipt)
            pins[receipt['binary']]=receipt['binary_sha256']
            if evidence.sha(args.preparation)!=PREPARATION_SHA: raise ValueError('Exact 22-case original preparation required')
            prep,rows=observer.check_preparation(args.preparation,[PLANS[s][0] for s in args.scenarios])
            raw=raw_resources(api,prep['item_metadata'],source);observer.write(output/'raw-item-metadata.json',raw)
            pins[str(args.preparation)]=PREPARATION_SHA
            def freeze_input(original,destination):
                frozen=observer.frozen_copy(Path(original),destination)
                pins[str(destination)]=frozen['sha256']
                return frozen
            freeze_input(args.preparation,output/'preparation.json')
            binary=output/'driver/Redux_active_slot_journey.exe';freeze_input(receipt['binary'],binary)
            freeze_input(args.build_receipt,output/'driver/build.json')
            for name,row in receipt['sources'].items():freeze_input(row['frozen'],output/'driver/sources'/Path(name).name)
            for scenario in args.scenarios:
                row=next(r for r in rows if r['spec']['id']==PLANS[scenario][0])
                folder=output/scenario;folder.mkdir();case=dict(scenario=scenario,nonce=uuid.uuid4().hex,passed=False)
                report['cases'].append(case)
                try:
                    if row['spec']['defense']!=[120,0,1]: raise ValueError('Required PFMW target differs')
                    shutil.copytree(row['fixture'],folder/'input')
                    if evidence.manifest(folder/'input')!=row['fixture_files']: raise ValueError('Copied final fixture drift')
                    for name,entry in row['fixture_files'].items():
                        pins[str(Path(row['fixture'])/name)]=entry['sha256']
                        pins[str(folder/'input'/name)]=entry['sha256']
                    pins[row['script_path']]=row['script_sha256']
                    override=folder/'override';override.mkdir();freeze_input(row['script_path'],override/(row['script']+'.bcs'))
                    private=observer.prepare_private_game(project,folder);private_receipts.append((folder,private))
                    for name in ('cache','engine-profile','capture','profile'):(folder/name).mkdir()
                    config=dict(GameType='bg2ee',GamePath=private['game'],GemRBPath=source/'gemrb',PluginsPath=build/'gemrb/plugins',
                        CachePath=folder/'cache',SavePath=folder/'engine-profile',UseAsLibrary=1,AudioDriver='none',GameLanguagePath='lang/en_US',
                        ModPath=override,Logging=1,LogColor=0,PathfinderThreadsCount=0,PathfinderMainThreadMode='immediate')
                    cfg=folder/'probe.cfg';cfg.write_text(''.join('%s=%s\n'%(k,str(v).replace('\\','/')) for k,v in config.items()),encoding='utf-8')
                    config_sha=evidence.sha(cfg)
                    pins[str(cfg)]=config_sha
                    command=[str(binary),'--config',str(cfg),'--output',str(folder/'capture'),'--save-dir',str(folder/'input'),
                        '--case-id',row['spec']['id'],'--repeats',str(args.repeats),'--scenario',scenario,'--nonce',case['nonce']]
                    launch_env=env.copy();launch_env.update(HOME=str(folder/'profile'),USERPROFILE=str(folder/'profile'),APPDATA=str(folder/'profile/AppData/Roaming'))
                    case['started_utc']=datetime.now(timezone.utc).isoformat();started=time.time_ns()
                    case['process']=baseline.execute(command,folder,launch_env,folder/'process.log',args.timeout)
                    observer.require_process(case['process'])
                    if (folder/'capture/journey.json').stat().st_mtime_ns<started: raise ValueError('Stale native journey')
                    case['observation']=validate_journey(folder/'capture',row,prep['item_metadata'],raw,scenario,args.repeats,case['nonce'],args.require_rng_observed)
                    obs=case['observation'];case['passed']=obs['query_noninterference'] and obs['stable_values'] and (not args.require_rng_observed or obs['rng_unchanged'])
                    if evidence.manifest(folder/'input')!=row['fixture_files'] or evidence.sha(cfg)!=config_sha:raise ValueError('Input/config changed')
                except Exception as error:case.update(passed=False,error=str(error))
                observer.write(folder/'result.json',case)
            report['passed']=len(report['cases'])==len(args.scenarios) and all(c['passed'] for c in report['cases'])
    except Exception as error:report['error']=str(error)
    finally:
        try:
            for folder,private in private_receipts:observer.validate_private_game(private,folder)
            if phase0 is not None:
                after=baseline.protected(project);observer.write(output/'phase0-after.json',after)
                report['phase0_preserved']=phase0==after
                if phase0!=after:raise ValueError('Protected Phase0 changed')
            if candidate is not None:
                after=observer.candidate_inventory(source,build);observer.write(output/'candidate-after.json',after)
                report['candidate_preserved']=candidate==after
                if candidate!=after:raise ValueError('Candidate source/binaries changed')
            for path,digest in pins.items():
                if evidence.sha(path)!=digest:raise ValueError('Bound source/compiler/fixture/script/driver changed')
            for entry in report.get('sources',{}).values():
                if evidence.sha(entry['frozen'])!=entry['sha256']:raise ValueError('Frozen helper changed')
        except Exception as error:report.update(passed=False,preservation_error=str(error))
        observer.write(output/('build.json' if args.mode=='build' else 'result.json'),report)
        files={}
        for root,dirs,names in os.walk(output,followlinks=False):
            dirs[:]=[n for n in dirs if n!='private-game']
            for name in names:
                p=Path(root)/name;files[p.relative_to(output).as_posix()]=dict(bytes=p.stat().st_size,sha256=evidence.sha(p))
        for folder,private in private_receipts:
            for p in Path(private['game']).iterdir():
                if p.is_file() and not p.is_symlink():
                    files[p.relative_to(output).as_posix()]=dict(bytes=p.stat().st_size,sha256=evidence.sha(p))
        observer.write(output/'artifact-manifest.json',dict(files=files,scope='Owned outputs; private-game linked assets excluded'))
    print(output,report['passed'],flush=True)
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
