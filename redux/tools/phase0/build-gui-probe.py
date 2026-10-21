"""Build the external GUI host without relinking or changing the engine."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

root = Path(__file__).resolve().parents[2]
prefix = root/'phase0-local/toolchain/msys64/ucrt64'
build = root/'phase0-local/build'
out = root/'phase0-local/gui-probe'
out.mkdir(exist_ok=True)
sources = [root/'tools/phase0/native/gui_probe.cpp', root/'tools/phase0/native/save_probe.cpp']
command = [str(prefix/'bin/g++.exe'), '-std=gnu++17','-g','-O0','-DHAVE_CONFIG_H','-DUSE_OPENGL_API',
           '-D_USE_MATH_DEFINES','-DFMT_HEADER_ONLY','-DFMT_USE_CONSTEVAL=0','-DFMT_EXCEPTIONS=0',
           '-DFMT_UNICODE=1','-fno-strict-aliasing']
for directory in [build,root/'gemrb/gemrb/includes',root/'gemrb/gemrb/core',root/'gemrb/platforms/Windows',
                  build/'gemrb/includes',prefix/'include/SDL2',prefix/'include/python3.14',root/'gemrb/includes/fmt']:
    command += ['-I',str(directory)]
command += [str(sources[0]), str(build/'gemrb/core/libgemrb_core.dll.a'), str(prefix/'lib/libiconv.dll.a'),
            '-lshlwapi','-o',str(out/'Redux_gui_probe.exe')]
env = os.environ.copy()
env['PATH'] = str(prefix/'bin')+os.pathsep+env['PATH']
with (out/'build.log').open('wb') as log:
    result = subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
(out/'build.json').write_text(json.dumps(dict(command=command,exit_code=result.returncode,
    sources={str(p.relative_to(root)):sha(p) for p in sources},engine_dll_sha256=sha(build/'gemrb/libgemrb_core.dll'),
    compiler_sha256=sha(prefix/'bin/g++.exe'),binary_sha256=sha(out/'Redux_gui_probe.exe') if result.returncode==0 else None),indent=2),encoding='utf-8')
print((out/'build.log').read_text(errors='replace')[-10000:])
raise SystemExit(result.returncode)
