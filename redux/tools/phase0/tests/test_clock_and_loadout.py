"""Fail closed on misleading live-clock observations and malformed CRE tables."""
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from live_clock import evaluate
from scan_cre_loadouts import inventory

def clock():
    return dict(ticks_per_second=15,samples=[dict(sample=i,phase='paused-initial' if i<=4 else ('running' if i<=12 else 'paused-final'),
        elapsed_ms=i*250,game_time=100+max(0,min(i,12)-4)*4) for i in range(17)])

class ClockAndLoadout(unittest.TestCase):
    def test_live_clock_observation_passes_without_exact_rate_assumption(self):
        checks,metrics=evaluate(clock());self.assertTrue(all(c['passed'] for c in checks))
        self.assertEqual(metrics['observed_game_ticks_per_wall_second'],16)

    def test_pause_drift_stays_visible(self):
        data=clock();data['samples'][16]['game_time']+=1
        self.assertFalse(next(c['passed'] for c in evaluate(data)[0] if c['name']=='final-pause-stable'))

    def test_frozen_run_is_not_clock_success(self):
        data=clock()
        for row in data['samples']:row['game_time']=100
        self.assertFalse(next(c['passed'] for c in evaluate(data)[0] if c['name']=='resume-advances'))

    def cre(self):
        data=bytearray(0x2d4+80+20);data[:8]=b'CRE V1.0'
        struct.pack_into('<III',data,0x2b8,0x2d4,0x2d4+80,1)
        for i in range(38):struct.pack_into('<H',data,0x2d4+i*2,0xffff)
        struct.pack_into('<H',data,0x2d4,0)
        data[0x2d4+80:0x2d4+88]=b'MAGIWEB\0'
        return data

    def test_loadout_reports_raw_file_slot_without_equipping_claim(self):
        row=inventory(self.cre())[0]
        self.assertEqual((row['item'],row['file_slots']),('magiweb',[0]))

    def test_invalid_slot_index_is_not_silently_skipped(self):
        data=self.cre();struct.pack_into('<H',data,0x2d4,2)
        with self.assertRaises(ValueError):inventory(data)

    def test_truncated_item_entry_fails(self):
        with self.assertRaises(ValueError):inventory(self.cre()[:-1])

if __name__=='__main__':unittest.main()
