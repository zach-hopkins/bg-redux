"""Focused synthetic negatives; never launches a game or prepares real fixtures."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
from unittest.mock import patch
import unittest
sys.path.insert(0,str(Path(__file__).parents[1]))
import cell_recruitment_journey as j
from test_weapon_query_validation import setup_case
from test_saved_npc_color_fixtures import cre as base_cre, record


def item(ref,slot=0,flags=1):return dict(resref=ref,slot=slot,flags=flags,expired=0,usages=[0,0,0])

def checkpoint(joined=False,taken=False):
    _,_,s,_=setup_case();s['game_time']=100;s['journal_count']=3
    s['journal']=[dict(text_ref=34089,time=1,chapter=1,section=4,group=255),dict(text_ref=96383,time=1,chapter=1,section=1,group=255),dict(text_ref=47519 if joined else 34105,time=2,chapter=1,section=2 if joined else 1,group=0)]
    s['globals']={'BD_DEFAI':1,'JAHEIRARELEASED':int(joined)}
    for a in s['party']:a['inventory']=dict(fist_slot=10,slot_count=39,items=[]);a['in_party']=1 if a['runtime_id']==10002 else 2
    target=copy.deepcopy(s['party'][1]);target.update(script_name='Jaheira',runtime_id=10004,in_party=3 if joined else 0)
    if taken and not joined:s['party'][0]['inventory']['items']=[item('MISC4B',15,17)]
    if joined:s['party'].append(target)
    s['stored_npcs']=[] if joined else [target];s['current_area_actors']=s['party']+([] if joined else [target])
    table=[item(r,i) for i,r in enumerate(j.TABLE_ITEMS) if not (joined or taken) or r!='MISC4B']
    actions=[dict(id=a['runtime_id'],position=a['position'],current=None,next=None,moving=False) for a in s['party']]
    scene=dict(schema='bg-redux-recruitment-scene/1',game_time=100,leader_id=10002,target_id=10004,target_name='Jaheira',target_in_party=3 if joined else 0,target_dialog='JAHEIRAJ' if joined else 'JAHEIRA',talk_count=2 if joined else 1,target_current=None,target_next=None,target_moving=False,party_count=3 if joined else 2,party_keys=int(taken and not joined),table_keys=int(not joined and not taken),table_id=20000,table_inventory=dict(items=table),door_id=20001,door_name='Cell01',door_key='MISC4B',door_flags=1633 if joined else 1634,door_open=joined,door_locked=not joined,released=int(joined),jerk=0,hunt=0,bd_defai=1,leader_class_script='BDDEFAI',selected_id=10002,selected_count=1,current_container=None,in_dialog=False,speaker=None,dialogue_target=None,party_actions=actions)
    return s,scene


def fixture(folder,joined):
    n=3 if joined else 2;gn=3;gam=bytearray(0xb4+gn*0x160);gam[:8]=b'GAMEV2.0';struct.pack_into('<II',gam,0x20,0xb4,n);struct.pack_into('<II',gam,0x30,0 if joined else 0xb4+2*0x160,0 if joined else 1)
    for index,name in enumerate(('None','Imoen','Jaheira')):
        cre=bytearray(base_cre());cre[0x280:0x2a0]=name.encode().ljust(32,b'\0')
        cre[0x2cc:0x2d4]=(b'JAHEIRAJ' if joined else b'JAHEIRA\0') if index==2 else bytes(8)
        row=0xb4+index*0x160;struct.pack_into('<II',gam,row+4,len(gam),len(cre));struct.pack_into('<I',gam,row+0xe0,2 if joined else 1);gam.extend(cre)
    off=len(gam);gam.extend(bytes(84));gam[off:off+16]=b'JAHEIRARELEASED\0';struct.pack_into('<I',gam,off+40,int(joined));struct.pack_into('<II',gam,0x38,off,1)
    off=len(gam)
    for ref,section in [(34089,4),(96383,1),(47519 if joined else 34105,2 if joined else 1)]:gam.extend(struct.pack('<IIBBBB',ref,1,1,0,section,0))
    struct.pack_into('<I',gam,0x50,off);struct.pack_into('<I',gam,0x4c,3)
    area=bytearray(0x11c+200+192);area[:8]=b'AREAV1.0';door=0x11c;container=door+200;items=len(area)
    struct.pack_into('<II',area,0xa4,1,door);area[door:door+6]=b'Cell01';area[door+120:door+128]=b'MISC4B\0\0';struct.pack_into('<I',area,door+40,1633 if joined else 1634);struct.pack_into('<I',area,door+140,100)
    refs=[r for r in j.TABLE_ITEMS if not joined or r!='MISC4B'];struct.pack_into('<IHHI',area,0x70,container,1,len(refs),items);area[container:container+14]=b'Jailkeep Table';struct.pack_into('<II',area,container+64,0,len(refs))
    for ref in refs:area.extend(ref.encode().ljust(8,b'\0')+struct.pack('<4HI',0,0,0,0,1))
    (folder/'baldur.gam').write_bytes(gam);(folder/'baldur.sav').write_bytes(b'SAV V1.0'+record('AR0602.ARE',bytes(area)));(folder/'baldur.bmp').write_bytes(b'BM')
    for i in range(n):(folder/('PORTRT%d.bmp'%i)).write_bytes(b'BM')


class RecruitmentOutcomeTests(unittest.TestCase):
    def test_exact_key_transfer_and_recruited_checkpoint(self):
        before,bs=checkpoint();after,as_=checkpoint(taken=True);j.transfer(before,after,bs,as_)
        j.scene_guard(bs,before,False);j.scene_guard(*reversed(checkpoint(True)),True)
    def test_key_loss_duplicate_other_charge_or_wrong_destination_rejected(self):
        for change in ('loss','duplicate','wrongpc','charges','otherloss'):
            before,bs=checkpoint();after,as_=checkpoint(taken=True)
            if change=='loss':after['party'][0]['inventory']['items']=[]
            elif change=='duplicate':after['party'][0]['inventory']['items'].append(item('MISC4B',16))
            elif change=='wrongpc':after['party'][1]['inventory']['items']=after['party'][0]['inventory']['items'];after['party'][0]['inventory']['items']=[]
            elif change=='charges':after['party'][0]['inventory']['items'][0]['usages'][0]=1
            else:as_['table_inventory']['items'].pop()
            with self.subTest(change=change),self.assertRaises(ValueError):j.transfer(before,after,bs,as_)
    def test_fabricated_join_counter_door_quest_or_duplicate_actor_rejected(self):
        for change in ('counter','door','global','duplicate','membership','dialog','journal'):
            s,c=checkpoint(True)
            if change=='counter':c['talk_count']=1
            elif change=='door':c['door_flags']=1634
            elif change=='global':s['globals']['JAHEIRARELEASED']=0
            elif change=='duplicate':s['current_area_actors'].append(copy.deepcopy(s['party'][2]))
            elif change=='membership':s['stored_npcs']=[s['party'][2]]
            elif change=='dialog':c['target_dialog']='JAHEIRA'
            else:s['journal'][-1]['section']=1
            with self.subTest(change=change),self.assertRaises(ValueError):j.scene_guard(c,s,True)
    def test_idle_requires_actual_queues_movement_selection_and_closed_container(self):
        for change in ('current','next','move','selection','container','targetnext','dialog'):
            _,c=checkpoint()
            if change in ('current','next'):c['party_actions'][0][change]=dict(id=1,int0=0,resref='')
            elif change=='move':c['party_actions'][0]['moving']=True
            elif change=='selection':c['selected_count']=2
            elif change=='container':c['current_container']=20000
            elif change=='targetnext':c['target_next']=dict(id=1,int0=0,resref='')
            else:c['in_dialog']=True
            with self.subTest(change=change):self.assertFalse(j.natural(c))
    def test_journal_duplicate_and_wrong_solved_chapter_rejected(self):
        s,_=checkpoint(True);j.quest_guard(s['journal'],True)
        s['journal'].append(copy.deepcopy(s['journal'][-1]))
        with self.assertRaises(ValueError):j.quest_guard(s['journal'],True)
        s,_=checkpoint(True);s['journal'][-1]['chapter']=2
        with self.assertRaises(ValueError):j.quest_guard(s['journal'],True)


class RecruitmentWireTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.folder=Path(self.tmp.name)
    def test_exact_two_and_three_party_manifests_and_wire_membership(self):
        fixture(self.folder,False);self.assertEqual(len(j.save_manifest(self.folder,2)),5);self.assertEqual(j.wire(self.folder,False)['target']['group'],'npcs')
        fixture(self.folder,True);self.assertEqual(len(j.save_manifest(self.folder,3)),6);self.assertEqual(j.wire(self.folder,True)['target']['index'],2)
    def test_missing_third_portrait_extra_file_wrong_party_and_truncation_rejected(self):
        fixture(self.folder,True);(self.folder/'PORTRT2.bmp').unlink()
        with self.assertRaises(ValueError):j.save_manifest(self.folder,3)
        fixture(self.folder,True);(self.folder/'unexpected.bin').write_bytes(b'x')
        with self.assertRaises(ValueError):j.save_manifest(self.folder,3)
        with self.assertRaises(ValueError):j.wire(self.folder,False)
        p=self.folder/'baldur.gam';p.write_bytes(p.read_bytes()[:-1])
        with self.assertRaises(ValueError):j.wire(self.folder,True)
    def test_declared_binary_section_alias_rejected(self):
        j.disjoint([(0,10),(10,20),(0,0)])
        with self.assertRaises(ValueError):j.disjoint([(0,10),(9,20)])
    def test_wrong_saved_lock_or_key_field_rejected(self):
        fixture(self.folder,True);p=self.folder/'baldur.sav';records=j.binary.sav_records(p.read_bytes());area=bytearray(j.binary.inflate(records[0]));struct.pack_into('<I',area,0x11c+40,1634);p.write_bytes(b'SAV V1.0'+record('AR0602.ARE',bytes(area)))
        with self.assertRaises(ValueError):j.wire(self.folder,True)


class RecruitmentProvenanceTests(unittest.TestCase):
    def test_parent_wrong_hash_rejected_before_artifact_use(self):
        with patch.object(j.evidence,'sha',return_value='wrong'),self.assertRaises(ValueError):j.parent_proof(Path('unused'))
    def test_frozen_dialogue_helper_derivation_rejects_drift(self):
        raw=(j.HERE/'native/recruitment_dialogue_snapshot.cpp').read_bytes();self.assertIn(b'int FrozenUnexecutedRecruitmentDialogueMain(',j.dialogue_helpers(raw))
        with self.assertRaises(ValueError):j.dialogue_helpers(raw+b'\n')
    def test_source_and_frozen_copy_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'tool.py';f=root/'frozen.py';p.write_bytes(b'code');f.write_bytes(b'code');receipt=dict(sources={str(p):dict(sha256=j.evidence.sha(p),frozen=str(f))})
            with patch.object(j,'sources',return_value=[p]):
                j.source_guard(receipt,root,root);f.write_bytes(b'drift')
                with self.assertRaises(ValueError):j.source_guard(receipt,root,root)
    def test_duplicate_commands_or_forced_native_claim_fail_early(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=dict(schema='bg-redux-recruitment-native/1',nonce='a'*32,journey='recruit',completed=True,error='',os_pointer_input=False,forced_outcomes=False,container_commands=1,takes=1,closes=1,door_commands=1,talk_requests=0,auto_dialogues=1,branches=2)
            for field,value in [('door_commands',2),('takes',0),('talk_requests',1),('auto_dialogues',0),('forced_outcomes',True),('nonce','b'*32)]:
                row=base|{field:value};(root/'recruitment-result.json').write_text(json.dumps(row),encoding='utf-8')
                with self.subTest(field=field),self.assertRaises(ValueError):j.validate_capture(root,'a'*32,False,None,{}, {})
    def test_runtime_provider_path_and_bytes_cannot_be_substituted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);rows={};receipt=dict(resources={})
            for name in j.RESOURCE_TYPES:
                original=root/(name+'.original');original.write_bytes(b'original');(root/(name+'.runtime')).write_bytes(b'original');rows[name]=dict(originalfile=str(original),bytes=8);receipt['resources'][name]=dict(provider=str(original),bytes=8,sha256=j.evidence.sha(original))
            report=root/'recruitment-providers.json';report.write_text(json.dumps(dict(schema='bg-redux-recruitment-providers/1',resources=rows)),encoding='utf-8');j.check_runtime_resources(root,receipt)
            (root/'misc4b.runtime').write_bytes(b'tampered')
            with self.assertRaises(ValueError):j.check_runtime_resources(root,receipt)
            (root/'misc4b.runtime').write_bytes(b'original');rows['misc4b']['originalfile']=str(root/'same-bytes-unapproved-path');report.write_text(json.dumps(dict(schema='bg-redux-recruitment-providers/1',resources=rows)),encoding='utf-8')
            with self.assertRaises(ValueError):j.check_runtime_resources(root,receipt)

class RecruitmentAutoRouteTests(unittest.TestCase):
    def test_intermediate_released_flag_is_not_join_success(self):
        s,c=checkpoint();s['globals']['JAHEIRARELEASED']=1;c['released']=1
        j.scene_guard(c,s)
        with self.assertRaises(ValueError):j.scene_guard(c,s,True)
    def test_exact_ids_bindings_reject_missing_wrong_and_conflicting_values(self):
        j.require_id(b'198 StartDialogueNoSet(O:Object*)\n','StartDialogueNoSet',198)
        for raw in (b'199 StartDialogueNoSet(O:Object*)\n',b'198 Other()\n',b'198 StartDialogueNoSet(O:Object*)\n199 StartDialogueNoSet(O:Object*)\n'):
            with self.assertRaises(ValueError):j.require_id(raw,'StartDialogueNoSet',198)
    def test_stale_native_prefix_rejected_before_ingestion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);row=dict(schema='bg-redux-recruitment-native/1',nonce='a'*32,journey='recruit',completed=True,error='',os_pointer_input=False,forced_outcomes=False,container_commands=1,takes=1,closes=1,door_commands=1,talk_requests=0,auto_dialogues=1,branches=2)
            p=root/'recruitment-result.json';p.write_text(json.dumps(row),encoding='utf-8');os.utime(p,ns=(1,1))
            with self.assertRaisesRegex(ValueError,'Stale'):j.validate_capture(root,'a'*32,False,2,{}, {})

if __name__=='__main__':unittest.main()
