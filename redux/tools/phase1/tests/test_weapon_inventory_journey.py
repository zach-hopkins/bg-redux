import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))
import weapon_inventory_journey as journey
import weapon_query_validation as evidence
import weapon_oracle_fixtures as fixtures
from test_weapon_query_validation import setup_case, capture, write


def make_journey(folder, stale=False):
    row, metadata, initial, cache_template = setup_case()
    row['spec'] = fixtures.cases()[1]
    metadata['shld01'] = dict(flags=0, enchantment=0, abilities=[])
    previous_state = previous_cache = None
    steps = []
    for index, (identity, off_ref) in enumerate(journey.STEPS):
        location = folder/identity; location.mkdir()
        state = copy.deepcopy(initial)
        inventory = state['party'][0]['inventory']
        inventory['items'] = [dict(slot=35, resref='SW1H02', flags=16417, usages=[0, 0, 0])]
        if off_ref:
            inventory['items'].append(dict(slot=9, resref=off_ref, flags=16417 if off_ref == 'sw1h02' else 97, usages=[0, 0, 0]))
        cache = copy.deepcopy(cache_template)
        cache['hands'][0].update(item='sw1h02', item_flags=64, base_enchantment=1, itemflags=16417, enchantment=1)
        if off_ref is None or off_ref == 'shld01':
            cache['hands'][1].update(item=None, header=None, header_index=-1)
        else:
            enchantment = int(off_ref == 'sw1h02')
            cache['hands'][1].update(item=off_ref, item_flags=64 if enchantment else 0,
                                      base_enchantment=enchantment, enchantment=enchantment,
                                      itemflags=16417 if enchantment else 97)
        if stale and identity == '05-create-plus':
            cache['hands'][1].update(item='sw1h01', item_flags=0, base_enchantment=0, enchantment=0, itemflags=97)
        data, _ = capture(location, row, state, cache)
        (location/'query-result.json').unlink()
        write(location/'before-mutation.state.json', previous_state if index else state)
        write(location/'before-mutation.weapons.json', previous_cache if index else cache)
        step = dict(id=identity, expected_off=off_ref, route='actual route recorded by native driver',
                    completed=True, observations=data['observations'])
        write(location/'step.json', step); steps.append(step)
        previous_state, previous_cache = state, cache
    root = dict(schema='bg-redux-phase1-inventory-journey-native/1', completed=True, case_id=row['spec']['id'], repeats=1,
                sender_runtime_id=10002, target_runtime_id=10003, parsed_queries=data['parsed_queries'], steps=steps, error='')
    write(folder/'journey.json', root)
    return row, metadata, root


class InventoryJourneyEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_complete_journey_coherent_with_separate_intentional_mutations(self):
        row, metadata, _ = make_journey(self.folder)
        result = journey.validate_journey(self.folder, row, metadata, 1)
        self.assertEqual(result['cache_mismatch_steps'], [])
        self.assertEqual(result['query_mutation_steps'], [])
        self.assertTrue(result['steps'][1]['intentional_state_changes'])
        self.assertIsNone(result['original_journey_parity'])

    def test_same_animation_stale_cache_is_observed_not_repaired_or_waived(self):
        row, metadata, _ = make_journey(self.folder, stale=True)
        result = journey.validate_journey(self.folder, row, metadata, 1)
        self.assertEqual(result['cache_mismatch_steps'], ['05-create-plus'])
        self.assertEqual(result['steps'][5]['actual_inventory'][9], 'sw1h02')
        self.assertEqual(result['steps'][5]['cached_weapons']['hands'][1]['item'], 'sw1h01')
        self.assertEqual(result['query_mutation_steps'], [])

    def test_missing_step_and_unsafe_incomplete_driver_rejected(self):
        row, metadata, data = make_journey(self.folder)
        original = copy.deepcopy(data)
        data['steps'].pop(); write(self.folder/'journey.json', data)
        with self.assertRaisesRegex(ValueError, 'coverage'): journey.validate_journey(self.folder, row, metadata, 1)
        original.update(completed=False, error='Unknown cache pointer; queries refused')
        write(self.folder/'journey.json', original)
        with self.assertRaisesRegex(ValueError, 'incomplete'): journey.validate_journey(self.folder, row, metadata, 1)

    def test_wrong_physical_result_after_mutation_is_setup_failure(self):
        row, metadata, _ = make_journey(self.folder)
        path = self.folder/'05-create-plus/initialized.state.json'; state = evidence.read(path)
        state['party'][0]['inventory']['items'][1]['resref'] = 'sw1h01'; write(path, state)
        with self.assertRaisesRegex(ValueError, 'Actual mutation'): journey.validate_journey(self.folder, row, metadata, 1)

    def test_interstage_cache_continuity_and_extra_evidence_rejected(self):
        row, metadata, _ = make_journey(self.folder)
        path = self.folder/'05-create-plus/before-mutation.weapons.json'; cache = evidence.read(path)
        changed = copy.deepcopy(cache); changed['hands'][0]['enchantment'] = 99; write(path, changed)
        with self.assertRaisesRegex(ValueError, 'between journey'): journey.validate_journey(self.folder, row, metadata, 1)
        write(path, cache); write(self.folder/'05-create-plus/stale.json', {})
        with self.assertRaisesRegex(ValueError, 'inventory'): journey.validate_journey(self.folder, row, metadata, 1)

    def test_query_mutation_after_intentional_change_is_separate_failure(self):
        row, metadata, data = make_journey(self.folder)
        step = data['steps'][-1]; folder = self.folder/step['id']
        changed = evidence.read(folder/'call-3-after.state.json'); changed['globals']['QUERYMUTATION'] = 1
        write(folder/'call-3-after.state.json', changed)
        for call in range(4, 9):
            write(folder/f'call-{call}-before.state.json', changed); write(folder/f'call-{call}-after.state.json', changed)
        write(folder/'final.state.json', changed)
        step['observations'][2]['native_equal'] = False
        write(folder/'step.json', step); write(self.folder/'journey.json', data)
        result = journey.validate_journey(self.folder, row, metadata, 1)
        self.assertEqual(result['query_mutation_steps'], ['09-create-normal'])
        self.assertEqual(result['cache_mismatch_steps'], [])
        step['observations'][2]['native_equal'] = True
        write(folder/'step.json', step); write(self.folder/'journey.json', data)
        with self.assertRaisesRegex(ValueError, 'independent diff'): journey.validate_journey(self.folder, row, metadata, 1)


if __name__ == '__main__': unittest.main()
