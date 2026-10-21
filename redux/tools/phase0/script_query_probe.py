"""Prepare a private BCS query/autosave fixture and validate its GemRB execution.

All script/CRE changes are declared laboratory inputs; this does not launch BG2EE.
"""
import datetime
import json
import shutil
import uuid
from pathlib import Path
from harness import ROOT,LOCAL,digest
from effect_cycle import block,u32,run_stage
from legacy_oracle import read_wire
from save_harness import manifest,write,member
from scan_weapon_triggers import condition_blocks

EMPTY='0 0 0 0 0 0 0 0 0 0 0 0 ""'
PLAYER2='0 0 0 0 0 0 0 22 0 0 0 0 ""'
QUERY_KEYS=('RDXVE','RDXVD','RDXDONE','RDXSTAGE')


def query_values(globals):
    """A chapter autosave or missing false value is not a completed query."""
    values={k:globals.get(k) for k in QUERY_KEYS}
    if values['RDXDONE']!=1 or values['RDXSTAGE']!=3:
        raise ValueError('Query completion marker missing')
    if any(type(values[k]) is not int or values[k] not in (0,1) for k in QUERY_KEYS[:2]):
        raise ValueError('Query Boolean missing or invalid')
    return values

def trigger(opcode,value=0,name='',obj=EMPTY):
    return f'TR\n{opcode} {value} 0 0 0 "{name}" "" OB\n{obj}OB\nTR\n'

def action(opcode,value=0,name=''):
    return f'{opcode}OB\n{EMPTY}OB\nOB\n{EMPTY}OB\nOB\n{EMPTY}OB\n{value} 0 0 0 0"{name}" "" AC\n'

def response(condition,actions):
    return 'CR\nCO\n'+condition+'CO\nRS\nRE\n100AC\n'+'AC\n'.join(actions)+'RE\nRS\nCR\n'

def program():
    source='SC\n'
    for stage,opcode,name in [(0,0x40ec,'RDXVE'),(1,0x40f2,'RDXVD')]:
        gate=trigger(0x400f,stage,'GLOBALRDXSTAGE')
        for truth in [True,False]:
            condition=gate+(trigger(opcode,1,obj=PLAYER2) if truth else '')
            source+=response(condition,[action(30,int(truth),'GLOBAL'+name),action(30,stage+1,'GLOBALRDXSTAGE')])
    source+=response(trigger(0x400f,2,'GLOBALRDXSTAGE'),[action(30,1,'GLOBALRDXDONE'),action(30,3,'GLOBALRDXSTAGE'),action(190,0)])
    source+='SC\n'
    return source.encode('ascii')

def prepare(out):
    original=LOCAL/'fixtures/original-bg2ee-20261020/GemRB'
    pinned=json.loads((ROOT/'docs/compatibility/evidence/vanilla-save-fixture.json').read_text(encoding='utf-8'))
    if manifest(original)!=pinned['files']:raise ValueError('Baseline drift')
    baseline=out/'query-input';shutil.copytree(original,baseline)
    gam=baseline/'BALDUR.gam';data=bytearray(gam.read_bytes())
    if data[:8]!=b'GAMEV2.0' or u32(data,0x24)!=2:raise ValueError('Expected two-actor GAMEV2.0')
    if any(name in read_wire(gam)['globals'] for name in ['RDXSTAGE','RDXVE','RDXVD','RDXDONE']):raise ValueError('Probe global collision')
    offsets=[]
    for index in range(2):
        at=u32(data,0x20)+index*0x160;creat,size=u32(data,at+4),u32(data,at+8)
        if block(data,creat,8)!=b'CRE V1.0' or size<0x2d4:raise ValueError('Expected embedded CRE V1.0')
        for slot in range(5):
            offset=creat+0x248+slot*8
            value=b'RDXQPROB' if index==0 and slot==0 else b'NONE\0\0\0\0'
            data[offset:offset+8]=value;offsets.append(dict(actor=index,file_script_slot=slot,offset=offset,value=value.rstrip(b'\0').decode()))
    gam.write_bytes(data)
    override=out/'query-override';override.mkdir();(override/'RDXQPROB.bcs').write_bytes(program())
    hits,total=condition_blocks(program())
    if total!=7 or len(hits)!=2:raise ValueError('Generated script validation failed')
    if manifest(original)!=pinned['files']:raise ValueError('Source mutated')
    return baseline,override,dict(input_files=manifest(baseline),declared_script_assignments=offsets,
        generated_script_sha256=digest(override/'RDXQPROB.bcs'),generated_trigger_records=total,
        semantics='Protagonist override queries MAINHAND against Player2, records results then requests slot0 autosave; both party actors other five file scripts NONE. Actor stats/items/effects unchanged.')

def main():
    out=LOCAL/'results'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-script-query-'+uuid.uuid4().hex[:8]);out.mkdir()
    report=dict(schema='bg-redux-script-query-prototype/1',directory=str(out),verdict='failed',original_runtime_executed=False)
    try:
        fixture,override,construction=prepare(out);report['construction']=construction
        stage,_=run_stage(out,'gemrb',fixture,override,'live-clock',30,['--clock-running-samples','32']);report['process']=stage['process']
        if report['process']['exit_code']!=0 or report['process']['timed_out']:raise ValueError('Native query process failed')
        saves=[p for p in (out/'gemrb/engine-profile/save').iterdir() if p.is_dir() and p.name!='000000007-HarnessInput']
        report['created_save_folders']=[p.name for p in saves]
        completed=[];report['saved_observations']=[]
        for save in saves:
            gam=member(save,'gam')
            globals=read_wire(gam)['globals'];values={k:globals.get(k) for k in ['RDXVE','RDXVD','RDXDONE','RDXSTAGE']}
            report['saved_observations'].append(dict(folder=save.name,query_globals=values))
            if values.get('RDXDONE')==1:completed.append((save,query_values(globals)))
        if not completed:raise ValueError('No completed BCS query autosave; chapter autosaves are not probe success')
        saved,report['query_globals']=completed[0]
        if report['query_globals']!={'RDXVE':0,'RDXVD':0,'RDXDONE':1,'RDXSTAGE':3}:raise ValueError('Incomplete/unexpected current-stub query result')
        report['autosave_files']=manifest(saved);report['verdict']='gemrb-script-prototype-executed'
    except (OSError,ValueError,KeyError,TypeError) as error:report['error']=str(error)
    report['source_sha256']=digest(Path(__file__))
    write(out/'result.json',report);write(ROOT/'docs/compatibility/evidence/script-query-results.json',report)
    print(json.dumps(report,indent=2))
    return 0 if report['verdict']=='gemrb-script-prototype-executed' else 1

if __name__=='__main__':raise SystemExit(main())
