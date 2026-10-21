"""Compile an external native host against the existing pinned engine DLL."""
from pathlib import Path
import os
import subprocess
import hashlib
import json

root = Path(__file__).resolve().parents[2]
build = root / 'phase0-local/build'
prefix = root / 'phase0-local/toolchain/msys64/ucrt64'
output = root / 'phase0-local/native-probe'
output.mkdir(parents=True, exist_ok=True)
source = root / 'tools/phase0/native/save_probe.cpp'
command = [str(prefix / 'bin/g++.exe'), '-std=gnu++17', '-g', '-O0', '-DHAVE_CONFIG_H',
           '-DUSE_OPENGL_API', '-D_USE_MATH_DEFINES', '-DFMT_HEADER_ONLY', '-DFMT_USE_CONSTEVAL=0',
           '-DFMT_EXCEPTIONS=0', '-DFMT_UNICODE=1', '-fno-strict-aliasing']
for directory in [build, root / 'gemrb/gemrb/includes', root / 'gemrb/gemrb/core',
                  root / 'gemrb/platforms/Windows', build / 'gemrb/includes', prefix / 'include/SDL2',
                  prefix / 'include/python3.14', root / 'gemrb/includes/fmt']:
    command += ['-I', str(directory)]
command += [str(source), str(build / 'gemrb/core/libgemrb_core.dll.a'),
            str(prefix / 'lib/libiconv.dll.a'), '-lshlwapi', '-o', str(output / 'Redux_save_probe.exe')]
env = os.environ.copy()
env['PATH'] = str(prefix / 'bin') + os.pathsep + env['PATH']
with (output / 'build.log').open('wb') as log:
    result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()
(output / 'build.json').write_text(json.dumps(dict(command=command, exit_code=result.returncode,
    source_sha256=sha(source), engine_dll_sha256=sha(build/'gemrb/libgemrb_core.dll'),
    compiler_sha256=sha(prefix/'bin/g++.exe'), binary_sha256=sha(output/'Redux_save_probe.exe') if result.returncode==0 else None), indent=2), encoding='utf-8')
print((output / 'build.log').read_text(errors='replace')[-14000:])
raise SystemExit(result.returncode)
