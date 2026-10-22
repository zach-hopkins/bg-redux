"""Coordinator-invoked two-process hotkey journey; no external player attachment.

Each launch owns a fresh profile/game root. Process B receives only A's exact
saved INI plus a fresh save copy, never A's process memory or other profile files.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import uuid

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('hotkey_menu_harness', HERE / 'menu_harness.py')
menu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(menu)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def ini_bytes(bindings):
    return ('; GemRB profile bindings v1; original game keymap is unchanged.\n[Bindings]\n' +
            ''.join('%s=%s\n' % (name, key) for name, key in sorted(bindings.items()))).encode('ascii')


def visible(ui, pack):
    return any(r.get('pack') == pack and r.get('window') == 2 and r.get('visible') is True
               for r in ui.get('controls', []))


def capture(directory, number, resolution):
    if type(number) is not int or number < 1:
        raise ValueError('Missing/invalid observation capture')
    prefix = directory / ('capture-%d' % number)
    bmp = prefix.with_suffix('.bmp').read_bytes()
    if len(bmp) < 54 or bmp[:2] != b'BM' or struct.unpack_from('<I', bmp, 2)[0] != len(bmp):
        raise ValueError('Missing/truncated hotkey screenshot')
    width, height = struct.unpack_from('<ii', bmp, 18)
    if [width, abs(height)] != list(resolution):
        raise ValueError('Hotkey screenshot resolution mismatch')
    for suffix in ('.state.json', '.observer.json'):
        read(str(prefix) + suffix)
    return read(str(prefix) + '.ui.json')


def validate_stage(directory, pin, resolution=(1024, 768)):
    directory = Path(directory)
    runtime, host = read(directory / 'hotkey-runtime.json'), read(directory / 'menu-host-result.json')
    if (runtime.get('schema') != 'bg-redux-hotkey-runtime/1' or runtime.get('nonce') != pin['nonce']
            or host.get('nonce') != pin['nonce'] or runtime.get('mode') != pin['mode']
            or host.get('journey') != pin['mode']):
        raise ValueError('Wrong/stale hotkey journey identity')
    if not runtime.get('completed') or not host.get('completed') or runtime['steps'] != runtime['planned_steps']:
        raise ValueError('Incomplete hotkey journey')
    if not runtime.get('process', {}).get('startup_nonce') or not runtime['process'].get('pid'):
        raise ValueError('Missing fresh process identity')
    base = runtime['baseline']
    if not base or set(base) != set(runtime['defaults']) or base != runtime['defaults']:
        raise ValueError('Vanilla/default action inventory differs')
    for name in ('inventory', 'character_record', 'journal'):
        if name not in base or len(base[name]) != 1 or base[name] not in 'abcdefghijklmnopqrstuvwxyz':
            raise ValueError('Required plain key route absent')
    if len({base[a] for a in ('inventory', 'character_record', 'journal')}) != 3:
        raise ValueError('Required plain menu keys overlap')
    swap = dict(base, inventory=base['character_record'], character_record=base['inventory'])
    if runtime.get('expected_swapped') != swap:
        raise ValueError('Runtime swap description differs from independently derived swap')
    reload = pin['mode'] == 'hotkeys-reload'
    if reload and (base != pin['baseline'] or swap != pin['expected_bindings']):
        raise ValueError('Reload does not match first-process baseline/persisted map')
    states = {}
    expected_profile = str((Path(pin['profile']) / 'gemrb-keymap.ini').resolve())
    for state in runtime['states']:
        if state['name'] in states or state.get('nonce') != pin['nonce']:
            raise ValueError('Duplicate/stale hotkey checkpoint')
        states[state['name']] = state
        observed = state['profile']
        if observed.get('path') != expected_profile:
            raise ValueError('Checkpoint read the wrong profile')
        if observed.get('exists') is True:
            data = bytes.fromhex(observed['bytes_hex'])
            if hashlib.sha256(data).hexdigest() != observed.get('sha256'):
                raise ValueError('Profile observation hash/content differs')
        elif observed.get('exists') is not False or observed.get('bytes_hex') is not None or observed.get('sha256') is not None:
            raise ValueError('Unknown/malformed absent profile observation')
        capture(directory, state['capture'], resolution)
    partial = dict(base, inventory=base['character_record'], character_record='')
    cleared = dict(base, inventory='')
    contracts = {'initial': (swap if reload else base, None, swap if reload else None),
                 'final': (swap, None, swap), 'mouse-inventory': (swap, None, swap)}
    if reload:
        contracts['reload-editor'] = (swap, swap, swap)
    else:
        contracts.update({'conflict-rejected': (base, base, None), 'replace-staged': (base, partial, None),
            'cancelled': (base, None, None), 'clear-staged': (base, cleared, None),
            'clear-cancelled': (base, None, None), 'swap-staged': (base, swap, None),
            'applied': (swap, None, swap), 'defaults-staged': (swap, base, swap),
            'defaults-cancelled': (swap, None, swap), 'defaults-applied': (base, None, base),
            'final-applied': (swap, None, swap)})
    for name, (live, staged, persisted) in contracts.items():
        if name not in states:
            raise ValueError('Missing required checkpoint: ' + name)
        state = states[name]
        if state['bindings'] != live or state['staged'] != staged or state['editor_open'] is not (staged is not None):
            raise ValueError('Native/staged/closed state differs: ' + name)
        if staged is not None:
            selected = state.get('selected')
            if selected not in staged or state.get('selected_label') != selected.replace('_', ' ').title():
                raise ValueError('Actual selected action label differs: ' + name)
            label = selected.replace('_', ' ').title() + ' : ' + (staged[selected].upper() or 'Unbound')
            if label not in state.get('visible_rows', []):
                raise ValueError('Actual visible staged row differs: ' + name)
        expected_data = ini_bytes(persisted) if persisted is not None else None
        actual_data = bytes.fromhex(state['profile']['bytes_hex']) if state['profile']['exists'] else None
        if actual_data != expected_data:
            raise ValueError('Persistence or cancel boundary differs: ' + name)
    if not reload and 'assigned to' not in states['conflict-rejected'].get('status', ''):
        raise ValueError('Explicit conflict refusal not observed')
    callback_rows = runtime['callbacks']
    if [r['sequence'] for r in callback_rows] != list(range(1, len(callback_rows) + 1)) or len(callback_rows) != host['callbacks']:
        raise ValueError('Native callback inventory incomplete/ambiguous')
    actions = {}
    for row in callback_rows:
        native = read(directory / ('callback-%d.json' % row['sequence']))
        if native.get('schema') != 'bg-redux-callback-dispatch/1' or native.get('performed') is not True:
            raise ValueError('Actual registered callback execution missing')
        for field in ('sequence', 'pack', 'window', 'control', 'nonce'):
            if native.get(field) != row[field]: raise ValueError('Callback target/nonce mismatch')
        if row['nonce'] != pin['nonce']: raise ValueError('Stale callback request')
        actions[row['action']] = row
    required = {'reload.cancel': 14} if reload else {
        'conflict.assign': 6001, 'conflict.replace': 6003, 'cancel.callback': 14, 'clear.callback': 6002,
        'clear.cancel': 14, 'apply.replace': 6003, 'apply.assign': 6001, 'apply.callback': 11,
        'defaults-cancel.callback': 6004, 'defaults-cancel.cancel': 14,
        'defaults-apply.defaults': 6004, 'defaults-apply.apply': 11,
        'final.replace': 6003, 'final.assign': 6001, 'final.apply': 11}
    for name, cid in required.items():
        row = actions.get(name, {})
        if (row.get('pack'), row.get('window'), row.get('control')) != ('WIN_KEYS', 0, cid):
            raise ValueError('Required editor callback not executed: ' + name)
    mouse = actions.get('inventory.mouse-callback', {})
    if (mouse.get('pack'), mouse.get('window'), mouse.get('control')) != ('OPTWIN', 0, 3):
        raise ValueError('Existing inventory mouse callback not executed')
    mouse_state = states['mouse-inventory']
    mouse_ui = capture(directory, mouse_state['capture'], resolution)
    if (mouse_state.get('step') != mouse.get('step', -2) + 1 or not visible(mouse_ui, 'GUIINV')
            or any(visible(mouse_ui, pack) for pack in ('GUIREC', 'GUIJRNL'))):
        raise ValueError('Registered mouse callback did not open inventory at the next boundary')
    expected_routes = {prefix + '.' + action: (mapping[action], pack, mapping, None if prefix=='original' else mapping)
        for prefix, mapping in ([('reloaded', swap)] if reload else [('original', base), ('swapped', swap), ('restored', base), ('final', swap)])
        for action, pack in (('inventory', 'GUIINV'), ('character_record', 'GUIREC'), ('journal', 'GUIJRNL'))}
    keys = runtime['keys']
    if len(keys) != len(expected_routes) or len(keys) != host['native_keys'] or [r['sequence'] for r in keys] != list(range(1, len(keys)+1)):
        raise ValueError('Native EventMgr key inventory incomplete/ambiguous')
    seen = set()
    for row in keys:
        name = row.get('observation')
        if name in seen or name not in expected_routes: raise ValueError('Missing/duplicate actual key outcome')
        seen.add(name)
        key, pack, current_map, persisted = expected_routes[name]
        if row.get('key') != key or row.get('nonce') != pin['nonce'] or row.get('observed_step') != row['step'] + 1:
            raise ValueError('Key request/observation boundary differs')
        if row.get('bindings_before') != current_map or row.get('bindings_after') != current_map:
            raise ValueError('Key dispatch native bindings differ before/after')
        expected_data = ini_bytes(persisted) if persisted is not None else None
        for phase in ('before', 'after'):
            snapshot = row.get('profile_'+phase, {})
            data = bytes.fromhex(snapshot['bytes_hex']) if snapshot.get('exists') else None
            if (snapshot.get('path') != expected_profile or data != expected_data
                    or snapshot.get('sha256') != (hashlib.sha256(data).hexdigest() if data is not None else None)):
                raise ValueError('Key dispatch profile pin differs before/after')
        native = read(directory / ('key-%d.json' % row['sequence']))
        expected_native = dict(schema='bg-redux-key-dispatch/1', nonce=pin['nonce'], keycode=ord(key),
                               sequence=row['sequence'], modifiers=0, keydown_dispatched=True, keyup_dispatched=True,
                               route='EventMgr::DispatchEvent', os_input_injected=False)
        if any(native.get(k) != v or type(native.get(k)) is not type(v) for k, v in expected_native.items()):
            raise ValueError('Actual EventMgr down/up dispatch not observed')
        before = read(directory / ('key-%d-before.ui.json' % row['sequence']))
        if any(visible(before, p) for p in ('GUIINV', 'GUIREC', 'GUIJRNL')):
            raise ValueError('Key target was already open before dispatch')
        for suffix in ('state', 'observer'):
            if (read(directory/('key-%d-before.%s.json'%(row['sequence'],suffix))) !=
                    read(directory/('key-%d-after.%s.json'%(row['sequence'],suffix)))):
                raise ValueError('Collected key dispatch state changed')
        ui = capture(directory, row['capture'], resolution)
        if not visible(ui, pack) or any(visible(ui, p) for p in ('GUIINV', 'GUIREC', 'GUIJRNL') if p != pack):
            raise ValueError('Actual key opened wrong/missing/ambiguous window')
    final_data = bytes.fromhex(states['final']['profile']['bytes_hex'])
    actual_final = (Path(pin['profile']) / 'gemrb-keymap.ini').read_bytes()
    if actual_final != final_data or (reload and hashlib.sha256(final_data).hexdigest() != pin['profile_sha256']):
        raise ValueError('Persisted final profile differs from frozen/cross-process pin')
    for suffix in ('state', 'observer'):
        if read(directory / ('before.'+suffix+'.json')) != read(directory / ('after.'+suffix+'.json')):
            raise ValueError('Collected game/observer state changed during hotkey-only journey')
    return dict(passed=True, baseline=base, persisted_bindings=swap, profile_sha256=hashlib.sha256(final_data).hexdigest(),
                process=runtime['process'], callbacks=len(callback_rows), eventmgr_key_pairs=len(keys),
                physical_typing_observed=False, pointer_hit_testing=False, hidden_rng_identity_proven=False,
                modifier_international_function_fidelity=False)


def validate_pair(stages):
    if len(stages) != 2 or [r['mode'] for r in stages] != ['hotkeys-edit', 'hotkeys-reload']:
        raise ValueError('Exactly two ordered native launches are required')
    first, second = stages
    if (first['pin']['profile'] == second['pin']['profile'] or first['pin']['nonce'] == second['pin']['nonce']
            or first['validation']['process']['startup_nonce'] == second['validation']['process']['startup_nonce']):
        raise ValueError('Reload profile/process identity is not fresh')
    for row in stages:
        if row['validation']['process']['pid'] != row['process']['owned_pid']:
            raise ValueError('Runtime observations belong to another process')
    if (first['validation']['profile_sha256'] != second['validation']['profile_sha256']
            or second['pin']['profile_sha256'] != first['validation']['profile_sha256']
            or first['validation']['persisted_bindings'] != second['validation']['persisted_bindings']
            or first['validation']['baseline'] != second['validation']['baseline']):
        raise ValueError('Cross-process persistence pin differs')
    return dict(two_fresh_profiles=True, two_owned_processes=True, exact_saved_profile_reloaded=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'build', 'prefix', 'output-root', 'probe', 'fixture', 'game'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=360)
    args = parser.parse_args()
    directory = args.output_root / (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-hotkeys-' + uuid.uuid4().hex[:8])
    directory.mkdir(parents=True, exist_ok=False)
    source_files = [HERE/'hotkey_harness.py', HERE/'gui/HotkeyRuntime.py', HERE/'gui/MenuRuntime.py',
                    HERE/'gui/MenuStart.py', HERE/'menu_probe.cpp', HERE/'menu_harness.py', HERE/'private_game.py',
                    HERE/'../phase0/native/gui_probe.cpp', HERE/'../phase0/native/save_probe.cpp']
    source_files += [args.source/'gemrb/GUIScripts'/name for name in
                     ('GUIHotkeys.py','KeyBindingEditor.py','MenuWindow.py','GUIOPT.py','GUIOPTExtra.py')]
    inputs = {str(p): menu.sha(p) for p in source_files}
    dll = args.build/'gemrb/libgemrb_core.dll'
    plugin_files = sorted((args.build/'gemrb/plugins').rglob('*.dll'))
    protected = dict(dll=menu.sha(dll), probe=menu.sha(args.probe), fixture=menu.manifest(args.fixture),
                     plugin_dlls={str(p):menu.sha(p) for p in plugin_files})
    result = dict(schema='bg-redux-hotkey-journey/1', source_files=inputs, protected=protected, stages=[])
    menu.write(directory/'preparation.json', result)
    if not protected['fixture'] or not (args.fixture/'BALDUR.GAM').is_file():
        raise ValueError('Required vanilla private save fixture absent')
    first = None
    for mode in ('hotkeys-edit', 'hotkeys-reload'):
        stage = directory/mode
        stage.mkdir()
        profile = stage/'profile'
        save = profile/'save/000000007-HarnessInput'
        shutil.copytree(args.fixture, save)
        (stage/'cache').mkdir()
        private = menu.private_game.prepare(args.game, stage/'game')
        menu.write(stage/'private-game-preparation.json', private)
        pin = dict(mode=mode, nonce=uuid.uuid4().hex, profile=str(profile.resolve()))
        if first:
            data = (directory/'hotkeys-edit/profile/gemrb-keymap.ini').read_bytes()
            if hashlib.sha256(data).hexdigest() != first['profile_sha256']:
                raise ValueError('First process profile changed before reload copy')
            (profile/'gemrb-keymap.ini').write_bytes(data)
            pin.update(profile_sha256=first['profile_sha256'], baseline=first['baseline'],
                       expected_bindings=first['persisted_bindings'])
        menu.write(stage/'journey-input.json', pin)
        cfg = stage/'hotkeys.cfg'
        config = dict(GameType='bg2ee', GameName='BG Redux hotkeys '+pin['nonce'], GamePath=stage/'game',
            GemRBPath=args.source/'gemrb', GUIScriptsPath=args.source/'gemrb', GemRBOverridePath=args.source/'gemrb',
            GemRBUnhardcodedPath=args.source/'gemrb', PluginsPath=args.build/'gemrb/plugins', CachePath=stage/'cache',
            SavePath=profile, UseAsLibrary=0, Width=1024, Height=768, FullScreen=0, CapFPS=30, AudioDriver='none',
            GameLanguagePath='lang/en_US', SkipIntroVideos=1, Logging=1, LogColor=0,
            PathfinderThreadsCount=0, PathfinderMainThreadMode='immediate')
        cfg.write_text(''.join('%s=%s\n' % (k,str(v).replace('\\','/')) for k,v in config.items()), encoding='utf-8')
        config_hash = menu.sha(cfg)
        env = os.environ.copy()
        env.update(HOME=str(profile), USERPROFILE=str(profile), APPDATA=str(profile/'AppData/Roaming'))
        env['PATH'] = os.pathsep.join([str(args.prefix/'bin'), str(args.build/'gemrb'), env.get('PATH','')])
        command = [str(args.probe), '--config', str(cfg), '--output', str(stage), '--scripts', str(HERE/'gui'),
                   '--journey', mode, '--nonce', pin['nonce']]
        row = dict(mode=mode, pin=pin, process=menu.run_owned(command,args.build,env,stage/'process.log',args.timeout))
        try:
            row['private_game'] = menu.private_game.validate(private)
            row['validation'] = validate_stage(stage,pin)
            if menu.sha(cfg) != config_hash or menu.manifest(save) != protected['fixture']:
                raise ValueError('Private launch config/save inputs changed')
            if row['process']['exit_code'] != 0 or row['process']['timed_out'] or not row['process']['cleanup_complete']:
                raise ValueError('Owned native process did not complete successfully')
            if row['validation']['process']['pid'] != row['process']['owned_pid']:
                raise ValueError('Runtime observations belong to another process')
            if first and row['validation']['process']['startup_nonce'] == first['process']['startup_nonce']:
                raise ValueError('Reload reused the first native process identity')
            row['passed'] = True
            first = row['validation']
        except (ValueError, OSError, KeyError, TypeError, IndexError) as error:
            row.update(passed=False, error=str(error))
        menu.write(stage/'result.json',row)
        result['stages'].append(row)
        menu.write(directory/'result.json',result)
        if not row['passed']: break
    result['protected_inputs_unchanged'] = (menu.sha(dll)==protected['dll'] and menu.sha(args.probe)==protected['probe']
        and menu.manifest(args.fixture)==protected['fixture'] and all(menu.sha(Path(p))==h for p,h in inputs.items())
        and {str(p):menu.sha(p) for p in (args.build/'gemrb/plugins').rglob('*.dll')}==protected['plugin_dlls'])
    result['passed'] = len(result['stages'])==2 and all(s['passed'] for s in result['stages']) and result['protected_inputs_unchanged']
    if result['passed']:
        try:
            result['cross_process_validation'] = validate_pair(result['stages'])
        except (ValueError, KeyError) as error:
            result.update(passed=False, error=str(error))
    menu.write(directory/'result.json',result)
    # Do not recurse through private game junctions when freezing the evidence inventory.
    menu.write(directory/'artifact-manifest.json',menu.artifact_manifest(directory))
    print(directory)
    return 0 if result['passed'] else 1


if __name__ == '__main__': raise SystemExit(main())
