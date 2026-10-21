"""Launch the built engine with isolated state and durable stdout/stderr capture."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
profile = sys.argv[1] if len(sys.argv) > 1 else 'bg2ee'
assert profile in ('minimal', 'demo', 'bg2ee')
prefix = root / 'phase0-local/toolchain/msys64/ucrt64'
build = root / 'phase0-local/build'
env = os.environ.copy()
env['PATH'] = str(prefix / 'bin') + os.pathsep + env['PATH']
env['PYTHONHOME'] = str(prefix)
env['PYTHONPATH'] = str(prefix / 'lib/python3.14')
env.pop('HOME', None)
env['HOMEDRIVE'] = root.drive
env['HOMEPATH'] = str(root / 'phase0-local/user-profile')[len(root.drive):]
(root / 'phase0-local/user-profile/Documents').mkdir(parents=True, exist_ok=True)
log = root / f'phase0-local/logs/{profile}-runtime.log'
print(f'Launching {profile}; log: {log}', flush=True)
with log.open('wb') as output:
    proc = subprocess.Popen([str(build / 'gemrb/gemrb.exe'), '-c', str(root / f'phase0-local/config/{profile}.cfg')],
        cwd=build, env=env, stdout=output, stderr=subprocess.STDOUT)
    (root / f'phase0-local/logs/{profile}-pid.txt').write_text(str(proc.pid))
    rc = proc.wait()
print(f'{profile} exit: {rc}', flush=True)
sys.exit(rc if 0 <= rc <= 255 else 1)
