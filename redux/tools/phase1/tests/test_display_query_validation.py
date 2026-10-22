"""Reject false display-query acceptance, including insensitive controls."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('display_validation_test', Path(__file__).resolve().parents[1]/'display_query_validation.py')
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)
NONCE = '0123456789abcdef0123456789abcdef'


class DisplayQueryValidationTests(unittest.TestCase):
    def write(self, name, data):
        (self.path/name).write_text(json.dumps(data), encoding='utf8')

    def read(self, name):
        return json.loads((self.path/name).read_text(encoding='utf8'))

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)
        self.write('menu-host-result.json', dict(nonce=NONCE,completed=True,journey='display-query',callbacks=0,captures=3))
        names = ['before','rng-control','pure','after-pure','legacy-default','legacy-false','arm-3e','reject-3e','final']
        actions = [dict(action='display.'+name,step=i,capture={0:1,3:2,8:3}.get(i)) for i,name in enumerate(names)]
        details = dict(ToHitStats=dict(Base=14,Ability=-2,Total=12),APR=2)
        samples = [dict(actor=pc,hand=hand,actor_name='Minsc' if pc==4 else 'Actor%d'%pc,
                        before=14,after=14,repeat_equal=True,details=copy.deepcopy(details))
                   for pc in range(1,5) for hand in (0,1)]
        signals = dict(eq14=True,eq12=False,gt13=True,missing=False,control=True)
        checks = actions + [dict(name='display-query.pure',passed=True,samples=samples,
            before_signals=signals,after_signals=signals,total_api_calls=144,repeated_calls=128,all_repeats_equal=True)]
        for name,before in [('legacy-default',14),('legacy-false',12)]:
            checks.append(dict(name='display-query.'+name,passed=True,before=before,after=12,
                               equals_display_result=True,details=copy.deepcopy(details)))
        checks += [dict(name='display-query.reject-3e',passed=True,error_message='Display-only combat details require 2E rules'),
                   dict(name='display-query.rng-control',passed=True,result=10)]
        self.write('menu-runtime.json',dict(nonce=NONCE,steps=9,planned_steps=9,checks=checks))
        self.log = ('normal native output\n[DisplayQueryControl]: begin unsupported-3e rejection\n'
                    '[GUIScript/ERROR]: Runtime Error:\n[DisplayQueryControl]: end unsupported-3e rejection\n')
        (self.path/'process.log').write_text(self.log,encoding='utf8')
        for i,(kind,step) in enumerate(zip([5,1,2,3,4],[2,3,5,6,8]),1):
            self.write('display-query-step-%d.json'%i,dict(nonce=NONCE,kind=kind,runtime_step=step,
                actor_stats_and_cache_bytes_unchanged=kind!=2,calling_thread_rng_before_available=True,
                calling_thread_rng_after_available=True,calling_thread_rng_unchanged=kind!=5,
                controlled_3e_rejection=kind==4,feature_flag_restored=True,python_step_nanoseconds=100))
        stats = [0]*256;stats[7]=14
        actor = dict(name='Minsc',runtime_id=4,modified_stats=stats)
        world = dict(party=[dict(name='Actor%d'%i,runtime_id=i,modified_stats=list(stats)) for i in range(1,4)]+[actor],
                     current_area_actors=[copy.deepcopy(actor)],gold=100)
        self.write('capture-1.state.json',world);self.write('capture-2.state.json',world)
        final = copy.deepcopy(world)
        final['party'][3]['modified_stats'][7]=12;final['current_area_actors'][0]['modified_stats'][7]=12
        self.write('capture-3.state.json',final)

    def validate(self):
        return validation.validate_stage(self.path,expected_nonce=NONCE)

    def mutate_native(self, index, **changes):
        name='display-query-step-%d.json'%index
        value=self.read(name);value.update(changes);self.write(name,value)

    def mutate_check(self, name, **changes):
        runtime=self.read('menu-runtime.json')
        next(row for row in runtime['checks'] if row.get('name')==name).update(changes)
        self.write('menu-runtime.json',runtime)

    def test_accepts_bounded_purity_with_declared_controls(self):
        result=self.validate()
        self.assertTrue(result['pure_phase_world_unchanged'])
        self.assertFalse(result['collected_world_unchanged'])
        self.assertFalse(result['hidden_state_or_other_threads_purity'])

    def test_rejects_stale_native_nonce(self):
        self.mutate_native(2,nonce='f'*32)
        with self.assertRaisesRegex(ValueError,'nonce'):self.validate()

    def test_rejects_missing_native_observation(self):
        (self.path/'display-query-step-3.json').unlink()
        with self.assertRaisesRegex(ValueError,'coverage'):self.validate()

    def test_rejects_pure_cache_mutation(self):
        self.mutate_native(2,actor_stats_and_cache_bytes_unchanged=False)
        with self.assertRaisesRegex(ValueError,'actor/cache'):self.validate()

    def test_rejects_pure_rng_draw(self):
        self.mutate_native(2,calling_thread_rng_unchanged=False)
        with self.assertRaisesRegex(ValueError,'RNG'):self.validate()

    def test_rejects_insensitive_rng_control(self):
        self.mutate_native(1,calling_thread_rng_unchanged=True)
        with self.assertRaisesRegex(ValueError,'RNG'):self.validate()

    def test_rejects_insensitive_legacy_control(self):
        self.mutate_native(3,actor_stats_and_cache_bytes_unchanged=True)
        with self.assertRaisesRegex(ValueError,'actor/cache'):self.validate()

    def test_rejects_unrestored_feature_flag(self):
        self.mutate_native(5,feature_flag_restored=False)
        with self.assertRaisesRegex(ValueError,'restore'):self.validate()

    def test_rejects_wrong_legacy_parity(self):
        self.mutate_check('display-query.legacy-default',details={})
        with self.assertRaisesRegex(ValueError,'legacy'):self.validate()

    def test_rejects_changed_trigger_contract(self):
        self.mutate_check('display-query.pure',after_signals={})
        with self.assertRaisesRegex(ValueError,'trigger'):self.validate()

    def test_rejects_pure_world_mutation(self):
        value=self.read('capture-2.state.json');value['gold']=101;self.write('capture-2.state.json',value)
        with self.assertRaisesRegex(ValueError,'pure phase'):self.validate()

    def test_rejects_extra_control_world_mutation(self):
        value=self.read('capture-3.state.json');value['gold']=101;self.write('capture-3.state.json',value)
        with self.assertRaisesRegex(ValueError,'additional world'):self.validate()

    def test_rejects_unproven_unsupported_rules(self):
        self.mutate_native(5,controlled_3e_rejection=False)
        with self.assertRaisesRegex(ValueError,'unsupported-rules'):self.validate()

    def test_rejects_error_outside_expected_control(self):
        (self.path/'process.log').write_text('[GUIScript/ERROR]: Runtime Error:\n'+self.log,encoding='utf8')
        with self.assertRaisesRegex(ValueError,'callback error'):self.validate()

    def test_rejects_missing_expected_error(self):
        (self.path/'process.log').write_text(self.log.replace('[GUIScript/ERROR]: Runtime Error:\n',''),encoding='utf8')
        with self.assertRaisesRegex(ValueError,'callback error'):self.validate()

    def test_rejects_missing_error_boundary(self):
        (self.path/'process.log').write_text('normal native output\n',encoding='utf8')
        with self.assertRaisesRegex(ValueError,'boundary'):self.validate()


if __name__ == '__main__':
    unittest.main()
