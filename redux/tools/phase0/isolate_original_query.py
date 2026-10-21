"""Prepare a fresh diagnostic profile without optional Steam integration.

Run after closing that copy. Retains its Steam library under an inert name;
never edits the installed game or account's Steam settings. Launch from the
game folder and verify no imports. Cloud Saves Enabled=0 alone was insufficient.
"""
import datetime
import json
import shutil
from pathlib import Path
from harness import ROOT, LOCAL, digest
from save_harness import manifest, write


def main():
    preparation=json.loads((ROOT/'docs/compatibility/evidence/original-query-preparation.json').read_text())
    game=(LOCAL/'original-query-game').resolve()
    if game!=Path(preparation['game']).resolve():raise ValueError('Unexpected private game')
    if digest(game/'Baldur.exe')!=preparation['executable_sha256']:raise ValueError('Executable drift')
    source=LOCAL/'original-query-profile/save/000000007-Redux Query'
    if manifest(source)!=preparation['fixture_files']:raise ValueError('Input fixture drift')
    profile=LOCAL/'original-query-profile-local'
    if profile.exists():raise ValueError('Refuse to overwrite diagnostic profile')
    dll=game/'steam_api64.dll';retained=game/'steam_api64.dll.phase0-retained'
    if not dll.is_file() or retained.exists():raise ValueError('Unexpected optional library state')
    dll_hash=digest(dll)
    old_engine=(game/'engine.lua').read_text()
    profile.mkdir();(profile/'save').mkdir()
    shutil.copytree(source,profile/'save/000000007-Redux Query')
    (profile/'Baldur.lua').write_text("SetPrivateProfileString('Window','Full Screen','0')\nSetPrivateProfileString('Program Options','Cloud Saves Enabled','0')\nSetPrivateProfileString('Program Options','Active Campaign','0')\nSetPrivateProfileString('MOVIES','INTRO15F','1')\nSetPrivateProfileString('MOVIES','LOGO','1')\nSetPrivateProfileString('MOVIES','INTRO','1')\n",encoding='ascii')
    (game/'engine.lua').write_text('engine_name = "ChatGPT/BG Multiplayer Redux/phase0-local/original-query-profile-local"\nengine_mode = 1\n',encoding='ascii')
    dll.rename(retained)
    report=dict(schema='bg-redux-original-query-isolation/1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        game=str(game),profile=str(profile),executable_sha256=digest(game/'Baldur.exe'),steam_dll_sha256=dll_hash,
        previous_engine_lua=old_engine,current_engine_lua_sha256=digest(game/'engine.lua'),
        fixture_files=manifest(profile/'save/000000007-Redux Query'),
        initial_profile_files=manifest(profile),launch_verified=False,cloud_isolation_verified=False,
        note='Optional Steam library retained under inert name in private copy. Launch from game folder and inspect Load Game before diagnostic autosaves. Configuration alone is not runtime attestation.')
    write(ROOT/'docs/compatibility/evidence/original-query-isolation.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
