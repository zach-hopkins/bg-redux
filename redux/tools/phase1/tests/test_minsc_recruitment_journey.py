"""Synthetic evidence/parser negatives only. No native processes or real fixtures."""
import copy
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib
sys.path.insert(0,str(Path(__file__).parents[1]))
import minsc_recruitment_journey as j


def actor(name,identity,party=0):
    return dict(script_name=name,name=name,runtime_id=identity,in_party=party,area='AR0602',position=[3816,2706],base_stats=[0]*256,modified_stats=[0]*256,inventory=dict(fist_slot=10,items=[]),effects=[],spellbook=[],locals={})

def checkpoint(joined=False):
    people=[actor(n,10002+i,i+1 if i<3 or joined else 0)for i,n in enumerate(('None','Imoen','Jaheira','Minsc'))]
    for a,xp in zip(people,(90500,96500,90000,90000)):a['base_stats'][44]=xp+(1000 if joined and a is not people[3]else 0)
    people[3]['position']=[4029,2759];people[3]['inventory']['items']=[dict(resref='MISC84',slot=15,expired=0,usages=[0,0,0],flags=1)]
    journal=[dict(text_ref=r,time=1,chapter=1,section=s,group=0)for r,s in ((34089,4),(96383,1),(47519,2))]
    if joined:journal.append(dict(text_ref=47518,time=2,chapter=1,section=2,group=0))
    state=dict(schema='bg-redux-state/1',game_time=100,current_area='AR0602',selection=1,globals={'JAHEIRARELEASED':1},area_locals={},party=people if joined else people[:3],stored_npcs=[]if joined else[people[3]],current_area_actors=people,journal=journal)
    scene=dict(schema='bg-redux-minsc-scene/1',game_time=100,leader_id=10002,target_id=10005,imoen_id=10003,target_name='Minsc',target_position=[4029,2759],target_dialog='MINSCJ'if joined else'MINSCA',target_in_party=4 if joined else 0,talk_count=2 if joined else 0,target_current=None,target_next=None,target_moving=False,party_count=4 if joined else 3,door_id=20000,door_name='Cell02',door_key='',door_flags=609 if joined else 610,door_open=joined,door_locked=not joined,cell01_flags=1633,released=1,bd_defai=1,leader_class_script='BDDEFAI',selected_id=10002,selected_count=1,current_container=None,in_dialog=False,speaker=None,dialogue_target=None,party_actions=[dict(id=a['runtime_id'],position=a['position'],current=None,next=None,moving=False)for a in state['party']])
    return state,scene

def branch(index=0,eligible=True):
    state,scene=checkpoint();dlg,source,ref,local,transition,response=j.BRANCHES[index]
    if index in (3,17)and not eligible:local,transition=0,39 if index==3 else 49
    texts={r:'text%d'%r for r in {x[2]for x in j.BRANCHES}|{v for refs in j.PREFIX_REFS.values()for v in refs}|{27484,27485,27486,27487}}
    choices=[dict(visible_index=i,value=i,strref=r,text=texts[r])for i,r in enumerate(j.PREFIX_REFS.get(index,[]))]
    message=texts[ref]+''.join('%d. - %s'%(c['visible_index']+1,c['text'])for c in choices)
    row=dict(index=index,dialog=dlg,state=source,npc_strref=ref,npc_text=texts[ref],previous_text='',message_text=message,choices=choices,imoen_eligible=eligible,local=local,transition=transition)
    event=dict(index=index,dialog=dlg,state=source,npc_strref=ref,local=local,transition=transition,imoen_eligible=eligible,entry='TextArea::SelectAvailableOption'if response is not None else'Control::PerformAction')
    scene.update(in_dialog=True,speaker=10002,dialogue_target=10003 if dlg=='IMOENJ'else 10005,talk_count=2 if index>=11 else 1)
    return row,event,scene,state,texts

def operation():
    events=[dict(kind=k,details={})for k in ('registered-button','ordinary-approach-command','stock-auto-dialogue-observed')]
    for i in range(21):
        if i==11:events.append(dict(kind='stock-restarted-dialogue-observed',details={}))
        events.append(dict(kind='registered-branch',details={'index':i}))
    events.extend(dict(kind=k,details={})for k in ('registered-button','registered-button','registered-save-name','registered-button'))
    return dict(movement_commands=1,talk_requests=0,door_commands=0,restart_requests=0,auto_dialogues=2,branches=21,events=events,saves=['private/save'])

def fixture(folder,joined):
    n=4 if joined else 3;gam=bytearray(0xb4+4*0x160);gam[:8]=b'GAMEV2.0';struct.pack_into('<II',gam,0x20,0xb4,n);struct.pack_into('<II',gam,0x30,0 if joined else 0xb4+3*0x160,0 if joined else 1)
    for i,name in enumerate(('None','Imoen','Jaheira','Minsc')):
        cre=bytearray(0x2d4+80+(20 if i==3 else 0));cre[:8]=b'CRE V1.0';cre[0x33]=1;cre[0x280:0x2a0]=name.encode().ljust(32,b'\0');struct.pack_into('<I',cre,0x2b8,0x2d4);struct.pack_into('<38HhH',cre,0x2d4,*([0xffff]*38),1000,0)
        dialog=b'JAHEIRAJ'if i==2 else(b'MINSCJ'if joined else b'MINSCA')if i==3 else b'';cre[0x2cc:0x2d4]=dialog.ljust(8,b'\0')
        if i==3:
            struct.pack_into('<II',cre,0x2bc,0x2d4+80,1);cre[-20:]=b'MISC84\0\0'+struct.pack('<4HI',0,0,0,0,1)
        row=0xb4+i*0x160;struct.pack_into('<II',gam,row+4,len(gam),len(cre));struct.pack_into('<I',gam,row+0xe0,2 if i==2 or i==3 and joined else 0);gam.extend(cre)
    offset=len(gam);gam.extend(bytes(84));gam[offset:offset+32]=b'JAHEIRARELEASED'.ljust(32,b'\0');struct.pack_into('<I',gam,offset+40,1);struct.pack_into('<II',gam,0x38,offset,1)
    offset=len(gam);refs=[(34089,4),(96383,1),(47519,2)]+([(47518,2)]if joined else[])
    for ref,section in refs:gam.extend(struct.pack('<IIBBBB',ref,1,1,0,section,0))
    struct.pack_into('<I',gam,0x50,offset);struct.pack_into('<I',gam,0x4c,len(refs))
    area=bytearray(0x11c+400+192);area[:8]=b'AREAV1.0';struct.pack_into('<II',area,0xa4,2,0x11c)
    for i,(name,flags,key)in enumerate((('Cell01',1633,'MISC4B'),('Cell02',609 if joined else 610,''))):
        at=0x11c+200*i;area[at:at+32]=name.encode().ljust(32,b'\0');struct.pack_into('<I',area,at+40,flags);area[at+120:at+128]=key.encode().ljust(8,b'\0');struct.pack_into('<I',area,at+140,100)
    container=0x11c+400;items=len(area);table=[r for r in j.TABLE_ITEMS if r!='MISC4B'];struct.pack_into('<IHHI',area,0x70,container,1,len(table),items);area[container:container+32]=b'Jailkeep Table'.ljust(32,b'\0');struct.pack_into('<II',area,container+64,0,len(table))
    for ref in table:area.extend(ref.encode().ljust(8,b'\0')+struct.pack('<4HI',0,0,0,0,1))
    packed=zlib.compress(area);name=b'AR0602.ARE\0';(folder/'baldur.gam').write_bytes(gam);(folder/'baldur.sav').write_bytes(b'SAV V1.0'+struct.pack('<I',len(name))+name+struct.pack('<II',len(area),len(packed))+packed);(folder/'baldur.bmp').write_bytes(b'BM')
    for i in range(n):(folder/('PORTRT%d.bmp'%i)).write_bytes(b'BM')

class MinscEvidenceTests(unittest.TestCase):
    def test_actual_three_and_four_party_synthetic_checkpoints(self):
        for joined in (False,True):
            state,scene=checkpoint(joined);j.scene_guard(scene,state,joined)
    def test_duplicate_stored_membership_boo_and_prior_door_fail(self):
        for kind in ('duplicate','stored','boo','wrong-owner','door','priorquest','counter','dialog'):
            state,scene=checkpoint(True)
            if kind=='duplicate':state['current_area_actors'].append(copy.deepcopy(state['party'][-1]))
            elif kind=='stored':state['stored_npcs']=[state['party'][-1]]
            elif kind=='boo':state['party'][-1]['inventory']['items']=[]
            elif kind=='wrong-owner':state['party'][0]['inventory']['items']=copy.deepcopy(state['party'][-1]['inventory']['items'])
            elif kind=='door':scene['cell01_flags']=1634
            elif kind=='priorquest':state['journal'][2]['section']=1
            elif kind=='counter':scene['talk_count']=1
            else:scene['target_dialog']='MINSCA'
            with self.subTest(kind=kind),self.assertRaises(ValueError):j.scene_guard(scene,state,True)
    def test_branch_normal_prefix_and_both_observed_conditional_paths(self):
        for index,eligible in ((0,True),(3,True),(3,False),(17,True),(17,False),(4,True),(18,True)):
            row,event,scene,state,texts=branch(index,eligible);j.branch_guard(row,event,scene,state,index,texts,'')
    def test_branch_wrong_participant_hidden_prefix_stale_text_and_entry_fail(self):
        for kind in ('speaker','target','stale','prefix','local','entry','condition'):
            row,event,scene,state,texts=branch(1)
            if kind=='speaker':scene['speaker']=10003
            elif kind=='target':scene['dialogue_target']=10003
            elif kind=='stale':row['previous_text']=row['message_text']
            elif kind=='prefix':row['message_text']=row['message_text'].replace('1. - ','hidden ')
            elif kind=='local':event['local']=0
            elif kind=='entry':event['entry']='TextArea::UpdateState'
            else:event['imoen_eligible']=False
            with self.subTest(kind=kind),self.assertRaises(ValueError):j.branch_guard(row,event,scene,state,1,texts,'')
    def test_imoen_interjection_requires_imoen_actual_target(self):
        row,event,scene,state,texts=branch(4);scene['dialogue_target']=scene['target_id']
        with self.assertRaises(ValueError):j.branch_guard(row,event,scene,state,4,texts,'')
    def test_protagonist_gender_expansion_has_exact_table_refs(self):
        state,_=checkpoint();texts={25102:'<PRO_HESHE> <PRO_HISHER>',27484:'he',27485:'she',27486:'his',27487:'her'}
        self.assertEqual(j.expanded_text(texts,25102,state),'he his');state['party'][0]['modified_stats'][35]=2;self.assertEqual(j.expanded_text(texts,25102,state),'she her')
    def test_one_move_zero_host_dialogue_and_exact_restart_inventory(self):j.operation_guard(operation(),False)
    def test_duplicate_move_manual_talk_door_restart_and_extra_event_fail(self):
        for kind in ('movement_commands','talk_requests','door_commands','restart_requests','auto_dialogues','extra'):
            native=operation()
            if kind=='extra':native['events'].insert(2,dict(kind='force-join',details={}))
            else:native[kind]+=1
            with self.subTest(kind=kind),self.assertRaises(ValueError):j.operation_guard(native,False)
    def test_reload_permits_load_only(self):
        n=dict(movement_commands=0,talk_requests=0,door_commands=0,restart_requests=0,auto_dialogues=0,branches=0,events=[dict(kind='registered-button')],saves=[]);j.operation_guard(n,True)
        n['saves']=['unexpected']
        with self.assertRaises(ValueError):j.operation_guard(n,True)
    def test_measured_xp_before_join_and_inventory_conservation(self):
        before,_=checkpoint();middle=copy.deepcopy(before);after,_=checkpoint(True);j.outcome_guard(before,middle,after)
        for kind in ('per-new-member','early-reward','old-inventory','boo-loss','priorjournal'):
            middle=copy.deepcopy(before);after,_=checkpoint(True)
            if kind=='per-new-member':after['party'][-1]['base_stats'][44]+=3000
            elif kind=='early-reward':middle['party'][0]['base_stats'][44]+=1000
            elif kind=='old-inventory':after['party'][0]['inventory']['items']=[dict(resref='GIFT',slot=15,flags=1,usages=[0,0,0])]
            elif kind=='boo-loss':after['party'][-1]['inventory']['items']=[]
            else:after['journal'][0]['time']=2
            with self.subTest(kind=kind),self.assertRaises(ValueError):j.outcome_guard(before,middle,after)
    def test_readiness_rejects_action_move_selection_and_container(self):
        for kind in ('current','moving','selected','container'):
            _,scene=checkpoint()
            if kind=='current':scene['party_actions'][0]['current']={'id':23}
            elif kind=='moving':scene['target_moving']=True
            elif kind=='selected':scene['selected_count']=2
            else:scene['current_container']=2000
            self.assertFalse(j.natural(scene))
    def test_wire_exact_three_and_four_party_manifest(self):
        for joined in (False,True):
            with tempfile.TemporaryDirectory()as temp:
                p=Path(temp);fixture(p,joined);parsed=j.wire(p,joined);self.assertEqual(parsed['party_count'],4 if joined else 3);j.save_manifest(p,4 if joined else 3)
    def test_fourth_portrait_missing_extra_file_and_wrong_party_fail(self):
        with tempfile.TemporaryDirectory()as temp:
            p=Path(temp);fixture(p,True);(p/'PORTRT3.bmp').unlink()
            with self.assertRaises(ValueError):j.save_manifest(p,4)
            (p/'PORTRT3.bmp').write_bytes(b'BM');(p/'undeclared').write_bytes(b'x')
            with self.assertRaises(ValueError):j.save_manifest(p,4)
            with self.assertRaises(ValueError):j.wire(p,False)
    def test_wire_overlapping_embedded_actor_rejected(self):
        with tempfile.TemporaryDirectory()as temp:
            p=Path(temp);fixture(p,True);g=bytearray((p/'baldur.gam').read_bytes());struct.pack_into('<II',g,0xb4+0x160+4,*struct.unpack_from('<II',g,0xb4+4));(p/'baldur.gam').write_bytes(g)
            with self.assertRaises(ValueError):j.wire(p,True)
    def test_wire_truncated_sav_and_lost_boo_fail(self):
        with tempfile.TemporaryDirectory()as temp:
            p=Path(temp);fixture(p,True);g=bytearray((p/'baldur.gam').read_bytes());g[g.index(b'MISC84'):g.index(b'MISC84')+6]=b'NOTBOO';(p/'baldur.gam').write_bytes(g)
            with self.assertRaises(ValueError):j.wire(p,True)
            fixture(p,True);(p/'baldur.sav').write_bytes((p/'baldur.sav').read_bytes()[:-1])
            with self.assertRaises(ValueError):j.wire(p,True)
    def test_dialogue_parser_rejects_escape_and_excess_counts(self):
        raw=bytearray(0x34+16+32);raw[:8]=b'DLG V1.0';struct.pack_into('<4I',raw,8,1,0x34,1,0x44);struct.pack_into('<3I',raw,0x34,2306,0,1);self.assertEqual(j.parse_dialogue(raw)[0][0],2306)
        struct.pack_into('<I',raw,0x34+4,1)
        with self.assertRaises(ValueError):j.parse_dialogue(raw)
        struct.pack_into('<I',raw,8,10001)
        with self.assertRaises(ValueError):j.parse_dialogue(raw)
    def test_mapping_rejects_hidden_source_prefix(self):
        rows={'minsca':[(0,0,[])for _ in range(44)],'imoenj':[(0,0,[])for _ in range(9)]}
        for i,(dlg,state,ref,local,transition,response)in enumerate(j.BRANCHES):
            prefix=[(1,r)for r in j.PREFIX_REFS.get(i,[])]or[(2,0),(2,0)]if i in (3,17)else[(0,0)]
            if response is not None:prefix=[(1,r)for r in j.PREFIX_REFS[i]]
            rows[dlg.lower()][state]=(ref,transition-local,prefix)
        with patch.object(j,'parse_dialogue',side_effect=lambda raw:rows[raw]):
            j.mapping_guard({'minsca':{'raw':'minsca'},'imoenj':{'raw':'imoenj'}})
            ref,first,choices=rows['minsca'][1];choices[0]=(3,choices[0][1])
            with self.assertRaises(ValueError):j.mapping_guard({'minsca':{'raw':'minsca'},'imoenj':{'raw':'imoenj'}})
    def test_exact_snapshot_helper_derivation_rejects_wrong_bytes(self):
        with self.assertRaises(ValueError):j.dialogue_helpers(b'int main(){return 0;}')

    def test_missing_wrong_nonce_forced_or_stale_capture_is_never_success(self):
        import json,time
        with tempfile.TemporaryDirectory()as temp:
            folder=Path(temp);native=operation();native.update(schema='bg-redux-minsc-native/1',nonce='a'*32,journey='recruit',completed=True,error='',os_pointer_input=False,forced_outcomes=False)
            for field,value in [('nonce','b'*32),('completed',False),('forced_outcomes',True)]:
                bad=copy.deepcopy(native);bad[field]=value;(folder/'minsc-result.json').write_text(json.dumps(bad),encoding='utf8')
                with self.subTest(field=field),self.assertRaises(ValueError):j.validate_capture(folder,'a'*32,False,None,{}, {})
            (folder/'minsc-result.json').write_text(json.dumps(native),encoding='utf8')
            with self.assertRaises(ValueError):j.validate_capture(folder,'a'*32,False,time.time_ns()+1000000000,{}, {})
    def test_frozen_source_current_or_frozen_tamper_rejected(self):
        with tempfile.TemporaryDirectory()as temp:
            folder=Path(temp);source=folder/'source';frozen=folder/'frozen';source.write_bytes(b'original');frozen.write_bytes(b'original');binding=folder/'build-receipt.json';binding.write_bytes(b'{}');receipt=dict(build=str(folder),sources={str(source):dict(frozen=str(frozen),sha256=j.evidence.sha(source)),str(binding):dict(frozen=str(binding),sha256=j.evidence.sha(binding))})
            with patch.object(j,'sources',return_value=[source]),patch.object(j,'check_engine_receipt',return_value={'build_support_files':{}}):
                j.source_guard(receipt,folder,folder)
                frozen.write_bytes(b'altered')
                with self.assertRaises(ValueError):j.source_guard(receipt,folder,folder)
                frozen.write_bytes(b'original');source.write_bytes(b'altered')
                with self.assertRaises(ValueError):j.source_guard(receipt,folder,folder)

    def test_actual_approach_range_and_command_evidence_required(self):
        before,bs=checkpoint();after,as_=checkpoint();after['game_time']=101;after['party'][0]['position']=[3909,2753]
        states={name:copy.deepcopy(before)for name in ('loaded','ready','before-move')};states['auto-dialogue']=after
        scenes={'before-move':bs,'auto-dialogue':as_,'after-move-command':copy.deepcopy(bs),'sample':as_};scenes['after-move-command']['party_actions'][0]['current']=dict(id=23,point=[3909,2753],int0=0,resref='')
        samples=[dict(checkpoint='sample',phase=1)];event=dict(kind='ordinary-approach-command',details=dict(action_id=23,point=[3909,2753],actor_id=10002));j.movement_guard(states,scenes,samples,[event],23)
        for kind in ('wrongpoint','duplicate','unreachable','no-queue'):
            ss=copy.deepcopy(states);cc=copy.deepcopy(scenes);events=[copy.deepcopy(event)]
            if kind=='wrongpoint':events[0]['details']['point']=[1,2]
            elif kind=='duplicate':events.append(copy.deepcopy(event))
            elif kind=='unreachable':ss['auto-dialogue']['party'][0]['position']=[3800,2700]
            else:cc['after-move-command']['party_actions'][0]['current']=None
            with self.subTest(kind=kind),self.assertRaises(ValueError):j.movement_guard(ss,cc,samples,events,23)

    def test_full_engine_receipt_rejects_stale_source_binary_and_support(self):
        import json
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);source=root/'source';build=root/'build';source.mkdir();build.mkdir();support={}
            for name in ('redux/tools/phase1/cmake/managed-tests.cmake','redux/tools/phase0/managed-test-main.cpp'):
                actual=source/name;frozen=build/'build-support'/name;actual.parent.mkdir(parents=True,exist_ok=True);frozen.parent.mkdir(parents=True,exist_ok=True);actual.write_bytes(b'support');frozen.write_bytes(b'support');support[name]=j.evidence.sha(actual)
            receipt=dict(schema='bg-redux-phase1-build/1',status='built-not-validated',source=str(source),directory=str(build),source_unchanged_during_build=True,build_support_unchanged=True,phase0_preservation=dict(source=True,binaries=True,fixture=True),source_files={'engine.cpp':'sourcehash'},binaries={'gemrb/libgemrb_core.dll':'dllhash','gemrb/core/libgemrb_core.dll.a':'linkhash'},build_support_files=support)
            (build/'build-receipt.json').write_text(json.dumps(receipt),encoding='utf8')
            with patch.object(j,'engine_source_inventory',return_value=receipt['source_files']),patch.object(j,'engine_binary_inventory',return_value=receipt['binaries']):
                j.check_engine_receipt(source,build)
                with patch.object(j,'engine_source_inventory',return_value={'engine.cpp':'stale'}),self.assertRaises(ValueError):j.check_engine_receipt(source,build)
                with patch.object(j,'engine_binary_inventory',return_value={'gemrb/libgemrb_core.dll':'stale'}),self.assertRaises(ValueError):j.check_engine_receipt(source,build)
                (build/'build-support'/next(iter(support))).write_bytes(b'changed')
                with self.assertRaises(ValueError):j.check_engine_receipt(source,build)

if __name__=='__main__':unittest.main()
