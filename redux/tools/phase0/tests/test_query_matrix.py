"""The batch oracle must require all controls rather than default false."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from query_matrix import CASES,values


class MatrixOracle(unittest.TestCase):
    def complete(self):return dict(RDXMDONE=1,RDXMSTAGE=9,**{c['key']:0 for c in CASES})

    def test_explicit_zero_controls_accepted(self):self.assertEqual(len(values(self.complete())),8)

    def test_missing_control_rejected(self):
        record=self.complete();record.pop('RDXMVD6')
        with self.assertRaises(ValueError):values(record)

    def test_partial_batch_rejected(self):
        record=self.complete();record['RDXMSTAGE']=8
        with self.assertRaises(ValueError):values(record)

    def test_non_boolean_rejected(self):
        record=self.complete();record['RDXMVE1']=2
        with self.assertRaises(ValueError):values(record)


if __name__=='__main__':unittest.main()
