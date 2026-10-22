"""Independent spellbook operation evidence contracts; never imports GemRB."""
import copy
from collections import Counter
import hashlib
from pathlib import Path
import struct
import saved_npc_color_fixtures as binary
import weapon_query_validation as evidence
CASES=(dict(name='mage',pc=2,pack='GUIMG',kind=1,level=1,ref='SPWI213',known=2,memo=0,modal=101,tabs=61,count=9),dict(name='priest',pc=3,pack='GUIPR',kind=0,level=0,ref='SPPR113',known=4,memo=0,modal=5,tabs=55,count=7))
NAV=('portrait','open','initial','next1','arrow1','tab1-click','tab1','previous0','arrow0','tab0-click','tab0','tab2-click','tab2','previous1','back1','tab1-repeat-click','tab1-repeat','operation-level-click','before')
OPERATIONS=('charged-cancel-request','cancel-modal','cancel','after-cancel','charged-remove-request','remove-modal','confirm-remove','after-remove','known-add','after-add','depleted-remove','after-depleted-remove','known-readd','final')

def expected_plan(mode):
    if mode not in ('operate','reload'):raise ValueError('Unsupported mode')
    return [c['name']+'.'+step for c in CASES for step in NAV+(OPERATIONS if mode=='operate'else())+('close',)]+['leader-portrait']

def page(actor,kind,level):
    rows=[r for r in actor['spellbook']if r['type']==kind and r['level']==level]
    if len(rows)!=1:raise ValueError('Missing/duplicate actual spellbook page')
    return rows[0]

def spells(rows):return [(r['resref'].upper(),r['flags'])for r in rows]

def stage_delta(before,after,case,phase):
    a=page(before['party'][case['pc']-1],case['kind'],case['level']);b=page(after['party'][case['pc']-1],case['kind'],case['level']);original=spells(a['memorized'])
    if not original or original[case['memo']]!=(case['ref'],1):raise ValueError('Declared charged original spell absent')
    if phase in ('cancel-modal','after-cancel','remove-modal','before'):expected=original
    elif phase in ('after-remove','after-depleted-remove'):expected=original[:case['memo']]+original[case['memo']+1:]
    elif phase in ('after-add','final'):expected=original[:case['memo']]+original[case['memo']+1:]+[(case['ref'],0)]
    else:raise ValueError('Unsupported declared delta phase')
    if spells(b['memorized'])!=expected:raise ValueError('Actual memorized resref/order/charged state differs: '+phase)
    left=copy.deepcopy(a);right=copy.deepcopy(b);left.pop('memorized');right.pop('memorized')
    if left!=right:raise ValueError('Known spells/slots/page metadata changed')

def caster_surfaces(state):
    """Do not normalize conflicting party/map spellbook observations away."""
    for case in CASES:
        actor=state['party'][case['pc']-1]
        matches=[row for row in state['current_area_actors']if row['runtime_id']==actor['runtime_id']]
        if len(matches)!=1 or matches[0]['spellbook']!=actor['spellbook']:
            raise ValueError('Caster spellbook disagrees between party and current-area surfaces')

def declared_world_delta(before,after,operated):
    evidence.require_state(before);evidence.require_state(after);caster_surfaces(before);caster_surfaces(after)
    left=copy.deepcopy(before);right=copy.deepcopy(after)
    # Actual portrait selection is allowed; no broad time/effect/global normalization.
    left.pop('selection');right.pop('selection')
    identities=[a['script_name'].casefold()for a in left['party']]
    if identities!=['none','imoen','jaheira','minsc']or [a['script_name'].casefold()for a in right['party']]!=identities:raise ValueError('Measured four-party caster identity changed')
    for case in CASES:
        if case['name']not in operated:continue
        stage_delta(before,after,case,'final')
        identity=before['party'][case['pc']-1]['runtime_id']
        for group in ('party','current_area_actors'):
            a=[r for r in left[group]if r['runtime_id']==identity];b=[r for r in right[group]if r['runtime_id']==identity]
            if len(a)!=1 or len(b)!=1:raise ValueError('Caster duplicate/lost on collected surfaces')
            page(a[0],case['kind'],case['level'])['memorized']=[];page(b[0],case['kind'],case['level'])['memorized']=[]
    if left!=right:raise ValueError('Undeclared collected world/item/XP/quest/stat/effect/spell mutation')

def field(ui,pack,window,cid):
    rows=[r for r in ui['controls']if r['pack']==pack and r['window']==window and r['id']==cid]
    if len(rows)!=1 or not rows[0]['visible']:raise ValueError('Missing/ambiguous actual visible control')
    return rows[0]

def book_guard(meta,state,ui,case,spell_names,level_template):
    pc=case['pc'];level=meta.get('level');actor=state['party'][pc-1]
    if meta.get('actor')!=pc or meta.get('kind')!=case['kind']or meta.get('pack')!=case['pack']or state['selection']!=pc or actor['script_name'].casefold()!=('imoen'if pc==2 else'jaheira'):raise ValueError('Shown/selected caster binding differs')
    data=page(actor,case['kind'],level);known=[]
    for index,row in enumerate(data['known']):known.append(dict(original_index=index,resref=row['resref'].upper(),name=spell_names[row['resref'].upper()]['name']))
    shown=sorted(known,key=lambda r:r['name']);memo=[dict(resref=r['resref'].upper(),flags=r['flags'])for r in data['memorized']]
    if meta.get('known')!=known or meta.get('shown')!=shown or meta.get('memorized')!=memo or meta.get('slots')!=data['slots_with_bonus']:raise ValueError('Raw caster page disagrees with shown content contract')
    if field(ui,case['pack'],2,0x10000035)['text']!=actor['name']or meta.get('actor_name')!=actor['name']:raise ValueError('Actual displayed caster name differs')
    expected=level_template.replace('<SPELLLEVEL>',str(level+1))
    if '<'in expected or meta.get('label')!=expected or field(ui,case['pack'],2,0x10000032)['text']!=expected:raise ValueError('Shown level label disagrees with captured content level')
    for index,row in enumerate(shown):
        item=field(ui,case['pack'],2,27+index)
        if item['value']!=row['original_index']or item['tooltip']!=row['name']or item['stored_tooltip']!=row['name']or item['disabled']or not item['picture_present']:raise ValueError('Sorted actual known slot/original index/tooltip binding differs')
    for index,row in enumerate(memo):
        item=field(ui,case['pack'],2,3+index)
        if item['value']!=index or item['tooltip']!=spell_names[row['resref']]['name']or not item['picture_present']:raise ValueError('Actual memorized slot binding differs')
    return [r['original_index']for r in shown]!=list(range(len(shown)))

def bmp_region_sha(path,rect):
    raw=Path(path).read_bytes()
    if raw[:2]!=b'BM'or len(raw)<54 or binary.u32(raw,2)!=len(raw):raise ValueError('Invalid bounded BMP')
    offset=binary.u32(raw,10);width,height=struct.unpack('<ii',binary.block(raw,18,8));bits=binary.u16(raw,28);compression=binary.u32(raw,30)
    if width<=0 or not height or bits not in (24,32)or compression!=0:raise ValueError('Unsupported uncompressed capture BMP')
    stride=((width*bits+31)//32)*4;binary.block(raw,offset,stride*abs(height));x,y,w,h=rect
    if any(type(v)is not int for v in rect)or min(x,y)<0 or min(w,h)<=0 or x+w>width or y+h>abs(height):raise ValueError('Actual tab rectangle escapes screenshot')
    pixels=[];size=bits//8
    for top in range(y,y+h):
        row=top if height<0 else height-1-top;pixels.append(binary.block(raw,offset+row*stride+x*size,w*size))
    return hashlib.sha256(b''.join(pixels)).hexdigest()

def tab_hashes(folder,meta,ui,case):
    return [bmp_region_sha(folder/('capture-%d.bmp'%meta['capture']),field(ui,case['pack'],2,case['tabs']+i)['screen_rect'])for i in range(case['count'])]

def tabs_guard(rows,case):
    prefix=case['name']+'.';reference0=rows[prefix+'tab0'];reference1=rows[prefix+'tab1']
    if reference0[0]==reference1[0]or reference0[1]==reference1[1]:raise ValueError('Direct tab references do not visibly distinguish selected level')
    for name,reference in [('arrow0',reference0),('arrow1',reference1),('back1',reference1),('tab1-repeat',reference1)]:
        if rows[prefix+name]!=reference:raise ValueError('Arrow/direct selected-tab visual state disagrees: '+name)

def wire_spellbooks(folder):
    files=list(Path(folder).iterdir());gams=[p for p in files if p.name.casefold()=='baldur.gam']
    if len(gams)!=1:raise ValueError('Unique saved GAME required')
    gam=gams[0].read_bytes()
    if gam[:8]!=b'GAMEV2.0'or binary.u32(gam,0x24)!=4:raise ValueError('Measured four-party GAME required')
    base=binary.u32(gam,0x20);binary.block(gam,base,4*0x160);result=[];spans=[]
    for actor in range(4):
        at=base+actor*0x160;start,size=binary.u32(gam,at+4),binary.u32(gam,at+8)
        if start<base+4*0x160 or any(max(start,a)<min(start+size,a+n)for a,n in spans):raise ValueError('Embedded caster overlap')
        spans.append((start,size));cre=binary.block(gam,start,size);binary.validate_cre(cre);known_at,known_n,books_at,books_n,memo_at,memo_n=struct.unpack('<6I',binary.block(cre,0x2a0,24))
        for pos,n,stride in ((known_at,known_n,12),(books_at,books_n,16),(memo_at,memo_n,12)):
            if n>10000 or n and pos<0x2d4:raise ValueError('CRE spell table bounds')
            binary.block(cre,pos,n*stride)
        spans_=[(pos,n*stride)for pos,n,stride in((known_at,known_n,12),(books_at,books_n,16),(memo_at,memo_n,12))if n]
        if any(max(a,b)<min(a+n,b+m)for i,(a,n)in enumerate(spans_)for b,m in spans_[:i]):raise ValueError('Overlapping CRE spell tables')
        pages={};used=[]
        for index in range(books_n):
            pos=books_at+16*index;level,slots,bonus,kind,first,count=struct.unpack('<4H2I',binary.block(cre,pos,16));key=(kind,level)
            if key in pages or first>memo_n or count>memo_n-first:raise ValueError('Duplicate/escaping spell page')
            if any(max(first,a)<min(first+count,a+n)for a,n in used):raise ValueError('Overlapping memorized spell ownership')
            used.append((first,count));memo=[]
            for i in range(first,first+count):memo.append(dict(resref=binary.block(cre,memo_at+i*12,8).split(b'\0')[0].decode('ascii').upper(),flags=binary.u32(cre,memo_at+i*12+8)))
            pages[key]=dict(type=kind,level=level,slots=slots,slots_with_bonus=bonus,known=[],memorized=memo)
        for index in range(known_n):
            pos=known_at+12*index;ref=binary.block(cre,pos,8).split(b'\0')[0].decode('ascii').upper();level,kind=struct.unpack('<2H',binary.block(cre,pos+8,4));key=(kind,level)
            if key not in pages:raise ValueError('Known spell without declared page')
            pages[key]['known'].append(dict(resref=ref,level=level,type=kind))
        if sum(n for _,n in used)!=memo_n:raise ValueError('Orphan memorized spell record')
        result.append(dict(name=binary.block(cre,0x280,32).split(b'\0')[0].decode('ascii').casefold(),pages=list(pages.values())))
    return result

def wire_state_guard(wire,state):
    caster_surfaces(state)
    if [r['name']for r in wire]!=[a['script_name'].casefold()for a in state['party']]:raise ValueError('Saved caster ordering differs')
    for saved,actor in zip(wire,state['party']):
        for page_ in saved['pages']:
            actual=page(actor,page_['type'],page_['level'])
            if spells(page_['memorized'])!=spells(actual['memorized'])or [(s['resref'].upper(),s['level'],s['type'])for s in page_['known']]!=[(s['resref'].upper(),s['level'],s['type'])for s in actual['known']]:raise ValueError('Saved spell refs/order/ready flags differ from actual caster')
    return True

def wire_delta_guard(before,after):
    left=copy.deepcopy(before);right=copy.deepcopy(after)
    if [r['name']for r in left]!=['none','imoen','jaheira','minsc']or [r['name']for r in right]!=[r['name']for r in left]:raise ValueError('Saved caster party identity changed')
    for case in CASES:
        a=[p for p in left[case['pc']-1]['pages']if p['type']==case['kind']and p['level']==case['level']];b=[p for p in right[case['pc']-1]['pages']if p['type']==case['kind']and p['level']==case['level']]
        if len(a)!=1 or len(b)!=1:raise ValueError('Saved target page absent')
        original=spells(a[0]['memorized'])
        if not original or original[0]!=(case['ref'],1)or spells(b[0]['memorized'])!=original[1:]+[(case['ref'],0)]:raise ValueError('Saved exact target charged/depleted delta differs')
        a[0]['memorized']=[];b[0]['memorized']=[]
    if left!=right:raise ValueError('Saved known spells/slots/other memorization bytes changed')

def equal_except_selection(before,after):
    left=copy.deepcopy(before);right=copy.deepcopy(after);left.pop('selection',None);right.pop('selection',None)
    if left!=right:raise ValueError('Unexpected collected state mutation in ordinary non-mutating callback')

def callback_guard(before,after,case,kind):
    caster_surfaces(before);caster_surfaces(after)
    pc=case['pc'];left=copy.deepcopy(before);right=copy.deepcopy(after);a=page(left['party'][pc-1],case['kind'],case['level']);b=page(right['party'][pc-1],case['kind'],case['level']);old=spells(a['memorized'])
    if kind=='confirm-remove':
        if not old or old[0]!=(case['ref'],1):raise ValueError('Charged confirmation target differs')
        expected=old[1:]
    elif kind in('known-add','known-readd'):expected=old+[(case['ref'],0)]
    elif kind=='depleted-remove':
        if not old or old[-1]!=(case['ref'],0):raise ValueError('Direct depleted target differs')
        expected=old[:-1]
    else:raise ValueError('Unknown mutating callback')
    if spells(b['memorized'])!=expected:raise ValueError('Actual callback changed wrong resref/index/charge/count')
    identity=before['party'][pc-1]['runtime_id']
    for group in('party','current_area_actors'):
        for state in(left,right):
            found=[row for row in state[group]if row['runtime_id']==identity]
            if len(found)!=1:raise ValueError('Callback caster identity missing/duplicate')
            page(found[0],case['kind'],case['level'])['memorized']=[]
    equal_except_selection(left,right)
