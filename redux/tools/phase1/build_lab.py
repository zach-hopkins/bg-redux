"""Build an isolated LAB candidate without modifying the Phase 0 baseline."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def execute(command, folder, env, log, timeout):
    row = dict(command=command, timeout_seconds=timeout, timed_out=False)
    with log.open('wb') as output:
        process = subprocess.Popen(command, cwd=folder, env=env, stdout=output, stderr=subprocess.STDOUT)
        row['pid'] = process.pid
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            row['timed_out'] = True
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                           stdout=output, stderr=subprocess.STDOUT, timeout=15, check=False)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                row['cleanup'] = 'termination requested; process still present'
        row['exit_code'] = process.returncode
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=4, choices=range(1, 7))
    args = parser.parse_args()
    root, source = args.project_root.resolve(), args.source.resolve()
    if not (source/'gemrb/core/Interface.cpp').is_file():
        parser.error('Source must be a GemRB checkout')
    sys.path.insert(0, str(root/'tools/phase0'))
    from baseline_runner import protected, preflight
    original_preflight = preflight(root)
    before = protected(root)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder = root/'phase1-local/builds'/(stamp+'-candidate-'+uuid.uuid4().hex[:8])
    folder.mkdir(parents=True, exist_ok=False)
    write(folder/'phase0-protected-before.json', before)
    prefix = root/'phase0-local/toolchain/msys64/ucrt64'
    cmake = str(prefix/'bin/cmake.exe')
    env = os.environ.copy()
    env['PATH'] = str(prefix/'bin')+os.pathsep+env['PATH']
    helper = source/'redux/tools/phase1/cmake/managed-tests.cmake'
    glew = source/'redux/tools/phase0/cmake'
    configure = [cmake, '-S', str(source), '-B', str(folder), '-G', 'Ninja',
                 '-DCMAKE_BUILD_TYPE=Debug', '-DSDL_BACKEND=SDL2', '-DOPENGL_BACKEND=OpenGL',
                 '-DUSE_TESTS=ON', '-DUSE_LIBVLC=OFF', '-DDISABLE_WERROR=ON',
                 '-DCMAKE_PREFIX_PATH='+str(prefix), '-DCMAKE_MODULE_PATH='+str(glew),
                 '-DCMAKE_PROJECT_TOP_LEVEL_INCLUDES='+str(helper),
                 '-DCMAKE_C_COMPILER='+str(prefix/'bin/gcc.exe'),
                 '-DCMAKE_CXX_COMPILER='+str(prefix/'bin/g++.exe'),
                 '-DCMAKE_MAKE_PROGRAM='+str(prefix/'bin/ninja.exe'),
                 '-DPython_ROOT_DIR='+str(prefix), '-DPython_FIND_REGISTRY=NEVER',
                 '-DPython_INCLUDE_DIR='+str(prefix/'include/python3.14'),
                 '-DPython_LIBRARY='+str(prefix/'lib/libpython3.14.dll.a'),
                 '-DCMAKE_RC_FLAGS=--preprocessor='+str(prefix/'bin/gcc.exe')+
                 ' --preprocessor-arg=-E --preprocessor-arg=-xc --preprocessor-arg=-DRC_INVOKED',
                 '-DCMAKE_INSTALL_PREFIX='+str(folder/'install')]
    configure = [argument.replace('\\', '/') for argument in configure]
    result = dict(schema='bg-redux-phase1-build/1', source=str(source), directory=str(folder),
                  status='failed', commands=[], original_preflight=original_preflight,
                  compiler_sha256=digest(prefix/'bin/g++.exe'),
                  source_commit=subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip(),
                  source_status=subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True))
    tracked = subprocess.check_output(['git', '-C', str(source), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'])
    result['source_files'] = {name: digest(source/name) for name in tracked.decode('utf-8').split('\0')
                              if name and not name.startswith('redux/') and (source/name).is_file()}
    support = [helper, source/'redux/tools/phase0/managed-test-main.cpp', *sorted(glew.glob('*.cmake'))]
    result['build_support_files'] = {p.relative_to(source).as_posix(): digest(p) for p in support}
    try:
        for name, expected in result['build_support_files'].items():
            frozen = folder/'build-support'/name
            frozen.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source/name, frozen)
            if digest(frozen) != expected or digest(source/name) != expected:
                raise ValueError('Build support changed while freezing: '+name)
        for label, command, timeout in [('configure', configure, 120),
                                        ('build', [cmake, '--build', str(folder), '--parallel', str(args.jobs)], 1800)]:
            print('Running '+label+' in '+str(folder), flush=True)
            row = execute(command, root, env, folder/(label+'.log'), timeout)
            row['step'] = label
            result['commands'].append(row)
            write(folder/'build-receipt.json', result)
            if row['exit_code'] != 0 or row['timed_out']:
                raise ValueError(label+' failed; retained log: '+str(folder/(label+'.log')))
        result['binaries'] = {p.relative_to(folder).as_posix(): digest(p)
                              for p in sorted((folder/'gemrb').rglob('*'))
                              if p.is_file() and (p.suffix in ('.dll', '.exe') or p.name=='libgemrb_core.dll.a')}
        result['source_unchanged_during_build'] = all((source/name).is_file() and digest(source/name)==value
                                                     for name, value in result['source_files'].items())
        if not result['source_unchanged_during_build']:
            raise ValueError('Candidate source changed during build')
        result['status'] = 'built-not-validated'
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result['error'] = str(error)
    finally:
        result['build_support_unchanged'] = all((source/name).is_file() and digest(source/name)==expected
                                                for name, expected in result['build_support_files'].items())
        if not result['build_support_unchanged']:
            result['status'] = 'failed'
            result['build_support_error'] = 'Compiled test entry or CMake support changed during build'
        after = protected(root)
        write(folder/'phase0-protected-after.json', after)
        result['phase0_preservation'] = {key: before[key] == after[key] for key in before}
        if not all(result['phase0_preservation'].values()):
            result['status'] = 'failed'
            result['preservation_error'] = 'Phase 0 protected input changed'
        result['completed_utc'] = datetime.now(timezone.utc).isoformat()
        shutil.copy2(Path(__file__), folder/'build_lab.py')
        write(folder/'build-receipt.json', result)
    print(json.dumps(dict(directory=str(folder), status=result['status'], error=result.get('error')), indent=2))
    return 0 if result['status'] == 'built-not-validated' else 1


if __name__ == '__main__':
    raise SystemExit(main())
