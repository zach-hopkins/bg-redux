"""Declared debug inn checkpoint and ordinary stock observation journey."""
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
import inn_checkpoint_validation as info
import spellbook_erase_journey as erase
import spellbook_presentation_control as presentation
HERE=Path(__file__).resolve().parent
KIND='bg-redux-inn-checkpoint-host/1'
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
        for original in (project/'tools/phase0/native/gui_probe.cpp',project/'tools/phase0/native/save_probe.cpp',HERE/'native/inn_checkpoint_journey.cpp',HERE/'native/window_render_regression.h'):
            shared.frozen_copy(original,compiled/original.name)
        for name,raw in compiled_helpers().items():(compiled/name).write_bytes(raw)
        result['compiled_sources']=evidence.manifest(compiled)
        result['parent_proof']=parent_proof(project)
        result['resources']={}
        for name,row in resource_guard(api,project,source).items():
            result['resources'][name]={k:v for k,v in row.items() if k!='raw'}
            if 'raw'in row:
                target=out/'resources'/name;target.parent.mkdir(exist_ok=True);target.write_bytes(row['raw']);result['resources'][name]['frozen']=str(target)
        resource_list=out/'resource-list.txt';resource_list.write_text(''.join(row['extension']+' '+name.rsplit('.',1)[0]+'\n'for name,row in result['resources'].items()if 'frozen'in row),encoding='ascii');result['resource_list_sha256']=evidence.sha(resource_list)
        prefix=project/'phase0-local/toolchain/msys64/ucrt64';compiler=prefix/'bin/g++.exe';host=out/'Redux_inn_checkpoint_gui.exe'
        compiler_sha=evidence.sha(compiler);cmake_sha=evidence.sha(build/'CMakeCache.txt')
        cmd=[str(compiler),'-std=gnu++17','-g','-O0','-DHAVE_CONFIG_H','-DUSE_OPENGL_API','-D_USE_MATH_DEFINES','-DFMT_HEADER_ONLY','-DFMT_USE_CONSTEVAL=0','-DFMT_EXCEPTIONS=0','-DFMT_UNICODE=1','-fno-strict-aliasing']
        for p in (build,source/'gemrb/includes',source/'gemrb/core',source/'platforms/Windows',build/'gemrb/includes',prefix/'include/SDL2',prefix/'include/python3.14',source/'gemrb/includes/fmt'):cmd+=['-I',str(p)]
        cmd+=[str(compiled/'inn_checkpoint_journey.cpp'),str(build/'gemrb/core/libgemrb_core.dll.a'),str(prefix/'lib/libiconv.dll.a'),'-lshlwapi','-o',str(host)]
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
    if r.get('schema')!=KIND or r.get('verdict')!='built-not-executed' or [r.get(k) for k in ('project','source','build')]!=list(map(str,(project,source,build))):raise ValueError('Wrong/failed information host build')
    shared.require_process(r['process']);source_guard(r,project,source)
    if r.get('phase0_preservation')!=dict(source=True,binaries=True,fixture=True) or r.get('candidate_preserved')is not True:raise ValueError('Build preservation failed')
    if evidence.sha(r['binary'])!=r['binary_sha256'] or evidence.sha(r['compiler'])!=r['compiler_sha256'] or evidence.sha(build/'CMakeCache.txt')!=r['cmake_sha256']:raise ValueError('Driver/compiler/CMake drift')
    if shared.candidate_inventory(source,build)!=r['candidate_inventory'] or evidence.manifest(Path(path).parent/'compiled-sources')!=r['compiled_sources']:raise ValueError('Candidate/compiled source drift')
    for name,raw in compiled_helpers().items():
        if (Path(path).parent/'compiled-sources'/name).read_bytes()!=raw:raise ValueError('Frozen inn helper derivation differs')
    if evidence.sha(Path(path).parent/'resource-list.txt')!=r['resource_list_sha256']:raise ValueError('Frozen resource list differs')
    check_resources(r,shared.phase0(project),project,source)
    return r

def run(args):
    project,source,build=(getattr(args,k).resolve() for k in ('project_root','engine_source_root','engine_build_root'))
    root_guard(project,source,build)
    if not args.results_root.resolve().is_relative_to(project/'phase1-local/results'):raise ValueError('Private Phase1 results root required')
    policy='characterize-current'
    control_mode='stock';label='debug-inn-checkpoint'
    if policy=='ee-direct':label+='-ee-direct'
    out=shared.new_output(args.results_root.resolve(),label);result=dict(confirmation_policy=policy,presentation_control=control_mode,schema='bg-redux-debug-inn-checkpoint/1',passed=False,stages=[],original_parity=None)
    api=before=candidate=None;preserved=[];privates=[];pins={};override_pins=[];controls=[]
    try:
        api=shared.phase0(project);result['preflight']=api.baseline_runner.preflight(project)
        before=api.baseline_runner.protected(project);candidate=shared.candidate_inventory(source,build)
        shared.write(out/'phase0-before.json',before);shared.write(out/'candidate-before.json',candidate)
        receipt=check_build(args.host_build.resolve(),project,source,build);result['resources']={k:{f:v for f,v in row.items() if f!='raw'} for k,row in resource_guard(api,project,source).items()};result['parent_proof']=parent_proof(project)
        driver=out/'driver';driver.mkdir();host=driver/'Redux_inn_checkpoint_gui.exe'
        shared.frozen_copy(Path(receipt['binary']),host);shared.frozen_copy(args.host_build.resolve(),driver/'build.json')
        for name,row in receipt['sources'].items():shared.frozen_copy(Path(row['frozen']),driver/'sources'/row['sha256']/Path(name).name)
        shutil.copytree(args.host_build.resolve().parent/'compiled-sources',driver/'compiled-sources')
        shutil.copytree(args.host_build.resolve().parent/'resources',driver/'resources')
        shared.frozen_copy(args.host_build.resolve().parent/'resource-list.txt',driver/'resource-list.txt')
        startup=driver/'startup';startup.mkdir();shared.frozen_copy(HERE/'InnCheckpointStart.py',startup/'InnCheckpointStart.py');shared.frozen_copy(HERE/'InnCheckpointRuntime.py',startup/'InnCheckpointRuntime.py');shared.frozen_copy(HERE/'SpellbookOperationRuntime.py',startup/'SpellbookOperationRuntime.py')
        parent_dir=driver/'parent';parent_dir.mkdir()
        for name in ('result.json','artifact-manifest.json'):shared.frozen_copy(project/'phase1-local/results'/PARENT/name,parent_dir/name)
        driver_files=evidence.manifest(driver);result['driver_files']=driver_files
        incoming=project/'phase1-local/results'/PARENT/'recruit/frozen-save'
        result['initial_wire']=wire(incoming);initial=save_manifest(incoming,4);preserved.append((incoming,initial))
        for mode in ('prepare','observe'):
            stage=out/mode;stage.mkdir();entry=dict(mode=mode,nonce=uuid.uuid4().hex,passed=False);result['stages'].append(entry)
            input_files=save_manifest(incoming,4);copied=stage/'profile/save/000000007-HarnessInput';shutil.copytree(incoming,copied)
            if binary.manifest(copied)!=input_files:raise ValueError('Copied measured input differs before launch')
            preserved.extend([(incoming,input_files),(copied,input_files)]);entry['input_files']=input_files
            private=shared.prepare_private_game(project,stage);privates.append((private,stage))
            for name in ('cache','capture','override'):(stage/name).mkdir()
            observed_receipt=dict(receipt,confirmation_policy=policy)
            if mode=='observe':
                observed_receipt=info.reload_resources(observed_receipt,copied,stage/'cache')
                entry['saved_resource_bindings']={name:row['saved_member']for name,row in observed_receipt['resources'].items()if 'saved_member'in row}
            if control_mode==presentation.CONTROL:
                control=presentation.prepare(receipt,stage/'override');presentation.verify(control,receipt);controls.append(control)
                shared.write(stage/'presentation-control.json',control);entry['presentation_control']=control
                observed_receipt=dict(receipt,resources=control['resources'],presentation_control=presentation.CONTROL,confirmation_policy=policy)
            override_pins.append((stage/'override',evidence.manifest(stage/'override')))
            config=dict(GameType='bg2ee',GamePath=private['game'],GemRBPath=source/'gemrb',PluginsPath=build/'gemrb/plugins',CachePath=stage/'cache',SavePath=stage/'profile',ModPath=stage/'override',UseAsLibrary=0,SaveAsOriginal=1,Width=1024,Height=768,FullScreen=0,CapFPS=30,AudioDriver='none',GameLanguagePath='lang/en_US',SkipIntroVideos=1,Logging=1,LogColor=0,PathfinderThreadsCount=0,PathfinderMainThreadMode='immediate')
            cfg=stage/'probe.cfg';cfg.write_text(''.join('%s=%s\n'%(k,str(v).replace('\\','/')) for k,v in config.items()),encoding='utf-8');pins[str(cfg)]=evidence.sha(cfg)
            command=[str(host),'--config',str(cfg),'--output',str(stage/'capture'),'--scripts',str(startup),'--mode',mode,'--nonce',entry['nonce'],'--resources',str(driver/'resource-list.txt'),'--confirmation-policy',policy]
            env=api.harness.environment(stage);prefix=project/'phase0-local/toolchain/msys64/ucrt64';env['PATH']=os.pathsep.join([str(build/'gemrb'),str(prefix/'bin'),env.get('PATH','')]);env['PYTHONDONTWRITEBYTECODE']='1'
            source_guard(receipt,project,source);check_resources(receipt,api,project,source);parent_proof(project);shared.validate_private_game(private,stage)
            if evidence.manifest(driver)!=driver_files:raise ValueError('Frozen launch closure changed')
            # This unexecuted all-natural-page plan has explicit callback and
            # owned wall-clock bounds; no timing claim is inferred from them.
            started=time.time_ns();entry['process']=api.baseline_runner.execute(command,build,env,stage/'process.log',900 if mode=='prepare'else 780)
            shared.require_process(entry['process'])
            if 'Traceback (most recent call last)' in (stage/'process.log').read_text(encoding='utf-8',errors='replace'):raise ValueError('Stock callback traceback')
            check_resources(receipt,api,project,source);parent_proof(project)
            entry['runtime_providers']=check_runtime_resources(stage/'capture',observed_receipt)
            entry['observation']=validate_capture(stage/'capture',entry['nonce'],mode,started,observed_receipt)
            if control_mode==presentation.CONTROL and not entry['observation']['nonidentity_sort_runtime']:raise ValueError('Declared presentation control did not produce actual nonidentity sorting')
            if mode=='prepare':
                saved=Path(entry['observation']['save']).resolve()
                if not saved.is_relative_to((stage/'profile/save').resolve()) or saved==copied.resolve():raise ValueError('Output escaped profile/overwrote input')
                entry['wire']=wire(saved);wire_state_guard(entry['wire'],evidence.read(stage/'capture/final.state.json'));info.wire_setup_guard(result['initial_wire'],entry['wire']);files=save_manifest(saved,4);frozen=stage/'frozen-save';shutil.copytree(saved,frozen)
                if save_manifest(frozen,4)!=files:raise ValueError('Frozen GUI save drift')
                preserved.extend([(saved,files),(frozen,files)]);incoming=frozen;entry.update(frozen_save=str(frozen),frozen_save_files=files)
            else:
                entry['wire']=wire(copied);wire_state_guard(entry['wire'],evidence.read(stage/'capture/loaded.state.json'));wire_state_guard(entry['wire'],evidence.read(stage/'capture/final.state.json'))
                prior=evidence.read(out/'prepare/capture/final.state.json');loaded=evidence.read(stage/'capture/loaded.state.json')
                if prior['journal']!=loaded['journal']:raise ValueError('Fresh-process reload changed journal fields')
                if entry['wire']!=result['stages'][0]['wire']:raise ValueError('Reload input wire differs from frozen operation output')
            entry['private_game_validation']=shared.validate_private_game(private,stage);entry['passed']=True
        if len({s['process']['pid'] for s in result['stages']})!=2:raise ValueError('Fresh-process ownership absent')
        result['passed']=True;result['coverage']=dict(debug_transfer=True,debug_gold_0_to_100=True,checkpoint_save_reload=True,ordinary_inn_callbacks=True,original_parity=None);result['verdict']='passed-declared-debug-checkpoint-and-current-inn-observation'
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
            q.add_argument('--host-build',type=Path,required=True);q.add_argument('--results-root',type=Path,required=True);q.add_argument('--confirmation-policy',choices=('characterize-current',),default='characterize-current')
    args=p.parse_args(argv)
    if args.command=='build' and not 1<=args.timeout<=300:p.error('Timeout must be bounded to 1..300 seconds')
    return build_host(args) if args.command=='build' else run(args)

def root_guard(project,source,build):
    if source==(project/'gemrb').resolve()or build==(project/'phase0-local/build').resolve():raise ValueError('Separate candidate source/build required')
    if HERE!=source/'redux/tools/phase1'or any(Path(m.__file__).resolve().parent!=HERE for m in (common,binary,shared,evidence,checkpoint,tables,v,presentation,info,erase)):raise ValueError('Exact candidate adapter/dependency roots required')
    check_engine_receipt(source,build)

def sources(project,source):
    local=['spellbook_information_validation.py','spellbook_presentation_control.py','spellbook_operation_journey.py','spellbook_operation_validation.py','SpellbookOperationRuntime.py','SpellbookOperationStart.py','native/spellbook_operation_journey.cpp','native/spellbook_operation_ui_snapshot.cpp']
    local+=['inn_checkpoint_journey.py','inn_checkpoint_validation.py','InnCheckpointRuntime.py','InnCheckpointStart.py','native/inn_checkpoint_journey.cpp','native/dialogue_journey.cpp','native/window_render_regression.h','spellbook_information_journey.py','spellbook_information_journey_validation.py','InnCheckpointRuntime.py','InnCheckpointStart.py','native/inn_checkpoint_journey.cpp','spellbook_erase_journey.py','spellbook_erase_validation.py']
    result={HERE/name for name in local}|set(erase.sources(project,source))
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if not filename:continue
        path=Path(filename).resolve()
        if path.suffix=='.py'and((path.is_relative_to(HERE)and not path.is_relative_to(HERE/'tests'))or path.is_relative_to(project/'tools/phase0')):result.add(path)
    for name in ['GUIScripts/GUIMG.py','GUIScripts/GUIPR.py','GUIScripts/EESpellbookHeading.py','GUIScripts/Spellbook.py','GUIScripts/PortraitWindow.py','GUIScripts/GUICommonWindows.py','GUIScripts/GUICommon.py','GUIScripts/GUIClasses.py','GUIScripts/GUIDefines.py','GUIScripts/GUILOAD.py','GUIScripts/GUISAVE.py','GUIScripts/GUIOPT.py','core/Spellbook.cpp','core/Spellbook.h','core/GUI/Button.cpp','core/GUI/Button.h','core/GUI/Control.cpp','core/GUI/Control.h','core/GUI/View.cpp','core/GUI/View.h','plugins/CREImporter/CREImporter.cpp','plugins/GAMImporter/GAMImporter.cpp','plugins/GUIScript/GUIScript.cpp','unhardcoded/shared/spldisp.2da','unhardcoded/bg2ee/guibtact.2da']:result.add(source/'gemrb'/name)
    result.update(source/'gemrb/GUIScripts'/name for name in ('GUIMG.py','GUIPR.py','EESpellbookHeading.py','EESpellbookInformation.py','BG2EEConfirmation.py','GUIOPT.py','GUIOPTControls.py','GUICommon.py','GUICommonWindows.py','Spellbook.py','GameCheck.py','GUIDefines.py','GUIClasses.py'))
    result.add(source/'gemrb/unhardcoded/shared/defaults.ini')
    for name in ('GUIScripts/GUISTORE.py','GUIScripts/Console.py','core/GameScript/GameScript.cpp','core/GameScript/Actions.cpp','core/GameScript/GSUtils.cpp','core/Map.cpp','core/GUI/GameControl.cpp','core/Interface.cpp','core/Store.cpp','core/DialogHandler.cpp','plugins/AREImporter/AREImporter.cpp','plugins/DLGImporter/DLGImporter.cpp','plugins/STOImporter/STOImporter.cpp','plugins/CHUImporter/CHUImporter.cpp'):result.add(source/'gemrb'/name)
    return sorted(result)

def source_guard(receipt,project,source):
    build=Path(receipt['build']);engine=check_engine_receipt(source,build);expected=set(map(str,sources(project,source)))|{str(build/'build-receipt.json')}|{str(source/name)for name in engine['build_support_files']}
    if set(receipt.get('sources',{}))!=expected:raise ValueError('Complete source/support closure differs')
    for name,row in receipt['sources'].items():
        if evidence.sha(name)!=row['sha256']or evidence.sha(row['frozen'])!=row['sha256']:raise ValueError('Current/frozen source drift')

def gui_helpers(raw):
    if raw.count(b'int main(')!=1 or b'#define REDUX_GUI_HOST'not in raw:raise ValueError('Exact GUI helper shape absent')
    return raw.replace(b'int main(',b'int FrozenUnusedSpellbookGuiMain(')

def compiled_helpers():
    dialogue=(HERE/'native/dialogue_journey.cpp').read_bytes()
    ui=(HERE/'native/spellbook_operation_ui_snapshot.cpp').read_bytes()
    if dialogue.count(b'int main(')!=1 or ui.count(b'#include "spellbook_gui_helpers.cpp"')!=1 or ui.count(b'{"GUIOPT",')!=1:raise ValueError('Pinned helper source shape differs')
    return {'inn_dialogue_helpers.cpp':dialogue.replace(b'int main(',b'int FrozenUnusedInnDialogueMain('),
        'inn_ui_snapshot.cpp':ui.replace(b'#include "spellbook_gui_helpers.cpp"',b'#include "inn_dialogue_helpers.cpp"').replace(b'{"GUIOPT",',b'{"GUISTORE","GUIOPT",')}

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

def wire(folder):return info.wire(folder)

def wire_state_guard(parsed,state):
    return info.wire_state_guard(parsed,state)

def tlk(project,refs):
    raw=(project/'phase0-local/bg2ee-clean/lang/en_US/dialog.tlk').read_bytes()
    if raw[:8]!=b'TLK V1  ':raise ValueError('English TLK version required')
    result={}
    for ref in refs:
        if not 0<=ref<binary.u32(raw,10):raise ValueError('TLK reference bounds')
        at=18+26*ref;result[ref]=binary.block(raw,binary.u32(raw,14)+binary.u32(raw,at+18),binary.u32(raw,at+22)).decode('utf8')
    return result

def resource_guard(api,project,source):
    return info.resource_guard(api,project,source)

def check_resources(receipt,api,project,source):
    actual=resource_guard(api,project,source)
    if set(receipt.get('resources',{}))!=set(actual):raise ValueError('Resource closure missing/extra')
    for name,row in actual.items():
        expected=receipt['resources'][name]
        if {k:value for k,value in expected.items()if k!='frozen'}!={k:value for k,value in row.items()if k!='raw'}or 'frozen'in expected and evidence.sha(expected['frozen'])!=expected['sha256']:raise ValueError('Resource/source/provider drift: '+name)

def check_runtime_resources(folder,receipt):
    data=evidence.read(folder/'book-providers.json');expected={k:r for k,r in receipt['resources'].items()if 'frozen'in r or 'saved_member'in r}
    if data.get('schema')!='bg-redux-book-providers/1'or set(data.get('resources',{}))!=set(expected):raise ValueError('Actual runtime provider closure incomplete')
    for name,row in expected.items():
        actual=data['resources'][name]
        if Path(actual['originalfile']).resolve()!=Path(row['provider']).resolve()or actual['bytes']!=row['bytes']or evidence.sha(folder/(name+'.runtime'))!=row['sha256']:raise ValueError('Runtime provider/path/bytes differ')
    return data


def validate_capture(folder,nonce,mode,started_ns,receipt):
    return info.validate_capture(folder,nonce,mode,started_ns,receipt)

if __name__=='__main__':raise SystemExit(main())
