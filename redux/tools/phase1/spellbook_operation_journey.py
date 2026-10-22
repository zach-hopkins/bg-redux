"""Separate external stock-caster spellbook operation and ordinary save/reload journey."""
import argparse
import copy
import os
from pathlib import Path
import shutil
import struct
import sys
import time
import uuid
import minsc_recruitment_journey as checkpoint
import spell_cast_journey as tables
import saved_npc_color_journey as common
import saved_npc_color_fixtures as binary
import weapon_query_observer as shared
import weapon_query_validation as evidence
import spellbook_operation_validation as v
import spellbook_presentation_control as presentation
HERE=Path(__file__).resolve().parent
KIND='bg-redux-spellbook-operation-host/1'
PARENT='20261022T075243Z-minsc-recruitment-072650e1'
PARENT_RESULT='93401ec89b0896ae8c69a846f81314afec75a69af9e62b173fdcd7c4ea8c8e6c'
PARENT_MANIFEST='cad14881c5aef6ef19d2396aa6ba68cc98be8855c94ddb92143ee7b78fb98252'
PARENT_GAM='31ed55776f08f3ef8b351b3eda8de02cda32dd6926fbb05a0808888d75070b7a'
PARENT_SAV='ab927d4f5de8a8b707a964d51c806da68360cc5d1771f77c2d8fd4ee1f2d9754'
check_engine_receipt=checkpoint.check_engine_receipt
save_manifest=checkpoint.save_manifest

def build_host(args):
    project,source,build=(getattr(args,k).resolve() for k in ('project_root','engine_source_root','engine_build_root'))
    root_guard(project,source,build)
    if not 1<=args.timeout<=300:raise ValueError('Bounded external compile timeout required')
    out=args.output_dir.resolve()
    if not out.is_relative_to(project/'phase1-local') or any(out.is_relative_to(p) for p in (source,build)):raise ValueError('Separate private external build root required')
    out.mkdir(parents=True,exist_ok=False);result=dict(schema=KIND,verdict='failed',project=str(project),source=str(source),build=str(build));api=before=candidate=None
    try:
        api=shared.phase0(project);result['preflight']=api.baseline_runner.preflight(project)
        before=api.baseline_runner.protected(project);candidate=shared.candidate_inventory(source,build)
        shared.write(out/'phase0-before.json',before);shared.write(out/'candidate-before.json',candidate)
        engine=check_engine_receipt(source,build);closure=sources(project,source)+[build/'build-receipt.json']+[source/name for name in engine['build_support_files']]
        result['sources']={str(p):shared.frozen_copy(p,out/'sources'/evidence.sha(p)/p.name)for p in sorted(set(closure))}
        result['engine_build_binding']=dict(receipt_sha256=evidence.sha(build/'build-receipt.json'),source_files=len(engine['source_files']),binaries=len(engine['binaries']),support_files=len(engine['build_support_files']))
        compiled=out/'compiled-sources';compiled.mkdir()
        for original in (project/'tools/phase0/native/save_probe.cpp',HERE/'native/spellbook_operation_journey.cpp',HERE/'native/spellbook_operation_ui_snapshot.cpp'):
            shared.frozen_copy(original,compiled/original.name)
        (compiled/'spellbook_gui_helpers.cpp').write_bytes(gui_helpers((project/'tools/phase0/native/gui_probe.cpp').read_bytes()))
        result['compiled_sources']=evidence.manifest(compiled)
        result['parent_proof']=parent_proof(project)
        result['resources']={}
        for name,row in resource_guard(api,project,source).items():
            result['resources'][name]={k:v for k,v in row.items() if k!='raw'}
            if 'raw'in row:
                target=out/'resources'/name;target.parent.mkdir(exist_ok=True);target.write_bytes(row['raw']);result['resources'][name]['frozen']=str(target)
        resource_list=out/'resource-list.txt';resource_list.write_text(''.join(row['extension']+' '+name.rsplit('.',1)[0]+'\n'for name,row in result['resources'].items()if 'frozen'in row),encoding='ascii');result['resource_list_sha256']=evidence.sha(resource_list)
        prefix=project/'phase0-local/toolchain/msys64/ucrt64';compiler=prefix/'bin/g++.exe';host=out/'Redux_spellbook_operations_gui.exe'
        compiler_sha=evidence.sha(compiler);cmake_sha=evidence.sha(build/'CMakeCache.txt')
        cmd=[str(compiler),'-std=gnu++17','-g','-O0','-DHAVE_CONFIG_H','-DUSE_OPENGL_API','-D_USE_MATH_DEFINES','-DFMT_HEADER_ONLY','-DFMT_USE_CONSTEVAL=0','-DFMT_EXCEPTIONS=0','-DFMT_UNICODE=1','-fno-strict-aliasing']
        for p in (build,source/'gemrb/includes',source/'gemrb/core',source/'platforms/Windows',build/'gemrb/includes',prefix/'include/SDL2',prefix/'include/python3.14',source/'gemrb/includes/fmt'):cmd+=['-I',str(p)]
        cmd+=[str(compiled/'spellbook_operation_journey.cpp'),str(build/'gemrb/core/libgemrb_core.dll.a'),str(prefix/'lib/libiconv.dll.a'),'-lshlwapi','-o',str(host)]
        env=os.environ.copy();env['PATH']=str(prefix/'bin')+os.pathsep+env.get('PATH','')
        result['process']=api.baseline_runner.execute(cmd,build,env,out/'build.log',args.timeout);shared.require_process(result['process'])
        if evidence.sha(compiler)!=compiler_sha or evidence.sha(build/'CMakeCache.txt')!=cmake_sha:raise ValueError('Compiler/CMake changed during build')
        result.update(binary=str(host),binary_sha256=evidence.sha(host),compiler=str(compiler),compiler_sha256=compiler_sha,
            cmake_sha256=cmake_sha,candidate_inventory=candidate,verdict='built-not-executed')
        source_guard(result,project,source);check_resources(result,api,project,source)
    except Exception as error:result.update(error=str(error),verdict='failed')
    finally:
        try:
            check_engine_receipt(source,build)
            common.finish_guards(result,out,project,source,build,api,before,candidate)
        except Exception as error:result.update(verdict='failed',preservation_error=str(error))
        shared.write(out/'build.json',result);shared.write(out/'artifact-manifest.json',dict(files=common.output_manifest(out)))
    print(out/'build.json',result['verdict']);return 0 if result['verdict']=='built-not-executed' else 1

def check_build(path,project,source,build):
    r=evidence.read(path)
    if r.get('schema')!=KIND or r.get('verdict')!='built-not-executed' or [r.get(k) for k in ('project','source','build')]!=list(map(str,(project,source,build))):raise ValueError('Wrong/failed recruitment host build')
    shared.require_process(r['process']);source_guard(r,project,source)
    if r.get('phase0_preservation')!=dict(source=True,binaries=True,fixture=True) or r.get('candidate_preserved')is not True:raise ValueError('Build preservation failed')
    if evidence.sha(r['binary'])!=r['binary_sha256'] or evidence.sha(r['compiler'])!=r['compiler_sha256'] or evidence.sha(build/'CMakeCache.txt')!=r['cmake_sha256']:raise ValueError('Driver/compiler/CMake drift')
    if shared.candidate_inventory(source,build)!=r['candidate_inventory'] or evidence.manifest(Path(path).parent/'compiled-sources')!=r['compiled_sources']:raise ValueError('Candidate/compiled source drift')
    if (Path(path).parent/'compiled-sources/spellbook_gui_helpers.cpp').read_bytes()!=gui_helpers((project/'tools/phase0/native/gui_probe.cpp').read_bytes()):raise ValueError('Frozen GUI helper derivation differs')
    if evidence.sha(Path(path).parent/'resource-list.txt')!=r['resource_list_sha256']:raise ValueError('Frozen resource list differs')
    check_resources(r,shared.phase0(project),project,source)
    return r

def run(args):
    project,source,build=(getattr(args,k).resolve() for k in ('project_root','engine_source_root','engine_build_root'))
    root_guard(project,source,build)
    if not args.results_root.resolve().is_relative_to(project/'phase1-local/results'):raise ValueError('Private Phase1 results root required')
    control_mode=getattr(args,'presentation_control','stock');label='spellbook-operation'if control_mode=='stock'else'spellbook-operation-name-control'
    out=shared.new_output(args.results_root.resolve(),label);result=dict(presentation_control=control_mode,schema='bg-redux-spellbook-operation-journey/1',passed=False,stages=[],original_parity=None)
    api=before=candidate=None;preserved=[];privates=[];pins={};override_pins=[];controls=[]
    try:
        api=shared.phase0(project);result['preflight']=api.baseline_runner.preflight(project)
        before=api.baseline_runner.protected(project);candidate=shared.candidate_inventory(source,build)
        shared.write(out/'phase0-before.json',before);shared.write(out/'candidate-before.json',candidate)
        receipt=check_build(args.host_build.resolve(),project,source,build);result['resources']={k:{f:v for f,v in row.items() if f!='raw'} for k,row in resource_guard(api,project,source).items()};result['parent_proof']=parent_proof(project)
        driver=out/'driver';driver.mkdir();host=driver/'Redux_spellbook_operations_gui.exe'
        shared.frozen_copy(Path(receipt['binary']),host);shared.frozen_copy(args.host_build.resolve(),driver/'build.json')
        for name,row in receipt['sources'].items():shared.frozen_copy(Path(row['frozen']),driver/'sources'/row['sha256']/Path(name).name)
        shutil.copytree(args.host_build.resolve().parent/'compiled-sources',driver/'compiled-sources')
        shutil.copytree(args.host_build.resolve().parent/'resources',driver/'resources')
        shared.frozen_copy(args.host_build.resolve().parent/'resource-list.txt',driver/'resource-list.txt')
        startup=driver/'startup';startup.mkdir();shared.frozen_copy(HERE/'SpellbookOperationStart.py',startup/'SpellbookOperationStart.py');shared.frozen_copy(HERE/'SpellbookOperationRuntime.py',startup/'SpellbookOperationRuntime.py')
        parent_dir=driver/'parent';parent_dir.mkdir()
        for name in ('result.json','artifact-manifest.json'):shared.frozen_copy(project/'phase1-local/results'/PARENT/name,parent_dir/name)
        driver_files=evidence.manifest(driver);result['driver_files']=driver_files
        incoming=project/'phase1-local/results'/PARENT/'recruit/frozen-save'
        result['initial_wire']=wire(incoming);initial=save_manifest(incoming,4);preserved.append((incoming,initial))
        for mode in ('operate','reload'):
            stage=out/mode;stage.mkdir();entry=dict(mode=mode,nonce=uuid.uuid4().hex,passed=False);result['stages'].append(entry)
            input_files=save_manifest(incoming,4);copied=stage/'profile/save/000000007-HarnessInput';shutil.copytree(incoming,copied)
            if binary.manifest(copied)!=input_files:raise ValueError('Copied measured input differs before launch')
            preserved.extend([(incoming,input_files),(copied,input_files)]);entry['input_files']=input_files
            private=shared.prepare_private_game(project,stage);privates.append((private,stage))
            for name in ('cache','capture','override'):(stage/name).mkdir()
            observed_receipt=receipt
            if control_mode==presentation.CONTROL:
                control=presentation.prepare(receipt,stage/'override');presentation.verify(control,receipt);controls.append(control)
                shared.write(stage/'presentation-control.json',control);entry['presentation_control']=control
                observed_receipt=dict(receipt,resources=control['resources'],presentation_control=presentation.CONTROL)
            override_pins.append((stage/'override',evidence.manifest(stage/'override')))
            config=dict(GameType='bg2ee',GamePath=private['game'],GemRBPath=source/'gemrb',PluginsPath=build/'gemrb/plugins',CachePath=stage/'cache',SavePath=stage/'profile',ModPath=stage/'override',UseAsLibrary=0,SaveAsOriginal=1,Width=1024,Height=768,FullScreen=0,CapFPS=30,AudioDriver='none',GameLanguagePath='lang/en_US',SkipIntroVideos=1,Logging=1,LogColor=0,PathfinderThreadsCount=0,PathfinderMainThreadMode='immediate')
            cfg=stage/'probe.cfg';cfg.write_text(''.join('%s=%s\n'%(k,str(v).replace('\\','/')) for k,v in config.items()),encoding='utf-8');pins[str(cfg)]=evidence.sha(cfg)
            command=[str(host),'--config',str(cfg),'--output',str(stage/'capture'),'--scripts',str(startup),'--mode',mode,'--nonce',entry['nonce'],'--resources',str(driver/'resource-list.txt')]
            env=api.harness.environment(stage);prefix=project/'phase0-local/toolchain/msys64/ucrt64';env['PATH']=os.pathsep.join([str(build/'gemrb'),str(prefix/'bin'),env.get('PATH','')]);env['PYTHONDONTWRITEBYTECODE']='1'
            source_guard(receipt,project,source);check_resources(receipt,api,project,source);parent_proof(project);shared.validate_private_game(private,stage)
            if evidence.manifest(driver)!=driver_files:raise ValueError('Frozen launch closure changed')
            started=time.time_ns();entry['process']=api.baseline_runner.execute(command,build,env,stage/'process.log',180 if mode=='operate'else 120)
            shared.require_process(entry['process'])
            if 'Traceback (most recent call last)' in (stage/'process.log').read_text(encoding='utf-8',errors='replace'):raise ValueError('Stock callback traceback')
            check_resources(receipt,api,project,source);parent_proof(project)
            entry['runtime_providers']=check_runtime_resources(stage/'capture',observed_receipt)
            entry['observation']=validate_capture(stage/'capture',entry['nonce'],mode,started,observed_receipt)
            if control_mode==presentation.CONTROL and not entry['observation']['nonidentity_sort_runtime']:raise ValueError('Declared presentation control did not produce actual nonidentity sorting')
            if mode=='operate':
                saved=Path(entry['observation']['save']).resolve()
                if not saved.is_relative_to((stage/'profile/save').resolve()) or saved==copied.resolve():raise ValueError('Output escaped profile/overwrote input')
                entry['wire']=wire(saved);wire_state_guard(entry['wire'],evidence.read(stage/'capture/final.state.json'));v.wire_delta_guard(result['initial_wire']['spellbooks'],entry['wire']['spellbooks']);files=save_manifest(saved,4);frozen=stage/'frozen-save';shutil.copytree(saved,frozen)
                if save_manifest(frozen,4)!=files:raise ValueError('Frozen GUI save drift')
                preserved.extend([(saved,files),(frozen,files)]);incoming=frozen;entry.update(frozen_save=str(frozen),frozen_save_files=files)
            else:
                entry['wire']=wire(copied);wire_state_guard(entry['wire'],evidence.read(stage/'capture/loaded.state.json'));wire_state_guard(entry['wire'],evidence.read(stage/'capture/final.state.json'))
                prior=evidence.read(out/'operate/capture/final.state.json');loaded=evidence.read(stage/'capture/loaded.state.json')
                if prior['journal']!=loaded['journal']:raise ValueError('Fresh-process reload changed journal fields')
                if entry['wire']!=result['stages'][0]['wire']:raise ValueError('Reload input wire differs from frozen operation output')
            entry['private_game_validation']=shared.validate_private_game(private,stage);entry['passed']=True
        if len({s['process']['pid'] for s in result['stages']})!=2:raise ValueError('Fresh-process ownership absent')
        result['passed']=True;result['coverage']=dict(actual_callbacks=True,arrow_tab_pixels=True,spellbook_wire_conservation=True,nonidentity_sort_runtime=all(s['observation']['nonidentity_sort_runtime']for s in result['stages']));result['verdict']='passed-private-presentation-control'if control_mode==presentation.CONTROL else'passed-with-runtime-sort-permutation-gap'
    except Exception as error:result.update(passed=False,error=str(error))
    finally:
        try:
            for folder,files in preserved:
                if binary.manifest(folder)!=files:raise ValueError('Immutable input/frozen output drift')
            for path,digest in pins.items():
                if evidence.sha(path)!=digest:raise ValueError('Config changed')
            for folder,manifest in override_pins:
                if evidence.manifest(folder)!=manifest:raise ValueError('Declared private override changed')
            for control in controls:presentation.verify(control,receipt)
            for private,stage in privates:shared.validate_private_game(private,stage)
            if 'receipt'in locals():check_build(args.host_build.resolve(),project,source,build)
            if 'driver_files'in locals() and evidence.manifest(driver)!=driver_files:raise ValueError('Frozen driver closure drift')
            if api is not None and 'receipt'in locals():check_resources(receipt,api,project,source);parent_proof(project)
            check_engine_receipt(source,build)
            common.finish_guards(result,out,project,source,build,api,before,candidate);result['inputs_preserved']=True
        except Exception as error:result.update(passed=False,preservation_error=str(error))
        shared.write(out/'result.json',result);shared.write(out/'artifact-manifest.json',dict(files=common.output_manifest(out)))
    print(out/'result.json',result['passed']);return 0 if result['passed'] else 1

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for mode in ('build','run'):
        q=sub.add_parser(mode)
        for name in ('project-root','engine-source-root','engine-build-root'):q.add_argument('--'+name,type=Path,required=True)
        if mode=='build':
            q.add_argument('--timeout',type=int,default=240);q.add_argument('--output-dir',type=Path,required=True)
        else:
            q.add_argument('--host-build',type=Path,required=True);q.add_argument('--results-root',type=Path,required=True);q.add_argument('--presentation-control',choices=('stock',presentation.CONTROL),default='stock')
    args=p.parse_args(argv)
    if args.command=='build' and not 1<=args.timeout<=300:p.error('Timeout must be bounded to 1..300 seconds')
    return build_host(args) if args.command=='build' else run(args)

def root_guard(project,source,build):
    if source==(project/'gemrb').resolve()or build==(project/'phase0-local/build').resolve():raise ValueError('Separate candidate source/build required')
    if HERE!=source/'redux/tools/phase1'or any(Path(m.__file__).resolve().parent!=HERE for m in (common,binary,shared,evidence,checkpoint,tables,v,presentation)):raise ValueError('Exact candidate adapter/dependency roots required')
    check_engine_receipt(source,build)

def sources(project,source):
    local=['spellbook_presentation_control.py','spellbook_operation_journey.py','spellbook_operation_validation.py','SpellbookOperationRuntime.py','SpellbookOperationStart.py','native/spellbook_operation_journey.cpp','native/spellbook_operation_ui_snapshot.cpp']
    result={HERE/name for name in local}|set(common.sources(project))
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if not filename:continue
        path=Path(filename).resolve()
        if path.suffix=='.py'and((path.is_relative_to(HERE)and not path.is_relative_to(HERE/'tests'))or path.is_relative_to(project/'tools/phase0')):result.add(path)
    for name in ['GUIScripts/GUIMG.py','GUIScripts/GUIPR.py','GUIScripts/Spellbook.py','GUIScripts/PortraitWindow.py','GUIScripts/GUICommonWindows.py','GUIScripts/GUICommon.py','GUIScripts/GUIClasses.py','GUIScripts/GUIDefines.py','GUIScripts/GUILOAD.py','GUIScripts/GUISAVE.py','GUIScripts/GUIOPT.py','core/Spellbook.cpp','core/Spellbook.h','core/GUI/Button.cpp','core/GUI/Button.h','core/GUI/Control.cpp','core/GUI/Control.h','core/GUI/View.cpp','core/GUI/View.h','plugins/CREImporter/CREImporter.cpp','plugins/GAMImporter/GAMImporter.cpp','plugins/GUIScript/GUIScript.cpp','unhardcoded/shared/spldisp.2da','unhardcoded/bg2ee/guibtact.2da']:result.add(source/'gemrb'/name)
    return sorted(result)

def source_guard(receipt,project,source):
    build=Path(receipt['build']);engine=check_engine_receipt(source,build);expected=set(map(str,sources(project,source)))|{str(build/'build-receipt.json')}|{str(source/name)for name in engine['build_support_files']}
    if set(receipt.get('sources',{}))!=expected:raise ValueError('Complete source/support closure differs')
    for name,row in receipt['sources'].items():
        if evidence.sha(name)!=row['sha256']or evidence.sha(row['frozen'])!=row['sha256']:raise ValueError('Current/frozen source drift')

def gui_helpers(raw):
    if raw.count(b'int main(')!=1 or b'#define REDUX_GUI_HOST'not in raw:raise ValueError('Exact GUI helper shape absent')
    return raw.replace(b'int main(',b'int FrozenUnusedSpellbookGuiMain(')

def parent_proof(project):
    root=project/'phase1-local/results'/PARENT
    if evidence.sha(root/'result.json')!=PARENT_RESULT or evidence.sha(root/'artifact-manifest.json')!=PARENT_MANIFEST:raise ValueError('Measured Minsc parent result/manifest differs')
    r=evidence.read(root/'result.json');rows=evidence.read(root/'artifact-manifest.json')['files']
    if r.get('schema')!='bg-redux-minsc-recruitment-journey/1'or not r.get('passed')or not r.get('candidate_preserved')or not r.get('inputs_preserved')or r.get('phase0_preservation')!=dict(source=True,binaries=True,fixture=True):raise ValueError('Accepted preserved parent proof absent')
    for name,row in rows.items():
        file=(root/name).resolve()
        if not file.is_relative_to(root.resolve())or file.stat().st_size!=row['bytes']or evidence.sha(file)!=row['sha256']:raise ValueError('Parent artifact drift/escape')
    stages=r['stages']
    if len(stages)!=2 or [s['journey']for s in stages]!=['recruit','reload']or not all(s['passed']for s in stages):raise ValueError('Measured parent save/reload incomplete')
    for stage in stages:shared.require_process(stage['process'])
    if stages[0]['process']['pid']==stages[1]['process']['pid']:raise ValueError('Parent reload not fresh')
    incoming=root/'recruit/frozen-save';files=save_manifest(incoming,4)
    if files!=stages[0]['frozen_save_files']or files!=stages[1]['input_files']or evidence.sha(common.member(incoming,'gam'))!=PARENT_GAM or evidence.sha(common.member(incoming,'sav'))!=PARENT_SAV:raise ValueError('Wrong parent frozen four-party save')
    p0=common.save_manifest(project/'phase0-local/fixtures/original-bg2ee-20261020/GemRB')
    if p0!=r['parent_proof']['phase0_fixture_files']:raise ValueError('Phase0 ancestor binding differs')
    checkpoint.wire(incoming,True);v.wire_spellbooks(incoming)
    return dict(parent=str(root),result_sha256=PARENT_RESULT,manifest_sha256=PARENT_MANIFEST,input=str(incoming),files=files,phase0_fixture_files=p0,artifact_count=len(rows))

def wire(folder):return dict(checkpoint=checkpoint.wire(folder,True),spellbooks=v.wire_spellbooks(folder))

def wire_state_guard(parsed,state):
    checkpoint.wire_state_guard(parsed['checkpoint'],state);return v.wire_state_guard(parsed['spellbooks'],state)

def tlk(project,refs):
    raw=(project/'phase0-local/bg2ee-clean/lang/en_US/dialog.tlk').read_bytes()
    if raw[:8]!=b'TLK V1  ':raise ValueError('English TLK version required')
    result={}
    for ref in refs:
        if not 0<=ref<binary.u32(raw,10):raise ValueError('TLK reference bounds')
        at=18+26*ref;result[ref]=binary.block(raw,binary.u32(raw,14)+binary.u32(raw,at+18),binary.u32(raw,at+22)).decode('utf8')
    return result

def resource_guard(api,project,source):
    game=project/'phase0-local/bg2ee-clean';wire_=v.wire_spellbooks(project/'phase1-local/results'/PARENT/'recruit/frozen-save');refs={r['resref']for actor in wire_[1:3]for page in actor['pages']if page['type']in(0,1)for r in page['known']};result={};cache={}
    specs=[(ref,'spl',1006)for ref in sorted(refs)]+[('guimg','chu',1002),('guipr','chu',1002),('spldisp','2da',1012),('guibtact','2da',1012)]
    for ref,ext,kind in specs:
        api.probe_ui_resources.TYPES[ext]=kind;policy=None
        if ext=='2da':raw,origin,policy=tables.table_provider(api,source,ref);provider=Path(origin)
        else:
            for category in ('override/bg2ee','override/shared','unhardcoded/bg2ee','unhardcoded/shared'):
                if (source/'gemrb'/category/(ref+'.'+ext)).exists():raise ValueError('Unexpected engine provider shadow')
            raw,origin=api.probe_ui_resources.read_resource(ref.lower(),ext);provider=(game/Path(origin.replace('\\','/'))).resolve()if origin else None
            if provider is None or not provider.is_relative_to(game.resolve()):raise ValueError('Declared resource provider absent/escape')
        if not raw or len(raw)>8*1024*1024:raise ValueError('Resource missing/bounds')
        key=str(provider)
        if key not in cache:cache[key]=evidence.sha(provider)
        row=dict(raw=raw,extension=ext,provider=key,provider_sha256=cache[key],sha256=binary.digest(raw),bytes=len(raw),origin=origin,policy=policy)
        if ext=='spl':
            if raw[:8]not in(b'SPL V1  ',b'SPL V2.0'):raise ValueError('Supported stock SPL required')
            row['spell_name_ref']=binary.u32(raw,8);row['spell_name']=tlk(project,[row['spell_name_ref']])[row['spell_name_ref']]
        result[ref+'.'+ext]=row
    for name,file in [('chitin',game/'chitin.key'),('tlk',game/'lang/en_US/dialog.tlk')]:result[name]=dict(path=str(file),bytes=file.stat().st_size,sha256=evidence.sha(file))
    result['level_template']=dict(value=tlk(project,[10345])[10345])
    return result

def check_resources(receipt,api,project,source):
    actual=resource_guard(api,project,source)
    if set(receipt.get('resources',{}))!=set(actual):raise ValueError('Resource closure missing/extra')
    for name,row in actual.items():
        expected=receipt['resources'][name]
        if {k:value for k,value in expected.items()if k!='frozen'}!={k:value for k,value in row.items()if k!='raw'}or 'frozen'in expected and evidence.sha(expected['frozen'])!=expected['sha256']:raise ValueError('Resource/source/provider drift: '+name)

def check_runtime_resources(folder,receipt):
    data=evidence.read(folder/'book-providers.json');expected={k:r for k,r in receipt['resources'].items()if 'frozen'in r}
    if data.get('schema')!='bg-redux-book-providers/1'or set(data.get('resources',{}))!=set(expected):raise ValueError('Actual runtime provider closure incomplete')
    for name,row in expected.items():
        actual=data['resources'][name]
        if Path(actual['originalfile']).resolve()!=Path(row['provider']).resolve()or actual['bytes']!=row['bytes']or evidence.sha(folder/(name+'.runtime'))!=row['sha256']:raise ValueError('Runtime provider/path/bytes differ')
    return data


def validate_capture(folder,nonce,mode,started_ns,receipt):
    host=evidence.read(folder/'book-result.json');runtime=evidence.read(folder/'book-runtime.json');plan=v.expected_plan(mode)
    if host.get('schema')!='bg-redux-book-host/1'or host.get('nonce')!=nonce or host.get('mode')!=mode or host.get('completed')is not True or host.get('error')or host.get('os_pointer_input')is not False or host.get('direct_spell_mutation')is not False:raise ValueError('Native spellbook host incomplete/stale/forced')
    if runtime.get('schema')!='bg-redux-book-runtime/1'or runtime.get('nonce')!=nonce or runtime.get('mode')!=mode or runtime.get('planned')!=plan or runtime.get('steps')!=len(plan)or runtime.get('completed')is not True:raise ValueError('Independent operation plan coverage incomplete')
    if started_ns is not None and any(p.stat().st_mtime_ns<started_ns for p in folder.iterdir()if p.is_file()):raise ValueError('Stale evidence capture')
    rows=runtime['rows'];events=host['events'];startup=host['startup']
    if len(rows)!=len(plan)or [r['step']for r in rows]!=list(range(len(plan)))or events!=evidence.read(folder/'book-events.json')or startup!=evidence.read(folder/'book-startup.json')or len(events)!=host['callbacks']:raise ValueError('Raw dispatch/startup continuity differs')
    if any(e['nonce']!=nonce or e['sequence']!=i+1 or e.get('performed')is not True for i,e in enumerate(events)):raise ValueError('Callback nonce/count/sequence differs')
    if events[0]['step']!=-1 or [events[0][k]for k in('pack','window','control')]!=['GUILOAD',0,26]:raise ValueError('Actual normal load callback missing')
    ready=evidence.read(folder/'ready.state.json');loaded=evidence.read(folder/'loaded.state.json');scene=evidence.read(folder/'ready.scene.json')
    evidence.require_state(ready)
    if len(ready['party'])!=4 or ready['current_area'].upper()!='AR0602'or scene['bd_defai']!=1 or scene['leader_class_script'].upper()!='BDDEFAI'or len(startup)<4 or any(not r['idle']for r in startup[-4:])or ready['game_time']<loaded['game_time']+30:raise ValueError('Natural normal-clock readiness not observed')
    if any(b['tick']<=a['tick']or b['game_time']<a['game_time']for a,b in zip(startup,startup[1:])):raise ValueError('Startup clock/order contradiction')
    for sample in startup:
        state=evidence.read(folder/(sample['checkpoint']+'.state.json'));actual=evidence.read(folder/(sample['checkpoint']+'.scene.json'))
        if sample['game_time']!=state['game_time']or actual['game_time']!=state['game_time']or sample['idle']!=actual['idle']or len(actual['party_actions'])!=4:raise ValueError('Readiness diagnostics contradict raw state')
    requests=[r for r in rows if r['event']=='request'];observations=[r for r in rows if r['event']=='observe'];dispatched=[e for e in events if e['step']>=0]
    if len(dispatched)!=len(requests)or any(e['step']!=r['step']or[e[k]for k in('pack','window','control')]!=[r[k]for k in('pack','window','control')]or e['actual_value']!=r['value']for r,e in zip(requests,dispatched)):raise ValueError('Actual registered callback differs from requested bound control')
    spell_names={name.rsplit('.',1)[0].upper():dict(name=row['spell_name'])for name,row in receipt['resources'].items()if row.get('extension')=='spl'};template=receipt['resources']['level_template']['value'];captures={};pixel_rows={};nonidentity=False
    for i,row in enumerate(observations,1):
        if row['capture']!=i or row['name']!=plan[row['step']]:raise ValueError('Observation inventory/name mismatch')
        meta=evidence.read(folder/('capture-%d.book.json'%i));state=evidence.read(folder/('capture-%d.state.json'%i));ui=evidence.read(folder/('capture-%d.ui.json'%i));native_scene=evidence.read(folder/('capture-%d.scene.json'%i));case=next(c for c in v.CASES if row['name'].startswith(c['name']+'.'));suffix=row['name'].split('.',1)[1]
        if meta.get('nonce')!=nonce or meta.get('name')!=row['name']or meta.get('capture')!=i or meta.get('step')!=row['step']or state['game_time']!=ready['game_time']or native_scene['game_time']!=state['game_time']:raise ValueError('Capture nonce/state/time/name differs')
        module=Path(meta['module']).resolve();expected=(Path(receipt['source'])/'gemrb/GUIScripts'/(case['pack']+'.py')).resolve()
        if module!=expected:raise ValueError('Actual stock spellbook script provider differs')
        expectedlevel={'initial':0,'arrow1':1,'tab1':1,'previous0':0,'arrow0':0,'tab0':0,'tab2':2,'back1':1,'tab1-repeat':1}.get(suffix,case['level'])
        if meta['level']!=expectedlevel:raise ValueError('Arrow/tab requested level disagrees with actual shown content')
        nonidentity=v.book_guard(meta,state,ui,case,spell_names,template)or nonidentity
        modal=any(c['pack']==case['pack']and c['window']==case['modal']and c['visible']for c in ui['controls'])
        if modal!=meta['confirmation']or modal!=(suffix in('cancel-modal','remove-modal')):raise ValueError('Actual charged/depleted confirmation boundary differs')
        captures[row['name']]=(meta,state,ui)
        if suffix in('tab0','tab1','arrow0','arrow1','back1','tab1-repeat'):pixel_rows[row['name']]=v.tab_hashes(folder,meta,ui,case)
    if len(observations)!=host['captures']or len(list(folder.glob('capture-*.bmp')))!=len(observations):raise ValueError('Missing/extra actual screenshot inventory')
    for case in v.CASES:
        v.tabs_guard(pixel_rows,case)
        if mode=='operate':
            baseline=captures[case['name']+'.before'][1]
            for suffix in('cancel-modal','after-cancel','remove-modal','after-remove','after-add','after-depleted-remove','final'):v.stage_delta(baseline,captures[case['name']+'.'+suffix][1],case,suffix)
    for event in events:
        before=evidence.read(folder/('callback-%d-before.state.json'%event['sequence']));after=evidence.read(folder/('callback-%d-after.state.json'%event['sequence']));step=event['step']
        if v.callback_game_boundary(event,before,after):continue
        if step<0:v.equal_except_selection(before,after);continue
        name=plan[step]
        if '.'in name:
            prefix,suffix=name.split('.',1);case=next(c for c in v.CASES if c['name']==prefix)
            if suffix in('confirm-remove','known-add','known-readd','depleted-remove'):
                if mode!='operate':raise ValueError('Reload executed memorization mutation')
                v.callback_guard(before,after,case,suffix)
            else:v.equal_except_selection(before,after)
            if suffix in('known-add','known-readd'):
                original=v.page(before['party'][case['pc']-1],case['kind'],case['level'])['known'];shown=sorted(enumerate(original),key=lambda pair:spell_names[pair[1]['resref'].upper()]['name']);matches=[i for i,pair in enumerate(shown)if pair[1]['resref'].upper()==case['ref']]
                if receipt.get('presentation_control')==presentation.CONTROL and matches!=[0]:raise ValueError('Controlled target did not move from original index to visible index zero')
                if len(matches)!=1 or event['actual_value']!=case['known']or event['control']!=27+matches[0]or event['actual_tooltip']!=spell_names[case['ref']]['name']:raise ValueError('Actual selected shown spell mapped to wrong original index/resref')
            if suffix=='confirm-remove'and(event['window']!=case['modal']or event['control']!=0 or event['actual_value']!=case['memo']):raise ValueError('Actual charged confirmation index differs')
        else:v.equal_except_selection(before,after)
    final=evidence.read(folder/'final.state.json');operations=evidence.read(folder/'operations-final.state.json');v.declared_world_delta(ready,operations,{c['name']for c in v.CASES}if mode=='operate'else set());v.equal_except_selection(operations,final)
    extras=[e for e in events if e['step']<0]
    if mode=='operate':
        if [(e['step'],e['pack'],e['window'],e['control'])for e in extras]!=[(-1,'GUILOAD',0,26),(-2,'GUIOPT',2,6),(-3,'GUISAVE',0,26),(-4,'GUISAVE',1,7)]:raise ValueError('Actual ordinary GUI save callback chain differs')
        name=evidence.read(folder/'save-name.json')
        if name!=dict(control=3,nonce=nonce,performed=True)or len(host['saves'])!=1 or evidence.read(folder/'before-save.state.json')!=final:raise ValueError('Ordinary GUI save did not preserve collected state')
    elif len(extras)!=1 or host['saves']!=[]:raise ValueError('Reload issued extra load/save/gameplay callback')
    return dict(save=host['saves'][0]if mode=='operate'else None,callbacks=len(events),observations=len(observations),actual_memorization_operations=mode=='operate',nonidentity_sort_runtime=nonidentity,arrow_tab_pixel_agreement=True,original_parity=None,os_pointer_input=False)


if __name__=='__main__':raise SystemExit(main())
