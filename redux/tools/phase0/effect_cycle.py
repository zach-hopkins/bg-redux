"""Bounded IMMCLOUD persistence experiment; engine and original data stay unchanged.

Runs stock GUI load/EnterGame in fresh processes, then a paused ordinary native
save. A timing-only private item override is a counterfactual, not a shipped fix.
"""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import struct
import uuid
import zlib

from harness import ROOT,LOCAL,BUILD,digest,environment,run_process
from save_harness import manifest,write
from probe_ui_resources import read_resource,TYPES

MAX=64*1024*1024
def text(data): return data.split(b'\0')[0].decode('ascii')
def block(data,at,size):
    if at<0 or size<0 or at+size>len(data): raise ValueError('Field exceeds fixture bounds')
    return data[at:at+size]
def u32(data,at): return struct.unpack('<I',block(data,at,4))[0]
def u16(data,at): return struct.unpack('<H',block(data,at,2))[0]

def area_from_save(folder):
    files=[p for p in folder.iterdir() if p.name.lower()=='baldur.sav']
    if len(files)!=1: raise ValueError('Required SAV absent/ambiguous')
    data=files[0].read_bytes()
    if data[:8]!=b'SAV V1.0' or len(data)>MAX: raise ValueError('Unsupported/excessive SAV')
    at=8;found=[]
    while at<len(data):
        n=u32(data,at);at+=4
        if not 1<=n<=260: raise ValueError('Invalid SAV filename')
        name=text(block(data,at,n));at+=n
        size,packed=u32(data,at),u32(data,at+4);at+=8
        compressed=block(data,at,packed);at+=packed
        if name.lower()!='ar0602.are': continue
        if size>MAX: raise ValueError('Area exceeds bound')
        decoder=zlib.decompressobj();area=decoder.decompress(compressed,MAX+1)
        if not decoder.eof or len(area)!=size or len(area)>MAX: raise ValueError('Bad compressed area')
        found.append(area)
    if len(found)!=1: raise ValueError('Required area absent/ambiguous')
    return found[0]

def wire_target(folder):
    data=area_from_save(folder)
    if data[:8]!=b'AREAV1.0': raise ValueError('Only AREAV1.0 supported')
    offset,count=u32(data,0x54),u16(data,0x58)
    if count>1000: raise ValueError('Excessive area actors')
    block(data,offset,count*272);found=[]
    for i in range(count):
        at=offset+i*272
        if struct.unpack('<HH',block(data,at+32,4))!=(2573,2461): continue
        cre=block(data,u32(data,at+136),u32(data,at+140))
        if cre[:8]!=b'CRE V1.0' or cre[0x33]!=1: raise ValueError('Requires embedded CRE V1.0 with v2 effects')
        effects=[];fxat,fxcount=u32(cre,0x2c4),u32(cre,0x2c8)
        if fxcount>10000: raise ValueError('Excessive CRE effects')
        block(cre,fxat,fxcount*264)
        for j in range(fxcount):
            f=block(cre,fxat+j*264,264)
            effects.append(dict(opcode=u32(f,8),parameters=[u32(f,20),u32(f,24)],timing=u16(f,28),
                duration=u32(f,32),source_ref=text(f[140:148])))
        found.append(dict(area_actor_index=i,cre_bytes=len(cre),cre_sha256=hashlib.sha256(cre).hexdigest(),effects=effects))
    if len(found)!=1: raise ValueError('Target CRE absent/ambiguous')
    return found[0]

def summarize_effects(effects):
    rows=[f for f in effects if f['source_ref'].upper()=='IMMCLOUD']
    from collections import Counter
    counts=Counter((f['opcode'],*f['parameters'][:2],f['timing']) for f in rows)
    return dict(total=len(rows),permanent=sum(f['timing']==1 for f in rows),equipped=sum(f['timing']==2 for f in rows),
        signatures=[dict(opcode=k[0],param1=k[1],param2=k[2],timing=k[3],count=v) for k,v in sorted(counts.items())])

def target_state(path):
    state=json.loads(path.read_text(encoding='utf-8'))
    rows=[a for a in state['current_area_actors'] if a['position']==[2573,2461]]
    if len(rows)!=1: raise ValueError('Native target absent/ambiguous')
    return state,rows[0]

def run_stage(output,name,fixture,override,mode='effect-cycle',cap_fps=30,native_args=None,timeout=45):
    receipt=json.loads((LOCAL/'gui-probe/build.json').read_text(encoding='utf-8'))
    if receipt['exit_code']!=0 or receipt['binary_sha256']!=digest(LOCAL/'gui-probe/Redux_gui_probe.exe'):
        raise ValueError('Native build failed or executable drifted')
    if receipt['engine_dll_sha256']!=digest(BUILD/'gemrb/libgemrb_core.dll'):raise ValueError('Engine binary drift')
    for path,sha in receipt['sources'].items():
        if digest(ROOT/path)!=sha:raise ValueError('Native source drift')
    directory=output/name;directory.mkdir()
    # Freeze the verified driver provenance before launch; a later host build
    # must not overwrite the only receipt for an earlier native experiment.
    write(directory/'build-receipt.json',receipt)
    frozen_sources=directory/'driver-sources';frozen_sources.mkdir()
    for path,sha in receipt['sources'].items():
        shutil.copy2(ROOT/path,frozen_sources/Path(path).name)
        if digest(frozen_sources/Path(path).name)!=sha:raise ValueError('Driver source changed during archive')
    profile=directory/'engine-profile';(profile/'save').mkdir(parents=True)
    copied=profile/'save/000000007-HarnessInput';shutil.copytree(fixture,copied)
    before=manifest(copied);(directory/'cache').mkdir()
    config=dict(GameType='bg2ee',GameName='Redux Phase 0 effect lifecycle',GamePath=LOCAL/'bg2ee-clean',
        GemRBPath=ROOT/'gemrb/gemrb',GUIScriptsPath=ROOT/'gemrb/gemrb',GemRBOverridePath=ROOT/'gemrb/gemrb',
        GemRBUnhardcodedPath=ROOT/'gemrb/gemrb',PluginsPath=BUILD/'gemrb/plugins',CachePath=directory/'cache',
        SavePath=profile,UseAsLibrary=0,Width=1024,Height=768,FullScreen=0,CapFPS=cap_fps,AudioDriver='none',
        GameLanguagePath='lang/en_US',SkipIntroVideos=1,Logging=1,LogColor=0,PathfinderThreadsCount=0,PathfinderMainThreadMode='immediate')
    if override:config['ModPath']=override
    cfg=directory/'probe.cfg';cfg.write_text(''.join(f'{k}={str(v).replace(chr(92),chr(47))}\n' for k,v in config.items()),encoding='utf-8')
    command=[str(LOCAL/'gui-probe/Redux_gui_probe.exe'),'--config',str(cfg),'--output',str(directory),
             '--scripts',str(ROOT/'tools/phase0/gui'),'--mode',mode]
    if native_args:command+=native_args
    process=run_process(command,BUILD,environment(directory),directory/'process.log',timeout)
    result=dict(name=name,process=process,command=command,input_unchanged=manifest(copied)==before,
                driver_build_receipt=receipt,
                input_wire=summarize_effects(wire_target(copied)['effects']) if mode!='live-clock' else None)
    write(directory/'process-result.json',result)
    if process['exit_code']!=0 or process['timed_out']: raise ValueError('Native effect cycle failed: '+str(directory))
    native=json.loads((directory/'gui-result.json').read_text())
    if not native['completed']:raise ValueError('Incomplete native lifecycle')
    if mode in ('string-challenge','live-clock'):
        result['native']=json.loads((directory/('string-challenge.json' if mode=='string-challenge' else 'clock-samples.json')).read_text())
        result['artifacts']={p.name:digest(p) for p in directory.iterdir() if p.is_file()}
        write(directory/'process-result.json',result)
        return result,None
    result['native']=json.loads((directory/'effect-result.json').read_text())
    for phase in ['entry','refresh1','refresh2','persisted']:
        state,actor=target_state(directory/(phase+'.state.json'))
        result[phase]=dict(game_time=state['game_time'],effects=summarize_effects(actor['effects']),
            total_actor_effects=len(actor['effects']),base_stats_sha256=hashlib.sha256(json.dumps(actor['base_stats']).encode()).hexdigest(),
            modified_stats_sha256=hashlib.sha256(json.dumps(actor['modified_stats']).encode()).hexdigest())
    created=[p for p in (profile/'save').iterdir() if p.name.endswith('-Redux Effect Cycle')]
    if len(created)!=1:raise ValueError('Required cycle save missing')
    result['output_wire']=summarize_effects(wire_target(created[0])['effects'])
    result['artifacts']={p.name:digest(p) for p in directory.iterdir() if p.is_file()}
    write(directory/'process-result.json',result)
    return result,created[0]

def main():
    output=LOCAL/'results'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-immcloud-'+uuid.uuid4().hex[:8]);output.mkdir()
    report=dict(schema='bg-redux-effect-lifecycle/1',directory=str(output),conditions={},assertions=[])
    report['runner_sha256']=digest(Path(__file__))
    report['startup_sha256']=digest(ROOT/'tools/phase0/gui/ReduxStart.py')
    fixture=LOCAL/'fixtures/original-bg2ee-20261020/GemRB';fixture_before=manifest(fixture)
    try:
        receipt=json.loads((LOCAL/'gui-probe/build.json').read_text())
        if receipt['binary_sha256']!=digest(LOCAL/'gui-probe/Redux_gui_probe.exe') or receipt['engine_dll_sha256']!=digest(BUILD/'gemrb/libgemrb_core.dll'):raise ValueError('Native provenance drift')
        for p,sha in receipt['sources'].items():
            if digest(ROOT/p)!=sha:raise ValueError('Native source drift')
        pinned=json.loads((ROOT/'docs/compatibility/evidence/vanilla-save-fixture.json').read_text())
        if fixture_before!=pinned['files']:raise ValueError('Original fixture drift')
        report['build']=receipt
        TYPES['itm']=0x3ed
        item,origin=read_resource('immcloud','itm')
        if item[:8]!=b'ITM V1  ':raise ValueError('Expected ITM V1')
        at,index,count=u32(item,0x6a),u16(item,0x6e),u16(item,0x70)
        rows=[];modified=bytearray(item)
        for i in range(count):
            p=at+(index+i)*48;block(item,p,48)
            rows.append(dict(index=i,opcode=u16(item,p),parameters=[u32(item,p+4),u32(item,p+8)],timing=item[p+12]))
            if item[p+12]==1:modified[p+12]=2
        mod=output/'timing-only-mod';mod.mkdir();(mod/'immcloud.itm').write_bytes(modified)
        report['item']=dict(origin=origin,sha256=hashlib.sha256(item).hexdigest(),equipping_effects=rows,
                           counterfactual_sha256=digest(mod/'immcloud.itm'),changed_byte_offsets=[i for i,(a,b) in enumerate(zip(item,modified)) if a!=b])
        for condition,override,cycles in [('stock',None,4),('timing2-control',mod,3)]:
            current=fixture;stages=[]
            for cycle in range(cycles):
                result,current=run_stage(output,f'{condition}-{cycle}',current,override);stages.append(result)
                print(condition,cycle,'wire in',result['input_wire']['total'],'entry',result['entry']['effects']['total'],'wire out',result['output_wire']['total'],flush=True)
            report['conditions'][condition]=stages
        def check(name,ok):report['assertions'].append(dict(name=name,passed=bool(ok)))
        stock=report['conditions']['stock'];control=report['conditions']['timing2-control']
        check('exactly-seven-private-item-timing-bytes',len(report['item']['changed_byte_offsets'])==7)
        check('stock-wire-growth-seven-per-cycle',all(s['output_wire']['total']==s['input_wire']['total']+7 for s in stock))
        check('stock-entry-equips-thirteen-effects',all(s['entry']['effects']['total']==s['input_wire']['total']+13 for s in stock))
        check('control-stops-wire-growth',all(s['output_wire']['total']==s['input_wire']['total'] for s in control))
        check('refresh-does-not-grow-queue',all(s['entry']['effects']==s['refresh1']['effects']==s['refresh2']['effects'] for ss in report['conditions'].values() for s in ss))
        check('protection-queries-true-and-stable',all(all(s['native']['protection_queries_before'].values()) and s['native']['protection_queries_before']==s['native']['protection_queries_after'] for ss in report['conditions'].values() for s in ss))
        check('inputs-unchanged',all(s['input_unchanged'] for ss in report['conditions'].values() for s in ss))
        for field in ['base_stats_sha256','modified_stats_sha256']:
            check('stable-'+field,len({s[phase][field] for ss in report['conditions'].values() for s in ss for phase in ['entry','refresh1','refresh2','persisted']})==1)
        report['original_fixture_unchanged']=fixture_before==manifest(fixture)
        report['verdict']='characterized' if all(c['passed'] for c in report['assertions']) and report['original_fixture_unchanged'] else 'failed'
    except (OSError,ValueError,KeyError,struct.error,zlib.error) as error:
        report['verdict']='failed';report['error']=str(error)
    report['engine_status']=__import__('subprocess').check_output(['git','-C',str(ROOT/'gemrb'),'status','--porcelain'],text=True)
    write(output/'result.json',report)
    print(json.dumps(dict(directory=str(output),verdict=report['verdict'],assertions=report['assertions'],error=report.get('error')),indent=2))
    return 0 if report['verdict']=='characterized' and not report['engine_status'].strip() else 1

if __name__=='__main__':raise SystemExit(main())
