"""Private-profile callback/key-event journey, run only by the owned native host.

Text input is populated explicitly; this does not claim physical typing/pointer
coverage. All editing operations use the actual registered control callbacks.
"""
import hashlib
import importlib
import json
import os
from pathlib import Path
import uuid
import GemRB
from GUIDefines import SV_SAVEPATH
import MenuRuntime as Menu

INPUT = None
MODE = None
NONCE = None
BASE = None
DEFAULTS = None
SWAPPED = None
STATES = []
REQUESTS = []
KEYS = []
PROCESS_IDENTITY = None


def profile():
    path = Path(GemRB.GetSystemVariable(SV_SAVEPATH)) / 'gemrb-keymap.ini'
    data = path.read_bytes() if path.exists() else None
    return dict(path=str(path.resolve()), exists=data is not None,
                sha256=hashlib.sha256(data).hexdigest() if data is not None else None,
                bytes_hex=data.hex() if data is not None else None)


def bindings():
    rows = GemRB.GetKeyBindings()
    values = {r['name']: r['key'] for r in rows}
    if len(values) != len(rows): raise RuntimeError('Duplicate native action binding')
    return values


def editor():
    return importlib.import_module('GUIHotkeys')


def checkpoint(name):
    module = editor()
    window = Menu.view('WIN_KEYS', 0)
    state = dict(name=name, nonce=NONCE, bindings=bindings(), profile=profile(),
                 editor_open=bool(window), staged=dict(module.Editor.working) if module.Editor else None,
                 defaults=dict(module.Editor.defaults) if module.Editor else None,
                 selected=module.Names[module.Selected] if module.Editor and module.Names else None,
                 status=window.GetControl(15).QueryText() if window else None,
                 visible_rows=[window.GetControl(5000+i).QueryText() for i in range(module.ROWS)
                               if window.GetControl(5000+i).IsVisible()] if window else [],
                 selected_label=window.GetControl(6008).QueryText() if window else None,
                 input_text=window.GetControl(6000).QueryText() if window else None,
                 capture=Menu.CAPTURE + 1, step=Menu.INDEX)
    STATES.append(state)


def callback(pack, wid, cid):
    Menu.press(pack, wid, cid)
    REQUESTS.append(dict(sequence=GemRB.GetVar('Phase1NativeCallbacks') + 1,
                         action=Menu.PLAN[Menu.INDEX][0], step=Menu.INDEX,
                         pack=pack, window=wid, control=cid, nonce=NONCE))


def select(action):
    module = editor()
    if not module.Editor or action not in module.Names:
        raise RuntimeError('Required editable action absent')
    index = module.Names.index(action)
    page = index // module.ROWS
    if page != module.Page:
        callback('WIN_KEYS', 0, 6006 if page > module.Page else 6005)
        Menu.PLAN.insert(Menu.INDEX + 1, ('select-page-' + action, lambda: select(action), False))
    else:
        callback('WIN_KEYS', 0, 5000 + index % module.ROWS)


def text(action, key):
    module = editor()
    if module.Names[module.Selected] != action:
        raise RuntimeError('Actual selected editor action differs from requested row')
    Menu.control('WIN_KEYS', 0, 6000).SetText(key)


def key_request(key):
    if len(key) != 1 or key not in 'abcdefghijklmnopqrstuvwxyz':
        raise RuntimeError('Journey supports existing plain letter menu keys only')
    if any(Menu.view(pack, wid) for pack, wid in (('GUIOPT', 2), ('GUIOPT', 8), ('WIN_KEYS', 0))):
        raise RuntimeError('Menu key dispatch requested with an options/editor modal open')
    number = GemRB.GetVar('Phase1NativeKeys') + 1
    GemRB.SetVar('Phase1DispatchKey', ord(key))
    KEYS.append(dict(sequence=number, key=key, nonce=NONCE, step=Menu.INDEX,
                     bindings_before=bindings(), profile_before=profile()))


def observe_key(name, pack):
    request = KEYS[-1]
    request.update(observation=name, capture=Menu.CAPTURE + 1, observed_step=Menu.INDEX,
                   expected_pack=pack, expected_window=2, bindings_after=bindings(), profile_after=profile())
    Menu.expect_window(name, pack, 2)
    # An inventory-to-record mismatch must not pass because some window opened.
    for other in ('GUIINV', 'GUIREC', 'GUIJRNL'):
        if other != pack:
            Menu.record(name + '.exclusive-' + other, not bool(Menu.view(other, 2)))


def initialize():
    global BASE, DEFAULTS, SWAPPED
    rows = GemRB.GetKeyBindings()
    live = bindings()
    DEFAULTS = {r['name']: r['default'] for r in rows}
    BASE = dict(INPUT['baseline']) if MODE == 'hotkeys-reload' else live
    for action in ('inventory', 'character_record', 'journal'):
        if action not in BASE or len(BASE[action]) != 1 or not BASE[action].islower():
            raise RuntimeError('Required existing plain menu route unavailable')
    if len({BASE[a] for a in ('inventory', 'character_record', 'journal')}) != 3:
        raise RuntimeError('Required menu routes overlap')
    SWAPPED = dict(BASE, inventory=BASE['character_record'], character_record=BASE['inventory'])
    if MODE == 'hotkeys-edit':
        if profile()['exists'] or BASE != DEFAULTS:
            raise RuntimeError('Edit profile must start fresh at game defaults')
        build_edit()
    else:
        if live != INPUT['expected_bindings'] or SWAPPED != INPUT['expected_bindings']:
            raise RuntimeError('Fresh process did not load the pinned persisted bindings')
        build_reload()
    checkpoint('initial')


def add(name, action, capture=False):
    Menu.PLAN.append((name, action, capture))


def observe(name):
    add(name, lambda: checkpoint(name), True)


def open_editor(prefix):
    add(prefix + '.options', lambda: Menu.call('GUIOPT', 'OpenOptionsWindow'))
    add(prefix + '.gameplay', lambda: callback('GUIOPT', 2, 9))
    add(prefix + '.open-editor', lambda: callback('GUIOPT', 8, 51))
    observe(prefix + '.editor-open')


def leave_options(prefix):
    add(prefix + '.close-gameplay', lambda: callback('GUIOPT', 8, 7))
    add(prefix + '.close-options', lambda: callback('GUIOPT', 2, 11))


def route(prefix, key, pack):
    add(prefix + '.dispatch', lambda: key_request(key))
    add(prefix + '.observed', lambda: observe_key(prefix, pack), True)
    add(prefix + '.close', lambda: Menu.call('GUICommonWindows', 'CloseTopWindow'))


def routes(prefix, mapping):
    for action, pack in (('inventory', 'GUIINV'), ('character_record', 'GUIREC'), ('journal', 'GUIJRNL')):
        route(prefix + '.' + action, mapping[action], pack)


def stage_swap(prefix):
    add(prefix + '.select-inventory', lambda: select('inventory'))
    add(prefix + '.input-record-key', lambda: text('inventory', BASE['character_record']))
    add(prefix + '.replace', lambda: callback('WIN_KEYS', 0, 6003))
    add(prefix + '.select-record', lambda: select('character_record'))
    add(prefix + '.input-inventory-key', lambda: text('character_record', BASE['inventory']))
    add(prefix + '.assign', lambda: callback('WIN_KEYS', 0, 6001))


def build_edit():
    open_editor('cancel')
    add('conflict.select-inventory', lambda: select('inventory'))
    add('conflict.input', lambda: text('inventory', BASE['character_record']))
    add('conflict.assign', lambda: callback('WIN_KEYS', 0, 6001))
    observe('conflict-rejected')
    add('conflict.replace', lambda: callback('WIN_KEYS', 0, 6003))
    observe('replace-staged')
    add('cancel.callback', lambda: callback('WIN_KEYS', 0, 14))
    observe('cancelled')
    leave_options('cancel')
    routes('original', BASE)
    open_editor('clear')
    add('clear.select', lambda: select('inventory'))
    add('clear.callback', lambda: callback('WIN_KEYS', 0, 6002))
    observe('clear-staged')
    add('clear.cancel', lambda: callback('WIN_KEYS', 0, 14))
    observe('clear-cancelled')
    leave_options('clear')
    open_editor('apply')
    stage_swap('apply')
    observe('swap-staged')
    add('apply.callback', lambda: callback('WIN_KEYS', 0, 11))
    observe('applied')
    leave_options('apply')
    routes('swapped', SWAPPED)
    open_editor('defaults-cancel')
    add('defaults-cancel.callback', lambda: callback('WIN_KEYS', 0, 6004))
    observe('defaults-staged')
    add('defaults-cancel.cancel', lambda: callback('WIN_KEYS', 0, 14))
    observe('defaults-cancelled')
    leave_options('defaults-cancel')
    open_editor('defaults-apply')
    add('defaults-apply.defaults', lambda: callback('WIN_KEYS', 0, 6004))
    add('defaults-apply.apply', lambda: callback('WIN_KEYS', 0, 11))
    observe('defaults-applied')
    leave_options('defaults-apply')
    routes('restored', BASE)
    open_editor('final')
    stage_swap('final')
    add('final.apply', lambda: callback('WIN_KEYS', 0, 11))
    observe('final-applied')
    leave_options('final')
    routes('final', SWAPPED)
    mouse_check()
    observe('final')


def mouse_check():
    add('inventory.mouse-callback', lambda: callback('OPTWIN', 0, 3))
    add('inventory.mouse-observed', lambda: (checkpoint('mouse-inventory'), Menu.expect_window('inventory.mouse', 'GUIINV', 2)), True)
    add('inventory.mouse-close', lambda: Menu.call('GUICommonWindows', 'CloseTopWindow'))


def build_reload():
    routes('reloaded', SWAPPED)
    mouse_check()
    open_editor('reload')
    observe('reload-editor')
    add('reload.cancel', lambda: callback('WIN_KEYS', 0, 14))
    leave_options('reload')
    observe('final')


def Configure(output, mode, nonce):
    global INPUT, MODE, NONCE, STATES, REQUESTS, KEYS, PROCESS_IDENTITY
    Menu.Configure(output, nonce)
    Menu.PLAN = [('initial', initialize, True)]
    INPUT = json.loads((Path(output) / 'journey-input.json').read_text(encoding='utf-8'))
    if mode not in ('hotkeys-edit', 'hotkeys-reload') or INPUT['nonce'] != nonce or INPUT['mode'] != mode:
        raise RuntimeError('Wrong/stale hotkey journey identity')
    if Path(INPUT['profile']).resolve() != Path(GemRB.GetSystemVariable(SV_SAVEPATH)).resolve():
        raise RuntimeError('Runtime profile differs from private launch pin')
    MODE, NONCE, STATES, REQUESTS, KEYS = mode, nonce, [], [], []
    PROCESS_IDENTITY = dict(pid=os.getpid(), startup_nonce=uuid.uuid4().hex)


def Step():
    GemRB.SetVar('Phase1DispatchKey', 0)
    Menu.Step()
    (Menu.OUTPUT / 'hotkey-runtime.json').write_text(json.dumps(dict(
        schema='bg-redux-hotkey-runtime/1', mode=MODE, nonce=NONCE,
        process=PROCESS_IDENTITY, baseline=BASE, defaults=DEFAULTS, expected_swapped=SWAPPED,
        states=STATES, callbacks=REQUESTS, keys=KEYS, steps=Menu.INDEX,
        planned_steps=len(Menu.PLAN), completed=bool(GemRB.GetVar('Phase1MenuComplete')),
        physical_typing_observed=False, pointer_hit_testing=False,
        modifier_international_function_routes_tested=False), indent=2), encoding='utf-8')
