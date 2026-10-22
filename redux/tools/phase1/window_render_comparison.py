"""Validate canonical RGBA synthetic-window captures without launching a runtime."""
import argparse
import hashlib
import json
from pathlib import Path


def compare(folder):
    folder=Path(folder);fixture=json.loads((folder/'fixture.json').read_text(encoding='utf-8'))
    if (fixture.get('schema')!='bg-redux-window-render-fixture/1' or fixture.get('completed')is not True
        or fixture.get('game_mutations_requested')is not False or fixture.get('width')!=160
        or fixture.get('height')!=120 or fixture.get('rgba_bytes_per_capture')!=76800):raise ValueError('Wrong/incomplete fixture')
    expected={'bg%d-alpha%d-scale%d'%(a,b,s) for a in (202,255)for b in (0,1)for s in (75,100,125)}
    if len(fixture['cases'])!=12 or {c['id']for c in fixture['cases']}!=expected:raise ValueError('Alpha/scale coverage differs')
    rows=[]
    for case in fixture['cases']:
        comparisons=[];path=folder/case['id']
        def read(name):
            data=(path/name).read_bytes()
            if len(data)!=76800:raise ValueError('RGBA extent differs')
            return data
        reference=read('fresh-final.rgba')
        names=['removed-final.rgba','dirty-0.rgba','dirty-1.rgba','dirty-2.rgba','partial-dirty.rgba','full-after-partial.rgba']
        if case['reference']!='fresh-final.rgba' or case['must_equal_reference']!=names or case['old_child_must_differ']!='old.rgba':raise ValueError('Comparison coverage differs')
        for name in names:
            data=read(name);diff=[i for i in range(0,len(data),4)if data[i:i+4]!=reference[i:i+4]]
            comparisons.append(dict(file=name,equal=not diff,different_rgba_pixels=len(diff),
                different_alpha_pixels=sum(data[i+3]!=reference[i+3]for i in range(0,len(data),4)),
                sha256=hashlib.sha256(data).hexdigest()))
        old_diff=read('old.rgba')!=reference
        rows.append(dict(id=case['id'],old_child_differs=old_diff,comparisons=comparisons,
            passed=old_diff and all(c['equal']for c in comparisons),reference_sha256=hashlib.sha256(reference).hexdigest()))
    return dict(schema='bg-redux-window-render-comparison/1',passed=all(c['passed']for c in rows),
        cases=rows,note='Unmanaged synthetic Window controls only; no GameControl world rendering, nonzero-origin scaled copy, or gameplay acceptance claim.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=compare(args.capture)
    with args.output.open('x',encoding='utf-8')as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(args.output,result['passed'])
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
