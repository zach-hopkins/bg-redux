"""Prepare an isolated copy of installed BG2EE for a generated BCS query fixture.

Does not launch or automate any application. No original assets/profile are edited.
"""
import datetime
import json
from pathlib import Path
import shutil
from harness import ROOT,LOCAL,digest
from save_harness import write,manifest

def main():
    result=json.loads((ROOT/'docs/compatibility/evidence/script-query-results.json').read_text(encoding='utf-8'))
    if result['verdict']!='gemrb-script-prototype-executed':raise ValueError('GemRB script prototype not validated')
    seed=Path(result['directory'])
    if manifest(seed/'query-input')!=result['construction']['input_files']:raise ValueError('Query fixture drift')
    original=json.loads((ROOT/'docs/compatibility/evidence/bg2ee-copy-manifest.json').read_text(encoding='utf-8'))
    source=Path(original['source']);game=LOCAL/'original-query-game';profile=LOCAL/'original-query-profile'
    if game.exists() or profile.exists():raise ValueError('Destination exists; refuse to overwrite')
    game.mkdir();profile.mkdir()
    for row in original['files']:
        dest=game/row['path'];dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source/row['path'],dest)
        if digest(dest)!=row['sha256']:raise ValueError('Original data copy hash mismatch: '+row['path'])
    engine_name='ChatGPT/BG Multiplayer Redux/phase0-local/original-query-profile'
    (game/'engine.lua').write_text('engine_name = "'+engine_name+'"\nengine_mode = 1\n',encoding='ascii')
    override=game/'override';override.mkdir()
    shutil.copy2(seed/'query-override/RDXQPROB.bcs',override/'RDXQPROB.bcs')
    (profile/'save').mkdir()
    shutil.copytree(seed/'query-input',profile/'save/000000007-Redux Query')
    (profile/'Baldur.lua').write_text("SetPrivateProfileString('Program Options','Full Screen','0')\nSetPrivateProfileString('Program Options','Screen Width','1280')\nSetPrivateProfileString('Program Options','Screen Height','720')\nSetPrivateProfileString('Program Options','Language','en_US')\n",encoding='ascii')
    receipt=dict(schema='bg-redux-original-query-preparation/1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        game=str(game),profile=str(profile),source_files_copied=len(original['files']),copied_original_hashes_match=True,
        executable_sha256=digest(game/'Baldur.exe'),generated_script_sha256=digest(override/'RDXQPROB.bcs'),
        intentional_differences=['Private engine.lua profile name','New generated override/RDXQPROB.bcs','Private declared CRE script assignment fixture and initial config'],
        fixture_files=manifest(profile/'save/000000007-Redux Query'),source_query_run=result['directory'],
        original_executed=False,source_sha256=digest(Path(__file__)))
    write(ROOT/'docs/compatibility/evidence/original-query-preparation.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='fixture_files'},indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
