"""Unit/source contracts; no engine runtime, real settings writes or game assets."""
import ast
import configparser
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
HELPER = ROOT / "gemrb/GUIScripts/BG2EEConfirmation.py"


class ConfirmationSettingTests(unittest.TestCase):
    def setUp(self):
        self.variables = {"Over Confirm Everything": 0}
        self.spells = []
        self.saved = []
        self.queries = []
        self.save_success = True
        self.bg2ee = True
        gem = types.ModuleType("GemRB")
        gem.GetVar = lambda name: self.variables.get(name)
        gem.SetVar = lambda name, value: self.variables.__setitem__(name, value)
        def save():
            self.saved.append(dict(self.variables))
            return self.save_success
        gem.SaveConfig = save
        def count(pc, kind, level, castable):
            self.queries.append((pc, kind, level, castable))
            return len(self.spells)
        gem.GetMemorizedSpellsCount = count
        gem.GetMemorizedSpell = lambda pc, kind, level, index: dict(self.spells[index])
        game = types.ModuleType("GameCheck")
        game.IsBG2EE = lambda: self.bg2ee
        controls = types.ModuleType("GUIOPTControls")
        self.bound = []
        controls.OptCheckbox = lambda *args: self.bound.append(args)
        self.labels = []
        self.closed = 0
        label = types.SimpleNamespace(SetText=self.labels.append)
        def get_control(identifier):
            self.assertEqual(identifier, 0x10000028)
            return label
        def close():
            self.closed += 1
        self.window = types.SimpleNamespace(GetControl=get_control, Close=close)
        with patch.dict(sys.modules, GemRB=gem, GameCheck=game, GUIOPTControls=controls):
            spec = importlib.util.spec_from_file_location("confirmation_setting_under_test", HELPER)
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)

    def prompt(self):
        return self.module.ShouldPromptPreparedRemoval(2, 1, 1, "SPWI213")

    def test_off_and_missing_option_do_not_scan_page(self):
        self.assertFalse(self.prompt())
        self.variables.clear()
        self.assertFalse(self.prompt())
        self.assertEqual(self.queries, [])

    def test_on_without_depleted_same_spell_prompts(self):
        self.variables[self.module.OPTION] = 1
        self.spells = [{"SpellResRef": "SPWI213", "Flags": 1}]
        self.assertTrue(self.prompt())
        self.assertEqual(self.queries, [(2, 1, 1, False)])
        self.assertEqual(self.spells, [{"SpellResRef": "SPWI213", "Flags": 1}])
        self.assertEqual(self.saved, [])

    def test_on_same_resref_depleted_suppresses_case_insensitively(self):
        self.variables[self.module.OPTION] = 7
        self.spells = [{"SpellResRef": "SPWI213", "Flags": 1},
                       {"SpellResRef": "spwi213", "Flags": 0}]
        self.assertFalse(self.prompt())
        self.assertEqual(self.spells[0]["Flags"], 1)

    def test_other_depleted_spell_does_not_suppress(self):
        self.variables[self.module.OPTION] = 1
        self.spells = [{"SpellResRef": "SPWI214", "Flags": 0}]
        self.assertTrue(self.prompt())

    def test_nonzero_flags_are_not_depleted(self):
        self.variables[self.module.OPTION] = 1
        self.spells = [{"SpellResRef": "SPWI213", "Flags": 2}]
        self.assertTrue(self.prompt())

    def test_classic_keeps_prompt_without_option_or_page_access(self):
        self.bg2ee = False
        self.assertTrue(self.prompt())
        self.assertEqual(self.queries, [])

    def test_feedback_binds_draft_and_localized_existing_row(self):
        self.module.BeginFeedback(self.window)
        self.assertEqual(self.labels, [102476])
        self.assertEqual(self.bound, [(102477, 38, 39, 102476, self.module.DRAFT)])
        self.assertEqual(self.variables[self.module.OPTION], 0)
        self.assertEqual(self.variables[self.module.DRAFT], 0)
        self.assertEqual(self.saved, [])

    def test_done_writes_actual_option_before_persistent_save(self):
        done, cancel = self.module.BeginFeedback(self.window)
        self.variables[self.module.DRAFT] = 1
        done()
        self.assertEqual(self.variables[self.module.OPTION], 1)
        self.assertEqual(self.saved[0][self.module.OPTION], 1)
        self.assertEqual(self.closed, 1)
        self.assertIsNone(self.variables[self.module.DRAFT])

    def test_done_supports_turning_option_off(self):
        self.variables[self.module.OPTION] = 1
        done, cancel = self.module.BeginFeedback(self.window)
        self.variables[self.module.DRAFT] = 0
        done()
        self.assertEqual(self.saved[0][self.module.OPTION], 0)

    def test_cancel_discards_only_draft_without_save_or_legacy_rollback(self):
        self.variables["Effect Text Level"] = 126
        done, cancel = self.module.BeginFeedback(self.window)
        self.variables[self.module.DRAFT] = 1
        self.variables["Effect Text Level"] = 127
        cancel()
        self.assertEqual(self.variables[self.module.OPTION], 0)
        self.assertEqual(self.variables["Effect Text Level"], 127)
        self.assertEqual(self.saved, [])
        self.assertEqual(self.closed, 1)

    def test_save_failure_restores_dictionary_and_keeps_draft_open(self):
        self.save_success = False
        done, cancel = self.module.BeginFeedback(self.window)
        self.variables[self.module.DRAFT] = 1
        done()
        self.assertEqual(self.variables[self.module.OPTION], 0)
        self.assertEqual(self.variables[self.module.DRAFT], 1)
        self.assertEqual(self.closed, 0)

    def test_reopen_initializes_from_actual_not_stale_draft(self):
        self.variables[self.module.DRAFT] = 1
        self.module.BeginFeedback(self.window)
        self.assertEqual(self.variables[self.module.DRAFT], 0)

    def test_feedback_cannot_be_installed_for_other_games(self):
        self.bg2ee = False
        with self.assertRaises(ValueError):
            self.module.BeginFeedback(self.window)
        self.assertEqual(self.bound, [])

    def test_real_key_is_persisted_whitelist_and_draft_is_not(self):
        defaults = configparser.ConfigParser(inline_comment_prefixes=(";",))
        defaults.read(ROOT / "gemrb/unhardcoded/shared/defaults.ini", encoding="utf8")
        self.assertEqual(defaults.getint("Game Options", self.module.OPTION), 0)
        self.assertFalse(any(self.module.DRAFT in defaults[section] for section in defaults.sections()))
        core = (ROOT / "gemrb/core/Interface.cpp").read_text(encoding="utf8")
        initialize = core[core.index("bool Interface::InitializeVarsWithINI"):core.index("bool Interface::SaveConfig")]
        save = core[core.index("bool Interface::SaveConfig"):core.index("void Interface::SetCutSceneRunner")]
        self.assertIn('vars.Set(key, overrides->GetKeyAsInt(group.GetName(), key, value))', initialize)
        self.assertIn('for (auto& group : *defaultsINI)', save)
        self.assertIn('auto lookup = vars.Get(key)', save)

    def test_feedback_integration_is_bg2ee_gated_with_explicit_handlers(self):
        tree = ast.parse((ROOT / "gemrb/GUIScripts/GUIOPT.py").read_text(encoding="utf8"))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "OpenFeedbackOptionsWindow")
        gated = [n for n in ast.walk(function) if isinstance(n, ast.If) and isinstance(n.test, ast.Call)
                 and isinstance(n.test.func, ast.Attribute) and n.test.func.attr == "IsBG2EE"]
        self.assertEqual(len(gated), 1)
        self.assertIn("BG2EEConfirmation.BeginFeedback(Window)", ast.unparse(gated[0]))
        calls = [n for n in ast.walk(function) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        self.assertEqual([ast.unparse(n.args[0]) for n in calls if n.func.attr == "OptDone"], ["Done"])
        self.assertEqual([ast.unparse(n.args[0]) for n in calls if n.func.attr == "OptCancel"], ["Cancel"])


if __name__ == "__main__":
    unittest.main()
