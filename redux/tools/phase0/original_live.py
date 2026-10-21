"""Disposable original-game combat feedback channel; no engine hooks or edits.

Preparation appends nonce-tagged TLK strings and instruments private stock AI
tails. Feedback entry/return markers are not exact action/target memory samples.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import shutil
import struct
import uuid

from harness import ROOT, LOCAL, digest
from save_harness import manifest, write
from ai_fallback import CASES, construct_ai
from scan_weapon_triggers import BLOCK, TRIGGER
from probe_ui_resources import read_resource, TYPES
from script_query_probe import trigger, action, response, EMPTY

MYSELF = '0 0 0 0 0 0 0 1 0 0 0 0 ""'


def append_tlk(data, strings):
    if len(data) < 18: raise ValueError('Truncated TLK header')
    if data[:8] != b'TLK V1  ': raise ValueError('Unsupported TLK')
    count, offset = struct.unpack_from('<II', data, 10)
    if offset != 18 + count * 26: raise ValueError('Unexpected TLK table layout')
    if len(data) < offset: raise ValueError('Truncated TLK')
    for index in range(count):
        start, size = struct.unpack_from('<II', data, 18+index*26+18)
        if start > len(data)-offset or size > len(data)-offset-start:
            raise ValueError('Existing TLK text span out of bounds')
    header = bytearray(data[:18]); records = bytearray(data[18:offset]); text = bytearray(data[offset:])
    refs = []
    for string in strings:
        encoded = string.encode('ascii')
        refs.append(count + len(refs))
        records.extend(struct.pack('<H8sIIII', 1, b'\0'*8, 0, 0, len(text), len(encoded)))
        text.extend(encoded)
    struct.pack_into('<II', header, 10, count + len(strings), offset + len(strings)*26)
    result = bytes(header + records + text)
    for ref, string in zip(refs, strings):
        at = 18 + ref*26; start, size = struct.unpack_from('<II', result, at+18)
        if result[offset+len(strings)*26+start:offset+len(strings)*26+start+size] != string.encode('ascii'):
            raise ValueError('TLK append verification failed')
    # Old entry offsets and text are unchanged relative to the relocated blob.
    if result[18:18+count*26] != data[18:offset] or result[offset+len(strings)*26:offset+len(strings)*26+len(data)-offset] != data[offset:]:
        raise ValueError('Existing TLK strings changed')
    return result, refs


def display(ref):
    return f'262OB\n{EMPTY}OB\nOB\n{MYSELF}OB\nOB\n{EMPTY}OB\n{ref} 0 0 0 0"" "" AC\n'


def live_program(spec, references):
    TYPES['bcs'] = 0x3ef
    data, origin = read_resource(spec['source'], 'bcs')
    blocks = list(BLOCK.finditer(data.decode('ascii').replace('\r\n','\n')))
    result = 'SC\n'
    foe = '0 0 0 0 0 0 0 0 0 0 0 0 "rdxfoe"'
    seen = trigger(0x400f,0,'GLOBALRDXFOESEEN') + trigger(0x401c,obj=foe)
    result += response(seen,[action(30,1,'GLOBALRDXFOESEEN'), display(references['seen'])])
    removed = 0
    originals = []
    for index in range(spec['first'],spec['first']+4):
        condition, resp = blocks[index].groups()
        originals.append(dict(block=index, response_sha256=hashlib.sha256(resp.encode()).hexdigest(),
                              actions=[int(x) for x in __import__('re').findall(r'(?m)^(\d+)OB$',resp)]))
        if spec['remove_queries']:
            def strip(match):
                nonlocal removed
                if int(match[1]) in (0x40ec,0x40f2): removed += 1; return ''
                return match[0]
            condition = TRIGGER.sub(strip,condition)
        prefix = 'AC\n'.join([action(30,index,'GLOBALRDXBRANCH'), action(30,1,'GLOBALRDXAIDONE'),
                              display(references[str(index)]['enter'])])+'AC\n'
        resp = resp.replace('100AC\n','100AC\n'+prefix,1)
        suffix = 'AC\n'+'AC\n'.join([action(30,1,'GLOBALRDXAFTER'),display(references[str(index)]['return'])])
        at = resp.rfind('RE\n'); resp = resp[:at]+suffix+resp[at:]
        result += 'CR\nCO\n'+trigger(0x400f,0,'GLOBALRDXAIDONE')+condition+'CO\nRS\n'+resp+'RS\nCR\n'
    # A return heartbeat keeps the observed branch readable without relying on
    # combat saving. It executes only after the retained action queue returns.
    for index in range(spec['first'],spec['first']+4):
        condition = trigger(0x400f,1,'GLOBALRDXAFTER')+trigger(0x400f,index,'GLOBALRDXBRANCH')
        result += response(condition,[display(references[str(index)]['return']),action(63,1)])
    if removed != (6 if spec['remove_queries'] else 0): raise ValueError('Unexpected query-removal count')
    return (result+'SC\n').encode('ascii'), dict(origin=origin,source_sha256=hashlib.sha256(data).hexdigest(),
               original_responses=originals, removed_query_records=removed,
               limits='Isolated stock tail with private markers/heartbeat. Entry marker proves selected response; return marker proves queue returned, not exact native action/target identity or DPR.')


def prepare():
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-original-live-'+uuid.uuid4().hex[:8]
    out = LOCAL/'results'/run_id; out.mkdir(parents=True)
    game = LOCAL/('original-live-game-'+run_id[-8:])
    profile = Path(os.environ['USERPROFILE'])/'Documents/BGReduxLab'/run_id
    if game.exists() or profile.exists(): raise ValueError('Refuse existing private destinations')
    game.mkdir(); profile.mkdir(parents=True); (profile/'save').mkdir()
    reference = json.loads((ROOT/'docs/compatibility/evidence/bg2ee-copy-manifest.json').read_text())
    source = LOCAL/'bg2ee-clean'
    print('Copying manifested original game into private diagnostic copy', flush=True)
    for entry in reference['files']:
        incoming = source/entry['path']; target = game/entry['path']
        if digest(incoming) != entry['sha256']: raise ValueError('Source game drift: '+entry['path'])
        target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(incoming,target)
        if digest(target) != entry['sha256']: raise ValueError('Copied game drift: '+entry['path'])
    nonce = uuid.uuid4().hex[:8].upper()
    strings = []; descriptors = []
    for case in CASES:
        row = dict(spec=case,nonce=nonce,refs={})
        row['refs']['seen'] = len(strings); strings.append(f'RDX {nonce} {case["id"]} SEEN')
        for index in range(case['first'],case['first']+4):
            row['refs'][str(index)] = {}
            for phase in ['enter','return']:
                row['refs'][str(index)][phase] = len(strings)
                strings.append(f'RDX {nonce} {case["id"]} B{index} {phase.upper()}')
        descriptors.append(row)
    tlk_path = game/'lang/en_US/dialog.tlk'
    original_tlk_hash = digest(tlk_path)
    edited, refs = append_tlk(tlk_path.read_bytes(),strings); tlk_path.write_bytes(edited)
    override = game/'override'; override.mkdir(exist_ok=True)
    for number, row in enumerate(descriptors,1):
        case = row['spec']; folder = out/case['id']; folder.mkdir()
        fixture, generated, construction = construct_ai(folder,case)
        mapped = {'seen':refs[row['refs']['seen']]}
        for key,value in row['refs'].items():
            if key != 'seen': mapped[key]={phase:refs[v] for phase,v in value.items()}
        compiled, annotation = live_program(case,mapped)
        # Each fixture has its own override resref, so selecting a different
        # named save cannot accidentally execute the previous case's script.
        resref = f'RDXL{number:04d}'
        data = bytearray((fixture/'BALDUR.gam').read_bytes())
        from equipped_defenses import embedded
        from effect_cycle import u32
        at,_ = embedded(data,0); cre_at = u32(data,at+4)
        data[cre_at+0x248:cre_at+0x250] = resref.encode('ascii')
        (fixture/'BALDUR.gam').write_bytes(data)
        construction['precursor_input_files'] = construction.pop('input_files')
        construction['precursor_ai_script_sha256'] = construction.pop('ai_script_sha256')
        construction['unique_script_assignment'] = dict(offset=cre_at+0x248,resref=resref)
        (override/(resref+'.bcs')).write_bytes(compiled)
        name = f'{number:09d}-{case["id"]}-{nonce}'
        destination = profile/'save'/name; shutil.copytree(fixture,destination)
        row.update(fixture=str(destination), fixture_files=manifest(destination),script=resref,
                   script_sha256=digest(override/(resref+'.bcs')),strings=[s for s in strings if case['id']+' ' in s],
                   construction=construction,live_annotation=annotation)
    engine_name = 'BGReduxLab/'+run_id
    (game/'engine.lua').write_text('engine_name = "'+engine_name+'"\nengine_mode = 1\n',encoding='ascii')
    dll = game/'steam_api64.dll'; dll.rename(game/'steam_api64.dll.phase0-retained')
    (profile/'Baldur.lua').write_text("SetPrivateProfileString('Window','Full Screen','0')\nSetPrivateProfileString('Language','Text','en_US')\nSetPrivateProfileString('Program Options','Cloud Saves Enabled','0')\nSetPrivateProfileString('Program Options','Active Campaign','0')\nSetPrivateProfileString('MOVIES','LOGO','1')\nSetPrivateProfileString('MOVIES','INTRO','1')\nSetPrivateProfileString('MOVIES','INTRO15F','1')\n",encoding='ascii')
    result = dict(schema='bg-redux-original-live-preparation/1',run_id=run_id,directory=str(out),game=str(game),
                  profile=str(profile),nonce=nonce,cases=descriptors,executable_sha256=digest(game/'Baldur.exe'),
                  original_tlk_sha256=original_tlk_hash,private_tlk_sha256=digest(tlk_path),
                  engine_lua_sha256=digest(game/'engine.lua'),retained_optional_steam_dll_sha256=digest(game/'steam_api64.dll.phase0-retained'),
                  original_file_count=len(reference['files']),phase='prepared-not-executed',
                  intended_changes=['Private engine.lua profile identity','Appended nonce strings in private TLK',
                                    'Four synthetic fixtures and uniquely named BCS scripts','Optional Steam library retained inert in private copy'],
                  scope='No installed game or personal profile edits; no original/GemRB engine code/binary changes')
    write(out/'preparation.json',result)
    print(json.dumps({k:result[k] for k in ['directory','game','profile','nonce','phase']},indent=2),flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.parse_args(); prepare()
