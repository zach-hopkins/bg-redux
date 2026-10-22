"""Exercise actual menu-observer traversal, including later-page corruption."""
import ast
from pathlib import Path
import types
import unittest

RUNTIME = Path(__file__).resolve().parents[1] / 'gui/MenuRuntime.py'


class StatsPageJourneyTests(unittest.TestCase):
    def setUp(self):
        self.page = 0
        self.actor = 1
        self.section = 3
        self.pages = ['Resistances\nFire: 0%', 'Cold: 0%', 'Poison: 0%']
        self.rows = []
        self.actions = []
        self.bad_text = False
        def control(pack, wid, cid):
            text = ('%d / %d' % (self.page + 1, len(self.pages)) if cid == 0x7fff0201
                    else 'corrupt' if self.bad_text else self.pages[self.page])
            return types.SimpleNamespace(QueryText=lambda: text)
        def press(pack, wid, cid):
            self.actions.append(cid)
            self.page += 1 if cid == 0x7fff0203 else -1
            self.assertTrue(0 <= self.page < len(self.pages))
        modules = dict(GUIREC=types.SimpleNamespace(GetSupplementalStats=lambda pc: ['']*6),
                       EECharacterSheet=types.SimpleNamespace(Pages=lambda content: self.pages))
        self.env = dict(PLAN=[], INDEX=0, control=control, press=press,
            record=lambda name, passed, **details: self.rows.append(dict(name=name, passed=passed, **details)),
            importlib=types.SimpleNamespace(import_module=lambda name: modules[name]),
            GemRB=types.SimpleNamespace(GetVar=lambda name: self.section,
                                       GameGetSelectedPCSingle=lambda: self.actor))
        tree = ast.parse(RUNTIME.read_text(encoding='utf8'))
        tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name in ('inspect_stats', 'expect_page')]
        exec(compile(tree, str(RUNTIME), 'exec'), self.env)

    def test_all_natural_pages_are_captured_and_return_to_first(self):
        self.env['inspect_stats'](3)
        for name, action, capture in self.env['PLAN']:
            action()
        transitions = [row for row in self.rows if row['name'] == 'stats.page-transition']
        self.assertEqual([row['expected'] for row in transitions], [2, 3, 2, 1])
        self.assertEqual(self.actions, [0x7fff0203]*2 + [0x7fff0202]*2)
        self.assertTrue(all(row['passed'] for row in self.rows))
        self.assertEqual(self.page, 0)

    def test_later_page_wrong_content_fails_even_with_correct_page_number(self):
        self.page = 2
        self.bad_text = True
        self.env['expect_page'](3, 3, 1, self.pages)
        self.assertFalse(self.rows[-1]['passed'])

    def test_actor_change_cannot_pass_as_the_same_record(self):
        self.actor = 2
        self.env['expect_page'](1, 3, 1, self.pages)
        self.assertFalse(self.rows[-1]['passed'])

    def test_single_page_has_no_disabled_button_dispatch(self):
        self.pages = self.pages[:1]
        self.env['inspect_stats'](3)
        self.assertEqual(self.env['PLAN'], [])
        self.assertTrue(all(row['passed'] for row in self.rows))


if __name__ == '__main__':
    unittest.main()
