"""Exercise actual source callback selection without importing a game runtime."""
import ast
from pathlib import Path
import types
import unittest
SOURCE=Path(__file__).resolve().parents[4]/'gemrb/GUIScripts'

def policy(pack):
    tree=ast.parse((SOURCE/(pack+'.py')).read_text(encoding='utf8'))
    candidates=[n for n in ast.walk(tree)if isinstance(n,ast.If)and any(isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr=='OnPress'and x.args and isinstance(x.args[0],ast.Name)and x.args[0].id=='Open'+('Mage'if pack=='GUIMG'else'Priest')+'SpellUnmemorizeWindow'for item in n.body for x in ast.walk(item))]
    # Match the direct callback-selection condition, not an enclosing loop/function.
    candidates=[n for n in candidates if any(isinstance(x,ast.Subscript)and isinstance(x.value,ast.Name)and x.value.id=='ms'for x in ast.walk(n.test))]
    if len(candidates)!=1:raise ValueError('Unique actual memorized callback policy absent')
    return tree,candidates[0]

class ConfirmationPolicyTests(unittest.TestCase):
    def test_actual_charged_callback_is_direct_only_for_bg2ee(self):
        for pack,role in (('GUIMG','Mage'),('GUIPR','Priest')):
            _,node=policy(pack);code=compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(SOURCE/(pack+'.py')),'exec')
            for ee,flags in ((True,1),(False,1),(True,0),(False,0)):
                called=[];direct=object();modal=object();scope=dict(ms={'Flags':flags},GameCheck=types.SimpleNamespace(IsBG2EE=lambda:ee),Button=types.SimpleNamespace(OnPress=called.append))
                scope['On'+role+'UnmemorizeSpell']=direct;scope['Open'+role+'SpellUnmemorizeWindow']=modal
                exec(code,scope)
                with self.subTest(pack=pack,ee=ee,flags=flags):self.assertEqual(called,[modal if flags and not ee else direct])
    def test_wizard_callback_policy_remains_inside_nonspontaneous_branch(self):
        tree,node=policy('GUIMG')
        guards=[n for n in ast.walk(tree)if isinstance(n,ast.If)and isinstance(n.test,ast.UnaryOp)and isinstance(n.test.op,ast.Not)and isinstance(n.test.operand,ast.Name)and n.test.operand.id=='Sorcerer'and any(x is node for child in n.body for x in ast.walk(child))]
        self.assertEqual(len(guards),1)
    def test_confirmation_functions_remain_available_for_classic(self):
        for pack,role in (('GUIMG','Mage'),('GUIPR','Priest')):
            tree,_=policy(pack);names={n.name for n in tree.body if isinstance(n,ast.FunctionDef)}
            self.assertIn('Open'+role+'SpellUnmemorizeWindow',names);self.assertIn('On'+role+'UnmemorizeSpell',names)

if __name__=='__main__':unittest.main()
