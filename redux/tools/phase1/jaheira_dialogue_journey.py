"""External stock Jaheira response/journal/save/fresh-process reload journey.

CLI build/run are explicit coordinator operations. Pure validators never launch.
No dialogue-state/global injection, original parity or OS pointer claim.
"""
import argparse
from collections import Counter
import os
from pathlib import Path
import shutil
import struct
import time
import uuid

import saved_npc_color_journey as common
import saved_npc_color_fixtures as binary
import weapon_query_observer as shared
import weapon_query_validation as evidence

HERE=Path(__file__).resolve().parent
KIND='bg-redux-jaheira-host/1'
DLG_SHA='b121dc6d804e52e431c15a1d2dd372b5242f518a31d925ce403c3e633882bbc9'
TLK_SHA='9e685225ff3c3436a8a35fa7022550620d24a92efe35436a062c02955d9f0952'
CRE_SHA='e85c3c724407f9f6cd65b055fd1e3922133c7df67fa691bd4b43f8639b8349fb'
AREA_SHA='11fe9bce9ecce5d75ef05f6947da9d872b58a868898ba0935307b7ea8c4914b5'
BRANCHES=[(0,899,4,4,904),(47,20128,94,0,None),(5,909,9,0,None),
 (51,20142,98,0,None),(8,912,12,0,None),(49,20132,96,0,None),
 (50,20136,97,0,None),(9,921,14,1,923),(58,20176,105,0,None),
 (59,20177,106,0,None),(14,945,45,0,None)]
RESPONSE_STATE_COUNTS={0:5,9:7}


def sources(project,source):
    # Stable existing serializer/wrapper closure; no dependency on the loot tool.
    paths=common.sources(project)+[Path(__file__).resolve(),HERE/'DialogueStart.py',HERE/'native/dialogue_journey.cpp',HERE/'native/window_render_regression.h']
    paths += [source/p for p in ('gemrb/core/DialogHandler.cpp','gemrb/core/GUI/TextArea.cpp',
        'gemrb/core/GUI/GameControl.cpp','gemrb/core/Scriptable/Scriptable.cpp','gemrb/core/GameScript/Actions.cpp','gemrb/core/GameScript/GSUtils.cpp',
        'gemrb/core/GUI/TextArea.h','gemrb/core/GUI/View.h','gemrb/core/GUI/TextSystem/TextContainer.h',
        'gemrb/core/GUI/Button.cpp','gemrb/core/GUI/Button.h',
        'gemrb/core/GUI/TextSystem/TextContainer.cpp','gemrb/core/Scriptable/Scriptable.h',
        'gemrb/GUIScripts/GUIWORLD.py','gemrb/GUIScripts/GUISAVE.py','gemrb/GUIScripts/GUILOAD.py')]
    paths += [source/'gemrb/core/DialogHandler.h',source/'gemrb/plugins/DLGImporter/DLGImporter.cpp']
    paths += [source/'gemrb/GUIScripts'/name for name in ('GUIMG.py','GUIPR.py','EESpellbookHeading.py','EESpellbookInformation.py','BG2EEConfirmation.py','GUIOPT.py','GUIOPTControls.py','GUICommon.py','GUICommonWindows.py','Spellbook.py','GameCheck.py','GUIDefines.py','GUIClasses.py')]
    paths += [source/'gemrb/unhardcoded/shared/defaults.ini']
    return sorted(set(paths))


def root_guard(project,source,build):
    if source==(project/'gemrb').resolve() or build==(project/'phase0-local/build').resolve():
        raise ValueError('Separate Phase1 candidate source/build roots required')


def source_guard(receipt,project,source):
    if set(receipt.get('sources',{}))!={str(p) for p in sources(project,source)}:raise ValueError('Dialogue helper closure differs')
    for name,pin in receipt['sources'].items():
        if evidence.sha(name)!=pin['sha256'] or evidence.sha(pin['frozen'])!=pin['sha256']:raise ValueError('Dialogue live/frozen source drift')


def wire(folder,initial=False):
    gam=common.member(folder,'gam').read_bytes()
    if binary.block(gam,0,8)!=b'GAMEV2.0' or binary.u32(gam,0x24)!=2:raise ValueError('Stock GAMEV2.0/two-party wire required')
    offset,count=binary.u32(gam,0x30),binary.u32(gam,0x34)
    if count>1000 or offset<0xb4:raise ValueError('NPC table bounds')
    binary.block(gam,offset,count*0x160);found=[]
    for i in range(count):
        at=offset+i*0x160;cre=binary.block(gam,binary.u32(gam,at+4),binary.u32(gam,at+8))
        binary.validate_cre(cre)
        if binary.block(cre,0x280,32).split(b'\0')[0].lower()!=b'jaheira':continue
        found.append(dict(name='jaheira',dialog=binary.block(cre,0x2cc,8).split(b'\0')[0].decode('ascii'),
            position=[binary.u16(gam,at+32),binary.u16(gam,at+34)],talk_count=binary.u32(gam,at+0xe0),
            cre_sha256=binary.digest(cre),record=at,cre_offset=binary.u32(gam,at+4),cre_bytes=len(cre)))
    if len(found)!=1 or found[0]['dialog']!='JAHEIRA' or found[0]['position']!=[3898,2676]:raise ValueError('Wire Jaheira target absent/duplicate/wrong identity')
    area_rows=[r for r in binary.sav_records(common.member(folder,'sav').read_bytes()) if r['name'].casefold()=='ar0602.are']
    if len(area_rows)!=1:raise ValueError('Unique saved AR0602 required')
    area=binary.inflate(area_rows[0]);doors=binary.u32(area,0xa8);n=binary.u32(area,0xa4)
    if binary.block(area,0,8)!=b'AREAV1.0' or n>1000 or doors<0x11c:raise ValueError('Door table bounds')
    binary.block(area,doors,n*200);matches=[]
    for i in range(n):
        at=doors+i*200
        if binary.block(area,at,32).split(b'\0')[0].lower()==b'cell01':matches.append(binary.u32(area,at+40))
    if matches!=[1634]:raise ValueError('Cell01 changed/absent/duplicate')
    start,n=binary.u32(gam,0x50),binary.u32(gam,0x4c)
    if n>10000 or start<0xb4:raise ValueError('Journal table bounds')
    binary.block(gam,start,n*12)
    journal=[dict(text_ref=binary.u32(gam,start+i*12),section=gam[start+i*12+10],chapter=gam[start+i*12+8]) for i in range(n)]
    expected=0 if initial else 1
    if found[0]['talk_count']!=expected:raise ValueError('Serialized talk counter differs')
    wanted=Counter([34089,96383]+([] if initial else [34105]))
    if Counter(j['text_ref'] for j in journal)!=wanted:raise ValueError('Serialized journal missing/fabricated/duplicate entry')
    if not initial and next(j for j in journal if j['text_ref']==34105)['section']!=1:raise ValueError('Quest must be Unsolved')
    if initial and (found[0]['cre_sha256']!=CRE_SHA or binary.digest(area)!=AREA_SHA or found[0]['record']!=6888):
        raise ValueError('Exact protected starting CRE/area differs')
    return dict(target=found[0],door_flags=1634,journal=journal)


def scene_guard(scene,state,talked,journaled=None):
    if journaled is None:journaled=talked
    evidence.require_state(state)
    if (scene.get('schema')!='bg-redux-dialogue-scene/1' or scene.get('target_name','').lower()!='jaheira'
        or scene.get('dialog')!='JAHEIRA' or scene.get('target_position')!=[3898,2676]
        or type(scene.get('talk_count'))is not int or scene['talk_count']!=int(talked)
        or scene.get('party_count')!=2 or scene.get('door_name')!='Cell01' or scene.get('door_flags')!=1634
        or scene.get('door_open')is not False or scene.get('has_key')is not False
        or state['current_area'].upper()!='AR0602' or len(state['party'])!=2 or state['selection']!=1):
        raise ValueError('Actual target/counter/door/party guard differs')
    targets=[a for a in state['current_area_actors'] if a['script_name'].lower()=='jaheira']
    if len(targets)!=1 or targets[0]['runtime_id']!=scene.get('target_id') or targets[0]['in_party']!=0 or targets[0]['position']!=[3898,2676]:
        raise ValueError('Actual dialogue target identity absent/duplicate')
    if scene.get('leader_id')!=state['party'][0]['runtime_id'] or scene['leader_id']==scene['target_id'] or scene.get('game_time')!=state['game_time']:
        raise ValueError('Focused/full actor/time binding differs')
    refs=Counter(j['text_ref'] for j in state['journal'])
    if refs!=Counter([34089,96383]+([34105] if journaled else [])) or state['journal_count']!=sum(refs.values()):
        raise ValueError('Actual journal missing/fabricated/duplicate entry')
    if journaled and any(next(j for j in state['journal'] if j['text_ref']==34105)[k]!=1 for k in ('section','chapter')):
        raise ValueError('Wrong quest journal section/chapter')
    if state['globals'].get('JAHEIRAJERK',0)!=0 or state['globals'].get('JAHEIRARELEASED',0)!=0:
        raise ValueError('Wrong dialogue branch quest effects')


def validate_capture(folder,nonce,reload=False,started_ns=None,texts=None,direct_selection=False,direct_mapping=None):
    folder=Path(folder);native=evidence.read(folder/'dialogue-result.json')
    if (native.get('schema')!='bg-redux-jaheira-native/1' or native.get('nonce')!=nonce or native.get('journey')!=('reload' if reload else 'talk')
        or native.get('completed')is not True or native.get('error') or native.get('os_pointer_input')is not False
        or native.get('forced_dialogue_state')is not False or native.get('render_diagnostic',False)is not False
        or native.get('window_render_diagnostic',False)is not False or native.get('talk_requests')!=(0 if reload else 1)
        or native.get('branches_completed')!=(0 if reload else 11)):
        raise ValueError('Wrong/stale/incomplete dialogue receipt')
    if (native.get('direct_selection_regression',False)is not direct_selection or
        native.get('response_selection_entry','TextArea::SelectAvailableOption')!=('TextArea::UpdateState'if direct_selection else'TextArea::SelectAvailableOption')):
        raise ValueError('Requested dialogue selection entry differs from native receipt')
    if direct_selection and not reload:
        if direct_mapping is None or evidence.sha(folder/'selection-dialogue.runtime')!=DLG_SHA:raise ValueError('Pinned runtime DLG mapping evidence required')
    if started_ns is not None and any(p.stat().st_mtime_ns<started_ns for p in folder.iterdir() if p.is_file()):raise ValueError('Stale capture evidence')
    samples=native.get('startup_samples',[])
    if len(samples)<4 or len(samples)>1000 or not all(s.get('idle')is True for s in samples[-4:]):raise ValueError('Four natural idle samples required')
    times=[];last_ids=None
    for index,sample in enumerate(samples):
        if sample.get('checkpoint')!='startup-'+str(index) or type(sample.get('game_time'))is not int:raise ValueError('Startup coverage/order differs')
        scene=evidence.read(folder/(sample['checkpoint']+'.scene.json'));state=evidence.read(folder/(sample['checkpoint']+'.state.json'))
        scene_guard(scene,state,reload)
        actions=scene.get('party_actions',[])
        if len(actions)!=2 or [a.get('runtime_id') for a in actions]!=[a['runtime_id'] for a in state['party']]:raise ValueError('Startup action observation incomplete')
        if any(type(a.get('moving'))is not bool or a.get('position')!=state['party'][i]['position'] for i,a in enumerate(actions)):
            raise ValueError('Startup action/movement observation malformed')
        actual_idle=(scene['target_action_id']is None and scene['target_next_action_id']is None and not scene['target_moving']
            and not scene['in_dialog'] and all(p['action_id']is None and p['next_action_id']is None and not p['moving'] for p in scene['party_actions']))
        if actual_idle!=sample['idle'] or scene['game_time']!=sample['game_time']:raise ValueError('Fabricated startup readiness')
        times.append(sample['game_time']);ids=(scene['leader_id'],scene['target_id'])
        if last_ids is not None and ids!=last_ids:raise ValueError('Runtime actor identity changed')
        last_ids=ids
    if times!=sorted(times) or times[-1]<=times[0]:raise ValueError('Natural stock startup did not progress')
    tps=native.get('ticks_per_second');loaded=evidence.read(folder/'loaded.state.json')
    if type(tps)is not int or not 1<=tps<=1000 or times[-1]<loaded['game_time']+2*tps:raise ValueError('Natural startup interval incomplete')
    for name in ('loaded','ready','final')+(() if reload else ('after-dialogue','before-save')):
        scene=evidence.read(folder/(name+'.scene.json'));state=evidence.read(folder/(name+'.state.json'))
        scene_guard(scene,state,reload or name in ('after-dialogue','before-save','final'))
        if (scene['leader_id'],scene['target_id'])!=last_ids:raise ValueError('Checkpoint actor identity changed')
        image=(folder/(name+'.bmp')).read_bytes()
        if image[:2]!=b'BM' or len(image)<54:raise ValueError('Missing/invalid checkpoint screenshot')
    events=native.get('events',[])
    if ([e.get('sequence') for e in events]!=list(range(1,len(events)+1))
        or any(type(e.get('sequence'))is not int or type(e.get('tick'))is not int or e.get('nonce')!=nonce for e in events)
        or [e['tick'] for e in events]!=sorted({e['tick'] for e in events})):raise ValueError('Callback sequence/nonce differs')
    response_events=[e for e in events if e['kind'] in ('registered-response','registered-continue-end')]
    if len(response_events)!=(0 if reload else len(BRANCHES)):raise ValueError('Missing dialogue callbacks')
    if not reload:
        if texts is None:raise ValueError('Pinned independent TLK text required')
        kinds=['registered-button','ordinary-talk-request']+[
            'registered-response' if b[4]is not None else 'registered-continue-end' for b in BRANCHES]+[
            'registered-button','registered-button','registered-save-name','registered-button']
        if [e['kind'] for e in events]!=kinds:raise ValueError('Missing/reordered one-request callback journey')
        talk=events[1]['details']
        if talk!=dict(route='GameControl::TryToTalk/NIDSpecial1',target_id=last_ids[1]):raise ValueError('Talk request target/route differs')
        previous_text=evidence.read(folder/'talk-request.message.json')['observed_text']
        for index,(event,expected) in enumerate(zip(response_events,BRANCHES)):
            state_id,strref,tr,local,response=expected;detail=event['details']
            visible=(4 if index==0 else 1) if response is not None else None
            wanted=dict(state=state_id,npc_strref=strref,transition=tr,local_transition=local,response_strref=response,performed=True,
                        selection_entry=('TextArea::UpdateState'if direct_selection else'TextArea::SelectAvailableOption') if response is not None else 'Control::PerformAction',visible_index=visible)
            if direct_selection and response is not None:wanted['selected_value']=local
            if (detail!=wanted or detail.get('performed')is not True
                or any(type(detail.get(k))is not int for k in ('state','npc_strref','transition','local_transition'))
                or (visible is not None and type(detail.get('visible_index'))is not int)
                or event['kind']!=('registered-response' if response is not None else 'registered-continue-end')):
                raise ValueError('Wrong actual branch/transition/response callback')
            text=evidence.read(folder/('branch-'+str(index)+'.text.json'))
            if text.get('expected_npc_strref')!=strref or text.get('expected_npc_text')!=texts[strref] or texts[strref]not in text.get('message_text',''):
                raise ValueError('Actual NPC text/strref evidence missing')
            old_count=previous_text.count(texts[strref]);new_count=text['message_text'].count(texts[strref])
            if (text.get('previous_text')!=previous_text or new_count<=old_count or text.get('npc_occurrences_before')!=old_count
                or text.get('npc_occurrences_after')!=new_count):raise ValueError('Stale transcript is not fresh branch evidence')
            previous_text=text['message_text']
            if response is not None and str(visible+1)+'. - '+texts[response]not in text['message_text']:raise ValueError('Actual numbered response text absent')
            if direct_selection and response is not None:
                mapping=evidence.read(folder/('branch-'+str(index)+'.selection.json'))
                validate_direct_mapping(mapping,direct_mapping[state_id],state_id,visible,local,tr,response,text['message_text'],texts)
            if response is None:
                button=evidence.read(folder/('branch-'+str(index)+'.button.json'));ref=9371 if index==10 else 9372;flags=button.get('flags')
                if type(flags)is not int or not 0<=flags<=0xffffffff or button.get('label_strref')!=ref or button.get('raw_label')!=texts[ref]:raise ValueError('Continue/End label source/flags differ')
                label=texts[ref].lower() if flags&0x2000 else texts[ref].upper() if flags&8 else texts[ref]
                if button.get('expected_label')!=label or button.get('actual_label')!=label:raise ValueError('Continue/End rendered label contradicts capitalization flags')
            focused=evidence.read(folder/('branch-'+str(index)+'.scene.json'))
            scene_guard(focused,evidence.read(folder/('branch-'+str(index)+'.state.json')),True,False)
            if (focused.get('in_dialog')is not True or (focused['leader_id'],focused['target_id'])!=last_ids
                or focused.get('dialogue_target_id')!=focused['target_id'] or focused.get('dialogue_speaker_id')!=focused['leader_id']):
                raise ValueError('Actual branch participants differ')
            image=(folder/('branch-'+str(index)+'.bmp')).read_bytes()
            if image[:2]!=b'BM' or len(image)<54:raise ValueError('Missing branch screenshot')
        buttons=[e['details'] for e in events if e['kind']=='registered-button']
        if buttons!=[dict(pack=p,window=w,control=c,performed=True) for p,w,c in [('GUILOAD',0,26),('GUIOPT',2,6),('GUISAVE',0,26),('GUISAVE',1,7)]]:
            raise ValueError('Missing actual load/options/save callbacks')
        names=[e for e in events if e['kind']=='registered-save-name']
        if len(names)!=1 or names[0]['details']!=dict(performed=True,control=3):raise ValueError('Save name callback absent')
        if len(native.get('saves',[]))!=1:raise ValueError('GUI save missing/ambiguous')
    elif (native.get('saves')!=[] or len(events)!=1 or events[0]['kind']!='registered-button'
        or events[0]['details']!=dict(pack='GUILOAD',window=0,control=26,performed=True)):
        raise ValueError('Reload unexpectedly mutates dialogue/save')
    baseline=evidence.read(folder/'loaded.state.json')['journal']
    baseline=[j for j in baseline if j['text_ref']!=34105]
    for name in ['ready','final']+([] if reload else ['after-dialogue','before-save']+['branch-'+str(i) for i in range(11)]):
        state=evidence.read(folder/(name+'.state.json'))
        if [j for j in state['journal'] if j['text_ref']!=34105]!=baseline:raise ValueError('Pre-existing journal entries changed')
    if not reload and evidence.read(folder/'before-save.state.json')!=evidence.read(folder/'final.state.json'):
        raise ValueError('GUI save changed collected state')
    return dict(completed=True,callbacks=len(events),startup_samples=len(samples),target_id=last_ids[1],
        save=native['saves'][0] if not reload else None,original_parity=None,os_pointer_input=False,direct_selection_regression=direct_selection,
        state_identity='Sequential displayed NPC strref transcript matching; private dialogue state index not sampled')


def dialogue_selection_mapping(raw):
    if raw[:8]!=b'DLG V1.0':raise ValueError('DLG mapping version differs')
    states,state_at,total,transition_at=struct.unpack('<4I',binary.block(raw,8,16))
    if states>10000 or total>100000:raise ValueError('DLG mapping counts exceed bound')
    binary.block(raw,state_at,states*16);binary.block(raw,transition_at,total*32);result={}
    for state,ref,global_transition,local,response in (b for b in BRANCHES if b[4]is not None):
        if state>=states:raise ValueError('Expected response state missing')
        actual,first,count=struct.unpack('<3I',binary.block(raw,state_at+16*state,12))
        if actual!=ref or count!=RESPONSE_STATE_COUNTS[state] or first>total or count>total-first or local>=count or first+local!=global_transition:raise ValueError('DLG local/global response mapping differs')
        choices=[]
        for value in range(local+1):
            flags,text_ref=struct.unpack('<2I',binary.block(raw,transition_at+32*(first+value),8))
            if text_ref==0xffffffff:raise ValueError('Hidden response in required prefix unsupported')
            choices.append(dict(visible_index=value,value=value,transition=first+value,strref=text_ref,flags=flags))
        if choices[local]['strref']!=response:raise ValueError('Chosen DLG response text differs')
        result[state]=choices
    return result


def validate_direct_mapping(receipt,choices,state,visible,value,transition,response,message,texts):
    selected=choices[visible]if type(visible)is int and 0<=visible<len(choices)else None
    if (receipt.get('schema')!='bg-redux-dialogue-direct-selection/1' or receipt.get('choices')!=choices or receipt.get('state')!=state or receipt.get('state_transition_count')!=RESPONSE_STATE_COUNTS[state]
        or receipt.get('visible_index')!=visible or receipt.get('selected_value')!=value or receipt.get('selection_entry')!='TextArea::UpdateState'
        or receipt.get('host_dispatch_calls')!=1 or selected is None or selected['value']!=value or selected['transition']!=transition or selected['strref']!=response
        or any(type(receipt.get(k))is not int for k in ('state','state_transition_count','visible_index','selected_value','host_dispatch_calls'))
        or any(any(type(row.get(k))is not int for k in ('visible_index','value','transition','strref','flags'))for row in receipt.get('choices',[]))):raise ValueError('Direct response value/visible mapping differs')
    for choice in choices:
        text=texts.get(choice['strref'])
        if not text or str(choice['visible_index']+1)+'. - '+text not in message:raise ValueError('Every direct mapped visible response must appear')


def resource_guard(api,project):
    api.probe_ui_resources.TYPES['dlg']=1011
    data,origin=api.probe_ui_resources.read_resource('jaheira','dlg')
    tlk=project/'phase0-local/bg2ee-clean/lang/en_US/dialog.tlk'
    if data is None or binary.digest(data)!=DLG_SHA or evidence.sha(tlk)!=TLK_SHA:raise ValueError('Shipped DLG/TLK input differs')
    return dict(dialog='JAHEIRA',dlg_sha256=DLG_SHA,dlg_origin=origin,tlk_sha256=TLK_SHA,direct_selection_mapping=dialogue_selection_mapping(data))


def tlk_texts(project,direct_mapping=None):
    raw=(project/'phase0-local/bg2ee-clean/lang/en_US/dialog.tlk').read_bytes()
    if binary.digest(raw)!=TLK_SHA or raw[:8]!=b'TLK V1  ':raise ValueError('Pinned TLK required')
    count,offset=binary.u32(raw,10),binary.u32(raw,14);result={}
    refs={b[1] for b in BRANCHES}|{b[4] for b in BRANCHES if b[4]is not None}|{9371,9372}
    if direct_mapping is not None:refs|={row['strref']for choices in direct_mapping.values()for row in choices}
    for ref in refs:
        if ref>=count:raise ValueError('TLK strref out of bounds')
        row=18+ref*26;start,length=binary.u32(raw,row+18),binary.u32(raw,row+22)
        text=binary.block(raw,offset+start,length).decode('utf-8')
        if not text or '<' in text or '>' in text:raise ValueError('Unsupported empty/tokenized dialogue text')
        result[ref]=text
    if len(set(result.values()))!=len(result):raise ValueError('Ambiguous pinned dialogue text')
    return result


def build_host(args):
    project,source,build=(getattr(args,k).resolve() for k in ('project_root','engine_source_root','engine_build_root'))
    root_guard(project,source,build)
    out=args.output_dir.resolve()
    if not out.is_relative_to(project/'phase1-local') or any(out.is_relative_to(p) for p in (source,build)):raise ValueError('Separate private external build root required')
    out.mkdir(parents=True,exist_ok=False);result=dict(schema=KIND,verdict='failed',project=str(project),source=str(source),build=str(build));api=before=candidate=None
    try:
        api=shared.phase0(project);result['preflight']=api.baseline_runner.preflight(project)
        before=api.baseline_runner.protected(project);candidate=shared.candidate_inventory(source,build)
        shared.write(out/'phase0-before.json',before);shared.write(out/'candidate-before.json',candidate)
        result['sources']={str(p):shared.frozen_copy(p,out/'sources'/evidence.sha(p)/p.name) for p in sources(project,source)}
        compiled=out/'compiled-sources';compiled.mkdir()
        for original in (project/'tools/phase0/native/gui_probe.cpp',project/'tools/phase0/native/save_probe.cpp',HERE/'native/dialogue_journey.cpp',HERE/'native/window_render_regression.h'):
            shared.frozen_copy(original,compiled/original.name)
        result['compiled_sources']=evidence.manifest(compiled)
        prefix=project/'phase0-local/toolchain/msys64/ucrt64';compiler=prefix/'bin/g++.exe';host=out/'Redux_jaheira_gui.exe'
        compiler_sha=evidence.sha(compiler);cmake_sha=evidence.sha(build/'CMakeCache.txt')
        cmd=[str(compiler),'-std=gnu++17','-g','-O0','-DHAVE_CONFIG_H','-DUSE_OPENGL_API','-D_USE_MATH_DEFINES','-DFMT_HEADER_ONLY','-DFMT_USE_CONSTEVAL=0','-DFMT_EXCEPTIONS=0','-DFMT_UNICODE=1','-fno-strict-aliasing']
        for p in (build,source/'gemrb/includes',source/'gemrb/core',source/'platforms/Windows',build/'gemrb/includes',prefix/'include/SDL2',prefix/'include/python3.14',source/'includes/fmt'):cmd+=['-I',str(p)]
        cmd+=[str(compiled/'dialogue_journey.cpp'),str(build/'gemrb/core/libgemrb_core.dll.a'),str(prefix/'lib/libiconv.dll.a'),'-lshlwapi','-o',str(host)]
        env=os.environ.copy();env['PATH']=str(prefix/'bin')+os.pathsep+env.get('PATH','')
        result['process']=api.baseline_runner.execute(cmd,build,env,out/'build.log',args.timeout);shared.require_process(result['process'])
        if evidence.sha(compiler)!=compiler_sha or evidence.sha(build/'CMakeCache.txt')!=cmake_sha:raise ValueError('Compiler/CMake changed during build')
        result.update(binary=str(host),binary_sha256=evidence.sha(host),compiler=str(compiler),compiler_sha256=compiler_sha,
            cmake_sha256=cmake_sha,candidate_inventory=candidate,verdict='built-not-executed')
        source_guard(result,project,source)
    except Exception as error:result.update(error=str(error),verdict='failed')
    finally:
        try:common.finish_guards(result,out,project,source,build,api,before,candidate)
        except Exception as error:result.update(verdict='failed',preservation_error=str(error))
        shared.write(out/'build.json',result);shared.write(out/'artifact-manifest.json',dict(files=common.output_manifest(out)))
    print(out/'build.json',result['verdict']);return 0 if result['verdict']=='built-not-executed' else 1


def check_build(path,project,source,build):
    r=evidence.read(path)
    if r.get('schema')!=KIND or r.get('verdict')!='built-not-executed' or [r.get(k) for k in ('project','source','build')]!=list(map(str,(project,source,build))):raise ValueError('Wrong/failed dialogue host build')
    shared.require_process(r['process']);source_guard(r,project,source)
    if r.get('phase0_preservation')!=dict(source=True,binaries=True,fixture=True) or r.get('candidate_preserved')is not True:raise ValueError('Build preservation failed')
    if evidence.sha(r['binary'])!=r['binary_sha256'] or evidence.sha(r['compiler'])!=r['compiler_sha256'] or evidence.sha(build/'CMakeCache.txt')!=r['cmake_sha256']:raise ValueError('Driver/compiler/CMake drift')
    if shared.candidate_inventory(source,build)!=r['candidate_inventory'] or evidence.manifest(Path(path).parent/'compiled-sources')!=r['compiled_sources']:raise ValueError('Candidate/compiled source drift')
    return r


def run(args):
    project,source,build=(getattr(args,k).resolve() for k in ('project_root','engine_source_root','engine_build_root'))
    root_guard(project,source,build)
    if not args.results_root.resolve().is_relative_to(project/'phase1-local/results'):raise ValueError('Private Phase1 results root required')
    direct=getattr(args,'direct_selection_regression',False)
    out=shared.new_output(args.results_root.resolve(),'jaheira-dialogue-direct'if direct else'jaheira-dialogue');result=dict(schema='bg-redux-jaheira-journey/1',passed=False,stages=[],original_parity=None,direct_selection_regression=direct)
    api=before=candidate=None;preserved=[];privates=[];pins={}
    try:
        api=shared.phase0(project);result['preflight']=api.baseline_runner.preflight(project)
        before=api.baseline_runner.protected(project);candidate=shared.candidate_inventory(source,build)
        shared.write(out/'phase0-before.json',before);shared.write(out/'candidate-before.json',candidate)
        receipt=check_build(args.host_build.resolve(),project,source,build);result['resources']=resource_guard(api,project)
        driver=out/'driver';driver.mkdir();host=driver/'Redux_jaheira_gui.exe'
        shared.frozen_copy(Path(receipt['binary']),host);shared.frozen_copy(args.host_build.resolve(),driver/'build.json')
        for name,row in receipt['sources'].items():shared.frozen_copy(Path(row['frozen']),driver/'sources'/row['sha256']/Path(name).name)
        shutil.copytree(args.host_build.resolve().parent/'compiled-sources',driver/'compiled-sources')
        startup=driver/'startup';startup.mkdir();shared.frozen_copy(HERE/'DialogueStart.py',startup/'DialogueStart.py')
        driver_files=evidence.manifest(driver);result['driver_files']=driver_files
        incoming=project/'phase0-local/fixtures/original-bg2ee-20261020/GemRB'
        result['initial_wire']=wire(incoming,True);initial=common.save_manifest(incoming);preserved.append((incoming,initial))
        for mode in ('talk','reload'):
            stage=out/mode;stage.mkdir();entry=dict(journey=mode,nonce=uuid.uuid4().hex,passed=False);result['stages'].append(entry)
            input_files=common.save_manifest(incoming);copied=stage/'profile/save/000000007-HarnessInput';shutil.copytree(incoming,copied)
            preserved.extend([(incoming,input_files),(copied,input_files)]);entry['input_files']=input_files
            private=shared.prepare_private_game(project,stage);privates.append((private,stage))
            for name in ('cache','capture','override'):(stage/name).mkdir()
            config=dict(GameType='bg2ee',GamePath=private['game'],GemRBPath=source/'gemrb',PluginsPath=build/'gemrb/plugins',CachePath=stage/'cache',SavePath=stage/'profile',ModPath=stage/'override',UseAsLibrary=0,SaveAsOriginal=1,Width=1024,Height=768,FullScreen=0,CapFPS=30,AudioDriver='none',GameLanguagePath='lang/en_US',SkipIntroVideos=1,Logging=1,LogColor=0,PathfinderThreadsCount=0,PathfinderMainThreadMode='immediate')
            cfg=stage/'probe.cfg';cfg.write_text(''.join('%s=%s\n'%(k,str(v).replace('\\','/')) for k,v in config.items()),encoding='utf-8');pins[str(cfg)]=evidence.sha(cfg)
            command=[str(host),'--config',str(cfg),'--output',str(stage/'capture'),'--scripts',str(startup),'--journey','window-render' if args.window_render_diagnostic else 'render' if args.render_diagnostic else mode,'--nonce',entry['nonce']]
            if direct:command+=['--selection-entry','direct-value']
            env=api.harness.environment(stage);prefix=project/'phase0-local/toolchain/msys64/ucrt64';env['PATH']=os.pathsep.join([str(build/'gemrb'),str(prefix/'bin'),env.get('PATH','')]);env['PYTHONDONTWRITEBYTECODE']='1'
            source_guard(receipt,project,source);shared.validate_private_game(private,stage)
            if evidence.manifest(driver)!=driver_files:raise ValueError('Frozen launch closure changed')
            if args.debugger_trace:
                debugger=prefix/'bin/gdb.exe'
                result['debugger_trace']=dict(path=str(debugger),sha256=evidence.sha(debugger),acceptance_run=False)
                command=[str(debugger),'--batch','--return-child-result','-ex','set pagination off','-ex','set confirm off','-ex','run','-ex','thread apply all bt 60','--args']+command
            started=time.time_ns();entry['process']=api.baseline_runner.execute(command,build,env,stage/'process.log',args.timeout)
            if args.debugger_trace:raise ValueError('Diagnostic debugger trace only; not an acceptance run')
            shared.require_process(entry['process'])
            if args.render_diagnostic or args.window_render_diagnostic:
                result['render_diagnostic']=dict(acceptance_run=False,stage=mode,
                    method='Synthetic alpha/opaque/scaled/clipped window fixture' if args.window_render_diagnostic else 'Delayed ordinary, MarkDirty-only, then explicitly cleared window buffer repaint')
                raise ValueError('Render diagnostic only; not a dialogue/save acceptance run')
            if 'Traceback (most recent call last)' in (stage/'process.log').read_text(encoding='utf-8',errors='replace'):raise ValueError('Stock callback traceback')
            mapping=result['resources']['direct_selection_mapping']if direct else None
            entry['observation']=validate_capture(stage/'capture',entry['nonce'],mode=='reload',started,tlk_texts(project,mapping),direct_selection=direct,direct_mapping=mapping)
            if mode=='talk':
                saved=Path(entry['observation']['save']).resolve()
                if not saved.is_relative_to((stage/'profile/save').resolve()) or saved==copied.resolve():raise ValueError('Output escaped profile/overwrote input')
                entry['wire']=wire(saved);files=common.save_manifest(saved);frozen=stage/'frozen-save';shutil.copytree(saved,frozen)
                if common.save_manifest(frozen)!=files:raise ValueError('Frozen GUI save drift')
                preserved.extend([(saved,files),(frozen,files)]);incoming=frozen;entry.update(frozen_save=str(frozen),frozen_save_files=files)
            else:
                entry['wire']=wire(copied)
                prior=evidence.read(out/'talk/capture/final.state.json');loaded=evidence.read(stage/'capture/loaded.state.json')
                if prior['journal']!=loaded['journal']:raise ValueError('Fresh-process reload changed journal fields')
            entry['private_game_validation']=shared.validate_private_game(private,stage);entry['passed']=True
        if len({s['process']['pid'] for s in result['stages']})!=2:raise ValueError('Fresh-process ownership absent')
        result['passed']=True
    except Exception as error:result.update(passed=False,error=str(error))
    finally:
        try:
            for folder,files in preserved:
                if common.save_manifest(folder)!=files:raise ValueError('Immutable input/frozen output drift')
            for path,digest in pins.items():
                if evidence.sha(path)!=digest or evidence.manifest(Path(path).parent/'override')!={}:raise ValueError('Config/empty override changed')
            for private,stage in privates:shared.validate_private_game(private,stage)
            if 'receipt'in locals():check_build(args.host_build.resolve(),project,source,build)
            if 'driver_files'in locals() and evidence.manifest(driver)!=driver_files:raise ValueError('Frozen driver closure drift')
            if 'debugger_trace' in result and evidence.sha(result['debugger_trace']['path'])!=result['debugger_trace']['sha256']:raise ValueError('Debugger binary drift')
            if api is not None:resource_guard(api,project)
            common.finish_guards(result,out,project,source,build,api,before,candidate);result['inputs_preserved']=True
        except Exception as error:result.update(passed=False,preservation_error=str(error))
        shared.write(out/'result.json',result);shared.write(out/'artifact-manifest.json',dict(files=common.output_manifest(out)))
    print(out/'result.json',result['passed']);return 0 if result['passed'] else 1


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for mode in ('build','run'):
        q=sub.add_parser(mode)
        for name in ('project-root','engine-source-root','engine-build-root'):q.add_argument('--'+name,type=Path,required=True)
        q.add_argument('--timeout',type=int,default=240)
        if mode=='build':q.add_argument('--output-dir',type=Path,required=True)
        else:
            q.add_argument('--host-build',type=Path,required=True);q.add_argument('--results-root',type=Path,required=True)
            q.add_argument('--debugger-trace',action='store_true',help='Run only the first stage under pinned GDB, retain stacks, and always reject acceptance')
            q.add_argument('--render-diagnostic',action='store_true',help='Hold the second NPC response and compare delayed, invalidated and cleared buffer renders; always reject gameplay acceptance')
            q.add_argument('--window-render-diagnostic',action='store_true',help='Run synthetic alpha/scaled/clipped window readbacks; always reject gameplay acceptance')
            q.add_argument('--direct-selection-regression',action='store_true',help='Opt-in public TextArea::UpdateState(local value) response regression with independently guarded DLG/visible mapping')
    args=p.parse_args(argv)
    if not 1<=args.timeout<=300:p.error('Timeout must be bounded to 1..300 seconds')
    if args.command=='run'and args.direct_selection_regression and(args.debugger_trace or args.render_diagnostic or args.window_render_diagnostic):p.error('Direct selection regression cannot be combined with diagnostic-only modes')
    return build_host(args) if args.command=='build' else run(args)


if __name__=='__main__':raise SystemExit(main())
