"""Prepare private six-query EE fixtures; never launch either engine.

Phase 0 modules are imported read-only from the explicit runtime project root.
Generated assets, saves, game copies and profiles are private run artifacts.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import struct
import sys
from types import SimpleNamespace
import uuid


QUERY_KEYS = ('RDXE1', 'RDXD1', 'RDXE2', 'RDXD2', 'RDXE3', 'RDXD3')
IDENTITY_KEYS = ('RDXCASE', 'RDXNONCE', 'RDXDONE', 'RDXSTAGE')
EXPECTED_FILES = {'BALDUR.bmp', 'BALDUR.gam', 'BALDUR.SAV', 'PORTRT0.bmp',
                  'PORTRT1.bmp', 'save_000000033-GemRB.cloud.meta'}


def cases():
    rows = []
    def add(name, main='sw1h01', off=None, ammo=None, defense=None, group='hands'):
        rows.append(dict(id=name, main=main, off=off, ammo=ammo, defense=defense, group=group))
    add('01-normal-plus-pfmw', off='sw1h02', defense=(120, 0, 1))
    add('02-plus-normal-pfmw', main='sw1h02', off='sw1h01', defense=(120, 0, 1))
    add('03-crush-slash-slash100', main='hamm01', off='sw1h01', defense=(86, 100, 1))
    add('04-slash-crush-slash100', off='hamm01', defense=(86, 100, 1))
    add('05-normal-empty')
    add('06-normal-shield', off='shld01')
    add('07-plus-empty-pfmw', main='sw1h02', defense=(120, 0, 1))
    add('08-normal-shield-pfmw', off='shld01', defense=(120, 0, 1))
    for launcher, ammo, label in [('bow01', 'arow02', 'ammo-plus'), ('bow02', 'arow01', 'bow-plus')]:
        for suffix, defense in [('pfmw', (120, 0, 1)), ('ench0', (120, 0, 0)),
                                ('ench1', (120, 1, 0)), ('ench2', (120, 2, 0))]:
            add(f'{label}-{suffix}', main=launcher, ammo=ammo, defense=defense, group='ammo')
    for name, main, ammo, defense in [
        ('crush-crush100', 'hamm01', None, (87, 100, 1)),
        ('pierce-pierce100', 'dagg01', None, (88, 100, 1)),
        ('missile-missile100', 'bow01', 'arow01', (89, 100, 1)),
        ('crush-slash100', 'hamm01', None, (86, 100, 1)),
        ('pierce-slash100', 'dagg01', None, (86, 100, 1)),
        ('missile-slash100', 'bow01', 'arow01', (86, 100, 1))]:
        add(name, main=main, ammo=ammo, defense=defense, group='damage')
    return rows


def validate_spec(spec):
    if not re.fullmatch('[a-z0-9-]{1,48}', spec['id']):
        raise ValueError('Unsafe case identity')
    for key in ('main', 'off', 'ammo'):
        ref = spec.get(key)
        if ref is not None and not re.fullmatch('[a-z0-9]{1,8}', ref):
            raise ValueError('Invalid item resource: '+key)
    if not spec.get('main'):
        raise ValueError('Main weapon required')
    if bool(spec.get('ammo')) != spec['main'].startswith('bow'):
        raise ValueError('Explicit bow/ammunition pair required')
    if spec.get('ammo') and spec.get('off'):
        raise ValueError('Two-handed launcher cannot declare off-hand')
    if spec.get('defense') is not None:
        opcode, p1, p2 = spec['defense']
        if opcode not in (86, 87, 88, 89, 120) or p1 < 0 or p2 not in (0, 1):
            raise ValueError('Unsupported exact diagnostic defense')


def selected_cases(group, ids=None):
    available = cases()
    if ids:
        if len(set(ids)) != len(ids) or set(ids)-{x['id'] for x in available}:
            raise ValueError('Duplicate or unknown case selection')
        chosen = [x for x in available if x['id'] in ids]
    else:
        chosen = [x for x in available if group == 'all' or x['group'] == group]
    for spec in chosen:
        validate_spec(spec)
    return chosen


def program(api, case_number, nonce):
    if not 1 <= case_number <= 9999 or not 1 <= nonce <= 0x7fffffff:
        raise ValueError('Case/nonce outside positive signed integer range')
    script = 'SC\n'
    for stage, key in enumerate(QUERY_KEYS):
        hand = stage//2+1
        opcode = 0x40ec if stage % 2 == 0 else 0x40f2
        gate = api.trigger(0x400f, stage, 'GLOBALRDXSTAGE')
        for truth in (True, False):
            condition = gate+(api.trigger(opcode, hand, obj=api.PLAYER2) if truth else '')
            actions = [api.action(30, int(truth), 'GLOBAL'+key),
                       api.action(30, case_number, 'GLOBALRDXCASE'),
                       api.action(30, nonce, 'GLOBALRDXNONCE'),
                       api.action(30, stage+1, 'GLOBALRDXSTAGE')]
            script += api.response(condition, actions)
    script += api.response(api.trigger(0x400f, 6, 'GLOBALRDXSTAGE'),
                           [api.action(30, 1, 'GLOBALRDXDONE'),
                            api.action(30, 7, 'GLOBALRDXSTAGE'), api.action(190, 0)])
    return (script+'SC\n').encode('ascii')


def replace_equipment(cre, spec):
    """Append a complete declared inventory to the isolated protagonist CRE."""
    validate_spec(spec)
    if cre[:8] != b'CRE V1.0' or len(cre) < 0x2d4:
        raise ValueError('Expected bounded CRE V1.0')
    if struct.unpack_from('<I', cre, 0x2c0)[0]:
        raise ValueError('Expected empty baseline protagonist inventory')
    refs = [spec['main']]+([spec['off']] if spec['off'] else [])+([spec['ammo']] if spec['ammo'] else [])
    item_at = len(cre)
    for ref in refs:
        cre.extend(ref.upper().encode().ljust(8, b'\0')+
                   struct.pack('<4HI', 0, 40 if ref == spec['ammo'] else 0, 0, 0, 1))
    slots = [0xffff]*38
    slots[9] = 0
    if spec['off']:
        slots[2] = 1
    if spec['ammo']:
        slots[13] = len(refs)-1
    slot_at = len(cre)
    cre.extend(struct.pack('<38HhH', *slots, -24 if spec['ammo'] else 0, 0))
    struct.pack_into('<III', cre, 0x2b8, slot_at, item_at, len(refs))
    return equipment_guard(cre, spec)


def equipment_guard(cre, spec):
    validate_spec(spec)
    if cre[:8] != b'CRE V1.0' or len(cre) < 0x2d4:
        raise ValueError('Expected CRE V1.0')
    slot_at, item_at, count = struct.unpack_from('<III', cre, 0x2b8)
    if count > 3 or item_at+20*count > len(cre) or slot_at+80 > len(cre):
        raise ValueError('Inventory offsets/count invalid')
    refs = [cre[item_at+i*20:item_at+i*20+8].split(b'\0')[0].decode('ascii').lower() for i in range(count)]
    expected = [spec['main']]+([spec['off']] if spec['off'] else [])+([spec['ammo']] if spec['ammo'] else [])
    if refs != expected:
        raise ValueError('Exact declared item table differs')
    slots = struct.unpack_from('<38HhH', cre, slot_at)
    expected_slots = [0xffff]*38
    expected_slots[9] = 0
    if spec['off']:
        expected_slots[2] = 1
    if spec['ammo']:
        expected_slots[13] = len(refs)-1
        if struct.unpack_from('<H', cre, item_at+20*(len(refs)-1)+10)[0] != 40:
            raise ValueError('Required ammunition charges differ')
    if tuple(expected_slots) != slots[:38] or slots[38:] != (-24 if spec['ammo'] else 0, 0):
        raise ValueError('Physical slots, selected weapon/ammo or ability differ')
    return dict(items=refs, main_physical_slot=9, off_physical_slot=2 if spec['off'] else None,
                ammo_physical_slot=13 if spec['ammo'] else None, selected=slots[38], ability=slots[39])


def output_values(globals_, case_number, nonce):
    if any(type(globals_.get(k)) is not int or globals_.get(k) != v
           for k, v in [('RDXCASE', case_number), ('RDXNONCE', nonce), ('RDXDONE', 1), ('RDXSTAGE', 7)]):
        raise ValueError('Stale/wrong case, nonce or incomplete query output')
    values = {k: globals_.get(k) for k in QUERY_KEYS}
    if any(type(v) is not int or v not in (0, 1) for v in values.values()):
        raise ValueError('Missing or non-Boolean query evidence')
    return values


def inspect_output(api, gam, row):
    """Read an explicitly selected output; never search or accept a stale save."""
    data = Path(gam).read_bytes()
    _, pc = api.equipped_defenses.embedded(data, 0)
    if pc[0x248:0x250].upper() != row['script'].upper().encode('ascii'):
        raise ValueError('Output primary script identity differs')
    guard = equipment_guard(pc, row['spec'])
    observed = api.equipped_defenses.observe(gam)
    expected = row['spec']['defense']
    defenses = observed[1]['defense_effects']
    if expected is None:
        if defenses:
            raise ValueError('Unexpected output diagnostic defense')
    else:
        opcode, p1, p2 = expected
        permitted_p1 = (p1, 0xffffffff) if opcode == 120 and p2 == 1 else (p1,)
        if (len(defenses) != 1 or defenses[0]['opcode'] != opcode or defenses[0]['p1'] not in permitted_p1
                or defenses[0]['p2'] != p2 or defenses[0]['timing'] != 9):
            raise ValueError('Output diagnostic defense differs')
    values = output_values(api.legacy_oracle.read_wire(gam)['globals'], row['number'], row['nonce'])
    return dict(values=values, equipment=guard, defenses=defenses, gam_sha256=digest(gam),
                scope='Serialized query results and declared inventory/defenses; not cached runtime weapon preflight or side-effect proof.')


def load_api(project):
    folder = project/'tools/phase0'
    sys.path.insert(0, str(folder))
    modules = {name: importlib.import_module(name) for name in
               ('harness', 'script_query_probe', 'equipped_defenses', 'save_harness', 'legacy_oracle', 'probe_ui_resources')}
    if any(not Path(m.__file__).resolve().is_relative_to(folder.resolve()) for m in modules.values()):
        raise ValueError('Phase 0 import resolved outside explicit project root')
    if modules['harness'].ROOT.resolve() != project:
        raise ValueError('Phase 0 project-root mismatch')
    return SimpleNamespace(**modules)


def write(path, data):
    path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_relative(value):
    path = PureWindowsPath(value)
    if not value or path.is_absolute() or path.drive or path.root or '..' in path.parts or not path.parts or ':' in str(path):
        raise ValueError('Unsafe manifested relative path')
    return Path(*path.parts)


def prepare(project, results, specs, with_original=False):
    project, results = project.resolve(), results.resolve()
    api = load_api(project)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-weapon-oracle-'+uuid.uuid4().hex[:8]
    out = results/run_id
    out.mkdir(parents=True, exist_ok=False)
    nonce = int(uuid.uuid4().hex[:8], 16) & 0x7fffffff or 1
    report = dict(schema='bg-redux-phase1-weapon-oracle-preparation/1', run_id=run_id,
                  directory=str(out), nonce=nonce, nonce_hex=f'{nonce:08X}', cases=[],
                  phase='preparing', executed=False, project=str(project), original_prepared=False,
                  limits='Input preparation only; no original or native predicate result is inferred.')
    write(out/'preparation.json', report)
    try:
        item_reader = api.probe_ui_resources
        item_reader.TYPES['itm'] = 0x3ed
        item_metadata = {}
        for spec in specs:
            validate_spec(spec)
            for key in ('main', 'off', 'ammo'):
                ref = spec.get(key)
                if not ref or ref in item_metadata:
                    continue
                raw, origin = item_reader.read_resource(ref, 'itm')
                if raw is None or raw[:8] != b'ITM V1  ' or len(raw) < 0x72:
                    raise ValueError('Missing/invalid declared item '+ref)
                header_at = struct.unpack_from('<I', raw, 0x64)[0]
                header_count = struct.unpack_from('<H', raw, 0x68)[0]
                if header_count > 100 or header_at+56*header_count > len(raw):
                    raise ValueError('Invalid item ability table '+ref)
                item_metadata[ref] = dict(origin=origin, sha256=hashlib.sha256(raw).hexdigest(),
                                          enchantment=struct.unpack_from('<I', raw, 0x60)[0],
                                          flags=struct.unpack_from('<I', raw, 0x18)[0],
                                          abilities=[dict(index=i, attack_type=raw[header_at+56*i],
                                                          damage_type=struct.unpack_from('<H', raw, header_at+56*i+0x1c)[0])
                                                     for i in range(header_count)])
        report['item_metadata'] = item_metadata
        for number, spec in enumerate(specs, 1):
            case_out = out/spec['id']; case_out.mkdir()
            fixture, override, precursor = api.script_query_probe.prepare(case_out)
            gam = fixture/'BALDUR.gam'; data = bytearray(gam.read_bytes())
            if set(QUERY_KEYS+IDENTITY_KEYS) & set(api.legacy_oracle.read_wire(gam)['globals']):
                raise ValueError('Fixture query identity/global collision')
            _, attacker = api.equipped_defenses.embedded(data, 0)
            input_guard = replace_equipment(attacker, spec)
            resref = f'P1{nonce & 255:02X}{number:04d}'
            attacker[0x248:0x250] = resref.encode('ascii')
            api.equipped_defenses.relocate(data, 0, attacker)
            row, _ = api.equipped_defenses.embedded(data, 0)
            struct.pack_into('<4H', data, row+0x8c, 11 if spec['ammo'] else 35, 10, 10, 10)
            struct.pack_into('<4H', data, row+0x94, 0, 0, 0, 0)
            quick_slots = struct.unpack_from('<4H', data, row+0x8c)
            quick_headers = struct.unpack_from('<4H', data, row+0x94)
            if quick_slots != (11 if spec['ammo'] else 35, 10, 10, 10) or quick_headers != (0, 0, 0, 0):
                raise ValueError('GAM quick weapon/header assignment differs')
            _, defender = api.equipped_defenses.embedded(data, 1)
            api.equipped_defenses.add_defense(defender, spec['defense'])
            api.equipped_defenses.relocate(data, 1, defender)
            gam.write_bytes(data)
            compiled = program(api.script_query_probe, number, nonce)
            script = override/(resref+'.bcs'); script.write_bytes(compiled)
            _, final_pc = api.equipped_defenses.embedded(gam.read_bytes(), 0)
            if final_pc[0x248:0x250] != resref.encode():
                raise ValueError('Unique primary script assignment missing')
            equipment_guard(final_pc, spec)
            observed = api.equipped_defenses.observe(gam)
            expected_defenses = [] if spec['defense'] is None else [dict(opcode=spec['defense'][0], p1=spec['defense'][1], p2=spec['defense'][2], timing=9)]
            if observed[1]['defense_effects'] != expected_defenses:
                raise ValueError('Exact declared defense input differs')
            files = api.save_harness.manifest(fixture)
            if set(files) != EXPECTED_FILES:
                raise ValueError('Final fixture must have exact six-file inventory')
            report['cases'].append(dict(number=number, spec=spec, nonce=nonce, script=resref,
                                        script_path=str(script), script_sha256=digest(script),
                                        fixture=str(fixture), fixture_files=files, input_guard=input_guard,
                                        quick_slot_input=dict(slots=quick_slots, headers=quick_headers),
                                        defense_input=observed[1]['defense_effects'], precursor=precursor,
                                        expected_identity=dict(RDXCASE=number, RDXNONCE=nonce, RDXDONE=1, RDXSTAGE=7),
                                        query_keys=list(QUERY_KEYS), observed_values=None))
            write(out/'preparation.json', report)
        if with_original:
            prepare_original(project, out, report, api)
        report['phase'] = 'prepared-not-executed'
        report['generator_sha256'] = digest(Path(__file__))
        report['phase0_imports'] = {name: dict(path=m.__file__, sha256=digest(m.__file__)) for name, m in vars(api).items()}
        write(out/'preparation.json', report)
    except Exception as error:
        report.update(phase='preparation-failed', error=str(error))
        write(out/'preparation.json', report)
        raise
    return report


def prepare_original(project, out, report, api):
    """Only explicit --prepare-original creates a fresh private game/profile."""
    game = project/'phase1-local'/('original-weapon-game-'+report['run_id'].split('-')[-1])
    profile = Path(os.environ['USERPROFILE'])/'Documents/BGReduxP1'/report['run_id']
    if game.exists() or profile.exists():
        raise ValueError('Refuse existing private original destinations')
    report.update(game=str(game), profile=str(profile))
    write(out/'preparation.json', report)
    game.mkdir(parents=True); (profile/'save').mkdir(parents=True)
    source = project/'phase0-local/bg2ee-clean'
    manifest = json.loads((project/'docs/compatibility/evidence/bg2ee-copy-manifest.json').read_text(encoding='utf-8'))
    paths = set()
    for row in manifest['files']:
        relative = safe_relative(row['path'])
        if str(relative).lower() in paths:
            raise ValueError('Duplicate source game manifest path')
        paths.add(str(relative).lower())
        incoming, destination = source/relative, game/relative
        if digest(incoming) != row['sha256']:
            raise ValueError('Original source drift: '+str(relative))
        destination.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(incoming, destination)
        if digest(destination) != row['sha256']:
            raise ValueError('Original copy drift: '+str(relative))
    override = game/'override'; override.mkdir(exist_ok=True)
    for row in report['cases']:
        destination = profile/'save'/f'{row["number"]:09d}-{row["spec"]["id"]}-{report["nonce_hex"]}'
        shutil.copytree(row['fixture'], destination)
        if api.save_harness.manifest(destination) != row['fixture_files']:
            raise ValueError('Copied final fixture drift')
        row['original_fixture'] = str(destination)
        shutil.copy2(row['script_path'], override/(row['script']+'.bcs'))
        if digest(override/(row['script']+'.bcs')) != row['script_sha256']:
            raise ValueError('Copied unique script drift')
    (game/'engine.lua').write_text(f'engine_name = "BGReduxP1/{report["run_id"]}"\nengine_mode = 1\n', encoding='ascii')
    dll = game/'steam_api64.dll'
    if dll.is_file():
        dll.rename(game/'steam_api64.dll.phase1-retained')
    (profile/'Baldur.lua').write_text("SetPrivateProfileString('Window','Full Screen','0')\nSetPrivateProfileString('Language','Text','en_US')\nSetPrivateProfileString('Program Options','Cloud Saves Enabled','0')\nSetPrivateProfileString('Program Options','Active Campaign','0')\nSetPrivateProfileString('MOVIES','LOGO','1')\nSetPrivateProfileString('MOVIES','INTRO','1')\nSetPrivateProfileString('MOVIES','INTRO15F','1')\n", encoding='ascii')
    report.update(original_prepared=True, executable_sha256=digest(game/'Baldur.exe'),
                  engine_lua_sha256=digest(game/'engine.lua'), private_profile_config_sha256=digest(profile/'Baldur.lua'),
                  original_source_manifest_sha256=digest(project/'docs/compatibility/evidence/bg2ee-copy-manifest.json'),
                  copied_game_files=len(paths), intended_changes=['Unique private engine.lua identity',
                  'Unique case scripts', 'Six-query laboratory fixtures in private profile',
                  'Private optional Steam DLL retained inert'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--results-root', type=Path, required=True)
    parser.add_argument('--group', choices=('hands', 'ammo', 'damage', 'all'), default='hands')
    parser.add_argument('--cases', nargs='+')
    parser.add_argument('--prepare-original', action='store_true')
    args = parser.parse_args(argv)
    report = prepare(args.project_root, args.results_root, selected_cases(args.group, args.cases), args.prepare_original)
    print(json.dumps({k: report[k] for k in ('directory', 'phase', 'nonce', 'original_prepared')}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
