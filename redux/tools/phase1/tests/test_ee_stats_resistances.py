"""Actual record assembly: zero protection is information, not an absent value."""
import ast
from pathlib import Path
import sys
import types
import unittest

SCRIPTS = Path(__file__).resolve().parents[4] / 'gemrb/GUIScripts'
sys.path.insert(0, str(SCRIPTS))
import ie_stats


def functions(filename, names, namespace):
    tree = ast.parse((SCRIPTS / filename).read_text(encoding='utf8'))
    tree.body = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    exec(compile(tree, filename, 'exec'), namespace)


class ResistancePresentationTests(unittest.TestCase):
    def setUp(self):
        self.values = {}
        self.game = types.SimpleNamespace(IsBG2OrEE=lambda: True,
            IsBG1=lambda: False, IsPST=lambda: False, IsIWD2=lambda: False,
            IsIWD1=lambda: False)
        gem = types.SimpleNamespace(GetString=lambda ref: 'label%d' % ref,
            GetPlayerStat=lambda pc, stat, base=0: self.values.get(stat, 0))
        self.env = dict(vars(ie_stats), GemRB=gem, GameCheck=self.game,
                        GS=lambda pc, stat: self.values.get(stat, 0))
        functions('GUIRECCommon.py', {'TypeSetStats'}, self.env)
        self.env['GUIRECCommon'] = types.SimpleNamespace(TypeSetStats=self.env['TypeSetStats'])
        functions('GUIREC.py', {'GetResistances'}, self.env)

    def test_ee_stats_lists_every_zero_resistance(self):
        text = self.env['GetResistances'](1, showZero=True)
        # Exact thirteen existing BG2 labels, including magic damage and poison.
        labels = (32213, 32222, 32214, 32223, 32220, 32221, 62146,
                  32233, 11767, 11768, 11769, 11770, 14017)
        for ref in labels:
            self.assertEqual(text.count('label%d: 0%%' % ref), 1)

    def test_negative_and_over_one_hundred_values_are_not_clamped(self):
        self.values.update({ie_stats.IE_RESISTFIRE: -25, ie_stats.IE_RESISTCOLD: 125})
        text = self.env['GetResistances'](1, showZero=True)
        self.assertIn('label32213: -25%', text)
        self.assertIn('label32214: 125%', text)
        self.assertIn('label11770: 0%', text)

    def test_default_record_path_still_omits_zero_resistances(self):
        self.values[ie_stats.IE_RESISTFIRE] = 25
        text = self.env['GetResistances'](1)
        self.assertIn('label32213: 25%', text)
        self.assertNotIn('label32214:', text)

    def test_default_formatter_keeps_existing_zero_filter(self):
        rows = [(32213, 0, '%'), (32214, -10, '%'), (32221, 0, '0')]
        text = self.env['TypeSetStats'](rows, 1)
        self.assertNotIn('label32213:', text)
        self.assertIn('label32214: -10%', text)
        self.assertIn('label32221: 0', text)

    def test_only_supplemental_ee_assembly_requests_zero_values(self):
        functions('GUIREC.py', {'GetSupplementalStats'}, self.env)
        for name in ('GetClassTitles', 'GetEffectIcons', 'GetLore', 'GetPartyReputation',
                     'GetActiveAIscript', 'GetSkills', 'GetSavingThrows', 'GetWeaponProficiencies'):
            self.env[name] = lambda *args: ''
        self.env['GUIRECCommon'].GetAbilityBonuses = lambda *args: []
        self.env['GUIRECCommon'].GetBonusSpells = lambda *args: ''
        result = self.env['GetSupplementalStats'](1, {})
        self.assertIn('label32213: 0%', result[3])


if __name__ == '__main__':
    unittest.main()
