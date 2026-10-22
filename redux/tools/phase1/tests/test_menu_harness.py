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


class MenuReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.runtime = dict(steps=10, planned_steps=10, context_required=["store"],
            checks=[dict(action=name, capture=i+1) for i, name in enumerate(sorted(harness.REQUIRED_OBSERVATIONS))] +
                   [dict(name="actual-hp", passed=True)])
        self.host = dict(completed=True, captures=len(harness.REQUIRED_OBSERVATIONS))
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
        self.save()

    def save(self):
        for name, data in (("menu-runtime", self.runtime), ("menu-host-result", self.host),
                           ("before.state", self.before), ("after.state", self.after)):
            harness.write(self.path / (name + ".json"), data)

    def tearDown(self): self.temp.cleanup()

    def test_selection_is_allowed_but_visual_rng_claims_remain_unproven(self):
        value = harness.validate_stage(self.path)
        self.assertTrue(value["assertion_passed"])
        self.assertTrue(value["collected_world_unchanged"])
        self.assertFalse(value["visual_acceptance"])
        self.assertIsNone(value["hidden_rng_unchanged"])

    def test_same_process_success_cannot_hide_changed_effects_or_ammo(self):
        self.after["ammo"] -= 1
        self.save()
        self.assertFalse(harness.validate_stage(self.path)["collected_world_unchanged"])

    def test_known_unimplemented_hotkey_failure_is_retained(self):
        self.runtime["checks"].append(dict(name="hotkeys.opens-real-window", passed=False))
        self.save()
        self.assertFalse(harness.validate_stage(self.path)["assertion_passed"])

    def test_visible_sheet_must_match_independent_native_cache(self):
        index = next(row["capture"] for row in self.runtime["checks"] if row.get("action") == "inventory.observed")
        harness.write(self.path / ("capture-%d.observer.json" % index), dict(actors=[dict(party_index=1, cached_thac0=9)]))
        value = harness.validate_stage(self.path)
        self.assertFalse(value["assertion_passed"])
        self.assertFalse(next(row["passed"] for row in value["checks"] if row["name"] == "inventory.observed.native-cached-thac0"))

    def test_missing_category_is_not_complete(self):
        self.runtime["checks"] = [row for row in self.runtime["checks"] if row.get("action") != "stats.observed-5"]
        self.save()
        with self.assertRaisesRegex(ValueError, "coverage"): harness.validate_stage(self.path)

    def test_capture_must_belong_to_observation_and_match_resolution(self):
        with self.assertRaisesRegex(ValueError, "resolution"): harness.validate_stage(self.path, (1024, 768))
        self.runtime["checks"][0].pop("capture")
        self.save()
        with self.assertRaisesRegex(ValueError, "lacks its capture"): harness.validate_stage(self.path)

    def test_duplicate_capture_and_incomplete_plan_rejected(self):
        self.runtime["checks"].append(dict(step=2, capture=1))
        self.save()
        with self.assertRaisesRegex(ValueError, "ambiguous"): harness.validate_stage(self.path)
        self.runtime["steps"] -= 1
        self.save()
        with self.assertRaisesRegex(ValueError, "incomplete"): harness.validate_stage(self.path)

    def test_truncated_or_absent_screenshot_rejected(self):
        (self.path / "capture-1.bmp").write_bytes(b"BM")
        with self.assertRaisesRegex(ValueError, "screenshot"): harness.validate_stage(self.path)
        (self.path / "capture-1.bmp").unlink()
        with self.assertRaises(OSError): harness.validate_stage(self.path)


class MenuRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.gem = types.ModuleType("GemRB")
        self.vars = {}
        self.gem.SetVar = lambda name, value: self.vars.update({name: value})
        self.gem.GetVar = lambda name: self.vars.get(name, 0)
        self.modules = patch.dict(sys.modules, {"GemRB": self.gem})
        self.modules.start()
        self.runtime = load("menu_runtime_test", HERE / "gui/MenuRuntime.py")
        self.temp = tempfile.TemporaryDirectory()
        self.runtime.Configure(self.temp.name)

    def tearDown(self):
        self.modules.stop()
        self.temp.cleanup()

    def test_declared_plan_covers_all_required_observations(self):
        names = {name for name, action, capture in self.runtime.PLAN}
        self.assertFalse(harness.REQUIRED_OBSERVATIONS - names)
        self.assertIn("hotkeys.callback", names)
        self.assertEqual(self.vars["Phase1MenuComplete"], 0)

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


if __name__ == "__main__": unittest.main()
