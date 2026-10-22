"""Execute the real wizard known-row loop; no licensed resources or GemRB import."""
import ast
from pathlib import Path
import types
import unittest

SOURCE=Path(__file__).resolve().parents[4]/'gemrb/GUIScripts/GUIMG.py'
ORIGINAL=('SPWI211','SPWI212','SPWI213','SPWI214')
EXPECTED={ref:index for index,ref in enumerate(ORIGINAL)}

def rendering_loop():
    tree=ast.parse(SOURCE.read_text(encoding='utf8'))
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='UpdateMageWindow']
    if len(functions)!=1:raise ValueError('Actual UpdateMageWindow absent/ambiguous')
    loops=[]
    for node in ast.walk(functions[0]):
        if not isinstance(node,ast.For):continue
        # Locate the actual loop owning info-dialogue metadata, without imposing
        # the correct assignment expression or rebuilding that expression here.
        assignments=[child for child in node.body if isinstance(child,ast.Assign)]
        if any(isinstance(target,ast.Subscript)and isinstance(target.slice,ast.Constant)and target.slice.value=='CurrentIndex'for child in assignments for target in child.targets):loops.append(node)
    if len(loops)!=1:raise ValueError('Actual known-row info metadata loop absent/ambiguous')
    return compile(ast.fix_missing_locations(ast.Module(body=[loops[0]],type_ignores=[])),str(SOURCE),'exec')

class Button:
    VarName='Known'
    def __init__(self):self.value=None;self.icon=None;self.left=None;self.right=None;self.tooltip=None
    def SetValue(self,value):self.value=value
    def SetSpellIcon(self,ref,mode):self.icon=(ref,mode)
    def OnPress(self,callback):self.left=callback
    def OnRightPress(self,callback):self.right=callback
    def SetTooltip(self,text):self.tooltip=text

class KnownSpellInfoIndexTests(unittest.TestCase):
    def check_order(self,order):
        buttons={27+i:Button()for i in range(len(ORIGINAL))};opened=[]
        def info(spell,kind):opened.append((spell,kind))
        def bind(callback,*args):return lambda:callback(*args)
        left=object()
        # Original storage identity is fixed independently of the displayed order.
        # Fake GetSpell creates independent metadata objects like the real export.
        scope=dict(known_cnt=len(ORIGINAL),knownSpells=[({'SpellResRef':ref},EXPECTED[ref])for ref in order],
            MageWindow=types.SimpleNamespace(GetControl=buttons.__getitem__),
            GemRB=types.SimpleNamespace(GetSpell=lambda ref:dict(SpellResRef=ref,SpellName='name:'+ref)),
            BindControlCallbackParams=bind,OpenMageSpellInfoWindow=info,OnMageMemorizeSpell=left)
        exec(rendering_loop(),scope)
        for display,ref in enumerate(order):
            with self.subTest(display=display,ref=ref):
                button=buttons[27+display]
                self.assertEqual(button.icon,(ref,0));self.assertEqual(button.tooltip,'name:'+ref)
                self.assertEqual(button.value,EXPECTED[ref]);self.assertIs(button.left,left)
                button.right();spell,kind=opened[-1]
                self.assertEqual(spell['SpellResRef'],ref)
                self.assertEqual(spell['CurrentIndex'],EXPECTED[ref])
                self.assertEqual(spell['CurrentIndex'],button.value)
                self.assertEqual(kind,'Known')
        self.assertEqual(len(opened),len(ORIGINAL))

    def test_identity_order(self):self.check_order(ORIGINAL)
    def test_reversed_display_order(self):self.check_order(tuple(reversed(ORIGINAL)))
    def test_original_index_two_displayed_first(self):self.check_order(('SPWI213','SPWI211','SPWI212','SPWI214'))
    def test_rotated_display_order(self):self.check_order(('SPWI212','SPWI213','SPWI214','SPWI211'))

if __name__=='__main__':unittest.main()
