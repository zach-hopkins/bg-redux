"""Join native UI/font observations to CHU and EE menu metadata.

No extracted game assets or complete UI text are published in the report.
"""
import argparse
import json
from pathlib import Path
import struct

from harness import ROOT, LOCAL, digest
from probe_ui_resources import read_resource

def font_names(data):
    tables={}
    for i in range(struct.unpack_from('>H',data,4)[0]):
        tag,_,offset,size=struct.unpack_from('>4sIII',data,12+i*16)
        tables[tag]=(offset,size)
    offset,_=tables[b'name']
    _,count,start=struct.unpack_from('>3H',data,offset)
    names=set()
    for i in range(count):
        platform,encoding,language,nid,length,relative=struct.unpack_from('>6H',data,offset+6+i*12)
        if nid in (1,2) and (language in (0,0x409) or platform==1):
            value=data[offset+start+relative:offset+start+relative+length]
            names.add((nid,value.decode('utf-16-be' if platform in (0,3) else 'latin1',errors='replace')))
    return [dict(name_id=nid,value=name) for nid,name in sorted(names)]

def inspect(directory):
    result=json.loads((directory/'result.json').read_text(encoding='utf-8'))
    stage=directory/'gui-save'
    fonts=json.loads((stage/'fonts.json').read_text(encoding='utf-8'))['fonts']
    metadata=json.loads((ROOT/'docs/compatibility/evidence/ui-resource-probe.json').read_text(encoding='utf-8'))
    windows=[]
    for pack,screen in [('guiinv','01-inventory'),('guirec','02-record')]:
        ui=json.loads((stage/(screen+'.ui.json')).read_text(encoding='utf-8'))
        controls=[c for c in ui['controls'] if c['pack'].lower()==pack and c['window']==2]
        labels=[c for c in controls if c['type']==6]
        chu=next(w for w in metadata['windows'] if w['resource']==pack and w['window']==2)
        overview=[c for c in controls if c['type']==5]
        windows.append(dict(resource=pack,chu_label_count=len(chu['labels']),runtime_label_count=len(labels),
            nonempty_runtime_labels=sum(bool(c['text']) for c in labels),
            empty_label_ids=[hex(c['id']) for c in labels if not c['text']],
            invisible_label_ids=[hex(c['id']) for c in labels if not c['visible']],
            textareas=[dict(id=c['id'],text_characters=len(c['text'])) for c in overview],
            screenshot_sha256=digest(stage/(screen+'.bmp')),ui_sha256=digest(stage/(screen+'.ui.json'))))
    return dict(run_id=result['run_id'],font_mode=result['font_mode'],execution_verdict=result.get('execution_verdict'),
                assertion_verdict=result.get('assertion_verdict'),persistence=result.get('persistence'),
                fonts=fonts,windows=windows)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs',nargs='+',type=Path)
    args=parser.parse_args()
    report=dict(schema='bg-redux-presentation-evidence/1',runs=[inspect(p) for p in args.runs],ttf_assets=[])
    for name in ['normal','floattxt','realms','stonebig','stonesml','toolfont','tooltip']:
        data,origin=read_resource(name,'ttf')
        if data:
            import hashlib
            report['ttf_assets'].append(dict(name=name,origin=origin,sha256=hashlib.sha256(data).hexdigest(),names=font_names(data)))
    menu,origin=read_resource('ui','menu')
    import hashlib
    report['ee_menu']=dict(origin=origin,sha256=hashlib.sha256(menu).hexdigest(),lines=len(menu.splitlines()),references={})
    lines=menu.decode('utf-8').splitlines()
    for marker in ['mosaic "INVSTATS"','mosaic\t"GUIREC2"','characters[id].AC.details','characters[id].HP.details',
                   'getInventoryTHAC0()',"characters[id].damage.details"]:
        report['ee_menu']['references'][marker]=[i+1 for i,line in enumerate(lines) if marker in line]
    report['interpretation_limits']=[
        'QueryText and visibility establish control content, not rendered pixel correctness.',
        'TTF asset hashes/names are KEY/BIFF metadata; native runtime_type establishes TTF versus BAM selection, not a complete provider trace.',
        'Blank legacy CHU placeholders and Lua-assembled EE menu panels must be distinguished from missing TLK entries.',
        'BAM and 18px TTF are private configuration experiments, not an engine fix or modern UI implementation.'
    ]
    output=ROOT/'docs/compatibility/evidence/gui-presentation-results.json'
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(output)

if __name__=='__main__': main()
