"""Validate canonical RGBA synthetic-window captures without launching a runtime."""
import argparse
import hashlib
import json
from pathlib import Path
from dialogue_render_comparison import bitmap


def compare(folder):
    folder=Path(folder);fixture=json.loads((folder/'fixture.json').read_text(encoding='utf-8'))
    if fixture.get('schema')in ('bg-redux-window-render-fixture/2','bg-redux-window-render-fixture/3'):return compare_v2(folder,fixture)
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
        measured_channels='RGB',alpha_measured=False,
        cases=rows,note='RGBA files originate from an RGB24 screenshot; their alpha byte is synthesized, not measured. Unmanaged synthetic Window controls only; no GameControl world rendering, nonzero-origin scaled copy, or gameplay acceptance claim.')


def compare_v2(folder,fixture):
    version3=fixture['schema']=='bg-redux-window-render-fixture/3'
    if version3 and (fixture.get('background_probe')!=[6,6] or fixture.get('opacity_expectation_scope')!='LAB-pinned-SDL20-shared-DISPLAY-DISPLAY_ALPHA-native-format'):
        raise ValueError('Wrong backend opacity scope')
    if (fixture.get('completed')is not True or fixture.get('game_mutations_requested')is not False
        or (fixture.get('width'),fixture.get('height'),fixture.get('rgb_bytes_per_capture'))!=(160,120,57600)
        or fixture.get('direct_alpha_readback')is not False
        or fixture.get('opacity_observation')!='paired-opaque-black-white-composition'):raise ValueError('Wrong/incomplete RGB fixture')
    expected={'bg%d-alpha%d-scale%d'%(a,b,s) for a in (202,255)for b in (0,1)for s in (75,100,125)}
    if len(fixture['cases'])!=12 or {c['id']for c in fixture['cases']}!=expected:raise ValueError('Alpha/scale coverage differs')
    rows=[]
    stems=['removed-final','dirty-0','dirty-1','dirty-2','partial-dirty','full-after-partial']
    suffixes=['.rgb','.black.rgb','.white.rgb']
    for case in fixture['cases']:
        path=folder/case['id'];comparisons=[];probes=[]
        alpha=case['background_alpha'];channel=case['window_alpha_channel'];scale=case['scale_percent']
        if alpha not in (202,255) or type(channel)is not bool or scale not in (75,100,125) or case['id']!='bg%d-alpha%d-scale%d'%(alpha,channel,scale):raise ValueError('Case identity differs')
        transmission=255-alpha if version3 or channel else 0
        if (case['reference']!='fresh-final.rgb' or case['comparison_suffixes']!=suffixes
            or case['must_equal_reference_stems']!=stems or case['expected_background_probe_transmission']!=transmission
            or case['transmission_rounding_tolerance']!=1 or case.get('partial_clip')!=[8,20,60,50]
            or case.get('outside_sentinel')!=[130,90,15,15]):raise ValueError('Comparison coverage differs')
        checked={}
        def read(name):
            if name in checked:return checked[name]
            data=(path/name).read_bytes()
            if len(data)!=57600:raise ValueError('RGB extent differs')
            ww,hh,pixels,_=bitmap((path/name).with_suffix('.bmp'))
            if (ww,hh)!=(160,120) or b''.join(bytes(p[::-1])for p in pixels)!=data:raise ValueError('BMP pixels differ from RGB')
            checked[name]=data
            return data
        for suffix in suffixes:
            reference=read('fresh-final'+suffix)
            for stem in stems:
                data=read(stem+suffix)
                diff=sum(data[i:i+3]!=reference[i:i+3]for i in range(0,57600,3))
                comparisons.append(dict(file=stem+suffix,equal=diff==0,different_rgb_pixels=diff,sha256=hashlib.sha256(data).hexdigest()))
        for stem in ['old','fresh-final']+stems:
            probe=json.loads((path/(stem+'.composite.json')).read_text(encoding='utf-8'))
            coordinate=6 if version3 else 80
            if probe['probe']!=[coordinate,coordinate] or probe['direct_alpha_readback']is not False:raise ValueError('Wrong opacity probe')
            pixel=(coordinate*160+coordinate)*3
            black=list(read(stem+'.black.rgb')[pixel:pixel+3]);white=list(read(stem+'.white.rgb')[pixel:pixel+3])
            actual=[w-b for w,b in zip(white,black)]
            if probe['black_rgb']!=black or probe['white_rgb']!=white or probe['transmission_rgb']!=actual:raise ValueError('Opacity probe differs from pixels')
            probes.append(dict(capture=stem,transmission_rgb=actual,expected=transmission,passed=all(abs(v-transmission)<=1 for v in actual)))
        old_diff=read('old.rgb')!=read('fresh-final.rgb')
        rows.append(dict(id=case['id'],old_child_differs=old_diff,comparisons=comparisons,opacity_probes=probes,
            passed=old_diff and all(c['equal']for c in comparisons)and all(p['passed']for p in probes)))
    return dict(schema='bg-redux-window-render-comparison/'+('3'if version3 else '2'),passed=all(c['passed']for c in rows),cases=rows,
        measured_channels='RGB',direct_alpha_readback=False,opacity_observation='paired-opaque-black-white-composition',
        note='Unmanaged synthetic Window controls only; no GameControl world rendering, nonzero-origin scaled copy, or gameplay acceptance claim.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=compare(args.capture)
    with args.output.open('x',encoding='utf-8')as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(args.output,result['passed'])
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
