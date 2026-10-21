"""Copy the user-nominated Steam dataset and verify every byte by SHA256."""
from pathlib import Path
import hashlib
import json
import shutil

root = Path(__file__).resolve().parents[2]
source = Path("C:/Program Files (x86)/Steam/steamapps/common/Baldur's Gate II Enhanced Edition")
target = root / 'phase0-local/bg2ee-clean'
evidence = root / 'docs/compatibility/evidence'
evidence.mkdir(parents=True, exist_ok=True)
assert source.is_dir()
assert target.resolve().is_relative_to(root.resolve())
if not target.exists():
    shutil.copytree(source, target)
def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()
manifest = []
for index, file in enumerate(sorted(source.rglob('*'))):
    if not file.is_file():
        continue
    relative = file.relative_to(source)
    copy = target / relative
    a, b = digest(file), digest(copy)
    assert a == b, str(relative)
    manifest.append({'path': relative.as_posix(), 'bytes': file.stat().st_size, 'sha256': a})
    if len(manifest) % 500 == 0:
        print(f'Verified {len(manifest)} files', flush=True)
assert {x['path'] for x in manifest} == {x.relative_to(target).as_posix() for x in target.rglob('*') if x.is_file()}
result = {'date': '2026-10-20', 'source': str(source), 'copy': str(target),
 'steam_appid': 257350, 'steam_buildid': '23534562', 'executable_version': '2.7.3.0',
 'file_count': len(manifest), 'bytes': sum(x['bytes'] for x in manifest),
 'source_copy_hashes_match': True, 'cleanliness': 'Exact copy of nominated Steam installation; no independent depot-content verification',
 'files': manifest}
(evidence / 'bg2ee-copy-manifest.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'files'}), flush=True)
