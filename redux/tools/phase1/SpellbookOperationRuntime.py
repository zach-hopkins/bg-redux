"""Ordinary spellbook controls only; the external host owns native dispatch."""
import importlib
import json
from pathlib import Path
import GemRB
from GUIDefines import IE_SPELL_TYPE_WIZARD, IE_SPELL_TYPE_PRIEST
PACKS=('PORTWIN','OPTWIN','GUIMG','GUIPR','GUIOPT','GUISAVE')
CASES=(dict(name='mage',pc=2,actor='Imoen',pack='GUIMG',kind=IE_SPELL_TYPE_WIZARD,level=1,ref='SPWI213',known=2,memo=0,modal=101,tabs=61,count=9,entry=5),dict(name='priest',pc=3,actor='Jaheira',pack='GUIPR',kind=IE_SPELL_TYPE_PRIEST,level=0,ref='SPPR113',known=4,memo=0,modal=5,tabs=55,count=7,entry=6))
OUTPUT=None
PLAN=[]
ROWS=[]
INDEX=0
CAPTURE=0
NONCE=None
MODE=None

def view(pack,window):
    item=GemRB.GetView(pack,window)
    return item if item and item.IsVisible()else None

def control(pack,window,cid):
    item=view(pack,window);item=item.GetControl(cid)if item else None
    if not item or not item.IsVisible():raise RuntimeError('Required actual control absent: %s/%s/%s'%(pack,window,cid))
    return item

def press(pack,window,cid,**binding):
    item=control(pack,window,cid)
    if item.Flags&(1<<29):raise RuntimeError('Actual requested control disabled')
    GemRB.SetVar('RDXBookPressPack',PACKS.index(pack)+1);GemRB.SetVar('RDXBookPressWindow',window);GemRB.SetVar('RDXBookPressControl',cid)
    ROWS.append(dict(event='request',step=INDEX,pack=pack,window=window,control=cid,value=item.Value,binding=binding))

def select(case):
    if GemRB.GameControlGetTargetMode()!=0 or importlib.import_module('GUICommonWindows').SelectionChangeHandler:raise RuntimeError('Not ordinary walking portrait selection')
    item=control('PORTWIN',0,case['pc']-1)
    if item.Value!=case['pc']:raise RuntimeError('Actual portrait binding differs')
    press('PORTWIN',0,case['pc']-1,actor=case['pc'],name=case['actor'])

def open_book(case):
    if GemRB.GameGetFirstSelectedPC()!=case['pc']:raise RuntimeError('Portrait did not select requested caster')
    GemRB.GameSelectPCSingle(case['pc'])
    press('OPTWIN',0,case['entry'],actor=case['pc'],route='ordinary spellbook toolbar entry')

def close_book(case):press('OPTWIN',0,case['entry'],actor=case['pc'],route='ordinary spellbook toolbar toggle')

def book(case):
    module=importlib.import_module(case['pack']);level=module.MageSpellLevel if case['pack']=='GUIMG'else module.PriestSpellLevel
    if GemRB.GameGetSelectedPCSingle()!=case['pc']or GemRB.GetPlayerName(case['pc'],0).casefold()!=case['actor'].casefold():raise RuntimeError('Actual selected caster identity differs')
    if GemRB.GetVar('MageSpellLevel'if case['pack']=='GUIMG'else'PriestSpellLevel')!=level:raise RuntimeError('Actual module/dictionary level disagree')
    rows=[]
    for index in range(GemRB.GetKnownSpellsCount(case['pc'],case['kind'],level)):
        spell=GemRB.GetKnownSpell(case['pc'],case['kind'],level,index);ref=spell['SpellResRef'];name=GemRB.GetString(GemRB.GetSpell(ref)['SpellName']);rows.append(dict(original_index=index,resref=ref.upper(),name=name))
    shown=sorted(rows,key=lambda r:r['name']);memorized=[]
    for i in range(GemRB.GetMemorizedSpellsCount(case['pc'],case['kind'],level,False)):
        row=GemRB.GetMemorizedSpell(case['pc'],case['kind'],level,i);memorized.append(dict(resref=row['SpellResRef'].upper(),flags=row['Flags']))
    return dict(actor=case['pc'],actor_name=GemRB.GetPlayerName(case['pc'],0),pack=case['pack'],kind=case['kind'],level=level,module=module.__file__,known=rows,shown=shown,memorized=memorized,slots=GemRB.GetMemorizableSpellsCount(case['pc'],case['kind'],level,1),label=control(case['pack'],2,0x10000032).QueryText())

def observe(case,name,level=None,modal=False):
    global CAPTURE
    row=book(case)
    if level is not None and row['level']!=level:raise RuntimeError('Shown spell level differs from declared navigation')
    if control(case['pack'],2,0x10000035).QueryText()!=row['actor_name']:raise RuntimeError('Shown caster name differs')
    for visible,spell in enumerate(row['shown']):
        item=control(case['pack'],2,27+visible)
        if item.Value!=spell['original_index']:raise RuntimeError('Sorted shown spell/original index/tooltip mismatch')
    if modal and not view(case['pack'],case['modal']):raise RuntimeError('Charged spell confirmation absent')
    if not modal and view(case['pack'],case['modal']):raise RuntimeError('Unexpected retained confirmation window')
    CAPTURE+=1;GemRB.SetVar('RDXBookCapture',CAPTURE)
    row.update(schema='bg-redux-book-observation/1',nonce=NONCE,name=name,capture=CAPTURE,step=INDEX,confirmation=bool(view(case['pack'],case['modal'])),tab_start=case['tabs'],tab_count=case['count'])
    (OUTPUT/('capture-%d.book.json'%CAPTURE)).write_text(json.dumps(row,indent=2)+'\n',encoding='utf8');ROWS.append(dict(event='observe',step=INDEX,name=name,capture=CAPTURE))

def tab(case,level):
    item=control(case['pack'],2,case['tabs']+level)
    if item.Value!=level:raise RuntimeError('Actual tab bound level differs')
    press(case['pack'],2,case['tabs']+level,level=level,route='tab')

def arrow(case,next_):press(case['pack'],2,2 if next_ else 1,route='next-arrow'if next_ else'previous-arrow')

def memo(case,depleted=False):
    row=book(case)
    if row['level']!=case['level']:raise RuntimeError('Operation at wrong actual level')
    index=len(row['memorized'])-1 if depleted else case['memo'];spell=row['memorized'][index]
    if spell['resref']!=case['ref']or spell['flags']!=(0 if depleted else 1):raise RuntimeError('Actual memorized target/charged state differs')
    item=control(case['pack'],2,3+index)
    if item.Value!=index:raise RuntimeError('Actual memorized button index differs')
    press(case['pack'],2,3+index,resref=case['ref'],memorized_index=index,flags=spell['flags'],route='depleted-no-confirm'if depleted else'charged-confirm')

def known(case):
    row=book(case);matches=[(i,r)for i,r in enumerate(row['shown'])if r['resref']==case['ref']]
    if row['level']!=case['level']or len(matches)!=1:raise RuntimeError('Target known spell missing/ambiguous')
    visible,spell=matches[0]
    if spell['original_index']!=case['known']:raise RuntimeError('Original known index differs from frozen parent')
    press(case['pack'],2,27+visible,resref=case['ref'],original_index=spell['original_index'],visible_index=visible,route='known-memorize')

def confirm(case,cancel):
    row=book(case);item=control(case['pack'],case['modal'],1 if cancel else 0)
    if not cancel and item.Value!=case['memo']:raise RuntimeError('Confirmation lost actual memorized index')
    press(case['pack'],case['modal'],1 if cancel else 0,resref=case['ref'],route='cancel-confirmation'if cancel else'confirm-unmemorize')

def add(name,fn):PLAN.append((name,fn))

def Configure(output,nonce,mode):
    global OUTPUT,NONCE,MODE,PLAN,ROWS,INDEX,CAPTURE
    if mode not in ('operate','reload')or len(nonce)!=32 or any(c not in'0123456789abcdef'for c in nonce):raise RuntimeError('Invalid private plan mode/nonce')
    OUTPUT=Path(output);NONCE=nonce;MODE=mode;PLAN=[];ROWS=[];INDEX=CAPTURE=0
    GemRB.SetVar('RDXBookComplete',0);GemRB.SetVar('RDXBookPressPack',0);GemRB.SetVar('RDXBookCapture',0)
    for case in CASES:
        name=case['name'];add(name+'.portrait',lambda c=case:select(c));add(name+'.open',lambda c=case:open_book(c))
        # Each arrow result is compared against an ordinary same-level tab reference.
        add(name+'.initial',lambda c=case:observe(c,c['name']+'.initial',0))
        for suffix,fn in [('next1',lambda c=case:arrow(c,True)),('arrow1',lambda c=case:observe(c,c['name']+'.arrow1',1)),('tab1-click',lambda c=case:tab(c,1)),('tab1',lambda c=case:observe(c,c['name']+'.tab1',1)),('previous0',lambda c=case:arrow(c,False)),('arrow0',lambda c=case:observe(c,c['name']+'.arrow0',0)),('tab0-click',lambda c=case:tab(c,0)),('tab0',lambda c=case:observe(c,c['name']+'.tab0',0)),('tab2-click',lambda c=case:tab(c,2)),('tab2',lambda c=case:observe(c,c['name']+'.tab2',2)),('previous1',lambda c=case:arrow(c,False)),('back1',lambda c=case:observe(c,c['name']+'.back1',1)),('tab1-repeat-click',lambda c=case:tab(c,1)),('tab1-repeat',lambda c=case:observe(c,c['name']+'.tab1-repeat',1)),('operation-level-click',lambda c=case:tab(c,c['level'])),('before',lambda c=case:observe(c,c['name']+'.before',c['level']))]:add(name+'.'+suffix,fn)
        if mode=='operate':
            for suffix,fn in [('charged-cancel-request',lambda c=case:memo(c)),('cancel-modal',lambda c=case:observe(c,c['name']+'.cancel-modal',c['level'],True)),('cancel',lambda c=case:confirm(c,True)),('after-cancel',lambda c=case:observe(c,c['name']+'.after-cancel',c['level'])),('charged-remove-request',lambda c=case:memo(c)),('remove-modal',lambda c=case:observe(c,c['name']+'.remove-modal',c['level'],True)),('confirm-remove',lambda c=case:confirm(c,False)),('after-remove',lambda c=case:observe(c,c['name']+'.after-remove',c['level'])),('known-add',lambda c=case:known(c)),('after-add',lambda c=case:observe(c,c['name']+'.after-add',c['level'])),('depleted-remove',lambda c=case:memo(c,True)),('after-depleted-remove',lambda c=case:observe(c,c['name']+'.after-depleted-remove',c['level'])),('known-readd',lambda c=case:known(c)),('final',lambda c=case:observe(c,c['name']+'.final',c['level']))]:add(name+'.'+suffix,fn)
        add(name+'.close',lambda c=case:close_book(c))
    add('leader-portrait',lambda:press('PORTWIN',0,0,actor=1,route='restore walking selection'))

def Step():
    global INDEX
    GemRB.SetVar('RDXBookPressPack',0);GemRB.SetVar('RDXBookCapture',0)
    if INDEX>=len(PLAN):GemRB.SetVar('RDXBookComplete',1)
    else:
        name,fn=PLAN[INDEX];GemRB.SetVar('RDXBookStep',INDEX);fn();INDEX+=1
    result=dict(schema='bg-redux-book-runtime/1',nonce=NONCE,mode=MODE,planned=[name for name,_ in PLAN],steps=INDEX,completed=INDEX==len(PLAN),rows=ROWS,sort_permutation_runtime_coverage=False)
    (OUTPUT/'book-runtime.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
