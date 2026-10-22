"""Source-only heading contracts; native geometry/font proof is a separate run."""
import ast
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


SCRIPTS = Path(__file__).resolve().parents[4] / 'gemrb/GUIScripts'
HEADING = 0x10000033


class Label:
    def __init__(self, x=295, width=275, y=490, height=30):
        self.source_frame = dict(x=x, y=y, w=width, h=height)
        self.frame = self.source_frame
        self.alignment = 'imported-center-middle'
        self.calls = []
        self.text = None
        self.visible = True

    def GetFrame(self): return self.frame
    def SetFrame(self, frame):
        self.calls.append(('frame', frame))
        self.frame = frame
    def SetFont(self, font): self.calls.append(('font', font))
    def SetColor(self, color): self.calls.append(('color', color))
    def SetText(self, text):
        self.calls.append(('text', text))
        self.text = text
    def SetVisible(self, visible):
        self.calls.append(('visible', visible))
        self.visible = visible


class Window:
    def __init__(self, label=None, origin=(80, 56), height=712, missing_heading=False):
        self.label = label or Label()
        self.origin = origin
        self.height = height
        self.controls = {}
        self.deleted = []
        self.missing_heading = missing_heading

    def GetControl(self, cid):
        if cid == HEADING:
            if self.missing_heading:
                return None
            if cid in self.deleted:
                raise AssertionError('The ordinary heading was deleted')
            return self.label
        return self.controls.setdefault(cid, MagicMock())

    def DeleteControl(self, cid): self.deleted.append(cid)
    def Focus(self): pass


def load_heading(ee=True, localized='Memorized'):
    game = types.ModuleType('GemRB')
    game.GetString = MagicMock(return_value=localized)
    check = types.ModuleType('GameCheck')
    check.IsBG2EE = MagicMock(return_value=ee)
    spec = importlib.util.spec_from_file_location('heading_under_test', SCRIPTS/'EESpellbookHeading.py')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, GemRB=game, GameCheck=check):
        spec.loader.exec_module(module)
    return module, game, check


def controller(filename, ee=True, spontaneous=False):
    """Execute the real Init/Update functions with ordinary engine queries faked.

    Other controls/callbacks are inert: this checks the real caller's heading
    lifecycle and count plumbing, not spell operations or the renderer.
    """
    heading, game, check = load_heading(ee)
    api = MagicMock()
    api.GameGetSelectedPCSingle.return_value = 2
    api.GetMemorizableSpellsCount.return_value = 7
    api.GetMemorizedSpellsCount.side_effect = lambda pc, book, level, ready: 1 if ready else 2
    api.GetKnownSpellsCount.return_value = 0
    api.GetMemorizedSpell.return_value = dict(SpellResRef='SPWI101', Flags=1)
    api.GetSpell.return_value = dict(SpellName=1)
    api.GetPlayerName.return_value = 'Selected Caster'
    check.IsBG2 = MagicMock(return_value=not ee)
    check.IsAnyEE = MagicMock(return_value=ee)
    check.IsBG2OrEE = MagicMock(return_value=True)
    check.IsBGEE = MagicMock(return_value=False)
    common = MagicMock()
    common.GetGUISpellButtonCount.return_value = 0
    book = MagicMock()
    book.HasSorcererBook.return_value = spontaneous
    namespace = dict(GemRB=api, GameCheck=check, GUICommon=common, Spellbook=book,
                     EESpellbookHeading=heading, Sorcerer=spontaneous,
                     MageSpellLevel=0, PriestSpellLevel=0, spellLevelOffset=None,
                     IE_SPELL_TYPE_WIZARD=1, IE_SPELL_TYPE_PRIEST=0)
    # GUIDefines is a constants-only source; no native module import is needed.
    exec(compile((SCRIPTS/'GUIDefines.py').read_text(encoding='utf8'), 'GUIDefines.py', 'exec'), namespace)
    tree = ast.parse((SCRIPTS/filename).read_text(encoding='utf8'))
    names = ('InitMageWindow', 'UpdateMageWindow') if filename == 'GUIMG.py' else ('InitPriestWindow', 'UpdatePriestWindow')
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    # Referenced callbacks outside these two functions are not dispatched here.
    for node in functions:
        for name in ast.walk(node):
            if isinstance(name, ast.Name) and isinstance(name.ctx, ast.Load) and name.id not in namespace:
                if name.id.startswith(('Open', 'On', 'Refresh', 'Mage', 'Priest')) or name.id == 'BindControlCallbackParams':
                    namespace[name.id] = MagicMock()
    exec(compile(ast.Module(body=functions, type_ignores=[]), filename, 'exec'), namespace)
    return namespace, names, api


class HeadingContracts(unittest.TestCase):
    def test_chu_geometry_is_copied_and_stays_above_prepared_row(self):
        heading, _, _ = load_heading()
        for x, width, old_y, old_h in ((295, 275, 490, 30), (295, 275, 489, 33), (17, 403, 10, 12)):
            label = Label(x, width, old_y, old_h)
            initial = dict(label.source_frame)
            window = Window(label)
            self.assertTrue(heading.Init(window))
            self.assertEqual(label.source_frame, initial)
            self.assertEqual((label.frame['x'], label.frame['w']), (x, width))
            self.assertEqual(label.alignment, 'imported-center-middle')
            self.assertGreaterEqual(label.frame['y'], 598)
            self.assertLess(label.frame['y'] + label.frame['h'], 644)
            self.assertLessEqual(label.frame['y'] + label.frame['h'], window.height)

    def test_window_origin_does_not_enter_relative_heading_coordinates(self):
        heading, _, _ = load_heading()
        frames = []
        for origin in ((80, 56), (208, 56), (208, 156)):
            window = Window(origin=origin)
            heading.Init(window)
            frames.append(window.label.frame)
        self.assertEqual(frames[0], frames[1])
        self.assertEqual(frames[1], frames[2])

    def test_uses_game_font_role_and_opaque_gray(self):
        heading, _, _ = load_heading()
        window = Window()
        heading.Init(window)
        self.assertIn(('font', 'STONESML'), window.label.calls)
        self.assertIn(('color', dict(r=206, g=206, b=206, a=255)), window.label.calls)

    def test_localized_allocated_count_refreshes_without_clamping(self):
        heading, game, _ = load_heading(localized='Mémorisés')
        window = Window()
        for memorized, capacity in ((4, 7), (0, 0), (2, 1)):
            heading.Update(window, memorized, capacity)
            self.assertEqual(window.label.text, 'Mémorisés: %d/%d' % (memorized, capacity))
        game.GetString.assert_called_with(11944)

    def test_classic_books_have_no_heading_side_effects(self):
        for ee, spontaneous in ((False, False), (False, True)):
            heading, game, _ = load_heading(ee)
            window = Window()
            self.assertFalse(heading.Init(window, spontaneous))
            self.assertFalse(heading.Update(window, 2, 7, spontaneous))
            self.assertEqual(window.label.calls, [])
            game.GetString.assert_not_called()

    def test_same_priest_window_hides_stale_count_and_restores_current_count(self):
        ns, names, api = controller('GUIPR.py')
        window = Window()
        ns[names[0]](window)
        ns[names[1]](window)
        self.assertTrue(window.label.visible)
        self.assertEqual(window.label.text, 'Memorized: 2/7')
        ns['Spellbook'].HasSorcererBook.return_value = True
        ns[names[1]](window)
        self.assertFalse(window.label.visible)
        self.assertEqual(window.label.text, 'Memorized: 2/7')  # retained but hidden
        ns['Spellbook'].HasSorcererBook.return_value = False
        api.GetMemorizedSpellsCount.side_effect = lambda pc, book, level, ready: 3
        api.GetMemorizableSpellsCount.return_value = 8
        ns[names[1]](window)
        self.assertTrue(window.label.visible)
        self.assertEqual(window.label.text, 'Memorized: 3/8')

    def test_separate_sorcerer_window_without_ordinary_label_is_supported(self):
        heading, game, _ = load_heading()
        window = Window(missing_heading=True)
        self.assertFalse(heading.Init(window, spontaneous=True))
        self.assertFalse(heading.Update(window, 2, 7, spontaneous=True))
        self.assertEqual(window.label.calls, [])
        game.GetString.assert_not_called()

    def test_ordinary_mage_init_retains_heading_and_refreshes_live_counts(self):
        ns, names, api = controller('GUIMG.py')
        window = Window()
        ns[names[0]](window)
        self.assertNotIn(HEADING, window.deleted)
        self.assertEqual(window.label.text, 'Memorized: 2/7')
        api.GetMemorizedSpellsCount.assert_any_call(2, ns['IE_SPELL_TYPE_WIZARD'], 0, False)
        api.GetMemorizedSpellsCount.side_effect = lambda pc, book, level, ready: 0
        api.GetMemorizableSpellsCount.return_value = 3
        ns[names[1]](window)
        self.assertEqual(window.label.text, 'Memorized: 0/3')

    def test_priest_refresh_uses_allocated_slots_and_existing_capacity(self):
        ns, names, api = controller('GUIPR.py')
        window = Window()
        ns[names[0]](window)
        ns[names[1]](window)
        self.assertEqual(window.label.text, 'Memorized: 2/7')
        api.GetMemorizedSpellsCount.assert_called_with(2, ns['IE_SPELL_TYPE_PRIEST'], 0, False)
        # The existing native export's omitted Bonus argument already defaults 1.
        api.GetMemorizableSpellsCount.assert_called_with(2, ns['IE_SPELL_TYPE_PRIEST'], 0)

    def test_actual_callers_preserve_classic_and_hide_only_ordinary_count(self):
        for filename in ('GUIMG.py', 'GUIPR.py'):
            for ee, spontaneous in ((False, False), (True, True)):
                ns, names, _ = controller(filename, ee, spontaneous)
                window = Window(missing_heading=filename == 'GUIMG.py' and spontaneous)
                ns[names[0]](window)
                ns[names[1]](window)
                if filename == 'GUIPR.py' and ee and spontaneous:
                    self.assertFalse(window.label.visible)
                    self.assertTrue(all(call == ('visible', False) for call in window.label.calls))
                else:
                    self.assertEqual(window.label.calls, [])
                if filename == 'GUIMG.py' and ee:
                    self.assertIn(59, window.deleted)


if __name__ == '__main__':
    unittest.main()
