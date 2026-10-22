"""Explicit preparation only: disposable fresh-NPC color characterization inputs.

No engine/game launches, original installations, profile installation or reload
simulation. Private overrides are experimental inputs, never production fixes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import uuid
import zlib

MAX = 64 * 1024 * 1024
IDENTITY = ('RDXCCASE', 'RDXCNONCE', 'RDXCSTAGE', 'RDXCREADY')
CASES = [('controlled-high', 228, True), ('ordinary-low', 46, True), ('stock-fresh-selector', 228, False)]
NONE = b'NONE\0\0\0\0'


def digest(data): return hashlib.sha256(data).hexdigest()


def block(data, offset, size):
    if type(offset) is not int or type(size) is not int or min(offset, size) < 0 or offset+size > len(data):
        raise ValueError('Field exceeds declared binary bounds')
    # Parsing may read a mutable area under construction. Return an immutable
    # field value consistently, including identities used in sets/dictionaries.
    return bytes(data[offset:offset+size])


def u32(data, at): return struct.unpack('<I', block(data, at, 4))[0]
def u16(data, at): return struct.unpack('<H', block(data, at, 2))[0]


def validate_cre(cre):
    if block(cre, 0, 8) != b'CRE V1.0' or len(cre) < 0x2d4 or len(cre) > MAX or cre[0x33] != 1:
        raise ValueError('Requires bounded CRE V1.0 with v2 effects')
    for off, count, size in [(0x2a0, 0x2a4, 12), (0x2a8, 0x2ac, 16), (0x2b0, 0x2b4, 12),
                             (0x2bc, 0x2c0, 20), (0x2c4, 0x2c8, 264)]:
        n = u32(cre, count)
        if n > 10000: raise ValueError('Excessive CRE table count')
        if n and u32(cre, off) < 0x2d4: raise ValueError('CRE table overlaps header')
        block(cre, u32(cre, off), n*size)
    slots = u32(cre, 0x2b8)
    if slots < 0x2d4: raise ValueError('CRE slots overlap header')
    block(cre, slots, 80)
    if any(x != 0xffff and x >= u32(cre, 0x2c0) for x in struct.unpack('<38H', block(cre, slots, 76))):
        raise ValueError('CRE physical slot aliases missing item')


def party_cre(gam, index):
    if block(gam, 0, 8) != b'GAMEV2.0' or not 0 <= index < u32(gam, 0x24) <= 8:
        raise ValueError('Requires bounded GAMEV2.0 party')
    table = u32(gam, 0x20); count = u32(gam,0x24)
    if table < 0xb4: raise ValueError('Party table overlaps GAME header')
    block(gam, table, count*0x160)
    spans = [(u32(gam,table+i*0x160+4),u32(gam,table+i*0x160+8)) for i in range(count)]
    for i,(start,size) in enumerate(spans):
        if start < table+count*0x160 or size < 0x2d4: raise ValueError('Embedded CRE overlaps GAME/party records')
        block(gam,start,size)
        if any(max(start,other) < min(start+size,other+length) for other,length in spans[:i]):
            raise ValueError('Overlapping party CRE ranges')
    row = table+index*0x160
    cre = block(gam, u32(gam, row+4), u32(gam, row+8)); validate_cre(cre)
    return row, cre


def only_changes(before, after, ranges):
    if len(before) != len(after): raise ValueError('Undeclared length change')
    if any(a != b and not any(lo <= i < hi for lo, hi in ranges) for i, (a, b) in enumerate(zip(before, after))):
        raise ValueError('Undeclared byte modification')


def inert_cre(source, color, identity='RDXCOLOR'):
    validate_cre(source)
    if u32(source, 0x28) != 0x6100 or source[0x272] != 1:
        raise ValueError('Requires reviewed paletted human animation0x6100/race1')
    if type(color) is not int or not 0 <= color <= 255 or not re.fullmatch('[A-Z0-9]{1,32}', identity):
        raise ValueError('Invalid color or actor identity')
    result = bytearray(source); slots = u32(source, 0x2b8)
    struct.pack_into('<Ihh', result, 0x20, 0, 100, 100)
    result[0x30] = color # leather color, IE_COLORS+4
    result[0x248:0x270] = NONE*5
    result[0x270] = 128 # neutral, not an attack target/control
    result[0x280:0x2a0] = identity.encode().ljust(32, b'\0')
    struct.pack_into('<I', result, 0x2c0, 0)
    struct.pack_into('<I', result, 0x2c8, 0)
    result[0x2cc:0x2d4] = NONE
    result[slots:slots+80] = struct.pack('<38HhH', *([0xffff]*38), 1000, 0)
    only_changes(source, result, [(0x20,0x28),(0x30,0x31),(0x248,0x271),(0x280,0x2a0),
                                 (0x2c0,0x2c4),(0x2c8,0x2d4),(slots,slots+80)])
    validate_cre(result)
    return bytes(result)


def sav_records(data):
    if len(data) > MAX or block(data, 0, 8) != b'SAV V1.0': raise ValueError('Invalid/excessive SAV')
    at = 8; records = []; names = set(); total = 0
    while at < len(data):
        start = at; n = u32(data, at); at += 4
        if not 2 <= n <= 65: raise ValueError('Invalid SAV member name length')
        raw = block(data, at, n); at += n
        if raw[-1:] != b'\0' or b'\0' in raw[:-1]: raise ValueError('Invalid SAV member terminator')
        name = raw[:-1].decode('ascii')
        if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_. -]{0,63}', name) or '..' in name or name.casefold() in names:
            raise ValueError('Unsafe/duplicate SAV member')
        names.add(name.casefold()); size, packed = u32(data, at), u32(data, at+4); at += 8
        if not 0 <= size <= MAX or not 0 < packed <= MAX: raise ValueError('Excessive SAV member size')
        total += size
        if total > 8*MAX or len(records) >= 10000: raise ValueError('Excessive SAV aggregate')
        payload = block(data, at, packed); at += packed
        # Ordinary native saves can contain an empty default.tot (zlib stream
        # size 8). Accept declared emptiness only when the complete stream is
        # actually empty, with no truncation, unconsumed input or trailing data.
        if size == 0: inflate(dict(size=0, payload=payload))
        records.append(dict(name=name, size=size, payload=payload, raw=data[start:at]))
    return records


def inflate(record):
    decoder = zlib.decompressobj()
    area = decoder.decompress(record['payload'], record['size']+1)
    if len(area) != record['size'] or not decoder.eof or decoder.unconsumed_tail or decoder.unused_data:
        raise ValueError('Invalid/bomb/trailing compressed area')
    return area


def install_idle(sav, cre):
    """Replace one declared Mephit with an inert low-color placeholder.

    RDXCOLOR itself is NEVER embedded here: it must be freshly created by script.
    """
    validate_cre(cre)
    if block(cre,0x280,32).split(b'\0')[0] != b'RDXIDLE' or cre[0x30] != 46 or cre != inert_cre(cre,46,'RDXIDLE'):
        raise ValueError('Only an inert low-color RDXIDLE placeholder may be embedded')
    records = sav_records(sav); matches = [r for r in records if r['name'].casefold() == 'ar0602.are']
    if len(matches) != 1: raise ValueError('Required area absent/ambiguous')
    original = inflate(matches[0]); area = bytearray(original)
    if block(area, 0, 8) != b'AREAV1.0': raise ValueError('Expected AREAV1.0')
    at, count = u32(area, 0x54), u16(area, 0x58)
    if count > 1000 or at < 0x11c: raise ValueError('Invalid area actor table')
    block(area, at, count*272)
    for i in range(count):
        p = at+i*272
        if not (u32(area,p+40)&1):
            existing = block(area,u32(area,p+136),u32(area,p+140));validate_cre(existing)
            if block(existing,0x280,32).split(b'\0')[0].upper() in {b'RDXCOLOR',b'RDXIDLE'}:
                raise ValueError('Color NPC identity already present')
    rows = [at+i*272 for i in range(count) if struct.unpack('<HH', block(area, at+i*272+32, 4)) == (2573,2461)]
    if len(rows) != 1: raise ValueError('Required Mephit location absent/ambiguous')
    row = rows[0]
    if u32(area, row+40) & 1: raise ValueError('Replacement actor is not embedded')
    validate_cre(block(area, u32(area,row+136), u32(area,row+140)))
    area[row:row+32] = b'RDXIDLE'.ljust(32,b'\0')
    area[row+72:row+128] = NONE*7 # ARE dialog and six script overrides
    struct.pack_into('<II', area, row+136, len(area), len(cre))
    only_changes(original, area, [(row,row+32),(row+72,row+128),(row+136,row+144)])
    area.extend(cre)
    if len(area) > MAX: raise ValueError('Appended area exceeds bound')
    result = bytearray(sav[:8])
    for record in records:
        if record is not matches[0]: result.extend(record['raw']); continue
        name = record['name'].encode()+b'\0'; packed = zlib.compress(area)
        result.extend(struct.pack('<I',len(name))+name+struct.pack('<II',len(area),len(packed))+packed)
    return bytes(result), dict(replaced_position=[2573,2461], placeholder='RDXIDLE', appended_cre_sha256=digest(cre),
                               changed_member='ar0602.are', other_members_byte_identical=True)


def inspect_npc_wire(sav, identity='RDXCOLOR'):
    """Read one persisted NPC color byte; never label it runtime palette state."""
    matches = [r for r in sav_records(sav) if r['name'].casefold() == 'ar0602.are']
    if len(matches)!=1: raise ValueError('Required area absent/ambiguous')
    area=inflate(matches[0])
    if block(area,0,8)!=b'AREAV1.0': raise ValueError('Expected AREAV1.0')
    at,count=u32(area,0x54),u16(area,0x58)
    if count>1000 or at<0x11c: raise ValueError('Invalid area actor table')
    block(area,at,count*272);found=[]
    for i in range(count):
        row=at+i*272
        if u32(area,row+40)&1: continue
        cre=block(area,u32(area,row+136),u32(area,row+140));validate_cre(cre)
        if block(cre,0x280,32).split(b'\0')[0].decode('ascii').casefold()!=identity.casefold(): continue
        found.append(dict(actor_index=i,identity=identity,leather_wire_byte=cre[0x30],
            cre_sha256=digest(cre),position=list(struct.unpack('<HH',block(area,row+32,4))),
            effects=u32(cre,0x2c8),items=u32(cre,0x2c0),scripts=[block(cre,0x248+8*j,8).split(b'\0')[0].decode('ascii') for j in range(5)],
            scope='Serialized CRE byte only; initial/fresh-reloaded runtime palette is not observed here.'))
    if len(found)!=1: raise ValueError('Persisted color NPC absent/ambiguous')
    return found[0]


def parse_table(raw):
    if len(raw) > 1024*1024: raise ValueError('Excessive RANDCOLR')
    lines = []; offset = 0
    for line in raw.splitlines(keepends=True):
        cells = [(m.group().decode('ascii'), offset+m.start(), offset+m.end()) for m in re.finditer(rb'\S+', line)]
        if cells: lines.append(cells)
        offset += len(line)
    if len(lines) < 5 or [x[0] for x in lines[0]] != ['2DA','V1.0'] or len(lines[1]) != 1:
        raise ValueError('Unsupported RANDCOLR header')
    header = [x[0] for x in lines[2]]
    if len(header) != len(set(x.casefold() for x in header)) or len(header) > 256:
        raise ValueError('Duplicate/excessive RANDCOLR columns')
    rows = lines[3:]
    if len(rows) > 10000 or any(len(row) != len(header)+1 for row in rows): raise ValueError('Ragged RANDCOLR')
    if rows[0][0][0] != '0' or len({r[0][0] for r in rows}) != len(rows): raise ValueError('RANDCOLR row identity')
    try: values = [[int(x[0]) for x in r[1:]] for r in rows]
    except ValueError as error: raise ValueError('Non-numeric RANDCOLR') from error
    if any(not 0 <= v <= 255 for row in values for v in row) or len(set(values[0])) != len(header):
        raise ValueError('Invalid RANDCOLR byte/selector')
    leather = [i for i,name in enumerate(header) if name.casefold() == 'leather']
    if len(leather) != 1 or values[0][leather[0]] != 228 or 237 not in values[0]:
        raise ValueError('Required stock Leather228 and selector237 not verified; no random fallback')
    return lines, header, values


def controlled_table(raw):
    lines, header, values = parse_table(raw)
    columns = {values[0].index(228):237, values[0].index(237):46}
    changes = []
    for row in lines[4:]:
        for col,value in columns.items():
            _,lo,hi = row[col+1]; changes.append((lo,hi,str(value).encode()))
    output = bytearray(raw)
    for lo,hi,value in sorted(changes, reverse=True): output[lo:hi] = value
    _, new_header, new_values = parse_table(output)
    if new_header != header or new_values[0] != values[0]: raise ValueError('Selector/header changed')
    for old,new in zip(values[1:],new_values[1:]):
        if any(v != columns.get(i,old[i]) for i,v in enumerate(new)): raise ValueError('Undeclared table change')
    return bytes(output), dict(source_sha256=digest(raw), override_sha256=digest(output),
        leather_selector=228, next_selector=237, controlled_columns={header[i]:dict(selector=values[0][i],output=v) for i,v in columns.items()},
        outcome_rows=len(values)-1, other_columns_preserved=True, fallback_used=False,
        stock_selector_outputs={str(values[0][i]):sorted({row[i] for row in values[1:]}) for i in columns})


def script(api, number, nonce, position):
    q = api.script_query_probe; empty = q.EMPTY; x,y = position
    create = f'7OB\n{empty}OB\nOB\n{empty}OB\nOB\n{empty}OB\n0 {x} {y} 0 0"RDXCOLOR" "" AC\n'
    source = 'SC\n'+q.response(q.trigger(0x400f,0,'GLOBALRDXCSTAGE'),[
        q.action(30,number,'GLOBALRDXCCASE'),q.action(30,nonce,'GLOBALRDXCNONCE'),
        q.action(30,1,'GLOBALRDXCSTAGE'),create])
    actor = '0 0 0 0 0 0 0 0 0 0 0 0 "rdxcolor"'
    source += q.response(q.trigger(0x400f,1,'GLOBALRDXCSTAGE')+q.trigger(0x401c,obj=actor),[
        q.action(30,1,'GLOBALRDXCREADY'),q.action(30,2,'GLOBALRDXCSTAGE')])
    return (source+'SC\n').encode('ascii')


def manifest(folder):
    entries = list(Path(folder).iterdir())
    if any(not p.is_file() or p.is_symlink() for p in entries): raise ValueError('Flat ordinary save files required')
    return {p.name:dict(bytes=p.stat().st_size,sha256=digest(p.read_bytes())) for p in sorted(entries)}


def prepare(project, source_save, results):
    # Deferred imports: importing this module/tests never reads the game or prepares fixtures.
    from weapon_oracle_fixtures import load_api
    project, source_save, results = project.resolve(), source_save.resolve(), results.resolve()
    private_results = project/'phase1-local/results'
    if results != private_results and not results.is_relative_to(private_results):
        raise ValueError('Results must stay inside the project private phase1-local/results root')
    if source_save == results or source_save in results.parents: raise ValueError('Results must be outside source save')
    before = manifest(source_save)
    expected = {'baldur.bmp','baldur.gam','baldur.sav','portrt0.bmp','portrt1.bmp','save_000000033-gemrb.cloud.meta'}
    if {n.casefold() for n in before} != expected or len(before) != 6: raise ValueError('Exact reviewed six-file vanilla save required')
    api = load_api(project)
    member = lambda ext: next(source_save/n for n in before if n.casefold() == 'baldur.'+ext)
    gam = member('gam').read_bytes(); row, original_cre = party_cre(gam,0)
    if u32(gam,0x24) != 2: raise ValueError('Requires reviewed two-party input')
    if api.equipped_defenses.embedded(gam,0)[1] != original_cre: raise ValueError('Independent party parser disagrees')
    if set(IDENTITY) & {n.upper() for n in api.legacy_oracle.read_wire(member('gam'))['globals']}:
        raise ValueError('Color fixture globals already present')
    raw_table, origin = api.probe_ui_resources.read_resource('randcolr','2da')
    modified, table_metadata = controlled_table(raw_table)
    api.probe_ui_resources.TYPES['ids'] = 0x3f0
    api.probe_ui_resources.TYPES['cre'] = 0x3f1
    collision,_ = api.probe_ui_resources.read_resource('rdxcolor','cre')
    if collision is not None: raise ValueError('RDXCOLOR resource already exists in protected game')
    ids, ids_origin = api.probe_ui_resources.read_resource('action','ids')
    if not re.search(rb'(?im)^\s*7\s+CreateCreature\(S:NewObject\*,P:Location\*,I:Face\*DIR\)',ids):
        raise ValueError('Shipped CreateCreature action7 signature differs')
    px,py = struct.unpack('<HH',block(gam,row+0x20,4)); position=(px+40,py)
    if not all(0 <= v <= 65535 for v in position): raise ValueError('Spawn point exceeds coordinate bounds')
    nonce = int(uuid.uuid4().hex[:8],16)&0x7fffffff or 1
    run = results/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-color-fixtures-'+uuid.uuid4().hex[:8]); run.mkdir(parents=True,exist_ok=False)
    report = dict(schema='bg-redux-phase1-color-preparation/1',directory=str(run),nonce=nonce,
        phase='preparing',executed=False,original_behavior_observed=False,source_save=str(source_save),source_files=before,
        generator_sha256=digest(Path(__file__).read_bytes()),randcolr_origin=origin,action_ids_origin=ids_origin,
        action_ids_sha256=digest(ids),table_control=table_metadata,
        phase0_imports={name:dict(path=m.__file__,sha256=digest(Path(m.__file__).read_bytes())) for name,m in vars(api).items()},cases=[])
    def save_report(): (run/'preparation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    save_report()
    try:
        idle = inert_cre(original_cre,46,'RDXIDLE')
        changed_sav, area_guard = install_idle(member('sav').read_bytes(), idle)
        for number,(identity,color,controlled) in enumerate(CASES,1):
            output=run/identity; fixture=output/'input'; shutil.copytree(source_save,fixture); override=output/'override';override.mkdir()
            npc = inert_cre(original_cre,color)
            data=bytearray(gam); ranges=[]; resref=f'C{nonce & 0xfffff:05X}{number:02d}'
            for index in range(2):
                r,_=party_cre(gam,index); at=u32(gam,r+4)+0x248
                data[at:at+40]=(resref.encode() if index==0 else NONE)+NONE*4; ranges.append((at,at+40))
            only_changes(gam,data,ranges)
            (fixture/member('gam').name).write_bytes(data);(fixture/member('sav').name).write_bytes(changed_sav)
            (override/'RDXCOLOR.cre').write_bytes(npc);(override/'RANDCOLR.2da').write_bytes(modified if controlled else raw_table)
            (override/(resref+'.bcs')).write_bytes(script(api,number,nonce,position))
            final=manifest(fixture)
            if set(final)!=set(before) or any(final[n]!=before[n] for n in before if n.casefold() not in {'baldur.gam','baldur.sav'}):
                raise ValueError('Undeclared save file change')
            report['cases'].append(dict(id=identity,number=number,nonce=nonce,fixture=str(fixture),fixture_files=final,
                override=str(override),override_files=manifest(override),resource='RDXCOLOR',npc_script_name='RDXCOLOR',
                raw_leather_color=color,controlled_randcolr=controlled,spawn_position=position,script=resref,
                npc_guard=dict(animation=0x6100,race=1,allegiance=128,hp=100,scripts='NONE',dialog='NONE',effects=0,items=0),
                guard_scope='Declared serialized CRE input; no runtime palette/derived stat result is inferred.',
                area_guard=area_guard,expected_ready_globals=dict(RDXCCASE=number,RDXCNONCE=nonce,RDXCSTAGE=2,RDXCREADY=1),
                fresh_creation_required=True,save_or_reload_executed=False,observed_colors=None))
            save_report()
        if manifest(source_save)!=before: raise ValueError('Protected source save changed')
        report.update(phase='prepared-not-executed',source_unchanged=True);save_report()
    except Exception as error:
        report.update(phase='preparation-failed',error=str(error));save_report();raise
    finally:
        try:
            report['source_after_files']=manifest(source_save)
            report['source_unchanged']=report['source_after_files']==before
        except (OSError,ValueError) as error:
            report['source_unchanged']=False
            report['source_inventory_error']=str(error)
        if not report['source_unchanged']:
            report.update(phase='preparation-failed',source_preservation_error='Protected source save changed')
        save_report()
    if not report['source_unchanged']: raise ValueError('Protected source save changed')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare'])
    for name in ('project-root','source-save','results-root'): parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args(argv)
    print(prepare(args.project_root,args.source_save,args.results_root)['directory'])


if __name__=='__main__': main()
