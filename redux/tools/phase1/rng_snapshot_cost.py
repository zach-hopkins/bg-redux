"""Coordinator-only external RNG snapshot API cost build/run; no engine changes.

Unique receipts preserve failures. Timing describes the imported Debug API copy
loop plus loop/counter overhead, excluding serialization, file IO and rendering.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import time
import uuid

HERE=Path(__file__).resolve().parent
MAX_ITERATIONS=1000000


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,value): Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def integer(value,minimum,maximum,label):
    if type(value) is not int or not minimum<=value<=maximum: raise ValueError('Invalid '+label)
    return value


def state(value):
    if not isinstance(value,str) or len(value)>12000: raise ValueError('Missing serialized RNG state')
    words=value.split(' ')
    if len(words)!=313 or any(not re.fullmatch(r'0|[1-9][0-9]*',w) for w in words):
        raise ValueError('Malformed mt19937_64 state')
    if any(int(w)>2**64-1 for w in words[:-1]) or int(words[-1])>312:
        raise ValueError('Invalid mt19937_64 state word/index')
    return value


def validate_capture(data,nonce,pid,iterations,limit_ms):
    integer(iterations,1,MAX_ITERATIONS,'requested iterations')
    integer(limit_ms,1,60000,'requested phase-boundary time budget')
    integer(pid,1,2**32-1,'owned PID')
    if (data.get('schema')!='bg-redux-rng-snapshot-cost/1' or data.get('nonce')!=nonce
            or type(data.get('pid')) is not int or data['pid']!=pid or data.get('completed') is not True
            or data.get('fresh_thread') is not True or type(data.get('trials_expected')) is not int or data['trials_expected']!=3
            or data.get('clock')!='std::chrono::steady_clock' or data.get('clock_is_steady') is not True
            or type(data.get('iterations')) is not int or data['iterations']!=iterations
            or type(data.get('time_limit_ms')) is not int or data['time_limit_ms']!=limit_ms
            or type(data.get('state_words')) is not int or data['state_words']!=312):
        raise ValueError('Stale/wrong/incomplete benchmark identity or mode')
    size=integer(data.get('copied_engine_bytes'),312*8,65536,'copied engine size')
    absent=data['absent']
    if (type(absent.get('iterations')) is not int or absent['iterations']!=iterations
            or type(absent.get('observed_count')) is not int or absent['observed_count']!=0
            or absent.get('output_unchanged') is not True or absent.get('initialized_after') is not False
            or state(absent['before'])!=state(absent['after'])):
        raise ValueError('Absent snapshot initialized RNG or changed output')
    trials=data['trials']
    if len(trials)!=3: raise ValueError('Three complete trials required')
    costs=[];previous=None
    for index,row in enumerate(trials,1):
        if (type(row.get('trial')) is not int or row['trial']!=index
                or type(row.get('iterations')) is not int or row['iterations']!=iterations
                or type(row.get('observed_count')) is not int or row['observed_count']!=iterations):
            raise ValueError('Incomplete/duplicate trial or unavailable initialized snapshot')
        elapsed=integer(row.get('elapsed_ns'),1,2**63-1,'elapsed nanoseconds')
        before,after,copied=state(row['before']),state(row['after']),state(row['copied'])
        if before!=after or copied!=after or (previous is not None and previous!=before):
            raise ValueError('Live RNG changed, copied state differs or trial continuity broken')
        previous=after
        costs.append(dict(trial=index,elapsed_ns=elapsed,iterations=iterations,ns_per_snapshot=elapsed/iterations))
    control=data['control']
    if sum(r['elapsed_ns'] for r in costs)>limit_ms*1000000:
        raise ValueError('Completed trial timings exceed requested time budget')
    if (type(control.get('real_live_rand_draws')) is not int or control['real_live_rand_draws']!=1
            or state(control['before'])!=previous or state(control['before'])==state(control['after'])):
        raise ValueError('Real RAND draw control absent, disconnected or undetected')
    return dict(validated=True,absent_calls=iterations,initialized_calls=iterations*3,copied_engine_bytes=size,
                trials=costs,calling_thread_live_rng_preserved_during_trials=True,real_rand_control_detected=True,
                timing_scope='Imported Debug snapshot API copy loop plus loop/counter overhead; no serialization/file IO/frame cost',
                performance_threshold_applied=False,other_threads_or_combat_performance_proven=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('build','run'))
    for name in ('project-root','engine-source-root','engine-build-root','prefix','results-root'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--build-receipt',type=Path)
    parser.add_argument('--iterations',type=int,default=100000)
    parser.add_argument('--time-limit-ms',type=int,default=30000)
    parser.add_argument('--timeout',type=int)
    args=parser.parse_args()
    for name,value in vars(args).items():
        if isinstance(value,Path): setattr(args,name,value.resolve())
    if not 1<=args.iterations<=MAX_ITERATIONS or not 1<=args.time_limit_ms<=60000:
        parser.error('iterations must be1..1000000; time-limit-ms1..60000')
    timeout=args.timeout if args.timeout is not None else (180 if args.mode=='build' else 90)
    if not 1<=timeout<=(600 if args.mode=='build' else 120): parser.error('Owned timeout outside bound')
    if args.mode=='run' and not args.build_receipt: parser.error('run requires --build-receipt')
    source,build=args.engine_source_root,args.engine_build_root
    if any(args.results_root.is_relative_to(p) for p in (source,build)):
        parser.error('Private results must be outside source and build roots')
    if source==args.project_root/'gemrb' or build==args.project_root/'phase0-local/build':
        parser.error('Use separate candidate source/build roots; preserve accepted Phase0')
    helper=load(HERE/'menu_harness.py','rng_cost_owned_helper')
    common=load(HERE/'paired_ai_live.py','rng_cost_inventory_helper')
    baseline=load(args.project_root/'tools/phase0/baseline_runner.py','rng_cost_baseline_guard')
    out=args.results_root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-rng-cost-'+args.mode+'-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    report=dict(schema='bg-redux-rng-cost-'+args.mode+'/1',passed=False,directory=str(out),mode=args.mode)
    before=candidate=None;pins={}
    try:
        report['phase0_preflight']=baseline.preflight(args.project_root)
        before=baseline.protected(args.project_root);write(out/'phase0-before.json',before)
        candidate=common.candidate_inventory(source,build);write(out/'candidate-before.json',candidate)
        report['candidate_inventory_sha256']=common.sha(out/'candidate-before.json')
        cache=build/'CMakeCache.txt'
        config=cache.read_text(encoding='utf-8-sig')
        if not re.search(r'^CMAKE_BUILD_TYPE:[^=]+=Debug$',config,re.M):
            raise ValueError('Cost report requires the receipt-bound Debug CMake build')
        compiler=args.prefix/'bin/g++.exe'
        files=[Path(__file__),HERE/'native/rng_snapshot_cost.cpp',HERE/'menu_harness.py',HERE/'private_game.py',
               HERE/'paired_ai_live.py',args.project_root/'tools/phase0/baseline_runner.py',compiler,cache,
               build/'config.h',build/'gemrb/libgemrb_core.dll',build/'gemrb/core/libgemrb_core.dll.a',
               source/'gemrb/core/RNG.h',source/'gemrb/core/RNG.cpp',source/'gemrb/core/Logging/Logging.h']
        pins={str(p.resolve()):common.sha(p) for p in files}
        report['pins']=dict(pins)
        for path,digest in pins.items():
            common.freeze(path,out/'inputs'/digest/Path(path).name,digest)
        env=os.environ.copy();env['PATH']=os.pathsep.join([str(args.prefix/'bin'),str(build/'gemrb'),env.get('PATH','')])
        profile=out/'profile';profile.mkdir()
        env.update(HOME=str(profile),USERPROFILE=str(profile),APPDATA=str(profile/'AppData/Roaming'),PYTHONDONTWRITEBYTECODE='1')
        if args.mode=='build':
            cpp=HERE/'native/rng_snapshot_cost.cpp'
            frozen=out/'inputs'/pins[str(cpp.resolve())]/cpp.name
            binary=out/'Redux_rng_snapshot_cost.exe'
            command=[str(compiler),'-std=gnu++17','-g','-O0','-pthread','-DHAVE_CONFIG_H','-DUSE_OPENGL_API',
                '-D_USE_MATH_DEFINES','-DFMT_HEADER_ONLY','-DFMT_USE_CONSTEVAL=0','-DFMT_EXCEPTIONS=0',
                '-DFMT_UNICODE=1','-fno-strict-aliasing']
            for inc in (build,source/'gemrb/includes',source/'gemrb/core',source/'platforms/Windows',
                        build/'gemrb/includes',args.prefix/'include/SDL2',args.prefix/'include/python3.14',source/'includes/fmt'):
                command+=['-I',str(inc)]
            command+=[str(frozen),str(build/'gemrb/core/libgemrb_core.dll.a'),str(args.prefix/'lib/libiconv.dll.a'),'-lshlwapi','-o',str(binary)]
            report['process']=helper.run_owned(command,out,env,out/'build.log',timeout)
            if report['process']['exit_code']!=0 or report['process']['timed_out'] or not report['process']['cleanup_complete']:
                raise ValueError('External microbenchmark compilation failed/incomplete')
            report.update(binary=str(binary),binary_sha256=common.sha(binary),passed=True)
        else:
            receipt=read(args.build_receipt)
            pins[str(args.build_receipt)]=common.sha(args.build_receipt)
            if receipt.get('schema')!='bg-redux-rng-cost-build/1' or receipt.get('passed') is not True or receipt.get('pins')!=report['pins']:
                raise ValueError('Successful build receipt/current candidate or tool/compiler inputs differ')
            historical_inventory=Path(receipt['directory'])/'candidate-before.json'
            if (common.sha(historical_inventory)!=receipt.get('candidate_inventory_sha256')
                    or read(historical_inventory)!=candidate):
                raise ValueError('Candidate source/binary inventory differs from external host build')
            pins[str(historical_inventory)]=receipt['candidate_inventory_sha256']
            common.freeze(historical_inventory,out/'build-candidate-inventory.json',receipt['candidate_inventory_sha256'])
            binary=Path(receipt['binary']);pins[str(binary)]=receipt['binary_sha256']
            common.freeze(binary,out/'Redux_rng_snapshot_cost.exe',receipt['binary_sha256'])
            common.freeze(args.build_receipt,out/'build-receipt.json',pins[str(args.build_receipt)])
            nonce=uuid.uuid4().hex;raw=out/'native.json'
            command=[str(out/'Redux_rng_snapshot_cost.exe'),'--output',str(raw),'--nonce',nonce,
                     '--iterations',str(args.iterations),'--time-limit-ms',str(args.time_limit_ms)]
            report.update(nonce=nonce,iterations=args.iterations,time_limit_ms=args.time_limit_ms,command=command)
            write(out/'preparation.json',report);started=time.time_ns()
            report['process']=helper.run_owned(command,out,env,out/'process.log',timeout)
            process=report['process']
            if process['exit_code']!=0 or process['timed_out'] or not process['cleanup_complete']:
                raise ValueError('Owned benchmark failed/timed out/incomplete')
            if raw.stat().st_mtime_ns<started: raise ValueError('Stale native result')
            report['observation']=validate_capture(read(raw),nonce,process['owned_pid'],args.iterations,args.time_limit_ms)
            report.update(native_sha256=common.sha(raw),passed=True)
    except Exception as error:
        report['error']=str(error)
    finally:
        try:
            if before is not None:
                after=baseline.protected(args.project_root);write(out/'phase0-after.json',after)
                report['phase0_preserved']=before==after
                if before!=after: raise ValueError('Protected Phase0 inputs changed')
            if candidate is not None:
                after=common.candidate_inventory(source,build);write(out/'candidate-after.json',after)
                report['candidate_preserved']=candidate==after
                if candidate!=after: raise ValueError('Candidate source/binaries changed')
            if any(common.sha(path)!=digest for path,digest in pins.items()): raise ValueError('Tool/compiler/build input pin drift')
            report['bound_inputs_preserved']=bool(pins)
        except Exception as error:
            report.update(passed=False,preservation_error=str(error))
        write(out/'build.json' if args.mode=='build' else out/'result.json',report)
        write(out/'artifact-manifest.json',helper.artifact_manifest(out))
    print(json.dumps(dict(directory=str(out),passed=report['passed'])))
    return 0 if report['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
