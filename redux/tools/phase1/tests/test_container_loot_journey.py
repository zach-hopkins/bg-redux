"""Synthetic evidence and parser mutations; never creates or launches a game."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).parents[1]))
import container_loot_journey as journey
from test_weapon_query_validation import setup_case

def item(ref,slot=0,flags=0):return dict(resref=ref,slot=slot,flags=flags,expired=0,usages=[0,0,0])
def inv(items):return dict(items=items,fist_slot=10,slot_count=39,equipped=1000,equipped_header=0)
def focused(reload=False):
    before=dict(schema='bg-redux-container-loot-state/1',container='Jailkeep Table',container_script_name='jailkeeptable',container_runtime_id=999,position=[3109,2829],type=5,flags=0,trapped=0,pc_runtime_id=10002,pc_position=[3741,2801],game_time=100,
                container_inventory=inv([item('SW1H04'),item('STAF01',1)]),pc_inventory=inv([item('FIST',10)]))
    after=copy.deepcopy(before);after['container_inventory']['items']=[item('STAF01')];after['pc_inventory']['items'].append(item('SW1H04',15,0x10));after['pc_position']=[3150,2840];after['game_time']=108
    return (copy.deepcopy(after),after) if reload else (before,after)

def write(folder,records):
    for name,value in records.items():(folder/name).write_text(json.dumps(value),encoding='utf-8')

def capture(folder,reload=False):
    first,last=focused(reload);_,_,state,_=setup_case();before=copy.deepcopy(state);after=copy.deepcopy(state)
    first['game_time']=100;last['game_time']=108
    for s,f,t in [(before,first,100),(after,last,108)]:
        s['game_time']=t;s['party'][0]['runtime_id']=10002;s['party'][0]['inventory']=f['pc_inventory'];s['party'][0]['position']=f['pc_position']
    samples=[dict(sample=i,phase='paused-initial' if i<5 else 'running' if i<13 else 'paused-final',elapsed_ms=i*250,game_time=100 if i<5 else min(108,96+i)) for i in range(17)]
    for sample in samples:sample['action_trace']=[dict(runtime_id=10002,action_id=172 if sample['sample']<9 else None,position=first['pc_position'] if sample['sample']<5 else last['pc_position'])]
    records={'clock-before.state.json':before,'clock-after.state.json':after,'clock-samples.json':dict(schema='bg-redux-live-clock/1',ticks_per_second=15,samples=samples),
      'gui-result.json':dict(completed=True,steps=17,events=['ReduxStart.PopulateLoad','press:load.baseline-row','ReduxStart.Ready','clock:resume','clock:pause']),
      'loot-before.json':first,'loot-after.json':last,'loot-before-save.state.json':copy.deepcopy(after),'loot-after-save.state.json':copy.deepcopy(after),
      'loot-result.json':dict(schema='bg-redux-container-loot-native/1',reload=reload,completed=True,action_id=-1 if reload else 172,callback='none' if reload else 'Container.TakeItemContainer',close_callback='none' if reload else 'Container.LeaveContainer',ui_left_index=None if reload else 0,os_pointer_input=False,save_return_code=0,forced=False,directories=['owned/save'])}
    if not reload:records.update({'loot-open.json':copy.deepcopy(first),'loot-after-take.json':copy.deepcopy(last)})
    write(folder,records);return records

class LootOutcomeTests(unittest.TestCase):
    def test_conserved_transfer_and_read_only_reload(self):
        self.assertEqual(journey.outcome(*focused())['item'],'SW1H04')
        self.assertEqual(journey.outcome(*focused(True),reload=True)['pc_after'],1)

    def test_missing_duplicate_wrong_item_and_charge_changes_rejected(self):
        for mutation in ('missing','duplicate','wrong','charges','stolen','other_loss','wrong_actor','locked','script_name','missing_script_name','stored_name'):
            before,after=focused()
            if mutation=='missing':after['pc_inventory']['items'].pop()
            elif mutation=='duplicate':after['pc_inventory']['items'].append(item('SW1H04',16))
            elif mutation=='wrong':after['pc_inventory']['items'][-1]['resref']='SW1H07'
            elif mutation=='charges':after['pc_inventory']['items'][-1]['usages'][0]=1
            elif mutation=='stolen':after['pc_inventory']['items'][-1]['flags']|=4
            elif mutation=='other_loss':after['container_inventory']['items']=[]
            elif mutation=='wrong_actor':after['pc_runtime_id']=10003
            elif mutation=='script_name':after['container_script_name']='anothercontainer'
            elif mutation=='missing_script_name':after.pop('container_script_name')
            elif mutation=='stored_name':after['container']='Another Table'
            else:after['flags']=1
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):journey.outcome(before,after)

    def test_reload_side_transfer_and_duplicate_slot_rejected(self):
        before,after=focused(True);after['pc_inventory']['items'].append(item('HAMM01',16))
        with self.assertRaises(ValueError):journey.outcome(before,after,True)
        before,after=focused();after['pc_inventory']['items'][-1]['slot']=10
        with self.assertRaises(ValueError):journey.outcome(before,after)

class LootCaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.folder=Path(self.tmp.name);self.records=capture(self.folder)
    def validate(self,reload=False,started=None):return journey.validate_capture(self.folder,8,reload,172,started)
    def test_complete_evidence_then_reload(self):
        self.assertEqual(self.validate()['samples'],17);capture(self.folder,True);self.assertEqual(self.validate(True)['outcome']['pc_after'],1)
    def test_missing_and_stale_raw_evidence_rejected(self):
        p=self.folder/'loot-after-take.json';p.unlink()
        with self.assertRaises(FileNotFoundError):self.validate()
        write(self.folder,self.records)
        for p in self.folder.iterdir():os.utime(p,ns=(1,1))
        with self.assertRaisesRegex(ValueError,'Stale'):self.validate(started=2)
    def test_completion_markers_cannot_replace_transfer_or_save(self):
        for field,value in [('callback','fake'),('close_callback','none'),('action_id',173),('forced',True),('save_return_code',True),('save_return_code',1),('os_pointer_input',True),('reload',True)]:
            records=copy.deepcopy(self.records);records['loot-result.json'][field]=value;write(self.folder,records)
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):self.validate()
    def test_clock_freeze_and_snapshot_save_mutation_rejected(self):
        records=copy.deepcopy(self.records)
        for row in records['clock-samples.json']['samples']:row['game_time']=100
        write(self.folder,records)
        with self.assertRaises(ValueError):self.validate()
        records=copy.deepcopy(self.records);records['loot-after-save.state.json']['gold']=1;write(self.folder,records)
        with self.assertRaisesRegex(ValueError,'changed captured state'):self.validate()
    def test_focused_full_and_open_before_callback_mismatch_rejected(self):
        for field in ('pc_runtime_id','pc_position'):
            records=copy.deepcopy(self.records);records['loot-after.json'][field]=10003 if field=='pc_runtime_id' else [0,0];write(self.folder,records)
            with self.assertRaises(ValueError):self.validate()
        records=copy.deepcopy(self.records);records['loot-open.json']['container_inventory']['items'].append(item('HAMM01',3));write(self.folder,records)
        with self.assertRaises(ValueError):self.validate()
    def test_missing_trace_and_unobserved_movement_rejected(self):
        records=copy.deepcopy(self.records);records['clock-samples.json']['samples'][0]['action_trace']=[];write(self.folder,records)
        with self.assertRaisesRegex(ValueError,'trace absent'):self.validate()
        records=copy.deepcopy(self.records)
        for sample in records['clock-samples.json']['samples']:sample['action_trace'][0]['position']=records['loot-before.json']['pc_position']
        write(self.folder,records)
        with self.assertRaisesRegex(ValueError,'movement'):self.validate()

class LootBindingTests(unittest.TestCase):
    def test_source_and_frozen_source_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);source=folder/'source.py';frozen=folder/'frozen.py';source.write_bytes(b'x=1\n');frozen.write_bytes(source.read_bytes())
            receipt=dict(sources={str(source):dict(sha256=journey.evidence.sha(source),frozen=str(frozen))})
            with patch.object(journey,'sources',return_value=[source]):
                journey.check_sources(receipt,folder,folder)
                for changed in (source,frozen):
                    changed.write_bytes(b'x=2\n')
                    with self.assertRaisesRegex(ValueError,'drift'):journey.check_sources(receipt,folder,folder)
                    changed.write_bytes(b'x=1\n')
    def test_wrong_build_schema_and_failed_preservation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);path=folder/'build.json'
            for data in [dict(schema='other'),dict(schema=journey.KIND,verdict='built-not-executed',project=str(folder),source=str(folder),build=str(folder),phase0_preservation=dict(source=False,binaries=True,fixture=True),candidate_preserved=True)]:
                path.write_text(json.dumps(data),encoding='utf-8')
                with self.assertRaises(ValueError):journey.check_build(path,folder,folder,folder)
    def test_serialized_missing_item_and_changed_charge_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'BALDUR.SAV').write_bytes(b'sav');(folder/'BALDUR.gam').write_bytes(b'gam')
            api=SimpleNamespace(legacy_oracle=SimpleNamespace(read_wire=lambda path:dict(party=[dict(items=[item('SW1H04')])])))
            with patch.object(journey,'container_wire',return_value=dict(items=[item('STAF01')])):
                journey.check_wire(folder,api,[item('STAF01')],[item('SW1H04')])
                with self.assertRaises(ValueError):journey.check_wire(folder,api,[item('STAF01')],[])
                changed=item('SW1H04');changed['usages'][0]=2
                with self.assertRaises(ValueError):journey.check_wire(folder,api,[item('STAF01')],[changed])

class LootWireTests(unittest.TestCase):
    def area(self):
        area=bytearray(0x11c+192+20);area[:8]=b'AREAV1.0';struct.pack_into('<IHHI',area,0x70,0x11c,1,1,0x11c+192)
        at=0x11c;area[at:at+14]=b'Jailkeep Table';struct.pack_into('<HHH',area,at+32,3109,2829,5);struct.pack_into('<II',area,at+64,0,1);area[-20:-12]=b'SW1H04\0\0';return area
    def parse(self,area):
        with patch.object(journey.binary,'sav_records',return_value=[dict(name='AR0602.are')]),patch.object(journey.binary,'inflate',return_value=area):return journey.container_wire(b'')
    def test_bounded_table_decodes_real_record_shape(self):self.assertEqual(self.parse(self.area())['items'][0]['resref'],'SW1H04')
    def test_truncated_overlap_slice_trap_and_wrong_name_rejected(self):
        for mutation in ('truncated','overlap','slice','trap','name'):
            area=self.area()
            if mutation=='truncated':area.pop()
            elif mutation=='overlap':struct.pack_into('<I',area,0x78,0x11c)
            elif mutation=='slice':struct.pack_into('<I',area,0x11c+68,2)
            elif mutation=='trap':struct.pack_into('<H',area,0x11c+48,1)
            else:area[0x11c]=ord('X')
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.parse(area)
    def test_generated_host_rejects_missing_or_ambiguous_anchors(self):
        source=(Path(journey.__file__).parent/'native/loot_gui_probe_snapshot.cpp').read_bytes()
        self.assertIn(b'LootTick(out,index)',journey.instrument(source))
        with self.assertRaises(ValueError):journey.instrument(source.replace(b'static Window* WindowIn',b'static Window* Changed'))
        with self.assertRaises(ValueError):journey.instrument(source+b'\nstatic Window* WindowIn')

if __name__=='__main__':unittest.main()
