"""Sample actual main-loop pause/resume; no deterministic stepping or FPS measurement."""
import datetime
import json
from pathlib import Path
import uuid
from harness import ROOT,LOCAL,digest
from save_harness import manifest,write
from effect_cycle import run_stage

def evaluate(native):
    rows=native['samples']
    expected=['paused-initial']*5+['running']*8+['paused-final']*4
    if [r['sample'] for r in rows]!=list(range(17)) or [r['phase'] for r in rows]!=expected:
        raise ValueError('Missing or invalid clock samples')
    checks=[dict(name='monotonic-wall-observations',passed=all(a['elapsed_ms']<b['elapsed_ms'] for a,b in zip(rows,rows[1:]))),
        dict(name='initial-pause-stable',passed=all(r['game_time']==rows[0]['game_time'] for r in rows[:5])),
        dict(name='resume-advances',passed=rows[12]['game_time']>rows[4]['game_time']),
        dict(name='running-clock-monotonic',passed=all(a['game_time']<=b['game_time'] for a,b in zip(rows[4:12],rows[5:13]))),
        dict(name='final-pause-stable',passed=all(r['game_time']==rows[12]['game_time'] for r in rows[13:]))]
    elapsed=rows[12]['elapsed_ms']-rows[4]['elapsed_ms']
    if elapsed<=0:raise ValueError('Invalid running observation duration')
    ticks=rows[12]['game_time']-rows[4]['game_time']
    return checks,dict(running_elapsed_ms=elapsed,running_game_ticks=ticks,
        observed_game_ticks_per_wall_second=round(ticks*1000/elapsed,3),configured_ticks_per_second=native['ticks_per_second'])

def main():
    out=LOCAL/'results'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-live-clock-'+uuid.uuid4().hex[:8]);out.mkdir()
    report=dict(schema='bg-redux-live-clock-results/1',scope=__doc__,directory=str(out),stages=[],verdict='failed')
    try:
        fixture=LOCAL/'fixtures/original-bg2ee-20261020/GemRB'
        pinned=json.loads((ROOT/'docs/compatibility/evidence/vanilla-save-fixture.json').read_text(encoding='utf-8'))
        if manifest(fixture)!=pinned['files']:raise ValueError('Baseline fixture drift')
        for cap in [30,60]:
            stage,_=run_stage(out,'cap'+str(cap),fixture,None,'live-clock',cap)
            checks,observation=evaluate(stage['native'])
            stage.update(cap_fps=cap,checks=checks,observation=observation)
            report['stages'].append(stage)
        report['assertions_total']=sum(len(s['checks']) for s in report['stages'])
        report['assertions_passed']=sum(c['passed'] for s in report['stages'] for c in s['checks'])
        report['verdict']='passed-bounded-live-clock' if report['assertions_total']==report['assertions_passed'] else 'differences'
        report['source_fixture_unchanged']=manifest(fixture)==pinned['files']
        if not report['source_fixture_unchanged']:raise ValueError('Source fixture mutated')
    except (OSError,ValueError,KeyError,TypeError) as error:report.update(verdict='failed',error=str(error))
    report['tool_sources']={str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),ROOT/'tools/phase0/effect_cycle.py']}
    write(out/'result.json',report);write(ROOT/'docs/compatibility/evidence/live-clock-results.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['stages','tool_sources']},indent=2))
    return 0 if report['verdict']=='passed-bounded-live-clock' else 1

if __name__=='__main__':raise SystemExit(main())
