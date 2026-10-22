"""Actual Stats observer callbacks, without importing a native game process."""
import ast
from pathlib import Path
import types
import unittest


class StatsRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.presses = [], []
        def record(name, passed, **details):
            self.rows.append(dict(name=name, passed=passed, **details))
        self.menu = types.SimpleNamespace(PLAN=[('current', None, False)], INDEX=0, ROWS=[],
            record=record, inspect_sheet=lambda pack: None,
            press=lambda *args: self.presses.append(args),
            control=lambda *args: types.SimpleNamespace(Value=2, QueryText=lambda: 'page'))
        self.gem = types.SimpleNamespace(GetPartySize=lambda: 4, GameGetSelectedPCSingle=lambda: 2,
            GetVar=lambda key: 5 if key == 'ReduxStatsSection' else 0, GetPlayerName=lambda pc, kind: 'Imoen',
            GetPlayerStat=lambda pc, stat: 7, GetPlayerStates=lambda pc: bytearray())
        modules = dict(GUIREC=types.SimpleNamespace(GetSupplementalStats=lambda pc: ['raw']*6),
                       EECharacterSheet=types.SimpleNamespace(Pages=lambda raw: ['page']))
        self.env = dict(menu=self.menu, GemRB=self.gem, IE_CLASS=232, IE_LEVEL=34, IE_LEVEL2=68, IE_LEVEL3=69,
                        importlib=types.SimpleNamespace(import_module=lambda name: modules[name]))
        path = Path(__file__).resolve().parents[1] / 'gui/StatsRuntime.py'
        tree = ast.parse(path.read_text(encoding='utf8'))
        tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
        exec(compile(tree,str(path),'exec'),self.env)

    def test_selection_uses_separate_actor_name_and_assertion_name(self):
        self.env['Selected'](2)
        self.assertEqual(self.rows[0]['name'],'stats.actor-selected')
        self.assertEqual(self.rows[0]['actor_name'],'Imoen')
        self.assertTrue(self.rows[0]['passed'])

    def test_wrong_portrait_binding_is_rejected_before_dispatch(self):
        with self.assertRaisesRegex(RuntimeError,'Portrait control'):
            self.env['Portrait'](3)
        self.assertEqual(self.presses,[])
        self.env['Portrait'](2)
        self.assertEqual(self.presses,[('PORTWIN',0,1)])

    def test_fixture_cannot_silently_omit_a_party_member(self):
        self.gem.GetPartySize=lambda: 3
        with self.assertRaisesRegex(RuntimeError,'four-party'):
            self.env['Prepare']()

    def test_every_section_of_every_actor_has_distinct_capture_action(self):
        self.env['Prepare']()
        names = [r[0] for r in self.menu.PLAN]
        self.assertEqual(len(names),len(set(names)))
        for actor in range(1,5):
            self.assertIn('stats.actor-%d.portrait' % actor,names)
            for section in range(6):
                self.assertIn('stats.actor-%d.section-%d.observed' % (actor,section),names)
        self.assertEqual(names[-1],'stats.record.closed')


if __name__ == '__main__':
    unittest.main()
