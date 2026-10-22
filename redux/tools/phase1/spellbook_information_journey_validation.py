"""Independent natural-page inventory, callback and exact mutation contracts."""
from pathlib import Path
import copy
import re
import spellbook_operation_validation as base
import spellbook_information_validation as page_contract
import weapon_query_validation as evidence

GENDER_ROWS={'PRO_HESHE':(0,27484,27485),'PRO_HIMHER':(0,27488,27487),'PRO_HISHER':(0,27486,27487)}
SCROLL_REFS={'mage':'SPWI302','priest':'SPPR303'}

def gender_rows(raw):
    lines=[line.split('//',1)[0].split()for line in raw.decode('ascii').splitlines()]
    lines=[line for line in lines if line]
    if lines[:3]!=[['2DA','V1.0'],['*'],['TYPE','MALE','FEMALE']]:raise ValueError('Unsupported frozen gender table header')
    for name,expected in GENDER_ROWS.items():
        found=[r for r in lines[3:]if r[0]==name]
        if found!=[[name,*map(str,expected)]]:raise ValueError('Wrong/missing/duplicate gender row/slot/refs: '+name)
    return {name:dict(slot=row[0],male=row[1],female=row[2])for name,row in GENDER_ROWS.items()}

def resolve_description(raw,table,words,state):
    rows=gender_rows(table);refs={str(ref)for row in GENDER_ROWS.values()for ref in row[1:]}
    if set(words)!=refs or any(not isinstance(w,str)or not w or '<'in w or '>'in w for w in words.values()):raise ValueError('Incomplete/unsupported frozen gender words')
    found=re.findall(r'<[^<>]*>',raw)
    if any(t[1:-1]not in rows for t in found)or '<'in re.sub(r'<[^<>]*>','',raw)or '>'in re.sub(r'<[^<>]*>','',raw):raise ValueError('Unsupported description tokens')
    if not found:return raw,[]
    if len(state['party'])!=4:raise ValueError('Protagonist slot missing')
    actor=state['party'][0];sex=actor['modified_stats'][35]
    mirrors=[a for a in state['current_area_actors']if a['runtime_id']==actor['runtime_id']]
    if actor['in_party']!=1 or actor['script_name'].casefold()!='none'or type(sex)is not int or not 0<=sex<=0xffffffff or len(mirrors)!=1 or mirrors[0]!=actor:raise ValueError('Wrong/incoherent protagonist sex/identity')
    evidence_rows=[]
    def replace(match):
        name=match[0][1:-1];row=rows[name];ref=row['female']if sex==2 else row['male']
        evidence_rows.append(dict(token=name,slot=0,actor_runtime_id=actor['runtime_id'],sex_stat=35,sex=sex,word_ref=ref,word=words[str(ref)]))
        return words[str(ref)]
    return re.sub(r'<[^<>]*>',replace,raw),evidence_rows

def scroll_identity(ready,case,resources):
    page=base.page(ready['party'][case['pc']-1],case['kind'],2)
    known=[dict(original_index=i,resref=r['resref'].upper(),name=resources[r['resref'].upper()+'.spl']['spell_name'])for i,r in enumerate(page['known'])]
    shown=sorted(known,key=lambda r:r['name']);matches=[(i,r)for i,r in enumerate(shown)if r['resref']==SCROLL_REFS[case['name']]]
    if len(matches)!=1:raise ValueError('Natural long-description target missing/ambiguous')
    return matches[0]

def expected_plan(ready,mode,resources=None):
    if mode not in ('operate','reload'):raise ValueError('Unknown information mode')
    result=[]
    for case in base.CASES:
        name=case['name'];result.extend([name+'.portrait',name+'.open']);total_known=0
        for level in range(case['count']):
            pages=[p for p in ready['party'][case['pc']-1]['spellbook']if p['type']==case['kind']and p['level']==level]
            if len(pages)>1:raise ValueError('Duplicate natural spellbook page')
            rows=pages[0]['known']if pages else []
            if not rows:continue
            total_known+=len(rows);prefix='%s.level%d'%(name,level);result.append(prefix+'.tab')
            for top in range(0,len(rows),7):
                p=prefix+'.page%d'%(top//7)
                if top:result.append(p+'.next')
                result.extend(p+'.'+suffix for suffix in ('default','select','selected','deselect','deselected'))
        if not 0<total_known<=256:raise ValueError('Natural known-spell inventory absent/unbounded')
        position,_=scroll_identity(ready,case,resources)
        p=name+'.scroll';result.extend([p+'.tab-away',p+'.tab'])
        result.extend(p+'.next%d'%i for i in range(1,position//7+1))
        result.extend(p+'.'+s for s in ('default','select','selected','scroll-down','scrolled','scroll-up','restored'))
        p=name+'.target'
        result.extend(p+'.'+s for s in ('tab-away','tab','default','other-portrait','other-actor','return-portrait','returned','assert-page','select','selected'))
        if mode=='operate':result.extend(p+'.'+s for s in ('remove','after-remove','separate','after-separate','full-icon','after-full-icon','remove-depleted','after-depleted','icon','final'))
        result.append(name+'.close')
    result.append('leader-portrait')
    if len(result)>650:raise ValueError('Information plan exceeds bound')
    return result

def display_guard(meta,state,ui,case,resources,source):
    pc=meta['actor'];kind=case['kind'];level=meta['level'];pack=case['pack'];actor=state['party'][pc-1]
    pages=[p for p in actor['spellbook']if p['type']==kind and p['level']==level]
    if len(pages)>1:raise ValueError('Duplicate displayed spellbook page')
    # A missing native page exposes zero through the count APIs. This is an
    # observation projection for the deliberately ineligible actor, not a saved
    # page or a replacement world snapshot.
    if not pages and pc==case['pc']:raise ValueError('Eligible actual page missing')
    actual=pages[0]if pages else dict(known=[],memorized=[],slots_with_bonus=0)
    known=[]
    for i,r in enumerate(actual['known']):
        ref=r['resref'].upper();known.append(dict(original_index=i,resref=ref,name=resources[ref+'.spl']['spell_name']))
    shown=sorted(known,key=lambda r:r['name'])
    if meta.get('schema')!='bg-redux-book-observation/2'or meta.get('pack')!=pack or meta.get('kind')!=kind or state['selection']!=pc:raise ValueError('Actual displayed book context differs')
    if Path(meta['module']).resolve()!=(Path(source)/'gemrb/GUIScripts'/(pack+'.py')).resolve():raise ValueError('Wrong GUI provider')
    if meta.get('known')!=known or meta.get('shown')!=shown or meta.get('memorized')!=[dict(resref=r['resref'].upper(),flags=r['flags'])for r in actual['memorized']]or meta.get('slots')!=actual['slots_with_bonus']:raise ValueError('Shown complete known/memorized/slot data contradicts raw state')
    if meta.get('actor_name')!=actor['name']or base.field(ui,pack,2,0x10000035).get('text')!=actor['name']:raise ValueError('Displayed actor name differs')
    windows=[r for r in ui['controls']if r.get('pack')==pack and r.get('window')is None and r.get('id')==2]
    if len(windows)!=1 or windows[0].get('visible')is not True or windows[0].get('disabled')!=(pc!=case['pc']):raise ValueError('Ordinary/ineligible book window state differs')
    label=resources['level_template']['value'].replace('<SPELLLEVEL>',str(level+1))
    if meta.get('label')!=label or base.field(ui,pack,2,0x10000032).get('text')!=label:raise ValueError('Displayed localized level differs')
    layout=meta['information_page'];selected=layout.get('selected')
    if layout.get('resolved_action_label')!=resources['information_action_labels'][str(17189 if pack=='GUIMG'else 17224)]:raise ValueError('Action label differs from frozen configured TLK')
    page_contract.validate_page(layout,shown,ui['controls'],pack,pc,kind,level,
        expected_module=Path(source)/'gemrb/GUIScripts/EESpellbookInformation.py',expected_help=resources['spellbook_help']['value'],require_unselected=False)
    token_trace=[]
    if selected:
        spell=resources[selected['resref']+'.spl'];raw=spell['spell_description']
        if '<'in raw or '>'in raw:
            table=(resources['_gender_path']).read_bytes()
            if gender_rows(table)!=resources['information_gender_tokens']['rows']:raise ValueError('Actual/frozen information gender rows differ')
            description,token_trace=resolve_description(raw,table,resources['information_gender_tokens']['words'],state)
        else:description=raw
        if layout['selected_description_ref']!=spell['spell_description_ref']or layout['selected_description']!=description:raise ValueError('Selected full description differs from frozen SPL/TLK/token binding')
        can=len(actual['memorized'])<actual['slots_with_bonus']
        if layout['action_disabled']!= (not can):raise ValueError('Selected separate action does not reflect actual capacity')
    if len(actual['memorized'])>12:raise ValueError('Prepared row capacity outside bounded ordinary layout')
    for i,r in enumerate(actual['memorized']):
        item=base.field(ui,pack,2,3+i)
        if item.get('value')!=i or item.get('tooltip')!=resources[r['resref'].upper()+'.spl']['spell_name']or not item.get('picture_present'):raise ValueError('Prepared row binding differs')
    for i in range(len(actual['memorized']),12):
        item=base.field(ui,pack,2,3+i)
        if item.get('stored_tooltip')or item.get('flags',0)&2:raise ValueError('Empty prepared row retained visible stale spell')
    return shown,token_trace

def selection_guard(name,meta,case,ready=None,resources=None):
    layout=meta['information_page'];selected=layout['selected'];expected_pc=(1 if case['name']=='mage'else 2)if name.endswith('.other-actor')else case['pc']
    if meta['actor']!=expected_pc:raise ValueError('Actor-change observation did not show requested actor')
    match=re.fullmatch(r'(mage|priest)\.level(\d+)\.page(\d+)\.(default|selected|deselected)',name)
    if match:
        _,level,page,phase=match.groups()
        if meta['level']!=int(level)or layout['top']!=int(page)*7:raise ValueError('Actual natural level/page differs from independent plan')
        if phase=='selected':
            if selected!=layout['visible_rows'][0]:raise ValueError('Name callback selected wrong identity')
        elif selected is not None:raise ValueError('Default/deselected page retained selected identity')
    elif '.scroll.'in name:
        position,target=scroll_identity(ready,case,resources)
        if meta['level']!=2 or layout['top']!=(position//7)*7:raise ValueError('Long-description level/page differs')
        if name.endswith('.default'):
            if selected is not None:raise ValueError('Long-description page retained stale selection')
        elif selected!=target:raise ValueError('Wrong natural long-description target selected')
    else:
        if meta['level']!=case['level']or layout['top']!=0:raise ValueError('Target/context reset did not return initial page/level')
        if name.rsplit('.',1)[1]in('default','other-actor','returned'):
            if selected is not None:raise ValueError('Actor/level change retained a stale selection')
        elif not selected or (selected['resref'],selected['original_index'])!=(case['ref'],case['known']):raise ValueError('Target selected identity differs')

def callback_route(name,event,before,resources):
    """Expected registered control comes from the independent plan and raw world."""
    if name=='leader-portrait':wanted=('PORTWIN',0,0)
    else:
        case=next(c for c in base.CASES if name.startswith(c['name']+'.'));suffix=name.rsplit('.',1)[-1]
        if suffix=='portrait':wanted=('PORTWIN',0,case['pc']-1)
        elif suffix in ('open','close'):wanted=('OPTWIN',0,5 if case['name']=='mage'else 6)
        elif suffix=='other-portrait':wanted=('PORTWIN',0,0 if case['name']=='mage'else 1)
        elif suffix=='return-portrait':wanted=('PORTWIN',0,case['pc']-1)
        elif suffix in ('tab','tab-away'):
            m=re.fullmatch(r'(mage|priest)\.level(\d+)\.tab',name)
            level=(3 if suffix=='tab-away'else 2)if '.scroll.'in name else int(m[2])if m else (case['level']+1)%case['count']if suffix=='tab-away'else case['level']
            wanted=(case['pack'],2,case['tabs']+level)
        elif suffix=='next'or re.fullmatch('next[1-9][0-9]*',suffix):wanted=(case['pack'],2,page_contract.DOWN)
        elif suffix in ('scroll-down','scroll-up'):wanted=(case['pack'],2,page_contract.INFO_DOWN if suffix=='scroll-down'else page_contract.INFO_UP)
        elif suffix in ('select','deselect')and'.level'in name:wanted=(case['pack'],2,page_contract.NAME)
        elif '.scroll.'in name and suffix=='select':
            position,_=scroll_identity(before,case,resources)
            wanted=(case['pack'],2,page_contract.NAME+position%7)
        else:
            rows=base.page(before['party'][case['pc']-1],case['kind'],case['level'])
            sorted_known=sorted(enumerate(rows['known']),key=lambda p:resources[p[1]['resref'].upper()+'.spl']['spell_name'])
            indices=[i for i,(original,r)in enumerate(sorted_known)if r['resref'].upper()==case['ref']and original==case['known']]
            if len(indices)!=1 or indices[0]>=7:raise ValueError('Fixed target is not on initial visible page')
            if suffix=='select':cid=page_contract.NAME+indices[0]
            elif suffix=='separate':cid=page_contract.ACTION
            elif suffix in ('icon','full-icon'):cid=27+indices[0]
            elif suffix=='remove':cid=3+case['memo']
            elif suffix=='remove-depleted':cid=3+len(rows['memorized'])-1
            else:raise ValueError('Unrecognized requested information callback')
            wanted=(case['pack'],2,cid)
    if tuple(event[k]for k in ('pack','window','control'))!=wanted:raise ValueError('Actual registered control differs from independent information route')

def observation_world_guard(ready,state):
    left=copy.deepcopy(ready);right=copy.deepcopy(state)
    base.caster_surfaces(ready);base.caster_surfaces(state)
    for c in base.CASES:
        identity=ready['party'][c['pc']-1]['runtime_id']
        for group in ('party','current_area_actors'):
            for raw in (left,right):
                people=[a for a in raw[group]if a['runtime_id']==identity]
                if len(people)!=1:raise ValueError('Caster missing/duplicated in observation')
                base.page(people[0],c['kind'],c['level'])['memorized']=[]
    base.equal_except_selection(left,right)

def validate_capture(folder,nonce,mode,started_ns,receipt):
    host=evidence.read(folder/'book-result.json');runtime=evidence.read(folder/'book-runtime.json')
    if not re.fullmatch('[0-9a-f]{32}',nonce):raise ValueError('Caller nonce invalid')
    if host.get('schema')!='bg-redux-information-host/1'or host.get('nonce')!=nonce or host.get('mode')!=mode or host.get('confirmation_policy')!='ee-direct'or host.get('completed')is not True or host.get('error')or host.get('os_pointer_input')is not False or host.get('direct_spell_mutation')is not False:raise ValueError('Incomplete/stale/forced information host')
    ready=evidence.read(folder/'ready.state.json');loaded=evidence.read(folder/'loaded.state.json');scene=evidence.read(folder/'ready.scene.json');evidence.require_state(ready)
    plan=expected_plan(ready,mode,receipt['resources'])
    if runtime.get('schema')!='bg-redux-information-runtime/1'or runtime.get('nonce')!=nonce or runtime.get('mode')!=mode or runtime.get('confirmation_policy')!='ee-direct'or runtime.get('planned')!=plan or runtime.get('steps')!=len(plan)or runtime.get('completed')is not True or runtime.get('physical_pointer_input')is not False:raise ValueError('Independent information plan coverage differs')
    if started_ns is not None and any(p.stat().st_mtime_ns<started_ns for p in folder.iterdir()if p.is_file()):raise ValueError('Stale evidence')
    events=host['events'];startup=host['startup'];rows=runtime['rows']
    if events!=evidence.read(folder/'book-events.json')or startup!=evidence.read(folder/'book-startup.json')or host['callbacks']!=len(events):raise ValueError('Raw native event continuity differs')
    if len(ready['party'])!=4 or ready['current_area'].upper()!='AR0602'or scene['bd_defai']!=1 or scene['leader_class_script'].upper()!='BDDEFAI'or len(startup)<4 or any(not r['idle']for r in startup[-4:])or ready['game_time']<loaded['game_time']+30:raise ValueError('Natural startup readiness absent')
    for i,s in enumerate(startup):
        state=evidence.read(folder/(s['checkpoint']+'.state.json'));raw=evidence.read(folder/(s['checkpoint']+'.scene.json'))
        if s['game_time']!=state['game_time']or raw['game_time']!=state['game_time']or s['idle']!=raw['idle']or len(raw['party_actions'])!=4:raise ValueError('Readiness sample contradictory')
        if i and(s['tick']<=startup[i-1]['tick']or s['game_time']<startup[i-1]['game_time']):raise ValueError('Readiness order contradictory')
    requests=[r for r in rows if r['event']=='request'];observations=[r for r in rows if r['event']=='observe'];dispatch=[e for e in events if e['step']>=0]
    if len(dispatch)!=len(requests):raise ValueError('Requested callback not dispatched')
    for r,e in zip(requests,dispatch):
        if e['step']!=r['step']or [e[k]for k in('pack','window','control')]!=[r[k]for k in('pack','window','control')]:raise ValueError('Callback route differs')
        base.request_value_guard(r,e)
    captures={};nonidentity=False;token_resolutions=[];resources=dict(receipt['resources'],_gender_path=folder/'gender.2da.runtime')
    expected_observations=[(i,n)for i,n in enumerate(plan)if n.endswith(('.default','.selected','.deselected','.other-actor','.returned','.scrolled','.restored','.after-remove','.after-separate','.after-full-icon','.after-depleted','.final'))]
    if [(r['step'],r['name'])for r in observations]!=expected_observations:raise ValueError('Natural page/selection/operation observation inventory incomplete')
    observed_steps={i for i,_ in expected_observations}
    expected_rows=[(i,'observe'if i in observed_steps else'request')for i,n in enumerate(plan)if not n.endswith('.assert-page')]
    if [(r['step'],r['event'])for r in rows]!=expected_rows:raise ValueError('Complete runtime request/observation inventory differs')
    for i,row in enumerate(observations,1):
        if row['capture']!=i:raise ValueError('Capture sequence differs')
        name=row['name'];case=next(c for c in base.CASES if name.startswith(c['name']+'.'));meta=evidence.read(folder/('capture-%d.book.json'%i));state=evidence.read(folder/('capture-%d.state.json'%i));ui=evidence.read(folder/('capture-%d.ui.json'%i));raw_scene=evidence.read(folder/('capture-%d.scene.json'%i))
        if (meta.get('nonce'),meta.get('name'),meta.get('capture'),meta.get('step'))!=(nonce,name,i,row['step'])or state['game_time']!=ready['game_time']or raw_scene['game_time']!=state['game_time']:raise ValueError('Capture nonce/clock/identity differs')
        if meta.get('confirmation_option')!=0 or meta.get('confirmation')is not False:raise ValueError('Actual default-off confirmation scope differs')
        shown,trace=display_guard(meta,state,ui,case,resources,receipt['source']);selection_guard(name,meta,case,ready,resources)
        if trace:token_resolutions.append(dict(capture=i,resref=meta['information_page']['selected']['resref'],description_ref=meta['information_page']['selected_description_ref'],resolutions=trace))
        observation_world_guard(ready,state)
        base.bmp_region_sha(folder/('capture-%d.bmp'%i),base.field(ui,case['pack'],2,page_contract.TEXT)['screen_rect'])
        nonidentity|=[r['original_index']for r in shown]!=list(range(len(shown)))
        captures[name]=(meta,state,ui,i)
    if host['captures']!=len(observations)or len(list(folder.glob('capture-*.bmp')))!=len(observations):raise ValueError('Missing/extra screenshot inventory')
    for i,e in enumerate(events,1):
        if e['nonce']!=nonce or e['sequence']!=i or e.get('performed')is not True:raise ValueError('Native callback nonce/order differs')
        before=evidence.read(folder/('callback-%d-before.state.json'%i));after=evidence.read(folder/('callback-%d-after.state.json'%i))
        if base.callback_game_boundary(e,before,after):continue
        step=e['step'];name=plan[step]if step>=0 else '';suffix=name.rsplit('.',1)[-1]
        if step>=0:callback_route(name,e,before,resources)
        mutation={'remove':'charged-remove','separate':'known-add','remove-depleted':'depleted-remove','icon':'known-readd'}.get(suffix)if '.target.'in name else None
        if mutation:
            if mode!='operate':raise ValueError('Reload mutated spellbook')
            case=next(c for c in base.CASES if name.startswith(c['name']+'.'));base.callback_guard(before,after,case,mutation)
            if suffix in('separate','icon')and(e['actual_value']!=case['known']or e['actual_tooltip']!=(''if suffix=='separate'else resources[case['ref']+'.spl']['spell_name'])):raise ValueError('Actual Memorize callback identity differs')
        else:base.equal_except_selection(before,after)
    scrolls=[]
    for case in base.CASES:
        p=case['name']+'.scroll';pre=captures[p+'.selected'];down=captures[p+'.scrolled'];up=captures[p+'.restored']
        rect=base.field(pre[2],case['pack'],2,page_contract.TEXT)['screen_rect']
        hashes=[base.bmp_region_sha(folder/('capture-%d.bmp'%c[3]),rect)for c in(pre,down,up)]
        if hashes[0]==hashes[1]or hashes[0]!=hashes[2]:raise ValueError('Description viewport did not visibly scroll down and return')
        scrolls.append(dict(book=case['name'],resref=SCROLL_REFS[case['name']],level=2,description_ref=pre[0]['information_page']['selected_description_ref'],description_characters=len(pre[0]['information_page']['selected_description']),rect=rect,selected_sha256=hashes[0],scrolled_sha256=hashes[1],restored_sha256=hashes[2]))
        if mode=='operate':
            p=case['name']+'.target'
            baseline=captures[p+'.returned'][1]
            for phase,expected in (('after-remove','after-remove'),('after-separate','after-add'),('after-full-icon','after-add'),('after-depleted','after-depleted-remove'),('final','final')):base.stage_delta(baseline,captures[p+'.'+phase][1],case,expected)
    final=evidence.read(folder/'final.state.json');operations=evidence.read(folder/'operations-final.state.json');base.declared_world_delta(ready,operations,{c['name']for c in base.CASES}if mode=='operate'else set());base.equal_except_selection(operations,final)
    extra=[e for e in events if e['step']<0];expected=[(-1,'GUILOAD',0,26)]+([(-2,'GUIOPT',2,6),(-3,'GUISAVE',0,26),(-4,'GUISAVE',1,7)]if mode=='operate'else[])
    if [(e['step'],e['pack'],e['window'],e['control'])for e in extra]!=expected:raise ValueError('Normal load/save callback chain differs')
    if mode=='operate':
        if len(host['saves'])!=1 or evidence.read(folder/'save-name.json')!=dict(control=3,nonce=nonce,performed=True)or evidence.read(folder/'before-save.state.json')!=final:raise ValueError('Actual GUI save evidence incomplete')
    elif host['saves']!=[]:raise ValueError('Reload unexpectedly saved')
    return dict(save=host['saves'][0]if mode=='operate'else None,callbacks=len(events),observations=len(observations),natural_pages=sum(n.endswith('.default')and'.level'in n for n in plan),
        natural_over24=any(len(p['known'])>24 for c in base.CASES for p in ready['party'][c['pc']-1]['spellbook']if p['type']==c['kind']),
        all_natural_pages_visited=True,nonidentity_sort_runtime=nonidentity,description_scrolls=scrolls,token_resolutions=token_resolutions,physical_pointer_input=False,original_parity=None,per_label_style_observed=False)
