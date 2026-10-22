"""Pure receipt corruption tests. No native process is started by this module."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import jaheira_dialogue_journey as journey


class DialogueValidationTests(unittest.TestCase):
    def write(self,root,name,value):
        (root/name).write_text(json.dumps(value),encoding='utf-8')

    def actor(self,name,identity,party):
        return dict(script_name=name,runtime_id=identity,in_party=party,position=[3898,2676] if name=='jaheira' else [3741,2801],
            area='AR0602',base_stats=[0]*256,modified_stats=[0]*256,inventory={},effects=[],spellbook={},locals={})

    def checkpoint(self,root,name,talked=False,journaled=None,time=5,in_dialog=False):
        if journaled is None:journaled=talked
        target=self.actor('jaheira',10005,0)
        state=dict(schema='bg-redux-state/1',game_time=time,current_area='AR0602',selection=1,globals={'CHAPTER':1},area_locals={},
            party=[self.actor('None',10002,1),self.actor('Imoen',10003,2)],stored_npcs=[],current_area_actors=[target],
            journal=[dict(text_ref=x,section=1,chapter=1,time=0,group=0) for x in [34089,96383]+([34105] if journaled else [])],journal_count=3 if journaled else 2)
        scene=dict(schema='bg-redux-dialogue-scene/1',target_name='jaheira',target_id=10005,target_position=[3898,2676],dialog='JAHEIRA',
            talk_count=int(talked),leader_id=10002,party_count=2,door_name='Cell01',door_flags=1634,door_open=False,has_key=False,
            in_dialog=in_dialog,target_action_id=None,target_next_action_id=None,target_moving=False,game_time=time,
            dialogue_target_id=10005 if in_dialog else None,dialogue_speaker_id=10002 if in_dialog else None,
            party_actions=[dict(runtime_id=i,action_id=None,next_action_id=None,moving=False,position=[3741,2801]) for i in (10002,10003)])
        self.write(root,name+'.scene.json',scene);self.write(root,name+'.state.json',state)
        (root/(name+'.bmp')).write_bytes(b'BM'+bytes(52))
        return scene,state

    def fixture(self,root):
        nonce='a'*32;texts={b[1]:'NPC_'+str(b[1]) for b in journey.BRANCHES}
        texts.update({904:'RESPONSE_904',923:'RESPONSE_923'})
        self.checkpoint(root,'loaded',time=0);self.checkpoint(root,'ready',time=4)
        for name in ('after-dialogue','before-save','final'):self.checkpoint(root,name,True)
        samples=[]
        for index in range(4):
            name='startup-'+str(index);self.checkpoint(root,name,time=index+1)
            samples.append(dict(checkpoint=name,idle=True,consecutive_idle=index+1,tick=index+2,game_time=index+1))
        events=[]
        def event(kind,details):events.append(dict(sequence=len(events)+1,tick=len(events)+1,nonce=nonce,kind=kind,details=details))
        def button(pack,window,control):event('registered-button',dict(pack=pack,window=window,control=control,performed=True))
        button('GUILOAD',0,26);event('ordinary-talk-request',dict(route='GameControl::TryToTalk/NIDSpecial1',target_id=10005))
        self.write(root,'talk-request.message.json',dict(observed_text=''))
        previous=''
        for index,(state,ref,tr,local,response) in enumerate(journey.BRANCHES):
            self.checkpoint(root,'branch-'+str(index),True,False,in_dialog=True)
            message=texts[ref]+(' '+texts[response] if response else '')
            self.write(root,'branch-'+str(index)+'.text.json',dict(expected_npc_strref=ref,expected_npc_text=texts[ref],message_text=message,
                previous_text=previous,npc_occurrences_before=previous.count(texts[ref]),npc_occurrences_after=message.count(texts[ref])))
            previous=message
            event('registered-response' if response else 'registered-continue-end',dict(state=state,npc_strref=ref,transition=tr,
                local_transition=local,response_strref=response,performed=True))
        button('GUIOPT',2,6);button('GUISAVE',0,26);event('registered-save-name',dict(performed=True,control=3));button('GUISAVE',1,7)
        native=dict(schema='bg-redux-jaheira-native/1',nonce=nonce,journey='talk',completed=True,error='',os_pointer_input=False,
            forced_dialogue_state=False,talk_requests=1,branches_completed=11,startup_samples=samples,events=events,saves=['private/save/output'],ticks_per_second=1)
        self.write(root,'dialogue-result.json',native)
        return nonce,texts,native

    def test_complete_stock_response_effect_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);nonce,texts,_=self.fixture(root)
            self.assertEqual(journey.validate_capture(root,nonce,texts=texts)['callbacks'],17)

    def test_wrong_branch_and_missing_callback_are_rejected(self):
        for mutation in ('wrong-transition','missing-callback'):
            with tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);nonce,texts,native=self.fixture(root)
                if mutation=='wrong-transition':native['events'][2]['details']['transition']=3
                else:native['events'].pop(2)
                self.write(root,'dialogue-result.json',native)
                with self.assertRaises(ValueError):journey.validate_capture(root,nonce,texts=texts)

    def test_repeated_talk_or_forced_state_cannot_satisfy_journey(self):
        for key,value in [('talk_requests',2),('forced_dialogue_state',True),('completed',False)]:
            with tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);nonce,texts,native=self.fixture(root);native[key]=value
                self.write(root,'dialogue-result.json',native)
                with self.assertRaises(ValueError):journey.validate_capture(root,nonce,texts=texts)

    def test_wrong_nonce_and_stale_files_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);nonce,texts,_=self.fixture(root)
            with self.assertRaises(ValueError):journey.validate_capture(root,'b'*32,texts=texts)
            with self.assertRaisesRegex(ValueError,'Stale'):journey.validate_capture(root,nonce,started_ns=10**30,texts=texts)

    def test_fabricated_talk_counter_and_wrong_target_rejected(self):
        for key,value in [('talk_count',0),('talk_count',True),('target_id',10003),('target_name','minsc')]:
            with tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);nonce,texts,_=self.fixture(root)
                scene=json.loads((root/'final.scene.json').read_text());scene[key]=value;self.write(root,'final.scene.json',scene)
                with self.assertRaises(ValueError):journey.validate_capture(root,nonce,texts=texts)

    def test_duplicate_or_fabricated_journal_and_wrong_section_rejected(self):
        for mutation in ('duplicate','wrong-entry','wrong-section'):
            with tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);nonce,texts,_=self.fixture(root);state=json.loads((root/'final.state.json').read_text())
                if mutation=='duplicate':state['journal'].append(copy.deepcopy(state['journal'][-1]));state['journal_count']+=1
                elif mutation=='wrong-entry':state['journal'][-1]['text_ref']=99999
                else:state['journal'][-1]['section']=0
                self.write(root,'final.state.json',state)
                with self.assertRaises(ValueError):journey.validate_capture(root,nonce,texts=texts)

    def test_wrong_door_or_party_is_not_waived(self):
        for key,value in [('door_flags',1635),('door_open',True),('party_count',3),('has_key',True)]:
            with tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);nonce,texts,_=self.fixture(root);scene=json.loads((root/'final.scene.json').read_text());scene[key]=value
                self.write(root,'final.scene.json',scene)
                with self.assertRaises(ValueError):journey.validate_capture(root,nonce,texts=texts)

    def test_idle_claim_requires_empty_current_and_pending_actions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);nonce,texts,_=self.fixture(root);scene=json.loads((root/'startup-3.scene.json').read_text())
            scene['party_actions'][0]['next_action_id']=60;self.write(root,'startup-3.scene.json',scene)
            with self.assertRaisesRegex(ValueError,'readiness'):journey.validate_capture(root,nonce,texts=texts)

    def test_capture_cannot_invent_expected_npc_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);nonce,texts,_=self.fixture(root)
            self.write(root,'branch-0.text.json',dict(expected_npc_strref=899,expected_npc_text='invented',message_text='invented'))
            with self.assertRaisesRegex(ValueError,'strref'):journey.validate_capture(root,nonce,texts=texts)

    def test_old_transcript_text_cannot_satisfy_fresh_branch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);nonce,texts,_=self.fixture(root)
            self.write(root,'talk-request.message.json',dict(observed_text=texts[899]))
            text=json.loads((root/'branch-0.text.json').read_text());text.update(previous_text=texts[899],npc_occurrences_before=1,npc_occurrences_after=1)
            self.write(root,'branch-0.text.json',text)
            with self.assertRaisesRegex(ValueError,'Stale transcript'):journey.validate_capture(root,nonce,texts=texts)


if __name__=='__main__':unittest.main()
