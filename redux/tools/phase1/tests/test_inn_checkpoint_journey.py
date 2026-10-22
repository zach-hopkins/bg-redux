"""Meaningful setup/identity/completion negatives; no runtime launch."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import zlib
import struct
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import inn_checkpoint_validation as v
import inn_checkpoint_journey as journey

def state(area='AR0602',gold=0):
    return dict(current_area=area,gold=gold,selection=1,globals={'JAHEIRARELEASED':1},journal=[dict(text_ref=47518)],party=[dict(runtime_id=100+i,script_name=name,area=area,position=[10,20],inventory=['owned-item'],xp=90000,spellbook=['unchanged'])for i,name in enumerate(('none','imoen','jaheira','minsc'))])

class InnCheckpointContracts(unittest.TestCase):
    def archive(self,folder,rows):
        data=b'SAV V1.0'
        for name,raw in rows:
            name=name.encode('ascii')+b'\0';packed=zlib.compress(raw)
            data+=struct.pack('<I',len(name))+name+struct.pack('<II',len(raw),len(packed))+packed
        (folder/'BALDUR.SAV').write_bytes(data)

    def test_saved_resources_require_exact_members_and_preserve_stock_contract(self):
        with tempfile.TemporaryDirectory()as root:
            folder=Path(root);cache=folder/'cache';cache.mkdir()
            rows=[('AR0704.are',b'AREAV1.0saved area'),('WINNKEEP.sto',b'STORV1.0saved store')]
            receipt=dict(resources={name:dict(frozen='stock',provider='stock.bif',bytes=8,sha256='stock')for name,_ in rows},nonce='unchanged')
            self.archive(folder,rows);bound=v.reload_resources(receipt,folder,cache)
            self.assertEqual(receipt['resources']['AR0704.are']['sha256'],'stock')
            self.assertEqual(bound['nonce'],'unchanged')
            for name,raw in rows:
                row=bound['resources'][name];self.assertEqual(row['sha256'],v.binary.digest(raw));self.assertEqual(row['saved_member']['archive_sha256'],v.evidence.sha(folder/'BALDUR.SAV'));self.assertEqual(Path(row['provider']),cache/name)
            for broken in (rows[:1],rows+[rows[0]],[(rows[0][0],b'BAD V1.0'),rows[1]]):
                self.archive(folder,broken)
                with self.assertRaises(ValueError):v.reload_resources(receipt,folder,cache)

    def test_runtime_saved_providers_still_reject_wrong_bytes_paths_and_extra_resources(self):
        with tempfile.TemporaryDirectory()as root:
            folder=Path(root);cache=folder/'cache';cache.mkdir();capture=folder/'capture';capture.mkdir()
            rows=[('AR0704.are',b'AREAV1.0saved area'),('WINNKEEP.sto',b'STORV1.0saved store')]
            receipt=dict(resources={name:dict(frozen='stock',provider='stock.bif',bytes=8,sha256='stock')for name,_ in rows})
            self.archive(folder,rows);bound=v.reload_resources(receipt,folder,cache)
            data=dict(schema='bg-redux-book-providers/1',resources={name:dict(originalfile=str(cache/name),bytes=len(raw))for name,raw in rows})
            for name,raw in rows:(capture/(name+'.runtime')).write_bytes(raw)
            def write(value):(capture/'book-providers.json').write_text(json.dumps(value),encoding='utf8')
            write(data);journey.check_runtime_resources(capture,bound)
            for fault in ('path','size','extra','bytes'):
                bad=copy.deepcopy(data)
                if fault=='path':bad['resources']['AR0704.are']['originalfile']=str(folder/'other/AR0704.are')
                elif fault=='size':bad['resources']['AR0704.are']['bytes']+=1
                elif fault=='extra':bad['resources']['extra.are']=bad['resources']['AR0704.are']
                else:(capture/'AR0704.are.runtime').write_bytes(b'AREAV1.0different')
                write(bad)
                with self.subTest(fault=fault),self.assertRaises(ValueError):journey.check_runtime_resources(capture,bound)
                (capture/'AR0704.are.runtime').write_bytes(rows[0][1])

    def test_dialogue_gender_uses_actual_speaker_and_exact_table_words(self):
        table=b'2DA V1.0\n*\n TYPE MALE FEMALE\nSIRMAAM -1 27473 27475\n'
        scene=dict(in_dialog=True,dialogue_speaker=102)
        for sex,word in ((1,'sir'),(2,"ma'am"),(0,'sir')):
            actor=dict(runtime_id=102,modified_stats=[0]*35+[sex])
            self.assertEqual(v.resolved_dialogue('Certainly, <SIRMAAM>.',table,{'27473':'sir','27475':"ma'am"},dict(party=[actor]),scene),'Certainly, '+word+'.')
        for raw,badtable,words,speaker in (('Certainly, <UNKNOWN>.',table,{'27473':'sir','27475':"ma'am"},102),('Certainly, <SIRMAAM>.',table.replace(b'-1',b'0'),{'27473':'sir','27475':"ma'am"},102),('Certainly, <SIRMAAM>.',table,{'27473':'sir'},102),('Certainly, <SIRMAAM>.',table,{'27473':'sir','27475':"ma'am"},999)):
            with self.assertRaises(ValueError):v.resolved_dialogue(raw,badtable,words,dict(party=[actor]),dict(scene,dialogue_speaker=speaker))

    def test_actual_runtime_declares_the_same_independent_fixed_plan(self):
        for mode in ('prepare','observe'):
            values={};gem=types.SimpleNamespace(SetVar=lambda k,n:values.__setitem__(k,n))
            spec=importlib.util.spec_from_file_location('InnRuntimeContract',Path(__file__).resolve().parents[1]/'InnCheckpointRuntime.py');runtime=importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules,{'GemRB':gem}):spec.loader.exec_module(runtime)
            runtime.Configure('/unused-private-output','a'*32,mode,'characterize-current')
            self.assertEqual([n for n,_ in runtime.PLAN],v.plan(mode))
            if mode=='observe':self.assertFalse(any(n.startswith('debug-')for n,_ in runtime.PLAN))

    def test_only_all_four_transfer_is_accepted(self):
        before=state();after=state('AR0704');after['party']=[dict(a,area='AR0704')for a in before['party']]
        v.setup_guard(1,before,after)
        for i in range(4):
            wrong=copy.deepcopy(after);wrong['party'][i]['area']='AR0602'
            with self.subTest(actor=i),self.assertRaises(ValueError):v.setup_guard(1,before,wrong)

    def test_transfer_cannot_hide_grants_party_reordering_or_quest_changes(self):
        before=state();after=state('AR0704')
        for problem in ('inventory','xp','order','global','journal'):
            bad=copy.deepcopy(after)
            if problem=='inventory':bad['party'][1]['inventory'].append('granted')
            elif problem=='xp':bad['party'][1]['xp']+=1
            elif problem=='order':bad['party'].reverse()
            elif problem=='global':bad['globals']['CHAPTER']=2
            else:bad['journal'].clear()
            with self.subTest(problem=problem),self.assertRaises(ValueError):v.setup_guard(1,before,bad)

    def test_currency_is_exact_zero_to100_and_no_other_setter(self):
        before=state('AR0704');after=copy.deepcopy(before);after['gold']=100;v.setup_guard(2,before,after)
        for amount in (0,1,99,101,200):
            bad=copy.deepcopy(after);bad['gold']=amount
            with self.subTest(amount=amount),self.assertRaises(ValueError):v.setup_guard(2,before,bad)
        bad=copy.deepcopy(after);bad['party'][0]['inventory'].append('granted')
        with self.assertRaises(ValueError):v.setup_guard(2,before,bad)
        with self.assertRaises(ValueError):v.setup_guard(2,after,dict(after,gold=200))

    def scenes(self):
        ids=[100,101,102,103]
        queued=dict(area='AR0602',idle=False,party=[dict(id=n,area='AR0704',position=[10,20],current=None,next=109,moving=False)for n in ids])
        complete=dict(area='AR0704',idle=True,party=[dict(id=n,area='AR0704',position=list(p),current=None,next=None,moving=False)for n,p in zip(ids,v.POINTS)])
        return queued,complete,ids

    def test_action_entry_never_substitutes_for_completed_coherent_transfer(self):
        q,c,ids=self.scenes();v.transfer_completion(q,c,ids,109)
        for fault in ('queued','busy','position','area','id','duplicate'):
            left=copy.deepcopy(q);right=copy.deepcopy(c)
            if fault=='queued':left['party'][2]['next']=None
            elif fault=='busy':right['party'][1]['current']=109
            elif fault=='position':right['party'][3]['position']=[5000,5000]
            elif fault=='area':right['party'][0]['area']='AR0602'
            elif fault=='id':right['party'][0]['id']=999
            else:right['party'][1]['id']=100
            with self.subTest(fault=fault),self.assertRaises(ValueError):v.transfer_completion(left,right,ids,109)

    def test_saved_fixture_must_retain_parent_proofs_and_one_inn_talk(self):
        old=dict(gold=0,checkpoint={'retained':'quest/items/xp'},spellbooks=['exact'],locations=[dict(area='AR0602',position=[10,20])for _ in range(4)],inn_target=None)
        new=dict(old,gold=100,locations=[dict(area='AR0704',position=p)for p in v.POINTS],inn_target=dict(talk_count=1))
        v.wire_setup_guard(old,new)
        approached=copy.deepcopy(new);approached['locations'][0]['position']=[792,438]
        v.wire_setup_guard(old,approached)
        remote=copy.deepcopy(new);remote['locations'][0]['position']=[2000,2000]
        with self.assertRaises(ValueError):v.wire_setup_guard(old,remote)
        for key,value in (('gold',101),('checkpoint',{}),('spellbooks',[]),('inn_target',dict(talk_count=2))):
            with self.subTest(key=key),self.assertRaises(ValueError):v.wire_setup_guard(old,dict(new,**{key:value}))

    def test_terminal_cannot_claim_campaign_parity_or_wrong_nonce(self):
        nonce='a'*32;good=dict(schema='bg-redux-inn-host/1',nonce=nonce,mode='prepare',completed=True,error='',ordinary_campaign_transfer=False,declared_debug_setup=True,os_pointer_input=False,production_inn_policy_changed=False)
        with tempfile.TemporaryDirectory()as root:
            folder=Path(root);(folder/'book-runtime.json').write_text('{}',encoding='utf8')
            for key,value in (('nonce','b'*32),('ordinary_campaign_transfer',True),('declared_debug_setup',False),('production_inn_policy_changed',True),('completed',False)):
                (folder/'book-result.json').write_text(json.dumps(dict(good,**{key:value})),encoding='utf8')
                with self.subTest(key=key),self.assertRaises(ValueError):v.validate_capture(folder,nonce,'prepare',None,{})

    def test_runtime_rejects_undeclared_mode_policy_and_nonce(self):
        spec=importlib.util.spec_from_file_location('InnScopeContract',Path(__file__).resolve().parents[1]/'InnCheckpointRuntime.py');runtime=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'GemRB':types.SimpleNamespace(SetVar=lambda *args:None)}):spec.loader.exec_module(runtime)
        for mode,nonce,policy in (('rest','a'*32,'characterize-current'),('prepare','A'*32,'characterize-current'),('prepare','a'*32,'fix-inn')):
            with self.subTest(mode=mode,policy=policy),self.assertRaises(RuntimeError):runtime.Configure('/unused',nonce,mode,policy)

if __name__=='__main__':unittest.main()
