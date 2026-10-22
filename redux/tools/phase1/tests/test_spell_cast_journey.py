"""Synthetic evidence mutations only. Coordinator runs these; no game is launched."""
import copy
import json
import os
from pathlib import Path
import sys
import struct
from unittest.mock import patch, Mock
from types import SimpleNamespace
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).parents[1]))
import spell_cast_journey as j
from test_weapon_query_validation import setup_case


def state(used=False,effects=False,t=100):
    _,_,s,_=setup_case();s['selection']=2;s['game_time']=t
    a=s['party'][1];a.update(name='Imoen',script_name='Imoen',effects=[])
    a['spellbook']=[dict(type=1,level=0,slots=4,slots_with_bonus=4,known=[dict(resref='SPWI102',type=1,level=0),dict(resref='SPWI118',type=1,level=0)],memorized=[dict(resref='spwi102',flags=0 if used else 1),dict(resref='spwi118',flags=1)])]
    if effects:
        a['effects']=[dict(opcode=op,source_ref='SPWI102',parameters=params+[0]*4,timing=0,duration=10000,caster_id=10003) for op,params in [(0,[6,16]),(142,[0,12])]]
    return s


def context(s,ready=True,casting=False):
    a=s['party'][1];action=dict(id=113,resref='spwi102',target_mode=-1,target_id=10003)
    return dict(actor=copy.deepcopy(a),game_time=s['game_time'],selected_id=10003,selected_count=1,bd_defai=1 if ready else None,leader_class_script='BDDEFAI' if ready else '',current=action if casting else None,next=None,in_move=False,current_action_target=10003 if casting else 0,last_spell_target=10003 if casting else 0,casting_resref='SPWI102' if casting else '',action_ticks=1 if casting else 0,action_state=10 if casting else 0)


def capture(folder,reload=False):
    first=state(reload,reload);last=state(True,True,108);rows=[];samples=[]
    command=state(t=105);post=copy.deepcopy(command);released=state(True,True,108)
    for i in range(17):
        t=100 if i<5 else min(108,96+i);used=reload or i>=10;effects=reload or i>=12
        ctx=context(state(used,effects,t),ready=reload or i>=5,casting=not reload and i in (10,11));after=copy.deepcopy(ctx)
        if not reload and i==9:after['next']=dict(id=113,resref='SPWI102',target_mode=-1,target_id=10003)
        rows.append(dict(sample=i,running=4<i<=12,eligible=j.eligible(ctx),streak=0 if reload or i<5 else min(4,i-4),press_count=0 if reload or i<9 else 1,opened=not reload and i==8,issued=not reload and i==9,before=ctx,after=after))
        samples.append(dict(sample=i,phase='paused-initial' if i<5 else 'running' if i<=12 else 'paused-final',game_time=t,elapsed_ms=i*250,action_trace=[dict(runtime_id=10003,position=after['actor']['position'],action_id=after['current']['id'] if after['current'] else None,current_action_target=after['current_action_target'])]))
    for table in ('spldisp','guibtact'):(folder/(table+'.runtime.2da')).write_bytes(b'2DA V1.0\n0\n')
    records={'spell-table-providers.json':dict(schema='bg-redux-spell-table-providers/1',tables={}), 'clock-before.state.json':first,'clock-after.state.json':last,'clock-samples.json':dict(schema='bg-redux-live-clock/1',ticks_per_second=15,samples=samples),
      'gui-result.json':dict(completed=True,steps=17,events=['ReduxStart.PopulateLoad','press:load.baseline-row','ReduxStart.Ready','clock:resume','clock:pause']),
      'spell-before.state.json':first,'spell-portrait-before.state.json':copy.deepcopy(first),'spell-before-save.state.json':last,'spell-after-save.state.json':copy.deepcopy(last),
      'spell-diagnostics.json':dict(schema='bg-redux-spell-diagnostics/1',samples=rows),
      'spell-result.json':dict(schema='bg-redux-spell-native/1',reload=reload,portrait_callback='GUICommonWindows.PortraitButtonOnPress',cast_callback='none' if reload else 'ActionsWindow.ActionCastPressed',spell_callback='none' if reload else 'ActionsWindow.SpellPressed',gui_save_callback='GUISAVE.ConfirmedSaveGame',save_return_code_observed=False,forced=False,os_pointer_input=False,action_id=113,press_count=0 if reload else 1,command_sample=-1 if reload else 9,open_sample=-1 if reload else 8,release_sample=-1 if reload else 12,directories=['owned/save'])}
    shots=['spell-before-portrait','spell-before','spell-before-save','spell-save-confirm','spell-after-save']
    if not reload:
        records.update({'spell-cast-before.state.json':state(t=104),'spell-cast-button.json':dict(control=2,action=2,visible=True,disabled=False),'spell-command-before.state.json':command,'spell-command-after.state.json':post,'spell-released.state.json':released,'spell-button.json':dict(resref='SPWI102',target=5,type=1,level=0,dict_name='Spell',dict_value=2000,disabled=False,visible=True,spell_control=0,cast_control=2,slot=0,ready_count=1,casting_time=9,header_index=0)})
        shots+=['spell-cast-before','spell-command-before','spell-icons','spell-command-after','spell-released']
    for shot in shots:(folder/(shot+'.bmp')).write_bytes(b'BM'+bytes(100))
    write(folder,records);return records


def write(folder,records):
    for name,value in records.items():(folder/name).write_text(json.dumps(value),encoding='utf-8')


class SpellEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.folder=Path(self.tmp.name);self.records=capture(self.folder)
    def validate(self,reload=False,started=None):return j.validate_capture(self.folder,8,reload,113,started)
    def test_complete_callback_release_and_reload(self):
        self.assertEqual(self.validate()['readiness']['callback_count'],1)
        capture(self.folder,True);self.assertEqual(self.validate(True)['readiness']['callback_count'],0)
    def test_consumption_without_actual_effects_cannot_pass(self):
        self.records['spell-diagnostics.json']['samples'][12]['after']['actor']['effects']=[];write(self.folder,self.records)
        with self.assertRaises(ValueError):self.validate()
    def test_wrong_or_missing_actual_self_action_rejected(self):
        for field,value in [('target_id',10002),('resref','SPWI118'),('id',114),('target_mode',0)]:
            records=copy.deepcopy(self.records);records['spell-diagnostics.json']['samples'][9]['after']['next'][field]=value;write(self.folder,records)
            with self.subTest(field=field),self.assertRaises(ValueError):self.validate()
    def test_depletion_does_not_substitute_for_observed_casting(self):
        records=copy.deepcopy(self.records)
        for i in (10,11):records['spell-diagnostics.json']['samples'][i]['before']['last_spell_target']=0
        write(self.folder,records)
        with self.assertRaises(ValueError):self.validate()
    def test_early_duplicate_callback_and_false_readiness_rejected(self):
        for change in ('early','duplicate','wrongscript','moving','multiselect','missingqueue'):
            records=copy.deepcopy(self.records);rows=records['spell-diagnostics.json']['samples']
            if change=='early':rows[7]['issued']=True
            elif change=='duplicate':rows[10]['press_count']=2
            elif change=='wrongscript':rows[5]['before']['leader_class_script']='DPLAYER3'
            elif change=='moving':rows[5]['before']['in_move']=True
            elif change=='multiselect':rows[5]['before']['selected_count']=2
            else:rows[5]['before'].pop('next')
            write(self.folder,records)
            with self.subTest(change=change),self.assertRaises(ValueError):self.validate()
    def test_wrong_icon_disabled_callback_or_force_save_rejected(self):
        for field,value in [('resref','SPWI118'),('disabled',True),('target',4),('dict_value',1000),('slot',1),('casting_time',0),('ready_count',2)]:
            records=copy.deepcopy(self.records);records['spell-button.json'][field]=value;write(self.folder,records)
            with self.subTest(field=field),self.assertRaises(ValueError):self.validate()
        records=copy.deepcopy(self.records);records['spell-result.json']['forced']=True;write(self.folder,records)
        with self.assertRaises(ValueError):self.validate()
    def test_release_snapshot_and_save_mutation_rejected(self):
        for name in ('spell-released.state.json','spell-after-save.state.json'):
            records=copy.deepcopy(self.records);records[name]['party'][1]['modified_stats'][2]+=1;write(self.folder,records)
            with self.subTest(name=name),self.assertRaises(ValueError):self.validate()
    def test_missing_stale_and_invalid_screenshot_rejected(self):
        p=self.folder/'spell-released.bmp';p.unlink()
        with self.assertRaises(ValueError):self.validate()
        capture(self.folder);os.utime(p,ns=(1,1))
        with self.assertRaises(ValueError):self.validate(started=2)
        p.write_bytes(b'not a BMP')
        with self.assertRaises(ValueError):self.validate()
    def test_reload_cannot_cast_or_lose_effects(self):
        records=capture(self.folder,True);records['spell-result.json']['press_count']=1;write(self.folder,records)
        with self.assertRaises(ValueError):self.validate(True)
    def test_clock_must_progress_with_correct_phases(self):
        for change in ('paused','phase','backwards'):
            records=copy.deepcopy(self.records);samples=records['clock-samples.json']['samples']
            if change=='paused':
                for row in samples:row['game_time']=100
            elif change=='phase':samples[9]['phase']='paused-initial'
            else:samples[9]['elapsed_ms']=0
            write(self.folder,records)
            with self.subTest(change=change),self.assertRaises(ValueError):self.validate()


class SpellConservationTests(unittest.TestCase):
    def test_exact_one_depletion_and_other_book_unchanged(self):
        j.conservation(state(),state(True,True),True)
        for change in ('othercharge','grant','inventory','slots'):
            after=state(True,True);a=after['party'][1]
            if change=='othercharge':a['spellbook'][0]['memorized'][1]['flags']=0
            elif change=='grant':a['spellbook'][0]['memorized'].append(dict(resref='SPWI102',flags=1))
            elif change=='inventory':a['inventory']['items']=[]
            else:a['spellbook'][0]['slots']=5
            with self.subTest(change=change),self.assertRaises(ValueError):j.conservation(state(),after,True)
    def test_wrong_source_caster_parameters_and_expired_effects_rejected(self):
        for field,value in [('source_ref','SPWI118'),('caster_id',10002),('duration',100),('parameters',[5,16,0,0,0,0]),('timing',9)]:
            a=state(True,True)['party'][1];a['effects'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):j.required_effects(a,100,True)
    def test_duplicate_page_and_effect_rejected(self):
        a=state()['party'][1];a['spellbook'].append(copy.deepcopy(a['spellbook'][0]))
        with self.assertRaises(ValueError):j.book(a)
        a=state(True,True)['party'][1];a['effects'].append(copy.deepcopy(a['effects'][0]))
        with self.assertRaises(ValueError):j.required_effects(a,100)
    def test_old_baseline_host_cannot_be_instrumented_when_anchor_drifts(self):
        raw=(Path(j.__file__).parent/'native/spell_gui_probe_snapshot.cpp').read_bytes()
        self.assertIn(b'SpellTick',j.instrument(raw))
        with self.assertRaises(ValueError):j.instrument(raw.replace(b'static Window* WindowIn',b'static Window* RemovedAnchor'))

class SpellWireAndProvenanceTests(unittest.TestCase):
    def gam(self,overlap=False):
        from test_saved_npc_color_fixtures import cre as base_cre
        data=bytearray(0xb4+2*0x160);data[:8]=b'GAMEV2.0';struct.pack_into('<II',data,0x20,0xb4,2)
        for index in range(2):
            source=bytearray(base_cre());source[0x280:0x285]=b'Imoen'
            memo=len(source);source.extend(struct.pack('<HHHHII',0,4,4,1,0,2))
            if overlap:source.extend(struct.pack('<HHHHII',1,1,1,1,0,1))
            spells=len(source);source.extend(b'SPWI102\0'+struct.pack('<I',0)+b'SPWI118\0'+struct.pack('<I',1))
            struct.pack_into('<II',source,0x2a8,memo,2 if overlap else 1);struct.pack_into('<II',source,0x2b0,spells,2)
            row=0xb4+index*0x160;struct.pack_into('<II',data,row+4,len(data),len(source));data.extend(source)
        return bytes(data)
    def test_bounded_wire_memorization_and_overlapping_page_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'BALDUR.GAM';p.write_bytes(self.gam())
            with patch.object(j.common,'member',return_value=p):
                self.assertEqual(j.ready(j.wire_spells(Path(tmp))),0)
                self.assertEqual(j.book(j.wire_spells(Path(tmp)))[(1,0,'spwi118',1)],1)
                p.write_bytes(self.gam(True))
                with self.assertRaises(ValueError):j.wire_spells(Path(tmp))
                p.write_bytes(self.gam()[:-1])
                with self.assertRaises(ValueError):j.wire_spells(Path(tmp))
    def test_frozen_source_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.py';frozen=root/'frozen.py';source.write_bytes(b'input');frozen.write_bytes(b'input')
            receipt=dict(sources={str(source):dict(sha256=j.evidence.sha(source),frozen=str(frozen))})
            with patch.object(j,'sources',return_value=[source]):
                j.check_sources(receipt,root,root)
                frozen.write_bytes(b'tamper')
                with self.assertRaises(ValueError):j.check_sources(receipt,root,root)
    def test_timeout_and_clock_budget_rejected_before_launch(self):
        with patch.object(j.shared,'new_output',side_effect=AssertionError('must not launch')):
            for count,timeout in [(80,91),(79,90),(80,0)]:
                args=SimpleNamespace(project_root=Path('.'),engine_source_root=Path('.'),engine_build_root=Path('.'),running_samples=count,timeout=timeout)
                with self.assertRaises(ValueError):j.run(args)

class SpellTableProviderTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.api=SimpleNamespace(probe_ui_resources=SimpleNamespace(TYPES={},read_resource=Mock(return_value=(None,None))))
    def put(self,relative,raw=b'2DA V1.0\n0\n COL\n0 1\n'):
        p=self.root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);return p
    def test_shared_fallback_and_bg2ee_precedence_are_explicit(self):
        shared=self.put('gemrb/unhardcoded/shared/spldisp.2da')
        raw,origin,proof=j.table_provider(self.api,self.root,'spldisp')
        self.assertEqual(Path(origin),shared);self.assertEqual(raw,shared.read_bytes());self.assertFalse(proof['checked_paths'][2]['exists'])
        specific=self.put('gemrb/unhardcoded/bg2ee/spldisp.2da',b'2DA V1.0\n0\n COL\n0 2\n')
        raw,origin,proof=j.table_provider(self.api,self.root,'spldisp')
        self.assertEqual(Path(origin),specific);self.assertEqual(raw,specific.read_bytes());self.assertTrue(proof['checked_paths'][2]['exists'])
    def test_missing_malformed_and_game_or_engine_shadow_rejected(self):
        with self.assertRaises(ValueError):j.table_provider(self.api,self.root,'guibtact')
        p=self.put('gemrb/unhardcoded/bg2ee/guibtact.2da',b'invalid')
        with self.assertRaises(ValueError):j.table_provider(self.api,self.root,'guibtact')
        p.write_bytes(b'2DA V1.0\n0\n')
        self.api.probe_ui_resources.read_resource.return_value=(b'2DA V1.0\n0\n','override/guibtact.2da')
        with self.assertRaisesRegex(ValueError,'game table provider'):j.table_provider(self.api,self.root,'guibtact')
        self.api.probe_ui_resources.read_resource.return_value=(None,None)
        self.put('gemrb/override/shared/guibtact.2da')
        with self.assertRaisesRegex(ValueError,'GemRB table override'):j.table_provider(self.api,self.root,'guibtact')
    def test_absence_proof_and_selected_content_drift_rejected(self):
        p=self.put('gemrb/unhardcoded/shared/spldisp.2da')
        def current(api,source):
            raw,origin,provider=j.table_provider(api,source,'spldisp')
            return dict(spldisp=dict(raw=raw,origin=origin,provider=provider,bytes=len(raw),sha256=j.binary.digest(raw)))
        expected=current(self.api,self.root)['spldisp'];frozen=self.put('frozen.2da',expected['raw'])
        receipt=dict(source=str(self.root),startup_resources=dict(spldisp={k:v for k,v in expected.items() if k!='raw'}|dict(frozen=str(frozen))))
        with patch.object(j,'startup_resources',side_effect=current):
            j.check_resources(receipt,self.api)
            self.put('gemrb/unhardcoded/bg2ee/spldisp.2da',p.read_bytes())
            with self.assertRaisesRegex(ValueError,'provider/frozen drift'):j.check_resources(receipt,self.api)
        (self.root/'gemrb/unhardcoded/bg2ee/spldisp.2da').unlink();p.write_bytes(b'2DA V1.0\n1\n')
        with patch.object(j,'startup_resources',side_effect=current),self.assertRaises(ValueError):j.check_resources(receipt,self.api)
    def test_runtime_actual_path_and_exact_bytes_required(self):
        rows={};receipt=dict(startup_resources={})
        for name in ('spldisp','guibtact'):
            original=self.put('gemrb/unhardcoded/shared/'+name+'.2da')
            frozen=self.put(name+'.runtime.2da',original.read_bytes())
            receipt['startup_resources'][name]=dict(provider=dict(path=str(original)),bytes=original.stat().st_size,sha256=j.evidence.sha(original))
            rows[name]=dict(originalfile=str(original),bytes=original.stat().st_size)
        report=self.root/'spell-table-providers.json'
        def save():report.write_text(json.dumps(dict(schema='bg-redux-spell-table-providers/1',tables=rows)),encoding='utf-8')
        save();j.check_runtime_tables(self.root,receipt)
        rows['spldisp']['originalfile']=str(self.root/'unexpected-identical.2da');save()
        with self.assertRaises(ValueError):j.check_runtime_tables(self.root,receipt)
        rows['spldisp']['originalfile']=receipt['startup_resources']['spldisp']['provider']['path'];save()
        (self.root/'spldisp.runtime.2da').write_bytes(b'drift')
        with self.assertRaises(ValueError):j.check_runtime_tables(self.root,receipt)

if __name__=='__main__':unittest.main()
