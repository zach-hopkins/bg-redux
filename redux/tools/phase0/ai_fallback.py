"""Execute instrumented, isolated stock AI attack tails against a declared foe.

This is branch characterization, not an unmodified full-AI campaign test.
Original AttackOneRound actions are retained after the marker/autosave actions.
"""
import datetime
import hashlib
import json
from pathlib import Path
import struct
import uuid
import zlib
from harness import ROOT,LOCAL,digest
from save_harness import manifest,write,member
from effect_cycle import block,u32,u16,text,run_stage
from equipped_defenses import construct,embedded,observe,validate_observation
from script_query_probe import trigger,action,response,EMPTY
from scan_weapon_triggers import BLOCK,TRIGGER
from probe_ui_resources import read_resource,TYPES
from legacy_oracle import read_wire

CASES=[dict(id=name,source=source,first=first,remove_queries=remove) for name,source,first,remove in [
    ('ai-imoen-stock','bdimoenc',115,False),('ai-imoen-noquery','bdimoenc',115,True),
    ('ai-default-stock','bddefai',307,False),('ai-default-noquery','bddefai',307,True)]]


def program(spec):
    TYPES['bcs']=0x3ef
    data,origin=read_resource(spec['source'],'bcs');source=data.decode('ascii').replace('\r\n','\n')
    blocks=list(BLOCK.finditer(source));compiled='SC\n';removed=0
    seen=trigger(0x400f,0,'GLOBALRDXFOESEEN')+trigger(0x401c,name='',obj='0 0 0 0 0 0 0 0 0 0 0 0 "rdxfoe"')
    compiled+=response(seen,[action(30,1,'GLOBALRDXFOESEEN')])
    for index in range(spec['first'],spec['first']+4):
        original=blocks[index];condition=original[1];resp=original[2]
        if spec['remove_queries']:
            def strip(match):
                nonlocal removed
                if int(match[1]) in (0x40ec,0x40f2):removed+=1;return ''
                return match[0]
            condition=TRIGGER.sub(strip,condition)
        # Retain original action payload byte-for-byte, inserting only markers.
        prefix='AC\n'.join([action(30,index,'GLOBALRDXBRANCH'),action(30,1,'GLOBALRDXAIDONE')])+'AC\n'
        resp=resp.replace('100AC\n','100AC\n'+prefix,1)
        foe='0 0 0 0 0 0 0 0 0 0 0 0 "rdxfoe"'
        neutral=f'153OB\n{EMPTY}OB\nOB\n{foe}OB\nOB\n{EMPTY}OB\n128 0 0 0 0"" "" AC\n'
        suffix='AC\n'+'AC\n'.join([neutral,action(63,3),action(190,0)])
        at=resp.rfind('RE\n');resp=resp[:at]+suffix+resp[at:]
        compiled+='CR\nCO\n'+trigger(0x400f,0,'GLOBALRDXAIDONE')+condition+'CO\nRS\n'+resp+'RS\nCR\n'
    compiled+=response(trigger(0x400f,0,'GLOBALRDXAIDONE'),[action(30,0,'GLOBALRDXBRANCH'),action(30,1,'GLOBALRDXAIDONE'),action(190,0)])
    if removed!=(6 if spec['remove_queries'] else 0):raise ValueError('Unexpected predicate removal count')
    return (compiled+'SC\n').encode('ascii'),dict(origin=origin,source_sha256=hashlib.sha256(data).hexdigest(),stock_blocks=list(range(spec['first'],spec['first']+4)),removed_query_records=removed,
        instrumentation='Added named-foe visibility marker and one-response gates; prepended branch/done globals, retained original AttackOneRound then appended lab cleanup (foe neutral, Wait3, SaveGame0); omitted other full-script branches')


def install_foe(fixture):
    gam=(fixture/'BALDUR.gam').read_bytes();row,cre=embedded(gam,0)
    # Strip the diagnostic weapon and all scripts/effects from this NPC copy.
    struct.pack_into('<I',cre,0x2c0,0);struct.pack_into('<I',cre,0x2c8,0)
    slotat=u32(cre,0x2b8);cre[slotat:slotat+80]=struct.pack('<38HhH',*([0xffff]*38),1000,0)
    cre[0x270]=255;cre[0x280:0x2a0]=b'RDXFOE'.ljust(32,b'\0');struct.pack_into('<I',cre,0x20,0);struct.pack_into('<hh',cre,0x24,200,200)
    for s in range(5):cre[0x248+s*8:0x250+s*8]=b'NONE\0\0\0\0'
    px,py=struct.unpack_from('<HH',gam,row+0x20);position=(px+40,py)
    sav=member(fixture,'sav');data=sav.read_bytes()
    if data[:8]!=b'SAV V1.0':raise ValueError('Expected SAV V1.0')
    result=bytearray(data[:8]);at=8;changed=0
    while at<len(data):
        start=at;n=u32(data,at);at+=4;name=text(block(data,at,n));at+=n
        size,packed=u32(data,at),u32(data,at+4);at+=8;payload=block(data,at,packed);at+=packed
        if name.lower()!='ar0602.are':result.extend(data[start:at]);continue
        if size>64*1024*1024:raise ValueError('Area exceeds bound')
        area=bytearray(zlib.decompress(payload))
        if len(area)!=size or area[:8]!=b'AREAV1.0':raise ValueError('Invalid area')
        actorat,count=u32(area,0x54),u16(area,0x58);matches=[]
        for i in range(count):
            p=actorat+i*272
            if struct.unpack_from('<HH',area,p+32)==(2573,2461):matches.append(p)
        if len(matches)!=1:raise ValueError('Required Mephit replacement target ambiguous')
        p=matches[0];area[p:p+32]=b'RDXFOE'.ljust(32,b'\0');struct.pack_into('<4H',area,p+32,*position,*position)
        struct.pack_into('<II',area,p+136,len(area),len(cre));area.extend(cre)
        packedarea=zlib.compress(area);result.extend(struct.pack('<I',n));result.extend(name.encode()+b'\0');result.extend(struct.pack('<II',len(area),len(packedarea)));result.extend(packedarea);changed+=1
    if changed!=1:raise ValueError('Expected one area change')
    sav.write_bytes(result)
    return dict(replaced_original_actor_position=[2573,2461],foe_position=position,foe_script_name='RDXFOE',allegiance=255,hp=200,foe_scripts='NONE',foe_effects=0,
        scope='Synthetic idle foe replaces one embedded area Mephit; other area actors/scripts are retained')


def construct_ai(out,spec):
    fixture,override,construction=construct(out,dict(id=spec['id'],weapon='sw1h02',defense=None))
    data=bytearray((fixture/'BALDUR.gam').read_bytes());row,cre=embedded(data,0)
    offset=u32(data,row+4)+0x248;data[offset:offset+8]=b'RDXAIPRB';(fixture/'BALDUR.gam').write_bytes(data)
    compiled,annotation=program(spec);(override/'RDXAIPRB.bcs').write_bytes(compiled)
    construction.update(ai_script=annotation,foe=install_foe(fixture),input_files=manifest(fixture),ai_script_sha256=digest(override/'RDXAIPRB.bcs'))
    return fixture,override,construction


def completed_ai(directory,spec):
    after=directory/'clock-after.state.json'
    if after.is_file():
        state=json.loads(after.read_text());g={k.upper():v for k,v in state['globals'].items()}
        if g.get('RDXAIDONE')!=1 or g.get('RDXFOESEEN')!=1 or g.get('RDXBRANCH') not in range(spec['first'],spec['first']+4):raise ValueError('AI branch/visibility completion missing')
        pc=state['party'][0];foes=[a for a in state['current_area_actors'] if a['script_name'].lower()=='rdxfoe']
        if len(foes)!=1:raise ValueError('Runtime foe absent/ambiguous')
        inv=pc['inventory']
        if inv['equipped']!=0 or not any(x['slot']==35 and x['resref'].lower()=='sw1h02' for x in inv['items']):raise ValueError('AI runtime weapon mismatch')
        samples=json.loads((directory/'clock-samples.json').read_text())['samples']
        attacks=[s['sample'] for s in samples if any(a['runtime_id']==pc['runtime_id'] and a['action_id']==105 and a['current_action_target']==foes[0]['runtime_id'] for a in s.get('action_trace',[]))]
        if not attacks:raise ValueError('AttackOneRound against declared foe not sampled')
        return dict(branch=g['RDXBRANCH'],foe_seen=g['RDXFOESEEN'],attack_samples=attacks,
            foe_runtime_id=foes[0]['runtime_id'],foe_hp_after=foes[0]['modified_stats'][0],
            observation_method='Normal-loop snapshot and action/target samples, independent of save availability',
            state_sha256=digest(after),samples_sha256=digest(directory/'clock-samples.json'),
            autosave_present=any(p.name!='000000007-HarnessInput' for p in (directory/'engine-profile/save').iterdir()))
    for folder in (directory/'engine-profile/save').iterdir():
        if not folder.is_dir() or folder.name=='000000007-HarnessInput':continue
        gam=member(folder,'gam');g=read_wire(gam)['globals']
        if g.get('RDXAIDONE')==1:
            if g.get('RDXFOESEEN')!=1 or g.get('RDXBRANCH') not in range(spec['first'],spec['first']+4):raise ValueError('AI tail/foe prerequisites did not succeed')
            actors=observe(gam);validate_observation(dict(weapon='sw1h02',defense=None),actors)
            return dict(folder=str(folder),branch=g['RDXBRANCH'],foe_seen=g['RDXFOESEEN'],actors=actors,files=manifest(folder))
    raise ValueError('AI completed marker autosave missing')


def main():
    out=LOCAL/'results'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-ai-fallback-'+uuid.uuid4().hex[:8]);out.mkdir()
    report=dict(schema='bg-redux-ai-fallback/1',directory=str(out),cases=[],verdict='failed')
    for spec in CASES:
        entry=dict(spec=spec,verdict='failed');report['cases'].append(entry)
        try:
            caseout=out/spec['id'];caseout.mkdir();fixture,override,construction=construct_ai(caseout,spec);entry['construction']=construction
            stage,_=run_stage(caseout,'gemrb',fixture,override,'live-clock',30,['--clock-running-samples','80','--trace-actions','1']);entry['process']=stage['process']
            entry['output']=completed_ai(caseout/'gemrb',spec);entry['verdict']='gemrb-ai-executed'
        except (OSError,ValueError,KeyError,TypeError) as error:entry['error']=str(error)
        write(out/'result.json',report);print(spec['id'],entry['verdict'],entry.get('error',''),flush=True)
    report['verdict']='gemrb-ai-cases-executed' if all(c['verdict']=='gemrb-ai-executed' for c in report['cases']) else 'partial-or-failed'
    report['source_sha256']=digest(Path(__file__));write(out/'result.json',report);write(ROOT/'docs/compatibility/evidence/ai-fallback-results.json',report)
    print('Directory:',out,flush=True);return 0 if report['verdict']=='gemrb-ai-cases-executed' else 1


if __name__=='__main__':raise SystemExit(main())
