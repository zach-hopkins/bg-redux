"""External ordinary name/page/description callbacks; no production replacement."""
import json
from pathlib import Path
import GemRB
import SpellbookOperationRuntime as b

PLAN=[]
BUILT=False
NAME=0x7fff0400
UP,DOWN,COUNT,ACTION,TEXT,INFO_UP,INFO_DOWN=range(0x7fff0410,0x7fff0417)
SCROLL_REFS={'mage':'SPWI302','priest':'SPPR303'}

def add(name,fn):PLAN.append((name,fn))

def observe(case,name):
    row=b.book(case)
    if row['level']!=case['level']:raise RuntimeError('Actual observed information level differs')
    if b.control(case['pack'],2,0x10000035).QueryText()!=row['actor_name']:raise RuntimeError('Actual displayed name differs')
    for visible,spell in enumerate(row['information_page']['visible_rows']):
        if b.control(case['pack'],2,27+visible).Value!=spell['original_index']:raise RuntimeError('Visible original-index binding differs')
    if b.view(case['pack'],case['modal']):raise RuntimeError('Unexpected confirmation modal in default-off journey')
    option=GemRB.GetVar('Over Confirm Everything')
    if option!=0:raise RuntimeError('This bounded mutation journey requires actual default-off confirmation policy')
    b.CAPTURE+=1;GemRB.SetVar('RDXBookCapture',b.CAPTURE)
    row.update(schema='bg-redux-book-observation/2',nonce=b.NONCE,name=name,capture=b.CAPTURE,step=b.INDEX,
        confirmation=False,confirmation_option=option,tab_start=case['tabs'],tab_count=case['count'])
    (b.OUTPUT/('capture-%d.book.json'%b.CAPTURE)).write_text(json.dumps(row,indent=2)+'\n',encoding='utf8')
    b.ROWS.append(dict(event='observe',step=b.INDEX,name=name,capture=b.CAPTURE))

def named(case,index,route):
    row=b.book(case);shown=row['shown'];top=row['information_page']['top']
    matches=[i for i,r in enumerate(shown)if r['original_index']==index]
    if len(matches)!=1 or not top<=matches[0]<top+7:raise RuntimeError('Named target not on actual page')
    actual=shown[matches[0]]
    b.press(case['pack'],2,NAME+matches[0]-top,route=route,resref=actual['resref'],original_index=index,visible_index=matches[0]-top)

def separate(case):
    row=b.book(case);selected=row['information_page']['selected']
    if not selected or selected['resref']!=case['ref']or selected['original_index']!=case['known']:raise RuntimeError('Separate action selected another known identity')
    b.press(case['pack'],2,ACTION,route='separate-memorize',resref=selected['resref'],original_index=selected['original_index'])

def page(case,down):b.press(case['pack'],2,DOWN if down else UP,route='known-page-down'if down else'known-page-up')

def scroll(case,down):b.press(case['pack'],2,INFO_DOWN if down else INFO_UP,route='description-scroll-down'if down else'description-scroll-up')

def target_page(case):
    row=b.book(case);positions=[i for i,r in enumerate(row['shown'])if r['resref']==case['ref']]
    if len(positions)!=1 or positions[0]>=7:raise RuntimeError('Fixed mutation target requires initial visible page')

def BuildPlan():
    global BUILT
    if GemRB.GetPartySize()!=4:raise RuntimeError('Measured four-party input required')
    for case in b.CASES:
        name=case['name'];add(name+'.portrait',lambda c=case:b.select(c));add(name+'.open',lambda c=case:b.open_book(c))
        # Enumerated after ordinary load, before any command; no spell grants.
        levels=[]
        for level in range(case['count']):
            known=GemRB.GetKnownSpellsCount(case['pc'],case['kind'],level)
            if known:levels.append((level,known))
        if not levels or sum(n for _,n in levels)>256:raise RuntimeError('Natural known-spell inventory absent/unbounded')
        for level,total in levels:
            c=dict(case,level=level);prefix='%s.level%d'%(name,level)
            add(prefix+'.tab',lambda c=c:b.tab(c,c['level']))
            for top in range(0,total,7):
                p=prefix+'.page%d'%(top//7)
                if top:add(p+'.next',lambda c=c:page(c,True))
                add(p+'.default',lambda c=c,p=p:observe(c,p+'.default'))
                # Resolve the index only when this real page is displayed.
                def pick(c=c):
                    row=b.book(c);index=row['information_page']['visible_rows'][0]['original_index'];named(c,index,'name-select')
                def unpick(c=c):
                    selected=b.book(c)['information_page']['selected']
                    if not selected:raise RuntimeError('Name selection was lost before deselection')
                    named(c,selected['original_index'],'name-deselect')
                add(p+'.select',pick);add(p+'.selected',lambda c=c,p=p:observe(c,p+'.selected'))
                add(p+'.deselect',unpick);add(p+'.deselected',lambda c=c,p=p:observe(c,p+'.deselected'))
            # Same-level tab re-entry must reset the actual page/selection only
            # on a context change. Switch away and back through real tabs.
        entries=[]
        for index in range(GemRB.GetKnownSpellsCount(case['pc'],case['kind'],2)):
            ref=GemRB.GetKnownSpell(case['pc'],case['kind'],2,index)['SpellResRef']
            entries.append((GemRB.GetString(GemRB.GetSpell(ref)['SpellName']),ref.upper(),index))
        ordered=sorted(entries,key=lambda row:row[0]);matches=[(i,row)for i,row in enumerate(ordered)if row[1]==SCROLL_REFS[name]]
        if len(matches)!=1:raise RuntimeError('Natural long-description target absent/ambiguous')
        position,entry=matches[0];s=dict(case,level=2,ref=entry[1],known=entry[2]);prefix=name+'.scroll'
        add(prefix+'.tab-away',lambda s=s:b.tab(s,3))
        add(prefix+'.tab',lambda s=s:b.tab(s,2))
        for page_index in range(1,position//7+1):add(prefix+'.next%d'%page_index,lambda s=s:page(s,True))
        add(prefix+'.default',lambda s=s,prefix=prefix:observe(s,prefix+'.default'))
        add(prefix+'.select',lambda s=s:named(s,s['known'],'long-description-name-select'))
        add(prefix+'.selected',lambda s=s,prefix=prefix:observe(s,prefix+'.selected'))
        add(prefix+'.scroll-down',lambda s=s:scroll(s,True))
        add(prefix+'.scrolled',lambda s=s,prefix=prefix:observe(s,prefix+'.scrolled'))
        add(prefix+'.scroll-up',lambda s=s:scroll(s,False))
        add(prefix+'.restored',lambda s=s,prefix=prefix:observe(s,prefix+'.restored'))
        c=dict(case,level=case['level']);prefix=name+'.target'
        add(prefix+'.tab-away',lambda c=c:b.tab(c,(c['level']+1)%c['count']))
        add(prefix+'.tab',lambda c=c:b.tab(c,c['level']))
        add(prefix+'.default',lambda c=c,prefix=prefix:observe(c,prefix+'.default'))
        other_pc=1 if name=='mage'else 2
        other=dict(c,pc=other_pc,actor=GemRB.GetPlayerName(other_pc,0))
        add(prefix+'.other-portrait',lambda other=other:b.press('PORTWIN',0,other['pc']-1,actor=other['pc'],route='open-book actor context change'))
        add(prefix+'.other-actor',lambda other=other,prefix=prefix:observe(other,prefix+'.other-actor'))
        add(prefix+'.return-portrait',lambda c=c:b.press('PORTWIN',0,c['pc']-1,actor=c['pc'],route='restore ordinary book actor'))
        add(prefix+'.returned',lambda c=c,prefix=prefix:observe(c,prefix+'.returned'))
        add(prefix+'.assert-page',lambda c=c:target_page(c))
        add(prefix+'.select',lambda c=c:named(c,c['known'],'target-name-select'))
        add(prefix+'.selected',lambda c=c,prefix=prefix:observe(c,prefix+'.selected'))
        if b.MODE=='operate':
            add(prefix+'.remove',lambda c=c:b.memo(c))
            add(prefix+'.after-remove',lambda c=c,prefix=prefix:observe(c,prefix+'.after-remove'))
            add(prefix+'.separate',lambda c=c:separate(c))
            add(prefix+'.after-separate',lambda c=c,prefix=prefix:observe(c,prefix+'.after-separate'))
            # A full-page icon stays callable, but capacity must prevent a new
            # entry. The disabled separate action is observed, never forced.
            add(prefix+'.full-icon',lambda c=c:b.known(c))
            add(prefix+'.after-full-icon',lambda c=c,prefix=prefix:observe(c,prefix+'.after-full-icon'))
            add(prefix+'.remove-depleted',lambda c=c:b.memo(c,True))
            add(prefix+'.after-depleted',lambda c=c,prefix=prefix:observe(c,prefix+'.after-depleted'))
            add(prefix+'.icon',lambda c=c:b.known(c))
            add(prefix+'.final',lambda c=c,prefix=prefix:observe(c,prefix+'.final'))
        add(name+'.close',lambda c=case:b.close_book(c))
    add('leader-portrait',lambda:b.press('PORTWIN',0,0,actor=1,route='restore walking selection'))
    if len(PLAN)>650:raise RuntimeError('Information plan exceeds bounded callback inventory')
    BUILT=True

def Configure(output,nonce,mode,policy):
    global PLAN,BUILT
    if mode not in ('operate','reload')or policy!='ee-direct'or len(nonce)!=32 or any(c not in'0123456789abcdef'for c in nonce):raise RuntimeError('Explicit direct-policy information plan/nonce required')
    PLAN=[];BUILT=False
    b.OUTPUT=Path(output);b.NONCE=nonce;b.MODE=mode;b.POLICY=policy;b.ROWS=[];b.INDEX=b.CAPTURE=0
    GemRB.SetVar('RDXBookComplete',0);GemRB.SetVar('RDXBookPressPack',0);GemRB.SetVar('RDXBookCapture',0)

def Step():
    GemRB.SetVar('RDXBookPressPack',0);GemRB.SetVar('RDXBookCapture',0)
    if not BUILT:BuildPlan()
    if b.INDEX>=len(PLAN):GemRB.SetVar('RDXBookComplete',1)
    else:
        _,fn=PLAN[b.INDEX];GemRB.SetVar('RDXBookStep',b.INDEX);fn();b.INDEX+=1
    result=dict(schema='bg-redux-information-runtime/1',nonce=b.NONCE,mode=b.MODE,confirmation_policy=b.POLICY,
        planned=[name for name,_ in PLAN],steps=b.INDEX,completed=b.INDEX==len(PLAN),rows=b.ROWS,
        all_pages_coverage_owner='independent_external_validator',physical_pointer_input=False)
    (b.OUTPUT/'book-runtime.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
