"""External TextArea regression build/run; importing never launches.

Freeze canonical helpers from the explicit declared roots at build time.
Historical private packages/receipts remain separate and unchanged.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, time, uuid
from datetime import datetime, timezone
from pathlib import Path
import textarea_selection_validation as contracts
from textarea_selection_validation import CASES, EXPECTED, native_contract, owned_terminal, case_inventory

HERE=Path(__file__).resolve().parent
SCHEMA='bg-redux-textarea-selection-build/1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,r):Path(p).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
def require(v,s):
 if not v:raise ValueError(s)
def files(p):
 return {x.relative_to(p).as_posix():dict(bytes=x.stat().st_size,sha256=sha(x))for x in sorted(Path(p).rglob('*'))if x.is_file()}
def fresh(base,label):
 p=Path(base)/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+label+'-'+uuid.uuid4().hex[:8]);p.mkdir(parents=True,exist_ok=False);return p
def frozen(p,target):
 target.parent.mkdir(parents=True,exist_ok=True);before=sha(p);shutil.copy2(p,target);require(sha(target)==before==sha(p),'Freeze drift '+str(p));return dict(source=str(p),frozen=str(target),sha256=before)

def canonical_helpers(p,s):
 return {'gui_probe.cpp':p/'tools/phase0/native/gui_probe.cpp',
         'save_probe.cpp':p/'tools/phase0/native/save_probe.cpp',
         'ReduxStart.py':p/'tools/phase0/gui/ReduxStart.py',
         'textarea_selection_regression.h':s/'redux/tools/phase1/native/textarea_selection_regression.h'}

def engine_source_inventory(s):
 names=subprocess.check_output(['git','-C',str(s),'ls-files','--cached','--others','--exclude-standard','-z'])
 return {name:sha(s/name)for name in names.decode('utf-8').split('\0')if name and not name.startswith('redux/')and(s/name).is_file()}

def engine_binary_inventory(b):
 return {x.relative_to(b).as_posix():sha(x)for x in sorted((b/'gemrb').rglob('*'))if x.is_file()and(x.suffix.lower()in('.dll','.exe')or x.name=='libgemrb_core.dll.a')}

def check_engine_receipt(s,b):
 receipt=read(b/'build-receipt.json')
 require(receipt.get('schema')=='bg-redux-phase1-build/1'and receipt.get('status')=='built-not-validated'and
         Path(receipt['source']).resolve()==s and Path(receipt['directory']).resolve()==b and
         receipt.get('source_unchanged_during_build')is True and receipt.get('build_support_unchanged')is True and
         receipt.get('phase0_preservation')==dict(source=True,binaries=True,fixture=True),
         'Successful preserved source-bound engine build receipt required')
 require(bool(receipt['source_files'])and engine_source_inventory(s)==receipt['source_files'],'Complete current engine source differs from build receipt')
 required={'gemrb/libgemrb_core.dll','gemrb/core/libgemrb_core.dll.a'}
 require(required.issubset(receipt['binaries'])and engine_binary_inventory(b)==receipt['binaries'],'Complete engine binary inventory differs from receipt')
 support=[s/'redux/tools/phase1/cmake/managed-tests.cmake',s/'redux/tools/phase0/managed-test-main.cpp',*sorted((s/'redux/tools/phase0/cmake').glob('*.cmake'))]
 require(set(receipt['build_support_files'])=={x.relative_to(s).as_posix()for x in support},'Engine compiled support inventory differs')
 for name,digest in receipt['build_support_files'].items():
  require(sha(s/name)==digest==sha(b/'build-support'/name),'Engine source/frozen compiled support differs: '+name)
 return receipt
def load(a):
 p,s,b=(getattr(a,k).resolve()for k in ('project_root','source_root','build_root'))
 require(s!=(p/'gemrb').resolve()and b!=(p/'phase0-local/build').resolve(),'Separate candidate required')
 require((s/'gemrb/core/Interface.cpp').is_file()and(b/'gemrb/libgemrb_core.dll').is_file(),'Candidate source/build missing')
 require(HERE.resolve()==s/'redux/tools/phase1','Invoke the tool from its declared candidate source root')
 require(Path(contracts.__file__).resolve()==HERE/'textarea_selection_validation.py','Selection contract module escaped source')
 check_engine_receipt(s,b)
 sys.path.insert(0,str(s/'redux/tools/phase1'))
 import weapon_query_observer as shared
 import saved_npc_color_journey as common
 api=shared.phase0(p)
 require(Path(shared.__file__).resolve().parent==s/'redux/tools/phase1'and Path(common.__file__).resolve().parent==s/'redux/tools/phase1','Shared module escaped source')
 return p,s,b,shared,common,api
def closure(p,s,b):
 rows={Path(__file__),HERE/'textarea_selection_validation.py',HERE/'native/textarea_selection_probe.cpp',
       HERE/'native/textarea_unnumbered_selection_regression.h',HERE/'tests/test_textarea_selection_journey.py',
       *canonical_helpers(p,s).values()}
 for module in tuple(sys.modules.values()):
  raw=getattr(module,'__file__',None)
  if not raw:continue
  path=Path(raw).resolve()
  if path.suffix=='.py'and(path.is_relative_to(p/'tools/phase0')or path.is_relative_to(s/'redux/tools/phase1')):rows.add(path)
 rows.update(s/'gemrb'/name for name in ('core/GUI/TextArea.cpp','core/GUI/TextArea.h','core/GUI/Control.cpp','core/GUI/Control.h','core/GUI/TextSystem/TextContainer.cpp','core/GUI/TextSystem/TextContainer.h','core/GUI/Window.cpp','core/Strings/StringMap.h'))
 rows.update(s/name for name in read(b/'build-receipt.json')['build_support_files'])
 return sorted(rows)
def check_sources(r):
 for name,row in r['sources'].items():require(sha(name)==row['sha256']==sha(row['frozen']),'Source closure drift '+name)
def finish(r,out,p,s,b,shared,api,before,candidate):
 if before is not None:
  after=api.baseline_runner.protected(p);write(out/'phase0-after.json',after);r['phase0_preservation']={k:before[k]==after[k]for k in before};require(all(r['phase0_preservation'].values()),'Phase0 changed')
 if candidate is not None:
  after=shared.candidate_inventory(s,b);write(out/'candidate-after.json',after);r['candidate_preserved']=candidate==after;require(r['candidate_preserved'],'Candidate changed')
  check_engine_receipt(s,b);r['build_inventory_preserved']=True
 if 'sources'in r:check_sources(r)
def build(a):
 p,s,b,shared,common,api=load(a)
 out=a.output_dir.resolve();require(out.is_relative_to(p/'phase1-local')and not out.is_relative_to(s)and not out.is_relative_to(b),'Separate private output required');out.mkdir(parents=True,exist_ok=False)
 r=dict(schema=SCHEMA,status='failed',project=str(p),source=str(s),build=str(b));before=candidate=None
 try:
  r['preflight']=api.baseline_runner.preflight(p);before=api.baseline_runner.protected(p);candidate=shared.candidate_inventory(s,b);write(out/'phase0-before.json',before);write(out/'candidate-before.json',candidate)
  r['sources']={str(x):frozen(x,out/'sources'/sha(x)/x.name)for x in closure(p,s,b)+[b/'build-receipt.json']}
  r['canonical_helpers']={name:dict(source=str(path),sha256=sha(path))for name,path in canonical_helpers(p,s).items()}
  compiled=out/'compiled';compiled.mkdir()
  helpers=canonical_helpers(p,s)
  raw=helpers['gui_probe.cpp'].read_bytes();require(raw.count(b'int main(')==1,'Expected exactly one helper main')
  (compiled/'gui_helpers.cpp').write_bytes(raw.replace(b'int main(',b'int FrozenUnusedTextAreaGuiMain('))
  for src in (HERE/'native/textarea_selection_probe.cpp',HERE/'native/textarea_unnumbered_selection_regression.h',helpers['save_probe.cpp'],helpers['textarea_selection_regression.h']):frozen(src,compiled/src.name)
  r['compiled_files']=files(compiled)
  prefix=p/'phase0-local/toolchain/msys64/ucrt64';cc=prefix/'bin/g++.exe';exe=out/'Redux_textarea_selection.exe'
  r.update(compiler=str(cc),compiler_sha256=sha(cc),cmake_sha256=sha(b/'CMakeCache.txt'),candidate_inventory=candidate)
  cmd=[str(cc),'-std=gnu++17','-g','-O0','-DHAVE_CONFIG_H','-DUSE_OPENGL_API','-D_USE_MATH_DEFINES','-DFMT_HEADER_ONLY','-DFMT_USE_CONSTEVAL=0','-DFMT_EXCEPTIONS=0','-DFMT_UNICODE=1','-fno-strict-aliasing']
  for include in (b,s/'gemrb/includes',s/'gemrb/core',s/'platforms/Windows',b/'gemrb/includes',prefix/'include/SDL2',prefix/'include/python3.14',s/'gemrb/includes/fmt'):cmd+=['-I',str(include)]
  cmd+=[str(compiled/'textarea_selection_probe.cpp'),str(b/'gemrb/core/libgemrb_core.dll.a'),str(prefix/'lib/libiconv.dll.a'),'-lshlwapi','-o',str(exe)]
  env=os.environ.copy();env['PATH']=str(prefix/'bin')+os.pathsep+env.get('PATH','')
  r['compile']=api.baseline_runner.execute(cmd,b,env,out/'compile.log',a.timeout);shared.require_process(r['compile'])
  require(sha(cc)==r['compiler_sha256']and sha(b/'CMakeCache.txt')==r['cmake_sha256'],'Compiler/cache changed during compilation')
  r.update(binary=str(exe),binary_sha256=sha(exe),status='built-not-executed');check_sources(r);check_engine_receipt(s,b)
 except Exception as error:r.update(status='failed',error=str(error))
 finally:
  try:finish(r,out,p,s,b,shared,api,before,candidate)
  except Exception as error:r.update(status='failed',preservation_error=str(error))
  write(out/'build.json',r);write(out/'artifact-manifest.json',dict(files=common.output_manifest(out)))
 print(out/'build.json');return int(r['status']!='built-not-executed')
def check_build(path,p,s,b,shared):
 r=read(path);require(r['schema']==SCHEMA and r['status']=='built-not-executed'and[r[k]for k in ('project','source','build')]==list(map(str,(p,s,b))),'Wrong/failed build')
 check_sources(r);check_engine_receipt(s,b)
 require(r['canonical_helpers']=={name:dict(source=str(original),sha256=sha(original))for name,original in canonical_helpers(p,s).items()},'Canonical helper identity changed')
 require(r['phase0_preservation']==dict(source=True,binaries=True,fixture=True)and r['candidate_preserved'],'Build preservation')
 require(sha(r['binary'])==r['binary_sha256']and sha(r['compiler'])==r['compiler_sha256']and sha(b/'CMakeCache.txt')==r['cmake_sha256'],'Binary/compiler/cache drift')
 require(shared.candidate_inventory(s,b)==r['candidate_inventory']and files(Path(path).parent/'compiled')==r['compiled_files'],'Candidate/compiled drift')
 return r
def validate_capture(stage,case,nonce,process):
 cap=stage/'capture';host=read(cap/'host-result.json');require(host['schema']=='bg-redux-textarea-host/1'and host['case']==case and host['nonce']==nonce and host['calls']==1 and host['completed']and not host['error'],'Native host incomplete/failed')
 require(process['exit_code']==0 and not process['timed_out'],'Native process failed')
 dispatch=read(cap/'dispatch.json');require(dispatch['case']==case and dispatch['nonce']==nonce and dispatch['calls']==1 and dispatch['normal_load']and dispatch['paused'],'Dispatch evidence')
 before,after=read(cap/'before.state.json'),read(cap/'after.state.json');dictionary_before,dictionary_after=read(cap/'before.dictionary.json'),read(cap/'after.dictionary.json')
 require(before==after and dictionary_before==dictionary_after and host['world_equal']and host['dictionary_equal'],'Collected state/dictionary mutation')
 directory=cap/('textarea-selection-'+case);begin=read(directory/'begin.json');result=read(directory/'result.json')
 require(begin['case']==case and begin['option_values']==[10,40]and begin['visible_index']==1 and begin['value_change_before_select_required'],'Fixture entry missing')
 events=[json.loads(line)for line in(directory/'events.jsonl').read_text(encoding='utf-8').splitlines()]if(directory/'events.jsonl').exists()else[]
 contract=native_contract(case,result,events)
 return dict(result=result,independent_contract=contract,world_equal=True,dictionary_equal=True,normal_load=True,os_input=False,gameplay_acceptance=False)
def run(a):
 p,s,b,shared,common,api=load(a);require(a.results_root.resolve().is_relative_to(p/'phase1-local/results'),'Private results required')
 selected=CASES if a.case=='all'else(a.case,)
 out=fresh(a.results_root.resolve(),'textarea-selection');r=dict(schema='bg-redux-textarea-selection-run/1',passed=False,declared_cases=list(CASES),declared_count=15,requested_cases=list(selected),requested_count=len(selected),independent_expected={k:dict(events=v[0],value=v[1])for k,v in EXPECTED.items()},stages=[]);before=candidate=None;private=None;immutable=[];wrappers=[]
 try:
  require(out.is_relative_to(p/'phase1-local/results'),'Private results required');r['preflight']=api.baseline_runner.preflight(p);before=api.baseline_runner.protected(p);candidate=shared.candidate_inventory(s,b);write(out/'phase0-before.json',before);write(out/'candidate-before.json',candidate)
  receipt=check_build(a.host_build.resolve(),p,s,b,shared);driver=out/'driver';driver.mkdir();frozen(a.host_build.resolve(),driver/'build.json');host=driver/'Redux_textarea_selection.exe';frozen(Path(receipt['binary']),host)
  for name,row in receipt['sources'].items():frozen(Path(row['frozen']),driver/'sources'/row['sha256']/Path(name).name)
  shutil.copytree(a.host_build.resolve().parent/'compiled',driver/'compiled')
  startup=driver/'startup';startup.mkdir();frozen(Path(receipt['sources'][str(canonical_helpers(p,s)['ReduxStart.py'])]['frozen']),startup/'ReduxStart.py');driver_pin=files(driver);r['driver_files']=driver_pin
  fixture=p/'phase0-local/fixtures/original-bg2ee-20261020/GemRB';input_files=files(fixture);r['input_files']=input_files
  for case in selected:
   stage=out/case;stage.mkdir();entry=dict(case=case,passed=False,nonce=uuid.uuid4().hex);r['stages'].append(entry)
   copied=stage/'profile/save/000000007-HarnessInput';shutil.copytree(fixture,copied);require(files(copied)==input_files,'Fixture copy differs');immutable.append((copied,input_files))
   private=shared.prepare_private_game(p,stage);wrappers.append((private,stage))
   for name in ('cache','capture','override'):(stage/name).mkdir()
   config=dict(GameType='bg2ee',GamePath=private['game'],GemRBPath=s/'gemrb',PluginsPath=b/'gemrb/plugins',CachePath=stage/'cache',SavePath=stage/'profile',ModPath=stage/'override',UseAsLibrary=0,SaveAsOriginal=1,Width=1024,Height=768,FullScreen=0,CapFPS=30,AudioDriver='none',GameLanguagePath='lang/en_US',SkipIntroVideos=1,Logging=1,LogColor=0,PathfinderThreadsCount=0,PathfinderMainThreadMode='immediate')
   cfg=stage/'probe.cfg';cfg.write_text(''.join('%s=%s\n'%(k,str(v).replace('\\','/'))for k,v in config.items()),encoding='utf-8');cfg_pin=sha(cfg);immutable.append((cfg,cfg_pin))
   env=api.harness.environment(stage);env['PATH']=os.pathsep.join([str(b/'gemrb'),str(p/'phase0-local/toolchain/msys64/ucrt64/bin'),env.get('PATH','')]);env['PYTHONDONTWRITEBYTECODE']='1'
   check_build(a.host_build.resolve(),p,s,b,shared);require(files(driver)==driver_pin,'Launch closure drift');shared.validate_private_game(private,stage)
   cmd=[str(host),'--config',str(cfg),'--output',str(stage/'capture'),'--scripts',str(startup),'--case',case,'--nonce',entry['nonce']]
   started=time.time_ns();entry['process']=api.baseline_runner.execute(cmd,b,env,stage/'process.log',90)
   # This comes from the pinned runner's owned Popen.wait, not a reused PID
   # query or an invented cleanup_complete property. A nonzero crash exit is
   # terminal evidence, while remaining an execution/contract failure.
   entry['terminal']=owned_terminal(entry['process'],cmd);write(stage/'owned-terminal.json',entry['terminal'])
   entry['execution_outcome']='timeout'if entry['process']['timed_out']else('native-process-failure'if entry['process']['exit_code']!=0 else'completed-process')
   entry['private_game_validation']=shared.validate_private_game(private,stage)
   require(files(fixture)==input_files==files(copied)and sha(cfg)==cfg_pin and files(stage/'override')=={},'Fixture/config/override drift')
   # Retain each failure, including assert/crash/timeout prefixes, then continue
   # only after bounded execution and preservation checks have returned.
   try:
    require(all(x.stat().st_mtime_ns>=started for x in(stage/'capture').rglob('*')if x.is_file()),'Stale native evidence')
    require('Traceback (most recent call last)'not in(stage/'process.log').read_text(encoding='utf-8',errors='replace'),'Startup traceback')
    entry['observation']=validate_capture(stage,case,entry['nonce'],entry['process']);entry['passed']=True;entry['execution_outcome']='passed'
   except Exception as error:entry['error']=str(error)
   check_build(a.host_build.resolve(),p,s,b,shared);private=None
   require(entry['process'].get('exit_code')is not None,'Owned process still pending; batch stopped')
  r['inventory']=case_inventory(selected,r['stages']);r['passed']=r['inventory']['passed']
 except Exception as error:r.update(passed=False,error=str(error))
 finally:
  try:
   if private is not None:shared.validate_private_game(private,stage)
   for wrapper,folder in wrappers:shared.validate_private_game(wrapper,folder)
   for path,expected in immutable:require((files(path)if path.is_dir()else sha(path))==expected,'Final immutable input drift')
   if 'input_files'in locals():require(files(fixture)==input_files,'Final source fixture drift')
   if 'receipt'in locals():check_build(a.host_build.resolve(),p,s,b,shared)
   if 'driver_pin'in locals():require(files(driver)==driver_pin,'Final launch closure drift')
   finish(r,out,p,s,b,shared,api,before,candidate);r['inputs_preserved']=True
  except Exception as error:r.update(passed=False,preservation_error=str(error))
  try:r['inventory']=case_inventory(selected,r['stages'])
  except Exception as error:r.update(passed=False,inventory_error=str(error))
  r['attempted_cases']=[x['case']for x in r['stages']];r['executed_cases']=[x['case']for x in r['stages']if type(x.get('process',{}).get('pid'))is int];r['missing_cases']=[x for x in selected if x not in r['executed_cases']];r['all_requested_executed']=r['executed_cases']==list(selected);r['all_owned_terminal']=all(x.get('terminal',{}).get('terminal')is True for x in r['stages']if type(x.get('process',{}).get('pid'))is int)
  write(out/'result.json',r);write(out/'artifact-manifest.json',dict(files=common.output_manifest(out)))
 print(out/'result.json');return int(not r['passed'])
def main():
 parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
 for mode in ('build','run'):
  q=sub.add_parser(mode)
  for option in ('project-root','source-root','build-root'):q.add_argument('--'+option,type=Path,required=True)
  if mode=='build':q.add_argument('--output-dir',type=Path,required=True);q.add_argument('--timeout',type=int,default=180)
  else:q.add_argument('--host-build',type=Path,required=True);q.add_argument('--results-root',type=Path,required=True);q.add_argument('--case',choices=('all',)+CASES,required=True)
 a=parser.parse_args()
 if a.command=='build'and not 1<=a.timeout<=300:parser.error('Compile timeout must be 1..300 seconds')
 return build(a)if a.command=='build'else run(a)
if __name__=='__main__':raise SystemExit(main())
