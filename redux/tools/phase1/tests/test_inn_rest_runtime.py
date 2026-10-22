"""Independent rest routes and fail-closed observations; no native launch."""
import importlib.util
from pathlib import Path
import sys,tempfile,types,json
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[1]/'InnRestRuntime.py'

class InnRestRuntimeContracts(unittest.TestCase):
    def runtime(self,root,mode='off',policy=None):
        self.vars={};self.gold=99;self.time=6000;self.option=int(mode=='on');self.visible={('GUISTORE',7)}
        button=types.SimpleNamespace(Flags=0,Value=0,IsVisible=lambda:True,QueryText=lambda:'prompt')
        window=types.SimpleNamespace(IsVisible=lambda:True,GetControl=lambda _:button)
        gem=types.SimpleNamespace(SetVar=lambda k,v:self.vars.__setitem__(k,v),GetVar=lambda k:self.option if k=='Over Confirm Everything'else self.vars.get(k),GetView=lambda p,w:window if(p,w)in self.visible else None,
            GetCurrentArea=lambda:'AR0704',GetPartySize=lambda:4,GameGetPartyGold=lambda:self.gold,GetGameTime=lambda:self.time,GetString=lambda _:'prompt',RestParty=lambda *args:dict(Error=False,Cutscene=False),GetStore=lambda:dict(StoreType=2,StoreName=33355,StoreButtons=[6],StoreRoomPrices=[1,6,10,16]))
        spec=importlib.util.spec_from_file_location('inn_rest_under_test',SOURCE);module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,GemRB=gem):spec.loader.exec_module(module)
        module.Configure(root,'a'*32,mode,policy or mode);return module

    def test_off_and_on_actual_fixed_routes_are_distinct(self):
        with tempfile.TemporaryDirectory()as root:
            off=self.runtime(root);on=self.runtime(root,'on')
            self.assertEqual([n for n,_ in off.PLAN],['loaded-inn','talk','response','dialogue-end','inn-room-page','room-zero','room-selected','rent','after-rest','store-done','closed'])
            self.assertEqual([n for n,_ in on.PLAN],['loaded-inn','settings.open','settings.gameplay','settings.feedback','settings.before-toggle','settings.toggle','settings.draft','settings.done','settings.committed','settings.gameplay-done','settings.return','talk','response','dialogue-end','inn-room-page','room-zero','room-selected','rent','confirmation','cancel','after-cancel','rent-again','confirmation-again','confirm','after-rest','store-done','closed'])
            self.visible.update({('OPTWIN',0),('GUIOPT',2),('GUIOPT',8),('GUIOPT',9),('GUISTORE',11),('GUISTORE',3)})
            names={'settings.open','settings.gameplay','settings.feedback','settings.toggle','settings.done','settings.gameplay-done','settings.return','talk','response','dialogue-end','room-zero','rent','cancel','rent-again','confirm','store-done'}
            on.REST_CALLS.append(dict(result=dict(Error=False,Cutscene=False)))
            for name,fn in on.PLAN:
                if name in names:fn()
            self.assertEqual([r['command']for r in on.ROWS if r['event']=='command-request'],[3,4,5])
            self.assertEqual([(r['pack'],r['window'],r['control'])for r in on.ROWS if r['event']=='request'],[('OPTWIN',0,7),('GUIOPT',2,9),('GUIOPT',8,5),('GUIOPT',9,41),('GUIOPT',9,26),('GUIOPT',8,7),('GUIOPT',2,11),('GUISTORE',7,0),('GUISTORE',7,11),('GUISTORE',11,1),('GUISTORE',7,11),('GUISTORE',11,0),('GUISTORE',3,0)])

    def test_rest_observation_requires_gold_option_and_actual_modal_boundary(self):
        with tempfile.TemporaryDirectory()as root:
            module=self.runtime(root);module.observe('after-rest',99,store=True)
            row=json.loads((Path(root)/'capture-1.inn.json').read_text(encoding='utf8'));self.assertEqual((row['gold'],row['option'],row['game_time']),(99,0,6000))
            for fault in('gold','option','modal','error','hidden-store'):
                self.gold=99;self.option=0;self.visible={('GUISTORE',7)}
                if fault=='gold':self.gold=100
                elif fault=='option':self.option=1
                elif fault=='modal':self.visible.add(('GUISTORE',11))
                elif fault=='error':self.visible.add(('GUISTORE',10))
                else:self.visible.clear()
                with self.subTest(fault=fault),self.assertRaises(RuntimeError):module.observe('after-rest',99,store=True)

    def test_reload_plan_does_not_request_talk_rest_or_setup(self):
        with tempfile.TemporaryDirectory()as root:
            for policy in('off','on'):
                module=self.runtime(root,'reload',policy)
                self.assertEqual([n for n,_ in module.PLAN],['reloaded-rest-save'])
            for command in(1,2,6):
                with self.assertRaises(RuntimeError):module.command(command)

    def test_invalid_mode_policy_and_nonce_are_rejected(self):
        with tempfile.TemporaryDirectory()as root:
            module=self.runtime(root)
            for mode,policy,nonce in(('off','on','a'*32),('on','off','a'*32),('prepare','off','a'*32),('off','off','A'*32)):
                with self.assertRaises(RuntimeError):module.Configure(root,nonce,mode,policy)

    def test_rest_trace_delegates_once_and_retains_exact_return_object(self):
        with tempfile.TemporaryDirectory()as root:
            module=self.runtime(root);self.gold=100;returned=dict(Error=False,Cutscene=True);calls=[]
            def original(*args):
                calls.append(args);self.gold=99;self.time+=2400;return returned
            module.BASE_REST=original
            self.assertIs(module.GemRB.RestParty(18,1,1),returned)
            self.assertEqual(calls,[(18,1,1)])
            row=json.loads((Path(root)/'rest-call.json').read_text(encoding='utf8'));self.assertEqual((row['gold_before'],row['gold_after'],row['time_after']-row['time_before']),(100,99,2400))
            with self.assertRaises(RuntimeError):module.GemRB.RestParty(18,1,1)
            self.assertEqual(calls,[(18,1,1)])

    def test_store_branch_requires_actual_rest_return_and_matching_visibility(self):
        with tempfile.TemporaryDirectory()as root:
            module=self.runtime(root)
            with self.assertRaises(RuntimeError):module.after_rest()
            module.REST_CALLS.append(dict(result=dict(Error=False,Cutscene=False)))
            module.after_rest();module.close_after_rest();self.assertEqual(module.ROWS[-1]['event'],'request')
            self.visible.clear()
            with self.assertRaises(RuntimeError):module.after_rest()
            module.REST_CALLS[0]['result']['Cutscene']=True
            module.after_rest();module.close_after_rest();self.assertEqual(module.ROWS[-1]['event'],'cutscene-store-already-closed')
            self.visible.add(('GUISTORE',7))
            with self.assertRaises(RuntimeError):module.after_rest()

if __name__=='__main__':unittest.main()
