"""Freeze one explicitly observed original-suite autosave, preserving raw results."""
import argparse
import datetime
import json
from pathlib import Path
import shutil
import uuid
from harness import ROOT,LOCAL,digest
from save_harness import manifest,write,member
from script_query_probe import query_values
from equipped_defenses import observe,validate_observation
from legacy_oracle import read_wire


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('case');parser.add_argument('--window-id',type=int,required=True)
    args=parser.parse_args();prepath=ROOT/'docs/compatibility/evidence/original-equipped-preparation.json';prep=json.loads(prepath.read_text())
    matches=[c for c in prep['cases'] if c['id']==args.case]
    if len(matches)!=1:raise ValueError('Unknown/ambiguous prepared case')
    case=matches[0];profile=Path(prep['profile']);game=Path(prep['game']);fixture=Path(case['folder']);saved=profile/'save/000000000-Auto-Save'
    out=LOCAL/'results'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-original-equipped-'+args.case+'-'+uuid.uuid4().hex[:8]);out.mkdir()
    result=dict(schema='bg-redux-original-equipped-case/1',case=case,directory=str(out),verdict='failed')
    try:
        if digest(game/'Baldur.exe')!=prep['executable_sha256'] or manifest(fixture)!=case['files']:raise ValueError('Executable/input drift')
        script='RDXQPROB.bcs' if case['kind']=='weapon-defense' else 'RDXAIPRB.bcs'
        if digest(game/'override'/script)!=prep['scripts'][script]:raise ValueError('Observed script drift')
        before=manifest(saved);gam=member(saved,'gam');g=read_wire(gam)['globals'];actors=observe(gam)
        if case['kind']=='weapon-defense':
            values=query_values(g);validate_observation(case['spec'],actors)
        else:
            if g.get('RDXAIDONE')!=1 or g.get('RDXFOESEEN')!=1 or g.get('RDXBRANCH') not in range(115,119):raise ValueError('Original AI branch/visibility marker missing')
            values={k:g[k] for k in ('RDXAIDONE','RDXFOESEEN','RDXBRANCH')};validate_observation(dict(weapon='sw1h02',defense=None),actors)
        shutil.copytree(saved,out/'autosave')
        if manifest(saved)!=before or manifest(out/'autosave')!=before:raise ValueError('Output changed during capture')
        result.update(verdict='original-case-observed',values=values,actors=actors,autosave_files=before,
            observation=dict(operator='Codex Computer Use / @oai/sky',window_id=args.window_id,
                window_title='ChatGPT/BG Multiplayer Redux/phase0-local/original-equipped-profile - v2.7.3.0',
                action='Observed private original GUI load of named prepared case, followed by script-generated autosave; no player attack/move commands issued',
                executable_sha256=digest(game/'Baldur.exe'),script_sha256=digest(game/'override'/script),input_files=manifest(fixture),
                original_execution_attestation=False),preparation_sha256=digest(prepath))
    except (OSError,ValueError,KeyError,TypeError) as error:result['error']=str(error)
    result['source_sha256']=digest(Path(__file__));write(out/'result.json',result)
    write(ROOT/'docs/compatibility/evidence'/('original-equipped-'+args.case+'.json'),result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('actors','autosave_files','observation','case')},indent=2))
    return 0 if result['verdict']=='original-case-observed' else 1


if __name__=='__main__':raise SystemExit(main())
