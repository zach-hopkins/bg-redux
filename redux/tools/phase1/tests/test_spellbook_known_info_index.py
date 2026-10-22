"""Real BG2EE rendering/binding regression; no native or licensed resource use."""
import unittest
from test_ee_spellbook_information import Harness

ORIGINAL=('SPWI211','SPWI212','SPWI213','SPWI214')
EXPECTED={ref:index for index,ref in enumerate(ORIGINAL)}

class KnownSpellInfoIndexTests(unittest.TestCase):
    def check_order(self,order):
        h=Harness(ORIGINAL);h.render(order)
        # Invoke real helper closures, rather than reconstructing its expressions.
        # Expected storage identity stays fixed independently of displayed order.
        for display,ref in enumerate(order):
            with self.subTest(display=display,ref=ref):
                icon=h.window.GetControl(27+display)
                self.assertEqual(icon.icon,(ref,0));self.assertEqual(icon.tooltip,'name:'+ref)
                self.assertEqual(icon.Value,EXPECTED[ref])
                h.press(27+display,right=True)
                spell,kind=h.infos[-1]
                self.assertEqual(spell['SpellResRef'],ref)
                self.assertEqual(spell['CurrentIndex'],EXPECTED[ref])
                self.assertEqual(spell['CurrentIndex'],icon.Value)
                self.assertEqual(kind,'Known')
                h.press(27+display)
                self.assertEqual(h.operations[-1],EXPECTED[ref])
        self.assertEqual(len(h.infos),len(ORIGINAL))

    def test_identity_order(self):self.check_order(ORIGINAL)
    def test_reversed_display_order(self):self.check_order(tuple(reversed(ORIGINAL)))
    def test_original_index_two_displayed_first(self):self.check_order(('SPWI213','SPWI211','SPWI212','SPWI214'))
    def test_rotated_display_order(self):self.check_order(('SPWI212','SPWI213','SPWI214','SPWI211'))

if __name__=='__main__':unittest.main()
