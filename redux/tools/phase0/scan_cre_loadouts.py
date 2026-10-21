"""Locate packaged CRE V1.0 item references; presence is not runtime equipping."""
import datetime
import hashlib
import json
from collections import Counter
from pathlib import Path

from harness import ROOT,digest
from probe_ui_resources import resources,read_resource,TYPES
from effect_cycle import block,u16,u32,text
from save_harness import write

def inventory(data):
    if data[:8]!=b'CRE V1.0':raise ValueError('Unsupported CRE signature')
    block(data,0,0x2d4)
    slotat,itemat,count=u32(data,0x2b8),u32(data,0x2bc),u32(data,0x2c0)
    if count>1000:raise ValueError('Excessive inventory count')
    block(data,itemat,count*20);block(data,slotat,80)
    slots=[u16(data,slotat+i*2) for i in range(38)]
    if any(i!=0xffff and i>=count for i in slots):raise ValueError('Slot refers past item table')
    return [dict(item=text(block(data,itemat+i*20,8)).lower(),entry=i,
        file_slots=[slot for slot,index in enumerate(slots) if index==i],flags=u32(data,itemat+i*20+16)) for i in range(count)]

def main():
    exposure=ROOT/'docs/compatibility/evidence/equip-exposure-results.json'
    candidates={r['item'] for r in json.loads(exposure.read_text(encoding='utf-8'))['items']}
    TYPES['cre']=0x3f1
    report=dict(schema='bg-redux-cre-loadout-scan/1',captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scope=__doc__,versions={},cre_resources_scanned=0,cre_v1_parsed=0,matches=[],errors=[],
        candidate_item_count=len(candidates),candidate_evidence_sha256=digest(exposure))
    versions=Counter()
    for ref,kind in sorted(resources):
        if kind!=TYPES['cre']:continue
        report['cre_resources_scanned']+=1
        try:
            data,origin=read_resource(ref,'cre');versions[data[:8].decode('ascii')]+=1
            if data[:8]!=b'CRE V1.0':continue
            rows=inventory(data);report['cre_v1_parsed']+=1
            matched=[r for r in rows if r['item'] in candidates]
            if matched:report['matches'].append(dict(cre=ref,origin=origin,sha256=hashlib.sha256(data).hexdigest(),items=matched))
        except (OSError,ValueError,KeyError,UnicodeError) as error:
            report['errors'].append(dict(cre=ref,error=str(error)))
    report['versions']=dict(versions)
    report['candidate_cre_counts']={item:sum(any(row['item']==item for row in hit['items']) for hit in report['matches']) for item in sorted(candidates)}
    report['verdict']='scanned' if not report['errors'] else 'incomplete'
    report['source_sha256']=digest(Path(__file__))
    write(ROOT/'docs/compatibility/evidence/cre-loadout-results.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['matches']},indent=2))
    return 0 if report['verdict']=='scanned' else 1

if __name__=='__main__':raise SystemExit(main())
