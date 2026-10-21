"""Stage a private Windows VM handoff; verify copied game bytes and preserve engine code."""
import datetime
import json
import shutil
import subprocess
from pathlib import Path
from harness import ROOT, LOCAL, digest
from save_harness import manifest, write


def main():
    destination = LOCAL / 'vm-transfer' / datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination.mkdir(parents=True, exist_ok=False)
    guest = destination / 'BGRedux'
    guest.mkdir()
    status = subprocess.check_output(['git', '-C', str(ROOT/'gemrb'), 'status', '--porcelain'], text=True)
    if status.strip():
        raise ValueError('Engine checkout is not clean; review before migration')
    selections = ['gemrb', 'docs', 'tools/phase0', 'phase0-local/build',
                  'phase0-local/toolchain/msys64/ucrt64', 'phase0-local/fixtures']
    for name in selections:
        shutil.copytree(ROOT/name, guest/name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        print('Copied', name, flush=True)
    game_manifest = json.loads((ROOT/'docs/compatibility/evidence/bg2ee-copy-manifest.json').read_text(encoding='utf-8'))
    for item in game_manifest['files']:
        relative = Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe resource path')
        source = LOCAL/'bg2ee-clean'/relative
        target = guest/'phase0-local/bg2ee-clean'/relative
        if digest(source) != item['sha256']:
            raise ValueError('Manifested game source drift: ' + str(relative))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if digest(target) != item['sha256']:
            raise ValueError('Copied game hash mismatch: ' + str(relative))
    for folder in ['results', 'logs', 'config', 'gui-probe', 'native-probe']:
        (guest/'phase0-local'/folder).mkdir(parents=True, exist_ok=True)
    # These mutation tests require real historical snapshots, even before a guest game run.
    oracle_roots = []
    for pattern in ['*gui-stock-verified*', '*vanilla-oracle*']:
        candidates = list((LOCAL/'results').glob(pattern))
        if not candidates:
            raise ValueError('Required historical oracle absent: ' + pattern)
        selected = max(candidates, key=lambda p: p.stat().st_mtime)
        shutil.copytree(selected, guest/'phase0-local/results'/selected.name)
        oracle_roots.append(selected.name)
    shutil.copy2(ROOT/'tools/phase0/vm-guest-check.ps1', destination/'vm-guest-check.ps1')
    files = manifest(guest)
    receipt = dict(schema='bg-redux-private-vm-transfer/1', utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        destination=str(destination), guest_destination='C:/BGRedux', copied_roots=selections,
        files=files, file_count=len(files), bytes=sum(v['bytes'] for v in files.values()),
        game_files_verified=len(game_manifest['files']), engine_revision=subprocess.check_output(['git','-C',str(ROOT/'gemrb'),'rev-parse','HEAD'],text=True).strip(),
        historical_oracle_runs=oracle_roots,
        excluded=['host account credentials', 'personal Documents game profiles', 'other Redux chats/projects',
                  'historical phase0-local/results except two required oracle runs', 'MSYS2 host accounts/configuration', 'old native host executables/receipts'],
        relocation=['Copied CMake cache contains host paths: do not rebuild engine in this build directory.',
                    'Rebuild external native hosts in guest to generate new local-path receipts.',
                    'Historical audit JSON paths/provenance remain host records; do not relabel as guest execution.',
                    'Only original-vanilla fixture is included; optional fixture entries may be absent.'],
        engine_git_status=status, vm_created=False, guest_booted=False, guest_tests_executed=False)
    write(destination/'transfer-manifest.json',receipt)
    compact={k:v for k,v in receipt.items() if k!='files'}
    compact['manifest_sha256']=digest(destination/'transfer-manifest.json')
    write(ROOT/'docs/compatibility/evidence/vm-transfer-preparation.json', compact)
    print(json.dumps(compact,indent=2))


if __name__ == '__main__':
    main()
