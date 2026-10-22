import ast
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "gemrb/GUIScripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("KeyBindingEditor_test", SCRIPTS / "KeyBindingEditor.py")
editor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(editor)


class API:
    def __init__(self):
        self.current = {"inventory": "i", "map": "m", "journal": "j"}
        self.calls = []
    def GetKeyBindings(self):
        return [dict(name=name, key=key, default=dict(inventory="i", map="m", journal="j")[name]) for name, key in self.current.items()]
    def SetKeyBindings(self, values, dry=False):
        self.calls.append((dict(values), dry))
        if not dry: self.current = dict(values)


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.api = API()
        self.draft = editor.Draft(self.api.GetKeyBindings())
        self.temp = tempfile.TemporaryDirectory()
        self.profile = Path(self.temp.name)
        self.file = self.profile / "gemrb-keymap.ini"
    def tearDown(self): self.temp.cleanup()

    def test_assign_is_staged_cancel_requires_no_undo(self):
        self.draft.assign("inventory", "B")
        self.assertEqual(self.draft.working["inventory"], "b")
        self.assertEqual(self.api.current["inventory"], "i")
        self.assertFalse(self.file.exists())
        self.assertEqual(self.api.calls, [])

    def test_conflict_requires_explicit_replacement(self):
        with self.assertRaises(editor.BindingConflict): self.draft.assign("inventory", "m")
        self.assertEqual(self.draft.working, self.draft.original)
        self.draft.assign("inventory", "m", replace=True)
        self.assertEqual(self.draft.working["map"], "")
        self.assertEqual(self.draft.working["inventory"], "m")

    def test_clear_and_defaults_remain_staged(self):
        self.draft.assign("inventory", "")
        self.draft.assign("map", "b")
        self.draft.reset()
        self.assertEqual(self.draft.working, self.draft.defaults)
        self.assertFalse(self.file.exists())

    def test_fixed_modified_unicode_and_multichar_keys_rejected(self):
        for key in (" ", "1", "0", "-", "=", "F1", "ctrl+i", "é", "i\n", "\t"):
            with self.subTest(key=key), self.assertRaises(ValueError): self.draft.assign("inventory", key)

    def test_apply_saves_profile_and_rebinds_after_dry_run(self):
        self.draft.assign("inventory", "b")
        rebound = []
        self.draft.apply(self.api, self.profile, lambda values: rebound.append(dict(values)))
        self.assertEqual([dry for values, dry in self.api.calls], [True, False])
        self.assertEqual(rebound, [self.draft.working])
        self.assertEqual(self.api.current["inventory"], "b")
        self.assertIn("inventory=b\n", self.file.read_text())
        self.assertEqual(self.draft.original, self.api.current)
        self.assertFalse(list(self.profile.glob(".gemrb-keymap-*")))

    def test_stale_editor_rejected_before_persistence_or_native_apply(self):
        self.api.current["inventory"] = "c"
        with self.assertRaisesRegex(ValueError, "changed"): self.draft.apply(self.api, self.profile, lambda values: None)
        self.assertFalse(self.file.exists())
        self.assertEqual(self.api.calls, [])

    def test_native_validation_failure_preserves_file_and_live_routes(self):
        self.file.write_bytes(b"previous profile")
        self.api.SetKeyBindings = lambda *args: (_ for _ in ()).throw(ValueError("reserved by another action"))
        with self.assertRaises(ValueError): self.draft.apply(self.api, self.profile, lambda values: None)
        self.assertEqual(self.file.read_bytes(), b"previous profile")
        self.assertEqual(self.api.current["inventory"], "i")

    def test_atomic_write_failure_does_not_apply_runtime_changes(self):
        self.file.write_bytes(b"previous profile")
        with patch.object(editor.os, "replace", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError): self.draft.apply(self.api, self.profile, lambda values: None)
        self.assertEqual(self.file.read_bytes(), b"previous profile")
        self.assertEqual(self.api.current["inventory"], "i")
        self.assertEqual([dry for values, dry in self.api.calls], [True])
        self.assertFalse(list(self.profile.glob(".gemrb-keymap-*")))

    def test_rebind_failure_rolls_back_profile_and_live_mapping(self):
        self.file.write_bytes(b"previous profile")
        self.draft.assign("inventory", "b")
        rebound = []
        def rebind(values):
            rebound.append(dict(values))
            if values["inventory"] == "b": raise RuntimeError("binding failed")
        with self.assertRaises(RuntimeError): self.draft.apply(self.api, self.profile, rebind)
        self.assertEqual(self.api.current["inventory"], "i")
        self.assertEqual(self.file.read_bytes(), b"previous profile")
        self.assertEqual([values["inventory"] for values in rebound], ["b", "i"])

    def test_failed_first_apply_removes_new_profile_file(self):
        self.draft.assign("inventory", "b")
        def rebind(values):
            if values["inventory"] == "b": raise RuntimeError("binding failed")
        with self.assertRaises(RuntimeError): self.draft.apply(self.api, self.profile, rebind)
        self.assertFalse(self.file.exists())
        self.assertEqual(self.api.current["inventory"], "i")

    def test_rebind_clears_all_old_global_keys_before_swapping(self):
        tree = ast.parse((SCRIPTS / "MenuWindow.py").read_text(encoding="utf8"))
        tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "RebindNamedKeys"]
        calls = []
        buttons = {1: types.SimpleNamespace(SetHotKey=lambda key, *args: calls.append((1, key))),
                   2: types.SimpleNamespace(SetHotKey=lambda key, *args: calls.append((2, key)))}
        window = types.SimpleNamespace(GetControl=lambda cid: buttons[cid])
        env = dict(NamedKeyButtons={("GUIW", 0, 1): "inventory", ("GUIW", 0, 2): "map"},
                   GemRB=types.SimpleNamespace(GetView=lambda *args: window))
        exec(compile(tree, "MenuWindow.py", "exec"), env)
        env["RebindNamedKeys"]({"inventory": "m", "map": "i"})
        self.assertEqual(calls, [(1, None), (2, None), (1, "m"), (2, "i")])


class UIControl:
    def __init__(self): self.text, self.callback = "", None
    def SetText(self, value): self.text = value
    def QueryText(self): return self.text
    def SetFrame(self, frame): self.frame = frame
    def SetFont(self, value): self.font = value
    def SetVisible(self, value): self.visible = value
    def SetFlags(self, *args): pass
    def SetColor(self, *args): pass
    def SetBackground(self, *args): pass
    def SetState(self, value): self.state = value
    def OnPress(self, callback): self.callback = callback
    def Focus(self): self.focused = True


class UIWindow:
    def __init__(self):
        self.controls, self.closed, self.onclose = {}, False, None
        # Match the inherited overlay: a regression must replace its partial
        # opacity before presenting the editor, rather than hiding another UI.
        self.background = dict(r=0, g=0, b=0, a=180)
        self.background_at_show = None
    def GetControl(self, cid):
        if cid not in self.controls: self.controls[cid] = UIControl()
        return self.controls[cid]
    def CreateButton(self, cid, *args): return self.GetControl(cid)
    def CreateLabel(self, cid, *args): return self.GetControl(cid)
    def CreateTextArea(self, cid, *args):
        control = self.GetControl(cid)
        control.SetFont(args[-1])
        return control
    def GetFrame(self): return dict(w=1024, h=768)
    def AddAlias(self, *args): pass
    def OnClose(self, callback): self.onclose = callback
    def SetBackground(self, value): self.background = dict(value)
    def ShowModal(self, mode):
        self.background_at_show = dict(self.background)
        self.modal = True
    def Focus(self): pass
    def Close(self):
        self.closed = True
        if self.onclose: self.onclose()


class EditorUITests(unittest.TestCase):
    def setUp(self):
        self.api, self.window, self.rebound = API(), UIWindow(), []
        self.temp = tempfile.TemporaryDirectory()
        gem = types.ModuleType("GemRB")
        gem.GetKeyBindings, gem.SetKeyBindings = self.api.GetKeyBindings, self.api.SetKeyBindings
        gem.GetSystemVariable = lambda key: self.temp.name
        self.modules = patch.dict(sys.modules, {"GemRB": gem,
            "GUIOPTExtra": types.SimpleNamespace(PrepareBlankWindow=lambda *args: self.window),
            "MenuWindow": types.SimpleNamespace(RebindNamedKeys=lambda values: self.rebound.append(dict(values)))})
        self.modules.start()
        spec = importlib.util.spec_from_file_location("GUIHotkeys_test", SCRIPTS / "GUIHotkeys.py")
        self.ui = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ui)
        self.ui.Open()
    def tearDown(self):
        self.modules.stop()
        self.temp.cleanup()

    def test_real_assign_cancel_callbacks_do_not_apply_or_persist(self):
        self.ui.Select(self.ui.Names.index("inventory"))
        self.window.GetControl(6000).SetText("B")
        self.window.GetControl(6001).callback(self.window.GetControl(6001))
        self.assertEqual(self.ui.Editor.working["inventory"], "b")
        self.assertEqual(self.api.current["inventory"], "i")
        self.window.GetControl(14).callback()
        self.assertTrue(self.window.closed)
        self.assertIsNone(self.ui.Editor)
        self.assertFalse((Path(self.temp.name) / "gemrb-keymap.ini").exists())

    def test_full_viewport_editor_is_opaque_before_modal_at_both_resolutions(self):
        for width, height in ((1024, 768), (1280, 960)):
            with self.subTest(resolution=(width,height)):
                self.window.Close()
                self.window.GetFrame = lambda: dict(w=width,h=height)
                self.window.background = dict(r=0,g=0,b=0,a=180)
                self.window.background_at_show = None
                self.ui.Open()
                # The fill belongs to the full viewport, not a smaller stock
                # mosaic or child text field; it is opaque before ShowModal.
                self.assertEqual(self.window.GetFrame(),dict(w=width,h=height))
                self.assertEqual(self.window.background_at_show['a'],255)
                self.assertEqual(self.window.GetControl(6000).font,'NORMAL')
                self.assertEqual(self.window.GetControl(11).frame,dict(x=width-270,y=height-46,w=120,h=30))
                self.assertEqual(self.api.current['inventory'],'i')
                self.assertFalse((Path(self.temp.name)/'gemrb-keymap.ini').exists())

    def test_conflict_clear_defaults_and_apply_use_real_callbacks(self):
        self.ui.Select(self.ui.Names.index("inventory"))
        self.window.GetControl(6000).SetText("m")
        self.window.GetControl(6001).callback(self.window.GetControl(6001))
        self.assertIn("assigned", self.window.GetControl(15).text)
        self.assertEqual(self.ui.Editor.working["map"], "m")
        self.window.GetControl(6003).callback()
        self.assertEqual(self.ui.Editor.working["map"], "")
        self.window.GetControl(6002).callback()
        self.assertEqual(self.ui.Editor.working["inventory"], "")
        self.window.GetControl(6004).callback()
        self.assertEqual(self.ui.Editor.working["inventory"], "i")
        self.assertEqual(self.ui.Editor.working["map"], "m")
        self.window.GetControl(6000).SetText("B")
        self.window.GetControl(6001).callback(self.window.GetControl(6001))
        self.window.GetControl(11).callback()
        self.assertTrue(self.window.closed)
        self.assertEqual(self.api.current["inventory"], "b")
        self.assertEqual(self.rebound[0]["inventory"], "b")
        self.assertIn("inventory=b", (Path(self.temp.name) / "gemrb-keymap.ini").read_text())

    def test_actual_control_argument_does_not_replace_captured_row_or_page(self):
        # Enough real Draft entries to require another page; the supplied
        # button is an event argument, never an index or navigation delta.
        self.ui.Names = ['action%02d' % i for i in range(25)]
        self.ui.Editor.working = {name:'' for name in self.ui.Names}
        self.ui.Render()
        self.window.GetControl(5002).callback(self.window.GetControl(5002))
        self.assertEqual(self.ui.Selected,2)
        self.window.GetControl(6006).callback(self.window.GetControl(6006))
        self.assertEqual(self.ui.Page,1)
        self.assertEqual(self.ui.Selected,12)
        self.window.GetControl(6005).callback(self.window.GetControl(6005))
        self.assertEqual(self.ui.Page,0)
        self.assertEqual(self.ui.Selected,0)


if __name__ == "__main__": unittest.main()
