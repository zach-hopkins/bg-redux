"""Compare held dialogue RGB captures; never certify gameplay or alpha fidelity."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bitmap(path):
    raw=path.read_bytes()
    if len(raw)<54 or raw[:2]!=b'BM':raise ValueError('BMP header required')
    offset=struct.unpack_from('<I',raw,10)[0]
    width,height=struct.unpack_from('<ii',raw,18)
    planes,bits,compression=struct.unpack_from('<HHI',raw,26)
    if planes!=1 or bits!=24 or compression!=0 or not 0<width<=4096 or not 0<height<=4096 or offset<54:
        raise ValueError('Bounded bottom-up uncompressed RGB24 BMP required')
    stride=(width*3+3)&~3
    if offset+stride*height!=len(raw):raise ValueError('BMP extent differs')
    pixels=[raw[offset+(height-1-y)*stride+x*3:offset+(height-1-y)*stride+x*3+3]
            for y in range(height) for x in range(width)]
    return width,height,pixels,digest(raw)


def compare(folder):
    folder=Path(folder)
    width,height,reference,_=bitmap(folder/'render-7-clear.bmp')
    x,y,w,h=80,12,690,100
    if x+w>width or y+h>height:raise ValueError('Text crop outside panel')
    crop=[yy*width+xx for yy in range(y,y+h) for xx in range(x,x+w)]
    rows=[];semantics=set()
    for step in range(11):
        method='ordinary' if step<4 else 'dirty' if step<7 else 'clear' if step==7 else 'after-clear-dirty'
        name='render-'+str(step)+'-'+method
        ww,hh,pixels,pin=bitmap(folder/(name+'.bmp'))
        if (width,height)!=(ww,hh):raise ValueError('Panel geometry changed')
        text=json.loads((folder/(name+'.text.json')).read_text(encoding='utf-8'))
        if text['method']!=method or text['acceptance_run']is not False:raise ValueError('Diagnostic provenance differs')
        semantic=digest(text['message_text'].encode('utf-8'));semantics.add(semantic)
        differences=[max(abs(a-b) for a,b in zip(pixels[i],reference[i])) for i in crop]
        rows.append(dict(step=step,file=name+'.bmp',sha256=pin,method=method,
            different_text_crop_pixels=sum(d>0 for d in differences),max_channel_difference=max(differences),
            channel_difference_sum=sum(differences),semantic_sha256=semantic,window_flags=text['window_flags']))
    if len(semantics)!=1:raise ValueError('Held transcript changed')
    return dict(schema='bg-redux-dialogue-render-comparison/1',reference='render-7-clear.bmp',
        crop=dict(x=x,y=y,w=w,h=h),rows=rows,
        ordinary_equals_cleared=all(r['different_text_crop_pixels']==0 for r in rows[:4]),
        repeated_dirty_equals_cleared=all(r['different_text_crop_pixels']==0 for r in rows[4:]),
        note='Diagnostic intervention, not gameplay acceptance. RGB text crop excludes portrait and scrollbar. BMP does not measure alpha.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=compare(args.capture)
    with args.output.open('x',encoding='utf-8')as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(args.output)


if __name__=='__main__':main()
