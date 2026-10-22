"""Strict external confirmation/settings contracts; does not import GemRB."""
import configparser
import copy
from pathlib import Path
import weapon_query_validation as evidence
import spellbook_operation_validation as base
from spellbook_operation_validation import wire_spellbooks, wire_state_guard, page
from spellbook_erase_validation import gender_row
CASES=(dict(name='mage',pc=2,pack='GUIMG',kind=1,level=1,ref='SPWI213',known=2,filler='SPWI214',modal=101,tabs=61,entry=5),dict(name='priest',pc=3,pack='GUIPR',kind=0,level=0,ref='SPPR113',known=4,filler='SPPR105',modal=5,tabs=55,entry=6))
SETTINGS=('loaded','open','gameplay','feedback','draft-before','toggle-cancel','draft-cancel','cancel','after-cancel','feedback-again','toggle-done','draft-done','done','after-done','gameplay-done','return','final')


def expected_plan(mode):
    if mode not in ('operate','reload'):raise ValueError('Explicit mode required')
    out=['settings.'+n for n in (SETTINGS if mode=='operate' else ('loaded',))]
    for c in CASES:
        names=['portrait','open','level','before']
        if mode=='operate':names+=['target-request','target-modal','cancel','after-cancel','filler-request','filler-modal','confirm','after-filler']+(['known-select','selected']if c['name']=='priest'else[])+['known-add','mixed-before','mixed-charged-click','after-mixed']
        out.extend(c['name']+'.'+n for n in names+['close'])
    return out+['leader-portrait']


def ini(raw):
    if not isinstance(raw,bytes) or len(raw)>1024*1024:raise ValueError('Bounded actual INI bytes required')
    p=configparser.ConfigParser(interpolation=None,inline_comment_prefixes=(';',),strict=True)
    try:p.read_string(raw.decode('utf8'))
    except (ValueError,configparser.Error)as e:raise ValueError('Malformed/duplicate actual settings INI')from e
    return p


def config_value(raw,expected,defaults=None):
    p=ini(raw)
    try:value=p.getint('Game Options','Over Confirm Everything')
    except (ValueError,configparser.Error)as e:raise ValueError('Persistent option missing/nonnumeric')from e
    if value!=expected:raise ValueError('Persistent option does not match observed runtime')
    if defaults is not None:
        d=ini(defaults)
        if set(p.sections())!=set(d.sections()) or any(set(p[s])!=set(d[s])for s in d.sections()):raise ValueError('Config writer whitelist differs')
        if any('bg2ee confirmation draft'in p[s]for s in p.sections()):raise ValueError('Draft option leaked into persistent INI')
    return value


def config_copy_guard(original,copied):
    config_value(original,1);config_value(copied,1)
    if original!=copied:raise ValueError('Fresh-process actual configuration copy is not byte-exact')


def memo_rows(rows):return [(x['resref'].upper(),x['flags'])for x in rows]


def changed(rows,case,kind):
    rows=copy.deepcopy(rows)
    if not any(x['resref'].upper()==case['ref']and x['flags']!=0 for x in rows):raise ValueError('Charged intended target absent')
    if kind=='filler':
        found=[i for i,x in enumerate(rows)if x['resref'].upper()==case['filler']and x['flags']!=0]
        if not found:raise ValueError('Declared charged filler absent')
        rows.pop(found[0])
    elif kind=='add':
        # Existing imported prepared refs are lowercase, but the callback adds
        # the uppercase known ref. Preserve both actual storage spellings.
        rows.append(dict(resref=case['ref'],flags=0))
    elif kind=='mixed':
        found=[i for i,x in enumerate(rows)if x['resref'].upper()==case['ref']and x['flags']==0]
        if len(found)!=1:raise ValueError('Exact measured mixed depleted copy absent/duplicate')
        rows.pop(found[0])
    else:raise ValueError('Undeclared memorization delta')
    return rows


def world_delta(before,after,case=None,kind=None):
    base.caster_surfaces(before);base.caster_surfaces(after)
    left=copy.deepcopy(before);right=copy.deepcopy(after)
    left.pop('selection',None);right.pop('selection',None)
    if case is not None:
        pc=case['pc'];identity=left['party'][pc-1]['runtime_id']
        for group in ('party','current_area_actors'):
            actors=[a for a in left[group]if a['runtime_id']==identity]
            if len(actors)!=1:raise ValueError('Caster identity lost/duplicated')
            p=page(actors[0],case['kind'],case['level']);p['memorized']=changed(p['memorized'],case,kind)
    if left!=right:raise ValueError('Undeclared world/XP/item/quest/effect/known/slot/memo mutation')


def wire_delta_guard(before,after):
    expected=copy.deepcopy(before)
    if [a['name']for a in expected]!=['none','imoen','jaheira','minsc']:raise ValueError('Measured four-party input absent')
    for c in CASES:
        p=next(p for p in expected[c['pc']-1]['pages']if(p['type'],p['level'])==(c['kind'],c['level']));p['memorized']=changed(p['memorized'],c,'filler')
    if expected!=after:raise ValueError('Saved wire differs beyond one declared filler per caster')


def terminal(host,runtime,nonce,mode):
    plan=expected_plan(mode)
    if len(nonce)!=32 or any(c not in'0123456789abcdef'for c in nonce):raise ValueError('Invalid nonce')
    if host.get('schema')!='bg-redux-book-host/1'or host.get('nonce')!=nonce or host.get('mode')!=mode or not host.get('completed')or host.get('error')or host.get('os_pointer_input')is not False or host.get('direct_spell_mutation')is not False:raise ValueError('Incomplete/forced native host')
    if runtime.get('schema')!='bg-redux-confirmation-runtime/1'or runtime.get('nonce')!=nonce or runtime.get('mode')!=mode or runtime.get('planned')!=plan or runtime.get('steps')!=len(plan)or not runtime.get('completed'):raise ValueError('Missing/stale explicit plan')
    return plan


def settings_file(folder,name):
    p=folder/(name+'.settings.json');r=evidence.read(p);path=folder/(name+'.ini')
    if r['ini_exists']:
        if not path.is_file()or path.read_bytes().decode('utf8')!=r['ini_text']:raise ValueError('Native INI snapshot bytes disagree')
        config_value(path.read_bytes(),1)
    elif r['ini_text']is not None or path.exists():raise ValueError('Missing INI falsely represented')
    if type(r['option'])is not int or r['option']not in (0,1):raise ValueError('Actual native option is unavailable/nonboolean')
    return r


def setting_observation(name,meta,native,mode):
    settings=meta['settings']
    if settings['option']!=native['option']or settings['ini_exists']!=native['ini_exists']or settings['ini_text']!=native['ini_text']:raise ValueError('Python/native option or INI observations disagree')
    raw=native['draft_raw']
    if raw not in(None,-12345,0,1):raise ValueError('Unsupported native draft value')
    expected=None if raw is None or raw==-12345 else raw
    if settings['draft']!=expected:raise ValueError('Draft sentinel bridge differs')
    expected_option=1 if mode=='reload'or name not in {'settings.loaded','settings.draft-before','settings.draft-cancel','settings.after-cancel','settings.draft-done'}else 0
    if native['option']!=expected_option or native['ini_exists']!=bool(expected_option):raise ValueError('Draft Cancel published/saved or Done failed to persist')
    drafts={'settings.draft-before':0,'settings.draft-cancel':1,'settings.draft-done':1}
    if name in drafts and settings['draft']!=drafts[name]:raise ValueError('Actual checkbox draft did not change')


def route_guard(name,event):
    actual=(event['pack'],event['window'],event['control'])
    settings={'settings.open':('OPTWIN',0,7),'settings.gameplay':('GUIOPT',2,9),'settings.feedback':('GUIOPT',8,5),'settings.feedback-again':('GUIOPT',8,5),'settings.toggle-cancel':('GUIOPT',9,38),'settings.toggle-done':('GUIOPT',9,38),'settings.cancel':('GUIOPT',9,27),'settings.done':('GUIOPT',9,26),'settings.gameplay-done':('GUIOPT',8,7),'settings.return':('GUIOPT',2,11),'leader-portrait':('PORTWIN',0,0)}
    if name in settings:
        if actual!=settings[name]:raise ValueError('Wrong actual settings/toolbar route')
        return
    c=next((c for c in CASES if name.startswith(c['name']+'.')),None)
    if c is None:raise ValueError('Undeclared callback name')
    suffix=name.split('.',1)[1];fixed={'portrait':('PORTWIN',0,c['pc']-1),'open':('OPTWIN',0,c['entry']),'close':('OPTWIN',0,c['entry']),'level':(c['pack'],2,c['tabs']+c['level']),'cancel':(c['pack'],c['modal'],1),'confirm':(c['pack'],c['modal'],0)}
    if suffix in fixed:
        if actual!=fixed[suffix]:raise ValueError('Wrong actual caster/navigation/modal route')
    elif suffix in('target-request','filler-request','mixed-charged-click'):
        if actual[:2]!=(c['pack'],2)or actual[2]!=3+event['actual_value']:raise ValueError('Wrong actual memo route')
    elif suffix=='known-select':
        if actual[:2]!=(c['pack'],2)or not 0x7fff0400<=actual[2]<0x7fff0407:raise ValueError('Wrong known-name row route')
    elif suffix=='known-add':
        if actual[:2]!=(c['pack'],2)or not(actual[2]==0x7fff0413 if c['name']=='priest'else 27<=actual[2]<34):raise ValueError('Wrong ordinary Memorize route')
    else:raise ValueError('Unexpected callback substituted for observation')


def fresh_evidence(folder,started_ns):
    required=('book-result.json','book-runtime.json','book-events.json','book-startup.json','loaded.state.json','loaded.settings.json','ready.state.json','ready.scene.json','operations-final.state.json','final.state.json')
    if any(not(folder/name).is_file()for name in required):raise ValueError('Required native evidence missing')
    if started_ns is not None and any(p.stat().st_mtime_ns<started_ns for p in folder.iterdir()if p.is_file()):raise ValueError('Stale evidence')


def validate_capture(folder,nonce,mode,started_ns,receipt):
    folder=Path(folder);fresh_evidence(folder,started_ns);host=evidence.read(folder/'book-result.json');runtime=evidence.read(folder/'book-runtime.json');plan=terminal(host,runtime,nonce,mode)
    if host.get('settings_ini')!=receipt['settings_ini']:raise ValueError('Wrong owned private settings path')
    rows=runtime['rows'];events=host['events'];startup=host['startup']
    if len(rows)!=len(plan)or [r['step']for r in rows]!=list(range(len(plan)))or events!=evidence.read(folder/'book-events.json')or startup!=evidence.read(folder/'book-startup.json')or host['callbacks']!=len(events):raise ValueError('Incomplete/raw event inventory')
    ready=evidence.read(folder/'ready.state.json');loaded=evidence.read(folder/'loaded.state.json');scene=evidence.read(folder/'ready.scene.json')
    evidence.require_state(ready)
    if len(ready['party'])!=4 or ready['current_area'].upper()!='AR0602'or scene['bd_defai']!=1 or scene['leader_class_script'].upper()!='BDDEFAI'or len(startup)<4 or any(not x['idle']for x in startup[-4:])or ready['game_time']<loaded['game_time']+30:raise ValueError('Natural startup readiness missing')
    for a,b in zip(startup,startup[1:]):
        if b['tick']<=a['tick']or b['game_time']<a['game_time']:raise ValueError('Startup time/order contradiction')
    for sample in startup:
        state=evidence.read(folder/(sample['checkpoint']+'.state.json'));sc=evidence.read(folder/(sample['checkpoint']+'.scene.json'))
        if sample['game_time']!=state['game_time']or sc['game_time']!=state['game_time']or sample['idle']!=sc['idle']:raise ValueError('Raw startup contradiction')
    initial=settings_file(folder,'loaded')
    if initial['option']!=(1 if mode=='reload'else 0)or initial['ini_exists']!=(mode=='reload'):raise ValueError('Fresh process did not load byte-copied actual setting')
    request=[r for r in rows if r['event']=='request'];actual=[e for e in events if e['step']>=0]
    if len(request)!=len(actual):raise ValueError('Request/actual callback count differs')
    snapshots={};observed={};strings=receipt['resources']['setting_strings']['values']
    for i,row in enumerate([r for r in rows if r['event']=='observe'],1):
        if row['capture']!=i or row['name']!=plan[row['step']]:raise ValueError('Capture order/identity differs')
        meta=evidence.read(folder/('capture-%d.book.json'%i));state=evidence.read(folder/('capture-%d.state.json'%i));ui=evidence.read(folder/('capture-%d.ui.json'%i));native=settings_file(folder,'capture-%d'%i)
        base.bmp_region_sha(folder/('capture-%d.bmp'%i),[0,0,1,1])
        if(meta.get('schema'),meta.get('nonce'),meta.get('name'),meta.get('step'),meta.get('capture'))!=('bg-redux-confirmation-observation/1',nonce,row['name'],row['step'],i)or state['game_time']!=ready['game_time']:raise ValueError('Stale/incorrect capture binding')
        setting_observation(row['name'],meta,native,mode)
        if row['name']in('settings.draft-before','settings.draft-cancel','settings.draft-done'):
            if base.field(ui,'GUIOPT',9,0x10000028)['text']!=strings['102476']:raise ValueError('Localized actual setting label differs')
            if row['name']!='settings.draft-before'and base.field(ui,'GUIOPT',9,28)['text']!=strings['102477']:raise ValueError('Actual checkbox callback did not set help')
        if 'book'in meta:
            c=next(c for c in CASES if row['name'].startswith(c['name']+'.'));b=meta['book'];a=state['party'][c['pc']-1];p=page(a,c['kind'],c['level'])
            if state['selection']!=c['pc']or b['actor']!=c['pc']or a['script_name'].casefold()!=('imoen'if c['pc']==2 else'jaheira')or b['level']!=c['level']or Path(b['module']).resolve()!=(Path(receipt['source'])/'gemrb/GUIScripts'/ (c['pack']+'.py')).resolve():raise ValueError('Selected caster/page/provider differs')
            known=[dict(original_index=j,resref=x['resref'].upper(),name=receipt['resources'][x['resref'].upper()+'.spl']['spell_name'])for j,x in enumerate(p['known'])];shown=sorted(known,key=lambda x:x['name']);top=b['top']
            if type(top)is not int or top<0 or top%7 or top>max(0,((len(shown)-1)//7)*7)or b['known']!=known or b['shown']!=shown or b['visible']!=shown[top:top+7]or memo_rows(b['memorized'])!=memo_rows(p['memorized'])or b['slots']!=p['slots_with_bonus']:raise ValueError('Actual known/memo/visible-pool/slot mapping differs')
            for j,x in enumerate(b['visible']):
                icon=base.field(ui,c['pack'],2,27+j);label=base.field(ui,c['pack'],2,0x7fff0400+j)
                if icon['value']!=x['original_index']or label['value']!=x['original_index']or label['text']!=x['name']or not icon['picture_present']:raise ValueError('Actual visible icon/name mapping differs')
            modal=row['name'].endswith(('.target-modal','.filler-modal'));actualmodal=any(x['pack']==c['pack']and x['window']==c['modal']and x['visible']for x in ui['controls'])
            if b['confirmation']!=modal or actualmodal!=modal:raise ValueError('Confirmation popup policy differs')
            if modal:
                if base.field(ui,c['pack'],c['modal'],3)['text']!=strings['11824']:raise ValueError('Wrong prepared-removal prompt text')
                for cid,ref in ((0,'17507'),(1,'13727')):
                    button=base.field(ui,c['pack'],c['modal'],cid);text=strings[ref].upper()if button['flags']&8 else strings[ref]
                    if button['text']!=text:raise ValueError('Wrong actual Remove/Cancel label')
            if row['name'].endswith('.selected'):
                selected=b['selected'];target=next(x for x in known if x['resref']==c['ref']);expected=[c['pc'],c['kind'],c['level'],c['ref'],c['known'],target['name']]
                if not selected or [*selected[:3],selected[3].upper(),*selected[4:]]!=expected or base.field(ui,c['pack'],2,0x7fff0413)['value']!=c['known']:raise ValueError('Separate Memorize selection binding differs')
        snapshots[row['name']]=state;observed[row['name']]=meta
    if host['captures']!=len(observed):raise ValueError('Capture inventory incomplete')
    for suffix in ('.bmp','.book.json','.state.json','.ui.json','.scene.json','.settings.json'):
        if {p.name for p in folder.glob('capture-*'+suffix)}!={'capture-'+str(i)+suffix for i in range(1,len(observed)+1)}:raise ValueError('Missing/extra capture evidence type')
    filler_indices={}
    for want,event in zip(request,actual):
        if[want[k]for k in('step','pack','window','control')]!=[event[k]for k in('step','pack','window','control')]or event['action']!='Press':raise ValueError('Actual registered callback identity differs')
        if want['value']is None:
            if event['actual_value']!=0xffffffff or event['actual_variable']!='':raise ValueError('Unbound null bridge differs')
        elif event['actual_value']!=want['value']:raise ValueError('Bound original callback value differs')
        if plan[event['step']].startswith('settings.toggle-'):
            if event['dispatch']!='view-mouse-down-up'or event['actual_variable']!='BG2EE Confirmation Draft'or event['control']!=38:raise ValueError('Checkbox used fabricated option setter')
        elif event['dispatch']!='registered-callback':raise ValueError('Undeclared dispatch route')
        binding=want['binding'];name=plan[event['step']];route_guard(name,event)
        if name.endswith(('.target-request','.mixed-charged-click','.filler-request')):
            c=next(c for c in CASES if name.startswith(c['name']+'.'));before=evidence.read(folder/('callback-%d-before.state.json'%event['sequence']));p=page(before['party'][c['pc']-1],c['kind'],c['level']);index=event['actual_value'];ref=c['filler']if name.endswith('.filler-request')else c['ref']
            if not 0<=index<len(p['memorized'])or memo_rows([p['memorized'][index]])!=[(ref,1)]or binding.get('resref')!=ref or binding.get('memo_index')!=index or event['control']!=3+index:raise ValueError('Clicked actual charged memo identity differs')
        if name.endswith('.filler-request'):filler_indices[c['name']]=index
        if name.endswith('.confirm'):
            c=next(c for c in CASES if name.startswith(c['name']+'.'))
            if event['actual_value']!=filler_indices.get(c['name']):raise ValueError('Confirm lost original filler memo index')
        if name.endswith(('.known-add','.known-select')):
            c=next(c for c in CASES if name.startswith(c['name']+'.'))
            if event['actual_value']!=c['known']or binding.get('resref')!=c['ref']or binding.get('original_index')!=c['known']:raise ValueError('Known-add original identity differs')
    for i,event in enumerate(events,1):
        if event['sequence']!=i or event['nonce']!=nonce or not event['performed']:raise ValueError('Callback ownership/sequence differs')
        before=evidence.read(folder/('callback-%d-before.state.json'%i));after=evidence.read(folder/('callback-%d-after.state.json'%i))
        if base.callback_game_boundary(event,before,after):continue
        ns=settings_file(folder,'callback-%d-before'%i);nt=settings_file(folder,'callback-%d-after'%i);name=plan[event['step']]if event['step']>=0 else''
        if name=='settings.done':
            if ns['option']!=0 or ns['ini_exists']or nt['option']!=1 or not nt['ini_exists']:raise ValueError('Done did not persist actual option')
        elif ns['option']!=nt['option']or ns['ini_exists']!=nt['ini_exists']or ns['ini_text']!=nt['ini_text']:raise ValueError('Non-Done callback changed committed config')
        c=next((c for c in CASES if name.startswith(c['name']+'.')),None);kind='filler'if name.endswith('.confirm')else'add'if name.endswith('.known-add')else'mixed'if name.endswith('.mixed-charged-click')else None
        world_delta(before,after,c if kind else None,kind)
    for c in CASES:
        before=snapshots[c['name']+'.before']
        if mode=='operate':
            for suffix in('target-modal','after-cancel','filler-modal'):world_delta(before,snapshots[c['name']+'.'+suffix])
            world_delta(before,snapshots[c['name']+'.after-filler'],c,'filler');world_delta(snapshots[c['name']+'.after-filler'],snapshots[c['name']+'.mixed-before'],c,'add');world_delta(snapshots[c['name']+'.mixed-before'],snapshots[c['name']+'.after-mixed'],c,'mixed')
    operations=evidence.read(folder/'operations-final.state.json');final=evidence.read(folder/'final.state.json');base.equal_except_selection(operations,final)
    expected=copy.deepcopy(ready)
    if mode=='operate':
        for c in CASES:
            identity=expected['party'][c['pc']-1]['runtime_id']
            for group in('party','current_area_actors'):
                actor=next(a for a in expected[group]if a['runtime_id']==identity);p=page(actor,c['kind'],c['level']);p['memorized']=changed(p['memorized'],c,'filler')
    base.equal_except_selection(expected,operations)
    extras=[(e['step'],e['pack'],e['window'],e['control'])for e in events if e['step']<0];expectedextras=[(-1,'GUILOAD',0,26)]+([(-2,'GUIOPT',2,6),(-3,'GUISAVE',0,26),(-4,'GUISAVE',1,7)]if mode=='operate'else[])
    if extras!=expectedextras or(mode=='operate'and len(host['saves'])!=1)or(mode=='reload'and host['saves']):raise ValueError('Ordinary load/save chain differs')
    return dict(save=host['saves'][0]if mode=='operate'else None,callbacks=len(events),captures=len(observed),books=['mage','priest'],option_loaded=initial['option'],mixed_charged_survives=mode=='operate',original_parity=None)
