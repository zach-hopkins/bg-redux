"""Ordinary spellbook controls only; the external host owns native dispatch."""
import importlib
import json
from pathlib import Path
import GemRB
from GUIDefines import IE_SPELL_TYPE_WIZARD, IE_SPELL_TYPE_PRIEST
PACKS=('PORTWIN','OPTWIN','GUIMG','GUIPR','GUIOPT','GUISAVE')
CASES=(dict(name='mage',pc=2,actor='Imoen',pack='GUIMG',kind=IE_SPELL_TYPE_WIZARD,level=1,ref='SPWI213',known=2,modal=101,tabs=61,count=9,entry=5),)
OUTPUT=None
PLAN=[]
ROWS=[]
INDEX=0
CAPTURE=0
NONCE=None
MODE=None
POLICY=None

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
    GemRB.SetVar('RDXBookRightPress',int(binding.get('action')=='RightPress'));GemRB.SetVar('RDXBookPressPack',PACKS.index(pack)+1);GemRB.SetVar('RDXBookPressWindow',window);GemRB.SetVar('RDXBookPressControl',cid)
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

def observe_known_page(pack, pc, kind, level, shown):
    helper=importlib.import_module('EESpellbookInformation')
    panel=helper.Panels.get(pack)
    if not panel or not panel.active or panel.context[:3]!=(pc,kind,level):
        raise RuntimeError('Actual ordinary information panel context absent')
    canonical=lambda r:dict(original_index=r[4],resref=r[3].upper(),name=r[5])
    if [canonical(r)for r in panel.rows]!=shown:
        raise RuntimeError('Helper rows disagree with independent full known-spell API list')
    selected=canonical(panel.selected)if panel.selected else None
    description_ref=GemRB.GetSpell(selected['resref'])['SpellDesc']if selected else None
    action=control(pack,2,0x7fff0413)
    return dict(schema='bg-redux-known-information-page/1',module=helper.__file__,pack=pack,actor=pc,kind=kind,level=level,
        page_size=7,top=panel.top,visible_rows=shown[panel.top:panel.top+7],selected=selected,
        default_help_strref=39254,resolved_help=GemRB.GetString(39254),
        selected_description_ref=description_ref,selected_description=GemRB.GetString(description_ref)if selected else None,
        information_text=control(pack,2,0x7fff0414).QueryText(),
        page_text=control(pack,2,0x7fff0412).QueryText(),
        action_strref=17189 if pack=='GUIMG'else 17224,
        resolved_action_label=GemRB.GetString(17189 if pack=='GUIMG'else 17224),
        action_text=action.QueryText(),action_value=action.Value,action_disabled=bool(action.Flags&(1<<29)),
        all_pages_visited=False,per_label_style_observed=False)

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
    return dict(actor=case['pc'],actor_name=GemRB.GetPlayerName(case['pc'],0),pack=case['pack'],kind=case['kind'],level=level,module=module.__file__,known=rows,shown=shown,memorized=memorized,slots=GemRB.GetMemorizableSpellsCount(case['pc'],case['kind'],level,1),label=control(case['pack'],2,0x10000032).QueryText(),information_page=observe_known_page(case['pack'],case['pc'],case['kind'],level,shown))

def observe(case,name,level=None,modal=False):
    global CAPTURE
    row=book(case)
    if level is not None and row['level']!=level:raise RuntimeError('Shown spell level differs from declared navigation')
    if control(case['pack'],2,0x10000035).QueryText()!=row['actor_name']:raise RuntimeError('Shown caster name differs')
    for visible,spell in enumerate(row['information_page']['visible_rows']):
        item=control(case['pack'],2,27+visible)
        if item.Value!=spell['original_index']:raise RuntimeError('Sorted shown spell/original index/tooltip mismatch')
    if modal and not view(case['pack'],case['modal']):raise RuntimeError('Charged spell confirmation absent')
    if not modal and view(case['pack'],case['modal']):raise RuntimeError('Unexpected retained confirmation window')
    CAPTURE+=1;GemRB.SetVar('RDXBookCapture',CAPTURE)
    row.update(schema='bg-redux-book-observation/2',nonce=NONCE,name=name,capture=CAPTURE,step=INDEX,confirmation=bool(view(case['pack'],case['modal'])),tab_start=case['tabs'],tab_count=case['count'])
    (OUTPUT/('capture-%d.book.json'%CAPTURE)).write_text(json.dumps(row,indent=2)+'\n',encoding='utf8');ROWS.append(dict(event='observe',step=INDEX,name=name,capture=CAPTURE))

def tab(case,level):
    item=control(case['pack'],2,case['tabs']+level)
    if item.Value!=level:raise RuntimeError('Actual tab bound level differs')
    press(case['pack'],2,case['tabs']+level,level=level,route='tab')

def add(name,fn):PLAN.append((name,fn))

def information():
    case=CASES[0];row=book(case)
    matches=[(i,s) for i,s in enumerate(row['shown']) if s['resref']==case['ref']]
    if row['level']!=1 or len(matches)!=1 or matches[0][1]['original_index']!=2:
        raise RuntimeError('Pinned SPWI213 original known index 2 absent')
    visible,spell=matches[0]
    top=row['information_page']['top']
    if not top<=visible<top+7:raise RuntimeError('Erase target is not on the actually observed page; paging journey required')
    visible-=top
    press('GUIMG',2,27+visible,action='RightPress',route='known-info',resref=case['ref'],original_index=2,visible_index=visible)

def capture(name):
    case=CASES[0]
    observe(case,name,1,modal=name.startswith('mage.confirmation'))
    path=OUTPUT/('capture-%d.book.json'%CAPTURE)
    row=json.loads(path.read_text(encoding='utf8'))
    row['information_visible']=bool(view('GUIMG',3))
    if row['information_visible']:
        row['information_name']=control('GUIMG',3,0x0fffffff).QueryText()
        row['information_description']=control('GUIMG',3,3).QueryText()
        row['erase_label']=control('GUIMG',3,6).QueryText()
    if view('GUIMG',101):
        row['confirmation_text']=control('GUIMG',101,3).QueryText()
    path.write_text(json.dumps(row,indent=2)+'\n',encoding='utf8')

def Configure(output,nonce,mode,policy):
    global OUTPUT,NONCE,MODE,POLICY,PLAN,ROWS,INDEX,CAPTURE
    if policy not in ('legacy-confirmation','ee-direct') or mode not in ('operate','reload'):
        raise RuntimeError('Explicit frozen mode/policy required')
    if len(nonce)!=32 or any(c not in '0123456789abcdef' for c in nonce):raise RuntimeError('Invalid nonce')
    OUTPUT=Path(output);NONCE=nonce;MODE=mode;POLICY=policy;PLAN=[];ROWS=[];INDEX=CAPTURE=0
    for key in ('RDXBookComplete','RDXBookPressPack','RDXBookCapture','RDXBookRightPress'):GemRB.SetVar(key,0)
    case=CASES[0]
    add('mage.portrait',lambda:select(case));add('mage.open',lambda:open_book(case))
    add('mage.level',lambda:tab(case,1));add('mage.before',lambda:capture('mage.before'))
    if mode=='operate':
        add('mage.info',information);add('mage.information',lambda:capture('mage.information'))
        add('mage.erase',lambda:press('GUIMG',3,6,route='erase-request'))
        add('mage.confirmation',lambda:capture('mage.confirmation'))
        add('mage.cancel',lambda:press('GUIMG',101,1,route='cancel-erase'))
        add('mage.after-cancel',lambda:capture('mage.after-cancel'))
        add('mage.erase-again',lambda:press('GUIMG',3,6,route='erase-request'))
        add('mage.confirmation-again',lambda:capture('mage.confirmation-again'))
        add('mage.confirm',lambda:press('GUIMG',101,0,route='confirm-erase'))
        add('mage.after-erase',lambda:capture('mage.after-erase'))
    add('mage.close',lambda:close_book(case))
    add('leader-portrait',lambda:press('PORTWIN',0,0,actor=1,route='restore walking selection'))

def Step():
    global INDEX
    for key in ('RDXBookPressPack','RDXBookCapture','RDXBookRightPress'):GemRB.SetVar(key,0)
    if INDEX>=len(PLAN):GemRB.SetVar('RDXBookComplete',1)
    else:
        name,fn=PLAN[INDEX];GemRB.SetVar('RDXBookStep',INDEX);fn();INDEX+=1
    row=dict(schema='bg-redux-book-runtime/1',nonce=NONCE,mode=MODE,confirmation_policy=POLICY,
             planned=[n for n,_ in PLAN],steps=INDEX,completed=INDEX==len(PLAN),rows=ROWS)
    (OUTPUT/'book-runtime.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8')
