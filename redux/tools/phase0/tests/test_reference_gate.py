"""Ensure missing/uncertified reference data cannot become original-runtime proof."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import original_reference as reference
from harness import LOCAL
from probe_ui_resources import read_resource,TYPES
from scan_equipping import item_effects

class ReferenceGate(unittest.TestCase):
    def test_observed_receipt_binds_files_and_executable(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder);fixture=self.setup_local(directory)
            exe=directory/'Baldur.exe';exe.write_bytes(b'synthetic executable')
            receipt=directory/'observation.json'
            data=dict(schema='bg-redux-original-ui-observation/1',executable=str(exe),
                executable_sha256=reference.digest(exe),sequence_completed=True,
                saves={k:dict(files=reference.manifest(fixture)) for k in ['reload1','reload2']})
            receipt.write_text(json.dumps(data))
            self.assertEqual(reference.observed_receipt(receipt,exe,fixture,fixture),data)
            exe.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'executable hash drift'):
                reference.observed_receipt(receipt,exe,fixture,fixture)

    def test_observed_receipt_rejects_changed_save(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder);fixture=self.setup_local(directory)
            exe=directory/'Baldur.exe';exe.write_bytes(b'synthetic executable')
            receipt=directory/'observation.json'
            receipt.write_text(json.dumps(dict(schema='bg-redux-original-ui-observation/1',executable=str(exe),
                executable_sha256=reference.digest(exe),sequence_completed=True,
                saves={k:dict(files={}) for k in ['reload1','reload2']})))
            with self.assertRaisesRegex(ValueError,'save manifest mismatch'):
                reference.observed_receipt(receipt,exe,fixture,fixture)

    def setup_local(self,directory):
        (directory/'results').mkdir()
        fixture=directory/'fixtures/original-bg2ee-20261020/GemRB'
        fixture.parent.mkdir(parents=True)
        shutil.copytree(LOCAL/'fixtures/original-bg2ee-20261020/GemRB',fixture)
        return fixture

    def test_missing_references_remain_pending(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder);(directory/'results').mkdir()
            captured=[]
            with patch.object(reference,'LOCAL',directory),patch.object(reference,'write',side_effect=lambda p,v:captured.append(v)):
                rc=reference.main(['--profile',str(directory/'empty-profile')])
            self.assertEqual(rc,2)
            self.assertEqual(captured[-1]['verdict'],'pending-reference')
            self.assertFalse(captured[-1]['observations'])

    def test_identical_files_without_runtime_provenance_are_not_certified(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder);fixture=self.setup_local(directory);captured=[]
            with patch.object(reference,'LOCAL',directory),patch.object(reference,'write',side_effect=lambda p,v:captured.append(v)):
                rc=reference.main(['--first',str(fixture),'--second',str(fixture)])
            self.assertEqual(rc,2)
            self.assertEqual(captured[-1]['verdict'],'reference-provenance-unconfirmed')
            self.assertEqual(captured[-1]['progression'],[7,7,7])

    def test_corrupted_frozen_copy_fails_instead_of_comparing(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder);fixture=self.setup_local(directory);captured=[]
            real_copy=shutil.copytree
            def corrupt(source,destination,*args,**kwargs):
                result=real_copy(source,destination,*args,**kwargs)
                gam=next(p for p in Path(destination).iterdir() if p.name.lower()=='baldur.gam')
                with gam.open('ab') as stream:stream.write(b'changed')
                return result
            with patch.object(reference,'LOCAL',directory),patch.object(reference,'write',side_effect=lambda p,v:captured.append(v)),patch.object(reference.shutil,'copytree',side_effect=corrupt):
                rc=reference.main(['--first',str(fixture),'--second',str(fixture),'--human-confirmed-clean'])
            self.assertEqual(rc,1)
            self.assertEqual(captured[-1]['verdict'],'failed')
            self.assertIn('changed during copy',captured[-1]['error'])

    def test_item_exposure_separates_permanent_from_equipped(self):
        TYPES['itm']=0x3ed
        data,_=read_resource('immcloud','itm')
        rows=item_effects(data)
        self.assertEqual((sum(r['timing']==1 for r in rows),sum(r['timing']==2 for r in rows)),(7,6))

    def test_bad_reference_compression_is_a_structured_failure(self):
        from effect_cycle import u32,text
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder);fixture=self.setup_local(directory);first=directory/'first'
            shutil.copytree(fixture,first);captured=[]
            sav=next(p for p in first.iterdir() if p.name.lower()=='baldur.sav');data=bytearray(sav.read_bytes());at=8
            while at<len(data):
                n=u32(data,at);at+=4;name=text(data[at:at+n]);at+=n
                packed=u32(data,at+4)
                if name.lower()=='ar0602.are':data[at+8]^=0xff;break
                at+=8+packed
            else:self.fail('Required reference area absent')
            sav.write_bytes(data)
            with patch.object(reference,'LOCAL',directory),patch.object(reference,'write',side_effect=lambda p,v:captured.append(v)):
                rc=reference.main(['--first',str(first),'--second',str(fixture),'--human-confirmed-clean'])
            self.assertEqual(rc,1)
            self.assertEqual(captured[-1]['verdict'],'failed')

    def test_truncated_item_cannot_silently_omit_last_effect(self):
        TYPES['itm']=0x3ed
        data,_=read_resource('immcloud','itm')
        with self.assertRaises(ValueError):item_effects(data[:-1])

if __name__=='__main__':unittest.main()
