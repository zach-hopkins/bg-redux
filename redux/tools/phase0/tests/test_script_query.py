"""Prevent incomplete autosaves and implicit false values becoming query proof."""
from pathlib import Path
import sys
import unittest
import tempfile
import copy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from script_query_probe import query_values
from capture_original_query import bind_receipt
from harness import digest
from save_harness import manifest


class ScriptQueryOracle(unittest.TestCase):
    def test_completed_explicit_false_is_valid(self):
        self.assertEqual(query_values(dict(RDXVE=0,RDXVD=0,RDXDONE=1,RDXSTAGE=3))['RDXVE'],0)

    def test_chapter_autosave_is_not_completed(self):
        with self.assertRaises(ValueError):query_values({})

    def test_completion_requires_final_stage(self):
        with self.assertRaises(ValueError):query_values(dict(RDXVE=1,RDXVD=1,RDXDONE=1,RDXSTAGE=2))

    def test_missing_boolean_is_not_false(self):
        with self.assertRaises(ValueError):query_values(dict(RDXVE=1,RDXDONE=1,RDXSTAGE=3))

    def test_invalid_boolean_rejected(self):
        for value in (2,True,'1'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                query_values(dict(RDXVE=value,RDXVD=1,RDXDONE=1,RDXSTAGE=3))


class ObservedQueryBinding(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);self.exe=root/'game.exe';self.exe.write_bytes(b'fixture executable')
        self.script=root/'query.bcs';self.script.write_bytes(b'fixture script')
        self.fixture=root/'input';self.saved=root/'output'
        for path in (self.fixture,self.saved):path.mkdir();(path/'state').write_bytes(b'fixture')
        self.receipt=dict(schema='bg-redux-original-query-observation/1',sequence_completed=True,
            executable=dict(path=str(self.exe),sha256=digest(self.exe)),script=dict(path=str(self.script),sha256=digest(self.script)),
            input=dict(path=str(self.fixture),files=manifest(self.fixture)),output=dict(path=str(self.saved),files=manifest(self.saved)))

    def bind(self):bind_receipt(self.receipt,self.exe,self.script,self.fixture,self.saved)

    def test_exact_binding_accepted(self):self.bind()

    def test_output_drift_rejected(self):
        (self.saved/'state').write_bytes(b'different save')
        with self.assertRaises(ValueError):self.bind()

    def test_wrong_executable_rejected(self):
        self.exe.write_bytes(b'different executable')
        with self.assertRaises(ValueError):self.bind()

    def test_uncompleted_observation_rejected(self):
        self.receipt['sequence_completed']=False
        with self.assertRaises(ValueError):self.bind()


if __name__=='__main__':unittest.main()
