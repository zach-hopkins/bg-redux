import importlib.util
from pathlib import Path
import unittest
import test_stats_validation as fixture_module

spec = importlib.util.spec_from_file_location('stats_failed_review_test', Path(__file__).resolve().parents[1] / 'stats_failed_review.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class CompletedStatsFailureTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_module.StatsValidationTests('test_complete_four_actor_journey')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def review(self):
        return review.review_completed_world_difference(self.fixture.path,(1,1),
            expected_nonce='0123456789abcdef0123456789abcdef',tlk_path=self.fixture.tlk)

    def test_completed_world_difference_is_reviewable_but_never_accepted(self):
        self.fixture.write('after.state.json',dict(self.fixture.world,gold=99))
        result = self.review()
        self.assertFalse(result['accepted'])
        self.assertTrue(result['preceding_strict_ui_numeric_callback_checks_completed'])
        self.assertEqual(result['undeclared_changes'],[dict(path='/gold',before=100,after=99)])

    def test_incomplete_ui_failure_cannot_be_relabelled_a_completed_review(self):
        call = self.fixture.read('callback-1.json')
        call['control'] = 5
        self.fixture.write('callback-1.json',call)
        with self.assertRaisesRegex(ValueError,'callback'):
            self.review()

    def test_passed_journey_cannot_be_presented_as_a_failure_review(self):
        with self.assertRaisesRegex(ValueError,'requires the completed'):
            self.review()
