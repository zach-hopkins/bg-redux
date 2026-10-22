"""Negative contracts for the separate source-only confirmation journey."""
import ast
import copy
from pathlib import Path
import sys
import os
import tempfile
import time
import unittest
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import confirmation_setting_validation as v


def state():
    actors=[]
    for i,name in enumerate(('none','imoen','jaheira','minsc'),1):
        pages=[]
        if i in (2,3):
            c=v.CASES[i-2]
            pages=[dict(type=c['kind'],level=c['level'],slots=3,slots_with_bonus=5 if i==3 else 3,known=[dict(resref=c['ref'],type=c['kind'],level=c['level'])],memorized=[dict(resref=c['ref'],flags=1),dict(resref=c['filler'],flags=1),dict(resref=c['filler'],flags=1)])]
        actors.append(dict(runtime_id=i,script_name=name,spellbook=pages,xp=123,items=[]))
    return dict(selection=1,party=actors,current_area_actors=copy.deepcopy(actors),journal=[dict(text=47518)],game_time=100)


def mutate(s,c,kind):
    x=copy.deepcopy(s)
    for group in ('party','current_area_actors'):
        p=v.page(x[group][c['pc']-1],c['kind'],c['level']);p['memorized']=v.changed(p['memorized'],c,kind)
    return x


class ConfirmationJourneyTests(unittest.TestCase):
    def test_added_copy_preserves_native_prepared_storage_spelling(self):
        c=v.CASES[0];a=state()
        for group in ('party','current_area_actors'):
            for row in v.page(a[group][1],1,1)['memorized']:row['resref']=row['resref'].lower()
        b=copy.deepcopy(a)
        for group in ('party','current_area_actors'):
            v.page(b[group][1],1,1)['memorized'].append(dict(resref='spwi213',flags=0))
        v.world_delta(a,b,c,'add')
        b['party'][1]['spellbook'][0]['memorized'][-1]['resref']='spwi214'
        with self.assertRaises(ValueError):v.world_delta(a,b,c,'add')
    def test_exact_plans_include_setting_cancel_done_both_books_and_mixed(self):
        p=v.expected_plan('operate')
        for n in ('settings.cancel','settings.done','mage.target-modal','priest.target-modal','mage.mixed-charged-click','priest.mixed-charged-click','priest.known-select'):
            self.assertEqual(p.count(n),1)
        self.assertNotIn('settings.done',v.expected_plan('reload'))
        self.assertNotIn('mage.mixed-charged-click',v.expected_plan('reload'))

    def test_persistent_config_not_dictionary_only_and_no_wrong_key(self):
        v.config_value(b'[Game Options]\nOver Confirm Everything=1\n',1)
        for raw in (b'',b'[Game Options]\nConfirm Dialog=1\n',b'[Game Options]\nOver Confirm Everything=0\n',b'[Game Options]\nOver Confirm Everything=one\n'):
            with self.assertRaises(ValueError):v.config_value(raw,1)

    def test_duplicate_config_rejected(self):
        with self.assertRaises(ValueError):v.config_value(b'[Game Options]\nOver Confirm Everything=1\nOver Confirm Everything=0\n',1)

    def test_whitelist_rejects_draft_or_missing_other_keys(self):
        default=b'[Game Options]\nOver Confirm Everything=0\nOther=2\n'
        v.config_value(b'[Game Options]\nOther=2\nOver Confirm Everything=1\n',1,default)
        for raw in (b'[Game Options]\nOver Confirm Everything=1\n',b'[Game Options]\nOver Confirm Everything=1\nOther=2\nBG2EE Confirmation Draft=1\n'):
            with self.assertRaises(ValueError):v.config_value(raw,1,default)

    def test_config_copy_must_be_byte_exact_even_with_equal_parsed_value(self):
        raw=b'[Game Options]\nOver Confirm Everything=1\n'
        v.config_copy_guard(raw,raw)
        with self.assertRaises(ValueError):v.config_copy_guard(raw,raw.replace(b'=1',b' = 1'))

    def test_cancel_cannot_publish_or_save_actual_setting(self):
        meta=dict(settings=dict(option=0,draft=1,ini_exists=False,ini_text=None))
        native=dict(option=0,draft_raw=1,ini_exists=False,ini_text=None)
        v.setting_observation('settings.draft-cancel',meta,native,'operate')
        bad=copy.deepcopy(native);bad['option']=1
        meta['settings']['option']=1
        with self.assertRaises(ValueError):v.setting_observation('settings.draft-cancel',meta,bad,'operate')

    def test_missing_draft_bridge_cannot_mask_wrong_value(self):
        meta=dict(settings=dict(option=0,draft=None,ini_exists=False,ini_text=None))
        native=dict(option=0,draft_raw=-12345,ini_exists=False,ini_text=None)
        v.setting_observation('settings.after-cancel',meta,native,'operate')
        native['draft_raw']=9
        with self.assertRaises(ValueError):v.setting_observation('settings.after-cancel',meta,native,'operate')

    def test_reload_cannot_claim_loaded_option_zero(self):
        meta=dict(settings=dict(option=0,draft=None,ini_exists=False,ini_text=None))
        with self.assertRaises(ValueError):v.setting_observation('settings.loaded',meta,dict(option=0,draft_raw=None,ini_exists=False,ini_text=None),'reload')

    def test_filler_removes_exactly_one_duplicate_in_order(self):
        c=v.CASES[1];a=state();b=mutate(a,c,'filler');v.world_delta(a,b,c,'filler')
        self.assertEqual(v.memo_rows(v.page(b['party'][2],0,0)['memorized']),[('SPPR113',1),('SPPR105',1)])
        b['party'][2]['spellbook'][0]['memorized'].pop()
        with self.assertRaises(ValueError):v.world_delta(a,b,c,'filler')

    def test_mixed_charged_click_removes_depleted_and_preserves_charged(self):
        c=v.CASES[0];a=mutate(state(),c,'filler');a=mutate(a,c,'add');b=mutate(a,c,'mixed');v.world_delta(a,b,c,'mixed')
        self.assertEqual(v.page(b['party'][1],1,1)['memorized'][0],dict(resref='SPWI213',flags=1))
        wrong=copy.deepcopy(a)
        for group in ('party','current_area_actors'):v.page(wrong[group][1],1,1)['memorized'].pop(0)
        with self.assertRaises(ValueError):v.world_delta(a,wrong,c,'mixed')

    def test_mixed_requires_exact_same_ref_depleted_and_not_other_page(self):
        c=v.CASES[0];rows=[dict(resref='SPWI213',flags=1),dict(resref='SPWI214',flags=0)]
        with self.assertRaises(ValueError):v.changed(rows,c,'mixed')
        rows=[dict(resref='SPWI213',flags=1),dict(resref='SPWI213',flags=0),dict(resref='SPWI213',flags=0)]
        with self.assertRaises(ValueError):v.changed(rows,c,'mixed')

    def test_other_world_and_known_changes_not_normalized(self):
        c=v.CASES[0];a=state()
        for field,value in (('xp',124),('items',['SW1H04'])):
            b=mutate(a,c,'filler');b['party'][1][field]=value
            with self.assertRaises(ValueError):v.world_delta(a,b,c,'filler')
        b=mutate(a,c,'filler');b['party'][1]['spellbook'][0]['known']=[]
        with self.assertRaises(ValueError):v.world_delta(a,b,c,'filler')

    def test_actual_settings_route_is_not_substitutable(self):
        v.route_guard('settings.done',dict(pack='GUIOPT',window=9,control=26))
        for c in (27,38):
            with self.assertRaises(ValueError):v.route_guard('settings.done',dict(pack='GUIOPT',window=9,control=c))

    def test_memo_route_requires_actual_original_index(self):
        v.route_guard('mage.mixed-charged-click',dict(pack='GUIMG',window=2,control=3,actual_value=0))
        with self.assertRaises(ValueError):v.route_guard('mage.mixed-charged-click',dict(pack='GUIMG',window=2,control=4,actual_value=0))

    def test_partial_or_stale_plan_rejected(self):
        nonce='a'*32;host=dict(schema='bg-redux-book-host/1',nonce=nonce,mode='reload',completed=True,error='',os_pointer_input=False,direct_spell_mutation=False)
        plan=v.expected_plan('reload');runtime=dict(schema='bg-redux-confirmation-runtime/1',nonce=nonce,mode='reload',planned=plan,steps=len(plan),completed=True)
        v.terminal(host,runtime,nonce,'reload')
        runtime['planned']=plan[:-1]
        with self.assertRaises(ValueError):v.terminal(host,runtime,nonce,'reload')
        runtime['planned']=plan;host['nonce']='b'*32
        with self.assertRaises(ValueError):v.terminal(host,runtime,nonce,'reload')

    def test_stale_and_missing_native_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            with self.assertRaises(ValueError):v.fresh_evidence(folder,None)
            required=('book-result.json','book-runtime.json','book-events.json','book-startup.json','loaded.state.json','loaded.settings.json','ready.state.json','ready.scene.json','operations-final.state.json','final.state.json')
            for name in required:(folder/name).write_text('{}',encoding='utf8')
            v.fresh_evidence(folder,None)
            os.utime(folder/'loaded.settings.json',ns=(1,1))
            with self.assertRaises(ValueError):v.fresh_evidence(folder,time.time_ns())

    def test_runtime_has_no_direct_option_or_spell_mutators(self):
        tree=ast.parse((HERE/'ConfirmationSettingRuntime.py').read_text(encoding='utf8'))
        forbidden={'MemorizeSpell','UnmemorizeSpell','SetPlayerStat','SetGlobal','ApplySpell','RestParty'}
        for node in ast.walk(tree):
            if isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)and isinstance(node.func.value,ast.Name)and node.func.value.id=='GemRB':
                self.assertNotIn(node.func.attr,forbidden)
                if node.func.attr=='SetVar'and isinstance(node.args[0],ast.Constant):self.assertTrue(node.args[0].value.startswith('RDXBook'))

    def test_source_closure_explicitly_binds_new_policy_and_layout(self):
        raw=(HERE/'confirmation_setting_journey.py').read_text(encoding='utf8')
        for name in ('GUIScripts/BG2EEConfirmation.py','GUIScripts/EESpellbookInformation.py','GUIScripts/GUIOPTControls.py','GUIScripts/MenuWindow.py','core/Interface.cpp','unhardcoded/shared/defaults.ini'):
            self.assertIn(name,raw)
        native=(HERE/'native/confirmation_setting_journey.cpp').read_text(encoding='utf8')
        self.assertIn('b->MouseDown(me,0)',native);self.assertIn('b->MouseUp(me,0)',native)
        self.assertIn('"view-mouse-down-up"',native)


if __name__=='__main__':unittest.main()
