"""Build a frozen external ordinary inn rest host; does not execute it."""
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
KIND='bg-redux-inn-rest-build/1'
check_engine_receipt=checkpoint.check_engine_receipt
save_manifest=checkpoint.save_manifest

import inn_checkpoint_journey as parent
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
        for original in (project/'tools/phase0/native/gui_probe.cpp',project/'tools/phase0/native/save_probe.cpp',HERE/'native/inn_rest_journey.cpp',HERE/'native/window_render_regression.h'):
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
        prefix=project/'phase0-local/toolchain/msys64/ucrt64';compiler=prefix/'bin/g++.exe';host=out/'Redux_inn_rest_gui.exe'
        compiler_sha=evidence.sha(compiler);cmake_sha=evidence.sha(build/'CMakeCache.txt')
        cmd=[str(compiler),'-std=gnu++17','-g','-O0','-DHAVE_CONFIG_H','-DUSE_OPENGL_API','-D_USE_MATH_DEFINES','-DFMT_HEADER_ONLY','-DFMT_USE_CONSTEVAL=0','-DFMT_EXCEPTIONS=0','-DFMT_UNICODE=1','-fno-strict-aliasing']
        for p in (build,source/'gemrb/includes',source/'gemrb/core',source/'platforms/Windows',build/'gemrb/includes',prefix/'include/SDL2',prefix/'include/python3.14',source/'gemrb/includes/fmt'):cmd+=['-I',str(p)]
        cmd+=[str(compiled/'inn_rest_journey.cpp'),str(build/'gemrb/core/libgemrb_core.dll.a'),str(prefix/'lib/libiconv.dll.a'),'-lshlwapi','-o',str(host)]
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

def source_guard(receipt,project,source):
    build=Path(receipt['build']);engine=check_engine_receipt(source,build);expected=set(map(str,sources(project,source)))|{str(build/'build-receipt.json')}|{str(source/name)for name in engine['build_support_files']}
    if set(receipt.get('sources',{}))!=expected:raise ValueError('Complete source/support closure differs')
    for name,row in receipt['sources'].items():
        if evidence.sha(name)!=row['sha256']or evidence.sha(row['frozen'])!=row['sha256']:raise ValueError('Current/frozen source drift')


root_guard=parent.root_guard
compiled_helpers=parent.compiled_helpers
resource_guard=parent.resource_guard
check_resources=parent.check_resources

def sources(project,source):
    return sorted(set(parent.sources(project,source))|{HERE/'inn_rest_host.py',HERE/'InnRestRuntime.py',HERE/'InnRestStart.py',HERE/'native/inn_rest_journey.cpp'})

def parent_proof(project):
    ancestor=parent.parent_proof(project)
    root=project/'phase1-local/results/20261022T185045Z-debug-inn-checkpoint-87848de6'
    if evidence.sha(root/'result.json')!='6623975ff742f2d054063dbe33a0cf2a1f31de22cd9366352cb9ce9b44e4661d'or evidence.sha(root/'artifact-manifest.json')!='99da8b42ebcdfbff03262185460fc9fb2a3df7ccf2ef508650decdd80a1e4289':raise ValueError('Pinned accepted inn parent result/manifest drift')
    receipt=evidence.read(root/'result.json');rows=evidence.read(root/'artifact-manifest.json')['files']
    if not receipt.get('passed')or receipt.get('schema')!='bg-redux-debug-inn-checkpoint/1'or receipt.get('phase0_preservation')!=dict(source=True,binaries=True,fixture=True)or not receipt.get('candidate_preserved')or not receipt.get('inputs_preserved'):raise ValueError('Accepted preserved inn checkpoint required')
    for name,row in rows.items():
        path=(root/name).resolve()
        if not path.is_relative_to(root.resolve())or path.stat().st_size!=row['bytes']or evidence.sha(path)!=row['sha256']:raise ValueError('Frozen inn parent artifact drift')
    if len(receipt['stages'])!=2 or not all(s['passed']for s in receipt['stages']):raise ValueError('Inn parent save/reload incomplete')
    for stage in receipt['stages']:shared.require_process(stage['process'])
    incoming=root/'prepare/frozen-save';files=save_manifest(incoming,4)
    if files!=receipt['stages'][0]['frozen_save_files']or files!=receipt['stages'][1]['input_files']:raise ValueError('Inn parent save/reload binding differs')
    if info.wire(incoming)['gold']!=100 or receipt['parent_proof']['result_sha256']!=ancestor['result_sha256']:raise ValueError('Inn input gold/ancestor differs')
    return dict(parent=str(root),input=str(incoming),files=files,result_sha256=evidence.sha(root/'result.json'),manifest_sha256=evidence.sha(root/'artifact-manifest.json'),ancestor=ancestor,artifact_count=len(rows))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in('project-root','engine-source-root','engine-build-root','output-dir'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--timeout',type=int,default=240);args=parser.parse_args()
    if not 1<=args.timeout<=300:parser.error('Timeout must be bounded to1..300 seconds')
    return build_host(args)

if __name__=='__main__':raise SystemExit(main())
