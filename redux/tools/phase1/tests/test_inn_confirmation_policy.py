"""Exercise the actual inn callbacks and shared setting with fake engine services."""
import ast
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock,patch

SOURCE=Path(__file__).resolve().parents[4]/'gemrb/GUIScripts'

class InnConfirmationPolicy(unittest.TestCase):
    def callbacks(self,ee=True,option=0,gold=100):
        values={'Over Confirm Everything':option,'RentIndex':0};calls=[]
        window=MagicMock();rent=MagicMock();stale=MagicMock()
        controls={i:MagicMock()for i in(0,1,3)}
        window.GetControl.side_effect=lambda i:controls[i]
        gem=types.SimpleNamespace(GetVar=lambda n:values.get(n),GameGetPartyGold=lambda:gold,
            GameSetPartyGold=lambda n:calls.append(('gold',n)),LoadWindow=lambda *a:(calls.append(('modal',a))or window),
            LoadTable=lambda n:types.SimpleNamespace(GetValue=lambda *a:1),RestParty=lambda *a:(calls.append(('rest',a))or dict(Cutscene=False,Error=False)),
            GetView=lambda n:rent,SetToken=lambda *a:None,SetVar=lambda n,v:values.__setitem__(n,v))
        spec=importlib.util.spec_from_file_location('inn_policy_helper',SOURCE/'BG2EEConfirmation.py');helper=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,GemRB=gem,GameCheck=types.SimpleNamespace(IsBG2EE=lambda:ee),GUIOPTControls=types.SimpleNamespace()):spec.loader.exec_module(helper)
        tree=ast.parse((SOURCE/'GUISTORE.py').read_text(encoding='utf8'));nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in('RentRoom','RentConfirm')]
        self.assertEqual(len(nodes),2)
        scope=dict(GemRB=gem,BG2EEConfirmation=helper,RentConfirmWindow=stale,Store={'StoreRoomPrices':[1,6,10,16]},windowIDs={'rentconfirm':11},strrefs={'roomtoocostly':11051,'rest':17199,'cancel':13727,'confirmrest':15358,'restedfor':16476},ErrorWindow=lambda ref:calls.append(('error',ref)),CloseStoreWindow=lambda:calls.append(('close-store',)),GTV_INT=0,IE_GUI_BUTTON_ENABLED=0,MODAL_SHADOW_GRAY=1)
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCE/'GUISTORE.py'),'exec'),scope)
        return scope,calls,window,stale,values

    def test_ee_off_rents_once_without_modal_or_stale_window_close(self):
        scope,calls,window,stale,values=self.callbacks();scope['RentRoom']()
        self.assertEqual(calls,[('gold',99),('rest',(18,1,1))]);stale.Close.assert_not_called();self.assertIsNone(values['RentIndex'])

    def test_ee_on_prompts_before_charge_and_cancel_never_rests(self):
        scope,calls,window,_,values=self.callbacks(option=1);scope['RentRoom']()
        self.assertEqual(calls,[('modal',(11,'GUISTORE'))])
        cancel=window.GetControl(1).OnPress.call_args.args[0];cancel()
        self.assertEqual(calls,[('modal',(11,'GUISTORE'))]);self.assertEqual(values['RentIndex'],0)

    def test_ee_on_confirm_uses_existing_single_charge_and_rest(self):
        scope,calls,window,_,_=self.callbacks(option=1);scope['RentRoom']()
        confirm=window.GetControl(0).OnPress.call_args.args[0];confirm(window)
        self.assertEqual(calls,[('modal',(11,'GUISTORE')),('gold',99),('rest',(18,1,1))]);window.Close.assert_called_once()

    def test_classic_keeps_prompt_even_when_ee_setting_is_off(self):
        scope,calls,_,_,_=self.callbacks(ee=False);scope['RentRoom']()
        self.assertEqual(calls,[('modal',(11,'GUISTORE'))])

    def test_price_failure_precedes_either_confirmation_path(self):
        for option in (0,1):
            scope,calls,_,_,_=self.callbacks(option=option,gold=0);scope['RentRoom']()
            with self.subTest(option=option):self.assertEqual(calls,[('error',11051)])

if __name__=='__main__':unittest.main()
