"""Declared CRE laboratory equipment/defense cases; unchanged engine binaries.

Append relocated embedded CRE copies to a disposable GAM. Existing GAM sections
stay at their original offsets. Each appended CRE declares its own item/effect
tables; obsolete bytes are intentionally unreferenced, never stripped to pass.
"""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import struct
import uuid
from harness import ROOT,LOCAL,digest
from save_harness import manifest,write,member
from script_query_probe import prepare,query_values
from effect_cycle import block,u16,u32,text,run_stage
from legacy_oracle import read_wire
from probe_ui_resources import read_resource,TYPES

CASES=[dict(id=name,weapon=weapon,defense=defense) for name,weapon,defense in [
    ('01-normal','sw1h01',None),('02-plus1','sw1h02',None),
    ('03-normal-magprot','sw1h01',(120,0,1)),('04-plus1-magprot','sw1h02',(120,0,1)),
    ('05-slash100','sw1h01',(86,100,1)),('06-stoneskin','sw1h02',(218,3,0)),
    ('07-mirror','sw1h02',(159,3,0)),('08-bow','bow01',None)]]


def embedded(data,index):
    if data[:8]!=b'GAMEV2.0' or index>=u32(data,0x24):raise ValueError('Missing GAMEV2.0 actor')
    row=u32(data,0x20)+index*0x160
    cre=bytearray(block(data,u32(data,row+4),u32(data,row+8)))
    if cre[:8]!=b'CRE V1.0' or cre[0x33]!=1:raise ValueError('Requires CRE V1.0 / v2 effects')
    return row,cre


def relocate(data,index,cre):
    row,_=embedded(data,index)
    struct.pack_into('<II',data,row+4,len(data),len(cre));data.extend(cre)


def add_equipment(cre,weapon):
    if u32(cre,0x2c0)!=0:raise ValueError('Expected empty protagonist inventory')
    refs=[weapon]+(['arow01'] if weapon=='bow01' else [])
    items=b''.join(r.upper().encode().ljust(8,b'\0')+struct.pack('<4HI',0,40 if r=='arow01' else 0,0,0,1) for r in refs)
    itemat=len(cre);cre.extend(items)
    slots=[0xffff]*38;slots[9]=0
    if weapon=='bow01':slots[13]=1
    slotat=len(cre);cre.extend(struct.pack('<38HhH',*slots,-24 if weapon=='bow01' else 0,0))
    struct.pack_into('<III',cre,0x2b8,slotat,itemat,len(refs))


def effect(opcode,p1,p2):
    data=bytearray(264)
    struct.pack_into('<IIIIIHHIHH',data,8,opcode,2,0,p1,p2,9,0,0,100,0)
    data[140:148]=b'RDXDEF\0\0';struct.pack_into('<I',data,156,0xffffffff)
    return data


def add_defense(cre,spec):
    if spec is None:return
    old=block(cre,u32(cre,0x2c4),u32(cre,0x2c8)*264)
    newat=len(cre);cre.extend(old);cre.extend(effect(*spec))
    struct.pack_into('<II',cre,0x2c4,newat,len(old)//264+1)


def observe(gam):
    data=Path(gam).read_bytes();actors=[]
    for i in range(2):
        _,c=embedded(data,i);itemat,count=u32(c,0x2bc),u32(c,0x2c0);slotat=u32(c,0x2b8)
        if count>100:raise ValueError('Inventory exceeds bound')
        block(c,itemat,count*20);block(c,slotat,80)
        refs=[text(block(c,itemat+j*20,8)).lower() for j in range(count)]
        slots=[u16(c,slotat+j*2) for j in range(38)]
        if any(v!=0xffff and v>=count for v in slots):raise ValueError('Invalid item slot index')
        fxat,fxcount=u32(c,0x2c4),u32(c,0x2c8)
        if fxcount>10000:raise ValueError('Excessive effects')
        fx=[]
        for j in range(fxcount):
            f=block(c,fxat+j*264,264)
            if text(f[140:148]).upper()=='RDXDEF':fx.append(dict(opcode=u32(f,8),p1=u32(f,20),p2=u32(f,24),timing=u16(f,28)))
        actors.append(dict(items=refs,physical_slots={str(j):refs[v] for j,v in enumerate(slots) if v!=0xffff},
            selected=struct.unpack_from('<h',c,slotat+76)[0],ability=u16(c,slotat+78),defense_effects=fx))
    return actors


def validate_observation(spec,actors):
    pc,target=actors
    if pc['physical_slots'].get('9')!=spec['weapon'] or pc['ability']!=0:raise ValueError('Required weapon/ability not equipped')
    if spec['weapon']=='bow01':
        if pc['physical_slots'].get('13')!='arow01' or pc['selected']!=-24:raise ValueError('Required bow/ammo selection absent')
    elif pc['selected']!=0:raise ValueError('Weapon slot0 not selected')
    fx=target['defense_effects']
    if spec['defense'] is None:
        if fx:raise ValueError('Unexpected diagnostic defense')
    elif len(fx)!=1 or fx[0]['opcode']!=spec['defense'][0]:raise ValueError('Required defense absent/ambiguous')
    elif spec['defense'][0]==120 and fx[0]['p2']!=1:raise ValueError('Magical-weapon protection mode changed')
    # Protection:Weapons is intentionally normalized by GemRB on reload.
    elif spec['defense'][0]!=120 and (fx[0]['p1'],fx[0]['p2'])!=tuple(spec['defense'][1:]):raise ValueError('Defense magnitude/mode changed')


def construct(out,spec):
    fixture,override,construction=prepare(out)
    gam=fixture/'BALDUR.gam';data=bytearray(gam.read_bytes())
    _,attacker=embedded(data,0);add_equipment(attacker,spec['weapon']);relocate(data,0,attacker)
    # BG2EE GAM quick slots use engine slot IDs:10 fists,35 weapon0,11 ammo0.
    # Keeping the baseline's quickslot10 silently reselects fists on entry.
    row,_=embedded(data,0)
    struct.pack_into('<4H',data,row+0x8c,11 if spec['weapon']=='bow01' else 35,10,10,10)
    struct.pack_into('<4H',data,row+0x94,0,0,0,0)
    _,defender=embedded(data,1);add_defense(defender,spec['defense']);relocate(data,1,defender)
    gam.write_bytes(data);observed=observe(gam);validate_observation(spec,observed)
    construction.update(input_files=manifest(fixture),equipment_defense=spec,input_observation=observed,
        relocation='Append new embedded CRE copies, update only GAM party CRE offset/size; preserve original GAM sections and old unreferenced bytes')
    return fixture,override,construction


def completed(directory,spec):
    candidates=[]
    for folder in (directory/'engine-profile/save').iterdir():
        if not folder.is_dir() or folder.name=='000000007-HarnessInput':continue
        gam=member(folder,'gam');g=read_wire(gam)['globals']
        if g.get('RDXDONE')==1:
            vals=query_values(g);actors=observe(gam);validate_observation(spec,actors)
            candidates.append(dict(folder=str(folder),values=vals,actors=actors,files=manifest(folder)))
    if not candidates:raise ValueError('Completed query/equipment/defense autosave missing')
    return candidates[0]


def main():
    out=LOCAL/'results'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-equipped-defenses-'+uuid.uuid4().hex[:8]);out.mkdir()
    report=dict(schema='bg-redux-equipped-defenses/1',directory=str(out),cases=[],verdict='failed')
    TYPES['itm']=0x3ed
    for spec in CASES:
        entry=dict(spec=spec,verdict='failed');report['cases'].append(entry)
        try:
            caseout=out/spec['id'];caseout.mkdir();fixture,override,construction=construct(caseout,spec)
            item,origin=read_resource(spec['weapon'],'itm')
            entry.update(construction=construction,weapon_metadata=dict(origin=origin,sha256=hashlib.sha256(item).hexdigest(),enchantment=u32(item,0x60)))
            stage,_=run_stage(caseout,'gemrb',fixture,override,'live-clock',30,['--clock-running-samples','32'])
            entry['process']=stage['process'];entry['output']=completed(caseout/'gemrb',spec);entry['verdict']='gemrb-executed'
        except (OSError,ValueError,KeyError,TypeError) as error:entry['error']=str(error)
        write(out/'result.json',report);print(spec['id'],entry['verdict'],entry.get('error',''),flush=True)
    report['verdict']='gemrb-cases-executed' if all(c['verdict']=='gemrb-executed' for c in report['cases']) else 'partial-or-failed'
    report['source_sha256']=digest(Path(__file__))
    write(out/'result.json',report);write(ROOT/'docs/compatibility/evidence/equipped-defense-results.json',report)
    print('Directory:',out,flush=True)
    return 0 if report['verdict']=='gemrb-cases-executed' else 1


if __name__=='__main__':raise SystemExit(main())
