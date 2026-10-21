"""Observe DisplayString protection with bounded private-fixture interventions.

No player commands, original-runtime effect challenge, deterministic ticks or
engine changes are claimed. Return codes are evidence, never outcome oracles.
"""
import datetime
import hashlib
import json
from pathlib import Path
import uuid

from harness import ROOT,LOCAL,BUILD,digest
from save_harness import manifest,write
from effect_cycle import run_stage,target_state

STRINGS=[14665,41616,40979,40969,41495]

def evaluate(native):
    rows=native['observations']
    expected=[('loaded-protection',s,True) for s in STRINGS]+[('removed-protection',s,False) for s in STRINGS]+[('reapplied-protection',14665,True)]
    if [(r['phase'],r['strref'],r['expected_suppressed']) for r in rows]!=expected:
        raise ValueError('Missing, duplicate or reordered challenge observations')
    checks=[]
    for row in rows:
        before,after,needle=row['before_text'],row['after_text'],row['expected_text']
        if not needle:raise ValueError('Empty challenge string')
        unchanged=before==after
        appended=after.startswith(before) and needle in after[len(before):]
        passed=unchanged if row['expected_suppressed'] else (not unchanged and appended)
        checks.append(dict(phase=row['phase'],strref=row['strref'],passed=passed,
            expected_suppressed=row['expected_suppressed'],message_unchanged=unchanged,
            appended_expected_text=appended,apply_return_code=row['apply_return_code'],
            before_sha256=hashlib.sha256(before.encode()).hexdigest(),after_sha256=hashlib.sha256(after.encode()).hexdigest()))
    checks.append(dict(phase='reapply-parameter-normalization',passed=native['reapplied_parameter2_normalized'] is True))
    return checks

def main():
    output=LOCAL/'results'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-string-challenge-'+uuid.uuid4().hex[:8]);output.mkdir()
    report=dict(schema='bg-redux-string-challenge-results/1',directory=str(output),stages=[],verdict='failed',
        scope=__doc__,engine_source_modified=False)
    try:
        receipt=json.loads((LOCAL/'gui-probe/build.json').read_text(encoding='utf-8'))
        if receipt['binary_sha256']!=digest(LOCAL/'gui-probe/Redux_gui_probe.exe') or receipt['engine_dll_sha256']!=digest(BUILD/'gemrb/libgemrb_core.dll'):raise ValueError('Native provenance drift')
        for path,sha in receipt['sources'].items():
            if digest(ROOT/path)!=sha:raise ValueError('Native source drift')
        report['build']=receipt
        reference=json.loads((ROOT/'docs/compatibility/evidence/original-reference-status.json').read_text(encoding='utf-8'))
        if reference['verdict']!='reference-observed':raise ValueError('Original reference not observed')
        frozen=Path(reference['directory'])
        fixtures=[('baseline',LOCAL/'fixtures/original-bg2ee-20261020/GemRB')]+[(o['label'],frozen/o['label']) for o in reference['observations'][1:]]
        for (label,fixture),observation in zip(fixtures,reference['observations']):
            before=manifest(fixture)
            if before!=observation['files']:raise ValueError('Reference fixture drift')
            stage,_=run_stage(output,label,fixture,None,'string-challenge')
            checks=evaluate(stage.pop('native'))
            # Include raw private state in artifacts, compact outcomes in public evidence.
            state,actor=target_state(output/label/'challenge-before.state.json')
            for phase in ['removed','restored']:
                changed,other=target_state(output/label/('challenge-'+phase+'.state.json'))
                checks.append(dict(phase=phase+'-clock-unchanged',passed=changed['game_time']==state['game_time']))
                checks.append(dict(phase=phase+'-base-stats-unchanged',passed=other['base_stats']==actor['base_stats']))
            stage.update(label=label,checks=checks,source_fixture_unchanged=manifest(fixture)==before)
            if not stage['source_fixture_unchanged']:raise ValueError('Source fixture mutated')
            report['stages'].append(stage)
        checks=[c for s in report['stages'] for c in s['checks']]
        report['assertions_total']=len(checks);report['assertions_passed']=sum(c['passed'] for c in checks)
        report['verdict']='passed-bounded-gemrb-behavior' if all(c['passed'] for c in checks) else 'differences'
    except (OSError,ValueError,KeyError,TypeError) as error:
        report['error']=str(error)
    report['tool_sources']={str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),ROOT/'tools/phase0/effect_cycle.py']}
    write(output/'result.json',report)
    write(ROOT/'docs/compatibility/evidence/string-challenge-results.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['stages','build','tool_sources']},indent=2))
    return 0 if report['verdict']=='passed-bounded-gemrb-behavior' else 1

if __name__=='__main__':raise SystemExit(main())
