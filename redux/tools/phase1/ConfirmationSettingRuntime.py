"""Separate normal confirmation/settings requests; no direct option/spell mutation."""
import importlib
import json
from pathlib import Path
import GemRB
PACKS=('PORTWIN','OPTWIN','GUIMG','GUIPR','GUIOPT','GUISAVE')
CASES=(dict(name='mage',pc=2,actor='Imoen',pack='GUIMG',kind=1,level=1,ref='SPWI213',known=2,filler='SPWI214',modal=101,tabs=61,entry=5),dict(name='priest',pc=3,actor='Jaheira',pack='GUIPR',kind=0,level=0,ref='SPPR113',known=4,filler='SPPR105',modal=5,tabs=55,entry=6))
OUTPUT=INI=None
PLAN=[]
ROWS=[]
INDEX=CAPTURE=0
NONCE=MODE=None


def view(pack,window):
    v=GemRB.GetView(pack,window)
    return v if v and v.IsVisible() else None


def control(pack,window,cid):
    v=view(pack,window);c=v.GetControl(cid) if v else None
    if not c or not c.IsVisible() or c.Flags&(1<<29):raise RuntimeError('Required enabled actual control absent')
    return c


def press(pack,window,cid,**binding):
    c=control(pack,window,cid)
    GemRB.SetVar('RDXBookPressPack',PACKS.index(pack)+1);GemRB.SetVar('RDXBookPressWindow',window);GemRB.SetVar('RDXBookPressControl',cid)
    ROWS.append(dict(event='request',step=INDEX,pack=pack,window=window,control=cid,value=c.Value,binding=binding))


def settings():
    return dict(option=GemRB.GetVar('Over Confirm Everything'),draft=GemRB.GetVar('BG2EE Confirmation Draft'),ini_exists=INI.is_file(),ini_text=INI.read_text(encoding='utf8') if INI.is_file() else None)


def book(case):
    module=importlib.import_module(case['pack']);level=module.MageSpellLevel if case['pack']=='GUIMG' else module.PriestSpellLevel
    if GemRB.GameGetSelectedPCSingle()!=case['pc'] or GemRB.GetPlayerName(case['pc'],0).casefold()!=case['actor'].casefold() or level!=case['level']:raise RuntimeError('Caster/level identity differs')
    if GemRB.GetVar('MageSpellLevel'if case['pack']=='GUIMG'else'PriestSpellLevel')!=level:raise RuntimeError('Module/dictionary page disagree')
    known=[]
    for i in range(GemRB.GetKnownSpellsCount(case['pc'],case['kind'],level)):
        ref=GemRB.GetKnownSpell(case['pc'],case['kind'],level,i)['SpellResRef'].upper();known.append(dict(original_index=i,resref=ref,name=GemRB.GetString(GemRB.GetSpell(ref)['SpellName'])))
    shown=sorted(known,key=lambda x:x['name']);panel=importlib.import_module('EESpellbookInformation').Panels.get(case['pack'])
    if not panel or not panel.active or panel.context[:3]!=(case['pc'],case['kind'],level):raise RuntimeError('Actual ordinary seven-row panel context absent')
    expected=[(case['pc'],case['kind'],level,x['resref'],x['original_index'],x['name'])for x in shown]
    if [(a,b,c,d.upper(),e,f)for a,b,c,d,e,f in panel.rows]!=expected:raise RuntimeError('Panel sorted identities disagree')
    visible=shown[panel.top:panel.top+7]
    for i,row in enumerate(visible):
        if control(case['pack'],2,27+i).Value!=row['original_index'] or control(case['pack'],2,0x7fff0400+i).Value!=row['original_index']:raise RuntimeError('Actual visible original index differs')
    memo=[]
    for i in range(GemRB.GetMemorizedSpellsCount(case['pc'],case['kind'],level,False)):
        s=GemRB.GetMemorizedSpell(case['pc'],case['kind'],level,i);memo.append(dict(resref=s['SpellResRef'].upper(),flags=s['Flags']))
    return dict(actor=case['pc'],actor_name=GemRB.GetPlayerName(case['pc'],0),pack=case['pack'],kind=case['kind'],level=level,module=module.__file__,known=known,shown=shown,visible=visible,top=panel.top,selected=panel.selected,generation=panel.generation,memorized=memo,slots=GemRB.GetMemorizableSpellsCount(case['pc'],case['kind'],level,1),label=control(case['pack'],2,0x10000032).QueryText(),heading=control(case['pack'],2,0x10000033).QueryText(),confirmation=bool(view(case['pack'],case['modal'])))


def observe(name,case=None):
    global CAPTURE
    CAPTURE+=1;row=dict(schema='bg-redux-confirmation-observation/1',nonce=NONCE,mode=MODE,step=INDEX,name=name,capture=CAPTURE,settings=settings())
    if case:row['book']=book(case)
    (OUTPUT/('capture-%d.book.json'%CAPTURE)).write_text(json.dumps(row,indent=2)+'\n',encoding='utf8');GemRB.SetVar('RDXBookCapture',CAPTURE);ROWS.append(dict(event='observe',step=INDEX,name=name,capture=CAPTURE))


def select(case):
    if importlib.import_module('GUICommonWindows').SelectionChangeHandler:raise RuntimeError('Portrait not in walking context')
    c=control('PORTWIN',0,case['pc']-1)
    if c.Value!=case['pc']:raise RuntimeError('Portrait PC differs')
    press('PORTWIN',0,case['pc']-1,actor=case['pc'])


def open_book(case):
    if GemRB.GameGetFirstSelectedPC()!=case['pc']:raise RuntimeError('Actual portrait selection differs')
    GemRB.GameSelectPCSingle(case['pc']);press('OPTWIN',0,case['entry'],actor=case['pc'])


def tab(case):
    c=control(case['pack'],2,case['tabs']+case['level'])
    if c.Value!=case['level']:raise RuntimeError('Actual tab binding differs')
    press(case['pack'],2,case['tabs']+case['level'],level=case['level'])


def memo(case,filler=False):
    row=book(case);ref=case['filler'] if filler else case['ref'];found=[(i,s)for i,s in enumerate(row['memorized'])if s['resref']==ref and s['flags']!=0]
    if not found:raise RuntimeError('Declared charged memo absent')
    index,spell=found[0];c=control(case['pack'],2,3+index)
    if c.Value!=index:raise RuntimeError('Actual memo original index differs')
    press(case['pack'],2,3+index,resref=ref,memo_index=index,flags=spell['flags'],route='charged-memorized')


def known(case,name_only=False):
    row=book(case);found=[(i,s)for i,s in enumerate(row['visible'])if s['resref']==case['ref']]
    if len(found)!=1 or found[0][1]['original_index']!=case['known']:raise RuntimeError('Target not in actual visible pool')
    i,s=found[0];press(case['pack'],2,(0x7fff0400 if name_only else 27)+i,resref=case['ref'],original_index=s['original_index'],visible_index=i,route='known-name'if name_only else'known-icon')


def memorize(case):
    row=book(case);c=control(case['pack'],2,0x7fff0413)
    if c.Value!=case['known'] or not row['selected']:raise RuntimeError('Separate Memorize is not bound to intended selection')
    press(case['pack'],2,0x7fff0413,resref=case['ref'],original_index=case['known'],route='selected-memorize')


def add(name,fn):PLAN.append((name,fn))


def Configure(output,nonce,mode,ini):
    global OUTPUT,INI,NONCE,MODE,PLAN,ROWS,INDEX,CAPTURE
    if mode not in ('operate','reload')or len(nonce)!=32 or any(c not in'0123456789abcdef'for c in nonce):raise RuntimeError('Explicit mode/nonce required')
    OUTPUT=Path(output);INI=Path(ini);NONCE=nonce;MODE=mode;PLAN=[];ROWS=[];INDEX=CAPTURE=0
    for key in('RDXBookComplete','RDXBookPressPack','RDXBookCapture','RDXBookRightPress'):GemRB.SetVar(key,0)
    add('settings.loaded',lambda:observe('settings.loaded'))
    if mode=='operate':
        for name,pack,win,cid in [('settings.open','OPTWIN',0,7),('settings.gameplay','GUIOPT',2,9),('settings.feedback','GUIOPT',8,5)]:add(name,lambda p=pack,w=win,c=cid:press(p,w,c))
        add('settings.draft-before',lambda:observe('settings.draft-before'))
        add('settings.toggle-cancel',lambda:press('GUIOPT',9,41,route='checkbox-mouse'))
        add('settings.draft-cancel',lambda:observe('settings.draft-cancel'))
        add('settings.cancel',lambda:press('GUIOPT',9,27));add('settings.after-cancel',lambda:observe('settings.after-cancel'))
        add('settings.feedback-again',lambda:press('GUIOPT',8,5));add('settings.toggle-done',lambda:press('GUIOPT',9,41,route='checkbox-mouse'))
        add('settings.draft-done',lambda:observe('settings.draft-done'));add('settings.done',lambda:press('GUIOPT',9,26));add('settings.after-done',lambda:observe('settings.after-done'))
        add('settings.gameplay-done',lambda:press('GUIOPT',8,7));add('settings.return',lambda:press('GUIOPT',2,11));add('settings.final',lambda:observe('settings.final'))
    for case in CASES:
        c=case;n=c['name'];add(n+'.portrait',lambda c=c:select(c));add(n+'.open',lambda c=c:open_book(c));add(n+'.level',lambda c=c:tab(c));add(n+'.before',lambda c=c,n=n:observe(n+'.before',c))
        if mode=='operate':
            add(n+'.target-request',lambda c=c:memo(c));add(n+'.target-modal',lambda c=c,n=n:observe(n+'.target-modal',c));add(n+'.cancel',lambda c=c:press(c['pack'],c['modal'],1));add(n+'.after-cancel',lambda c=c,n=n:observe(n+'.after-cancel',c))
            add(n+'.filler-request',lambda c=c:memo(c,True));add(n+'.filler-modal',lambda c=c,n=n:observe(n+'.filler-modal',c));add(n+'.confirm',lambda c=c:press(c['pack'],c['modal'],0));add(n+'.after-filler',lambda c=c,n=n:observe(n+'.after-filler',c))
            if n=='priest':
                add(n+'.known-select',lambda c=c:known(c,True));add(n+'.selected',lambda c=c,n=n:observe(n+'.selected',c));add(n+'.known-add',lambda c=c:memorize(c))
            else:add(n+'.known-add',lambda c=c:known(c))
            add(n+'.mixed-before',lambda c=c,n=n:observe(n+'.mixed-before',c));add(n+'.mixed-charged-click',lambda c=c:memo(c));add(n+'.after-mixed',lambda c=c,n=n:observe(n+'.after-mixed',c))
        add(n+'.close',lambda c=c:press('OPTWIN',0,c['entry']))
    add('leader-portrait',lambda:press('PORTWIN',0,0,actor=1))


def Step():
    global INDEX
    for key in('RDXBookPressPack','RDXBookCapture','RDXBookRightPress'):GemRB.SetVar(key,0)
    if INDEX>=len(PLAN):GemRB.SetVar('RDXBookComplete',1)
    else:
        name,fn=PLAN[INDEX];GemRB.SetVar('RDXBookStep',INDEX);fn();INDEX+=1
    (OUTPUT/'book-runtime.json').write_text(json.dumps(dict(schema='bg-redux-confirmation-runtime/1',nonce=NONCE,mode=MODE,planned=[n for n,_ in PLAN],steps=INDEX,completed=INDEX==len(PLAN),rows=ROWS),indent=2)+'\n',encoding='utf8')
