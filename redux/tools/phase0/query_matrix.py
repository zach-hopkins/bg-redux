"""Batched hand and missing-target controls using generated BCS/autosaves."""
import datetime
import json
from pathlib import Path
import uuid
import shutil
from harness import ROOT,LOCAL,digest
from save_harness import manifest,write,member
from legacy_oracle import read_wire
from effect_cycle import run_stage
from script_query_probe import prepare,trigger,action,response,PLAYER2
from scan_weapon_triggers import condition_blocks

PLAYER6='0 0 0 0 0 0 0 26 0 0 0 0 ""'
CASES=[dict(key=f'RDXM{kind}{hand}',opcode=opcode,hand=hand,target='Player2',object=PLAYER2)
    for hand in (1,2,3) for kind,opcode in [('VE',0x40ec),('VD',0x40f2)]]+[
    dict(key='RDXMVE6',opcode=0x40ec,hand=1,target='Player6-absent',object=PLAYER6),
    dict(key='RDXMVD6',opcode=0x40f2,hand=1,target='Player6-absent',object=PLAYER6)]


def program():
    source='SC\n'
    for stage,case in enumerate(CASES):
        gate=trigger(0x400f,stage,'GLOBALRDXMSTAGE')
        for truth in (True,False):
            cond=gate+(trigger(case['opcode'],case['hand'],obj=case['object']) if truth else '')
            source+=response(cond,[action(30,int(truth),'GLOBAL'+case['key']),action(30,stage+1,'GLOBALRDXMSTAGE')])
    source+=response(trigger(0x400f,len(CASES),'GLOBALRDXMSTAGE'),
        [action(30,1,'GLOBALRDXMDONE'),action(30,len(CASES)+1,'GLOBALRDXMSTAGE'),action(190,0)])
    return (source+'SC\n').encode('ascii')


def values(globals):
    if globals.get('RDXMDONE')!=1 or globals.get('RDXMSTAGE')!=len(CASES)+1:
        raise ValueError('Matrix completion missing')
    result={c['key']:globals.get(c['key']) for c in CASES}
    if any(type(v) is not int or v not in (0,1) for v in result.values()):raise ValueError('Matrix Boolean missing/invalid')
    return result


def prepare_original():
    """File preparation only; close the private game before calling."""
    report=json.loads((ROOT/'docs/compatibility/evidence/query-matrix-results.json').read_text())
    if report['verdict']!='gemrb-matrix-executed':raise ValueError('Matrix prototype not completed')
    seed=Path(report['directory']);game=LOCAL/'original-query-game';profile=LOCAL/'original-query-profile-matrix'
    if profile.exists():raise ValueError('Refuse to overwrite matrix profile')
    if (game/'steam_api64.dll').exists() or not (game/'steam_api64.dll.phase0-retained').exists():raise ValueError('Private library isolation missing')
    if manifest(seed/'query-input')!=report['construction']['input_files']:raise ValueError('Matrix fixture drift')
    script=seed/'query-override/RDXMPROB.bcs'
    if digest(script)!=report['construction']['matrix_script_sha256']:raise ValueError('Matrix script drift')
    if (game/'override/RDXMPROB.bcs').exists():raise ValueError('Refuse to replace matrix script')
    profile.mkdir();(profile/'save').mkdir()
    shutil.copytree(seed/'query-input',profile/'save/000000007-Redux Matrix')
    shutil.copy2(LOCAL/'original-query-profile-local/Baldur.lua',profile/'Baldur.lua')
    shutil.copy2(script,game/'override/RDXMPROB.bcs')
    (game/'engine.lua').write_text('engine_name = "ChatGPT/BG Multiplayer Redux/phase0-local/original-query-profile-matrix"\nengine_mode = 1\n')
    receipt=dict(schema='bg-redux-original-matrix-preparation/1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        game=str(game),profile=str(profile),executable_sha256=digest(game/'Baldur.exe'),script_sha256=digest(script),
        fixture_files=manifest(profile/'save/000000007-Redux Matrix'),gemrb_evidence_sha256=digest(ROOT/'docs/compatibility/evidence/query-matrix-results.json'))
    write(ROOT/'docs/compatibility/evidence/original-matrix-preparation.json',receipt)
    print(json.dumps(receipt,indent=2))


def main():
    out=LOCAL/'results'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-query-matrix-'+uuid.uuid4().hex[:8]);out.mkdir()
    report=dict(schema='bg-redux-query-matrix/1',directory=str(out),verdict='failed',cases=CASES)
    try:
        fixture,override,construction=prepare(out)
        gam=fixture/'BALDUR.gam';data=bytearray(gam.read_bytes())
        offset=construction['declared_script_assignments'][0]['offset'];data[offset:offset+8]=b'RDXMPROB';gam.write_bytes(data)
        script=override/'RDXMPROB.bcs';script.write_bytes(program())
        # The unused prototype script stays in this declared private override.
        hits,total=condition_blocks(program())
        if len(hits)!=len(CASES) or total!=len(CASES)*3+1:raise ValueError('Matrix script validation failed')
        construction['declared_script_assignments'][0]['value']='RDXMPROB'
        construction.update(input_files=manifest(fixture),matrix_script_sha256=digest(script),
            matrix_trigger_records=total,semantics='Eight query cases: Player2 hands1/2/3, absent Player6 MAINHAND; unchanged baseline items/stats/effects; replaced party scripts; automatic slot0 save')
        report['construction']=construction
        stage,_=run_stage(out,'gemrb',fixture,override,'live-clock',30,['--clock-running-samples','80']);report['process']=stage['process']
        if report['process']['exit_code']!=0 or report['process']['timed_out']:raise ValueError('Native matrix process failed')
        completed=[];report['saved_observations']=[]
        for saved in (out/'gemrb/engine-profile/save').iterdir():
            if not saved.is_dir() or saved.name=='000000007-HarnessInput':continue
            gam=member(saved,'gam')
            globals=read_wire(gam)['globals'];report['saved_observations'].append(dict(folder=saved.name,globals={k:v for k,v in globals.items() if k.startswith('RDXM')}))
            if globals.get('RDXMDONE')==1:completed.append((saved,values(globals)))
        if not completed:raise ValueError('No completed matrix autosave')
        saved,report['query_values']=completed[0];report['autosave_files']=manifest(saved)
        report['verdict']='gemrb-matrix-executed'
    except (OSError,ValueError,KeyError,TypeError) as error:report['error']=str(error)
    report['source_sha256']=digest(Path(__file__))
    write(out/'result.json',report);write(ROOT/'docs/compatibility/evidence/query-matrix-results.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('construction','saved_observations','autosave_files')},indent=2))
    return 0 if report['verdict']=='gemrb-matrix-executed' else 1


if __name__=='__main__':raise SystemExit(main())
