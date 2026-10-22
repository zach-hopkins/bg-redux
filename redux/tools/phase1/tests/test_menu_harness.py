import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


harness = load("menu_harness_test", HERE / "menu_harness.py")


def spell_fixture():
    contract = dict(pack='GUIMG', actor=2, actor_name='Imoen', level=0, sorcerer=False,
        known=[dict(resref='spwi112', value=3, tooltip='Magic Missile')],
        memorized=[dict(resref='spwi112', value=0, tooltip='Magic Missile', ready=1)],
        known_capacity=24, memorized_capacity=12)
    state = dict(selection=2, party=[dict(name='Fighter'), dict(name='Imoen')])
    controls = [dict(pack='GUIMG', window=2, id=0x10000035, visible=True, text='Imoen')]
    for family, base, count in (('known',27,24),('memorized',3,12)):
        for i in range(count):
            spell = contract[family][i] if i < len(contract[family]) else None
            controls.append(dict(pack='GUIMG',window=2,id=base+i,visible=True,disabled=False,
                rect=[0,0,32,32],
                value=spell['value'] if spell else i, flags=2 if spell else 0,
                tooltip=spell['tooltip'] if spell else '', stored_tooltip=spell['tooltip'] if spell else '',
                picture_observable=True,picture_present=bool(spell),picture_size=[32,32] if spell else None))
    return contract,state,dict(controls=controls)


class MenuReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        (self.path/'process.log').write_text('normal native log\n',encoding='utf-8')
        self.runtime = dict(nonce="0123456789abcdef0123456789abcdef", steps=10, planned_steps=10, context_required=["store"],
            checks=[dict(action=name, capture=i+1) for i, name in enumerate(sorted(harness.REQUIRED_OBSERVATIONS))] +
                   [dict(name="actual-hp", passed=True)])
        self.host = dict(completed=True, captures=len(harness.REQUIRED_OBSERVATIONS), nonce='0123456789abcdef0123456789abcdef')
        self.before = dict(selection=1, hp=20, ammo=8, effects=[1, 2], globals={"QUEST": 3})
        self.after = dict(self.before, selection=2)
        bmp = bytearray(58)
        bmp[:2] = b"BM"
        struct.pack_into("<I", bmp, 2, len(bmp))
        struct.pack_into("<I", bmp, 10, 54)
        struct.pack_into("<ii", bmp, 18, 1, 1)
        for i in range(1, self.host["captures"] + 1):
            (self.path / ("capture-%d.bmp" % i)).write_bytes(bmp)
            for suffix in ("ui", "state", "observer"):
                harness.write(self.path / ("capture-%d.%s.json" % (i, suffix)), {})
        for action, pack, ids in (("inventory.observed", "GUIINV", (0x10000032, 0x10000039, 0x10000055)),
                                   ("record.observed", "GUIREC", (0x1000000e, 0x10000029, 0x10000040))):
            index = next(row["capture"] for row in self.runtime["checks"] if row.get("action") == action)
            harness.write(self.path / ("capture-%d.ui.json" % index), dict(controls=[dict(pack=pack, window=2, id=cid, visible=True, text=value)
                for cid, value in zip(ids, ("Actor", "20", "13"))]))
            harness.write(self.path / ("capture-%d.state.json" % index), dict(selection=1, party=[dict(name="Actor", modified_stats=[20])]))
            harness.write(self.path / ("capture-%d.observer.json" % index), dict(actors=[dict(party_index=1, cached_thac0=13)]))
        contract,state,ui=spell_fixture()
        self.runtime['checks'].extend([
            dict(name='mage-book.applicability',applicable=True,selected_actor=2),
            dict(name='mage-book.content-contract',**contract),
            dict(name='priest-book.applicability',applicable=False,selected_actor=None),
            dict(step=7,action='mage-book.select-eligible'),dict(step=8,action='mage-book.open')])
        for sequence,step,pack,cid in ((1,8,'PORTWIN',1),(2,9,'OPTWIN',5)):
            harness.write(self.path/('callback-%d.json'%sequence),dict(runtime_step=step,
                pack=pack,window=0,control=cid,performed=True,nonce=self.host['nonce']))
        index=next(row['capture'] for row in self.runtime['checks'] if row.get('action')=='mage-book.observed')
        harness.write(self.path / ('capture-%d.ui.json'%index),ui)
        harness.write(self.path / ('capture-%d.state.json'%index),state)
        self.save()

    def save(self):
        for name, data in (("menu-runtime", self.runtime), ("menu-host-result", self.host),
                           ("before.state", self.before), ("after.state", self.after)):
            harness.write(self.path / (name + ".json"), data)

    def tearDown(self): self.temp.cleanup()

    def test_selection_is_allowed_but_visual_rng_claims_remain_unproven(self):
        value = harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')
        self.assertTrue(value["assertion_passed"])
        self.assertTrue(value["collected_world_unchanged"])
        self.assertFalse(value["visual_acceptance"])
        self.assertIsNone(value["hidden_rng_unchanged"])

    def test_nonce_must_be_pinned_by_caller_not_only_match_between_outputs(self):
        # An internally consistent old pair must still fail a fresh launch pin.
        with self.assertRaisesRegex(ValueError,'caller-pinned menu nonce'):
            harness.validate_stage(self.path, expected_nonce='fedcba9876543210fedcba9876543210')
        for value in ('', None, 'short', 'G'*32):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError,'caller-pinned menu nonce'):
                    harness.validate_stage(self.path, expected_nonce=value)

    def test_missing_or_mismatched_runtime_host_nonces_fail(self):
        for which in (self.host,self.runtime):
            original=which.pop('nonce')
            self.save()
            with self.assertRaisesRegex(ValueError,'caller-pinned menu nonce'):
                harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')
            which['nonce']='fedcba9876543210fedcba9876543210'
            self.save()
            with self.assertRaisesRegex(ValueError,'caller-pinned menu nonce'):
                harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')
            which['nonce']=original
        self.save()

    def test_validation_has_no_unpinned_call_compatibility_bypass(self):
        with self.assertRaises(TypeError): harness.validate_stage(self.path)

    def test_same_process_success_cannot_hide_changed_effects_or_ammo(self):
        self.after["ammo"] -= 1
        self.save()
        self.assertFalse(harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')["collected_world_unchanged"])

    def test_known_unimplemented_hotkey_failure_is_retained(self):
        self.runtime["checks"].append(dict(name="hotkeys.opens-real-window", passed=False))
        self.save()
        self.assertFalse(harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')["assertion_passed"])

    def test_visible_sheet_must_match_independent_native_cache(self):
        index = next(row["capture"] for row in self.runtime["checks"] if row.get("action") == "inventory.observed")
        harness.write(self.path / ("capture-%d.observer.json" % index), dict(actors=[dict(party_index=1, cached_thac0=9)]))
        value = harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')
        self.assertFalse(value["assertion_passed"])
        self.assertFalse(next(row["passed"] for row in value["checks"] if row["name"] == "inventory.observed.native-cached-thac0"))

    def test_missing_category_is_not_complete(self):
        self.runtime["checks"] = [row for row in self.runtime["checks"] if row.get("action") != "stats.observed-5"]
        self.save()
        with self.assertRaisesRegex(ValueError, "coverage"): harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')

    def test_old_window_only_book_receipt_is_rejected(self):
        self.runtime['checks']=[r for r in self.runtime['checks'] if r.get('name')!='mage-book.content-contract']
        self.save()
        with self.assertRaisesRegex(ValueError,'semantic contract'): harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')

    def test_context_gated_book_cannot_carry_content(self):
        self.runtime['checks'].append(dict(name='priest-book.content-contract',actor=3))
        self.save()
        with self.assertRaisesRegex(ValueError,'fabricated content'): harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')

    def test_stale_wrong_or_duplicate_portrait_receipt_cannot_prove_selection(self):
        path=self.path/'callback-1.json'
        original=json.loads(path.read_text())
        for key,value in (('nonce','stale'),('control',0),('pack','GUIREC'),('performed',False),('runtime_step',7)):
            with self.subTest(key=key):
                harness.write(path,dict(original,**{key:value}))
                with self.assertRaisesRegex(ValueError,'spellbook registered callback'):
                    harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')
        harness.write(path,original)
        harness.write(self.path/'callback-3.json',original)
        with self.assertRaisesRegex(ValueError,'spellbook registered callback'):
            harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')

    def test_capture_must_belong_to_observation_and_match_resolution(self):
        with self.assertRaisesRegex(ValueError, "resolution"): harness.validate_stage(self.path, (1024, 768), expected_nonce='0123456789abcdef0123456789abcdef')
        self.runtime["checks"][0].pop("capture")
        self.save()
        with self.assertRaisesRegex(ValueError, "lacks its capture"): harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')

    def test_duplicate_capture_and_incomplete_plan_rejected(self):
        self.runtime["checks"].append(dict(step=2, capture=1))
        self.save()
        with self.assertRaisesRegex(ValueError, "ambiguous"): harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')
        self.runtime["steps"] -= 1
        self.save()
        with self.assertRaisesRegex(ValueError, "incomplete"): harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')

    def test_truncated_or_absent_screenshot_rejected(self):
        (self.path / "capture-1.bmp").write_bytes(b"BM")
        with self.assertRaisesRegex(ValueError, "screenshot"): harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')
        (self.path / "capture-1.bmp").unlink()
        with self.assertRaises(OSError): harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')

    def test_artifact_inventory_never_descends_private_asset_root(self):
        game = self.path / 'stage/game/data'
        game.mkdir(parents=True)
        (game / 'licensed.bif').write_bytes(b'private asset stand-in')
        (self.path / 'stage/result.json').write_text('{}')
        result = harness.artifact_manifest(self.path)
        self.assertIn('stage/result.json', result)
        self.assertFalse(any('/game/' in p for p in result))

    def test_python_callback_traceback_cannot_hide_behind_matching_initial_ui_value(self):
        (self.path/'process.log').write_text('[Python/ERROR]: Traceback (most recent call last):\n',encoding='utf-8')
        result=harness.validate_stage(self.path, expected_nonce='0123456789abcdef0123456789abcdef')
        self.assertFalse(result['assertion_passed'])
        self.assertFalse(next(c for c in result['checks'] if c['name']=='native-python-callback-log')['passed'])


class MenuRuntimeTests(unittest.TestCase):
    def setUp(self):
        # This module must also run independently of the character-sheet suite.
        self.paths = patch.object(sys, 'path', [str(HERE.parents[2] / 'gemrb/GUIScripts')] + sys.path)
        self.paths.start()
        self.gem = types.ModuleType("GemRB")
        self.vars = {}
        self.gem.SetVar = lambda name, value: self.vars.update({name: value})
        self.gem.GetVar = lambda name: self.vars.get(name, 0)
        self.modules = patch.dict(sys.modules, {"GemRB": self.gem})
        self.modules.start()
        self.runtime = load("menu_runtime_test", HERE / "gui/MenuRuntime.py")
        self.temp = tempfile.TemporaryDirectory()
        self.runtime.Configure(self.temp.name, '0123456789abcdef0123456789abcdef')

    def tearDown(self):
        self.modules.stop()
        self.paths.stop()
        self.temp.cleanup()

    def test_declared_plan_covers_all_required_observations(self):
        names = {name for name, action, capture in self.runtime.PLAN}
        self.assertFalse(harness.REQUIRED_OBSERVATIONS - names)
        self.assertIn("hotkeys.callback", names)
        self.assertEqual(self.vars["Phase1MenuComplete"], 0)

    def test_runtime_requires_explicit_valid_nonce(self):
        with self.assertRaises(TypeError): self.runtime.Configure(self.temp.name)
        for nonce in ('',None,'not-a-run','F'*32):
            with self.subTest(nonce=nonce):
                with self.assertRaises(ValueError): self.runtime.Configure(self.temp.name,nonce)

    def test_hotkey_runtime_passes_owned_nonce_through_real_shared_menu_configuration(self):
        nonce='0123456789abcdef0123456789abcdef'
        self.gem.GetSystemVariable=lambda key:self.temp.name
        Path(self.temp.name,'journey-input.json').write_text(json.dumps(dict(
            nonce=nonce,mode='hotkeys-edit',profile=self.temp.name)))
        with patch.dict(sys.modules,{'MenuRuntime':self.runtime}):
            hotkeys=load('hotkey_runtime_menu_nonce_test',HERE/'gui/HotkeyRuntime.py')
            hotkeys.Configure(self.temp.name,'hotkeys-edit',nonce)
        self.assertEqual(hotkeys.NONCE,nonce)
        self.assertEqual(self.runtime.NONCE,nonce)
        self.assertEqual([r[0] for r in self.runtime.PLAN],['initial'])

    def test_missing_hotkey_transition_fails_even_after_dispatch(self):
        self.gem.GetView = lambda *args: None
        self.runtime.inspect_hotkeys()
        self.assertFalse(self.runtime.ROWS[-1]["passed"])

    def test_callback_request_names_actual_native_control(self):
        item = types.SimpleNamespace(Flags=0, IsVisible=lambda: True)
        window = types.SimpleNamespace(IsVisible=lambda: True, GetControl=lambda cid: item)
        self.gem.GetView = lambda *args: window
        self.runtime.press("GUIOPT", 2, 7)
        self.assertEqual(self.vars["Phase1PressPack"], 1)
        self.assertEqual(self.vars["Phase1PressWindow"], 2)
        self.assertEqual(self.vars["Phase1PressControl"], 7)

    def test_spellbook_selects_real_eligible_actor_and_requests_ordinary_sidebar_callback(self):
        self.gem.GetPartySize=lambda:2
        self.gem.GetPlayerName=lambda pc,which:'Imoen' if pc==2 else 'Fighter'
        self.gem.GetKnownSpellsCount=lambda pc,kind,level:4 if (pc,kind,level)==(2,1,0) else 0
        self.gem.GetMemorizableSpellsCount=lambda *args:0
        selected=[]
        self.gem.GameSelectPCSingle=lambda pc:selected.append(pc)
        self.gem.GameControlGetTargetMode=lambda:0
        self.gem.GameGetFirstSelectedPC=lambda:2
        item=types.SimpleNamespace(Flags=0,Value=2,IsVisible=lambda:True)
        self.gem.GetView=lambda *args:types.SimpleNamespace(IsVisible=lambda:True,GetControl=lambda cid:item)
        with patch.dict(sys.modules,{'GUICommonWindows':types.SimpleNamespace(SelectionChangeHandler=None)}):
            self.runtime.select_spell_actor('mage-book',1,True)
        self.assertEqual(selected,[]) # Native callback has not dispatched yet.
        self.assertTrue(self.runtime.ROWS[-1]['applicable'])
        self.assertEqual(self.vars['Phase1PressPack'],self.runtime.PACKS.index('PORTWIN')+1)
        self.assertEqual(self.vars['Phase1PressControl'],1)
        self.runtime.open_spellbook('mage-book',5)
        self.assertEqual(selected,[2])
        self.assertEqual(self.vars['Phase1PressPack'],self.runtime.PACKS.index('OPTWIN')+1)
        self.assertEqual(self.vars['Phase1PressControl'],5)

    def test_sidebar_cannot_open_when_portrait_callback_left_fighter_selected(self):
        self.runtime.SPELL_ACTORS['priest-book']=3
        self.gem.GameGetFirstSelectedPC=lambda:1
        with self.assertRaisesRegex(RuntimeError,'did not select'):
            self.runtime.open_spellbook('priest-book',6)
        self.assertEqual(self.vars['Phase1PressPack'],0)

    def test_loader_selection_reset_is_rejected_before_content_contract(self):
        self.runtime.SPELL_ACTORS['priest-book']=3
        self.gem.GameGetSelectedPCSingle=lambda:1
        self.runtime.expect_window=lambda *args:None
        with self.assertRaisesRegex(RuntimeError,'different actor'):
            self.runtime.inspect_spellbook('priest-book','GUIPR')
        self.assertFalse(any(r.get('name','').endswith('content-contract') for r in self.runtime.ROWS))

    def test_targeting_mode_cannot_turn_portrait_selection_into_gameplay_action(self):
        self.gem.GetPartySize=lambda:1
        self.gem.GetPlayerName=lambda *args:'Imoen'
        self.gem.GetKnownSpellsCount=lambda *args:1
        self.gem.GetMemorizableSpellsCount=lambda *args:0
        self.gem.GameControlGetTargetMode=lambda:1
        with self.assertRaisesRegex(RuntimeError,'target instead of select'):
            self.runtime.select_spell_actor('mage-book',1,True)
        self.assertEqual(self.vars['Phase1PressPack'],0)

    def test_missing_required_wizard_fails_and_priest_context_does_not_force_an_opener(self):
        self.gem.GetPartySize=lambda:1
        self.gem.GetPlayerName=lambda *args:'Fighter'
        self.gem.GetKnownSpellsCount=lambda *args:0
        self.gem.GetMemorizableSpellsCount=lambda *args:0
        with self.assertRaisesRegex(RuntimeError,'real spellbook actor absent'):
            self.runtime.select_spell_actor('mage-book',1,True)
        self.runtime.select_spell_actor('priest-book',0,False)
        self.runtime.open_spellbook('priest-book',6)
        self.assertEqual(self.vars['Phase1PressPack'],0)
        self.runtime.inspect_spellbook('priest-book','GUIPR')
        self.assertIsNone(self.runtime.ROWS[-1]['passed'])
        self.assertEqual(self.runtime.ROWS[-1]['status'],'context-gated')


class SpellbookContentTests(unittest.TestCase):
    def test_real_populated_and_empty_controls_match(self):
        c,s,u=spell_fixture()
        self.assertTrue(all(r['passed'] for r in harness.validate_spellbook_capture(c,s,u)))

    def test_wrong_actor_even_with_right_name_label_fails(self):
        c,s,u=spell_fixture(); s['selection']=1
        self.assertFalse(all(r['passed'] for r in harness.validate_spellbook_capture(c,s,u)))

    def test_blank_wrong_stale_or_nonrendered_spell_cannot_pass(self):
        for field,value in (('stored_tooltip',''),('tooltip','Armor'),('value',0),('flags',0),
                            ('disabled',True),('picture_present',False),('picture_observable',False),
                            ('picture_size',[0,32]),('rect',[0,0,0,32])):
            with self.subTest(field=field):
                c,s,u=spell_fixture(); u['controls'][1][field]=value
                self.assertFalse(all(r['passed'] for r in harness.validate_spellbook_capture(c,s,u)))

    def test_empty_slot_retaining_old_visible_spell_fails(self):
        c,s,u=spell_fixture(); u['controls'][2]['flags']=2
        self.assertFalse(all(r['passed'] for r in harness.validate_spellbook_capture(c,s,u)))

    def test_missing_duplicate_hidden_control_fails_closed(self):
        for mode in ('missing','duplicate','hidden'):
            with self.subTest(mode=mode):
                c,s,u=spell_fixture()
                if mode=='missing': u['controls'].pop()
                elif mode=='duplicate': u['controls'].append(u['controls'][1])
                else: u['controls'][1]['visible']=False
                with self.assertRaisesRegex(ValueError,'spellbook control'):
                    harness.validate_spellbook_capture(c,s,u)


if __name__ == "__main__": unittest.main()
