"""Bounded external Imoen SPWI102 callback, GUI save and fresh reload journey."""
from __future__ import annotations
import argparse
from collections import Counter
import os
from pathlib import Path
import re
import shutil
import struct
import time

import saved_npc_color_journey as common
import saved_npc_color_fixtures as binary
import weapon_query_observer as shared
import weapon_query_validation as evidence

KIND='bg-redux-spell-cast-host/1'
SCOPE='Shipped portrait, Cast and resref-bound spell callbacks; normal self-cast and GUI save; no OS pointer or original parity observed.'
SPELL='spwi102'
RESOURCE_SPECS={'ar0602':('bcs',0x3ef),'bddefai':('bcs',0x3ef),'dplayer3':('bcs',0x3ef),'spwi102':('spl',0x3ee),'action':('ids',0x3f0),'spldisp':('2da',0x3f4),'guibtact':('2da',0x3f4)}

def sources(project,source):
    tool=Path(__file__).resolve().parent
    local=['spell_cast_journey.py','gui/SpellStart.py','native/spell_gui_probe_snapshot.cpp','native/spell_save_probe_snapshot.cpp','native/spell_journey.h']
    engine=['gemrb/GUIScripts/'+x for x in ['ActionsWindow.py','Spellbook.py','PortraitWindow.py','GUICommonWindows.py','GUISAVE.py','GUIOPT.py','ie_action.py','ie_spells.py']]
    engine += ['gemrb/'+x for x in ['core/GUI/GameControl.cpp','core/GUI/Control.cpp','core/GUI/Button.cpp','core/GameScript/Actions.cpp','core/GameScript/GameScript.cpp','core/GameScript/GSUtils.cpp','core/GameScript/ParseText.cpp','core/Scriptable/Scriptable.cpp','core/Scriptable/Actor.cpp','core/Spellbook.cpp','core/Interface.cpp','core/InterfaceConfig.cpp','core/ResourceManager.cpp','plugins/DirectoryImporter/DirectoryImporter.cpp','plugins/FXOpcodes/FXOpcodes.cpp','plugins/CREImporter/CREImporter.cpp','plugins/EFFImporter/EFFImporter.cpp','plugins/GUIScript/GUIScript.cpp']]
    engine += ['gemrb/unhardcoded/shared/spldisp.2da','gemrb/unhardcoded/bg2ee/guibtact.2da']
    engine += ['gemrb/GUIScripts/'+name for name in ('GUIMG.py','GUIPR.py','EESpellbookHeading.py','EESpellbookInformation.py','BG2EEConfirmation.py','GUIOPT.py','GUIOPTControls.py','GUICommon.py','GUICommonWindows.py','Spellbook.py','GameCheck.py','GUIDefines.py','GUIClasses.py')]
    engine += ['gemrb/unhardcoded/shared/defaults.ini']
    return common.sources(project)+[tool/x for x in local]+[source/x for x in engine]


def table_provider(api,source,name):
    """Bounded stock bg2ee provider contract, not a general resource resolver.

    Interface registers GemRB overrides before game providers, then bg2ee and
    shared unhardcoded directories. Reject high-priority table shadows here;
    native GetResourceStream separately verifies the actual runtime path/bytes,
    covering profile/loose providers outside the game-only Phase0 probe.
    """
    if name not in ('spldisp','guibtact'):raise ValueError('Unsupported spell table')
    source=Path(source).resolve();root=source/'gemrb';filename=name+'.2da';checks=[]
    for path in (root/'override/bg2ee'/filename,root/'override/shared'/filename):
        checks.append(dict(path=str(path),exists=path.exists()))
        if path.exists():raise ValueError('Unexpected higher-priority GemRB table override: '+str(path))
    api.probe_ui_resources.TYPES['2da']=0x3f4
    game,origin=api.probe_ui_resources.read_resource(name,'2da')
    if game is not None:raise ValueError('Unexpected higher-priority game table provider: '+str(origin))
    chosen=None
    for label in ('bg2ee','shared'):
        path=root/'unhardcoded'/label/filename
        checks.append(dict(path=str(path),exists=path.exists()))
        if path.exists() and chosen is None:chosen=path
    if chosen is None or not chosen.is_file():raise ValueError('Required GemRB table provider absent: '+name)
    raw=chosen.read_bytes()
    if not raw.startswith(b'2DA V1.0') or len(raw)>1024*1024:raise ValueError('Invalid GemRB table: '+name)
    return raw,str(chosen),dict(kind='stock-bg2ee-unhardcoded',path=str(chosen),checked_paths=checks,game_probe_absent=True,
        runtime_proof='GetResourceStream path and byte equality required for both fresh processes')


def startup_resources(api,source):
    result={}
    for name,(ext,kind) in RESOURCE_SPECS.items():
        api.probe_ui_resources.TYPES[ext]=kind
        provider=None
        if name in ('spldisp','guibtact'):raw,origin,provider=table_provider(api,source,name)
        else:raw,origin=api.probe_ui_resources.read_resource(name,ext)
        if not raw or len(raw)>1024*1024:raise ValueError('Spell resource missing/invalid: '+name)
        if name=='spwi102' and binary.digest(raw)!='7525db308f6d76b6e31587623fe9b19cfe2a8b49f0b1fdb43b6df57906974b70':raise ValueError('Declared stock SPWI102 resource differs')
        result[name]=dict(raw=raw,origin=origin,sha256=binary.digest(raw),bytes=len(raw),provider=provider)
    return result


def check_resources(receipt,api):
    actual=startup_resources(api,Path(receipt['source']))
    if set(receipt.get('startup_resources',{}))!=set(actual):raise ValueError('Startup resource closure differs')
    for name,row in receipt['startup_resources'].items():
        expected=actual[name]
        if any(row.get(k)!=expected[k] for k in ('origin','sha256','bytes','provider')) or evidence.sha(row['frozen'])!=row['sha256']:raise ValueError('Startup resource/provider/frozen drift: '+name)


def check_runtime_tables(folder,receipt):
    rows=evidence.read(folder/'spell-table-providers.json')
    if rows.get('schema')!='bg-redux-spell-table-providers/1' or set(rows.get('tables',{}))!={'spldisp','guibtact'}:raise ValueError('Actual runtime table provider evidence incomplete')
    for name,row in rows['tables'].items():
        expected=receipt['startup_resources'][name]
        path=folder/(name+'.runtime.2da')
        if Path(row.get('originalfile','')).resolve()!=Path(expected['provider']['path']).resolve() or row.get('bytes')!=expected['bytes'] or evidence.sha(path)!=expected['sha256']:raise ValueError('Actual runtime table path/bytes differs: '+name)
    return rows

def instrument(raw):
    changes=[(b'actor!=core->GetGame()->GetPC(0,false) &&',b'actor!=core->GetGame()->GetPC(0,false) && actor!=core->GetGame()->GetPC(1,false) &&'),(b'#include "save_probe.cpp"',b'#include "spell_save_probe_snapshot.cpp"'),
      (b'static Window* WindowIn',b'#include "spell_journey.h"\n\nstatic Window* WindowIn'),
      (b'    const int runningSamples=',b'    if (args["--mode"]!="live-clock" || (args["--journey"]!="cast" && args["--journey"]!="reload")) return 64;\n    const int runningSamples='),
      (b'                    const int endRunning=4+runningSamples;',b'                    const int endRunning=4+runningSamples;\n                    SpellTick(out,index,endRunning);'),
      (b'                        Write(out+"/clock-after.state.json",Snapshot(core->GetGame()));',b'                        Write(out+"/clock-after.state.json",Snapshot(core->GetGame()));\n                        SpellFinish(out);'),
      (b'                        clockStart=GetMilliseconds();sampleClock(0,"paused-initial");',b'                        SpellStart(out,args["--journey"]=="reload");\n                        clockStart=GetMilliseconds();sampleClock(0,"paused-initial");')]
    for old,new in changes:
        if raw.count(old)!=1:raise ValueError('Frozen spell host anchor absent/ambiguous')
        raw=raw.replace(old,new)
    return raw

def check_sources(receipt,project,source):
    if set(receipt['sources'])!={str(p) for p in sources(project,source)}:raise ValueError('Spell source closure differs')
    for name,row in receipt['sources'].items():
        if evidence.sha(name)!=row['sha256'] or evidence.sha(row['frozen'])!=row['sha256']:raise ValueError('Spell source/frozen drift: '+name)

def build_host(args):
    project,source,build=args.project_root.resolve(),args.engine_source_root.resolve(),args.engine_build_root.resolve()
    out=args.output_dir.resolve()
    if not out.is_relative_to(project/'phase1-local') or out.is_relative_to(source) or out.is_relative_to(build):raise ValueError('External spell build must use a separate private Phase1 folder')
    if not 1<=args.timeout<=300:raise ValueError('External spell compile timeout must be bounded')
    out.mkdir(parents=True,exist_ok=False)
    result=dict(schema=KIND,verdict='failed',project=str(project),source=str(source),build=str(build));before=candidate=None;api=None
    try:
        api=shared.phase0(project);result['phase0_preflight']=api.baseline_runner.preflight(project)
        before=api.baseline_runner.protected(project);shared.write(out/'phase0-before.json',before)
        candidate=shared.candidate_inventory(source,build);shared.write(out/'candidate-before.json',candidate)
        tool=Path(__file__).resolve().parent
        for copy,origin in [('spell_gui_probe_snapshot.cpp','gui_probe.cpp'),('spell_save_probe_snapshot.cpp','save_probe.cpp')]:
            if evidence.sha(tool/'native'/copy)!=evidence.sha(project/'tools/phase0/native'/origin):raise ValueError('Spell frozen host/serializer differs from Phase0')
        result['sources']={str(p):shared.frozen_copy(p,out/'sources'/evidence.sha(p)/p.name) for p in sources(project,source)}
        result['startup_resources']={}
        resource_out=out/'startup-resources';resource_out.mkdir()
        for name,row in startup_resources(api,source).items():
            target=resource_out/(name+'.'+RESOURCE_SPECS[name][0]);target.write_bytes(row['raw'])
            result['startup_resources'][name]={k:v for k,v in row.items() if k!='raw'}|dict(frozen=str(target))
        compiled=out/'compiled-sources';compiled.mkdir();generated=compiled/'spell_gui_probe.cpp'
        generated.write_bytes(instrument((tool/'native/spell_gui_probe_snapshot.cpp').read_bytes()))
        for name in ('spell_save_probe_snapshot.cpp','spell_journey.h'):shared.frozen_copy(tool/'native'/name,compiled/name)
        result['compiled_sources']=evidence.manifest(compiled)
        prefix=project/'phase0-local/toolchain/msys64/ucrt64';compiler=prefix/'bin/g++.exe';host=out/'Redux_spell_gui.exe'
        command=[str(compiler),'-std=gnu++17','-g','-O0','-DHAVE_CONFIG_H','-DUSE_OPENGL_API','-D_USE_MATH_DEFINES','-DFMT_HEADER_ONLY','-DFMT_USE_CONSTEVAL=0','-DFMT_EXCEPTIONS=0','-DFMT_UNICODE=1','-fno-strict-aliasing']
        for path in [build,source/'gemrb/includes',source/'gemrb/core',source/'platforms/Windows',build/'gemrb/includes',prefix/'include/SDL2',prefix/'include/python3.14',source/'includes/fmt']:command+=['-I',str(path)]
        command += [str(generated),str(build/'gemrb/core/libgemrb_core.dll.a'),str(prefix/'lib/libiconv.dll.a'),'-lshlwapi','-o',str(host)]
        env=os.environ.copy();env['PATH']=str(prefix/'bin')+os.pathsep+env.get('PATH','')
        result['process']=api.baseline_runner.execute(command,build,env,out/'build.log',args.timeout);shared.require_process(result['process'])
        result.update(binary=str(host),binary_sha256=evidence.sha(host),compiler=str(compiler),compiler_sha256=evidence.sha(compiler),candidate_inventory=candidate,command=command,verdict='built-not-executed')
        check_sources(result,project,source)
        check_resources(result,api)
    except Exception as error:result['error']=str(error);result['verdict']='failed'
    finally:
        try:
            if result.get('startup_resources'):check_resources(result,api)
            common.finish_guards(result,out,project,source,build,api,before,candidate)
        except Exception as error:result.update(verdict='failed',preservation_error=str(error))
        shared.write(out/'build.json',result);shared.write(out/'artifact-manifest.json',dict(files=common.output_manifest(out)))
    print(out/'build.json',result['verdict'],flush=True)
    return 0 if result['verdict']=='built-not-executed' else 1

def check_build(path,project,source,build):
    receipt=evidence.read(path)
    if receipt.get('schema')!=KIND or receipt.get('verdict')!='built-not-executed' or [Path(receipt[k]).resolve() for k in ('project','source','build')]!=[project,source,build]:raise ValueError('Wrong/failed spell host build')
    if receipt.get('phase0_preservation')!=dict(source=True,binaries=True,fixture=True) or receipt.get('candidate_preserved')is not True:raise ValueError('Spell build preservation failed')
    shared.require_process(receipt['process']);check_sources(receipt,project,source)
    if evidence.sha(receipt['binary'])!=receipt['binary_sha256'] or evidence.sha(receipt['compiler'])!=receipt['compiler_sha256']:raise ValueError('Spell host/compiler drift')
    if shared.candidate_inventory(source,build)!=receipt['candidate_inventory']:raise ValueError('Spell build candidate mismatch')
    compiled=Path(path).parent/'compiled-sources'
    if evidence.manifest(compiled)!=receipt['compiled_sources'] or (compiled/'spell_gui_probe.cpp').read_bytes()!=instrument((Path(__file__).parent/'native/spell_gui_probe_snapshot.cpp').read_bytes()):raise ValueError('Spell compiled source drift')
    check_resources(receipt,shared.phase0(project))
    return receipt

def imoen(state):
    evidence.require_state(state)
    if state['current_area'].upper()!='AR0602' or len(state['party'])!=2:raise ValueError('Declared party/area differs')
    actor=state['party'][1]
    if actor['script_name'].casefold()!='imoen' or actor['name']!='Imoen':raise ValueError('Declared Imoen identity differs')
    return actor

def book(actor):
    result=[];seen=set()
    for page in actor['spellbook']:
        key=(page['type'],page['level'])
        if key in seen:raise ValueError('Duplicate spellbook page')
        seen.add(key)
        for row in page['memorized']:
            if type(row.get('flags'))is not int or not 0<=row['flags']<=0xffffffff:raise ValueError('Invalid memorized flags')
            result.append((page['type'],page['level'],row['resref'].casefold(),row['flags']))
    return Counter(result)

def ready(actor):return sum(n for (t,l,r,f),n in book(actor).items() if (t,l,r)==(1,0,SPELL) and f!=0)

def required_effects(actor,now,self_caster=False):
    found={}
    for fx in actor['effects']:
        if fx['source_ref'].casefold()!=SPELL:continue
        params=fx['parameters'];opcode=fx['opcode']
        key='ac' if opcode==0 and params[:2]==[6,16] else 'icon' if opcode==142 and params[1]==12 else None
        if key is None:continue
        if key in found:raise ValueError('Duplicate required spell effect')
        if type(fx.get('duration'))is not int or not 0<fx['duration']-now<=2700*15 or fx['timing']&0xff!=0:raise ValueError('Required effect absent/expired/unbounded timing')
        if self_caster and fx.get('caster_id')!=actor['runtime_id']:raise ValueError('Required effect came from another actor')
        found[key]=fx
    if set(found)!={'ac','icon'}:raise ValueError('Required SPWI102 effects absent')
    return found

def conservation(before,after,consumed=False):
    a,b=imoen(before),imoen(after)
    for index,(left,right) in enumerate(zip(before['party'],after['party'])):
        if index!=1 and (book(left)!=book(right) or left['inventory']!=right['inventory']):raise ValueError('Another party member lost memorization/items during spell journey')
    if a['inventory']!=b['inventory']:raise ValueError('Spell journey changed equipment/items/charges')
    expected=book(a)
    if consumed:
        if ready(a)!=1 or ready(b)!=0 or expected[(1,0,SPELL,1)]!=1:raise ValueError('Exactly one ready SPWI102 must be consumed')
        expected[(1,0,SPELL,1)]-=1;expected[(1,0,SPELL,0)]+=1
    if +expected!=book(b):raise ValueError('Other memorized spells changed or selected spell granted/lost')
    if [(p['type'],p['level'],p['slots'],p['slots_with_bonus'],p['known']) for p in a['spellbook']]!=[(p['type'],p['level'],p['slots'],p['slots_with_bonus'],p['known']) for p in b['spellbook']]:raise ValueError('Known spells/slot capacity changed')

def eligible(context):
    a=context.get('actor',{})
    if a.get('script_name','').casefold()!='imoen' or type(a.get('runtime_id'))is not int:raise ValueError('Diagnostic Imoen identity missing')
    for key in ('current','next'):
        action=context.get(key,'missing')
        if action is not None and (not isinstance(action,dict) or set(action)!={'id','resref','target_id','target_mode'} or type(action['id'])is not int):raise ValueError('Missing/malformed actual action diagnostic')
    for k in ('selected_id','selected_count','game_time','action_state','action_ticks','last_spell_target','current_action_target'):
        if type(context.get(k))is not int:raise ValueError('Missing/malformed diagnostic '+k)
    if type(context.get('in_move'))is not bool or 'bd_defai'not in context or not isinstance(context.get('leader_class_script'),str):raise ValueError('Missing readiness diagnostic')
    return context['bd_defai']==1 and context['leader_class_script'].casefold()=='bddefai' and context['current']is None and context['next']is None and not context['in_move'] and context['selected_count']==1 and context['selected_id']==a['runtime_id']

def validate_diagnostics(data,running,reload,native,action_id):
    rows=data.get('samples',[])
    if data.get('schema')!='bg-redux-spell-diagnostics/1' or len(rows)!=running+9:raise ValueError('Incomplete spell diagnostics')
    streak=presses=0;command=-1;opened=-1;queued=False;casting=False;actor_id=None
    for index,row in enumerate(rows):
        if type(row.get('sample'))is not int or row['sample']!=index or row.get('running')is not (4<index<=running+4):raise ValueError('Diagnostic coverage/phase differs')
        before,after=row['before'],row['after'];ok=eligible(before);eligible(after)
        if actor_id is None:actor_id=before['actor']['runtime_id']
        if before['actor']['runtime_id']!=actor_id or after['actor']['runtime_id']!=actor_id:raise ValueError('Actor identity changed within process')
        if row.get('eligible')is not ok:raise ValueError('Readiness contradicts raw state')
        if not reload and opened<0:streak=streak+1 if row['running'] and ok else 0
        opening=not reload and opened<0 and streak==4
        issued=not reload and not presses and opened>=0 and index==opened+1 and row['running'] and ok
        if row.get('opened')is not opening:raise ValueError('Missing/duplicate stock Cast callback')
        if opening:opened=index
        if row.get('issued')is not issued or type(row.get('streak'))is not int or row['streak']!=streak:raise ValueError('Early/duplicate callback or false readiness')
        if issued:
            command=index;presses+=1
            queued=any(a is not None and a['id']==action_id and a['resref'].casefold()==SPELL and a['target_mode']==-1 and a['target_id']==actor_id for a in (after['current'],after['next']))
            if not queued:raise ValueError('Actual self-target SPWI102 action not queued')
        if row.get('press_count')!=presses or type(row['press_count'])is not int:raise ValueError('Callback count continuity differs')
        if index>command>=0 and before['current'] and before['current']['id']==action_id and before['current']['resref'].casefold()==SPELL:
            if before['last_spell_target']==actor_id and before.get('casting_resref','').casefold()==SPELL:casting=True
    if native.get('open_sample')!=opened:raise ValueError('Cast callback boundary missing')
    if native.get('press_count')!=presses or native.get('command_sample')!=command or presses!=(0 if reload else 1):raise ValueError('Missing/excessive spell callback')
    release=native.get('release_sample')
    if reload:
        if release!=-1:raise ValueError('Reload must not cast')
    else:
        if not queued or not casting or type(release)is not int or not command<release<=running+4:raise ValueError('Actual casting/release not observed')
        ctx=rows[release]['after']
        if ctx['current']is not None or ctx['next']is not None or ready(ctx['actor'])!=0:raise ValueError('Release queue/consumption differs')
        required_effects(ctx['actor'],ctx['game_time'],True)
    return dict(command_sample=command,release_sample=release,casting_self_target_observed=casting,callback_count=presses)

def validate_capture(folder,running,reload,action_id,started_ns=None):
    names=['clock-before.state.json','clock-after.state.json','clock-samples.json','gui-result.json','spell-before.state.json','spell-portrait-before.state.json','spell-before-save.state.json','spell-after-save.state.json','spell-result.json','spell-diagnostics.json','spell-table-providers.json']
    if not reload:names+=['spell-cast-before.state.json','spell-cast-button.json','spell-command-before.state.json','spell-command-after.state.json','spell-released.state.json','spell-button.json']
    shots=['spell-before-portrait','spell-before','spell-before-save','spell-save-confirm','spell-after-save']
    if not reload:shots+=['spell-cast-before','spell-command-before','spell-icons','spell-command-after','spell-released']
    for name in names+[s+'.bmp' for s in shots]+['spldisp.runtime.2da','guibtact.runtime.2da']:
        path=folder/name
        if not path.is_file() or (started_ns is not None and path.stat().st_mtime_ns<started_ns):raise ValueError('Missing/stale spell evidence: '+name)
    for shot in shots:
        raw=(folder/(shot+'.bmp')).read_bytes()
        if len(raw)<100 or raw[:2]!=b'BM':raise ValueError('Invalid screenshot evidence')
    data={name:evidence.read(folder/name) for name in names}
    for name,state in data.items():
        if name.endswith('.state.json'):imoen(state)
    native=data['spell-result.json']
    expected=dict(schema='bg-redux-spell-native/1',reload=reload,portrait_callback='GUICommonWindows.PortraitButtonOnPress',cast_callback='none' if reload else 'ActionsWindow.ActionCastPressed',spell_callback='none' if reload else 'ActionsWindow.SpellPressed',gui_save_callback='GUISAVE.ConfirmedSaveGame',save_return_code_observed=False,forced=False,os_pointer_input=False,action_id=action_id)
    if any(native.get(k)!=v or type(native.get(k))is not type(v) for k,v in expected.items()) or len(native.get('directories',[]))!=1:raise ValueError('Stock callbacks/GUI save evidence differs')
    clock=data['clock-samples.json'];samples=clock.get('samples',[])
    if clock.get('schema')!='bg-redux-live-clock/1' or clock.get('ticks_per_second')!=15 or len(samples)!=running+9:raise ValueError('Missing live clock')
    for i,s in enumerate(samples):
        if s.get('sample')!=i or s.get('phase')!=('paused-initial' if i<=4 else 'running' if i<=running+4 else 'paused-final'):raise ValueError('Clock phases differ')
    for key in ('game_time','elapsed_ms'):
        vals=[s.get(key) for s in samples]
        if any(type(v)is not int for v in vals) or vals!=sorted(vals):raise ValueError('Clock monotonicity differs')
    if len({s['game_time'] for s in samples[:5]})!=1 or len({s['game_time'] for s in samples[-4:]})!=1 or samples[-1]['game_time']<=samples[4]['game_time']:raise ValueError('Normal running/pause evidence absent')
    gui=data['gui-result.json']
    if gui.get('completed')is not True or gui.get('steps')!=running+9 or gui.get('events')!=['ReduxStart.PopulateLoad','press:load.baseline-row','ReduxStart.Ready','clock:resume','clock:pause']:raise ValueError('Normal loop did not complete')
    first,last=data['clock-before.state.json'],data['clock-after.state.json']
    if first!=data['spell-before.state.json'] or last!=data['spell-before-save.state.json']:raise ValueError('Snapshot clock/save continuity differs')
    for state,sample in ((first,samples[0]),(last,samples[-1])):
        if state['game_time']!=sample['game_time']:raise ValueError('Clock snapshot boundary differs')
    diag=data['spell-diagnostics.json'];observed=validate_diagnostics(diag,running,reload,native,action_id)
    for i,row in enumerate(diag['samples']):
        if row['after']['game_time']!=samples[i]['game_time']:raise ValueError('Diagnostics/clock times differ')
        ctx=row['after'];matches=[t for t in samples[i].get('action_trace',[]) if t.get('runtime_id')==ctx['actor']['runtime_id']]
        if len(matches)!=1 or matches[0].get('position')!=ctx['actor']['position'] or matches[0].get('action_id')!=(ctx['current']['id'] if ctx['current'] else None) or matches[0].get('current_action_target')!=ctx['current_action_target']:raise ValueError('Clock trace contradicts actual Imoen action/target')
    for state,ctx in ((first,diag['samples'][0]['before']),(last,diag['samples'][-1]['after'])):
        if imoen(state)!=ctx['actor']:raise ValueError('Full/focused actor continuity differs')
    conservation(data['spell-portrait-before.state.json'],first)
    command=first if reload else data['spell-command-before.state.json']
    if not reload:
        conservation(first,data['spell-cast-before.state.json']);conservation(first,command)
        cb=data['spell-cast-button.json']
        if cb.get('action')!=2 or cb.get('visible')is not True or cb.get('disabled')is not False or type(cb.get('control'))is not int or not 0<=cb['control']<12:raise ValueError('Actual enabled stock Cast control missing')
        opening=diag['samples'][native['open_sample']]['before']
        if imoen(data['spell-cast-before.state.json'])!=opening['actor'] or data['spell-cast-before.state.json']['game_time']!=opening['game_time']:raise ValueError('Stock Cast opening snapshot differs')
        row=diag['samples'][observed['command_sample']]
        if imoen(command)!=row['before']['actor'] or command['game_time']!=row['before']['game_time'] or imoen(data['spell-command-after.state.json'])!=row['after']['actor']:raise ValueError('Callback boundary snapshot differs')
        button=data['spell-button.json']
        if button.get('resref','').casefold()!=SPELL or button.get('target')!=5 or button.get('type')!=1 or button.get('level')!=0 or button.get('dict_name','').casefold()!='spell' or button.get('dict_value',-1)//1000!=2 or button.get('disabled')is not False or button.get('visible')is not True or not 0<=button.get('spell_control',-1)<12:raise ValueError('Enabled resref-bound spell icon guard differs')
        pages=[p for p in imoen(command)['spellbook'] if (p['type'],p['level'])==(1,0)]
        slot=button.get('slot')
        if len(pages)!=1 or type(slot)is not int or not 0<=slot<len(pages[0]['memorized']) or pages[0]['memorized'][slot]['resref'].casefold()!=SPELL or pages[0]['memorized'][slot]['flags']!=1 or button.get('ready_count')!=1 or button.get('casting_time')!=9 or button.get('header_index')!=0:raise ValueError('Actual selected memorized slot/header differs')
        release=data['spell-released.state.json'];row=diag['samples'][observed['release_sample']]
        if imoen(release)!=row['after']['actor'] or release['game_time']!=row['after']['game_time']:raise ValueError('Release evidence differs')
        if any(fx['source_ref'].casefold()==SPELL for fx in imoen(command)['effects']):raise ValueError('Preexisting spell effect invalidates causal cast evidence')
    conservation(command,last,not reload)
    required_effects(imoen(last),last['game_time'],not reload)
    if reload:required_effects(imoen(first),first['game_time'])
    # GUI close callbacks may change selection; compare the actual gameplay actor,
    # spellbook/effects/inventory/stats and game time, retain all world differences.
    saved=data['spell-after-save.state.json']
    if imoen(saved)!=imoen(last) or saved['game_time']!=last['game_time']:raise ValueError('GUI save changed captured Imoen gameplay state')
    return dict(native=native,output_save=native['directories'][0],readiness=observed,samples=len(samples),save_state_differences=evidence.diff(last,saved),before_stats=imoen(command)['modified_stats'],after_stats=imoen(last)['modified_stats'],effect_remaining_ticks={k:v['duration']-last['game_time'] for k,v in required_effects(imoen(last),last['game_time']).items()})

def wire_spells(folder):
    gam=common.member(folder,'gam').read_bytes();_,cre=binary.party_cre(gam,1)
    if binary.block(cre,0x280,32).split(b'\0')[0].lower()!=b'imoen':raise ValueError('Wire Imoen identity differs')
    # CRE V1 known/memorization/memorized/effect tables are independently bounded.
    start,count=binary.u32(cre,0x2b0),binary.u32(cre,0x2b4)
    spells=[dict(resref=binary.block(cre,start+12*i,8).split(b'\0')[0].decode('ascii').lower(),flags=binary.u32(cre,start+12*i+8)) for i in range(count)]
    pages=[];used=set();base,n=binary.u32(cre,0x2a8),binary.u32(cre,0x2ac)
    for i in range(n):
        at=base+16*i;level,slots,bonus,kind=struct.unpack('<HHHH',binary.block(cre,at,8));first,length=struct.unpack('<II',binary.block(cre,at+8,8))
        if first>count or length>count-first or any(j in used for j in range(first,first+length)):raise ValueError('Wire spell page range overlaps/exceeds table')
        used.update(range(first,first+length));pages.append(dict(type=kind,level=level,memorized=spells[first:first+length]))
    if used!=set(range(count)):raise ValueError('Orphan wire memorized spell')
    effects=[];base,n=binary.u32(cre,0x2c4),binary.u32(cre,0x2c8)
    for i in range(n):
        raw=binary.block(cre,base+264*i,264)
        effects.append(dict(opcode=binary.u32(raw,8),parameters=[binary.u32(raw,20),binary.u32(raw,24)],timing=binary.u16(raw,28),duration=binary.u32(raw,32),source_ref=binary.block(raw,140,8).split(b'\0')[0].decode('ascii').lower()))
    return dict(spellbook=pages,effects=effects)

def check_wire(folder,state):
    actual=wire_spells(folder);actor=imoen(state)
    if book(actual)!=book(actor):raise ValueError('Wire memorization/depletion differs from actual actor')
    wanted=required_effects(actor,state['game_time']);found=required_effects(actual,state['game_time'])
    for key in wanted:
        for field in ('opcode','timing','duration'):
            if found[key][field]!=wanted[key][field]:raise ValueError('Wire persistent spell effect differs')
    return actual

def run(args):
    project,source,build=args.project_root.resolve(),args.engine_source_root.resolve(),args.engine_build_root.resolve()
    if args.running_samples!=80 or not 1<=args.timeout<=90:raise ValueError('Spell requires exactly 80 running samples and at most 90 seconds per process')
    results=args.results_root.resolve()
    if not results.is_relative_to(project/'phase1-local/results'):raise ValueError('Spell results must stay under private Phase1 results')
    out=shared.new_output(results,'spell-cast-journey')
    result=dict(schema='bg-redux-spell-cast-journey/1',directory=str(out),execution='not-run',verdict='failed',scope=SCOPE,stages=[],process_budget_seconds=2*args.timeout);before=candidate=None;api=None;preserved=[];configs=[];privates=[]
    try:
        api=shared.phase0(project);result['phase0_preflight']=api.baseline_runner.preflight(project)
        before=api.baseline_runner.protected(project);shared.write(out/'phase0-before.json',before)
        candidate=shared.candidate_inventory(source,build);shared.write(out/'candidate-before.json',candidate)
        receipt=check_build(args.host_build.resolve(),project,source,build)
        driver=out/'driver';driver.mkdir();host=driver/'Redux_spell_gui.exe';shared.frozen_copy(Path(receipt['binary']),host);shared.frozen_copy(args.host_build.resolve(),driver/'build.json')
        for name,row in receipt['sources'].items():shared.frozen_copy(Path(row['frozen']),driver/'sources'/row['sha256']/Path(name).name)
        shutil.copytree(args.host_build.resolve().parent/'compiled-sources',driver/'compiled-sources')
        result['startup_resources']={}
        for name,row in receipt['startup_resources'].items():
            frozen=driver/'startup-resources'/(name+'.'+RESOURCE_SPECS[name][0]);shared.frozen_copy(Path(row['frozen']),frozen)
            result['startup_resources'][name]={**row,'run_frozen':str(frozen)}
        startup=driver/'startup';startup.mkdir();shared.frozen_copy(Path(__file__).parent/'gui/SpellStart.py',startup/'ReduxStart.py')
        api.probe_ui_resources.TYPES['ids']=0x3f0
        raw_ids,origin=api.probe_ui_resources.read_resource('action','ids')
        if raw_ids is None:raise ValueError('Shipped ACTION.IDS unavailable')
        matches=re.findall(rb'^\s*(\d+)\s+NIDSpecial6\(\)\s*$',raw_ids,re.M|re.I)
        if len(matches)!=1:raise ValueError('Shipped NIDSpecial6 action signature absent/ambiguous')
        action_id=int(matches[0]);(driver/'ACTION.IDS').write_bytes(raw_ids)
        result['action_ids']=dict(sha256=binary.digest(raw_ids),origin=origin,self_cast_action_id=action_id)
        driver_files=evidence.manifest(driver);result['driver_files']=driver_files
        incoming=args.fixture.resolve()
        if incoming!=(project/'phase0-local/fixtures/original-bg2ee-20261020/GemRB').resolve():raise ValueError('Only the protected stock saved fixture is supported')
        initial=common.save_manifest(incoming);wire=api.legacy_oracle.read_wire(common.member(incoming,'gam'));input_spells=wire_spells(incoming)
        if len(wire['party'])!=2 or wire['party'][1]['area']!='AR0602' or ready(input_spells)!=1 or any(f['source_ref']==SPELL for f in input_spells['effects']):raise ValueError('Declared stock Imoen spell fixture guard differs')
        result['fixture']=dict(path=str(incoming),files=initial,imoen_spells=input_spells,party1=wire['party'][1]);preserved.append((incoming,initial))
        for index,name in enumerate(('cast','reload')):
            stage=out/name;stage.mkdir();entry=dict(id=name,execution='not-run');result['stages'].append(entry);private=None
            try:
                input_files=common.save_manifest(incoming);entry['input_files']=input_files
                copied=stage/'profile/save/000000007-HarnessInput';shutil.copytree(incoming,copied)
                if common.save_manifest(copied)!=input_files:raise ValueError('Spell copied input drift')
                preserved.append((copied,input_files))
                private=shared.prepare_private_game(project,stage)
                privates.append((private,stage))
                for folder in ('capture','cache','override'):(stage/folder).mkdir()
                config=dict(GameType='bg2ee',GamePath=private['game'],GemRBPath=source/'gemrb',PluginsPath=build/'gemrb/plugins',CachePath=stage/'cache',SavePath=stage/'profile',ModPath=stage/'override',UseAsLibrary=0,SaveAsOriginal=1,Width=1024,Height=768,FullScreen=0,CapFPS=30,AudioDriver='none',GameLanguagePath='lang/en_US',SkipIntroVideos=1,Logging=1,LogColor=0,PathfinderThreadsCount=0,PathfinderMainThreadMode='immediate')
                cfg=stage/'probe.cfg';cfg.write_text(''.join(f'{k}={str(v).replace(chr(92),chr(47))}\n' for k,v in config.items()),encoding='utf-8');entry['config_sha256']=evidence.sha(cfg)
                configs.append((cfg,entry['config_sha256']))
                command=[str(host),'--config',str(cfg),'--output',str(stage/'capture'),'--scripts',str(startup),'--mode','live-clock','--clock-running-samples',str(args.running_samples),'--trace-actions','1','--journey',name]
                env=api.harness.environment(stage);prefix=project/'phase0-local/toolchain/msys64/ucrt64';env['PATH']=os.pathsep.join([str(build/'gemrb'),str(prefix/'bin'),env.get('PATH','')]);env['PYTHONDONTWRITEBYTECODE']='1'
                check_sources(receipt,project,source);check_resources(receipt,api);shared.validate_private_game(private,stage)
                if evidence.manifest(driver)!=driver_files:raise ValueError('Frozen spell driver/source closure drift')
                started=time.time_ns();entry['process']=api.baseline_runner.execute(command,build,env,stage/'process.log',args.timeout)
                check_resources(receipt,api)
                if (stage/'capture/spell-result.json').is_file():entry['native_receipt']=evidence.read(stage/'capture/spell-result.json')
                shared.require_process(entry['process'])
                if 'Traceback (most recent call last)' in (stage/'process.log').read_text(encoding='utf-8',errors='replace'):raise ValueError('Stock callback traceback')
                entry['runtime_table_providers']=check_runtime_tables(stage/'capture',receipt)
                observed=validate_capture(stage/'capture',args.running_samples,bool(index),action_id,started);entry['observation']=observed
                loaded=evidence.read(stage/'capture/spell-before.state.json')
                entry['loaded_wire_guard']=check_wire(incoming,loaded) if index else dict(memorized=wire_spells(incoming)['spellbook'])
                if book(wire_spells(incoming))!=book(imoen(loaded)):raise ValueError('Loaded spellbook differs from immutable wire input')
                saved=Path(observed['output_save']).resolve()
                if not saved.is_relative_to((stage/'profile/save').resolve()) or saved==copied.resolve():raise ValueError('Spell output escaped private profile or overwrote input')
                output_files=common.save_manifest(saved);frozen=stage/'frozen-save';shutil.copytree(saved,frozen)
                if common.save_manifest(frozen)!=output_files:raise ValueError('Frozen spell save differs')
                focused=evidence.read(stage/'capture/spell-before-save.state.json')
                entry['wire']=check_wire(frozen,focused)
                if index:
                    prior=evidence.read(out/'cast/capture/spell-before-save.state.json');loaded=evidence.read(stage/'capture/spell-before.state.json')
                    conservation(prior,loaded)
                    for key,fx in required_effects(imoen(prior),prior['game_time']).items():
                        new=required_effects(imoen(loaded),loaded['game_time'])[key]
                        if new['duration']!=fx['duration']:raise ValueError('Fresh process changed persistent effect expiration')
                if common.save_manifest(copied)!=input_files or common.save_manifest(incoming)!=input_files or evidence.sha(cfg)!=entry['config_sha256']:raise ValueError('Immutable spell input/config changed')
                if evidence.manifest(stage/'override')!={}:raise ValueError('Unexpected private spell override appeared')
                entry.update(execution='passed',frozen_save=str(frozen),frozen_save_files=output_files);preserved.extend([(saved,output_files),(frozen,output_files),(copied,input_files)]);incoming=frozen
            except Exception as error:entry.update(execution='failed' if 'process'in entry else 'not-run',error=str(error));raise
            finally:
                if private is not None:entry['private_game_validation']=shared.validate_private_game(private,stage)
        result.update(execution='passed',verdict='stock-spell-callback-cast-persisted')
    except Exception as error:
        result['error']=str(error)
        if any('process'in stage for stage in result['stages']):result['execution']='failed'
    finally:
        try:
            for folder,files in preserved:
                if common.save_manifest(folder)!=files:raise ValueError('Frozen/input spell save changed: '+str(folder))
            for cfg,digest in configs:
                if evidence.sha(cfg)!=digest or evidence.manifest(cfg.parent/'override')!={}:raise ValueError('Private spell config/override drift')
            result['private_game_final_validations']=[shared.validate_private_game(private,stage) for private,stage in privates]
            result['inputs_and_outputs_preserved']=True
            if 'receipt'in locals():check_sources(receipt,project,source)
            if 'receipt'in locals():check_resources(receipt,api)
            if 'driver_files'in locals() and evidence.manifest(driver)!=driver_files:raise ValueError('Frozen spell driver/source closure changed')
            common.finish_guards(result,out,project,source,build,api,before,candidate)
        except Exception as error:result.update(execution='failed',verdict='failed',preservation_error=str(error))
        shared.write(out/'result.json',result);shared.write(out/'artifact-manifest.json',dict(files=common.output_manifest(out)))
    print(out/'result.json',result['verdict'],flush=True)
    return 0 if result['execution']=='passed' else 1

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    for command in ('build','run'):
        p=sub.add_parser(command)
        for option in ('project-root','engine-source-root','engine-build-root'):p.add_argument('--'+option,type=Path,required=True)
        p.add_argument('--timeout',type=int,default=180 if command=='build' else 90)
        if command=='build':p.add_argument('--output-dir',type=Path,required=True)
        else:
            p.add_argument('--host-build',type=Path,required=True);p.add_argument('--fixture',type=Path,required=True);p.add_argument('--results-root',type=Path,required=True);p.add_argument('--running-samples',type=int,default=80)
    args=parser.parse_args(argv);return build_host(args) if args.command=='build' else run(args)

if __name__=='__main__':raise SystemExit(main())
