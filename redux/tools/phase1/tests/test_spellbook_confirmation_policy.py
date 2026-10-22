"""Exercise actual source callback selection without importing a game runtime."""
import ast
import copy
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch
SOURCE=Path(__file__).resolve().parents[4]/'gemrb/GUIScripts'

def policy(pack):
    tree=ast.parse((SOURCE/(pack+'.py')).read_text(encoding='utf8'))
    candidates=[n for n in ast.walk(tree)if isinstance(n,ast.If)and any(isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr=='OnPress'and x.args and isinstance(x.args[0],ast.Name)and x.args[0].id=='Open'+('Mage'if pack=='GUIMG'else'Priest')+'SpellUnmemorizeWindow'for item in n.body for x in ast.walk(item))]
    # Match the direct callback-selection condition, not an enclosing loop/function.
    candidates=[n for n in candidates if any(isinstance(x,ast.Subscript)and isinstance(x.value,ast.Name)and x.value.id=='ms'for x in ast.walk(n.test))]
    if len(candidates)!=1:raise ValueError('Unique actual memorized callback policy absent')
    return tree,candidates[0]

class Page:
    def __init__(self,rows,ee=True,option=0):
        self.rows=copy.deepcopy(rows);self.calls=[];self.ee=ee;self.option=option
    def GetVar(self,name):
        if name!='Over Confirm Everything':raise AssertionError('Unexpected option')
        return self.option
    def GameGetSelectedPCSingle(self):return 2
    def GetMemorizedSpellsCount(self,*args):return len(self.rows)
    def GetMemorizedSpell(self,pc,kind,level,index):return copy.deepcopy(self.rows[index])
    def UnmemorizeSpell(self,pc,kind,level,index):
        self.calls.append((pc,kind,level,index));self.rows.pop(index);return True
    def PlaySound(self,sound):pass

def actual_helper(page):
    spec=importlib.util.spec_from_file_location('confirmation_under_test',SOURCE/'BG2EEConfirmation.py')
    module=importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules,dict(GemRB=page,GameCheck=types.SimpleNamespace(IsBG2EE=lambda:page.ee),GUIOPTControls=types.SimpleNamespace())):
        spec.loader.exec_module(module)
    return module

def actual_unmemorize(pack,page):
    role='Mage'if pack=='GUIMG'else'Priest';name='On'+role+'UnmemorizeSpell'
    tree=ast.parse((SOURCE/(pack+'.py')).read_text(encoding='utf8'))
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==name]
    if len(nodes)!=1:raise ValueError('Actual ordinary removal callback absent/ambiguous')
    window=MagicMock();scope=dict(GemRB=page,BG2EEConfirmation=actual_helper(page),MageSpellLevel=1,PriestSpellLevel=1,
        IE_SPELL_TYPE_WIZARD=1,IE_SPELL_TYPE_PRIEST=0,A_ANI_PLAYONCE=1,A_ANI_BLEND=2,FlashResRef='FLASHBR',
        MageWindow=window,PriestSpellWindow=window,UpdateMageWindow=lambda window:None,UpdatePriestWindow=lambda window:None)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCE/(pack+'.py')),'exec'),scope)
    return scope[name],window

def spell(ref='TARGET',flags=1):return dict(SpellResRef=ref,Flags=flags)

class ConfirmationPolicyTests(unittest.TestCase):
    def test_actual_callbacks_follow_option_and_same_ref_depleted_policy(self):
        for pack,role in (('GUIMG','Mage'),('GUIPR','Priest')):
            _,node=policy(pack);code=compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(SOURCE/(pack+'.py')),'exec')
            cases=[([spell()],True),([spell(),spell(flags=0)],False),([spell(),spell('OTHER',0)],True),([spell(flags=0)],False)]
            for ee in (False,True):
                for option in (0,1):
                    for rows,ee_prompt in cases:
                        page=Page(rows,ee,option);called=[];direct=object();modal=object()
                        scope=dict(ms=rows[0],pc=2,spelltype=1 if pack=='GUIMG'else 0,level=1,
                            BG2EEConfirmation=actual_helper(page),GameCheck=types.SimpleNamespace(IsBG2EE=lambda:ee),Button=types.SimpleNamespace(OnPress=called.append))
                        scope['On'+role+'UnmemorizeSpell']=direct;scope['Open'+role+'SpellUnmemorizeWindow']=modal
                        exec(code,scope)
                        expected=(bool(option)and ee_prompt)if ee else bool(rows[0]['Flags'])
                        with self.subTest(pack=pack,ee=ee,option=option,rows=rows):self.assertEqual(called,[modal if expected else direct])
    def test_wizard_callback_policy_remains_inside_nonspontaneous_branch(self):
        tree,node=policy('GUIMG')
        guards=[n for n in ast.walk(tree)if isinstance(n,ast.If)and isinstance(n.test,ast.UnaryOp)and isinstance(n.test.op,ast.Not)and isinstance(n.test.operand,ast.Name)and n.test.operand.id=='Sorcerer'and any(x is node for child in n.body for x in ast.walk(child))]
        self.assertEqual(len(guards),1)
    def test_confirmation_functions_remain_available_for_classic(self):
        for pack,role in (('GUIMG','Mage'),('GUIPR','Priest')):
            tree,_=policy(pack);names={n.name for n in tree.body if isinstance(n,ast.FunctionDef)}
            self.assertIn('Open'+role+'SpellUnmemorizeWindow',names);self.assertIn('On'+role+'UnmemorizeSpell',names)
    def test_actual_removal_consumes_preferred_depleted_copy_and_retains_charged(self):
        rows=[spell(),spell('OTHER',0),spell(flags=0),spell()]
        for pack in ('GUIMG','GUIPR'):
            for ee,index in ((True,2),(False,0)):
                page=Page(rows,ee,1);callback,window=actual_unmemorize(pack,page)
                callback(types.SimpleNamespace(Value=0))
                self.assertEqual(page.calls,[(2,1 if pack=='GUIMG'else 0,1,index)])
                self.assertEqual(page.rows,rows[:index]+rows[index+1:])
                self.assertEqual(sum(r['Flags']==1 and r['SpellResRef']=='TARGET'for r in page.rows),2 if ee else 1)
                window.GetControl.assert_called_with(index+3)
    def test_actual_removal_keeps_clicked_index_for_unrelated_depleted_copy(self):
        rows=[spell('OTHER',0),spell(),spell()]
        for pack in ('GUIMG','GUIPR'):
            page=Page(rows,True,1);callback,_=actual_unmemorize(pack,page)
            callback(types.SimpleNamespace(Value=2))
            self.assertEqual(page.calls[0][3],2);self.assertEqual(page.rows,rows[:2])
    def test_invalid_ee_index_never_calls_native_removal_or_animation(self):
        for pack in ('GUIMG','GUIPR'):
            for index in (-1,1):
                page=Page([spell()],True,1);callback,window=actual_unmemorize(pack,page)
                callback(types.SimpleNamespace(Value=index))
                self.assertEqual(page.calls,[]);self.assertEqual(page.rows,[spell()]);window.GetControl.assert_not_called()
    def test_confirmed_callback_rechecks_live_page_after_modal_open(self):
        for pack in ('GUIMG','GUIPR'):
            page=Page([spell()],True,1)
            self.assertTrue(actual_helper(page).ShouldPromptPreparedRemoval(2,1 if pack=='GUIMG'else 0,1,'TARGET'))
            callback,_=actual_unmemorize(pack,page);page.rows.append(spell(flags=0))
            callback(types.SimpleNamespace(Value=0))
            self.assertEqual(page.calls[0][3],1);self.assertEqual(page.rows,[spell()])

if __name__=='__main__':unittest.main()
