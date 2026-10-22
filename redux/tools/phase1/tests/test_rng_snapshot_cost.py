"""Validator sources only; execution is deferred to the coordinator."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('rng_snapshot_cost',Path(__file__).resolve().parents[1]/'rng_snapshot_cost.py')
cost=importlib.util.module_from_spec(spec)
spec.loader.exec_module(cost)


def engine(word=1,index=312): return ' '.join([str(word)]*312+[str(index)])


class CostEvidenceTests(unittest.TestCase):
    def setUp(self):
        unchanged=engine()
        self.data=dict(schema='bg-redux-rng-snapshot-cost/1',nonce='a'*32,pid=123,completed=True,
            fresh_thread=True,trials_expected=3,iterations=100000,time_limit_ms=30000,
            clock='std::chrono::steady_clock',clock_is_steady=True,
            copied_engine_bytes=2504,state_words=312,
            absent=dict(iterations=100000,observed_count=0,output_unchanged=True,initialized_after=False,
                before=unchanged,after=unchanged),
            trials=[dict(trial=i,iterations=100000,observed_count=100000,elapsed_ns=i*1000000,
                before=unchanged,after=unchanged,copied=unchanged) for i in range(1,4)],
            control=dict(real_live_rand_draws=1,before=unchanged,after=engine(2,1)))

    def validate(self): return cost.validate_capture(self.data,'a'*32,123,100000,30000)

    def test_complete_observation_reports_descriptive_cost_without_threshold(self):
        result=self.validate()
        self.assertEqual(result['initialized_calls'],300000)
        self.assertEqual(result['trials'][0]['ns_per_snapshot'],10)
        self.assertFalse(result['performance_threshold_applied'])
        self.assertFalse(result['other_threads_or_combat_performance_proven'])

    def test_absent_api_cannot_initialize_the_live_generator(self):
        self.data['absent']['initialized_after']=True
        with self.assertRaisesRegex(ValueError,'Absent snapshot'): self.validate()

    def test_absent_api_cannot_change_output_despite_forged_unchanged_flag(self):
        self.data['absent']['after']=engine(3)
        with self.assertRaisesRegex(ValueError,'Absent snapshot'): self.validate()

    def test_unavailable_snapshot_cannot_count_as_a_copy(self):
        self.data['trials'][1]['observed_count']=99999
        with self.assertRaisesRegex(ValueError,'unavailable'): self.validate()

    def test_raw_live_rng_mutation_rejected(self):
        self.data['trials'][0]['after']=engine(2)
        with self.assertRaisesRegex(ValueError,'Live RNG changed'): self.validate()

    def test_wrong_copied_engine_is_not_hidden_by_unchanged_live_state(self):
        self.data['trials'][0]['copied']=engine(2)
        with self.assertRaisesRegex(ValueError,'copied state'): self.validate()

    def test_disconnected_trial_before_state_rejected(self):
        self.data['trials'][1].update(before=engine(2),after=engine(2),copied=engine(2))
        with self.assertRaisesRegex(ValueError,'continuity'): self.validate()

    def test_control_must_change_real_live_state_from_final_trial(self):
        self.data['control']['after']=self.data['control']['before']
        with self.assertRaisesRegex(ValueError,'control'): self.validate()

    def test_control_cannot_substitute_an_unrelated_engine(self):
        self.data['control']['before']=engine(3)
        with self.assertRaisesRegex(ValueError,'control'): self.validate()

    def test_stale_nonce_and_wrong_owned_process_rejected(self):
        original=copy.deepcopy(self.data)
        for field,value in (('nonce','b'*32),('pid',456),('completed',False),('fresh_thread',False)):
            self.data=copy.deepcopy(original);self.data[field]=value
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'identity'): self.validate()

    def test_missing_duplicate_and_wrong_sized_trials_rejected(self):
        original=copy.deepcopy(self.data)
        for change in ('missing','duplicate','size'):
            self.data=copy.deepcopy(original)
            if change=='missing': self.data['trials'].pop()
            elif change=='duplicate': self.data['trials'][1]['trial']=1
            else: self.data['trials'][1]['iterations']=1
            with self.subTest(change=change),self.assertRaises(ValueError): self.validate()

    def test_noninteger_and_impossible_budget_timings_rejected(self):
        for value in (True,0,-1,30000000001):
            self.data['trials'][0]['elapsed_ns']=value
            with self.subTest(value=value),self.assertRaises(ValueError): self.validate()

    def test_serialized_engine_requires_exact_words_and_valid_index(self):
        for invalid in ('1 2',engine(index=313),engine(2**64),engine().replace('1','-1',1)):
            with self.subTest(state=invalid[:20]),self.assertRaises(ValueError): cost.state(invalid)


if __name__=='__main__': unittest.main()
