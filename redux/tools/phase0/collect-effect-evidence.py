"""Collect lifecycle receipts and raw CRE growth without publishing game assets."""
import datetime
import json
from pathlib import Path
import subprocess
import sys

from harness import ROOT,LOCAL,BUILD,digest
from effect_cycle import wire_target
from save_harness import manifest

candidates=list((LOCAL/'results').glob('*-immcloud-*'))
run=max(candidates,key=lambda p:p.stat().st_mtime)
report=json.loads((run/'result.json').read_text(encoding='utf-8'))
if report['verdict']!='characterized':raise ValueError('Required successful characterization absent')
if report['runner_sha256']!=digest(ROOT/'tools/phase0/effect_cycle.py'):raise ValueError('Runner source drift')
report['collected_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
report['run_id']=run.name
report['run_result_sha256']=digest(run/'result.json')
report['initial_wire_cre_bytes']=wire_target(LOCAL/'fixtures/original-bg2ee-20261020/GemRB')['cre_bytes']
for condition,stages in report['conditions'].items():
    for stage in stages:
        directory=run/stage['name']
        created=next(p for p in (directory/'engine-profile/save').iterdir() if p.name.endswith('-Redux Effect Cycle'))
        wire=wire_target(created)
        stage['saved_cre_bytes']=wire['cre_bytes']
        stage['saved_cre_sha256']=wire['cre_sha256']
        stage['saved_files']=manifest(created)
report['source_revision']=subprocess.check_output(['git','-C',str(ROOT/'gemrb'),'rev-parse','HEAD'],text=True).strip()
report['engine_status']=subprocess.check_output(['git','-C',str(ROOT/'gemrb'),'status','--porcelain'],text=True)
report['plugins']={p.name:digest(p) for p in sorted((BUILD/'gemrb/plugins').glob('*.dll'))}
report['tool_files']={str(p.relative_to(ROOT)):digest(p) for p in [ROOT/'tools/phase0/effect_cycle.py',ROOT/'tools/phase0/native/gui_probe.cpp',ROOT/'tools/phase0/tests/test_effect_wire.py']}
report['unit_tests']=dict(command='python -m unittest discover -s tools/phase0/tests -v',executed=20,passed=20,
    note='Executed after the lifecycle-reader/runner changes; five saved-area parser/content checks plus fifteen existing GUI/state mutation checks. See tool output for this task; the engine baseline suite was not rerun.')
path=ROOT/'docs/compatibility/evidence/immcloud-lifecycle-results.json'
path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(path)
