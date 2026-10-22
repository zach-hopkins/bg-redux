"""Strict debug setup boundaries and current stock inn characterization."""
from pathlib import Path
import copy
import re
import struct
import minsc_recruitment_journey as checkpoint
import spellbook_operation_validation as base
import saved_npc_color_journey as common
import saved_npc_color_fixtures as binary
import weapon_query_validation as evidence
import spellbook_erase_journey as erase

PINS={'AR0704.are':('are',1010,'c8061c51f2e009917a0b95ba537456da7adf3b308de4d202bbbdc8f8b41d1d32'),
 'WINNKEEP.cre':('cre',1009,'a42acbb669745443db9a263c09634474b406644642d2cf346d191bced2d9e851'),
 'WINNKEEP.dlg':('dlg',1011,'7500056e91ebf0abbd8e43f4045aae119d4ba44c396855110a6c71614029d98e'),
 'WINNKEEP.sto':('sto',1014,'d76502ca4a177d8c52eb0d1699b6d54d4b5004d9cbc2b9830b78c86d5cd559d4'),
 'guistore.chu':('chu',1002,None),'action.ids':('ids',1008,None),'trigger.ids':('ids',1008,None)}
POINTS=[[690,550],[730,550],[690,590],[730,590]]

def resolved_dialogue(raw,table,words,state,scene):
    lines=[line.split('//',1)[0].split() for line in table.decode('ascii').splitlines()]
    if [r for r in lines if r and r[0]=='SIRMAAM']!=[['SIRMAAM','-1','27473','27475']]:raise ValueError('Wrong current-speaker gender rule')
    if set(words)!={'27473','27475'} or any(not isinstance(w,str) or not w or '<' in w or '>' in w for w in words.values()):raise ValueError('Wrong gender words')
    speaker=[a for a in state['party'] if a['runtime_id']==scene['dialogue_speaker']]
    if len(speaker)!=1 or not scene['in_dialog']:raise ValueError('Actual dialogue speaker absent')
    actor=speaker[0];sex=actor['modified_stats'][35]
    if type(sex)is not int or not 0<=sex<=0xffffffff:raise ValueError('Invalid actual speaker sex')
    if any(t!='<SIRMAAM>' for t in re.findall(r'<[^<>]*>',raw)):raise ValueError('Unsupported dialogue token')
    result=raw.replace('<SIRMAAM>',words['27475' if sex==2 else '27473'])
    if '<' in result or '>' in result:raise ValueError('Unresolved dialogue token')
    return result

def plan(mode):
    if mode not in ('prepare','observe'):raise ValueError('Unsupported inn mode')
    result=['debug-transfer','transferred-zero-gold']if mode=='prepare'else['reloaded-checkpoint']
    result+=['talk','response','dialogue-end','inn-room-page','room-zero','room-selected','rent']
    result+=['zero-gold-error','error-done','after-error']if mode=='prepare'else['current-forced-confirmation','cancel','after-cancel']
    return result+['store-done','closed']+(['debug-add-100','checkpoint']if mode=='prepare'else[])

def resource_guard(api,project,source):
    game=project/'phase0-local/bg2ee-clean';rows={};cache={};specs=dict(PINS)
    def read(name,ext,kind,sha):
        ref=name.rsplit('.',1)[0];api.probe_ui_resources.TYPES[ext]=kind
        for category in ('override/bg2ee','override/shared','unhardcoded/bg2ee','unhardcoded/shared'):
            if (source/'gemrb'/category/name).exists():raise ValueError('Unexpected engine inn resource shadow')
        raw,origin=api.probe_ui_resources.read_resource(ref.lower(),ext)
        provider=(game/Path(origin.replace('\\','/'))).resolve()if origin else None
        if not raw or len(raw)>8*1024*1024 or provider is None or not provider.is_relative_to(game.resolve()):raise ValueError('Resource/provider bounds')
        digest=binary.digest(raw)
        if sha and digest!=sha:raise ValueError('Wrong stock inn resource: '+name)
        key=str(provider)
        if key not in cache:cache[key]=evidence.sha(provider)
        return dict(raw=raw,extension=ext,provider=key,provider_sha256=cache[key],sha256=digest,bytes=len(raw),origin=origin,policy='exact-stock-inn-debug-fixture')
    for name,(ext,kind,sha)in specs.items():rows[name]=read(name,ext,kind,sha)
    gender,provider,policy=erase.gender_provider(api,source)
    rows['gender.2da']=dict(raw=gender,extension='2da',provider=provider,provider_sha256=evidence.sha(provider),sha256=binary.digest(gender),bytes=len(gender),policy=policy)
    scripts={'BALDUR','BDDEFAI',text(rows['AR0704.are']['raw'],0x94,8).upper()}
    scripts.update(text(rows['WINNKEEP.cre']['raw'],offset,8).upper()for offset in (0x248,0x250,0x258,0x260,0x268))
    for ref in sorted(scripts-{'','NONE'}):rows[ref+'.bcs']=read(ref+'.bcs','bcs',1007,None)
    jumps=re.findall(rb'(?im)^\s*(\d+)\s+JumpToPoint\s*\(',rows['action.ids']['raw'])
    if len(jumps)!=1:raise ValueError('Actual action.ids lacks unique parsed JumpToPoint')
    rows['action.ids']['jump_action_id']=int(jumps[0])
    raw=(game/'lang/en_US/dialog.tlk').read_bytes();refs=(30197,33355,28755,28763,28771,9371,11051,15358,11973,13727,27473,27475);strings={}
    if raw[:8]!=b'TLK V1  ':raise ValueError('TLK signature')
    for ref in refs:
        if ref>=binary.u32(raw,10):raise ValueError('TLK ref bounds')
        at=18+26*ref;strings[str(ref)]=binary.block(raw,binary.u32(raw,14)+binary.u32(raw,at+18),binary.u32(raw,at+22)).decode('utf8')
        if not strings[str(ref)]:raise ValueError('Empty pinned inn text')
    rows['strings']=dict(values=strings)
    for name,file in (('chitin',game/'chitin.key'),('tlk',game/'lang/en_US/dialog.tlk')):rows[name]=dict(path=str(file),bytes=file.stat().st_size,sha256=evidence.sha(file))
    return rows

def text(raw,at,size):return binary.block(raw,at,size).split(b'\0')[0].decode('ascii')
def wire(folder):
    raw=common.member(folder,'gam').read_bytes()
    if raw[:8]!=b'GAMEV2.0'or binary.u32(raw,0x24)!=4:raise ValueError('Four-party GAMEV2.0 required')
    count=4;table=binary.u32(raw,0x20);binary.block(raw,table,count*0x160);locations=[]
    for i in range(count):
        at=table+i*0x160;locations.append(dict(area=text(raw,at+24,8).upper(),position=[binary.u16(raw,at+32),binary.u16(raw,at+34)]))
    target=None;members=[r for r in binary.sav_records(common.member(folder,'sav').read_bytes())if r['name'].casefold()=='ar0704.are']
    if len(members)>1:raise ValueError('Duplicate saved inn area')
    if members:
        area=binary.inflate(members[0]);base_=binary.u32(area,0x54);n=binary.u16(area,0x58);binary.block(area,base_,n*272);found=[]
        for i in range(n):
            at=base_+272*i
            start,size=binary.u32(area,at+136),binary.u32(area,at+140);cre=binary.block(area,start,size);binary.validate_cre(cre)
            if text(cre,0x2cc,8).upper()!='WINNKEEP'or binary.u32(cre,8)!=30197:continue
            found.append(dict(name_ref=30197,dialog='WINNKEEP',position=[binary.u16(area,at+32),binary.u16(area,at+34)],talk_count=binary.u32(area,at+68),cre_sha256=binary.digest(cre)))
        if len(found)!=1 or found[0]['position']!=[786,408]:raise ValueError('Saved exact stock inn target absent/duplicate')
        target=found[0]
    return dict(checkpoint=checkpoint.wire(folder,True),spellbooks=base.wire_spellbooks(folder),gold=binary.u32(raw,0x18),locations=locations,inn_target=target)

def wire_state_guard(parsed,state):
    checkpoint.wire_state_guard(parsed['checkpoint'],state);base.wire_state_guard(parsed['spellbooks'],state)
    if parsed['gold']!=state['gold']or parsed['locations']!=[dict(area=a['area'].upper(),position=a['position'])for a in state['party']]:raise ValueError('Saved gold/party area/positions differ from actual state')
    return True

def wire_setup_guard(before,after):
    if before['gold']!=0 or after['gold']!=100 or [r['area']for r in before['locations']]!=['AR0602']*4 or [r['area']for r in after['locations']]!=['AR0704']*4:raise ValueError('Undeclared saved area/currency setup')
    if before['checkpoint']!=after['checkpoint']or before['spellbooks']!=after['spellbooks']:raise ValueError('Debug setup altered retained quest/items/XP/spellbooks')
    if before['inn_target']is not None or not after['inn_target']or after['inn_target']['talk_count']!=1:raise ValueError('Wrong saved first inn conversation')
    # Ordinary TryToTalk walks the leader to the keeper after debug completion.
    # Exact saved coordinates are separately bound to the final native snapshot.
    for row in after['locations']:
        if sum((a-b)**2 for a,b in zip(row['position'],[786,408]))>320**2:raise ValueError('Saved party not coherent near inn')

def party_guard(before,after):
    a=copy.deepcopy(before['party']);b=copy.deepcopy(after['party'])
    for rows in (a,b):
        for actor in rows:actor.pop('area');actor.pop('position')
    if a!=b or before['globals']!=after['globals']or before['journal']!=after['journal']:raise ValueError('Undeclared party/quest mutation during inn setup')

def setup_guard(command,before,after):
    if command==1:
        if before['gold']!=0 or after['gold']!=0 or before['current_area'].upper()!='AR0602'or any(a['area'].upper()!='AR0704'for a in after['party']):raise ValueError('Transfer did not move all four measured PCs')
        party_guard(before,after)
    elif command==2:
        if before['gold']!=0 or after['gold']!=100:raise ValueError('Currency must be exactly0 to100')
        a=copy.deepcopy(before);b=copy.deepcopy(after);a.pop('gold');b.pop('gold');base.equal_except_selection(a,b)
    else:raise ValueError('Not a declared setup command')

def transfer_completion(queued,completed,ids,jump):
    if len(ids)!=4 or len(set(ids))!=4 or [p['id']for p in queued['party']]!=ids or [p['id']for p in completed['party']]!=ids:raise ValueError('Transferred actor identity/order differs')
    if any(p['area'].upper()!='AR0704'or jump not in(p['current'],p['next'])for p in queued['party']):raise ValueError('Parsed JumpToPoint was not queued for every moved slot')
    if completed['area'].upper()!='AR0704'or not completed['idle']or any(p['area'].upper()!='AR0704'or p['current']is not None or p['next']is not None or p['moving']for p in completed['party']):raise ValueError('Queued transfer completion absent')
    for p,wanted in zip(completed['party'],POINTS):
        if sum((a-b)**2 for a,b in zip(p['position'],wanted))>96**2:raise ValueError('Transfer positions incoherent')

def validate_capture(folder,nonce,mode,started_ns,receipt):
    host=evidence.read(folder/'book-result.json');runtime=evidence.read(folder/'book-runtime.json');expected=plan(mode)
    if not re.fullmatch('[0-9a-f]{32}',nonce)or host.get('schema')!='bg-redux-inn-host/1'or host.get('nonce')!=nonce or host.get('mode')!=mode or host.get('completed')is not True or host.get('error')or host.get('ordinary_campaign_transfer')is not False or host.get('declared_debug_setup')is not True or host.get('os_pointer_input')is not False or host.get('production_inn_policy_changed')is not False:raise ValueError('Stale/forced/misrepresented inn host')
    if runtime.get('schema')!='bg-redux-inn-runtime/1'or runtime.get('nonce')!=nonce or runtime.get('mode')!=mode or runtime.get('planned')!=expected or runtime.get('steps')!=len(expected)or runtime.get('completed')is not True or runtime.get('ordinary_campaign_transfer')is not False or runtime.get('debug_setup_declared')is not True:raise ValueError('Independent inn plan incomplete')
    if started_ns is not None and any(p.stat().st_mtime_ns<started_ns for p in folder.iterdir()if p.is_file()):raise ValueError('Stale inn artifact')
    rows=runtime['rows'];events=host['events'];commands=host['commands'];samples=host['startup']
    if [r['step']for r in rows]!=list(range(len(expected)))or events!=evidence.read(folder/'book-events.json')or commands!=evidence.read(folder/'inn-commands.json')or samples!=evidence.read(folder/'book-startup.json'):raise ValueError('Raw runtime/callback/command inventory differs')
    cmd_names={'debug-transfer':1,'debug-add-100':2,'talk':3,'response':4,'dialogue-end':5}
    control_names={'room-zero','rent','error-done','cancel','store-done'}
    for i,row in enumerate(rows):
        name=expected[i];kind='command-request'if name in cmd_names else'request'if name in control_names else'observe'
        if row['event']!=kind or kind=='command-request'and row['command']!=cmd_names[name]:raise ValueError('Fixed inn plan command/callback type differs')
    ready=evidence.read(folder/'ready.state.json');loaded=evidence.read(folder/'loaded.state.json')
    if len(ready['party'])!=4 or ready['current_area'].upper()!=('AR0602'if mode=='prepare'else'AR0704')or len(samples)<4 or any(not r['idle']for r in samples[-4:])or ready['game_time']<loaded['game_time']+30:raise ValueError('Natural four-idle startup absent')
    for i,s in enumerate(samples):
        state=evidence.read(folder/(s['checkpoint']+'.state.json'));scene=evidence.read(folder/(s['checkpoint']+'.scene.json'))
        if s['game_time']!=state['game_time']or scene['game_time']!=state['game_time']or s['idle']!=scene['idle']or i and(s['tick']<=samples[i-1]['tick']or s['game_time']<samples[i-1]['game_time']):raise ValueError('Startup evidence contradictory')
    wanted_commands=[1,3,4,5,2]if mode=='prepare'else[3,4,5]
    requested=[r for r in rows if r['event']=='command-request']
    if [r['command']for r in commands]!=wanted_commands or len(commands)!=len(requested)or host['talk_requests']!=1:raise ValueError('Missing/extra debug or talk/selection command')
    for i,(c,r)in enumerate(zip(commands,requested),1):
        if(c['nonce'],c['sequence'],c['step'],c['command'])!=(nonce,i,r['step'],r['command'])or c['queued_completion_pending']!=(c['command']!=2):raise ValueError('Command binding/nonce/entry-completion scope differs')
        before=evidence.read(folder/('command-%d-before.state.json'%i));after=evidence.read(folder/('command-%d-after.state.json'%i))
        if c['command']in(1,2):setup_guard(c['command'],before,after)
        elif before['gold']!=after['gold']:raise ValueError('Ordinary conversation changed currency')
    for branch,ref in ((0,28755),(1,28771)):
        text_=evidence.read(folder/('branch-%d.text.json'%branch));scene=evidence.read(folder/('branch-%d.scene.json'%branch))
        strings=receipt['resources']['strings']['values'];table=(folder/'gender.2da.runtime').read_bytes()
        if binary.digest(table)!=receipt['resources']['gender.2da']['sha256']:raise ValueError('Runtime gender table drift')
        resolved=resolved_dialogue(strings[str(ref)],table,{k:strings[k] for k in ('27473','27475')},evidence.read(folder/('branch-%d.state.json'%branch)),scene)
        if text_.get('nonce')!=nonce or text_['strref']!=ref or text_['occurrences_after']<=text_['occurrences_before']or text_['text'].count(resolved)!=text_['occurrences_after']or text_['previous'].count(resolved)!=text_['occurrences_before']:raise ValueError('Fresh stock dialogue text not observed')
        if branch==0 and '1. - '+receipt['resources']['strings']['values']['28763']not in text_['text']:raise ValueError('Pinned first response missing')
        if scene['target_position']!=[786,408]or scene['target_dialog'].upper()!='WINNKEEP'or scene['dialogue_target']!=scene['target_id']or scene['dialogue_speaker']!=ready['party'][0]['runtime_id']or scene['talk_count']!=(1 if mode=='prepare'else 2):raise ValueError('Wrong actual talk target/speaker/counter')
    labels=evidence.read(folder/'dialogue-end-label.json')
    if labels['raw_strref']!=9371 or labels['expected']!=labels['actual']or not labels['actual']:raise ValueError('Stock End callback label differs')
    requests=[r for r in rows if r['event']=='request'];dispatch=[e for e in events if e['step']>=0]
    if host['callbacks']!=len(events)or len(requests)!=len(dispatch):raise ValueError('Actual callback count differs')
    routes={'room-zero':('GUISTORE',7,0),'rent':('GUISTORE',7,11),'error-done':('GUISTORE',10,0),'cancel':('GUISTORE',11,1),'store-done':('GUISTORE',3,0)}
    for r,e in zip(requests,dispatch):
        if e['step']!=r['step']or tuple(e[k]for k in ('pack','window','control'))!=routes[expected[r['step']]]:raise ValueError('Ordinary inn callback route differs')
        base.request_value_guard(r,e)
    for i,e in enumerate(events,1):
        if e['sequence']!=i or e['nonce']!=nonce or e.get('performed')is not True:raise ValueError('Stale callback event')
        before=evidence.read(folder/('callback-%d-before.state.json'%i));after=evidence.read(folder/('callback-%d-after.state.json'%i))
        if base.callback_game_boundary(e,before,after):continue
        base.equal_except_selection(before,after)
    captures={};obs=[r for r in rows if r['event']=='observe'];expected_obs=[n for n in expected if n in ('transferred-zero-gold','reloaded-checkpoint','inn-room-page','room-selected','zero-gold-error','after-error','current-forced-confirmation','after-cancel','closed','checkpoint')]
    if [r['name']for r in obs]!=expected_obs or host['captures']!=len(obs)or len(list(folder.glob('capture-*.bmp')))!=len(obs):raise ValueError('Inn observation inventory incomplete')
    for i,r in enumerate(obs,1):
        meta=evidence.read(folder/('capture-%d.inn.json'%i));state=evidence.read(folder/('capture-%d.state.json'%i));scene=evidence.read(folder/('capture-%d.scene.json'%i));ui=evidence.read(folder/('capture-%d.ui.json'%i));name=r['name'];gold=100 if mode=='observe'or name=='checkpoint'else 0
        if(meta.get('schema'),meta.get('nonce'),meta.get('mode'),meta.get('name'),meta.get('step'),meta.get('capture'))!=('bg-redux-inn-observation/1',nonce,mode,name,r['step'],i)or r['capture']!=i or meta['gold']!=gold or state['gold']!=gold or scene['gold']!=gold or state['current_area'].upper()!='AR0704'or any(a['area'].upper()!='AR0704'for a in state['party']):raise ValueError('Inn capture identity/gold/area differs')
        party_guard(ready,state)
        if meta['option']!=0:raise ValueError('Current forced-prompt characterization requires observed optionOFF')
        store_expected=name in ('inn-room-page','room-selected','zero-gold-error','after-error','current-forced-confirmation','after-cancel')
        if (meta['store']is not None)!=store_expected or scene['store_present']!=store_expected or scene['in_dialog']:raise ValueError('Actual store/dialogue readiness differs')
        err=name=='zero-gold-error';confirm=name=='current-forced-confirmation'
        if meta['error']!=err or meta['confirmation']!=confirm:raise ValueError('Wrong affordability/confirmation modal boundary')
        for window,visible in ((10,err),(11,confirm)):
            found=[x for x in ui['controls']if x['pack']=='GUISTORE'and x.get('window')is None and x['id']==window and x['visible']]
            if bool(found)!=visible or len(found)>1:raise ValueError('Actual native inn modal visibility differs')
        if meta['store']is not None:
            store=meta['store']
            if store['StoreType']!=2 or store['StoreName']!=33355 or store['StoreButtons'][0]!=6 or store['StoreRoomPrices']!=[1,6,10,16]or store['StoreOwner']!=scene['target_id']:raise ValueError('Wrong actual inn/store owner/prices')
            if name!='inn-room-page'and meta['room']!=0:raise ValueError('Actual room0 not selected')
        if err and base.field(ui,'GUISTORE',10,3)['text']!=receipt['resources']['strings']['values']['11051']:raise ValueError('Wrong actual affordability error')
        if confirm and base.field(ui,'GUISTORE',11,3)['text']!=receipt['resources']['strings']['values']['15358']:raise ValueError('Wrong actual rent confirmation')
        base.bmp_region_sha(folder/('capture-%d.bmp'%i),[0,0,1,1]);captures[name]=(state,scene)
    if mode=='prepare':
        selection=evidence.read(folder/'debug-selection.json')
        if selection.get('nonce')!=nonce or selection.get('actor_ids')!=[a['runtime_id']for a in ready['party']]or selection.get('selected')!=[True]*4:raise ValueError('Actual select-all transfer boundary absent')
        transfer_completion(evidence.read(folder/'command-1-after.scene.json'),evidence.read(folder/'debug-transfer-complete.scene.json'),[a['runtime_id']for a in ready['party']],receipt['resources']['action.ids']['jump_action_id'])
    final=evidence.read(folder/'final.state.json');operations=evidence.read(folder/'operations-final.state.json');base.equal_except_selection(operations,final)
    extra=[e for e in events if e['step']<0];wanted=[(-1,'GUILOAD',0,26)]+([(-2,'GUIOPT',2,6),(-3,'GUISAVE',0,26),(-4,'GUISAVE',1,7)]if mode=='prepare'else[])
    if [(e['step'],e['pack'],e['window'],e['control'])for e in extra]!=wanted:raise ValueError('Actual normal load/save chain differs')
    if mode=='prepare':
        if len(host['saves'])!=1 or evidence.read(folder/'save-name.json')!=dict(control=3,nonce=nonce,performed=True)or evidence.read(folder/'before-save.state.json')!=final:raise ValueError('Checkpoint GUI save incomplete')
    elif host['saves']!=[]:raise ValueError('Observation process unexpectedly saved')
    return dict(save=host['saves'][0]if mode=='prepare'else None,debug_transfer=mode=='prepare',debug_added_gold=100 if mode=='prepare'else 0,zero_gold_affordability_observed=mode=='prepare',current_forced_prompt_at_option_off=mode=='observe',talk_requests=1,callbacks=len(events),observations=len(obs),ordinary_campaign_transfer=False,original_parity=None,rest_or_charge_observed=False)
