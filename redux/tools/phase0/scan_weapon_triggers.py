"""Census two verified EE trigger stubs in packaged BG2EE BCS condition blocks.

This is a bounded compiled-text reader, not a script interpreter or branch hit trace.
"""
import datetime
import hashlib
import json
from pathlib import Path
import re
from collections import Counter
from harness import ROOT,LOCAL,digest
from probe_ui_resources import resources,read_resource,TYPES
from effect_cycle import block,u32,text
from save_harness import write

IDS={0x40ec:'WeaponEffectiveVs',0x40f2:'WeaponCanDamage'}
TRIGGER=re.compile(r'(?m)^TR\n(\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) "([^"\n]*)" "([^"\n]*)" OB\n([^\n]*)OB\nTR(?:\n|$)')
BLOCK=re.compile(r'(?ms)^CR\nCO\n(.*?)^CO\nRS\n(.*?)^RS\nCR(?:\n|$)')

def condition_blocks(data):
    if len(data)>16*1024*1024:raise ValueError('BCS exceeds scan bound')
    source=data.decode('ascii').replace('\r\n','\n')
    if not source.startswith('SC\n'):raise ValueError('Unsupported compiled script signature')
    result=[];total=0;blocks=list(BLOCK.finditer(source))
    for index,match in enumerate(blocks):
        cond,response=match.groups();rows=list(TRIGGER.finditer(cond))
        if len(re.findall(r'(?m)^TR$',cond))!=len(rows)*2:raise ValueError('Unsupported/incomplete trigger record')
        triggers=[dict(opcode=int(r[1]),hand=int(r[2]),flags=int(r[3]),int1=int(r[4]),int2=int(r[5]),object_encoding=r[8]) for r in rows]
        total+=len(rows)
        hits=[t for t in triggers if t['opcode'] in IDS]
        if hits:
            result.append(dict(block=index,triggers=hits,contains_or=any(t['opcode']==0x4000 for t in triggers),
                positive_stub_without_or=not any(t['opcode']==0x4000 for t in triggers) and any(t['flags']&1==0 for t in hits),
                response_action_ids=[int(i) for i in re.findall(r'(?m)^(\d+)OB$',response)]))
    if result and result[-1]['block']+1<len(blocks):
        following=blocks[result[-1]['block']+1]
        result[-1]['following_block']=dict(index=result[-1]['block']+1,
            trigger_opcodes=[int(r[1]) for r in TRIGGER.finditer(following[1])],
            response_action_ids=[int(i) for i in re.findall(r'(?m)^(\d+)OB$',following[2])])
    if len(re.findall(r'(?m)^TR$',source))!=total*2:raise ValueError('Trigger records outside parsed response blocks')
    return result,total

def saved_party_scripts():
    data=(LOCAL/'fixtures/original-bg2ee-20261020/GemRB/BALDUR.gam').read_bytes()
    if data[:8]!=b'GAMEV2.0':raise ValueError('Expected GAMEV2.0 reference')
    offset,count=u32(data,0x20),u32(data,0x24)
    if count>6:raise ValueError('Unexpected baseline party size')
    rows=[]
    for index in range(count):
        at=offset+index*0x160;cre=block(data,u32(data,at+4),u32(data,at+8))
        if cre[:8]!=b'CRE V1.0':raise ValueError('Expected CRE V1.0 party')
        rows.append(dict(party_index=index,file_scripts={name:text(block(cre,0x248+i*8,8)).lower()
            for i,name in enumerate(['override','class','race','general','default'])}))
    return rows

def main():
    TYPES.update(bcs=0x3ef,ids=0x3f0)
    report=dict(schema='bg-redux-weapon-trigger-exposure/1',captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scope=__doc__,scripts_scanned=0,trigger_records_scanned=0,hits=[],errors=[],known_stubs=IDS)
    counts=Counter();action,_=read_resource('action','ids');names={}
    for line in action.decode('ascii').splitlines():
        parts=line.split()
        if len(parts)>1 and parts[0].isdigit():names.setdefault(int(parts[0]),parts[1].split('(')[0])
    for ref,kind in sorted(resources):
        if kind!=TYPES['bcs']:continue
        report['scripts_scanned']+=1
        try:
            data,origin=read_resource(ref,'bcs');blocks,total=condition_blocks(data)
            report['trigger_records_scanned']+=total
            if blocks:
                for b in blocks:
                    counts.update(IDS[t['opcode']] for t in b['triggers'])
                    b['response_actions']=[names.get(i,'unknown') for i in b['response_action_ids']]
                report['hits'].append(dict(script=ref,origin=origin,sha256=hashlib.sha256(data).hexdigest(),blocks=blocks))
        except (OSError,ValueError,UnicodeError) as error:report['errors'].append(dict(script=ref,error=str(error)))
    report['stub_occurrences']=dict(counts)
    report['baseline_party_file_scripts']=saved_party_scripts()
    report['verdict']='scanned' if not report['errors'] else 'incomplete'
    report['source_sha256']=digest(Path(__file__))
    write(ROOT/'docs/compatibility/evidence/weapon-trigger-results.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['hits']},indent=2))
    return 0 if report['verdict']=='scanned' else 1

if __name__=='__main__':raise SystemExit(main())
