import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))
import weapon_query_validation as v
import weapon_query_observer as runner
from test_weapon_query_validation import setup_case, capture, write


def add_rng(folder, data, observed=True, initialized=True, mutation=None):
    state = dict(observed=observed, scope='calling-thread',
                 initialized=initialized if observed else None,
                 state='123 456 312' if observed and initialized else None)
    write(folder/'initialized.rng.json', state)
    for obs in data['observations']:
        before = copy.deepcopy(state)
        if obs['call'] == 3 and mutation:
            state['initialized'] = True
            state['state'] = '789 456 1'
        for side, value in [('before', before), ('after', state)]:
            obs['rng_'+side] = f'call-{obs["call"]}-{side}.rng.json'
            write(folder/obs['rng_'+side], value)
        obs['rng_equal'] = before == state if observed else None
    write(folder/'final.rng.json', state)
    if mutation:
        data['rng_control_draw_call'] = 3
    write(folder/'query-result.json', data)


class QueryRNGTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.row, self.metadata, state, cache = setup_case()
        self.data, _ = capture(self.folder, self.row, state, cache)

    def validate(self, required=False):
        return v.validate_capture(self.folder, self.row, self.metadata, 1, require_rng_observed=required)

    def test_legacy_capture_remains_explicitly_unobserved(self):
        result = self.validate()
        self.assertFalse(result['rng_observed'])
        self.assertIsNone(result['rng_unchanged'])
        with self.assertRaisesRegex(ValueError, 'required but unavailable'):
            self.validate(True)

    def test_old_api_host_unavailable_does_not_claim_invariance(self):
        add_rng(self.folder, self.data, observed=False)
        self.assertIsNone(self.validate()['rng_unchanged'])
        with self.assertRaisesRegex(ValueError, 'required but unavailable'):
            self.validate(True)

    def test_initialized_and_absent_stable_states_are_observed(self):
        for initialized in (True, False):
            add_rng(self.folder, self.data, initialized=initialized)
            result = self.validate(True)
            self.assertTrue(result['rng_unchanged'])
            self.assertEqual(result['rng_scope'], 'calling-thread')
            self.assertIsNone(result['hidden_state_unchanged'])

    def test_positive_draw_detected_with_collected_state_unchanged(self):
        add_rng(self.folder, self.data, mutation=True)
        result = self.validate(True)
        self.assertFalse(result['rng_unchanged'])
        self.assertTrue(result['collected_state_unchanged'])
        self.assertEqual(result['rng_mutation_observations'], [dict(call=3,
            expression=v.QUERIES[0], initialization_changed=False, state_changed=True)])
        self.assertEqual(runner.observation_verdict(result, None, True), 'calling-thread-rng-mutation')
        with self.assertRaisesRegex(ValueError, 'requested mode'):
            runner.observation_verdict(result, None, False)

    def test_control_cannot_pass_when_draw_evidence_is_missing(self):
        add_rng(self.folder, self.data)
        self.data['rng_control_draw_call'] = 3
        write(self.folder/'query-result.json', self.data)
        result = self.validate(True)
        self.assertEqual(runner.observation_verdict(result, None, True), 'rng-control-not-detected')
        result['rng_control_draw_call'] = None
        with self.assertRaisesRegex(ValueError, 'requested mode'):
            runner.observation_verdict(result, None, True)

    def test_initialization_by_query_is_mutation(self):
        add_rng(self.folder, self.data, initialized=False, mutation=True)
        result = self.validate(True)
        self.assertFalse(result['rng_unchanged'])
        self.assertTrue(result['rng_mutation_observations'][0]['initialization_changed'])

    def test_forged_native_equality_cannot_hide_draw(self):
        add_rng(self.folder, self.data, mutation=True)
        self.data['observations'][2]['rng_equal'] = True
        write(self.folder/'query-result.json', self.data)
        with self.assertRaisesRegex(ValueError, 'Native RNG equality'):
            self.validate(True)

    def test_rng_continuity_and_final_boundary_required(self):
        add_rng(self.folder, self.data)
        path = self.folder/'call-4-before.rng.json'; original = v.read(path)
        write(path, original | dict(state='999 456 1'))
        with self.assertRaisesRegex(ValueError, 'continuity'):
            self.validate(True)
        write(path, original)
        write(self.folder/'final.rng.json', original | dict(state='999 456 1'))
        with self.assertRaisesRegex(ValueError, 'Final RNG'):
            self.validate(True)

    def test_missing_reused_or_partial_rng_evidence_rejected(self):
        add_rng(self.folder, self.data)
        path = self.folder/'call-3-before.rng.json'; value = path.read_bytes(); path.unlink()
        with self.assertRaises(OSError): self.validate(True)
        path.write_bytes(value)
        self.data['observations'][2]['rng_before'] = 'call-2-before.rng.json'
        write(self.folder/'query-result.json', self.data)
        with self.assertRaisesRegex(ValueError, 'filename'):
            self.validate(True)
        (self.folder/'initialized.rng.json').unlink()
        with self.assertRaisesRegex(ValueError, 'without initialization'):
            self.validate()

    def test_strict_schema_absence_and_availability_rejected(self):
        add_rng(self.folder, self.data)
        path = self.folder/'call-3-after.rng.json'; original = v.read(path)
        for changed in [dict(initialized=1), dict(observed=1), dict(scope='all-threads'),
                        dict(state=''), dict(state='bad state'), dict(initialized=False),
                        dict(observed=False, initialized=None, state=None)]:
            write(path, original | changed)
            with self.assertRaises(ValueError): self.validate(True)
