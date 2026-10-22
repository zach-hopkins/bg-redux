import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import weapon_query_validation as v
import weapon_query_observer as runner
import weapon_oracle_fixtures as fixtures


def write(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


def setup_case():
    row = dict(spec=fixtures.cases()[0], number=1, nonce=123, script='P1AB0001', script_sha256='script',
               fixture_files={'input': {'bytes': 1, 'sha256': 'fixture'}}, original_fixture='private/input')
    metadata = {
        'sw1h01': dict(flags=0, enchantment=0, abilities=[dict(index=0, attack_type=1, damage_type=3)]),
        'sw1h02': dict(flags=64, enchantment=1, abilities=[dict(index=0, attack_type=1, damage_type=3)])}
    inventory = dict(equipped=0, equipped_header=0, fist_slot=10, items=[
        dict(slot=35, resref='SW1H01', flags=97, usages=[0, 0, 0]),
        dict(slot=9, resref='SW1H02', flags=16417, usages=[0, 0, 0])])
    def actor(identity, name):
        return dict(runtime_id=identity, script_name=name, area='AR0602', position=[1, 2],
                    base_stats=[0]*256, modified_stats=[0]*256, inventory=copy.deepcopy(inventory),
                    effects=[], spellbook=[], locals={})
    sender, target = actor(10002, 'lab'), actor(10003, 'imoen')
    target['effects'] = [dict(opcode=120, parameters=[0xffffffff, 1, 0, 0, 0, 0], timing=9, source_ref='RDXDEF')]
    state = dict(schema='bg-redux-state/1', game_time=12, current_area='AR0602', selection=1,
                 globals={}, area_locals={}, party=[sender, target], stored_npcs=[], current_area_actors=[], journal=[])
    hands = []
    for hand, ref, slot, flags, enchantment in [(1, 'sw1h01', 35, 97, 0), (2, 'sw1h02', 9, 16417, 1)]:
        hands.append(dict(hand=hand, slot=slot, item=ref, item_flags=metadata[ref]['flags'],
                          base_enchantment=enchantment, itemflags=flags, enchantment=enchantment,
                          wflags=1 if hand == 1 else 17, header_index=0,
                          header=dict(location=1, attack_type=1, damage_type=3)))
    cache = dict(schema='bg-redux-phase1-weapon-cache/1', sender_runtime_id=10002, equipped_slot=35, shield_slot=9, hands=hands)
    return row, metadata, state, cache


def capture(folder, row, state, cache, values=None, repeats=1):
    values = values or dict(zip(fixtures.QUERY_KEYS, (1, 1, 0, 1, 1, 1)))
    write(folder/'initialized.state.json', state); write(folder/'initialized.weapons.json', cache)
    observations = []
    for call, (expression, repetition) in enumerate([('True()', 0), ('False()', 0)]+[(q, r) for r in range(1, repeats+1) for q in v.QUERIES], 1):
        entry = dict(call=call, expression=expression, repetition=repetition,
                     value=1 if expression == 'True()' else 0 if expression == 'False()' else values[fixtures.QUERY_KEYS[v.QUERIES.index(expression)]],
                     native_equal=True, weapons_equal=True)
        for key, side, surface, value in [('before', 'before', 'state', state), ('after', 'after', 'state', state),
                                           ('weapons_before', 'before', 'weapons', cache), ('weapons_after', 'after', 'weapons', cache)]:
            entry[key] = f'call-{call}-{side}.{surface}.json'
            write(folder/entry[key], value)
        observations.append(entry)
    data = dict(schema='bg-redux-phase1-weapon-query-native/1', completed=True, case_id=row['spec']['id'], repeats=repeats,
                error='', sender_runtime_id=10002, target_runtime_id=10003,
                parsed_queries=[dict(expression=q, trigger_id=0xf2 if i % 2 else 0xec, hand=i//2+1,
                                     target_count=1, target_runtime_id=10003) for i, q in enumerate(v.QUERIES)],
                observations=observations)
    write(folder/'query-result.json', data); write(folder/'final.state.json', state); write(folder/'final.weapons.json', cache)
    return data, values


class QueryEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.row, self.metadata, self.state, self.cache = setup_case()
        self.data, self.expected = capture(self.folder, self.row, self.state, self.cache)

    def validate(self, expected=None):
        return v.validate_capture(self.folder, self.row, self.metadata, 1, expected)

    def test_actual_six_queries_match_and_controls_are_independent(self):
        result = self.validate(self.expected)
        self.assertEqual(result['observations'], 8)
        self.assertEqual(result['repeated_queries'], 6)
        self.assertTrue(result['original_match'])
        self.assertTrue(result['collected_state_unchanged'])
        self.assertIsNone(result['hidden_state_unchanged'])

    def test_no_reference_is_explicitly_not_compared(self):
        self.assertIsNone(self.validate()['original_match'])

    def test_repeated_values_must_be_stable(self):
        data, _ = capture(self.folder, self.row, self.state, self.cache, repeats=2)
        data['observations'][8]['value'] = 0
        write(self.folder/'query-result.json', data)
        result = v.validate_capture(self.folder, self.row, self.metadata, 2)
        self.assertFalse(result['stable_values'])
        self.assertEqual(result['predicate_values']['RDXE1'], [1, 0])

    def test_incomplete_expected_values_are_rejected(self):
        for expected in [{}, self.expected | dict(RDXE1=True), self.expected | dict(RDXD1=2)]:
            with self.assertRaisesRegex(ValueError, 'six strict'): self.validate(expected)

    def test_reference_difference_is_retained_not_pass_override(self):
        expected = self.expected | dict(RDXE2=1)
        result = self.validate(expected)
        self.assertFalse(result['original_match'])
        self.assertEqual(result['original_differences'][0]['key'], 'RDXE2')

    def test_missing_raw_snapshot_and_extra_stale_artifact_rejected(self):
        path = self.folder/'call-3-before.state.json'; value = path.read_bytes(); path.unlink()
        with self.assertRaises(OSError): self.validate()
        path.write_bytes(value)
        write(self.folder/'stale.json', {})
        with self.assertRaisesRegex(ValueError, 'inventory'): self.validate()

    def test_parser_wrong_hand_and_wrong_target_rejected(self):
        for change in [dict(hand=1), dict(target_runtime_id=999)]:
            data = copy.deepcopy(self.data); data['parsed_queries'][2].update(change)
            write(self.folder/'query-result.json', data)
            with self.assertRaisesRegex(ValueError, 'parsed'): self.validate()

    def test_control_false_and_boolean_impostor_rejected(self):
        for index, value in [(0, 0), (1, 1), (2, True), (2, 2)]:
            data = copy.deepcopy(self.data); data['observations'][index]['value'] = value
            write(self.folder/'query-result.json', data)
            with self.assertRaises(ValueError): self.validate()

    def test_missing_call_reused_filename_and_completion_rejected(self):
        for kind in ('missing', 'reuse', 'incomplete'):
            data = copy.deepcopy(self.data)
            if kind == 'missing': data['observations'].pop()
            if kind == 'reuse': data['observations'][2]['before'] = 'call-1-before.state.json'
            if kind == 'incomplete': data['completed'] = False
            write(self.folder/'query-result.json', data)
            with self.assertRaises(ValueError): self.validate()

    def test_discontinuous_collected_state_rejected(self):
        state = copy.deepcopy(self.state); state['game_time'] += 1
        write(self.folder/'call-3-before.state.json', state)
        with self.assertRaisesRegex(ValueError, 'continuity'): self.validate()

    def mutate_tail(self, cache=False):
        value = copy.deepcopy(self.cache if cache else self.state)
        if cache: value['hands'][0]['enchantment'] = 9
        else: value['globals']['MUTATION'] = 1
        surface = 'weapons' if cache else 'state'
        write(self.folder/f'call-3-after.{surface}.json', value)
        for call in range(4, 9):
            write(self.folder/f'call-{call}-before.{surface}.json', value)
            write(self.folder/f'call-{call}-after.{surface}.json', value)
        write(self.folder/f'final.{surface}.json', value)
        self.data['observations'][2]['weapons_equal' if cache else 'native_equal'] = False
        write(self.folder/'query-result.json', self.data)

    def test_observed_state_mutation_is_preserved(self):
        self.mutate_tail()
        result = self.validate()
        self.assertFalse(result['collected_state_unchanged'])
        self.assertEqual(result['mutation_observations'][0]['changes'][0]['path'], '/globals/MUTATION')
        self.assertFalse(result['final_equals_initialized'])

    def test_observed_cached_weapon_mutation_is_preserved(self):
        self.mutate_tail(cache=True)
        result = self.validate()
        self.assertFalse(result['collected_state_unchanged'])
        self.assertTrue(result['mutation_observations'][0]['weapon_changes'])

    def test_false_native_equality_cannot_hide_mutation(self):
        self.mutate_tail()
        self.data['observations'][2]['native_equal'] = True
        write(self.folder/'query-result.json', self.data)
        with self.assertRaisesRegex(ValueError, 'independent'): self.validate()

    def test_incomplete_surface_and_final_mismatch_rejected(self):
        state = copy.deepcopy(self.state); state['party'][0]['modified_stats'].pop()
        write(self.folder/'call-3-after.state.json', state)
        with self.assertRaisesRegex(ValueError, 'stat surface'): self.validate()
        write(self.folder/'call-3-after.state.json', self.state)
        state = copy.deepcopy(self.state); state['game_time'] += 1
        write(self.folder/'final.state.json', state)
        with self.assertRaisesRegex(ValueError, 'Final'): self.validate()

    def test_cached_flag_enchantment_header_and_offhand_preconditions(self):
        for change in [dict(enchantment=0), dict(itemflags=1), dict(header_index=1), dict(slot=35), dict(item='sw1h01')]:
            cache = copy.deepcopy(self.cache); cache['hands'][1].update(change)
            with self.assertRaisesRegex(ValueError, 'cached'):
                v.runtime_guard(self.row, self.metadata, self.state, cache)
        state = copy.deepcopy(self.state); state['party'][0]['inventory']['items'][1]['slot'] = 34
        with self.assertRaisesRegex(ValueError, 'physical'):
            v.runtime_guard(self.row, self.metadata, state, self.cache)

    def test_derived_resistance_and_defense_mode_required(self):
        row = copy.deepcopy(self.row); row['spec']['defense'] = (86, 100, 1)
        state = copy.deepcopy(self.state)
        state['party'][1]['effects'][0].update(opcode=86, parameters=[100, 1, 0, 0, 0, 0])
        with self.assertRaisesRegex(ValueError, 'derived'):
            v.runtime_guard(row, self.metadata, state, self.cache)
        state['party'][1]['modified_stats'][21] = 100
        v.runtime_guard(row, self.metadata, state, self.cache)
        state['party'][1]['effects'][0]['parameters'][1] = 0
        with self.assertRaisesRegex(ValueError, 'defense'):
            v.runtime_guard(row, self.metadata, state, self.cache)

    def test_bow_ammo_cache_uses_actual_ammo_header_and_launcher_enchantment(self):
        row = copy.deepcopy(self.row); row['spec'].update(main='bow02', off=None, ammo='arow01', defense=None)
        state = copy.deepcopy(self.state); state['party'][1]['effects'] = []
        inv = state['party'][0]['inventory']; inv.update(equipped=-24)
        inv['items'] = [dict(slot=35, resref='BOW02', flags=0x4201, usages=[0, 0, 0]),
                        dict(slot=11, resref='AROW01', flags=225, usages=[40, 0, 0])]
        metadata = dict(bow02=dict(flags=66, enchantment=1, abilities=[dict(index=0, attack_type=4, damage_type=4)]),
                        arow01=dict(flags=0, enchantment=0, abilities=[dict(index=0, attack_type=2, damage_type=4)]))
        cache = copy.deepcopy(self.cache); cache['equipped_slot'] = 11
        cache['hands'][0].update(slot=11, item='arow01', item_flags=0, base_enchantment=0, itemflags=225,
                                  enchantment=1, wflags=2, header=dict(location=1, attack_type=2, damage_type=4))
        cache['hands'][1].update(item=None, header=None, header_index=-1)
        v.runtime_guard(row, metadata, state, cache)
        inv['items'][1]['usages'][0] = 39
        with self.assertRaisesRegex(ValueError, 'ammunition/charges'):
            v.runtime_guard(row, metadata, state, cache)
        inv['items'][1]['usages'][0] = 40
        cache['hands'][0]['enchantment'] = 0
        with self.assertRaisesRegex(ValueError, 'cached'):
            v.runtime_guard(row, metadata, state, cache)

    def test_owned_timeout_and_nonzero_exit_never_complete(self):
        for process in [dict(exit_code=0, timed_out=True), dict(exit_code=1, timed_out=False),
                        dict(exit_code=None, timed_out=False), dict(exit_code=0)]:
            with self.assertRaises(ValueError): runner.require_process(process)
        runner.require_process(dict(exit_code=0, timed_out=False))


class OriginalBindingTests(unittest.TestCase):
    def test_exact_frozen_reference_binding_and_negative_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); preparation_path = root/'preparation.json'; write(preparation_path, {'identity': 1})
            row, _, _, _ = setup_case(); preparation = dict(executable_sha256='original-exe')
            autosave = root/'frozen-autosave'; autosave.mkdir(); (autosave/'BALDUR.GAM').write_bytes(b'frozen mock output')
            values = dict.fromkeys(fixtures.QUERY_KEYS, 1)
            receipt = dict(schema='bg-redux-phase1-original-weapon-case/1', verdict='original-case-observed', preparation_sha256=v.sha(preparation_path),
                           case_id=row['spec']['id'], number=1, nonce=123, executable_sha256='original-exe',
                           script_sha256='script', input_files=row['fixture_files'], values=values,
                           autosave_directory=str(autosave), autosave_files=v.manifest(autosave),
                           observation=dict(window_id=1, window_app='private-exe', window_title='private-profile',
                                            loaded_fixture=row['original_fixture'], captured_utc='2026-10-21T23:00:00Z',
                                            method='operator', load_boundary_screenshot_sha256='screenshot'))
            path = root/'receipt.json'; write(path, receipt)
            with patch.object(v, 'inspect_output', return_value=dict(values=values)):
                self.assertEqual(v.bind_original_reference(None, path, preparation_path, preparation, row)['values'], values)
                for mutation in [dict(nonce=124), dict(preparation_sha256='stale'), dict(script_sha256='other'),
                                 dict(input_files={}), dict(values={}), dict(observation={})]:
                    write(path, receipt | mutation)
                    with self.assertRaises(ValueError):
                        v.bind_original_reference(None, path, preparation_path, preparation, row)
                write(path, receipt)
                (autosave/'BALDUR.GAM').write_bytes(b'drift')
                with self.assertRaisesRegex(ValueError, 'autosave'):
                    v.bind_original_reference(None, path, preparation_path, preparation, row)

    def test_reference_wire_values_must_match_receipt(self):
        # Wire parser/output guard itself has separate generator tests. This
        # establishes that validator cannot simply trust receipt Boolean values.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); prep_path = root/'prep.json'; write(prep_path, {})
            folder = root/'save'; folder.mkdir(); (folder/'baldur.gam').write_bytes(b'wire')
            row, _, _, _ = setup_case(); values = dict.fromkeys(fixtures.QUERY_KEYS, 1)
            data = dict(schema='bg-redux-phase1-original-weapon-case/1', verdict='original-case-observed', preparation_sha256=v.sha(prep_path),
                        case_id=row['spec']['id'], number=1, nonce=123, executable_sha256='exe',
                        script_sha256='script', input_files=row['fixture_files'], values=values,
                        autosave_directory=str(folder), autosave_files=v.manifest(folder),
                        observation=dict(window_id=1, window_app='app', window_title='title', loaded_fixture='private/input',
                                         captured_utc='time', method='operator', load_boundary_screenshot_sha256='sha'))
            path = root/'reference.json'; write(path, data)
            with patch.object(v, 'inspect_output', return_value=dict(values=dict.fromkeys(fixtures.QUERY_KEYS, 0))):
                with self.assertRaisesRegex(ValueError, 'contradict'):
                    v.bind_original_reference(None, path, prep_path, dict(executable_sha256='exe'), row)


class BuildReceiptTests(unittest.TestCase):
    def test_failed_preservation_and_binary_drift_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('binary', 'compiler', 'source', 'frozen'):
                (root/name).write_bytes(b'fixed source' if name in ('source', 'frozen') else name.encode())
            inventory = dict(source={}, binaries={})
            receipt = dict(schema='bg-redux-phase1-weapon-query-build/1', verdict='built-not-executed',
                           project=str(root), engine_source_root=str(root), engine_build_root=str(root),
                           candidate_preserved=True, candidate_inventory=inventory,
                           phase0_preservation=dict(source=True, binaries=True, fixture=True),
                           process=dict(exit_code=0, timed_out=False), binary=str(root/'binary'),
                           binary_sha256=v.sha(root/'binary'), compiler=str(root/'compiler'), compiler_sha256=v.sha(root/'compiler'),
                           sources={str(root/'source'): dict(sha256=v.sha(root/'source'), frozen=str(root/'frozen'))})
            path = root/'receipt.json'; write(path, receipt)
            with patch.object(runner, 'candidate_inventory', return_value=inventory), \
                    patch.object(runner, 'required_sources', return_value=[root/'source']):
                runner.check_build(path, root, root, root)
                for change in [dict(phase0_preservation={}), dict(candidate_preserved=False),
                               dict(process=dict(exit_code=0, timed_out=True)), dict(candidate_inventory={'changed': True})]:
                    write(path, receipt | change)
                    with self.assertRaises(ValueError): runner.check_build(path, root, root, root)
                write(path, receipt); (root/'binary').write_bytes(b'drift')
                with self.assertRaisesRegex(ValueError, 'binary/compiler'):
                    runner.check_build(path, root, root, root)


if __name__ == '__main__':
    unittest.main()
