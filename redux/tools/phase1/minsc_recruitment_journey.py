"""External one-shot stock Minsc/Cell02 checkpoint from one measured three-party save.

Build and run are explicit coordinator operations; pure evidence readers never launch.
"""
import argparse
from collections import Counter
import os
from pathlib import Path
import re
import shutil
import subprocess
import struct
import time
import uuid
import saved_npc_color_journey as common
import saved_npc_color_fixtures as binary
import weapon_query_observer as shared
import weapon_query_validation as evidence

HERE=Path(__file__).resolve().parent
KIND='bg-redux-minsc-recruitment-host/1'
PARENT='20261022T054005Z-cell-recruitment-ac33ed70'
PARENT_RESULT='73479cf269f2aa27e3651db75dec2bc6779b2b2c051a44569f96fdc5ed2bba55'
PARENT_MANIFEST='b34e07c1b49d50bd1257d48b337569ece0b0533d510e918af03121908ac99699'
PARENT_GAM='64e5833d97499b2ffb6186640667bc1b24844ee7bb946cd28b7f1f99e24deae5'
PARENT_SAV='aee7d02f2d641456dce7eb25aef14cc0356d2c3e685de41f2196f4b225a62e2f'
SNAPSHOT_SHA='3efce63ac88475b7e0e1ad93ff6370b402d397dee5166960d179379cf2af396d'
TLK_SHA='9e685225ff3c3436a8a35fa7022550620d24a92efe35436a062c02955d9f0952'
RESOURCE_PINS={'minsca.dlg': '0bfdcdb81ccd32834cc23476cc35656ad4f0ac0cab1c7bfbc4dbc33431667ca4', 'imoenj.dlg': '68e5234e9575b355a7c0c5a16bc69b0e72b5ef2ddb5afcbbad70078ba9a83911', 'minscx.bcs': 'ea5f16b5f41efb6ceaaa9b7d54080b0b895ee3cb2d03f74bbf5fc3315f1d27f6', 'minscj.dlg': 'cb8b37958970bcf1e6157a35720a0b7c9730b63161dc2c30d9aee64b5e6dda3d', 'object.ids': 'c5b9fdea886dd39cacdc2948dd6eec3490c7c230a5ea4df2daf7b66c98f3ba44', 'minsc.bcs': 'c13fbaaf640b9ff31bcfa26f1607808e6bbf4c4186fe4bfd604db58c4548fc6b', 'action.ids': 'fb4b2c021fc4131d10863420a7bfda0e947bc86766e30edf6c4cabb38ccc2129', 'trigger.ids': '74072a62b4d27259759a81ce465226a67bc673a100c7a4aa8b0b7d89f7d44d30', 'pdialog.2da': '3106153aec08948c24484599f4bfc07b4e0b4d0814046beb24b666339005899c'}
RESOURCE_TYPES={'minsca': ('dlg', 1011), 'imoenj': ('dlg', 1011), 'minscx-script': ('bcs', 1007), 'minscj': ('dlg', 1011), 'object': ('ids', 1008), 'minsc-script': ('bcs', 1007), 'action': ('ids', 1008), 'trigger': ('ids', 1008), 'pdialog': ('2da', 1012)}
BRANCHES=[('MINSCA', 0, 2306, 0, 0, 2356), ('MINSCA', 1, 2364, 2, 6, 2395), ('MINSCA', 8, 2524, 0, 22, None), ('MINSCA', 20, 19993, 1, 40, None), ('IMOENJ', 7, 38539, 0, 9, None), ('MINSCA', 43, 38542, 0, 75, None), ('MINSCA', 32, 25066, 0, 54, 25067), ('MINSCA', 34, 25071, 1, 59, 25091), ('MINSCA', 38, 25101, 0, 66, 25102), ('MINSCA', 39, 25105, 0, 69, None), ('MINSCA', 26, 20008, 0, 46, None), ('MINSCA', 40, 25106, 0, 70, None), ('MINSCA', 41, 25107, 0, 71, None), ('MINSCA', 42, 25108, 1, 73, 25110), ('MINSCA', 22, 20001, 0, 42, None), ('MINSCA', 23, 20002, 0, 43, None), ('MINSCA', 10, 2530, 0, 25, 2548), ('MINSCA', 29, 20018, 1, 50, None), ('IMOENJ', 8, 38543, 0, 10, None), ('MINSCA', 13, 2547, 1, 31, 2557), ('MINSCA', 15, 2564, 0, 34, None)]
PREFIX_REFS={0:[2356],1:[2393,2394,2395],6:[25067],7:[25090,25091],8:[25102],13:[25109,25110],16:[2548],19:[2555,2557]}
TABLE_ITEMS=['SW1H04','SW1H07','STAF01','BLUN04','AX1H01','SPER01','HALB01','MISC4B','HAMM01','SW2H01','SW1H43']


def engine_source_inventory(source):
    names=subprocess.check_output(['git','-C',str(source),'ls-files','--cached','--others','--exclude-standard','-z'])
    return {name:evidence.sha(source/name)for name in names.decode('utf8').split('\0')if name and not name.startswith('redux/')and(source/name).is_file()}

def engine_binary_inventory(build):
    return {p.relative_to(build).as_posix():evidence.sha(p)for p in sorted((build/'gemrb').rglob('*'))if p.is_file()and(p.suffix.lower()in('.dll','.exe')or p.name=='libgemrb_core.dll.a')}

def check_engine_receipt(source,build):
    receipt=evidence.read(build/'build-receipt.json')
    if receipt.get('schema')!='bg-redux-phase1-build/1' or receipt.get('status')!='built-not-validated' or Path(receipt['source']).resolve()!=source or Path(receipt['directory']).resolve()!=build or receipt.get('source_unchanged_during_build')is not True or receipt.get('build_support_unchanged')is not True or receipt.get('phase0_preservation')!=dict(source=True,binaries=True,fixture=True):raise ValueError('Successful preserved source-bound engine build receipt required')
    if not receipt['source_files']or engine_source_inventory(source)!=receipt['source_files']:raise ValueError('Complete engine source differs from build receipt')
    if not {'gemrb/libgemrb_core.dll','gemrb/core/libgemrb_core.dll.a'}.issubset(receipt['binaries'])or engine_binary_inventory(build)!=receipt['binaries']:raise ValueError('Complete engine binary inventory differs from build receipt')
    support=[source/'redux/tools/phase1/cmake/managed-tests.cmake',source/'redux/tools/phase0/managed-test-main.cpp',*sorted((source/'redux/tools/phase0/cmake').glob('*.cmake'))]
    if set(receipt['build_support_files'])!={p.relative_to(source).as_posix()for p in support}:raise ValueError('Engine compiled support inventory differs')
    for name,digest in receipt['build_support_files'].items():
        if evidence.sha(source/name)!=digest or evidence.sha(build/'build-support'/name)!=digest:raise ValueError('Engine current/frozen compiled support differs')
    return receipt

def sources(project,source):
    local=['minsc_recruitment_journey.py','MinscStart.py','native/minsc_journey.cpp','native/minsc_dialogue_snapshot.cpp']
    engine=['unhardcoded/bg2ee/gender.2da','plugins/TLKImporter/TLKImporter.cpp','core/Region.h','core/GameScript/Triggers.cpp','core/GUI/GameControl.cpp','core/GUI/GameControl.h','core/GUI/Control.cpp','core/GUI/ScrollBar.cpp','core/GUI/TextArea.cpp','core/GUI/TextArea.h','core/GUI/View.h','core/GUI/Button.cpp','core/GUI/Button.h','core/GUI/TextSystem/TextContainer.h','core/GUI/TextSystem/TextContainer.cpp','core/DialogHandler.cpp','core/Dialog.h','core/Game.cpp','core/Inventory.cpp','core/GameScript/Actions.cpp','core/GameScript/GameScript.cpp','core/GameScript/GSUtils.cpp','core/GameScript/ParseText.cpp','core/Scriptable/Scriptable.cpp','core/Scriptable/Scriptable.h','core/Scriptable/Actor.cpp','core/Scriptable/Door.cpp','core/Scriptable/Door.h','core/Scriptable/Highlightable.cpp','core/Interface.cpp','core/InterfaceConfig.cpp','core/ResourceManager.cpp','core/Streams/SlicedStream.cpp','plugins/AREImporter/AREImporter.cpp','plugins/GAMImporter/GAMImporter.cpp','plugins/CREImporter/CREImporter.cpp','plugins/DLGImporter/DLGImporter.cpp','plugins/KEYImporter/KEYImporter.cpp','plugins/BIFImporter/BIFImporter.cpp','plugins/DirectoryImporter/DirectoryImporter.cpp','plugins/GUIScript/GUIScript.cpp','GUIScripts/Container.py','GUIScripts/GUIWORLD.py','GUIScripts/GUICommonWindows.py','GUIScripts/GUIOPT.py','GUIScripts/GUISAVE.py','GUIScripts/GUILOAD.py']
    engine += ['GUIScripts/'+name for name in ('GUIMG.py','GUIPR.py','EESpellbookHeading.py','EESpellbookInformation.py','BG2EEConfirmation.py','GUIOPT.py','GUIOPTControls.py','GUICommon.py','GUICommonWindows.py','Spellbook.py','GameCheck.py','GUIDefines.py','GUIClasses.py')]
    engine += ['unhardcoded/shared/defaults.ini']
    return sorted(set(common.sources(project)+[HERE/p for p in local]+[source/'gemrb'/p for p in engine]))


def source_guard(receipt,project,source):
    compiled=check_engine_receipt(source,Path(receipt['build']))
    required=set(map(str,sources(project,source)))|{str(Path(receipt['build'])/'build-receipt.json')}|{str(source/name)for name in compiled['build_support_files']}
    if set(receipt.get('sources',{}))!=required:raise ValueError('Recruitment source closure differs')
    for name,row in receipt['sources'].items():
        if evidence.sha(name)!=row['sha256'] or evidence.sha(row['frozen'])!=row['sha256']:raise ValueError('Recruitment source/frozen drift')


def save_manifest(folder,party):
    if party not in (3,4):raise ValueError('Only declared three/four-party saves supported')
    rows=binary.manifest(folder);names={n.casefold() for n in rows};required={'baldur.gam','baldur.sav','baldur.bmp'}|{'portrt%d.bmp'%i for i in range(party)}
    if len(names)!=len(rows) or names!=required or any(r['bytes']==0 for r in rows.values()):raise ValueError('Exact declared party save file inventory differs')
    return rows


def parent_proof(project):
    root=project/'phase1-local/results'/PARENT
    if evidence.sha(root/'result.json')!=PARENT_RESULT or evidence.sha(root/'artifact-manifest.json')!=PARENT_MANIFEST:raise ValueError('Exact measured recruitment parent differs')
    receipt=evidence.read(root/'result.json');rows=evidence.read(root/'artifact-manifest.json')['files']
    if receipt.get('schema')!='bg-redux-cell-recruitment-journey/1' or not receipt.get('passed') or not receipt.get('candidate_preserved') or not receipt.get('inputs_preserved') or receipt.get('phase0_preservation')!=dict(source=True,binaries=True,fixture=True):raise ValueError('Parent accepted preservation proof absent')
    for relative,pin in rows.items():
        file=(root/relative).resolve()
        if not file.is_relative_to(root.resolve()) or file.stat().st_size!=pin['bytes'] or evidence.sha(file)!=pin['sha256']:raise ValueError('Parent artifact drift/escape')
    stages=receipt['stages']
    if len(stages)!=2 or [s['journey']for s in stages]!=['recruit','reload'] or not all(s['passed']for s in stages):raise ValueError('Measured parent reload chain absent')
    for stage in stages:shared.require_process(stage['process'])
    if stages[0]['process']['pid']==stages[1]['process']['pid']:raise ValueError('Parent reload process is not fresh')
    incoming=root/'recruit/frozen-save';files=save_manifest(incoming,3)
    if files!=stages[0]['frozen_save_files'] or stages[1]['input_files']!=files or Path(stages[0]['frozen_save']).resolve()!=incoming.resolve():raise ValueError('Parent immutable output/reload differs')
    if evidence.sha(common.member(incoming,'gam'))!=PARENT_GAM or evidence.sha(common.member(incoming,'sav'))!=PARENT_SAV:raise ValueError('Wrong frozen parent wire')
    original=project/'phase0-local/fixtures/original-bg2ee-20261020/GemRB';p0=common.save_manifest(original)
    if p0!=receipt['parent_proof']['phase0_fixture_files']:raise ValueError('Parent Phase0 ancestor binding differs')
    wire(incoming,False)
    return dict(parent=str(root),result_sha256=PARENT_RESULT,manifest_sha256=PARENT_MANIFEST,input=str(incoming),files=files,artifact_count=len(rows),phase0_fixture_files=p0)





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
            if (source/'gemrb'/category/(resref+'.'+ext)).exists():raise ValueError('Unexpected engine resource shadow: '+name)
        raw,origin=api.probe_ui_resources.read_resource(resref,ext)
        if not raw or len(raw)>8*1024*1024 or binary.digest(raw)!=RESOURCE_PINS[resref+'.'+ext]:raise ValueError('Exact resource missing/bounds/hash: '+name)
        if name=='action':require_id(raw,'StartDialogueNoSet',198)
        if name=='trigger':
            require_id(raw,'NumTimesTalkedTo',16441);require_id(raw,'Range',16408)
        provider=(game/Path(origin.replace('\\','/'))).resolve()
        if not provider.is_relative_to(game.resolve()):raise ValueError('Resource provider escapes game')
        result[name]=dict(raw=raw,origin=origin,provider=str(provider),provider_sha256=evidence.sha(provider),sha256=binary.digest(raw),bytes=len(raw),extension=ext)
    # Exact active GemRB fallback for the one tokenized chosen response. No generic provider claim.
    for path in (game/'override/gender.2da',game/'lang/en_US/gender.2da',source/'gemrb/override/bg2ee/gender.2da',source/'gemrb/override/shared/gender.2da'):
        if path.exists():raise ValueError('Unexpected earlier gender provider')
    provider=(source/'gemrb/unhardcoded/bg2ee/gender.2da').resolve();raw=provider.read_bytes()
    if not re.search(rb'^PRO_HESHE\s+0\s+27484\s+27485\s*$',raw,re.M):raise ValueError('Exact protagonist gender mapping differs')
    if not re.search(rb'^PRO_HISHER\s+0\s+27486\s+27487\s*$',raw,re.M):raise ValueError('Exact possessive gender mapping differs')
    result['gender']=dict(raw=raw,origin=str(provider),provider=str(provider),provider_sha256=evidence.sha(provider),sha256=binary.digest(raw),bytes=len(raw),extension='2da')
    for name,path in [('chitin',game/'chitin.key'),('tlk',game/'lang/en_US/dialog.tlk')]:result[name]=dict(path=str(path),sha256=evidence.sha(path),bytes=path.stat().st_size)
    if result['tlk']['sha256']!=TLK_SHA:raise ValueError('Pinned English TLK differs')
    mapping_guard(result)
    return result




def check_resources(receipt,api,project,source):
    current=resource_guard(api,project,source)
    if set(receipt['resources'])!=set(current):raise ValueError('Build resource closure missing/extra')
    for name,row in receipt['resources'].items():
        wanted={k:v for k,v in current[name].items() if k!='raw'}
        if {k:v for k,v in row.items() if k!='frozen'}!=wanted or ('frozen'in row and evidence.sha(row['frozen'])!=row['sha256']):raise ValueError('Recruitment resource/provider drift')


def check_runtime_resources(folder,receipt):
    rows=evidence.read(folder/'minsc-providers.json')
    if rows.get('schema')!='bg-redux-minsc-providers/1' or set(rows.get('resources',{}))!=set(RESOURCE_TYPES)|{'gender'}:raise ValueError('Actual resource provider closure incomplete')
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
    if gam[:8]!=b'GAMEV2.0' or count!=(4 if joined else 3):raise ValueError('Wrong declared wire party')
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
    if [a['name']for a in people if a['group']=='party']!=['none','imoen','jaheira']+(['minsc']if joined else []):raise ValueError('Wire prior party identity/order differs')
    prior=[a for a in people if a['name']=='jaheira']
    if len(prior)!=1 or prior[0]['group']!='party' or prior[0]['dialog']!='JAHEIRAJ' or prior[0]['talk_count']!=2:raise ValueError('Wire prior Jaheira checkpoint lost')
    target=[a for a in people if a['name']=='minsc']
    if len(target)!=1 or target[0]['group']!=('party' if joined else 'npcs') or target[0]['dialog']!=('MINSCJ' if joined else 'MINSCA') or target[0]['talk_count']!=(2 if joined else 0) or (joined and target[0]['index']!=3):raise ValueError('Wire Minsc membership/identity/counter differs')
    if sum(i['resref']=='MISC84'for i in target[0]['items'])!=1 or any(i['resref']=='MISC84'for a in people if a['group']=='party'and a['name']!='minsc'for i in a['items']):raise ValueError('Wire Boo ownership differs')
    area_rows=[r for r in binary.sav_records(common.member(folder,'sav').read_bytes()) if r['name'].casefold()=='ar0602.are']
    if len(area_rows)!=1:raise ValueError('Unique saved area required')
    area=binary.inflate(area_rows[0])
    if area[:8]!=b'AREAV1.0':raise ValueError('ARE V1 required')
    base,n=binary.u32(area,0xa8),binary.u32(area,0xa4)
    if n>1000 or base<0x11c:raise ValueError('Door table bounds')
    binary.block(area,base,n*200);door_span=(base,n*200);doors=[];prior_doors=[]
    for i in range(n):
        at=base+i*200
        if text(area,at,32).casefold()=='cell01':prior_doors.append(binary.u32(area,at+40))
        if text(area,at,32).casefold()=='cell02':doors.append(dict(flags=binary.u32(area,at+40),key=text(area,at+120,8).upper(),trapped=binary.u16(area,at+112),lock_difficulty=binary.u32(area,at+140)))
    if prior_doors!=[1633]:raise ValueError('Wire prior Cell01 checkpoint lost')
    if doors!=[dict(flags=609 if joined else 610,key='',trapped=0,lock_difficulty=100)]:raise ValueError('Wire Cell02 lock/open state differs')
    base,n,items,ni=binary.u32(area,0x70),binary.u16(area,0x74),binary.u32(area,0x78),binary.u16(area,0x76)
    if n>1000 or ni>10000 or base<0x11c or items<0x11c:raise ValueError('Container table bounds')
    binary.block(area,base,n*192);binary.block(area,items,ni*20);disjoint([(0,0x11c),door_span,(base,n*192),(items,ni*20)]);tables=[]
    for i in range(n):
        at=base+i*192;first,length=binary.u32(area,at+64),binary.u32(area,at+68)
        if first>ni or length>ni-first:raise ValueError('Container slice exceeds item table')
        if text(area,at,32)=='Jailkeep Table':tables.append([item(area,items+20*j) for j in range(first,first+length)])
    if len(tables)!=1 or [x['resref'] for x in tables[0]]!=[x for x in TABLE_ITEMS if x!='MISC4B']:raise ValueError('Wire table item inventory differs')
    globals_={};base,n=binary.u32(gam,0x38),binary.u32(gam,0x3c)
    if n>100000 or base<0xb4:raise ValueError('Global table bounds')
    binary.block(gam,base,n*84);sections.append((base,n*84))
    for i in range(n):
        at=base+84*i;name=text(gam,at,32).casefold()
        if name in globals_:raise ValueError('Duplicate wire global')
        globals_[name]=binary.u32(gam,at+40)
    if globals_.get('jaheirareleased',0)!=1 or any(globals_.get(k,0) for k in ('jaheirajerk','jaheirahunt')):raise ValueError('Wire quest globals differ')
    base,n=binary.u32(gam,0x50),binary.u32(gam,0x4c)
    if n>10000 or base<0xb4:raise ValueError('Journal table bounds')
    binary.block(gam,base,n*12);sections.append((base,n*12));disjoint(sections+spans)
    journal=[dict(text_ref=binary.u32(gam,base+12*i),time=binary.u32(gam,base+12*i+4),chapter=gam[base+12*i+8],section=gam[base+12*i+10],group=gam[base+12*i+11]) for i in range(n)]
    quest_guard(journal,joined)
    if any(x['resref']=='MISC4B' for a in people if a['group']=='party' for x in a['items']):raise ValueError('Key not consumed/absent in expected wire checkpoint')
    return dict(party_count=count,target=target[0],party=[a for a in people if a['group']=='party'],door=doors[0],table=tables[0],journal=journal,globals=globals_)


def quest_guard(journal,joined):
    expected=[34089,96383,47519]+([47518]if joined else [])
    if Counter(j['text_ref']for j in journal)!=Counter(expected):raise ValueError('Missing/duplicate/unexpected retained quest')
    for ref in (47519,47518)if joined else (47519,):
        row=next(j for j in journal if j['text_ref']==ref)
        if row['chapter']!=1 or row['section']!=2:raise ValueError('Solved quest section/chapter differs')





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
    return Counter((x['resref'].upper(),x.get('expired',0),tuple(x['usages']),x['flags']) for x in items)


def scene_guard(scene,state,joined=None):
    evidence.require_state(state)
    if scene.get('schema')!='bg-redux-minsc-scene/1' or state['current_area'].upper()!='AR0602' or scene.get('game_time')!=state['game_time'] or scene.get('party_count')!=len(state['party']) or len(state['party'])not in (3,4):raise ValueError('Minsc scene/world clock/party differs')
    targets=[a for a in state['current_area_actors']if a['script_name'].casefold()=='minsc'];imoen=[a for a in state['party']if a['script_name'].casefold()=='imoen']
    if len(targets)!=1 or len(imoen)!=1 or targets[0]['runtime_id']!=scene.get('target_id') or imoen[0]['runtime_id']!=scene.get('imoen_id') or scene.get('leader_id')!=state['party'][0]['runtime_id'] or scene.get('target_name','').casefold()!='minsc':raise ValueError('Actual Minsc/Imoen/leader identity differs')
    names=[a['script_name'].casefold()for a in state['party']]
    if names!=['none','imoen','jaheira']+(['minsc']if len(names)==4 else []):raise ValueError('Prior party identity/order changed')
    target=targets[0];stored=[a for a in state['stored_npcs']if a['script_name'].casefold()=='minsc'];member=len(state['party'])==4
    if len(stored)!=int(not member) or target['in_party']!=scene.get('target_in_party') or target['in_party']!=(4 if member else 0):raise ValueError('Minsc lost/duplicate party/stored membership')
    if scene.get('door_name')!='Cell02' or scene.get('door_key')!='' or scene.get('door_flags')not in (610,608,609) or scene.get('door_open')!=bool(scene['door_flags']&1) or scene.get('door_locked')!=bool(scene['door_flags']&2) or scene.get('cell01_flags')!=1633:raise ValueError('Door progression/prior Cell01 differs')
    if scene.get('released')!=1 or {k.casefold():v for k,v in state['globals'].items()}.get('jaheirareleased')!=1:raise ValueError('Prior Jaheira release lost')
    if target['position']!=scene.get('target_position'):raise ValueError('Target position contradiction')
    if sum(i['resref'].upper()=='MISC84'for i in runtime_items(target['inventory']))!=1 or any(i['resref'].upper()=='MISC84'for a in state['party']if a['script_name'].casefold()!='minsc'for i in runtime_items(a['inventory'])):raise ValueError('Boo missing/duplicated/wrong owner')
    if len(scene.get('party_actions',[]))!=len(state['party']):raise ValueError('Missing raw actor queue diagnostics')
    for row,actor in zip(scene['party_actions'],state['party']):
        if row.get('id')!=actor['runtime_id'] or row.get('position')!=actor['position'] or type(row.get('moving'))is not bool:raise ValueError('Queue/actor position mismatch')
        for key in ('current','next'):
            if key not in row or row[key]is not None and (set(row[key])!={'id','point','int0','resref'} or type(row[key]['id'])is not int):raise ValueError('Missing/malformed action diagnostics')
    if joined is not None:
        if member!=joined or scene['target_dialog']!=('MINSCJ'if joined else'MINSCA') or scene['talk_count']!=(2 if joined else 0) or scene['door_flags']!=(609 if joined else 610):raise ValueError('Declared Minsc checkpoint absent')
        quest_guard(state['journal'],joined)
    return scene['leader_id'],scene['target_id'],scene['imoen_id'],scene['door_id']




def natural(scene):
    return not scene['in_dialog'] and scene['target_current']is None and scene['target_next']is None and not scene['target_moving'] and all(r['current']is None and r['next']is None and not r['moving'] for r in scene['party_actions']) and scene['selected_id']==scene['leader_id'] and scene['selected_count']==1 and scene['current_container']is None






def validate_capture(folder,nonce,reload,started_ns,texts,action_ids):
    native=evidence.read(folder/'minsc-result.json')
    if native.get('schema')!='bg-redux-minsc-native/1' or native.get('nonce')!=nonce or native.get('journey')!=('reload'if reload else'recruit') or native.get('completed')is not True or native.get('error') or native.get('os_pointer_input')is not False or native.get('forced_outcomes')is not False:raise ValueError('Wrong/stale/forced/incomplete Minsc native receipt')
    operation_guard(native,reload)
    if started_ns is not None and any(p.stat().st_mtime_ns<started_ns for p in folder.iterdir()if p.is_file()):raise ValueError('Stale capture file')
    samples=native['samples'];events=native['events']
    if samples!=evidence.read(folder/'minsc-samples.json') or events!=evidence.read(folder/'minsc-events.json') or not samples or len(samples)>(360 if reload else 720):raise ValueError('Missing/unbounded raw continuity')
    if any(e['nonce']!=nonce or e['sequence']!=i+1 for i,e in enumerate(events)):raise ValueError('Event nonce/sequence differs')
    states={};scenes={};ids=None
    for file in folder.glob('*.scene.json'):
        name=file.name.removesuffix('.scene.json');scene=evidence.read(file);state=evidence.read(folder/(name+'.state.json'));actual=scene_guard(scene,state)
        if ids is not None and actual!=ids:raise ValueError('Runtime identities drift within process')
        ids=actual;scenes[name]=scene;states[name]=state
    if any(s['checkpoint']not in scenes or s['game_time']!=states[s['checkpoint']]['game_time']for s in samples) or any(b['tick']<=a['tick'] or b['game_time']<a['game_time']for a,b in zip(samples,samples[1:])):raise ValueError('Sample clock/order contradiction')
    ready=[scenes[r['checkpoint']]for r in samples if r['phase']==0]
    if len(ready)<4 or any(not natural(c)for c in ready[-4:]) or scenes['ready']['bd_defai']!=1 or scenes['ready']['leader_class_script'].upper()!='BDDEFAI' or states['ready']['game_time']<states['loaded']['game_time']+30:raise ValueError('Natural startup readiness/clock not observed')
    if reload:
        for name in ('loaded','ready','final'):scene_guard(scenes[name],states[name],True)
        return dict(save=None,joined=True,samples=len(samples),operations=len(events),host_dialogue_requests=0,original_parity=None)
    scene_guard(scenes['loaded'],states['loaded'],False);scene_guard(scenes['ready'],states['ready'],False)
    movement_guard(states,scenes,samples,events,action_ids['MoveToPoint'])
    previous=evidence.read(folder/'baseline.message.json')['observed_text'];branches=[e['details']for e in events if e['kind']=='registered-branch'];expected=0
    for event in branches:
        index=event['index']
        if index!=expected:raise ValueError('Unexpected/missing/duplicate dialogue state progression')
        row=evidence.read(folder/('branch-%d.text.json'%index));state=states['branch-%d'%index];scene=scenes['branch-%d'%index]
        branch_guard(row,event,scene,state,index,texts,previous)
        previous=row['message_text'];expected=6 if index==3 and not row['imoen_eligible']else 19 if index==17 and not row['imoen_eligible']else index+1
        if BRANCHES[index][5]is None:
            label=evidence.read(folder/('branch-%d.button.json'%index));ref=9371 if index in (10,20)else 9372;flags=label.get('flags')
            if type(flags)is not int or label.get('strref')!=ref or label.get('raw')!=texts[ref] or label.get('actual')!=(texts[ref].lower()if flags&0x2000 else texts[ref].upper()if flags&8 else texts[ref]):raise ValueError('Actual Continue/End capitalization-aware label differs')
    if expected!=21 or len(branches)!=native['branches']:raise ValueError('Dialogue path incomplete')
    if scenes['auto-dialogue']['talk_count']!=1 or scenes['auto-dialogue']['door_flags']!=610 or scenes['door-open']['door_flags']!=609 or scenes['restarted-dialogue']['talk_count']!=2 or scenes['restarted-dialogue']['dialogue_target']!=ids[1]:raise ValueError('Actual script-driven open/restart missing')
    for name in ('recruited','before-save','final'):scene_guard(scenes[name],states[name],True)
    if not natural(scenes['recruited']) or states['before-save']!=states['final']:raise ValueError('Queued join incomplete or save changed collected state')
    outcome_guard(states['before-move'],states['before-join'],states['final'])
    save_events=[e for e in events if e['kind']in ('registered-button','registered-save-name')]
    if save_events[0]['details']!=dict(pack='GUILOAD',window=0,control=26) or [(e['kind'],e['details'])for e in save_events[1:]]!=[('registered-button',dict(pack='GUIOPT',window=2,control=6)),('registered-button',dict(pack='GUISAVE',window=0,control=26)),('registered-save-name',dict(control=3)),('registered-button',dict(pack='GUISAVE',window=1,control=7))]:raise ValueError('GUI save callback chain differs')
    if len(native['saves'])!=1:raise ValueError('Unique ordinary save absent')
    return dict(save=native['saves'][0],joined=True,samples=len(samples),operations=len(events),visited_indices=[e['index']for e in branches],party_xp_before=[a['base_stats'][44]for a in states['before-join']['party']],party_xp_after=[a['base_stats'][44]for a in states['final']['party']],host_dialogue_requests=0,stock_restarts=1,original_parity=None,xp_order_scope='Source queues divided3000 before JoinParty; intermediate allocation need not land on a timer sample.')




def root_guard(project,source,build):
    if source==(project/'gemrb').resolve() or build==(project/'phase0-local/build').resolve():raise ValueError('Separate candidate source/build required')
    if HERE.resolve()!=source/'redux/tools/phase1' or any(Path(module.__file__).resolve().parent!=HERE for module in (common,binary,shared,evidence)):raise ValueError('Invoke exact candidate adapter/dependency closure')
    check_engine_receipt(source,build)


def dialogue_helpers(raw):
    if binary.digest(raw)!=SNAPSHOT_SHA or raw.count(b'int main(')!=1:raise ValueError('Exact current-root dialogue snapshot required')
    return raw.replace(b'int main(',b'int FrozenUnexecutedRecruitmentDialogueMain(')


def tlk_texts(project):
    raw=(project/'phase0-local/bg2ee-clean/lang/en_US/dialog.tlk').read_bytes()
    if binary.digest(raw)!=TLK_SHA or raw[:8]!=b'TLK V1  ':raise ValueError('Pinned English TLK required')
    refs={b[2]for b in BRANCHES}|{r for values in PREFIX_REFS.values()for r in values}|{9371,9372,27484,27485,27486,27487};result={}
    for ref in refs:
        if ref>=binary.u32(raw,10):raise ValueError('TLK reference bounds')
        at=18+26*ref;value=binary.block(raw,binary.u32(raw,14)+binary.u32(raw,at+18),binary.u32(raw,at+22)).decode('utf8')
        if not value:raise ValueError('Empty required text')
        stripped=value.replace('<PRO_HESHE>','').replace('<PRO_HISHER>','')
        if '<'in stripped or '>'in stripped:raise ValueError('Unbound text token')
        result[ref]=value
    return result




def action_ids(receipt):
    raw=Path(receipt['resources']['action']['frozen']).read_bytes();rows=re.findall(rb'^\s*(\d+)\s+MoveToPoint\(P:Point\*\)\s*$',raw,re.I|re.M)
    if len(rows)!=1:raise ValueError('Exact MoveToPoint IDS signature absent/ambiguous')
    return dict(MoveToPoint=int(rows[0]))



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
        engine=check_engine_receipt(source,build);closure=sources(project,source)+[build/'build-receipt.json']+[source/name for name in engine['build_support_files']]
        result['sources']={str(p):shared.frozen_copy(p,out/'sources'/evidence.sha(p)/p.name)for p in sorted(set(closure))}
        result['engine_build_binding']=dict(receipt_sha256=evidence.sha(build/'build-receipt.json'),source_files=len(engine['source_files']),binaries=len(engine['binaries']),support_files=len(engine['build_support_files']))
        compiled=out/'compiled-sources';compiled.mkdir()
        for original in (project/'tools/phase0/native/gui_probe.cpp',project/'tools/phase0/native/save_probe.cpp',HERE/'native/minsc_journey.cpp'):
            shared.frozen_copy(original,compiled/original.name)
        (compiled/'minsc_dialogue_helpers.cpp').write_bytes(dialogue_helpers((HERE/'native/minsc_dialogue_snapshot.cpp').read_bytes()))
        result['compiled_sources']=evidence.manifest(compiled)
        result['parent_proof']=parent_proof(project)
        result['resources']={}
        for name,row in resource_guard(api,project,source).items():
            result['resources'][name]={k:v for k,v in row.items() if k!='raw'}
            if 'raw'in row:
                target=out/'resources'/(name+'.'+row['extension']);target.parent.mkdir(exist_ok=True);target.write_bytes(row['raw']);result['resources'][name]['frozen']=str(target)
        prefix=project/'phase0-local/toolchain/msys64/ucrt64';compiler=prefix/'bin/g++.exe';host=out/'Redux_minsc_recruitment_gui.exe'
        compiler_sha=evidence.sha(compiler);cmake_sha=evidence.sha(build/'CMakeCache.txt')
        cmd=[str(compiler),'-std=gnu++17','-g','-O0','-DHAVE_CONFIG_H','-DUSE_OPENGL_API','-D_USE_MATH_DEFINES','-DFMT_HEADER_ONLY','-DFMT_USE_CONSTEVAL=0','-DFMT_EXCEPTIONS=0','-DFMT_UNICODE=1','-fno-strict-aliasing']
        for p in (build,source/'gemrb/includes',source/'gemrb/core',source/'platforms/Windows',build/'gemrb/includes',prefix/'include/SDL2',prefix/'include/python3.14',source/'gemrb/includes/fmt'):cmd+=['-I',str(p)]
        cmd+=[str(compiled/'minsc_journey.cpp'),str(build/'gemrb/core/libgemrb_core.dll.a'),str(prefix/'lib/libiconv.dll.a'),'-lshlwapi','-o',str(host)]
        env=os.environ.copy();env['PATH']=str(prefix/'bin')+os.pathsep+env.get('PATH','')
        result['process']=api.baseline_runner.execute(cmd,build,env,out/'build.log',args.timeout);shared.require_process(result['process'])
        if evidence.sha(compiler)!=compiler_sha or evidence.sha(build/'CMakeCache.txt')!=cmake_sha:raise ValueError('Compiler/CMake changed during build')
        result.update(binary=str(host),binary_sha256=evidence.sha(host),compiler=str(compiler),compiler_sha256=compiler_sha,
            cmake_sha256=cmake_sha,candidate_inventory=candidate,verdict='built-not-executed')
        source_guard(result,project,source);check_resources(result,api,project,source)
    except Exception as error:result.update(error=str(error),verdict='failed')
    finally:
        try:
            check_engine_receipt(source,build)
            common.finish_guards(result,out,project,source,build,api,before,candidate)
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
    if (Path(path).parent/'compiled-sources/minsc_dialogue_helpers.cpp').read_bytes()!=dialogue_helpers((HERE/'native/minsc_dialogue_snapshot.cpp').read_bytes()):raise ValueError('Frozen dialogue helper derivation differs')
    check_resources(r,shared.phase0(project),project,source)
    return r


def run(args):
    project,source,build=(getattr(args,k).resolve() for k in ('project_root','engine_source_root','engine_build_root'))
    root_guard(project,source,build)
    if not args.results_root.resolve().is_relative_to(project/'phase1-local/results'):raise ValueError('Private Phase1 results root required')
    out=shared.new_output(args.results_root.resolve(),'minsc-recruitment');result=dict(schema='bg-redux-minsc-recruitment-journey/1',passed=False,stages=[],original_parity=None)
    api=before=candidate=None;preserved=[];privates=[];pins={}
    try:
        api=shared.phase0(project);result['preflight']=api.baseline_runner.preflight(project)
        before=api.baseline_runner.protected(project);candidate=shared.candidate_inventory(source,build)
        shared.write(out/'phase0-before.json',before);shared.write(out/'candidate-before.json',candidate)
        receipt=check_build(args.host_build.resolve(),project,source,build);result['resources']={k:{f:v for f,v in row.items() if f!='raw'} for k,row in resource_guard(api,project,source).items()};result['parent_proof']=parent_proof(project)
        driver=out/'driver';driver.mkdir();host=driver/'Redux_minsc_recruitment_gui.exe'
        shared.frozen_copy(Path(receipt['binary']),host);shared.frozen_copy(args.host_build.resolve(),driver/'build.json')
        for name,row in receipt['sources'].items():shared.frozen_copy(Path(row['frozen']),driver/'sources'/row['sha256']/Path(name).name)
        shutil.copytree(args.host_build.resolve().parent/'compiled-sources',driver/'compiled-sources')
        shutil.copytree(args.host_build.resolve().parent/'resources',driver/'resources')
        startup=driver/'startup';startup.mkdir();shared.frozen_copy(HERE/'MinscStart.py',startup/'MinscStart.py')
        parent_dir=driver/'parent';parent_dir.mkdir()
        for name in ('result.json','artifact-manifest.json'):shared.frozen_copy(project/'phase1-local/results'/PARENT/name,parent_dir/name)
        driver_files=evidence.manifest(driver);result['driver_files']=driver_files
        incoming=project/'phase1-local/results'/PARENT/'recruit/frozen-save'
        result['initial_wire']=wire(incoming,False);initial=save_manifest(incoming,3);preserved.append((incoming,initial))
        for mode in ('recruit','reload'):
            stage=out/mode;stage.mkdir();entry=dict(journey=mode,nonce=uuid.uuid4().hex,passed=False);result['stages'].append(entry)
            input_files=save_manifest(incoming,3 if mode=='recruit' else 4);copied=stage/'profile/save/000000007-HarnessInput';shutil.copytree(incoming,copied)
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
                entry['wire']=wire(saved,True);wire_state_guard(entry['wire'],evidence.read(stage/'capture/final.state.json'));files=save_manifest(saved,4);frozen=stage/'frozen-save';shutil.copytree(saved,frozen)
                if save_manifest(frozen,4)!=files:raise ValueError('Frozen GUI save drift')
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
            check_engine_receipt(source,build)
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


# Additional independent evidence guards; no engine or test execution.
def operation_guard(native,reload):
    for name,want in [('movement_commands',int(not reload)),('talk_requests',0),('door_commands',0),('restart_requests',0),('auto_dialogues',0 if reload else 2)]:
        if type(native.get(name))is not int or native[name]!=want:raise ValueError('Missing/duplicate/prohibited host operation: '+name)
    events=native.get('events',[]);branches=[e for e in events if e.get('kind')=='registered-branch']
    if type(native.get('branches'))is not int or native['branches']!=len(branches) or len(branches)not in ((0,)if reload else(18,19,20,21)):raise ValueError('Branch inventory differs')
    kinds=[e['kind']for e in events]
    if reload:
        if kinds!=['registered-button']or native.get('saves')!=[]:raise ValueError('Reload issued gameplay/save commands')
    else:
        expected=['registered-button','ordinary-approach-command','stock-auto-dialogue-observed']
        for event in branches:
            if event['details']['index']==11:expected.append('stock-restarted-dialogue-observed')
            expected.append('registered-branch')
        expected+=['registered-button','registered-button','registered-save-name','registered-button']
        if kinds!=expected:raise ValueError('Unrecognized/early/duplicate operation ordering')

def expanded_text(texts,ref,state):
    female=state['party'][0]['modified_stats'][35]==2
    return texts[ref].replace('<PRO_HESHE>',texts[27485 if female else 27484]).replace('<PRO_HISHER>',texts[27487 if female else 27486])

def branch_guard(row,event,scene,state,index,texts,previous):
    dlg,source_state,ref,local,transition,response=BRANCHES[index]
    if row.get('index')!=index or row.get('dialog')!=dlg or row.get('state')!=source_state or row.get('npc_strref')!=ref or type(row.get('imoen_eligible'))is not bool:raise ValueError('Wrong source branch identity')
    eligible=row['imoen_eligible']
    if index in (3,17)and not eligible:local,transition=0,39 if index==3 else 49
    expected=dict(index=index,dialog=dlg,state=source_state,npc_strref=ref,local=local,transition=transition,imoen_eligible=eligible,entry='TextArea::SelectAvailableOption'if response is not None else'Control::PerformAction')
    if event!=expected or row.get('local')!=local or row.get('transition')!=transition:raise ValueError('Conditional/local/global/entry mapping differs')
    npc=expanded_text(texts,ref,state);message=row.get('message_text','')
    if row.get('npc_text')!=npc or row.get('previous_text')!=previous or message.count(npc)!=previous.count(npc)+1:raise ValueError('Missing fresh exact NPC sentence')
    target=scene['imoen_id']if dlg=='IMOENJ'else scene['target_id']
    if not scene['in_dialog']or scene['speaker']!=scene['leader_id']or scene['dialogue_target']!=target or scene['talk_count']!=(2 if index>=11 else 1):raise ValueError('Actual dialogue participant/restart differs')
    choices=[]
    for visible,choice in enumerate(PREFIX_REFS.get(index,[])):
        value=expanded_text(texts,choice,state);choices.append(dict(visible_index=visible,value=visible,strref=choice,text=value))
        if '%d. - %s'%(visible+1,value)not in message:raise ValueError('Actual visible response prefix absent')
    if row.get('choices')!=choices:raise ValueError('Wrong/hidden/reordered visible value prefix')

def movement_guard(states,scenes,samples,events,action_id):
    moves=[e for e in events if e['kind']=='ordinary-approach-command']
    if len(moves)!=1 or moves[0]['details'].get('action_id')!=action_id or moves[0]['details'].get('point')!=[3909,2753]or moves[0]['details'].get('actor_id')!=scenes['before-move']['leader_id']:raise ValueError('Wrong/duplicate ordinary movement command')
    before,after=states['before-move'],states['auto-dialogue'];left=before['party'][0]['position'];right=after['party'][0]['position'];target=scenes['auto-dialogue']['target_position']
    distance=sum((a-b)**2 for a,b in zip((right[0]//16,right[1]//12),(target[0]//16,target[1]//12)))
    if left==right or distance>49 or after['game_time']<=before['game_time']:raise ValueError('Actual approach/range/clock not observed')
    if not any(c['party_actions'][0]['moving']or any(a is not None and a['id']==action_id for a in (c['party_actions'][0]['current'],c['party_actions'][0]['next']))for c in [scenes['after-move-command']]+[scenes[r['checkpoint']]for r in samples if r['phase']==1]):raise ValueError('Movement/current-next action evidence missing')
    for first,last in [('loaded','ready'),('ready','before-move')]:
        if [item_counts(runtime_items(a['inventory']))for a in states[first]['party']]!=[item_counts(runtime_items(a['inventory']))for a in states[last]['party']]:raise ValueError('Inventory changed before ordinary approach')

def outcome_guard(before,prejoin,after):
    if len(before['party'])!=3 or len(prejoin['party'])!=3 or len(after['party'])!=4:raise ValueError('Missing real prejoin/join party boundary')
    for index,(left,middle,right)in enumerate(zip(before['party'],prejoin['party'],after['party'])):
        if left['script_name'].casefold()!=right['script_name'].casefold()or middle['script_name'].casefold()!=left['script_name'].casefold():raise ValueError('Prior party membership changed')
        if left['base_stats'][44]!=middle['base_stats'][44]or right['base_stats'][44]!=middle['base_stats'][44]+1000:raise ValueError('Divided XP before-join allocation differs from measured three-party expectation')
        if item_counts(runtime_items(left['inventory']))!=item_counts(runtime_items(right['inventory'])):raise ValueError('Unrelated prior inventory changed')
    original=[a for a in before['current_area_actors']if a['script_name'].casefold()=='minsc'];joined=after['party'][3]
    if len(original)!=1 or joined['script_name'].casefold()!='minsc'or joined['runtime_id']!=original[0]['runtime_id']or joined['base_stats'][44]!=original[0]['base_stats'][44]or item_counts(runtime_items(joined['inventory']))!=item_counts(runtime_items(original[0]['inventory'])):raise ValueError('Minsc identity/XP/Boo inventory did not persist through join')
    if [j for j in after['journal']if j['text_ref']!=47518]!=before['journal']:raise ValueError('Prior quest fields changed')
    quest_guard(after['journal'],True)

def parse_dialogue(raw):
    if raw[:8]!=b'DLG V1.0':raise ValueError('DLG version differs')
    count,offset,total,at=struct.unpack('<4I',binary.block(raw,8,16))
    if count>10000 or total>100000:raise ValueError('DLG counts exceed bound')
    binary.block(raw,offset,count*16);binary.block(raw,at,total*32);rows=[]
    for state in range(count):
        ref,first,n=struct.unpack('<3I',binary.block(raw,offset+state*16,12))
        if first>total or n>total-first:raise ValueError('DLG state transition bounds')
        rows.append((ref,first,[struct.unpack('<2I',binary.block(raw,at+(first+i)*32,8))for i in range(n)]))
    return rows

def mapping_guard(resources):
    parsed={name:parse_dialogue(resources[name]['raw'])for name in ('minsca','imoenj')}
    for index,(dlg,state,ref,local,transition,response)in enumerate(BRANCHES):
        if state>=len(parsed[dlg.lower()]):raise ValueError('Required source dialogue state missing')
        actual,first,choices=parsed[dlg.lower()][state]
        if actual!=ref or first+local!=transition or local>=len(choices):raise ValueError('Pinned DLG selected state/local/global mapping differs')
        if response is not None:
            prefix=choices[:local+1]
            if len(prefix)!=len(PREFIX_REFS[index])or any(flags&3!=1 or text!=expected for (flags,text),expected in zip(prefix,PREFIX_REFS[index])):raise ValueError('Hidden/conditional/changed source response prefix')
        if index in (3,17)and (first!=transition-1 or len(choices)!=2 or any(flags!=2 for flags,_ in choices)):raise ValueError('Unsupported conditional interjection mapping')
    return True


if __name__=='__main__':raise SystemExit(main())
