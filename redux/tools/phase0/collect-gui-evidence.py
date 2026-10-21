"""Publish compact result/provenance receipts without licensed game assets."""
from pathlib import Path
import datetime
import json
import subprocess
import sys

from harness import ROOT, LOCAL, BUILD, digest
from save_harness import manifest

patterns=['gui-stock-verified','gui-bam-comparison','gui-ttf18-screens','gui-missing-negative',
          'gui-timeout-verified','post-gui-library-check']
report=dict(schema='bg-redux-gui-evidence/1',captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runs=[])
for pattern in patterns:
    matches=list((LOCAL/'results').glob('*-'+pattern+'-*'))
    if len(matches)!=1: raise ValueError('Expected one executed run: '+pattern)
    path=matches[0]
    result=json.loads((path/'result.json').read_text(encoding='utf-8'))
    stages=[]
    for stage in result.get('stages',[]):
        item={k:stage[k] for k in ['name','mode','font_mode','process','passed','assertions','error','native_error'] if k in stage}
        stage_path=path/stage['name']
        item['artifacts']={str(p.relative_to(path)):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in stage_path.glob('*')
                           if p.is_file() and p.suffix in ['.json','.bmp','.cfg','.log']}
        if 'created_save' in stage: item['created_save']=stage['created_save']
        stages.append(item)
    report['runs'].append(dict(run_id=result['run_id'],result_sha256=digest(path/'result.json'),
        result={k:result[k] for k in ['verdict','execution_verdict','assertion_verdict','screens_only','persistence',
                'legacy_semantic_diagnostic','fixture_unchanged','source_unchanged','created_save_unchanged_on_reload','error','postprocessing'] if k in result},
        stages=stages))
report['build']=json.loads((LOCAL/'gui-probe/build.json').read_text(encoding='utf-8'))
report['tool_sources']={str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/'tools/phase0').rglob('*'))
    if p.is_file() and p.suffix in ['.py','.cpp'] and '__pycache__' not in str(p)}
report['plugins']={p.name:digest(p) for p in sorted((BUILD/'gemrb/plugins').glob('*.dll'))}
report['revision']=subprocess.check_output(['git','-C',str(ROOT/'gemrb'),'rev-parse','HEAD'],text=True).strip()
report['engine_status']=subprocess.check_output(['git','-C',str(ROOT/'gemrb'),'status','--porcelain'],text=True)
report['fixture_matches_pinned_manifest']=manifest(LOCAL/'fixtures/original-bg2ee-20261020/GemRB')==json.loads((ROOT/'docs/compatibility/evidence/vanilla-save-fixture.json').read_text())['files']
log=LOCAL/'logs/gui-harness-unit-tests.log'
with log.open('wb') as output:
    command=[sys.executable,'-m','unittest','discover','-s','tools/phase0/tests','-v']
    unit=subprocess.run(command,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
report['unit_tests']=dict(command=command,exit_code=unit.returncode,log_sha256=digest(log),
    output=log.read_text(encoding='utf-8',errors='replace'))
report['development_failures']=[
    dict(run='20261021T011144Z-gui-stock-first-96cc3e1c',classification='harness setup',detail='Wrong shader working directory; corrected to build root.'),
    dict(run='20261021T011158Z-gui-stock-cwd-7e11cd2f',classification='harness bootstrap',detail='GUILOAD called outside normal LoadScript globals merge; corrected to SetNextScript. Timeout tree killed.'),
    dict(run='20261021T011305Z-gui-stock-load-0960eac0',classification='insufficient test deadline',detail='30s deadline interrupted screen/save-confirmation traversal; no success claimed.'),
    dict(run='20261021T011512Z-gui-save-debug-270a5cc8',classification='harness crash confirmed with GDB',detail='UIJSON dereferenced absent window primary scripting ref after closure. Null-checked in external host; not an engine crash finding.'),
    dict(run='20261021T011640Z-gui-stock-paused-bf9d2173',classification='external host cleanup order',detail='All GUI steps completed; host destroyed VideoDriver before Interface. Matched GemRB.cpp order; subsequent stock/BAM/screen runs exit0.')]
path=ROOT/'docs/compatibility/evidence/gui-harness-results.json'
path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(path)
print('unit exit',unit.returncode,'engine clean',not report['engine_status'].strip(),'fixture pinned',report['fixture_matches_pinned_manifest'])
raise SystemExit(unit.returncode or bool(report['engine_status'].strip()) or not report['fixture_matches_pinned_manifest'])
