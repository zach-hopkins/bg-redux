"""Branch markers alone must not certify attack execution against the test foe."""
from pathlib import Path
import sys
import json
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ai_fallback import completed_ai


class AIRuntimeOracle(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        (self.root/'engine-profile/save').mkdir(parents=True)
        self.state=dict(globals=dict(rdxaidone=1,rdxfoeseen=1,rdxbranch=118),
            party=[dict(runtime_id=100,inventory=dict(equipped=0,items=[dict(slot=35,resref='SW1H02')]))],
            current_area_actors=[dict(script_name='RDXFOE',runtime_id=200,modified_stats=[190])])
        self.trace=dict(samples=[dict(sample=10,action_trace=[dict(runtime_id=100,action_id=105,current_action_target=200)])])

    def run_oracle(self):
        (self.root/'clock-after.state.json').write_text(json.dumps(self.state))
        (self.root/'clock-samples.json').write_text(json.dumps(self.trace))
        return completed_ai(self.root,dict(first=115))

    def test_observed_attack_target_accepted_without_save(self):
        result=self.run_oracle();self.assertEqual(result['branch'],118);self.assertFalse(result['autosave_present'])

    def test_missing_visibility_rejected(self):
        self.state['globals'].pop('rdxfoeseen')
        with self.assertRaises(ValueError):self.run_oracle()

    def test_marker_without_attack_rejected(self):
        self.trace['samples']=[]
        with self.assertRaises(ValueError):self.run_oracle()

    def test_wrong_target_attack_rejected(self):
        self.trace['samples'][0]['action_trace'][0]['current_action_target']=999
        with self.assertRaises(ValueError):self.run_oracle()

    def test_fists_rejected(self):
        self.state['party'][0]['inventory']['equipped']=1000
        with self.assertRaises(ValueError):self.run_oracle()

    def test_outside_tail_branch_rejected(self):
        self.state['globals']['rdxbranch']=114
        with self.assertRaises(ValueError):self.run_oracle()

    def test_ambiguous_foe_rejected(self):
        self.state['current_area_actors']*=2
        with self.assertRaises(ValueError):self.run_oracle()


if __name__=='__main__':unittest.main()
