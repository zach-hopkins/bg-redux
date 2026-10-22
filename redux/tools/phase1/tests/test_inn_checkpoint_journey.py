"""Meaningful setup/identity/completion negatives; no runtime launch."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import inn_checkpoint_validation as v

def state(area='AR0602',gold=0):
    return dict(current_area=area,gold=gold,selection=1,globals={'JAHEIRARELEASED':1},journal=[dict(text_ref=47518)],party=[dict(runtime_id=100+i,script_name=name,area=area,position=[10,20],inventory=['owned-item'],xp=90000,spellbook=['unchanged'])for i,name in enumerate(('none','imoen','jaheira','minsc'))])

class InnCheckpointContracts(unittest.TestCase):
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
