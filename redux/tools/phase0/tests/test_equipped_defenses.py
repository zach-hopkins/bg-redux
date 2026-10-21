"""Reject laboratory setup drift rather than mislabeling fists as a weapon test."""
from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from equipped_defenses import validate_observation,effect
from effect_cycle import u32,u16


class EquippedPreflight(unittest.TestCase):
    def actors(self):return [dict(physical_slots={'9':'sw1h01'},selected=0,ability=0),dict(defense_effects=[])]

    def test_equipped_normal_weapon_accepted(self):validate_observation(dict(weapon='sw1h01',defense=None),self.actors())

    def test_fists_or_invalid_selection_rejected(self):
        for slot in (1000,-25,1):
            actors=self.actors();actors[0]['selected']=slot
            with self.subTest(slot=slot),self.assertRaises(ValueError):validate_observation(dict(weapon='sw1h01',defense=None),actors)

    def test_wrong_weapon_rejected(self):
        with self.assertRaises(ValueError):validate_observation(dict(weapon='sw1h02',defense=None),self.actors())

    def test_missing_ammunition_rejected(self):
        actors=self.actors();actors[0].update(physical_slots={'9':'bow01'},selected=-24)
        with self.assertRaises(ValueError):validate_observation(dict(weapon='bow01',defense=None),actors)

    def test_bow_and_arrow_selection_accepted(self):
        actors=self.actors();actors[0].update(physical_slots={'9':'bow01','13':'arow01'},selected=-24)
        validate_observation(dict(weapon='bow01',defense=None),actors)

    def test_missing_defense_rejected(self):
        with self.assertRaises(ValueError):validate_observation(dict(weapon='sw1h01',defense=(86,100,1)),self.actors())

    def test_changed_defense_amount_rejected(self):
        actors=self.actors();actors[1]['defense_effects']=[dict(opcode=86,p1=0,p2=1,timing=9)]
        with self.assertRaises(ValueError):validate_observation(dict(weapon='sw1h01',defense=(86,100,1)),actors)

    def test_effect_wire_shape(self):
        data=effect(86,100,1)
        self.assertEqual(len(data),264);self.assertEqual(u32(data,8),86);self.assertEqual(u32(data,20),100)
        self.assertEqual(u16(data,28),9);self.assertEqual(u16(data,36),100);self.assertEqual(data[140:148],b'RDXDEF\0\0')


if __name__=='__main__':unittest.main()
