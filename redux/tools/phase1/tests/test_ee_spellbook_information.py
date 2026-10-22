"""Resource-free real-helper behavior; native rendering/actions remain separate."""
import copy
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

SCRIPTS=Path(__file__).resolve().parents[4]/'gemrb/GUIScripts'

class Control:
    def __init__(self,cid,frame):
        self.ID=cid;self.frame=dict(frame);self.visible=True;self.flags=0;self.value=0
        self.state=0;self.text='';self.press=None;self.right=None;self.colors={};self.scroll=[]
    def GetFrame(self):return dict(self.frame)
    @property
    def Flags(self):return self.flags
    def SetFrame(self,frame):self.frame=dict(frame)
    def SetFlags(self,value,operation):self.flags=value
    def SetVisible(self,value):self.visible=value
    def SetFont(self,value):self.font=value
    def SetColor(self,value,index=0):self.colors[index]=value
    def SetSprites(self,*args):self.sprites=args
    def SetBackground(self,value):self.background=value
    def SetState(self,value):self.state=value
    def SetValue(self,value):self.value=value
    @property
    def Value(self):return self.value
    def SetSpellIcon(self,ref,mode):self.icon=(ref,mode)
    def SetTooltip(self,value):self.tooltip=value
    def SetText(self,value):self.text=value
    def OnPress(self,callback):self.press=callback
    def OnRightPress(self,callback):self.right=callback
    def ScrollTo(self,x,y):self.scroll.append(('absolute',x,y))
    def ScrollDelta(self,x,y):self.scroll.append(('relative',x,y))

class Window:
    def __init__(self,identity=2):
        self.ID=identity;self.visible=True;self.controls={}
        for i in range(24):self.controls[27+i]=Control(27+i,dict(x=160+i,y=198,w=54,h=54))
    def IsVisible(self):return self.visible
    def GetControl(self,cid):return self.controls.get(cid)
    def create(self,cid,x,y,w,h):
        if cid in self.controls:raise AssertionError('Duplicate control allocation')
        c=Control(cid,dict(x=x,y=y,w=w,h=h));self.controls[cid]=c;return c
    def CreateButton(self,cid,x,y,w,h):return self.create(cid,x,y,w,h)
    def CreateLabel(self,cid,x,y,w,h,font,text,alignment):
        c=self.create(cid,x,y,w,h);c.font=font;c.text=text;return c
    def CreateTextArea(self,cid,x,y,w,h,font):
        c=self.create(cid,x,y,w,h);c.font=font;return c

class Harness:
    def __init__(self,refs=None):
        self.original=list(refs or ('SPWI211','SPWI212','SPWI213','SPWI214'))
        self.window=Window();self.selected=2;self.level=1;self.capacity=3;self.allocated=0
        self.ee=True;self.spontaneous=False;self.eligible=True;self.alive=True;self.operations=[];self.infos=[]
        spec=importlib.util.spec_from_file_location('InformationTestDefines',SCRIPTS/'GUIDefines.py')
        defines=importlib.util.module_from_spec(spec);spec.loader.exec_module(defines)
        gemrb=types.SimpleNamespace(GetSpell=lambda ref:dict(SpellResRef=ref,SpellName='name:'+ref,SpellDesc='desc:'+ref),
            GetString=lambda ref:'Localized full instruction paragraph.' if ref==39254 else ref,
            GetPlayerName=lambda pc,_:'actor:'+str(pc),GameGetSelectedPCSingle=lambda:self.selected,
            GetKnownSpellsCount=lambda *args:len(self.original),GetKnownSpell=lambda pc,kind,level,index:dict(SpellResRef=self.original[index]),
            GetMemorizedSpellsCount=lambda *args:self.allocated,GetMemorizableSpellsCount=lambda *args:self.capacity,
            ValidTarget=lambda *args:self.alive,GetView=lambda *args:self.window)
        modules=dict(GemRB=gemrb,GameCheck=types.SimpleNamespace(IsBG2EE=lambda:self.ee),
            GUICommon=types.SimpleNamespace(CantUseSpellbookWindow=lambda *args:not self.eligible),
            Spellbook=types.SimpleNamespace(HasSorcererBook=lambda pc:self.spontaneous),GUIDefines=defines)
        spec=importlib.util.spec_from_file_location('InformationTestModule',SCRIPTS/'EESpellbookInformation.py')
        self.m=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,modules):spec.loader.exec_module(self.m)
        self.gemrb=gemrb
    def render(self,order=None,pack='GUIMG',pc=2):
        order=self.original if order is None else order;kind=1 if pack=='GUIMG' else 0
        self.selected=pc
        return self.m.Update(self.window,pack,pc,kind,self.level,[({'SpellResRef':ref},self.original.index(ref))for ref in order],self.spontaneous,
            lambda icon:self.operations.append(icon.Value),lambda *args:self.infos.append(args),lambda:self.level)
    def press(self,cid,right=False):
        c=self.window.GetControl(cid);fn=c.right if right else c.press
        if not c.visible or c.state==self.m.IE_GUI_BUTTON_DISABLED or not fn:raise AssertionError('Inactive control dispatched')
        fn(c)
    @property
    def panel(self):return next(iter(self.m.Panels.values()))

class SpellbookInformationTests(unittest.TestCase):
    def test_ineligible_book_keeps_full_help_without_enabling_actions(self):
        h=Harness();h.eligible=False;h.render()
        self.assertEqual(h.window.GetControl(h.m.INFORMATION).text,39254)
        self.assertEqual(h.window.GetControl(h.m.MEMORIZE).state,h.m.IE_GUI_BUTTON_DISABLED)
        h.press(27);h.press(h.m.NAME_BASE)
        self.assertEqual(h.operations,[]);self.assertIsNone(h.panel.selected)
    def test_initially_hidden_book_keeps_help_and_rejects_actions(self):
        h=Harness();h.window.visible=False;h.render()
        self.assertEqual(h.window.GetControl(h.m.INFORMATION).text,39254)
        self.assertEqual(h.window.GetControl(h.m.MEMORIZE).state,h.m.IE_GUI_BUTTON_DISABLED)
        h.press(27);h.press(h.m.NAME_BASE)
        self.assertEqual(h.operations,[]);self.assertIsNone(h.panel.selected)
    def test_select_and_deselect_names_never_memorize(self):
        h=Harness();h.render();h.press(h.m.NAME_BASE+2)
        self.assertEqual(h.operations,[]);self.assertIn('desc:SPWI213',h.window.GetControl(h.m.INFORMATION).text)
        self.assertEqual(h.panel.selected[4],2);h.press(h.m.NAME_BASE+2)
        self.assertEqual(h.operations,[]);self.assertIsNone(h.panel.selected)
        self.assertEqual(h.window.GetControl(h.m.INFORMATION).text,39254)
    def test_separate_memorize_and_icon_shortcut_use_original_identity(self):
        h=Harness();h.render(('SPWI213','SPWI211','SPWI212','SPWI214'))
        h.press(h.m.NAME_BASE);h.press(h.m.MEMORIZE);h.press(27)
        self.assertEqual(h.operations,[2,2])
    def test_live_capacity_and_eligibility_gate_old_enabled_action(self):
        h=Harness();h.render();h.press(h.m.NAME_BASE+2)
        self.assertEqual(h.window.GetControl(h.m.MEMORIZE).state,h.m.IE_GUI_BUTTON_ENABLED)
        for field,value in (('allocated',3),('eligible',False),('alive',False),('spontaneous',True)):
            original=getattr(h,field);setattr(h,field,value)
            h.press(h.m.MEMORIZE);h.press(29)
            self.assertEqual(h.operations,[]);setattr(h,field,original)
        h.allocated=3;h.render()
        self.assertEqual(h.window.GetControl(h.m.MEMORIZE).state,h.m.IE_GUI_BUTTON_DISABLED)
    def test_all_31_entries_reachable_without_more_icon_allocation(self):
        h=Harness(['SPELL%03d'%i for i in range(31)]);h.render();seen=[]
        while True:
            for i in range(h.m.ROWS):
                icon=h.window.GetControl(27+i)
                if icon.visible:
                    seen.append(icon.icon[0]);h.press(h.m.NAME_BASE+i,right=True)
            down=h.window.GetControl(h.m.PAGE_DOWN)
            if down.state==h.m.IE_GUI_BUTTON_DISABLED:break
            h.press(h.m.PAGE_DOWN)
        self.assertEqual(seen,h.original);self.assertEqual(len(h.infos),31)
        self.assertEqual([args[0]['CurrentIndex']for args in h.infos],list(range(31)))
        self.assertTrue(all(not h.window.GetControl(27+i).visible for i in range(7,24)))
        self.assertEqual(h.window.GetControl(h.m.PAGE_INFO).text,'5/5 (29-31/31)')
        h.press(h.m.PAGE_UP);self.assertEqual(h.panel.top,21)
    def test_paging_clears_selection_and_stale_closures(self):
        h=Harness(['SPELL%03d'%i for i in range(30)]);h.render();h.press(h.m.NAME_BASE)
        old=h.window.GetControl(h.m.MEMORIZE).press
        h.press(h.m.PAGE_DOWN);old(h.window.GetControl(h.m.MEMORIZE))
        self.assertIsNone(h.panel.selected);self.assertEqual(h.operations,[])
        self.assertEqual(h.window.GetControl(h.m.INFORMATION).text,39254)
    def test_actor_and_level_changes_clear_selection(self):
        h=Harness();h.render();h.press(h.m.NAME_BASE);old=h.window.GetControl(27).press
        h.level=2;old(h.window.GetControl(27));self.assertEqual(h.operations,[])
        h.render();self.assertIsNone(h.panel.selected)
        h.press(h.m.NAME_BASE);h.render(pc=3);self.assertIsNone(h.panel.selected)
    def test_known_storage_changed_before_callback_rejects_old_identity(self):
        h=Harness();h.render();old=h.window.GetControl(29).press
        h.original[2]='OTHER';old(h.window.GetControl(29));self.assertEqual(h.operations,[])
    def test_classic_untouched_and_spontaneous_restores_chu_frames(self):
        h=Harness();original=copy.deepcopy(h.window.GetControl(27).frame)
        h.ee=False;self.assertFalse(h.render());self.assertEqual(len(h.window.controls),24)
        h.ee=True;h.render();h.press(h.m.NAME_BASE)
        h.spontaneous=True;self.assertFalse(h.render())
        self.assertEqual(h.window.GetControl(27).frame,original)
        self.assertFalse(h.window.GetControl(h.m.INFORMATION).visible)
        h.spontaneous=False;h.render();self.assertIsNone(h.panel.selected)
        self.assertEqual(h.window.GetControl(h.m.INFORMATION).text,39254)
    def test_full_localized_help_and_description_have_real_scroll_actions(self):
        h=Harness();h.render()
        self.assertEqual(h.window.GetControl(h.m.INFORMATION).text,39254)
        h.press(h.m.INFO_DOWN);h.press(h.m.INFO_UP)
        self.assertEqual(h.window.GetControl(h.m.INFORMATION).scroll[-2:],[('relative',0,-250),('relative',0,250)])
        h.press(h.m.NAME_BASE);self.assertEqual(h.window.GetControl(h.m.INFORMATION).text,'name:SPWI211\n\ndesc:SPWI211')
        self.assertEqual(h.window.GetControl(h.m.MEMORIZE).text,17189)
    def test_missing_help_is_explicit_failure_not_english_substitution(self):
        h=Harness();h.gemrb.GetString=lambda ref:'' if ref==39254 else ref
        with self.assertRaisesRegex(RuntimeError,'39254'):h.render()
    def test_priest_selection_and_action_label(self):
        h=Harness();h.render(pack='GUIPR',pc=3);h.press(h.m.NAME_BASE+2)
        h.press(h.m.MEMORIZE);h.press(29,right=True)
        self.assertEqual(h.operations,[2]);self.assertEqual(len(h.infos[0]),1)
        self.assertEqual(h.window.GetControl(h.m.MEMORIZE).text,17224)
    def test_closed_or_reinitialized_window_rejects_old_callbacks(self):
        h=Harness();h.render();old=h.window.GetControl(27).press
        h.window.visible=False;old(h.window.GetControl(27));self.assertEqual(h.operations,[])
        h.window.visible=True;h.m.Reset(h.window,'GUIMG');old(h.window.GetControl(27));self.assertEqual(h.operations,[])
        h.render();h.press(h.m.NAME_BASE);self.assertIsNotNone(h.panel.selected)
    def test_empty_book_and_duplicate_names_keep_identity(self):
        h=Harness();h.original=[];h.render()
        self.assertEqual(h.window.GetControl(h.m.PAGE_INFO).text,'1/1 (0-0/0)')
        self.assertEqual(h.window.GetControl(h.m.MEMORIZE).state,h.m.IE_GUI_BUTTON_DISABLED)
        h.original=['A','B'];h.gemrb.GetString=lambda ref:'Same' if isinstance(ref,str)and ref.startswith('name:')else ref
        h.render(('B','A'));h.press(h.m.NAME_BASE);h.press(h.m.MEMORIZE)
        self.assertEqual(h.operations,[1])

if __name__=='__main__':unittest.main()
