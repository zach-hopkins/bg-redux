"""Generate isolated runtime configs without changing upstream or game data."""
from pathlib import Path
import ctypes

root = Path(__file__).resolve().parents[2]
short = ctypes.create_unicode_buffer(32768)
assert ctypes.windll.kernel32.GetShortPathNameW(str(root), short, 32768)
base = short.value.replace('\\', '/')
configs = root / 'phase0-local/config'
configs.mkdir(parents=True, exist_ok=True)
for name, kind, data, width, height in [
 ('minimal', 'test', 'gemrb/gemrb/tests/minimal', 640, 480),
 ('demo', 'demo', 'gemrb/demo', 800, 600),
 ('bg2ee', 'bg2ee', 'phase0-local/bg2ee-clean', 1024, 768),
]:
    for p in [f'phase0-local/cache/{name}', f'phase0-local/profiles/{name}/save']:
        (root / p).mkdir(parents=True, exist_ok=True)
    content = f'''GameType={kind}
GameName=BG Redux Phase 0 - {name}
GamePath={base}/{data}
GemRBPath={base}/gemrb/gemrb
PluginsPath={base}/phase0-local/build/gemrb/plugins
CachePath={base}/phase0-local/cache/{name}
SavePath={base}/phase0-local/profiles/{name}
GUIScriptsPath={base}/gemrb/gemrb
GemRBOverridePath={base}/gemrb/gemrb
GemRBUnhardcodedPath={base}/gemrb/gemrb
Width={width}
Height={height}
FullScreen=0
CapFPS=30
AudioDriver={'none' if name == 'minimal' else 'openal'}
GamepadSupport=0
SkipIntroVideos=1
LogColor=0
Logging=1
PathfinderThreadsCount=0
PathfinderMainThreadMode=immediate
'''
    if name == 'bg2ee':
        content += 'GameLanguagePath=lang/en_US\n'
    (configs / f'{name}.cfg').write_text(content, encoding='utf-8')
print(configs)
