"""Inspect permanent equip records and contrast two reviewed item effect blocks.

The controlled runs substitute an item block into IMMCLOUD's fixture carrier;
they do not establish the natural original-game behavior of those items.
"""
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid
from collections import Counter

from harness import ROOT,LOCAL,BUILD,digest
from probe_ui_resources import resources,read_resource,TYPES
from effect_cycle import u16,u32,block,run_stage
from save_harness import manifest,write

def item_effects(data):
    if data[:8] not in (b'ITM V1  ',b'ITM V1.1',b'ITM V2.0'):raise ValueError('Unsupported ITM header')
    at,index,count=u32(data,0x6a),u16(data,0x6e),u16(data,0x70)
    block(data,at+index*48,count*48)
    return [dict(index=i,opcode=u16(data,at+(index+i)*48),target=data[at+(index+i)*48+2],
        parameters=[u32(data,at+(index+i)*48+4),u32(data,at+(index+i)*48+8)],
        timing=data[at+(index+i)*48+12]) for i in range(count)]

def main():
    output=LOCAL/'results'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-equip-exposure-'+uuid.uuid4().hex[:8]);output.mkdir()
    report=dict(schema='bg-redux-equip-exposure/1',directory=str(output),items=[],controls={},errors=[],assertions=[])
    report['runner_sha256']=digest(Path(__file__))
    try:
        receipt=json.loads((LOCAL/'gui-probe/build.json').read_text())
        if receipt['binary_sha256']!=digest(LOCAL/'gui-probe/Redux_gui_probe.exe') or receipt['engine_dll_sha256']!=digest(BUILD/'gemrb/libgemrb_core.dll'):raise ValueError('Native provenance drift')
        for p,sha in receipt['sources'].items():
            if digest(ROOT/p)!=sha:raise ValueError('Native source drift')
        report['build']=receipt
        TYPES['itm']=0x3ed
        ids={}
        for line in (ROOT/'gemrb/gemrb/unhardcoded/bg2ee/effects.ids').read_text().splitlines():
            parts=line.split()
            if len(parts)>=2 and parts[0].startswith('0x'):ids[int(parts[0],16)]=parts[1]
        count=0;opcodes=Counter();all_equip_count=0
        for ref,kind in sorted(resources):
            if kind!=0x3ed:continue
            count+=1
            data,origin=read_resource(ref,'itm')
            try:rows=item_effects(data)
            except ValueError as error:
                report['errors'].append(dict(item=ref,error=str(error)));continue
            all_equip_count+=len(rows)
            permanent=[dict(row,name=ids.get(row['opcode'],'unmapped')) for row in rows if row['timing']==1]
            if permanent:
                report['items'].append(dict(item=ref,origin=origin,sha256=hashlib.sha256(data).hexdigest(),
                    equip_effect_count=len(rows),permanent_effects=permanent))
                opcodes.update(row['opcode'] for row in permanent)
        report['scan']=dict(key_item_resources=count,total_equipping_effects=all_equip_count,
            items_with_permanent_equip_effects=len(report['items']),permanent_equip_effects=sum(opcodes.values()),
            opcodes=[dict(opcode=k,name=ids.get(k,'unmapped'),records=v) for k,v in opcodes.most_common()],
            scope='KEY-enumerated resources with fixture loose override/lang lookup; not a full GemRB provider traversal, mod corpus or count of defects.')
        fixture=LOCAL/'fixtures/original-bg2ee-20261020/GemRB';before=manifest(fixture)
        pinned=json.loads((ROOT/'docs/compatibility/evidence/vanilla-save-fixture.json').read_text())
        if before!=pinned['files']:raise ValueError('Fixture provenance drift')
        for item in ['ring09','magiweb']:
            data,origin=read_resource(item,'itm');mod=output/(item+'-carrier-mod');mod.mkdir()
            # Keep the CRE/carrier identity fixed; only the item resource bytes
            # change in this test's private provider. SourceRef remains IMMCLOUD.
            (mod/'immcloud.itm').write_bytes(data)
            current=fixture;stages=[]
            for cycle in range(2):
                result,current=run_stage(output,f'{item}-carrier-{cycle}',current,mod);stages.append(result)
                print(item,cycle,'wire in',result['input_wire']['total'],'runtime',result['entry']['effects']['total'],'wire out',result['output_wire']['total'],flush=True)
            report['controls'][item]=dict(source_item_sha256=hashlib.sha256(data).hexdigest(),source_origin=origin,
                provider_alias='IMMCLOUD.ITM',source_effects=item_effects(data),stages=stages,
                limitation='Synthetic fixed carrier, not a naturally equipped item test or original BG2EE runtime observation.')
        def check(name,ok):report['assertions'].append(dict(name=name,passed=bool(ok)))
        check('all-item-headers-parsed',not report['errors'])
        check('ring09-one-shot-cures-do-not-accumulate',all(s['output_wire']['total']==s['input_wire']['total'] for s in report['controls']['ring09']['stages']))
        check('magiweb-six-records-accumulate',all(s['output_wire']['total']==s['input_wire']['total']+6 for s in report['controls']['magiweb']['stages']))
        check('refresh-does-not-grow-candidates',all(s['entry']['effects']==s['refresh1']['effects']==s['refresh2']['effects'] for c in report['controls'].values() for s in c['stages']))
        check('inputs-unchanged',before==manifest(fixture) and all(s['input_unchanged'] for c in report['controls'].values() for s in c['stages']))
        report['verdict']='characterized' if all(c['passed'] for c in report['assertions']) else 'differences'
    except (OSError,ValueError,KeyError) as error:
        report['verdict']='failed';report['error']=str(error)
    report['engine_status']=subprocess.check_output(['git','-C',str(ROOT/'gemrb'),'status','--porcelain'],text=True)
    report['tool_sources']={str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),ROOT/'tools/phase0/effect_cycle.py',ROOT/'tools/phase0/probe_ui_resources.py']}
    write(output/'result.json',report)
    write(ROOT/'docs/compatibility/evidence/equip-exposure-results.json',report)
    print(json.dumps({k:report[k] for k in ['directory','verdict','scan','assertions','error'] if k in report},indent=2))
    return 0 if report['verdict']=='characterized' and not report['engine_status'].strip() else 1

if __name__=='__main__':raise SystemExit(main())
