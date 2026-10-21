"""Compile only the external fixed-query observer into a fresh private folder."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import uuid

from baseline_runner import execute, sha, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    project = args.project_root.resolve()
    output = args.output_dir.resolve() if args.output_dir else project/'phase0-local/query-side-effect-probes'/(
        datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    if output.exists() and any(output.iterdir()):
        parser.error('Refusing nonempty external build destination')
    output.mkdir(parents=True, exist_ok=True)
    tool = Path(__file__).resolve().parent
    prefix = project/'phase0-local/toolchain/msys64/ucrt64'
    build = project/'phase0-local/build'
    source = tool/'native/query_side_effect_probe.cpp'
    sources = [source, tool/'native/save_probe.cpp', Path(__file__).resolve()]
    before = sha(build/'gemrb/libgemrb_core.dll')
    binary = output/'Redux_query_side_effect_probe.exe'
    command = [str(prefix/'bin/g++.exe'), '-std=gnu++17','-g','-O0','-DHAVE_CONFIG_H','-DUSE_OPENGL_API',
               '-D_USE_MATH_DEFINES','-DFMT_HEADER_ONLY','-DFMT_USE_CONSTEVAL=0','-DFMT_EXCEPTIONS=0',
               '-DFMT_UNICODE=1','-fno-strict-aliasing']
    for directory in [build, project/'gemrb/gemrb/includes', project/'gemrb/gemrb/core',
                      project/'gemrb/platforms/Windows',build/'gemrb/includes',prefix/'include/SDL2',
                      prefix/'include/python3.14',project/'gemrb/includes/fmt']:
        command += ['-I',str(directory)]
    command += [str(source),str(build/'gemrb/core/libgemrb_core.dll.a'),str(prefix/'lib/libiconv.dll.a'),
                '-lshlwapi','-o',str(binary)]
    env = os.environ.copy(); env['PATH'] = str(prefix/'bin')+os.pathsep+env.get('PATH','')
    process = execute(command, project, env, output/'build.log', 240)
    receipt = dict(schema='bg-redux-query-side-effect-build/1', created_utc=datetime.now(timezone.utc).isoformat(),
                   project=str(project), binary=str(binary), process=process, sources={str(p):sha(p) for p in sources},
                   compiler_sha256=sha(prefix/'bin/g++.exe'), engine_dll_sha256=before,
                   engine_dll_unchanged=sha(build/'gemrb/libgemrb_core.dll') == before,
                   binary_sha256=sha(binary) if process['exit_code'] == 0 and binary.is_file() else None)
    for path in sources:
        target = output/'sources'/path.name; target.parent.mkdir(exist_ok=True)
        shutil.copy2(path,target)
    write(output/'build.json',receipt)
    print(str(output/'build.json'), flush=True)
    return 0 if process['exit_code'] == 0 and receipt['engine_dll_unchanged'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
