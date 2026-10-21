"""Mutation checks use the actual native vanilla snapshot as the oracle input."""
from pathlib import Path
import copy
import json
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from save_harness import normalize, differences, assertion
from harness import LOCAL


class NativeSnapshotOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidates=list((LOCAL/'results').glob('*vanilla-oracle*/import/state.json'))
        if not candidates: raise RuntimeError('Required executed vanilla snapshot missing; no silent skip')
        cls.raw=json.loads(max(candidates,key=lambda p:p.stat().st_mtime).read_text(encoding='utf-8'))

    def changed(self,mutate):
        changed=copy.deepcopy(self.raw)
        mutate(changed)
        self.assertTrue(differences(normalize(self.raw),normalize(changed)))

    def test_damage_is_detected(self):
        self.changed(lambda s:s['party'][0]['base_stats'].__setitem__(0,s['party'][0]['base_stats'][0]-1))

    def test_charge_loss_is_detected(self):
        self.changed(lambda s:s['party'][1]['inventory']['items'][0]['usages'].__setitem__(1,99))

    def test_wrong_global_is_detected(self):
        self.changed(lambda s:s['globals'].__setitem__('CHAPTER',999))

    def test_missing_actor_is_detected(self):
        self.changed(lambda s:s['current_area_actors'].pop())

    def test_color_changes_remain_visible(self):
        self.changed(lambda s:s['current_area_actors'][0]['base_stats'].__setitem__(213,123))

    def test_effect_duration_change_is_detected(self):
        self.changed(lambda s:s['party'][1]['effects'][0].__setitem__('duration',123456789))

    def test_missing_query_is_failure(self):
        result=assertion(self.raw,dict(path='/party/999/name',op='exists'))
        self.assertFalse(result['passed'])

    def test_wrong_expected_area_is_failure(self):
        result=assertion(self.raw,dict(path='/current_area',op='eq',value='AR_FAKE'))
        self.assertFalse(result['passed'])


if __name__=='__main__': unittest.main()
