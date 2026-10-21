"""Freeze a computer-use-observed original query save; never launches a game."""
import datetime
import json
from pathlib import Path
import shutil
import uuid
from harness import ROOT, LOCAL, digest
from save_harness import write, manifest
from legacy_oracle import read_wire
from script_query_probe import query_values


def bind_receipt(receipt, exe, script, fixture, saved):
    if receipt.get('schema')!='bg-redux-original-query-observation/1' or receipt.get('sequence_completed') is not True:
        raise ValueError('Missing observed execution receipt')
    for key,path in [('executable',exe),('script',script)]:
        if Path(receipt[key]['path']).resolve()!=path.resolve() or receipt[key]['sha256']!=digest(path):
            raise ValueError('Observed '+key+' drift')
    for key,path in [('input',fixture),('output',saved)]:
        if receipt[key]['files']!=manifest(path) or Path(receipt[key]['path']).resolve()!=path.resolve():
            raise ValueError('Observed '+key+' drift')


def main():
    out=LOCAL/'results'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-original-script-query-'+uuid.uuid4().hex[:8]);out.mkdir()
    result=dict(schema='bg-redux-original-script-query/1',directory=str(out),verdict='failed')
    try:
        receipt_path=ROOT/'docs/compatibility/evidence/original-query-observation.json'
        receipt=json.loads(receipt_path.read_text())
        game=LOCAL/'original-query-game';profile=LOCAL/'original-query-profile-local'
        fixture=profile/'save/000000007-Redux Query';saved=profile/'save/000000000-Auto-Save'
        bind_receipt(receipt,game/'Baldur.exe',game/'override/RDXQPROB.bcs',fixture,saved)
        gemrb_path=ROOT/'docs/compatibility/evidence/script-query-results.json'
        gemrb=json.loads(gemrb_path.read_text())
        if gemrb['verdict']!='gemrb-script-prototype-executed':raise ValueError('GemRB query execution unavailable')
        if manifest(fixture)!=gemrb['construction']['input_files'] or digest(game/'override/RDXQPROB.bcs')!=gemrb['construction']['generated_script_sha256']:
            raise ValueError('Original/GemRB query input mismatch')
        before=manifest(saved);shutil.copytree(saved,out/'original-autosave')
        if manifest(saved)!=before or manifest(out/'original-autosave')!=before:raise ValueError('Autosave changed during freeze')
        original=query_values(read_wire(out/'original-autosave/BALDUR.gam')['globals'])
        other=query_values(gemrb['query_globals'])
        result.update(verdict='observed-query-difference' if original!=other else 'observed-query-match',
            original=original,gemrb=other,input_files=manifest(fixture),autosave_files=before,
            observation=receipt,receipt_sha256=digest(receipt_path),gemrb_evidence_sha256=digest(gemrb_path),
            limitations=['Single synthetic two-actor/fists MAINHAND case; not the full predicate contract',
                'Operator-observed UI execution bound to files, not process/module or network attestation',
                'Optional Steam library omitted from private copy; actor scripts intentionally replaced',
                'Area scripts/effects remain active; no deterministic time or RNG control'])
    except (OSError,ValueError,KeyError,TypeError) as error:result['error']=str(error)
    result['source_sha256']=digest(Path(__file__))
    write(out/'result.json',result);write(ROOT/'docs/compatibility/evidence/original-script-query-results.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('observation','input_files','autosave_files')},indent=2))
    return 0 if result['verdict'].startswith('observed-query-') else 1


if __name__=='__main__':raise SystemExit(main())
