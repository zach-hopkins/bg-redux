"""Link already built core-test objects to a separate executable.

Useful while the user's running game holds the baseline DLL/executable open.
Requires managed-live-tests.cmake's managed-test-main object to be compiled.
Does not rebuild, overwrite or patch the engine DLL or baseline test executable.
"""
from pathlib import Path
import os
import subprocess

root = Path(__file__).resolve().parents[2]
build = root / 'phase0-local/build'
prefix = root / 'phase0-local/toolchain/msys64/ucrt64'
objects = sorted((build / 'gemrb/CMakeFiles/Test_gemrb_core.dir').rglob('*.obj'))
assert any('managed-test-main' in obj.name for obj in objects), 'Compile the external entry first'
command = [str(prefix / 'bin/g++.exe'), '-g', '-o', str(build / 'gemrb/Redux_phase0_core.exe')]
command += [str(obj) for obj in objects]
command += [str(build / 'gemrb/core/libgemrb_core.dll.a'), str(prefix / 'lib/libgtest.dll.a'),
            str(prefix / 'lib/libiconv.dll.a'), '-lshlwapi']
env = os.environ.copy()
env['PATH'] = str(prefix / 'bin') + os.pathsep + env['PATH']
subprocess.run(command, cwd=build, env=env, check=True)
print(f'Linked {len(objects)} existing test objects; separate managed entry, unchanged engine DLL')
