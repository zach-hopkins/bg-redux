"""Verify original manifest members and record a point-in-time local run inventory."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[2]
local = root / 'phase0-local'
evidence = root / 'docs/compatibility/evidence'
manifest = json.loads((evidence / 'bg2ee-copy-manifest.json').read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


game = local / 'bg2ee-clean'
expected = {entry['path'] for entry in manifest['files']}
mismatches = [entry['path'] for entry in manifest['files'] if sha(game / entry['path']) != entry['sha256']]
additions = sorted(path.relative_to(game).as_posix() for path in game.rglob('*')
                   if path.is_file() and path.relative_to(game).as_posix() not in expected)
snapshot = local / 'logs/bg2ee-runtime-audit-snapshot.log'
shutil.copyfile(local / 'logs/bg2ee-runtime.log', snapshot)
results = [json.loads(path.read_text()) for path in sorted((local / 'results').glob('*/result.json'))]
stock = []
for path in sorted((local / 'results/stock/gtest').glob('*.xml')):
    cases = list(ET.parse(path).iter('testcase'))
    stock.append(dict(report=path.relative_to(root).as_posix(), discovered=len(cases),
        disabled=sum(case.get('status') == 'notrun' for case in cases),
        skipped=sum(case.find('skipped') is not None for case in cases),
        failed=sum(case.find('failure') is not None for case in cases)))
binaries = [local / 'build/gemrb' / name for name in ['gemrb.exe', 'libgemrb_core.dll',
             'Test_gemrb_core.exe', 'Redux_phase0_core.exe']]
fixture = local / 'gemrb/tests/resources/saves/0 - bg2ee'
report = dict(captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    revision=subprocess.check_output(['git', '-C', str(root / 'gemrb'), 'rev-parse', 'HEAD'], text=True).strip(),
    engine_git_status=subprocess.check_output(['git', '-C', str(root / 'gemrb'), 'status', '--porcelain'], text=True),
    original_data_files_checked=len(expected), data_mismatches=mismatches, added_runtime_files=additions,
    binaries=[dict(path=path.relative_to(root).as_posix(), bytes=path.stat().st_size, sha256=sha(path)) for path in binaries],
    runtime_log_snapshot=dict(path=snapshot.relative_to(root).as_posix(), sha256=sha(snapshot)),
    original_save_fixture=dict(provenance='Historical Chapter 1 snapshot: GAMEV2.0 with verified EEex payload markers. Retained negative fixture, not vanilla. A separate human-created vanilla fixture and native import/reload results now exist; see save-harness-results.json.',
        files=[dict(name=path.name, bytes=path.stat().st_size, sha256=sha(path)) for path in sorted(fixture.iterdir()) if path.is_file()]),
    stock_gtest_reports=stock, bounded_harness_runs=results)
(evidence / 'baseline-results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: report[key] for key in ['captured_utc','revision','engine_git_status','original_data_files_checked','data_mismatches','added_runtime_files','stock_gtest_reports']}, indent=2))
assert not mismatches
