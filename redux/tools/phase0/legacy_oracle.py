"""Independent, bounded GAMEV2.0 / embedded CRE V1.0 wire-field checks.

Layout references: IESDP gam_v2.0.htm and cre_v1.htm; compare selected fields,
not a claim of a complete original-runtime oracle. No engine code is imported.
"""
from pathlib import Path
import struct
from collections import Counter


def read_wire(path):
    data = Path(path).read_bytes()
    def block(offset,size):
        if offset < 0 or offset+size > len(data): raise ValueError('Wire field outside GAM bounds')
        return data[offset:offset+size]
    def u32(offset): return struct.unpack('<I',block(offset,4))[0]
    def text(raw): return raw.split(b'\0')[0].decode('ascii')
    if block(0,8) != b'GAMEV2.0': raise ValueError('Oracle supports GAMEV2.0 only')
    result=dict(game_time_seconds=u32(8),gold=u32(0x18),reputation=u32(0x54),party=[],stored_npcs=[],globals={})
    for group,where in [('party',0x20),('stored_npcs',0x30)]:
        offset,count=u32(where),u32(where+4)
        if count>1000: raise ValueError('Excessive actor count')
        block(offset,count*0x160)
        for index in range(count):
            actor_at=offset+index*0x160
            cre_offset,cre_size=u32(actor_at+4),u32(actor_at+8)
            cre=block(cre_offset,cre_size)
            if cre[:8]!=b'CRE V1.0': raise ValueError('Oracle requires embedded CRE V1.0')
            def cb(at,size):
                if at<0 or at+size>len(cre): raise ValueError('Wire field outside CRE bounds')
                return cre[at:at+size]
            def cu32(at): return struct.unpack('<I',cb(at,4))[0]
            item_offset,item_count=cu32(0x2bc),cu32(0x2c0)
            cb(item_offset,item_count*20)
            items=[]
            for item in range(item_count):
                row=cb(item_offset+item*20,20)
                expired,a,b,c,flags=struct.unpack_from('<4HI',row,8)
                items.append(dict(resref=text(row[:8]).upper(),expired=expired,usages=[a,b,c],flags=flags))
            stats={'hp':struct.unpack('<h',cb(0x24,2))[0], 'max_hp':struct.unpack('<H',cb(0x26,2))[0],
                   'xp':cu32(0x18),'class':cb(0x273,1)[0],'race':cb(0x272,1)[0],'sex':cb(0x275,1)[0],
                   'str':cb(0x238,1)[0],'int':cb(0x23a,1)[0],'wis':cb(0x23b,1)[0],
                   'dex':cb(0x23c,1)[0],'con':cb(0x23d,1)[0],'chr':cb(0x23e,1)[0]}
            result[group].append(dict(area=text(block(actor_at+0x18,8)).upper(),
                position=list(struct.unpack('<HH',block(actor_at+0x20,4))),stats=stats,items=items))
    offset,count=u32(0x38),u32(0x3c)
    block(offset,count*84)
    for index in range(count):
        at=offset+index*84
        result['globals'][text(block(at,32)).upper()]=u32(at+40)
    return result


def compare_wire(wire,state):
    checks=[]
    def check(field,expected,actual):
        checks.append(dict(field=field,expected=expected,actual=actual,passed=expected==actual))
    # GemRB stores game time in 15-Hz logical ticks; GAM stores seconds.
    check('game_time_ticks',wire['game_time_seconds']*15,state['game_time'])
    for key in ('gold','reputation','globals'):
        check(key,wire[key],state[key])
    stats={'hp':0,'max_hp':1,'xp':44,'class':232,'race':231,'sex':35,'str':36,'int':38,'wis':39,'dex':40,'con':41,'chr':42}
    def key(item): return (item['resref'].upper(),item['expired'],tuple(item['usages']),item['flags'])
    for group in ('party','stored_npcs'):
        check(group+'.count',len(wire[group]),len(state[group]))
        for index,(original,native) in enumerate(zip(wire[group],state[group])):
            prefix=f'{group}/{index}'
            check(prefix+'/area',original['area'],native['area'].upper())
            check(prefix+'/position',original['position'],native['position'])
            for name,stat in stats.items(): check(prefix+'/'+name,original['stats'][name],native['base_stats'][stat])
            # Fists are an engine-created virtual inventory entry, not a lost or
            # duplicated source item. Compare source records with real slots.
            actual=[item for item in native['inventory']['items'] if item['slot']!=native['inventory']['fist_slot']]
            expected=Counter(key(item) for item in original['items']); observed=Counter(key(item) for item in actual)
            check(prefix+'/item_records',sorted(expected.items()),sorted(observed.items()))
    return dict(schema='bg-redux-wire-oracle/1',checks=len(checks),passed=sum(c['passed'] for c in checks),
                differences=[c for c in checks if not c['passed']], scope='Selected wire fields only; HP values may be recalculated by actor/equipment initialization. Differences require interpretation, not automatic normalization.')
