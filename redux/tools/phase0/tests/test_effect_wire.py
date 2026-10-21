"""Malformed input and content mutations against the real saved-area fixture."""
import copy
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import effect_cycle
from harness import LOCAL

class EffectWire(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=LOCAL/'fixtures/original-bg2ee-20261020/GemRB'
        cls.area=effect_cycle.area_from_save(cls.fixture)

    def test_original_wire_contains_seven_permanent_markers(self):
        result=effect_cycle.summarize_effects(effect_cycle.wire_target(self.fixture)['effects'])
        self.assertEqual((result['total'],result['permanent'],result['equipped']),(7,7,0))

    def test_truncated_sav_is_not_a_pass(self):
        source=next(p for p in self.fixture.iterdir() if p.name.lower()=='baldur.sav').read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/'baldur.sav').write_bytes(source[:-1])
            with self.assertRaises(ValueError):effect_cycle.area_from_save(Path(folder))

    def test_excessive_decompression_claim_is_refused(self):
        data=bytearray(next(p for p in self.fixture.iterdir() if p.name.lower()=='baldur.sav').read_bytes())
        at=8
        while at<len(data):
            n=effect_cycle.u32(data,at);at+=4;name=effect_cycle.text(data[at:at+n]);at+=n
            packed=effect_cycle.u32(data,at+4)
            if name.lower()=='ar0602.are':
                struct.pack_into('<I',data,at,effect_cycle.MAX+1);break
            at+=8+packed
        else:self.fail('Required area missing')
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/'baldur.sav').write_bytes(data)
            with self.assertRaises(ValueError):effect_cycle.area_from_save(Path(folder))

    def test_impossible_effect_count_is_refused(self):
        data=bytearray(self.area)
        offset,count=effect_cycle.u32(data,0x54),effect_cycle.u16(data,0x58)
        for i in range(count):
            at=offset+i*272
            if struct.unpack_from('<HH',data,at+32)==(2573,2461):
                cre=effect_cycle.u32(data,at+136);struct.pack_into('<I',data,cre+0x2c8,10001);break
        else:self.fail('Required target missing')
        with patch.object(effect_cycle,'area_from_save',return_value=bytes(data)):
            with self.assertRaises(ValueError):effect_cycle.wire_target(self.fixture)

    def test_changed_protection_is_visible_in_signature(self):
        raw=effect_cycle.wire_target(self.fixture)['effects']
        changed=copy.deepcopy(raw);changed[0]['parameters'][0]+=1
        self.assertNotEqual(effect_cycle.summarize_effects(raw),effect_cycle.summarize_effects(changed))

if __name__=='__main__':unittest.main()
