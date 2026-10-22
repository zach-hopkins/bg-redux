"""External one-shot key/Cell01/Jaheira checkpoint from one measured parent save.

Build and run are explicit coordinator operations; pure evidence readers never launch.
"""
import argparse
from collections import Counter
import os
from pathlib import Path
import re
import shutil
import struct
import time
import uuid
import saved_npc_color_journey as common
import saved_npc_color_fixtures as binary
import weapon_query_observer as shared
import weapon_query_validation as evidence

HERE=Path(__file__).resolve().parent
KIND='bg-redux-cell-recruitment-host/1'
PARENT='20261022T042747Z-jaheira-dialogue-30a50511'
PARENT_RESULT='d1d8a784ff203df8793bc4e0726deb67f95b6dd896c17095f6d6ce33f4a1bd3d'
PARENT_MANIFEST='958f1cd894cb5acc14a0feb5b59943306566292ff40d59e062a79d92f8176a1b'
PARENT_GAM='7925bdbcf11c3833f41ecae8f6fbd02c12b9948d2e845ca0e150a4c3c6c34cff'
PARENT_SAV='f102de5734ea685d75f1b9afc2a239d16d955fae41506b5f3180fe9ae45c6e43'
SNAPSHOT_SHA='3efce63ac88475b7e0e1ad93ff6370b402d397dee5166960d179379cf2af396d'
DLG_SHA='b121dc6d804e52e431c15a1d2dd372b5242f518a31d925ce403c3e633882bbc9'
TLK_SHA='9e685225ff3c3436a8a35fa7022550620d24a92efe35436a062c02955d9f0952'
SCRIPT_SHA='5b1b0407167d3b5d06f98aad087c7d0b7656186bb9881210fefb2b272d9758be'
KEY_SHA='36d1c437ab1f502d2b1afa3eefa69db85a3d556a8cf50ed94694a63300ae879f'
RESOURCE_TYPES={'jaheira':('dlg',1011),'misc4b':('itm',1005),'action':('ids',1008),'pdialog':('2da',1012),'jaheira-script':('bcs',1007),'trigger':('ids',1008),'object':('ids',1008)}
TABLE_ITEMS=['SW1H04','SW1H07','STAF01','BLUN04','AX1H01','SPER01','HALB01','MISC4B','HAMM01','SW2H01','SW1H43']


def sources(project,source):
    local=['cell_recruitment_journey.py','RecruitStart.py','native/recruitment_journey.cpp','native/recruitment_dialogue_snapshot.cpp']
    engine=['core/GUI/GameControl.cpp','core/GUI/GameControl.h','core/GUI/Control.cpp','core/GUI/ScrollBar.cpp','core/GUI/TextArea.cpp','core/GUI/TextArea.h','core/GUI/View.h','core/GUI/Button.cpp','core/GUI/Button.h','core/GUI/TextSystem/TextContainer.h','core/GUI/TextSystem/TextContainer.cpp','core/DialogHandler.cpp','core/Dialog.h','core/Game.cpp','core/Inventory.cpp','core/GameScript/Actions.cpp','core/GameScript/GameScript.cpp','core/GameScript/GSUtils.cpp','core/GameScript/ParseText.cpp','core/Scriptable/Scriptable.cpp','core/Scriptable/Scriptable.h','core/Scriptable/Actor.cpp','core/Scriptable/Door.cpp','core/Scriptable/Door.h','core/Scriptable/Highlightable.cpp','core/Interface.cpp','core/InterfaceConfig.cpp','core/ResourceManager.cpp','core/Streams/SlicedStream.cpp','plugins/AREImporter/AREImporter.cpp','plugins/GAMImporter/GAMImporter.cpp','plugins/CREImporter/CREImporter.cpp','plugins/DLGImporter/DLGImporter.cpp','plugins/KEYImporter/KEYImporter.cpp','plugins/BIFImporter/BIFImporter.cpp','plugins/DirectoryImporter/DirectoryImporter.cpp','plugins/GUIScript/GUIScript.cpp','GUIScripts/Container.py','GUIScripts/GUIWORLD.py','GUIScripts/GUICommonWindows.py','GUIScripts/GUIOPT.py','GUIScripts/GUISAVE.py','GUIScripts/GUILOAD.py']
    engine += ['GUIScripts/'+name for name in ('GUIMG.py','GUIPR.py','EESpellbookHeading.py','EESpellbookInformation.py','BG2EEConfirmation.py','GUIOPT.py','GUIOPTControls.py','GUICommon.py','GUICommonWindows.py','Spellbook.py','GameCheck.py','GUIDefines.py','GUIClasses.py')]
    engine += ['unhardcoded/shared/defaults.ini']
    return sorted(set(common.sources(project)+[HERE/p for p in local]+[source/'gemrb'/p for p in engine]))


def source_guard(receipt,project,source):
    if set(receipt.get('sources',{}))!={str(p) for p in sources(project,source)}:raise ValueError('Recruitment source closure differs')
    for name,row in receipt['sources'].items():
        if evidence.sha(name)!=row['sha256'] or evidence.sha(row['frozen'])!=row['sha256']:raise ValueError('Recruitment source/frozen drift')


def save_manifest(folder,party):
    if party not in (2,3):raise ValueError('Only declared two/three-party saves supported')
    rows=binary.manifest(folder);names={n.casefold() for n in rows};required={'baldur.gam','baldur.sav','baldur.bmp'}|{'portrt%d.bmp'%i for i in range(party)}
    if len(names)!=len(rows) or names!=required or any(r['bytes']==0 for r in rows.values()):raise ValueError('Exact declared party save file inventory differs')
    return rows


def parent_proof(project):
    root=project/'phase1-local/results'/PARENT
    if evidence.sha(root/'result.json')!=PARENT_RESULT or evidence.sha(root/'artifact-manifest.json')!=PARENT_MANIFEST:raise ValueError('Measured parent receipt/manifest hash differs')
    receipt=evidence.read(root/'result.json');manifest=evidence.read(root/'artifact-manifest.json')['files']
    if receipt.get('schema')!='bg-redux-jaheira-journey/1' or receipt.get('passed')is not True or receipt.get('inputs_preserved')is not True or receipt.get('candidate_preserved')is not True or receipt.get('phase0_preservation')!=dict(source=True,binaries=True,fixture=True):raise ValueError('Measured parent proof is not accepted')
    for relative,pin in manifest.items():
        path=(root/relative).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file() or path.stat().st_size!=pin['bytes'] or evidence.sha(path)!=pin['sha256']:raise ValueError('Parent artifact evidence drift/escape: '+relative)
    stages=receipt['stages']
    if len(stages)!=2 or [s['journey'] for s in stages]!=['talk','reload'] or not all(s.get('passed')is True for s in stages):raise ValueError('Parent talk/reload chain incomplete')
    for stage in stages:shared.require_process(stage['process'])
    if stages[0]['process']['pid']==stages[1]['process']['pid']:raise ValueError('Parent reload was not a fresh process')
    incoming=root/'talk/frozen-save';files=save_manifest(incoming,2)
    if files!=stages[0]['frozen_save_files'] or stages[1]['input_files']!=files or Path(stages[0]['frozen_save']).resolve()!=incoming.resolve():raise ValueError('Parent saved-output/load-input chain differs')
    if evidence.sha(common.member(incoming,'gam'))!=PARENT_GAM or evidence.sha(common.member(incoming,'sav'))!=PARENT_SAV:raise ValueError('Wrong measured frozen save')
    original=project/'phase0-local/fixtures/original-bg2ee-20261020/GemRB'
    if common.save_manifest(original)!=stages[0]['input_files']:raise ValueError('Parent proof no longer binds protected P0 fixture')
    return dict(parent=str(root),result_sha256=PARENT_RESULT,manifest_sha256=PARENT_MANIFEST,input=str(incoming),files=files,artifact_count=len(manifest),phase0_fixture_files=stages[0]['input_files'])



def require_id(raw,label,expected):
    values=set()
    for line in raw.decode('ascii').splitlines():
        parts=line.split(None,1)
        if len(parts)!=2 or parts[1].split('(')[0].strip().casefold()!=label.casefold():continue
        try:value=int(parts[0],0)
        except ValueError:
            try:value=int(parts[0])
            except ValueError:continue
        values.add(value)
    if values!={expected}:raise ValueError('Actual IDS binding differs: '+label)

def resource_guard(api,project,source):
    game=project/'phase0-local/bg2ee-clean';result={}
    for name,(ext,kind) in RESOURCE_TYPES.items():
        api.probe_ui_resources.TYPES[ext]=kind;resref=name.split('-')[0]
        for category in ('override/bg2ee','override/shared','unhardcoded/bg2ee','unhardcoded/shared'):
            if (source/'gemrb'/category/(resref+'.'+ext)).exists():raise ValueError('Unexpected engine recruitment resource provider shadow')
        raw,origin=api.probe_ui_resources.read_resource(resref,ext)
        if not raw or len(raw)>8*1024*1024:raise ValueError('Required recruitment resource missing/bounds')
        digest=binary.digest(raw)
        if (name=='jaheira' and digest!=DLG_SHA) or (name=='misc4b' and digest!=KEY_SHA) or (name=='jaheira-script' and digest!=SCRIPT_SHA):raise ValueError('Pinned DLG/key item differs')
        if name=='action':require_id(raw,'StartDialogueNoSet',198)
        if name=='trigger':
            for label,value in [('OpenState',16502),('See',16412),('Global',16399)]:require_id(raw,label,value)
        if name=='object':require_id(raw,'Player1',21)
        provider=(game/Path(origin.replace('\\','/'))).resolve()
        if not provider.is_relative_to(game.resolve()):raise ValueError('Resource provider escapes clean game')
        result[name]=dict(raw=raw,origin=origin,provider=str(provider),provider_sha256=evidence.sha(provider),sha256=digest,bytes=len(raw),extension=ext)
    for name,path in [('chitin',game/'chitin.key'),('tlk',game/'lang/en_US/dialog.tlk')]:
        result[name]=dict(path=str(path),sha256=evidence.sha(path),bytes=path.stat().st_size)
    if result['tlk']['sha256']!=TLK_SHA:raise ValueError('Pinned English TLK differs')
    return result


def check_resources(receipt,api,project,source):
    current=resource_guard(api,project,source)
    for name,row in receipt['resources'].items():
        wanted={k:v for k,v in current[name].items() if k!='raw'}
        if {k:v for k,v in row.items() if k!='frozen'}!=wanted or ('frozen'in row and evidence.sha(row['frozen'])!=row['sha256']):raise ValueError('Recruitment resource/provider drift')


def check_runtime_resources(folder,receipt):
    rows=evidence.read(folder/'recruitment-providers.json')
    if rows.get('schema')!='bg-redux-recruitment-providers/1' or set(rows.get('resources',{}))!=set(RESOURCE_TYPES):raise ValueError('Actual resource provider closure incomplete')
    for name,row in rows['resources'].items():
        expected=receipt['resources'][name]
        if Path(row.get('originalfile','')).resolve()!=Path(expected['provider']).resolve() or row.get('bytes')!=expected['bytes'] or evidence.sha(folder/(name+'.runtime'))!=expected['sha256']:raise ValueError('Runtime recruitment provider/bytes differs: '+name)
    return rows


def text(raw,at,length):return binary.block(raw,at,length).split(b'\0')[0].decode('ascii')

def item(raw,at):
    return dict(resref=text(raw,at,8).upper(),expired=binary.u16(raw,at+8),usages=list(struct.unpack('<3H',binary.block(raw,at+10,6))),flags=binary.u32(raw,at+16))


def disjoint(spans):
    nonempty=[(start,size) for start,size in spans if size]
    for i,(start,size) in enumerate(nonempty):
        if start<0 or size<0 or any(max(start,x)<min(start+size,x+y) for x,y in nonempty[:i]):raise ValueError('Overlapping declared binary sections')

def wire(folder,joined):
    gam=common.member(folder,'gam').read_bytes();count=binary.u32(gam,0x24)
    if gam[:8]!=b'GAMEV2.0' or count!=(3 if joined else 2):raise ValueError('Wrong declared wire party')
    people=[];spans=[];sections=[(0,0xb4)]
    for group,off,count_at in [('party',0x20,0x24),('npcs',0x30,0x34)]:
        base,n=binary.u32(gam,off),binary.u32(gam,count_at)
        if n>1000 or (n and base<0xb4):raise ValueError('GAM actor table bounds')
        binary.block(gam,base,n*0x160);sections.append((base,n*0x160))
        for i in range(n):
            at=base+0x160*i;start,size=binary.u32(gam,at+4),binary.u32(gam,at+8)
            if start<base+n*0x160 or size<0x2d4 or any(max(start,x)<min(start+size,x+y) for x,y in spans):raise ValueError('GAM embedded actor range overlap/bounds')
            spans.append((start,size));cre=binary.block(gam,start,size);binary.validate_cre(cre)
            people.append(dict(group=group,index=i,name=text(cre,0x280,32).casefold(),dialog=text(cre,0x2cc,8).upper(),talk_count=binary.u32(gam,at+0xe0),items=[item(cre,binary.u32(cre,0x2bc)+20*j) for j in range(binary.u32(cre,0x2c0))],xp=binary.u32(cre,0x18)))
    target=[a for a in people if a['name']=='jaheira']
    if len(target)!=1 or target[0]['group']!=('party' if joined else 'npcs') or target[0]['dialog']!=('JAHEIRAJ' if joined else 'JAHEIRA') or target[0]['talk_count']!=(2 if joined else 1) or (joined and target[0]['index']!=2):raise ValueError('Wire Jaheira membership/identity/counter differs')
    area_rows=[r for r in binary.sav_records(common.member(folder,'sav').read_bytes()) if r['name'].casefold()=='ar0602.are']
    if len(area_rows)!=1:raise ValueError('Unique saved area required')
    area=binary.inflate(area_rows[0])
    if area[:8]!=b'AREAV1.0':raise ValueError('ARE V1 required')
    base,n=binary.u32(area,0xa8),binary.u32(area,0xa4)
    if n>1000 or base<0x11c:raise ValueError('Door table bounds')
    binary.block(area,base,n*200);door_span=(base,n*200);doors=[]
    for i in range(n):
        at=base+i*200
        if text(area,at,32).casefold()=='cell01':doors.append(dict(flags=binary.u32(area,at+40),key=text(area,at+120,8).upper(),trapped=binary.u16(area,at+112),lock_difficulty=binary.u32(area,at+140)))
    if doors!=[dict(flags=1633 if joined else 1634,key='MISC4B',trapped=0,lock_difficulty=100)]:raise ValueError('Wire Cell01 key/lock/open state differs')
    base,n,items,ni=binary.u32(area,0x70),binary.u16(area,0x74),binary.u32(area,0x78),binary.u16(area,0x76)
    if n>1000 or ni>10000 or base<0x11c or items<0x11c:raise ValueError('Container table bounds')
    binary.block(area,base,n*192);binary.block(area,items,ni*20);disjoint([(0,0x11c),door_span,(base,n*192),(items,ni*20)]);tables=[]
    for i in range(n):
        at=base+i*192;first,length=binary.u32(area,at+64),binary.u32(area,at+68)
        if first>ni or length>ni-first:raise ValueError('Container slice exceeds item table')
        if text(area,at,32)=='Jailkeep Table':tables.append([item(area,items+20*j) for j in range(first,first+length)])
    if len(tables)!=1 or [x['resref'] for x in tables[0]]!=[x for x in TABLE_ITEMS if not joined or x!='MISC4B']:raise ValueError('Wire table item inventory differs')
    globals_={};base,n=binary.u32(gam,0x38),binary.u32(gam,0x3c)
    if n>100000 or base<0xb4:raise ValueError('Global table bounds')
    binary.block(gam,base,n*84);sections.append((base,n*84))
    for i in range(n):
        at=base+84*i;name=text(gam,at,32).casefold()
        if name in globals_:raise ValueError('Duplicate wire global')
        globals_[name]=binary.u32(gam,at+40)
    if globals_.get('jaheirareleased',0)!=int(joined) or any(globals_.get(k,0) for k in ('jaheirajerk','jaheirahunt')):raise ValueError('Wire quest globals differ')
    base,n=binary.u32(gam,0x50),binary.u32(gam,0x4c)
    if n>10000 or base<0xb4:raise ValueError('Journal table bounds')
    binary.block(gam,base,n*12);sections.append((base,n*12));disjoint(sections+spans)
    journal=[dict(text_ref=binary.u32(gam,base+12*i),time=binary.u32(gam,base+12*i+4),chapter=gam[base+12*i+8],section=gam[base+12*i+10],group=gam[base+12*i+11]) for i in range(n)]
    quest_guard(journal,joined)
    if any(x['resref']=='MISC4B' for a in people if a['group']=='party' for x in a['items']):raise ValueError('Key not consumed/absent in expected wire checkpoint')
    return dict(party_count=count,target=target[0],party=[a for a in people if a['group']=='party'],door=doors[0],table=tables[0],journal=journal,globals=globals_)


def quest_guard(journal,joined):
    refs=Counter(j['text_ref'] for j in journal)
    if refs!=Counter([34089,96383,47519 if joined else 34105]):raise ValueError('Quest journal missing/duplicate/wrong entry')
    q=next(j for j in journal if j['text_ref']==(47519 if joined else 34105))
    if q['chapter']!=1 or q['section']!=(2 if joined else 1):raise ValueError('Quest journal section/chapter differs')



def wire_state_guard(parsed,state):
    evidence.require_state(state)
    if len(state['party'])!=parsed['party_count'] or state['journal']!=parsed['journal']:raise ValueError('Wire party/journal fields differ from captured actual state')
    def identities(items):return Counter((x['resref'].upper(),x.get('expired',0),tuple(x['usages'])) for x in items)
    for row,actor in zip(parsed['party'],state['party']):
        if row['name']!=actor['script_name'].casefold() or identities(row['items'])!=identities(runtime_items(actor['inventory'])) or row['xp']!=actor['base_stats'][44]:raise ValueError('Wire actual party identity/inventory/XP differs')
    globals_={k.casefold():v for k,v in state['globals'].items()}
    if any(globals_.get(k,0)!=parsed['globals'].get(k,0) for k in ('jaheirareleased','jaheirahunt','jaheirajerk')):raise ValueError('Wire quest globals differ from actual state')
    return dict(identity_charges_xp_and_quest_matched=True,flags_scope='All raw flags retained; wire/runtime extension flag representation is not equated.')

def runtime_items(inv):
    items=inv['items'];slots=[x['slot'] for x in items]
    if len(slots)!=len(set(slots)):raise ValueError('Duplicate runtime item slots')
    return [x for x in items if x['slot']!=inv.get('fist_slot',-1)]

def item_counts(items):
    return Counter((x['resref'].upper(),x.get('expired',0),tuple(x['usages']),x['flags']&~0x10) for x in items)


def scene_guard(scene,state,joined=None):
    evidence.require_state(state)
    if scene.get('schema')!='bg-redux-recruitment-scene/1' or state['current_area'].upper()!='AR0602' or scene.get('game_time')!=state['game_time'] or scene.get('party_count')!=len(state['party']) or len(state['party'])not in (2,3):raise ValueError('Scene/full party/clock binding differs')
    targets=[a for a in state['current_area_actors'] if a['script_name'].casefold()=='jaheira']
    if len(targets)!=1 or targets[0]['runtime_id']!=scene.get('target_id') or scene.get('target_name','').casefold()!='jaheira' or scene.get('leader_id')!=state['party'][0]['runtime_id']:raise ValueError('Actual actor/target identity differs')
    target=targets[0];members=[a for a in state['party'] if a['script_name'].casefold()=='jaheira'];stored=[a for a in state['stored_npcs'] if a['script_name'].casefold()=='jaheira']
    if len(members)!=(len(state['party'])==3) or len(stored)!=(len(state['party'])==2) or target['in_party']!=scene.get('target_in_party'):raise ValueError('Duplicate/lost party/stored membership')
    keys=sum(x['resref'].upper()=='MISC4B' for a in state['party'] for x in runtime_items(a['inventory']))
    if scene.get('party_keys')!=keys or scene.get('table_keys')!=sum(x['resref'].upper()=='MISC4B' for x in scene['table_inventory']['items']):raise ValueError('Key count contradicts actual inventory')
    if scene.get('door_name')!='Cell01' or scene.get('door_key')!='MISC4B' or type(scene.get('door_flags'))is not int or scene['door_flags'] not in (1634,1633) or scene.get('door_open')!=bool(scene['door_flags']&1) or scene.get('door_locked')!=bool(scene['door_flags']&2):raise ValueError('Door lock/key/flags guard differs')
    if len(scene.get('party_actions',[]))!=len(state['party']):raise ValueError('Missing actor queue observations')
    for i,row in enumerate(scene['party_actions']):
        if row.get('id')!=state['party'][i]['runtime_id'] or row.get('position')!=state['party'][i]['position'] or type(row.get('moving'))is not bool:raise ValueError('Actual queue position/identity differs')
        for key in ('current','next'):
            if key not in row or (row[key]is not None and (set(row[key])!={'id','int0','resref'} or type(row[key]['id'])is not int)):raise ValueError('Missing/malformed current/next action')
    globals_={k.casefold():v for k,v in state['globals'].items()}
    for field,name in [('released','jaheirareleased'),('jerk','jaheirajerk'),('hunt','jaheirahunt'),('bd_defai','bd_defai')]:
        if scene.get(field)!=globals_.get(name,0):raise ValueError('Observed quest/global contradiction')
    if joined is not None:
        if len(state['party'])!=(3 if joined else 2) or scene['talk_count']!=(2 if joined else 1) or scene['target_dialog']!=('JAHEIRAJ' if joined else 'JAHEIRA') or scene['door_flags']!=(1633 if joined else 1634) or scene['party_keys']!=0 or scene['table_keys']!=int(not joined) or scene['released']!=int(joined) or scene['jerk'] or scene['hunt']:raise ValueError('Declared progression checkpoint missing')
        quest_guard(state['journal'],joined)
    return (scene['leader_id'],scene['target_id'],scene['door_id'],scene['table_id'])


def natural(scene):
    return not scene['in_dialog'] and scene['target_current']is None and scene['target_next']is None and not scene['target_moving'] and all(r['current']is None and r['next']is None and not r['moving'] for r in scene['party_actions']) and scene['selected_id']==scene['leader_id'] and scene['selected_count']==1 and scene['current_container']is None


def transfer(before,after,bs,as_):
    key=[x for x in bs['table_inventory']['items'] if x['resref'].upper()=='MISC4B']
    if len(key)!=1 or bs['party_keys']!=0 or as_['party_keys']!=1 or as_['table_keys']!=0:raise ValueError('One ordinary key acquisition not observed')
    moved=item_counts(key)
    if item_counts(as_['table_inventory']['items'])+moved!=item_counts(bs['table_inventory']['items']):raise ValueError('Table conservation failed')
    for i,(left,right) in enumerate(zip(before['party'],after['party'])):
        a,b=item_counts(runtime_items(left['inventory'])),item_counts(runtime_items(right['inventory']))
        if a+(moved if i==0 else Counter())!=b:raise ValueError('Actual key destination/other inventory conservation failed')


def validate_capture(folder,nonce,reload,started_ns,texts,action_ids):
    native=evidence.read(folder/'recruitment-result.json')
    if native.get('schema')!='bg-redux-recruitment-native/1' or native.get('nonce')!=nonce or native.get('journey')!=('reload' if reload else 'recruit') or native.get('completed')is not True or native.get('error') or native.get('os_pointer_input')is not False or native.get('forced_outcomes')is not False:raise ValueError('Wrong/stale/forced/incomplete native receipt')
    for name,want in [('container_commands',int(not reload)),('takes',int(not reload)),('closes',int(not reload)),('door_commands',int(not reload)),('talk_requests',0),('auto_dialogues',int(not reload)),('branches',0 if reload else 2)]:
        if type(native.get(name))is not int or native[name]!=want:raise ValueError('Missing/duplicate ordinary operation: '+name)
    if started_ns is not None and any(p.stat().st_mtime_ns<started_ns for p in folder.iterdir() if p.is_file()):raise ValueError('Stale capture evidence')
    samples=native.get('samples',[])
    if samples!=evidence.read(folder/'recruitment-samples.json') or not samples or len(samples)>(360 if reload else 720):raise ValueError('Missing/unbounded raw sample continuity')
    events=native['events']
    if events!=evidence.read(folder/'recruitment-events.json'):raise ValueError('Event prefix/result differs')
    kinds=['registered-button'] if reload else ['registered-button','ordinary-container-command','registered-scroll','registered-key-take','registered-container-close','ordinary-door-command','stock-auto-dialogue-observed','registered-recruit-response','registered-recruit-end','registered-button','registered-button','registered-save-name','registered-button']
    if [e.get('kind') for e in events]!=kinds:raise ValueError('Missing/reordered/repeated control sequence')
    if [e.get('sequence') for e in events]!=list(range(1,len(events)+1)) or any(e.get('nonce')!=nonce for e in events):raise ValueError('Event nonce/sequence mismatch')
    if any(type(e.get('tick'))is not int for e in events) or [e['tick'] for e in events]!=sorted(e['tick'] for e in events):raise ValueError('Event clock order differs')
    names=['loaded','ready','final']+([] if reload else ['before-container-command','after-container-command','before-scroll','before-key-take','after-key-take','before-door-command','after-door-command','door-open','auto-dialogue','branch-0','branch-1','dialogue-ended','recruited','before-save'])
    states={};scenes={};ids=None
    def load(name):
        nonlocal ids
        s=evidence.read(folder/(name+'.state.json'));c=evidence.read(folder/(name+'.scene.json'));ident=scene_guard(c,s)
        if ids is None:ids=ident
        if ident!=ids:raise ValueError('Within-process target/door/container identity changed')
        return s,c
    for name in names:
        states[name],scenes[name]=load(name)
        if name not in ('after-container-command','after-door-command'):
            raw=(folder/(name+'.bmp')).read_bytes()
            if len(raw)<54 or raw[:2]!=b'BM':raise ValueError('Missing checkpoint screenshot')
    scene_guard(scenes['loaded'],states['loaded'],reload);scene_guard(scenes['final'],states['final'],True)
    if events[0]['details']!=dict(pack='GUILOAD',window=0,control=26):raise ValueError('Actual load callback missing')
    prior_ticks=0;prior_time=-1;streaks={};sample_scenes=[]
    for row in samples:
        if type(row.get('tick'))is not int or row['tick']<=prior_ticks or row.get('checkpoint')!='sample-'+str(row['tick']) or type(row.get('phase'))is not int:raise ValueError('Raw phase sample index differs')
        s,c=load(row['checkpoint']);sample_scenes.append(c)
        if row.get('game_time')!=s['game_time'] or s['game_time']<prior_time or row.get('idle')is not natural(c):raise ValueError('Raw idle/clock assertion contradicted')
        p=row['phase'];streaks[p]=streaks.get(p,0)+1 if natural(c) else 0
        prior_ticks,prior_time=row['tick'],s['game_time']
    if not reload:
        phases={r['tick']:r['phase'] for r in samples}
        if [phases.get(e['tick']) for e in events[1:]]!=[0,1,2,2,3,4,5,5,7,8,9,10]:raise ValueError('Actual callback ticks do not bind their running/save phases')
    zero=[(r,c) for r,c in zip(samples,sample_scenes) if r['phase']==0]
    if len(zero)<4 or any(not natural(c) for _,c in zero[-4:]) or zero[-1][1]['game_time']<scenes['loaded']['game_time']+30 or scenes['ready']['bd_defai']!=1 or scenes['ready']['leader_class_script'].casefold()!='bddefai':raise ValueError('Natural readiness boundary absent')
    preserved=[j for j in states['loaded']['journal'] if j['text_ref']!=34105 and j['text_ref']!=47519]
    for s in states.values():
        if [j for j in s['journal'] if j['text_ref']not in (34105,47519)]!=preserved:raise ValueError('Preexisting journal fields changed')
    if reload:
        if native.get('saves')!=[]:raise ValueError('Reload must not issue a save/gameplay operation')
        for name in ('ready','final'):scene_guard(scenes[name],states[name],True)
        return dict(save=None,joined=True,samples=len(samples),operations=1,original_parity=None)
    if events[1]['details']!=dict(action_id=action_ids['UseContainer'],target_id=ids[3]) or events[2]['details'].get('control')!=52 or events[2]['details'].get('value')!=1 or events[2]['details'].get('dict_name','').casefold()!='lefttopindex':raise ValueError('Container command/real scrollbar differs')
    if events[3]['details']!=dict(control=4,dict_value=7,dict_name='LeftIndex',resref='MISC4B') or events[4]['details']!=dict(control=51):raise ValueError('Actual visible key binding/close callback differs')
    if events[5]['details']!=dict(action_id=action_ids['NIDSpecial9'],int0=ids[2],clicked_actor=ids[0],route='Mirrored HandleDoor/NIDSpecial9'):raise ValueError('Normal door command/target/clicked trigger differs')
    if events[6]['details']!=dict(target_id=ids[1],speaker_id=ids[0],route='Source-supported JAHEIRA.BCS/OpenState/StartDialogueNoSet; exact action may be between samples'):raise ValueError('Actual stock auto-dialogue participant/route differs')
    auto=scenes['auto-dialogue']
    if not auto['in_dialog'] or auto['speaker']!=ids[0] or auto['dialogue_target']!=ids[1] or auto['talk_count']!=2 or auto['released']!=1 or auto['target_in_party']!=0:raise ValueError('Natural auto-dialogue intermediate boundary missing')
    if events[7]['details']!=dict(state=33,npc_strref=1021,transition=75,response=1022,visible_index=0,entry='TextArea::SelectAvailableOption') or events[8]['details']!=dict(state=34,npc_strref=1026,transition=79,label_strref=9371):raise ValueError('Wrong recruitment branch/selector/End')
    for checkpoint,action in [('after-container-command',action_ids['UseContainer']),('after-door-command',action_ids['NIDSpecial9'])]:
        row=scenes[checkpoint]['party_actions'][0]
        if not any(a is not None and a['id']==action and (checkpoint!='after-door-command' or a['int0']==ids[2]) for a in (row['current'],row['next'])):raise ValueError('Actual queued command not observed')
    if scenes['after-container-command']['current_container']!=ids[3]:raise ValueError('Wrong actual current container')
    # Startup and ordinary approach must conserve all declared inventories.
    for first,last in [('loaded','before-container-command'),('before-container-command','before-key-take')]:
        if item_counts(scenes[first]['table_inventory']['items'])!=item_counts(scenes[last]['table_inventory']['items']) or any(item_counts(runtime_items(a['inventory']))!=item_counts(runtime_items(b['inventory'])) for a,b in zip(states[first]['party'],states[last]['party'])):raise ValueError('Key/source inventory changed before Take callback')
    transfer(states['before-key-take'],states['after-key-take'],scenes['before-key-take'],scenes['after-key-take'])
    if scenes['before-door-command']['party_keys']!=1 or scenes['before-door-command']['door_flags']!=1634 or scenes['door-open']['party_keys']!=0 or scenes['door-open']['door_flags']!=1633:raise ValueError('Actual unlock/open/key-consumption missing')
    for i,(a,b) in enumerate(zip(states['after-key-take']['party'],states['door-open']['party'])):
        expected=item_counts(runtime_items(a['inventory']))
        if i==0:expected.subtract(item_counts([x for x in runtime_items(a['inventory']) if x['resref'].upper()=='MISC4B']))
        if +expected!=item_counts(runtime_items(b['inventory'])):raise ValueError('Key consumption/other party inventory conservation differs')
    if scenes['before-container-command']['party_actions'][0]['position']==scenes['before-key-take']['party_actions'][0]['position'] or scenes['before-door-command']['party_actions'][0]['position']==scenes['door-open']['party_actions'][0]['position'] or not any(c['party_actions'][0]['moving'] for c in sample_scenes):raise ValueError('Ordinary approach movement not observed')
    for phase in (3,6):
        rows=[c for r,c in zip(samples,sample_scenes) if r['phase']==phase]
        if len(rows)<4 or any(not natural(c) for c in rows[-4:]):raise ValueError('Natural post-operation readiness absent')
    previous=evidence.read(folder/'auto-baseline.message.json')['observed_text']
    for index,ref in ((0,1021),(1,1026)):
        name='branch-'+str(index);row=evidence.read(folder/(name+'.text.json'));c=scenes[name]
        if row.get('expected_npc_strref')!=ref or row.get('expected_npc_text')!=texts[ref] or row.get('previous_text')!=previous or row.get('message_text','').count(texts[ref])<=previous.count(texts[ref]):raise ValueError('Stale/wrong actual dialogue transcript')
        if not c['in_dialog'] or c['speaker']!=ids[0] or c['dialogue_target']!=ids[1]:raise ValueError('Dialogue participant identity differs')
        previous=row['message_text']
        if index==0 and '1. - '+texts[1022]not in previous:raise ValueError('Actual numbered response absent')
    button=evidence.read(folder/'branch-1.button.json');flags=button.get('flags')
    if type(flags)is not int or button.get('raw_label')!=texts[9371]:raise ValueError('End label source missing')
    expected=texts[9371].lower() if flags&0x2000 else texts[9371].upper() if flags&8 else texts[9371]
    if button.get('expected_label')!=expected or button.get('actual_label')!=expected:raise ValueError('End capitalization-aware rendered label differs')
    for name in ('recruited','before-save','final'):scene_guard(scenes[name],states[name],True)
    if not natural(scenes['recruited']):raise ValueError('Recruitment actions not finished')
    if states['before-save']!=states['final']:raise ValueError('GUI save changed collected state')
    if [e['details'] for e in events[9:] if e['kind']=='registered-button']!=[dict(pack=p,window=w,control=c) for p,w,c in [('GUIOPT',2,6),('GUISAVE',0,26),('GUISAVE',1,7)]] or events[11]['details']!=dict(control=3):raise ValueError('Actual GUI save callback chain differs')
    if len(native.get('saves',[]))!=1:raise ValueError('Unique ordinary GUI save absent')
    return dict(save=native['saves'][0],joined=True,samples=len(samples),operations=len(events),party_xp_before=[a['base_stats'][44] for a in states['door-open']['party']],party_xp_after=[a['base_stats'][44] for a in states['final']['party']],auto_action198_sampled=any(a is not None and a['id']==198 for c in sample_scenes for a in (c['target_current'],c['target_next'])),host_dialogue_requests=0,xp_order_scope='DLG source allocates 3000 before JoinParty; intermediate allocation is not guaranteed to land on a timer sample.',original_parity=None)


def root_guard(project,source,build):
    if source==(project/'gemrb').resolve() or build==(project/'phase0-local/build').resolve():raise ValueError('Separate candidate source/build required')


def dialogue_helpers(raw):
    if binary.digest(raw)!=SNAPSHOT_SHA or raw.count(b'int main(')!=1:raise ValueError('Exact current-root dialogue snapshot required')
    return raw.replace(b'int main(',b'int FrozenUnexecutedRecruitmentDialogueMain(')


def tlk_texts(project):
    raw=(project/'phase0-local/bg2ee-clean/lang/en_US/dialog.tlk').read_bytes()
    if binary.digest(raw)!=TLK_SHA or raw[:8]!=b'TLK V1  ':raise ValueError('Pinned English TLK required')
    count,offset=binary.u32(raw,10),binary.u32(raw,14);result={}
    for ref in (1021,1022,1026,9371):
        if ref>=count:raise ValueError('TLK bounds')
        at=18+26*ref;result[ref]=binary.block(raw,offset+binary.u32(raw,at+18),binary.u32(raw,at+22)).decode('utf-8')
        if not result[ref] or '<'in result[ref] or '>'in result[ref]:raise ValueError('Unsupported empty/tokenized text')
    return result


def action_ids(receipt):
    raw=Path(receipt['resources']['action']['frozen']).read_bytes();result={}
    for name in ('UseContainer','NIDSpecial9'):
        rows=re.findall(rb'^\s*(\d+)\s+'+name.encode()+rb'\(\)\s*$',raw,re.I|re.M)
        if len(rows)!=1:raise ValueError('Actual ACTION.IDS signature missing/ambiguous')
        result[name]=int(rows[0])
    return result

def build_host(args):
    project,source,build=(getattr(args,k).resolve() for k in ('project_root','engine_source_root','engine_build_root'))
    root_guard(project,source,build)
    if not 1<=args.timeout<=300:raise ValueError('Bounded external compile timeout required')
    out=args.output_dir.resolve()
    if not out.is_relative_to(project/'phase1-local') or any(out.is_relative_to(p) for p in (source,build)):raise ValueError('Separate private external build root required')
    out.mkdir(parents=True,exist_ok=False);result=dict(schema=KIND,verdict='failed',project=str(project),source=str(source),build=str(build));api=before=candidate=None
    try:
        api=shared.phase0(project);result['preflight']=api.baseline_runner.preflight(project)
        before=api.baseline_runner.protected(project);candidate=shared.candidate_inventory(source,build)
        shared.write(out/'phase0-before.json',before);shared.write(out/'candidate-before.json',candidate)
        result['sources']={str(p):shared.frozen_copy(p,out/'sources'/evidence.sha(p)/p.name) for p in sources(project,source)}
        compiled=out/'compiled-sources';compiled.mkdir()
        for original in (project/'tools/phase0/native/gui_probe.cpp',project/'tools/phase0/native/save_probe.cpp',HERE/'native/recruitment_journey.cpp'):
            shared.frozen_copy(original,compiled/original.name)
        (compiled/'recruitment_dialogue_helpers.cpp').write_bytes(dialogue_helpers((HERE/'native/recruitment_dialogue_snapshot.cpp').read_bytes()))
        result['compiled_sources']=evidence.manifest(compiled)
        result['parent_proof']=parent_proof(project)
        result['resources']={}
        for name,row in resource_guard(api,project,source).items():
            result['resources'][name]={k:v for k,v in row.items() if k!='raw'}
            if 'raw'in row:
                target=out/'resources'/(name+'.'+row['extension']);target.parent.mkdir(exist_ok=True);target.write_bytes(row['raw']);result['resources'][name]['frozen']=str(target)
        prefix=project/'phase0-local/toolchain/msys64/ucrt64';compiler=prefix/'bin/g++.exe';host=out/'Redux_cell_recruitment_gui.exe'
        compiler_sha=evidence.sha(compiler);cmake_sha=evidence.sha(build/'CMakeCache.txt')
        cmd=[str(compiler),'-std=gnu++17','-g','-O0','-DHAVE_CONFIG_H','-DUSE_OPENGL_API','-D_USE_MATH_DEFINES','-DFMT_HEADER_ONLY','-DFMT_USE_CONSTEVAL=0','-DFMT_EXCEPTIONS=0','-DFMT_UNICODE=1','-fno-strict-aliasing']
        for p in (build,source/'gemrb/includes',source/'gemrb/core',source/'platforms/Windows',build/'gemrb/includes',prefix/'include/SDL2',prefix/'include/python3.14',source/'includes/fmt'):cmd+=['-I',str(p)]
        cmd+=[str(compiled/'recruitment_journey.cpp'),str(build/'gemrb/core/libgemrb_core.dll.a'),str(prefix/'lib/libiconv.dll.a'),'-lshlwapi','-o',str(host)]
        env=os.environ.copy();env['PATH']=str(prefix/'bin')+os.pathsep+env.get('PATH','')
        result['process']=api.baseline_runner.execute(cmd,build,env,out/'build.log',args.timeout);shared.require_process(result['process'])
        if evidence.sha(compiler)!=compiler_sha or evidence.sha(build/'CMakeCache.txt')!=cmake_sha:raise ValueError('Compiler/CMake changed during build')
        result.update(binary=str(host),binary_sha256=evidence.sha(host),compiler=str(compiler),compiler_sha256=compiler_sha,
            cmake_sha256=cmake_sha,candidate_inventory=candidate,verdict='built-not-executed')
        source_guard(result,project,source);check_resources(result,api,project,source)
    except Exception as error:result.update(error=str(error),verdict='failed')
    finally:
        try:common.finish_guards(result,out,project,source,build,api,before,candidate)
        except Exception as error:result.update(verdict='failed',preservation_error=str(error))
        shared.write(out/'build.json',result);shared.write(out/'artifact-manifest.json',dict(files=common.output_manifest(out)))
    print(out/'build.json',result['verdict']);return 0 if result['verdict']=='built-not-executed' else 1


def check_build(path,project,source,build):
    r=evidence.read(path)
    if r.get('schema')!=KIND or r.get('verdict')!='built-not-executed' or [r.get(k) for k in ('project','source','build')]!=list(map(str,(project,source,build))):raise ValueError('Wrong/failed recruitment host build')
    shared.require_process(r['process']);source_guard(r,project,source)
    if r.get('phase0_preservation')!=dict(source=True,binaries=True,fixture=True) or r.get('candidate_preserved')is not True:raise ValueError('Build preservation failed')
    if evidence.sha(r['binary'])!=r['binary_sha256'] or evidence.sha(r['compiler'])!=r['compiler_sha256'] or evidence.sha(build/'CMakeCache.txt')!=r['cmake_sha256']:raise ValueError('Driver/compiler/CMake drift')
    if shared.candidate_inventory(source,build)!=r['candidate_inventory'] or evidence.manifest(Path(path).parent/'compiled-sources')!=r['compiled_sources']:raise ValueError('Candidate/compiled source drift')
    if (Path(path).parent/'compiled-sources/recruitment_dialogue_helpers.cpp').read_bytes()!=dialogue_helpers((HERE/'native/recruitment_dialogue_snapshot.cpp').read_bytes()):raise ValueError('Frozen dialogue helper derivation differs')
    check_resources(r,shared.phase0(project),project,source)
    return r


def run(args):
    project,source,build=(getattr(args,k).resolve() for k in ('project_root','engine_source_root','engine_build_root'))
    root_guard(project,source,build)
    if not args.results_root.resolve().is_relative_to(project/'phase1-local/results'):raise ValueError('Private Phase1 results root required')
    out=shared.new_output(args.results_root.resolve(),'cell-recruitment');result=dict(schema='bg-redux-cell-recruitment-journey/1',passed=False,stages=[],original_parity=None)
    api=before=candidate=None;preserved=[];privates=[];pins={}
    try:
        api=shared.phase0(project);result['preflight']=api.baseline_runner.preflight(project)
        before=api.baseline_runner.protected(project);candidate=shared.candidate_inventory(source,build)
        shared.write(out/'phase0-before.json',before);shared.write(out/'candidate-before.json',candidate)
        receipt=check_build(args.host_build.resolve(),project,source,build);result['resources']={k:{f:v for f,v in row.items() if f!='raw'} for k,row in resource_guard(api,project,source).items()};result['parent_proof']=parent_proof(project)
        driver=out/'driver';driver.mkdir();host=driver/'Redux_cell_recruitment_gui.exe'
        shared.frozen_copy(Path(receipt['binary']),host);shared.frozen_copy(args.host_build.resolve(),driver/'build.json')
        for name,row in receipt['sources'].items():shared.frozen_copy(Path(row['frozen']),driver/'sources'/row['sha256']/Path(name).name)
        shutil.copytree(args.host_build.resolve().parent/'compiled-sources',driver/'compiled-sources')
        shutil.copytree(args.host_build.resolve().parent/'resources',driver/'resources')
        startup=driver/'startup';startup.mkdir();shared.frozen_copy(HERE/'RecruitStart.py',startup/'RecruitStart.py')
        parent_dir=driver/'parent';parent_dir.mkdir()
        for name in ('result.json','artifact-manifest.json'):shared.frozen_copy(project/'phase1-local/results'/PARENT/name,parent_dir/name)
        driver_files=evidence.manifest(driver);result['driver_files']=driver_files
        incoming=project/'phase1-local/results'/PARENT/'talk/frozen-save'
        result['initial_wire']=wire(incoming,False);initial=save_manifest(incoming,2);preserved.append((incoming,initial))
        for mode in ('recruit','reload'):
            stage=out/mode;stage.mkdir();entry=dict(journey=mode,nonce=uuid.uuid4().hex,passed=False);result['stages'].append(entry)
            input_files=save_manifest(incoming,2 if mode=='recruit' else 3);copied=stage/'profile/save/000000007-HarnessInput';shutil.copytree(incoming,copied)
            if binary.manifest(copied)!=input_files:raise ValueError('Copied measured input differs before launch')
            preserved.extend([(incoming,input_files),(copied,input_files)]);entry['input_files']=input_files
            private=shared.prepare_private_game(project,stage);privates.append((private,stage))
            for name in ('cache','capture','override'):(stage/name).mkdir()
            config=dict(GameType='bg2ee',GamePath=private['game'],GemRBPath=source/'gemrb',PluginsPath=build/'gemrb/plugins',CachePath=stage/'cache',SavePath=stage/'profile',ModPath=stage/'override',UseAsLibrary=0,SaveAsOriginal=1,Width=1024,Height=768,FullScreen=0,CapFPS=30,AudioDriver='none',GameLanguagePath='lang/en_US',SkipIntroVideos=1,Logging=1,LogColor=0,PathfinderThreadsCount=0,PathfinderMainThreadMode='immediate')
            cfg=stage/'probe.cfg';cfg.write_text(''.join('%s=%s\n'%(k,str(v).replace('\\','/')) for k,v in config.items()),encoding='utf-8');pins[str(cfg)]=evidence.sha(cfg)
            command=[str(host),'--config',str(cfg),'--output',str(stage/'capture'),'--scripts',str(startup),'--journey',mode,'--nonce',entry['nonce']]
            env=api.harness.environment(stage);prefix=project/'phase0-local/toolchain/msys64/ucrt64';env['PATH']=os.pathsep.join([str(build/'gemrb'),str(prefix/'bin'),env.get('PATH','')]);env['PYTHONDONTWRITEBYTECODE']='1'
            source_guard(receipt,project,source);check_resources(receipt,api,project,source);parent_proof(project);shared.validate_private_game(private,stage)
            if evidence.manifest(driver)!=driver_files:raise ValueError('Frozen launch closure changed')
            started=time.time_ns();entry['process']=api.baseline_runner.execute(command,build,env,stage/'process.log',180 if mode=='recruit' else 90)
            shared.require_process(entry['process'])
            if 'Traceback (most recent call last)' in (stage/'process.log').read_text(encoding='utf-8',errors='replace'):raise ValueError('Stock callback traceback')
            check_resources(receipt,api,project,source);parent_proof(project)
            entry['runtime_providers']=check_runtime_resources(stage/'capture',receipt)
            entry['observation']=validate_capture(stage/'capture',entry['nonce'],mode=='reload',started,tlk_texts(project),action_ids(receipt))
            if mode=='recruit':
                saved=Path(entry['observation']['save']).resolve()
                if not saved.is_relative_to((stage/'profile/save').resolve()) or saved==copied.resolve():raise ValueError('Output escaped profile/overwrote input')
                entry['wire']=wire(saved,True);wire_state_guard(entry['wire'],evidence.read(stage/'capture/final.state.json'));files=save_manifest(saved,3);frozen=stage/'frozen-save';shutil.copytree(saved,frozen)
                if save_manifest(frozen,3)!=files:raise ValueError('Frozen GUI save drift')
                preserved.extend([(saved,files),(frozen,files)]);incoming=frozen;entry.update(frozen_save=str(frozen),frozen_save_files=files)
            else:
                entry['wire']=wire(copied,True);wire_state_guard(entry['wire'],evidence.read(stage/'capture/loaded.state.json'));wire_state_guard(entry['wire'],evidence.read(stage/'capture/final.state.json'))
                prior=evidence.read(out/'recruit/capture/final.state.json');loaded=evidence.read(stage/'capture/loaded.state.json')
                if prior['journal']!=loaded['journal']:raise ValueError('Fresh-process reload changed journal fields')
            entry['private_game_validation']=shared.validate_private_game(private,stage);entry['passed']=True
        if len({s['process']['pid'] for s in result['stages']})!=2:raise ValueError('Fresh-process ownership absent')
        result['passed']=True
    except Exception as error:result.update(passed=False,error=str(error))
    finally:
        try:
            for folder,files in preserved:
                if binary.manifest(folder)!=files:raise ValueError('Immutable input/frozen output drift')
            for path,digest in pins.items():
                if evidence.sha(path)!=digest or evidence.manifest(Path(path).parent/'override')!={}:raise ValueError('Config/empty override changed')
            for private,stage in privates:shared.validate_private_game(private,stage)
            if 'receipt'in locals():check_build(args.host_build.resolve(),project,source,build)
            if 'driver_files'in locals() and evidence.manifest(driver)!=driver_files:raise ValueError('Frozen driver closure drift')
            if api is not None and 'receipt'in locals():check_resources(receipt,api,project,source);parent_proof(project)
            common.finish_guards(result,out,project,source,build,api,before,candidate);result['inputs_preserved']=True
        except Exception as error:result.update(passed=False,preservation_error=str(error))
        shared.write(out/'result.json',result);shared.write(out/'artifact-manifest.json',dict(files=common.output_manifest(out)))
    print(out/'result.json',result['passed']);return 0 if result['passed'] else 1


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for mode in ('build','run'):
        q=sub.add_parser(mode)
        for name in ('project-root','engine-source-root','engine-build-root'):q.add_argument('--'+name,type=Path,required=True)
        if mode=='build':
            q.add_argument('--timeout',type=int,default=240);q.add_argument('--output-dir',type=Path,required=True)
        else:
            q.add_argument('--host-build',type=Path,required=True);q.add_argument('--results-root',type=Path,required=True)
    args=p.parse_args(argv)
    if args.command=='build' and not 1<=args.timeout<=300:p.error('Timeout must be bounded to 1..300 seconds')
    return build_host(args) if args.command=='build' else run(args)


if __name__=='__main__':raise SystemExit(main())
