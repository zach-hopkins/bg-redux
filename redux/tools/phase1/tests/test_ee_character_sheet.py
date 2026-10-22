"""Semantic/binding checks; native rendered fidelity is a separate required run."""
import copy
import ast
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "gemrb/GUIScripts"
sys.path.insert(0, str(SCRIPTS))
import ie_stats


class Control:
    def __init__(self):
        self.text = ""
        self.font = None
        self.frame = {"x": 533, "y": 345, "w": 45, "h": 44}
        self.tooltip = None
        self.callback = None
        self.font_slots = {}
        self.color_slots = {}
        self.style_at_text = None

    def SetText(self, value):
        self.text = value
        self.style_at_text = (dict(self.font_slots), dict(self.color_slots))
    def SetFont(self, value, which=0):
        self.font = value
        self.font_slots[which] = value
    def SetTooltip(self, value): self.tooltip = value
    def GetFrame(self): return dict(self.frame)
    def SetFrame(self, value): self.frame = dict(value)
    def SetFlags(self, *args): self.flags = args
    def SetBackground(self, value): self.background = value
    def SetDisabled(self, value): self.disabled = value
    def SetVisible(self, value): self.visible = value
    def SetState(self, value): self.state = value
    def SetColor(self, value, which=0):
        self.color = value
        self.color_slots[which] = value
    def OnPress(self, value): self.callback = value
    def ScrollTo(self, *args): self.scroll = args


class Window:
    def __init__(self): self.controls = {}
    def GetControl(self, cid):
        if cid not in self.controls: self.controls[cid] = Control()
        return self.controls[cid]
    def CreateButton(self, cid, *args): return self.GetControl(cid)
    def CreateLabel(self, cid, *args): return self.GetControl(cid)


def combat(**changes):
    result = dict(Slot=9, ToHitStats={"Total": 13, "Base": 17, "Ability": -2, "Generic": -2},
                  HitHeaderNumDice=1, HitHeaderDiceSides=8, HitHeaderDiceBonus=2,
                  DamageBonus=7, WeaponStrBonus=3, ProfDmgBon=2, LauncherDmgBon=1,
                  APR=5, DamageOpcodes=())
    result.update(changes)
    return result


class CharacterSheetTests(unittest.TestCase):
    def setUp(self):
        self.gem = types.ModuleType("GemRB")
        self.common = types.ModuleType("GUICommon")
        self.common.GetACStyleBonus = lambda pc, details=None: -1
        self.gem.GetString = lambda ref: {17183: "Armor Class", 17184: "Hit Points", 9457: "THAC0",
            10336: "Damage", 9458: "Attacks per round", 56910: "Off Hand THAC0", 56911: "Main Hand THAC0"}.get(ref, str(ref))
        self.hands = [combat(), combat(Slot=10, DamageBonus=1, WeaponStrBonus=2, ToHitStats={"Total": 19})]
        self.gem.GetCombatDetails = lambda pc, hand, displayOnly=False: copy.deepcopy(self.hands[hand])
        self.gem.IsDualWielding = lambda pc: False
        self.gem.GetSlotItem = lambda pc, slot, translated: {"Flags": 1}
        stats = {ie_stats.IE_ARMORCLASS: 2, ie_stats.IE_HITPOINTS: 20, ie_stats.IE_MAXHITPOINTS: 35}
        self.gem.GetPlayerStat = lambda pc, stat, base=0: (30 if stat == ie_stats.IE_MAXHITPOINTS and base else stats.get(stat, 0))
        self.modules = patch.dict(sys.modules, {"GemRB": self.gem, "GUICommon": self.common})
        self.modules.start()
        spec = importlib.util.spec_from_file_location("EECharacterSheet_test", SCRIPTS / "EECharacterSheet.py")
        self.sheet = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.sheet)

    def tearDown(self): self.modules.stop()

    def test_aggregate_damage_not_double_counted(self):
        self.assertEqual(self.sheet.DamageText(combat()), "1d8+10")
        self.assertEqual(self.sheet.DamageText(combat(DamageBonus=-5, WeaponStrBonus=2)), "1d8-3")
        self.assertEqual(self.sheet.DamageText(combat(HitHeaderNumDice=0, HitHeaderDiceSides=0)), "10")

    def test_unidentified_never_exposes_damage_or_effects(self):
        self.gem.GetSlotItem = lambda *args: {"Flags": 0}
        self.hands[0]["DamageOpcodes"] = ({"TypeName": "SECRET", "NumDice": 9, "DiceSides": 9, "DiceBonus": 0, "Chance": 100},)
        model = self.sheet.ReadActor(1)
        self.assertEqual(model["hands"][0]["damage"], "?")
        self.assertNotIn("SECRET", self.sheet.CombatTooltip(model))
        self.assertNotIn("1d8", self.sheet.CombatTooltip(model))

    def test_conditional_damage_not_folded_into_weapon_dice(self):
        self.hands[0]["DamageOpcodes"] = ({"TypeName": "Fire", "NumDice": 1, "DiceSides": 6, "DiceBonus": 0, "Chance": 25},)
        model = self.sheet.ReadActor(1)
        self.assertEqual(model["hands"][0]["damage"], "1d8+10")
        self.assertIn("Fire: 1d6+0 (25%)", self.sheet.CombatTooltip(model))

    def test_dual_hands_are_distinct_and_half_attacks_retained(self):
        self.gem.IsDualWielding = lambda pc: True
        model = self.sheet.ReadActor(1)
        self.assertEqual([h["thac0"] for h in model["hands"]], [13, 19])
        self.assertEqual([h["damage"] for h in model["hands"]], ["1d8+10", "1d8+3"])
        self.assertEqual(model["apr"], "2½")
        self.assertEqual(self.sheet.AttacksText(2), "1")

    def test_display_queries_do_not_need_main_hand_cache_restoration(self):
        calls = []
        def query(pc, hand, displayOnly=False):
            calls.append((hand, displayOnly))
            return copy.deepcopy(self.hands[hand])
        self.gem.GetCombatDetails = query
        self.sheet.Update(Window(), 1)
        self.assertEqual(calls, [(0, True)])
        calls.clear()
        self.gem.IsDualWielding = lambda pc: True
        self.sheet.Update(Window(), 1)
        self.assertEqual(calls, [(0, True), (1, True)])

    def test_record_display_preserves_script_stat_while_using_adjusted_total(self):
        state = {'script_thac0': 14}
        def query(pc, hand, displayOnly=False):
            if not displayOnly:
                state['script_thac0'] = 12
            return combat(ToHitStats={'Total': 12})
        self.gem.GetCombatDetails = query
        window = Window()
        self.sheet.Update(window, 1, record=True)
        self.assertEqual(window.GetControl(0x10000040).text, '12')
        self.assertEqual(state['script_thac0'], 14)

    def test_dead_or_missing_weapon_has_explicit_unavailable_value(self):
        self.hands[0] = {}
        model = self.sheet.ReadActor(1)
        self.assertEqual(model["hands"], [])
        self.assertEqual(model["apr"], "—")
        self.assertIn("—", self.sheet.PanelText(model)[2])

    def test_refresh_updates_existing_panels_after_equipment_change(self):
        window = Window()
        self.sheet.Update(window, 1)
        self.assertIn("13", window.GetControl(79).text)
        self.hands[0]["ToHitStats"]["Total"] = 9
        self.hands[0]["DamageBonus"] = 11
        self.sheet.Update(window, 1)
        self.assertEqual(window.GetControl(0x10000055).text, "9")
        self.assertEqual(window.GetControl(0x10000056).text, "1d8+14")
        self.assertEqual(window.GetControl(0x10000056).font, "NORMAL")
        self.assertEqual(window.GetControl(0x10000056).frame["w"], 78)
        self.assertEqual(window.GetControl(80).text.count("Attacks per round"), 1)

    def test_inventory_art_is_noninteractive_game_mosaic(self):
        window = Window()
        self.sheet.InitInventory(window)
        art = window.GetControl(0x7FFF0100)
        self.assertEqual(art.background, "INVSTATS")
        self.assertTrue(art.disabled)
        self.assertEqual(window.GetControl(77).font, "NORMAL")
        self.assertEqual(window.GetControl(0x10000055).font, 'NORMAL')
        self.assertEqual(window.GetControl(0x10000055).color, dict(r=215,g=215,b=215,a=255))

    def test_real_chu_black_body_and_dim_initials_are_overridden_before_new_spans(self):
        for record, panels in ((False,(77,78,79,80)), (True,(53,54,55,56))):
            with self.subTest(record=record):
                window=Window()
                for cid in panels:
                    control=window.GetControl(cid)
                    control.SetFont('STONESML')
                    control.SetFont('STONESML',1)
                    control.SetColor(dict(r=0,g=0,b=0,a=255),0)
                    control.SetColor(dict(r=64,g=64,b=64,a=255),1)
                self.sheet.Update(window,1,record=record)
                for cid in panels:
                    fonts,colors=window.GetControl(cid).style_at_text
                    self.assertEqual(fonts,{0:'NORMAL',1:'NORMAL'})
                    self.assertEqual(colors[0],dict(r=215,g=215,b=215,a=255))
                    self.assertEqual(colors[1],colors[0])

    def test_actual_tlk_thac0_hand_labels_do_not_mislabel_damage(self):
        model=self.sheet.ReadActor(1)
        self.assertIn('Main Hand THAC0',self.sheet.PanelText(model)[2])
        self.assertIn('Main hand: 1d8+10',self.sheet.PanelText(model)[3])
        self.assertNotIn('THAC0',self.sheet.PanelText(model)[3])
        self.assertNotIn('Hand THAC0:',self.sheet.CombatTooltip(model))

    def test_pages_preserve_every_long_record_token_with_bounded_rows(self):
        tokens = ["proficiency%03d" % i for i in range(100)]
        pages = self.sheet.Pages("[p]" + " ".join(tokens) + "[/p]")
        joined = " ".join(" ".join(pages).split())
        self.assertEqual(joined.split(), tokens)
        self.assertTrue(all(len(page.splitlines()) <= 12 for page in pages))
        self.assertTrue(all(len(line) <= 36 for page in pages for line in page.splitlines()))

    def test_pages_strip_record_markup_not_game_information(self):
        pages = self.sheet.Pages("[color=FFFFFF]Saves[/color][p]Death: 4\nSpell: 9[/p]")
        self.assertIn("Death: 4", pages[0])
        self.assertIn("Spell: 9", pages[0])
        self.assertNotIn("[", pages[0])
        self.assertEqual(self.sheet.Pages(""), ["—"])

    def test_unknown_ammunition_cannot_leak_its_damage_header(self):
        self.hands[0]["Flags"] = 2
        self.gem.GetEquippedAmmunition = lambda pc: 20
        self.gem.GetSlotItem = lambda pc, slot, translated=0: {"Flags": 0 if slot == 20 else 1}
        self.assertEqual(self.sheet.ReadActor(1)["hands"][0]["damage"], "?")

    def record_namespace(self):
        # Execute the real page/callback functions without importing unrelated
        # class/level-up subsystems that require a running game at import time.
        tree = ast.parse((SCRIPTS / "GUIREC.py").read_text(encoding="utf8"))
        names = {"InitEEStats", "SelectEEStats", "UpdateEEStats", "GetSupplementalStats"}
        tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
        self.vars = {}
        self.gem.GetVar = lambda key: self.vars.get(key, 0)
        self.gem.SetVar = lambda key, value: self.vars.update({key: value})
        self.gem.GameGetSelectedPCSingle = lambda: 1
        env = dict(vars(sys.modules["GUIDefines"]))
        env.update(GemRB=self.gem, EECharacterSheet=self.sheet)
        exec(compile(tree, "GUIREC.py", "exec"), env)
        return env

    def test_real_stats_buttons_select_distinct_sections_and_bound_pages(self):
        env = self.record_namespace()
        sections = ["row%d " % i + " ".join("value%03d" % x for x in range(100)) for i in range(6)]
        env["GetSupplementalStats"] = lambda pc, combat=None: sections
        window = Window()
        env["InitEEStats"](window)
        env["UpdateEEStats"](window, 1)
        self.assertTrue(window.GetControl(45).text.startswith("row0"))
        self.assertFalse(window.GetControl(46).visible)
        window.GetControl(0x7fff0214).callback(window.GetControl(0x7fff0214))
        self.assertEqual(self.vars["ReduxStatsSection"], 4)
        self.assertTrue(window.GetControl(45).text.startswith("row4"))
        window.GetControl(0x7fff0203).callback(window.GetControl(0x7fff0203))
        self.assertEqual(self.vars["ReduxStatsPage"], 1)
        window.GetControl(0x7fff0202).callback(window.GetControl(0x7fff0202))
        self.assertEqual(self.vars["ReduxStatsPage"], 0)
        self.vars["ReduxStatsPage"] = 999
        env["UpdateEEStats"](window, 1)
        self.assertEqual(self.vars["ReduxStatsPage"], len(self.sheet.Pages(sections[4])) - 1)

    def test_supplement_keeps_unique_abilities_excludes_repeated_headlines(self):
        env = self.record_namespace()
        for name in ("GetClassTitles", "GetEffectIcons", "GetLore", "GetPartyReputation", "GetActiveAIscript",
                     "GetSkills", "GetSavingThrows", "GetResistances", "GetWeaponProficiencies", "GetWeaponStyleBonuses"):
            env[name] = lambda *args, name=name, **kwargs: name
        rows = [(10332, 1, 'p'), (10336, 2, 'p'), (10339, 3, 'p'), (10340, 4, 'p'),
                (10337, 5, '0'), (10338, 6, '0'), (10342, 7, '0'), (10343, 8, '%')]
        env["GUIRECCommon"] = types.SimpleNamespace(GetAbilityBonuses=lambda *args: rows,
            TypeSetStats=lambda rows, pc: ",".join(str(row[0]) for row in rows),
            GetBonusSpells=lambda pc: "bonus spells")
        sections = env["GetSupplementalStats"](1)
        self.assertEqual(len(sections), 6)
        for ref in (10332, 10336, 10339, 10340): self.assertNotIn(str(ref), sections[5])
        for ref in (10337, 10338, 10342, 10343): self.assertIn(str(ref), sections[5])
        self.assertIn("bonus spells", sections[5])
        self.assertIn("GetWeaponStyleBonuses", sections[4])

    def test_supplement_uses_provided_snapshot_even_when_empty(self):
        env = self.record_namespace()
        for name in ("GetClassTitles", "GetEffectIcons", "GetLore", "GetPartyReputation", "GetActiveAIscript",
                     "GetSkills", "GetSavingThrows", "GetResistances", "GetWeaponProficiencies", "GetWeaponStyleBonuses"):
            env[name] = lambda *args, **kwargs: ""
        env["GUIRECCommon"] = types.SimpleNamespace(GetAbilityBonuses=lambda *args: [],
            TypeSetStats=lambda *args: "", GetBonusSpells=lambda *args: "")
        self.gem.GetCombatDetails = lambda *args: self.fail("unexpected repeated combat query")
        env["GetSupplementalStats"](1, {})
        env["GetSupplementalStats"](1, combat())

    def test_record_initialization_creates_stats_before_first_refresh(self):
        env = self.record_namespace()
        tree = ast.parse((SCRIPTS / "GUIREC.py").read_text(encoding="utf8"))
        tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "InitRecordsWindow"]
        env.update(GameCheck=types.SimpleNamespace(IsBG2EE=lambda: True, IsBG2OrEE=lambda: True),
                   DualClass=types.SimpleNamespace(DualClassWindow=lambda: None),
                   LevelUp=types.SimpleNamespace(OpenLevelUpWindow=lambda: None),
                   GUIRECCommon=types.SimpleNamespace(OpenCustomizeWindow=lambda: None, OpenExportWindow=lambda: None),
                   OpenInformationWindow=lambda: None, OpenRecReformPartyWindow=lambda: None,
                   OpenKitInfoWindow=lambda: None)
        window = Window()
        def refresh(view):
            self.assertIn(0x7fff0200, view.controls)
            self.assertIn(0x7fff0203, view.controls)
        env["UpdateActorDescription"] = refresh
        exec(compile(tree, "GUIREC.py", "exec"), env)
        env["InitRecordsWindow"](window)
        self.assertFalse(window.GetControl(0x1000003d).visible)


if __name__ == "__main__": unittest.main()
