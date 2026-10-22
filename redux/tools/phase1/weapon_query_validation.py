"""Read-only validation for Phase 1 six-hand native query captures.

No stub-specific expected values or log rules. Original references must bind
the exact prepared fixture and independently readable frozen output.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from weapon_oracle_fixtures import QUERY_KEYS, inspect_output, safe_relative


QUERIES = tuple(f'{name}(Player2,{hand})' for hand in ('MAINHAND', 'OFFHAND', 'BOTH')
                for name in ('WeaponEffectiveVs', 'WeaponCanDamage'))
LIMIT = ('Collected same-process state and selected weapon caches after library initialization only; '
         'optional calling-thread RNG state is reported separately. No loop/ticks/save. '
         'Other threads, other hidden state/caches and future scheduling are not proven unchanged.')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def manifest(folder):
    folder = Path(folder)
    return {p.relative_to(folder).as_posix(): dict(bytes=p.stat().st_size, sha256=sha(p))
            for p in sorted(folder.rglob('*')) if p.is_file()}


def member(folder, relative):
    path = (Path(folder)/safe_relative(relative)).resolve()
    if not path.is_relative_to(Path(folder).resolve()):
        raise ValueError('Evidence path escapes capture')
    return path


def diff(before, after, path=''):
    if type(before) is not type(after):
        return [dict(path=path, before=before, after=after)]
    if isinstance(before, dict):
        rows = []
        for key in sorted(before.keys() | after.keys()):
            pointer = path+'/'+key.replace('~', '~0').replace('/', '~1')
            if key not in before or key not in after:
                rows.append(dict(path=pointer, before=before.get(key), after=after.get(key),
                                 missing='before' if key not in before else 'after'))
            else:
                rows.extend(diff(before[key], after[key], pointer))
        return rows
    if isinstance(before, list):
        rows = []
        if len(before) != len(after):
            rows.append(dict(path=path+'/length', before=len(before), after=len(after)))
        for index, (a, b) in enumerate(zip(before, after)):
            rows.extend(diff(a, b, path+'/'+str(index)))
        return rows
    return [] if before == after else [dict(path=path, before=before, after=after)]


def require_state(state):
    if state.get('schema') != 'bg-redux-state/1':
        raise ValueError('Required state snapshot schema missing')
    for key in ('game_time', 'current_area', 'selection', 'globals', 'area_locals', 'party',
                'stored_npcs', 'current_area_actors', 'journal'):
        if key not in state:
            raise ValueError('State surface incomplete: '+key)
    for group in ('party', 'stored_npcs', 'current_area_actors'):
        for actor in state[group]:
            if len(actor.get('base_stats', [])) != 256 or len(actor.get('modified_stats', [])) != 256:
                raise ValueError('Actor stat surface incomplete')
            for key in ('inventory', 'effects', 'spellbook', 'locals', 'runtime_id', 'position', 'area', 'script_name'):
                if key not in actor:
                    raise ValueError('Actor state surface incomplete: '+key)


def runtime_guard(row, metadata, state, cache):
    require_state(state)
    if state['current_area'].upper() != 'AR0602' or len(state['party']) != 2 or state['selection'] != 1:
        raise ValueError('Required selected protagonist/two actors in AR0602 missing')
    sender, target = state['party']
    if (target['script_name'].lower() != 'imoen' or sender['runtime_id'] == target['runtime_id']
            or any(actor['area'].upper() != 'AR0602' for actor in (sender, target))):
        raise ValueError('Actual sender/Player2 target identity differs')
    if (cache.get('schema') != 'bg-redux-phase1-weapon-cache/1'
            or cache.get('sender_runtime_id') != sender['runtime_id']
            or cache.get('equipped_slot') != (11 if row['spec']['ammo'] else 35)
            or cache.get('shield_slot') != 9 or len(cache.get('hands', [])) != 2):
        raise ValueError('Weapon cache identity/slot surface differs')
    spec = row['spec']; inv = sender['inventory']
    if inv['equipped'] != (-24 if spec['ammo'] else 0) or inv['equipped_header'] != 0:
        raise ValueError('Selected weapon/ammunition or ability differs')
    items = {item['slot']: item for item in inv['items']}
    if len(items) != len(inv['items']):
        raise ValueError('Duplicate actual inventory slots')
    expected_items = {35: spec['main']}
    if spec['off']:
        expected_items[9] = spec['off']
    if spec['ammo']:
        expected_items[11] = spec['ammo']
        if items.get(11, {}).get('usages', [None])[0] != 40:
            raise ValueError('Actual ammunition/charges missing')
    actual_items = {slot: item['resref'].lower() for slot, item in items.items() if slot != inv['fist_slot']}
    if actual_items != expected_items:
        raise ValueError('Actual physical weapon/off-hand/ammunition differs')
    flag_mask = (0x2 | 0x10 | 0x40 | 0x100 | 0x200) << 8
    for index, hand in enumerate(cache['hands']):
        if hand.get('hand') != index+1:
            raise ValueError('Cache hand order/identity differs')
        ref = (spec['ammo'] or spec['main']) if index == 0 else spec['off']
        has_weapon = ref is not None and not ref.startswith('shld')
        if not has_weapon:
            if hand.get('item') is not None or hand.get('header') is not None or hand.get('header_index') != -1:
                raise ValueError('Empty/shield off-hand must not borrow main-hand cache')
            continue
        item_meta = metadata[ref]
        slot = (11 if spec['ammo'] else 35) if index == 0 else 9
        ability = next((a for a in item_meta['abilities'] if a['index'] == 0), None)
        header = hand.get('header')
        enchantment = max(metadata[spec['main']]['enchantment'], item_meta['enchantment']) if spec['ammo'] else item_meta['enchantment']
        if (hand.get('item', '').lower() != ref or hand.get('slot') != slot
                or hand.get('header_index') != 0 or not header or ability is None
                or header.get('location') != 1 or header.get('attack_type') != ability['attack_type']
                or header.get('damage_type') != ability['damage_type']
                or hand.get('item_flags') != item_meta['flags']
                or hand.get('base_enchantment') != item_meta['enchantment']
                or hand.get('enchantment') != enchantment
                or hand.get('itemflags') != items[slot]['flags']
                or (hand['itemflags'] & flag_mask) != ((item_meta['flags'] << 8) & flag_mask)):
            raise ValueError('Actual cached selected weapon/header/flags/enchantment differs')
        if hand.get('wflags', 0) & 3 != (2 if spec['ammo'] else 1):
            raise ValueError('Actual cached melee/ranged mode differs')
        if bool(hand['wflags'] & 16) != bool(index):
            raise ValueError('Actual cached off-hand flag differs')
    defenses = [fx for fx in target['effects'] if fx.get('source_ref', '').upper() == 'RDXDEF']
    defense = spec['defense']
    if defense is None:
        if defenses:
            raise ValueError('Unexpected diagnostic defense')
    else:
        opcode, p1, p2 = defense
        permitted_p1 = (p1, 0xffffffff) if opcode == 120 and p2 == 1 else (p1,)
        if (len(defenses) != 1 or defenses[0]['opcode'] != opcode
                or defenses[0]['parameters'][0] not in permitted_p1 or defenses[0]['parameters'][1] != p2
                or defenses[0]['timing'] != 9):
            raise ValueError('Actual exact diagnostic defense differs')
        stat = {86: 21, 87: 22, 88: 23, 89: 24}.get(opcode)
        if stat is not None and target['modified_stats'][stat] != p1:
            raise ValueError('Actual derived resistance missing')
    return dict(sender_runtime_id=sender['runtime_id'], target_runtime_id=target['runtime_id'],
                inventory=actual_items, cache=cache, defense_effects=defenses)


def require_rng_snapshot(value):
    if (not isinstance(value, dict) or set(value) != {'observed', 'scope', 'initialized', 'state'}
            or type(value['observed']) is not bool or value['scope'] != 'calling-thread'):
        raise ValueError('Malformed calling-thread RNG evidence')
    if not value['observed']:
        if value['initialized'] is not None or value['state'] is not None:
            raise ValueError('Unavailable RNG evidence claims state')
    elif type(value['initialized']) is not bool:
        raise ValueError('RNG initialized flag must be strict Boolean')
    elif value['initialized']:
        state = value['state']
        if (not isinstance(state, str) or not 1 <= len(state) <= 50000
                or any(not token.isascii() or not token.isdecimal() for token in state.split())
                or len(state.split()) < 2):
            raise ValueError('Malformed private RNG serialization')
    elif value['state'] is not None:
        raise ValueError('Absent RNG evidence contains state')
    return value


def validate_capture(folder, row, metadata, repeats, expected=None, require_rng_observed=False):
    folder = Path(folder)
    if type(repeats) is not int or not 1 <= repeats <= 32:
        raise ValueError('Repeats must be in [1,32]')
    if expected is not None and (set(expected) != set(QUERY_KEYS)
            or any(type(value) is not int or value not in (0, 1) for value in expected.values())):
        raise ValueError('Expected reference must contain six strict Boolean values')
    data = read(folder/'query-result.json')
    controlled_draw = data.get('rng_control_draw_call')
    if controlled_draw is not None and (type(controlled_draw) is not int or controlled_draw != 3):
        raise ValueError('Invalid controlled RNG draw identity')
    if (data.get('schema') != 'bg-redux-phase1-weapon-query-native/1' or data.get('completed') is not True
            or data.get('case_id') != row['spec']['id'] or data.get('repeats') != repeats or data.get('error')):
        raise ValueError('Native completion/case/repeat identity failed')
    initialized = read(folder/'initialized.state.json'); initialized_cache = read(folder/'initialized.weapons.json')
    guard = runtime_guard(row, metadata, initialized, initialized_cache)
    if data.get('sender_runtime_id') != guard['sender_runtime_id'] or data.get('target_runtime_id') != guard['target_runtime_id']:
        raise ValueError('Native sender/target differs from initialized state')
    parsed = data.get('parsed_queries', [])
    if len(parsed) != 6:
        raise ValueError('Six-query parser evidence missing')
    for index, parsed_row in enumerate(parsed):
        if (parsed_row.get('expression') != QUERIES[index] or parsed_row.get('trigger_id') != (0xf2 if index % 2 else 0xec)
                or parsed_row.get('hand') != index//2+1 or parsed_row.get('target_count') != 1
                or parsed_row.get('target_runtime_id') != guard['target_runtime_id']):
            raise ValueError('Fixed parsed query/hand/Player2 target differs')
    order = [('True()', 0), ('False()', 0)]+[(q, r) for r in range(1, repeats+1) for q in QUERIES]
    observations = data.get('observations', [])
    if len(observations) != len(order):
        raise ValueError('Repeated query coverage incomplete')
    previous, previous_cache = initialized, initialized_cache
    has_rng = (folder/'initialized.rng.json').exists()
    previous_rng = require_rng_snapshot(read(folder/'initialized.rng.json')) if has_rng else None
    rng_observed = bool(has_rng and previous_rng['observed'])
    if require_rng_observed and not rng_observed:
        raise ValueError('Calling-thread RNG observation required but unavailable')
    rng_mutations = []
    mutation_rows, values = [], {key: [] for key in QUERY_KEYS}
    expected_names = {'query-result.json', 'initialized.state.json', 'initialized.weapons.json', 'final.state.json', 'final.weapons.json'}
    if has_rng:
        expected_names.update({'initialized.rng.json', 'final.rng.json'})
    for call, (obs, (expression, repetition)) in enumerate(zip(observations, order), 1):
        if (obs.get('call') != call or obs.get('expression') != expression or obs.get('repetition') != repetition
                or type(obs.get('value')) is not int or obs['value'] not in (0, 1)):
            raise ValueError('Observation order/Boolean mismatch')
        files = {key: f'call-{call}-{side}.{surface}.json' for key, side, surface in
                 [('before', 'before', 'state'), ('after', 'after', 'state'),
                  ('weapons_before', 'before', 'weapons'), ('weapons_after', 'after', 'weapons')]}
        for key, filename in files.items():
            if obs.get(key) != filename:
                raise ValueError('Per-call evidence filename mismatch/reuse')
            expected_names.add(filename)
        before, after = (read(member(folder, files[key])) for key in ('before', 'after'))
        cache_before, cache_after = (read(member(folder, files[key])) for key in ('weapons_before', 'weapons_after'))
        require_state(before); require_state(after)
        if before != previous or cache_before != previous_cache:
            raise ValueError('State/cache continuity broken between calls')
        changes, cache_changes = diff(before, after), diff(cache_before, cache_after)
        if obs.get('native_equal') is not (not changes) or obs.get('weapons_equal') is not (not cache_changes):
            raise ValueError('Native equality contradicts independent state/cache diff')
        if has_rng:
            rng = {}
            for side in ('before', 'after'):
                filename = f'call-{call}-{side}.rng.json'
                if obs.get('rng_'+side) != filename:
                    raise ValueError('RNG evidence filename missing/reused')
                expected_names.add(filename)
                rng[side] = require_rng_snapshot(read(member(folder, filename)))
                if rng[side]['observed'] != rng_observed:
                    raise ValueError('RNG observation availability changed')
            if rng['before'] != previous_rng:
                raise ValueError('RNG continuity broken between calls')
            equal = rng['before'] == rng['after']
            if obs.get('rng_equal') is not (equal if rng_observed else None):
                raise ValueError('Native RNG equality contradicts independent diff')
            if rng_observed and not equal:
                rng_mutations.append(dict(call=call, expression=expression,
                    initialization_changed=rng['before']['initialized'] != rng['after']['initialized'],
                    state_changed=rng['before']['state'] != rng['after']['state']))
            previous_rng = rng['after']
        elif any(key in obs for key in ('rng_before', 'rng_after', 'rng_equal')):
            raise ValueError('RNG call evidence without initialization boundary')
        if changes or cache_changes:
            mutation_rows.append(dict(call=call, expression=expression, changes=changes, weapon_changes=cache_changes))
        if expression == 'True()' and obs['value'] != 1 or expression == 'False()' and obs['value'] != 0:
            raise ValueError('Positive/negative evaluator control failed')
        if expression in QUERIES:
            values[QUERY_KEYS[QUERIES.index(expression)]].append(obs['value'])
        previous, previous_cache = after, cache_after
    final, final_cache = read(folder/'final.state.json'), read(folder/'final.weapons.json')
    require_state(final)
    if final != previous or final_cache != previous_cache:
        raise ValueError('Final state/cache differs from last captured call')
    if has_rng and require_rng_snapshot(read(folder/'final.rng.json')) != previous_rng:
        raise ValueError('Final RNG evidence differs from last captured call')
    if set(manifest(folder)) != expected_names:
        raise ValueError('Unexpected/missing capture file inventory')
    stable = all(len(set(rows)) == 1 for rows in values.values())
    differences = [] if expected is None else [dict(key=key, expected=expected[key], actual=rows)
                                               for key, rows in values.items() if any(v != expected[key] for v in rows)]
    return dict(runtime_preflight=guard, observations=len(order), repeated_queries=6*repeats,
                predicate_values=values, stable_values=stable, original_reference_provided=expected is not None,
                original_differences=differences, original_match=None if expected is None else not differences,
                mutation_observations=mutation_rows, collected_state_unchanged=not mutation_rows,
                final_equals_initialized=final == initialized and final_cache == initialized_cache,
                rng_observed=rng_observed, rng_scope='calling-thread', rng_mutation_observations=rng_mutations,
                rng_unchanged=not rng_mutations if rng_observed else None,
                rng_control_draw_call=controlled_draw,
                hidden_state_unchanged=None, scope=LIMIT)


def bind_original_reference(api, path, preparation_path, preparation, row):
    path, preparation_path = Path(path), Path(preparation_path)
    data = read(path)
    bindings = dict(schema='bg-redux-phase1-original-weapon-case/1', preparation_sha256=sha(preparation_path),
                    case_id=row['spec']['id'], number=row['number'], nonce=row['nonce'],
                    executable_sha256=preparation['executable_sha256'], script_sha256=row['script_sha256'],
                    input_files=row['fixture_files'])
    if any(data.get(key) != value for key, value in bindings.items()):
        raise ValueError('Original reference preparation/case/script/input/executable binding failed')
    if data.get('verdict') != 'original-case-observed':
        raise ValueError('Original reference did not complete observation')
    if not isinstance(data.get('values'), dict) or set(data['values']) != set(QUERY_KEYS):
        raise ValueError('Original reference six Boolean keys missing')
    if any(type(value) is not int or value not in (0, 1) for value in data['values'].values()):
        raise ValueError('Original reference values must be strict Booleans')
    observation = data.get('observation', {})
    required = ('window_id', 'window_app', 'window_title', 'loaded_fixture', 'captured_utc', 'method', 'load_boundary_screenshot_sha256')
    if any(not observation.get(key) for key in required):
        raise ValueError('Original reference observation provenance missing')
    if observation['loaded_fixture'] != row.get('original_fixture'):
        raise ValueError('Original observation loaded fixture differs')
    folder = Path(data['autosave_directory'])
    if manifest(folder) != data['autosave_files'] or not data['autosave_files']:
        raise ValueError('Original reference frozen autosave missing/stale')
    gam = [p for p in folder.iterdir() if p.name.lower() == 'baldur.gam']
    if len(gam) != 1:
        raise ValueError('Original reference output GAM missing/ambiguous')
    parsed = inspect_output(api, gam[0], row)
    if parsed['values'] != data['values']:
        raise ValueError('Original reference values contradict frozen wire output')
    return dict(values=data['values'], receipt_sha256=sha(path), receipt_path=str(path),
                autosave_directory=str(folder), autosave_files=data['autosave_files'],
                output_guard=parsed, observation=observation,
                scope='Hash-bound operator/window provenance and serialized output; not exact original runtime memory.')


def verify_original_artifacts(reference_path, preparation, row):
    """Validate the capture's frozen ancillary files, without rerunning its live gate."""
    reference_path = Path(reference_path)
    folder = reference_path.parent
    receipt = read(reference_path)
    expected = read(folder/'artifact-manifest.json')['files']
    actual = manifest(folder); actual.pop('artifact-manifest.json', None)
    if actual != expected:
        raise ValueError('Original capture artifact inventory missing/stale')
    bindings = [('preparation.json', receipt['preparation_sha256']), ('case.bcs', row['script_sha256']),
                ('load-boundary.jpg', receipt['observation']['load_boundary_screenshot_sha256'])]
    if any(sha(folder/name) != expected_hash for name, expected_hash in bindings):
        raise ValueError('Original frozen preparation/script/load-boundary binding differs')
    observation, boundary, launch = (read(folder/name) for name in ('observation.json', 'load-boundary.json', 'launch.json'))
    if (observation.get('case_id') != row['spec']['id'] or observation.get('number') != row['number']
            or observation.get('nonce') != row['nonce'] or boundary.get('nonce') != row['nonce']
            or observation.get('window') != boundary.get('window')
            or sha(folder/'loaded.jpg') != observation.get('screenshot_sha256')
            or sha(folder/'selected.jpg') != observation.get('selected_screenshot_sha256')
            or launch.get('executable_sha256') != preparation['executable_sha256']):
        raise ValueError('Original frozen window/screenshot/launch observation differs')
    observed_window = observation['window']
    public = receipt['observation']
    if (public['window_id'] != observed_window['id'] or public['window_app'] != observed_window['app']
            or public['window_title'] != observed_window['title']
            or public['loaded_fixture'] != observation['loaded_fixture']
            or public['captured_utc'] != observation['captured_utc']):
        raise ValueError('Original result contradicts frozen observation')
    return dict(files=expected, scope='Frozen capture inventory and identity checks; visual attestations are not OCR or native memory sampling.')
