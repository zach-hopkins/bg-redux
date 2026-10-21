"""Static exposure must not turn malformed BCS or OR alternatives into proof."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scan_weapon_triggers import condition_blocks

def record(opcode,flags=0):
    return f'TR\n{opcode} 1 {flags} 0 0 "" "" OB\n0 0 0 0 0 0 0 1 12 0 0 0 ""OB\nTR\n'

def script(condition):return ('SC\nCR\nCO\n'+condition+'CO\nRS\nRE\n100AC\n105OB\nRE\nRS\nCR\nSC\n').encode()

class WeaponExposure(unittest.TestCase):
    def test_or_alternative_prevents_unconditional_false_inference(self):
        hits,_=condition_blocks(script(record(0x4000)+record(0x40ec)))
        self.assertTrue(hits[0]['contains_or']);self.assertFalse(hits[0]['positive_stub_without_or'])

    def test_negated_stub_does_not_become_false_branch_claim(self):
        hits,_=condition_blocks(script(record(0x40ec,1)))
        self.assertFalse(hits[0]['positive_stub_without_or'])

    def test_truncated_record_refused(self):
        data=script(record(0x40ec)).replace(b'""OB\nTR\n',b'""OB\n')
        with self.assertRaises(ValueError):condition_blocks(data)

    def test_trigger_outside_response_blocks_is_not_omitted(self):
        with self.assertRaises(ValueError):condition_blocks(b'SC\n'+record(0x40ec).encode()+b'SC\n')

if __name__=='__main__':unittest.main()
