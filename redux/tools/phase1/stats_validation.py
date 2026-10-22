"""Fail-closed raw review for four actors' ordinary record/Stats callbacks.

Numeric save/resistance rows use captured native stats and actual TLK labels.
Other section text is checked against the declared assembly/page contract;
that is not an independent oracle for class mechanics or information completeness.
"""
import copy
import hashlib
import json
from pathlib import Path
import struct

NUMERIC_ROWS = {
    2: ((17380, 9), (17381, 10), (17382, 11), (17383, 12), (17384, 13)),
    3: ((32213, 14), (32222, 19), (32214, 15), (32223, 20),
        (32220, 16), (32221, 17), (62146, 18), (32233, 73),
        (11767, 24), (11768, 21), (11769, 23), (11770, 22), (14017, 74)),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def without_selection(value):
    value = copy.deepcopy(value)
    value.pop('selection', None)
    return value


def validate_stage(directory, resolution, *, expected_nonce, tlk_path):
    directory, tlk_path = Path(directory), Path(tlk_path)
    read = lambda name: json.loads((directory / name).read_text(encoding='utf8'))
    host, runtime = read('menu-host-result.json'), read('menu-runtime.json')
    log = (directory / 'process.log').read_text(encoding='utf8', errors='replace')
    require(not any(line.startswith(('[Python/ERROR]: Traceback (most recent call last):',
                                     '[GUIScript/ERROR]: Runtime Error:')) for line in log.splitlines()),
            'Stats native Python callback error')
    require(isinstance(expected_nonce, str) and len(expected_nonce) == 32
            and all(c in '0123456789abcdef' for c in expected_nonce)
            and host.get('nonce') == runtime.get('nonce') == expected_nonce,
            'Stats requires caller-pinned matching nonce')
    require(host.get('journey') == 'stats' and host.get('completed') is True
            and runtime.get('steps', 0) > 0 and runtime['steps'] == runtime.get('planned_steps'),
            'Stats journey incomplete or wrong host mode')
    checks = runtime['checks']
    verdicts = [row for row in checks if isinstance(row.get('passed'), bool)]
    require(verdicts and all(row['passed'] for row in verdicts), 'Stats runtime assertion failed')
    actions = [row for row in checks if 'action' in row]
    require(len(actions) == runtime['steps'] and [r['step'] for r in actions] == list(range(runtime['steps'])),
            'Stats action sequence incomplete')
    require(len({r['action'] for r in actions}) == len(actions), 'Stats action identity ambiguous')
    captures = [row['capture'] for row in actions if row.get('capture')]
    require(captures == list(range(1, host['captures'] + 1)), 'Stats capture inventory incomplete')
    callback_paths = sorted(directory.glob('callback-*.json'))
    callback_paths = [p for p in callback_paths if not p.name.endswith(('-before.state.json', '-after.state.json',
                         '-before.observer.json', '-after.observer.json'))]
    callbacks = [read(p.name) for p in callback_paths]
    require(len(callbacks) == host['callbacks'], 'Stats callback inventory incomplete')
    expected_callbacks = []
    contracts = [r for r in checks if r.get('name') == 'stats.actor-section-contract']
    require([(r['actor'], r['section']) for r in contracts] == [(a, s) for a in range(1, 5) for s in range(6)],
            'Stats actor/section coverage missing or duplicated')
    selected = [r for r in checks if r.get('name') == 'stats.actor-selected']
    require([r['actor'] for r in selected] == [1, 2, 3, 4], 'Stats actor selection coverage missing')
    tlk = tlk_path.read_bytes()
    require(tlk[:8] == b'TLK V1  ', 'Invalid Stats TLK')
    count, offset = struct.unpack_from('<II', tlk, 10)
    def string(ref):
        require(0 <= ref < count, 'Stats TLK reference outside table')
        start, length = struct.unpack_from('<II', tlk, 18 + 26*ref + 18)
        require(offset + start + length <= len(tlk), 'Stats TLK string outside file')
        return tlk[offset+start:offset+start+length].decode('utf8')
    cached = {}
    def capture(index):
        if index not in cached:
            bmp = (directory / ('capture-%d.bmp' % index)).read_bytes()
            require(len(bmp) >= 54 and bmp[:2] == b'BM', 'Stats capture missing BMP')
            size, start = struct.unpack_from('<I', bmp, 2)[0], struct.unpack_from('<I', bmp, 10)[0]
            w, h = struct.unpack_from('<ii', bmp, 18)
            require(size == len(bmp) and 54 <= start < size and [w, abs(h)] == list(resolution),
                    'Stats BMP size/resolution invalid')
            cached[index] = (read('capture-%d.ui.json' % index), read('capture-%d.state.json' % index),
                             read('capture-%d.observer.json' % index))
        return cached[index]
    def field(ui, cid):
        found = [c for c in ui['controls'] if c.get('pack') == 'GUIREC'
                 and c.get('window') == 2 and c.get('id') == cid]
        require(len(found) == 1 and found[0].get('visible'), 'Stats visible field missing/ambiguous')
        return found[0]['text']
    def action(name):
        found = [r for r in actions if r['action'] == name]
        require(len(found) == 1, 'Stats required action missing')
        return found[0]
    def callback(name, pack, wid, cid):
        step = action(name)['step'] + 1
        found = [r for r in callbacks if r.get('runtime_step') == step]
        require(len(found) == 1 and found[0].get('nonce') == expected_nonce
                and found[0].get('performed') is True and found[0].get('pack') == pack
                and found[0].get('window') == wid and found[0].get('control') == cid,
                'Stats registered callback missing/stale/wrong target')
        expected_callbacks.append(found[0]['sequence'])
    actor_details = []
    for record in selected:
        pc = record['actor']
        prefix = 'stats.actor-%d' % pc
        callback(prefix + '.portrait', 'PORTWIN', 0, pc - 1)
        ui, state, observer = capture(action(prefix + '.selected')['capture'])
        require(len(state['party']) == 4 and state['selection'] == pc, 'Stats captured actor mismatch')
        actor = state['party'][pc-1]
        native = [a for a in observer['actors'] if a['party_index'] == pc]
        require(len(native) == 1 and record['actor_name'] == actor['name'] == field(ui, 0x1000000e)
                and record['actor_class'] == actor['modified_stats'][232]
                and record['levels'] == [actor['modified_stats'][s] for s in (34, 68, 69)]
                and field(ui, 0x10000029) == str(actor['modified_stats'][0])
                and field(ui, 0x10000040).split('/')[0] == str(native[0]['cached_thac0']),
                'Stats actor identity/class/level/headline mismatch')
        require(field(ui, 0x7fff0201).startswith('1 / '), 'Stats actor change did not reset page')
        actor_details.append(dict(actor=pc, name=actor['name'], actor_class=record['actor_class'],
                                  levels=record['levels'], states=record['states']))
    page_count = 0
    for contract in contracts:
        pc, section, pages = contract['actor'], contract['section'], contract['pages']
        require(isinstance(pages, list) and pages and all(isinstance(p, str) and p for p in pages),
                'Stats page contract empty')
        prefix = 'stats.actor-%d.section-%d' % (pc, section)
        callback(prefix + '.select', 'GUIREC', 2, 0x7fff0210 + section)
        sequence = [0] + list(range(1, len(pages))) + list(range(len(pages)-2, -1, -1))
        observations = [r for r in actions if r['action'].startswith(prefix + '.') and r['action'].endswith('.observed')]
        page_rows = [r for r in checks if r.get('name') == 'stats.actor-page' and r['actor'] == pc and r['section'] == section]
        require([r['page'] for r in page_rows] == sequence and len(observations) == len(sequence),
                'Stats page traversal incomplete')
        for index, (row, observation, page) in enumerate(zip(page_rows, observations, sequence)):
            if index:
                cid = 0x7fff0203 if index < len(pages) else 0x7fff0202
                callback(observation['action'].replace('.observed', '.press'), 'GUIREC', 2, cid)
            ui, state, _ = capture(observation['capture'])
            require(state['selection'] == pc and field(ui, 45) == row['content'] == pages[page]
                    and row['pages'] == len(pages)
                    and field(ui, 0x7fff0201) == '%d / %d' % (page+1, len(pages)),
                    'Stats captured page text/actor/index mismatch')
            if section in NUMERIC_ROWS:
                actor = state['party'][pc-1]
                expected = [string(17379 if section == 2 else 32204)]
                for ref, stat in NUMERIC_ROWS[section]:
                    value, base = actor['modified_stats'][stat], actor['base_stats'][stat]
                    suffix = '%' if section == 3 else (' (%d)' % (value-base) if value != base else '')
                    expected.append(string(ref) + ': ' + str(value) + suffix)
                require([line for line in '\n'.join(pages).splitlines() if line.strip()] == expected,
                        'Stats numeric save/resistance rows disagree with native state/TLK')
            page_count += 1
    require(sorted(expected_callbacks) == list(range(1, len(callbacks)+1)), 'Stats unexpected/repeated callback')
    for row in callbacks:
        sequence = row['sequence']
        require(without_selection(read('callback-%d-before.state.json' % sequence))
                == without_selection(read('callback-%d-after.state.json' % sequence)),
                'Stats callback changed collected world')
    require(action('stats.record.closed').get('capture'), 'Stats record close observation missing')
    for index in captures:
        capture(index)
    require(not any('GUIREC' == c.get('pack') and c.get('window') == 2 and c.get('visible')
                    for c in capture(action('stats.record.closed')['capture'])[0]['controls']),
            'Stats record remained visible after close')
    require(without_selection(read('before.state.json')) == without_selection(read('after.state.json')),
            'Stats journey changed collected world')
    return dict(assertion_passed=True, collected_world_unchanged=True, captures=len(captures),
                actor_sections=len(contracts), page_visits=page_count, actors=actor_details,
                numeric_saves_and_resistances_validated=True, visual_acceptance=False,
                independent_class_mechanics_oracle=False, pointer_hit_testing=False, hidden_rng_unchanged=None,
                tlk_sha256=hashlib.sha256(tlk).hexdigest())
