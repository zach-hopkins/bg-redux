"""Freeze an observed original BCS batch and compare explicit query Booleans."""
import datetime
import json
from pathlib import Path
import shutil
import uuid
from harness import ROOT,LOCAL,digest
from save_harness import manifest,write
from legacy_oracle import read_wire
from query_matrix import CASES,values
from capture_original_query import bind_receipt


def main():
    out=LOCAL/'results'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-original-query-matrix-'+uuid.uuid4().hex[:8]);out.mkdir()
    result=dict(schema='bg-redux-original-query-matrix/1',directory=str(out),verdict='failed')
    try:
        receipt_path=ROOT/'docs/compatibility/evidence/original-matrix-observation.json';receipt=json.loads(receipt_path.read_text())
        game=LOCAL/'original-query-game';profile=LOCAL/'original-query-profile-matrix'
        fixture=profile/'save/000000007-Redux Matrix';saved=profile/'save/000000000-Auto-Save'
        bind_receipt(receipt,game/'Baldur.exe',game/'override/RDXMPROB.bcs',fixture,saved)
        gemrb_path=ROOT/'docs/compatibility/evidence/query-matrix-results.json';gemrb=json.loads(gemrb_path.read_text())
        if gemrb['verdict']!='gemrb-matrix-executed':raise ValueError('GemRB matrix incomplete')
        if manifest(fixture)!=gemrb['construction']['input_files'] or digest(game/'override/RDXMPROB.bcs')!=gemrb['construction']['matrix_script_sha256']:raise ValueError('Matrix input/script mismatch')
        before=manifest(saved);shutil.copytree(saved,out/'original-autosave')
        if manifest(saved)!=before or manifest(out/'original-autosave')!=before:raise ValueError('Output drift during freeze')
        original=values(read_wire(out/'original-autosave/BALDUR.gam')['globals'])
        candidates=[p for p in (Path(gemrb['directory'])/'gemrb/engine-profile/save').iterdir() if p.is_dir() and manifest(p)==gemrb['autosave_files']]
        if not candidates:raise ValueError('Completed GemRB autosave unavailable/drifted')
        other=values(read_wire(candidates[0]/'BALDUR.gam')['globals'])
        if other!=gemrb['query_values']:raise ValueError('GemRB result does not match its autosave')
        rows=[dict(case=c['key'],hand=c['hand'],target=c['target'],opcode=c['opcode'],original=original[c['key']],gemrb=other[c['key']],equal=original[c['key']]==other[c['key']]) for c in CASES]
        result.update(verdict='matrix-observed',comparisons=rows,mismatches=sum(not r['equal'] for r in rows),
            cases=len(rows),receipt=receipt,receipt_sha256=digest(receipt_path),gemrb_evidence_sha256=digest(gemrb_path),
            autosave_files=before,scope='Same baseline fists/no offhand item, three hand selectors and absent party member; sequential queries with uncontrolled area scripts/time')
    except (OSError,ValueError,KeyError,TypeError) as error:result['error']=str(error)
    result['source_sha256']=digest(Path(__file__))
    write(out/'result.json',result);write(ROOT/'docs/compatibility/evidence/original-query-matrix-results.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('receipt','autosave_files')},indent=2))
    return 0 if result['verdict']=='matrix-observed' else 1


if __name__=='__main__':raise SystemExit(main())
