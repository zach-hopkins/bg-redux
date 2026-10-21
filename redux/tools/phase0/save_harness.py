"""Menu-free native import/query/resave/fresh-process reload characterization.

The probe links the unchanged engine DLL. Every native stage has a fresh cache,
Windows home, and process. Comparisons never turn unexplained differences green.
"""
from __future__ import annotations
import argparse
import copy
import datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import uuid

from harness import ROOT, LOCAL, BUILD, digest, environment, run_process

PROBE = LOCAL / 'native-probe/Redux_save_probe.exe'
REGISTRY = Path(__file__).with_name('fixtures.json')
NORMALIZATION = {
    'schema': 'bg-redux-persistence-comparison/1',
    'runtime_id': 'Actor process handles removed; raw snapshots retain them.',
    'effect_caster_id': 'Map to observed actor script-name/area/position identity; unresolved IDs remain explicit.',
    'random_value': 'Effect cached random value is runtime-only, not serialized; raw differences retained.',
    'actor_order': 'Current-area actors sorted by script-name/area/position/name; party and stored NPC order retained.',
    'not_normalized': 'Stats, inventory, effects/order, spells, globals, positions, portraits, timers, selection and all other collected fields.'
}


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def manifest(folder):
    return {path.relative_to(folder).as_posix(): dict(bytes=path.stat().st_size, sha256=digest(path))
            for path in sorted(folder.rglob('*')) if path.is_file()}


def member(folder, extension):
    matches = [path for path in folder.iterdir() if path.is_file() and path.name.lower() == 'baldur.' + extension]
    if len(matches) != 1 or matches[0].stat().st_size == 0:
        raise ValueError(f'Required nonempty baldur.{extension} missing/ambiguous in fixture')
    return matches[0]


def validate_fixture(folder):
    gam, sav = member(folder, 'gam'), member(folder, 'sav')
    if not gam.read_bytes().startswith(b'GAME'):
        raise ValueError('Invalid GAM signature; refusing native import')
    if not sav.read_bytes().startswith(b'SAV V1.0'):
        raise ValueError('Invalid SAV signature; refusing native import')


def actor_key(actor):
    return (actor['script_name'].lower(), actor['area'].lower(), tuple(actor['position']), actor['name'])


def normalize(state):
    state = copy.deepcopy(state)
    identities = {}
    for group in ('party', 'stored_npcs', 'current_area_actors'):
        for actor in state[group]:
            key = json.dumps(actor_key(actor), ensure_ascii=False)
            identities.setdefault(actor['runtime_id'], set()).add(key)
    for group in ('party', 'stored_npcs', 'current_area_actors'):
        for actor in state[group]:
            actor.pop('runtime_id')
            for effect in actor['effects']:
                caster = effect.pop('caster_id')
                effect['caster_identity'] = sorted(identities[caster]) if caster in identities else ('none' if caster == 0 else f'unresolved:{caster}')
                effect.pop('random_value')
    state['current_area_actors'].sort(key=actor_key)
    return state


def differences(left, right, path=''):
    if type(left) is not type(right):
        return [dict(path=path, before=left, after=right)]
    if isinstance(left, dict):
        out = []
        for key in sorted(left.keys() | right.keys()):
            escaped = key.replace('~', '~0').replace('/', '~1')
            here = path + '/' + escaped
            if key not in left or key not in right:
                out.append(dict(path=here, before=left.get(key), after=right.get(key), missing='before' if key not in left else 'after'))
            else:
                out.extend(differences(left[key], right[key], here))
        return out
    if isinstance(left, list):
        out = []
        if len(left) != len(right):
            out.append(dict(path=path + '/length', before=len(left), after=len(right)))
        for index, (a, b) in enumerate(zip(left, right)):
            out.extend(differences(a, b, path + '/' + str(index)))
        return out
    return [] if left == right else [dict(path=path, before=left, after=right)]


def comparison_scopes(left, right):
    a,b = normalize(left),normalize(right)
    scopes = {}
    for name, keys in {'party':['party'], 'stored_npcs':['stored_npcs'],
                       'world_metadata':['game_time','gold','reputation','current_area','campaign','expansion','globals','journal'],
                       'current_area':['current_area_actors','area_locals']}.items():
        diff = differences({key:a[key] for key in keys},{key:b[key] for key in keys})
        scopes[name]=dict(passed=not diff,differences=len(diff))
    return scopes


def query(state, pointer):
    if pointer == '':
        return state
    if not pointer.startswith('/'):
        raise ValueError('Queries use JSON Pointer, starting with /')
    for token in pointer[1:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        state = state[int(token)] if isinstance(state, list) else state[token]
    return state


def assertion(state, spec):
    operator = spec.get('op', 'eq')
    try:
        actual = query(state, spec['path'])
        expected = spec.get('value')
        if operator == 'eq': ok = actual == expected
        elif operator == 'ge': ok = actual >= expected
        elif operator == 'length_eq': ok = len(actual) == expected
        elif operator == 'length_ge': ok = len(actual) >= expected
        elif operator == 'exists': ok = True
        else: raise ValueError('Unsupported assertion operator: ' + operator)
        return dict(spec=spec, passed=ok, actual=actual)
    except (KeyError, IndexError, TypeError, ValueError) as error:
        return dict(spec=spec, passed=False, error=str(error))


def stage(output, name, fixture, save_to, timeout, select=None):
    directory = output / name
    directory.mkdir()
    cache = directory / 'cache'
    cache.mkdir()
    profile = directory / 'engine-profile'
    profile.mkdir()
    config = dict(GameType='bg2ee', GamePath=LOCAL / 'bg2ee-clean', GemRBPath=ROOT / 'gemrb/gemrb',
        PluginsPath=BUILD / 'gemrb/plugins', CachePath=cache, SavePath=profile, UseAsLibrary=1,
        AudioDriver='none', GameLanguagePath='lang/en_US', Logging=1, LogColor=0,
        PathfinderThreadsCount=0, PathfinderMainThreadMode='immediate')
    config_path = directory / 'probe.cfg'
    config_path.write_text(''.join(f'{k}={str(v).replace(chr(92), chr(47))}\n' for k,v in config.items()), encoding='utf-8')
    command = [str(PROBE), '--config', str(config_path), '--save-id', '7', '--save-dir', str(fixture),
               '--output', str(directory / 'state.json')]
    if select is not None:
        command += ['--select', str(select)]
    if save_to:
        save_to.mkdir()
        command += ['--resave', str(save_to)]
    process = run_process(command, directory, environment(directory), directory / 'process.log', timeout)
    result = dict(name=name, command=command, process=process, config_sha256=digest(config_path),
                  state_path=str(directory / 'state.json'))
    error_file = directory / 'state.json.error.json'
    if error_file.exists():
        result['native_error'] = json.loads(error_file.read_text(encoding='utf-8'))
    state = None
    if process['exit_code'] == 0 and not process['timed_out']:
        try:
            state = json.loads((directory / 'state.json').read_text(encoding='utf-8'))
            if state['schema'] != 'bg-redux-state/1' or not state['party']:
                raise ValueError('Missing required state/party')
        except (OSError, ValueError, KeyError) as error:
            result['artifact_error'] = str(error)
            state = None
    result['passed'] = state is not None
    write(directory / 'process-result.json', result)
    return result, state


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['save', 'inspect', 'scenario'])
    parser.add_argument('--fixture', default='gemrb-autosave')
    parser.add_argument('--fixture-dir', type=Path)
    parser.add_argument('--scenario', type=Path)
    parser.add_argument('--timeout', type=float, default=45)
    parser.add_argument('--name', default='save-baseline')
    parser.add_argument('--select', type=int)
    parser.add_argument('--query', action='append', default=[])
    args = parser.parse_args(argv)
    if args.timeout <= 0 or not re.fullmatch(r'[a-zA-Z0-9_-]+', args.name):
        parser.error('Positive timeout and simple run name required')
    now = datetime.datetime.now(datetime.timezone.utc)
    run_id = now.strftime('%Y%m%dT%H%M%SZ') + '-' + args.name + '-' + uuid.uuid4().hex[:8]
    output = LOCAL / 'results' / run_id
    output.mkdir(parents=True)
    result = dict(schema='bg-redux-save-run/1', run_id=run_id, captured_utc=now.isoformat(),
        verdict='failed', mode=args.mode, stages=[], comparisons=[], assertions=[], artifacts=str(output))
    original = before = None
    try:
        build_receipt=json.loads((LOCAL/'native-probe/build.json').read_text(encoding='utf-8'))
        if (build_receipt['exit_code'] != 0 or build_receipt['source_sha256'] != digest(ROOT/'tools/phase0/native/save_probe.cpp')
            or build_receipt['engine_dll_sha256'] != digest(BUILD/'gemrb/libgemrb_core.dll')
            or build_receipt['binary_sha256'] != digest(PROBE)):
            raise ValueError('Native probe build receipt stale or mismatched; rebuild the external host')
        scenario = json.loads(args.scenario.read_text(encoding='utf-8')) if args.scenario else {}
        if args.mode == 'scenario' and not scenario:
            raise ValueError('scenario mode requires --scenario')
        fixture_name = scenario.get('fixture', args.fixture)
        registry = json.loads(REGISTRY.read_text(encoding='utf-8'))['fixtures']
        entry = registry.get(fixture_name)
        if args.fixture_dir:
            original = args.fixture_dir.resolve()
            provenance = 'User-supplied fixture directory; creation/mod provenance must be established separately'
        elif entry:
            original = (ROOT / entry['path']).resolve()
            provenance = entry['provenance']
        else:
            raise ValueError('Unknown fixture: ' + fixture_name)
        validate_fixture(original)
        before = manifest(original)
        if entry and not args.fixture_dir and entry.get('manifest'):
            pinned = json.loads((ROOT/entry['manifest']).read_text(encoding='utf-8'))['files']
            if before != pinned:
                raise ValueError('Registered fixture differs from pinned manifest; preserve and investigate drift')
        result['fixture'] = dict(id=fixture_name, source=str(original), provenance=provenance, files=before,
            gam_signature=member(original,'gam').read_bytes()[:8].decode('ascii'),
            eeex_marker_count=member(original,'gam').read_bytes().count(b'EEex'))
        result['provenance'] = dict(engine_revision=subprocess.check_output(['git','-C',str(ROOT/'gemrb'),'rev-parse','HEAD'],text=True).strip(),
            engine_status=subprocess.check_output(['git','-C',str(ROOT/'gemrb'),'status','--porcelain'],text=True),
            probe_sha256=digest(PROBE), engine_dll_sha256=digest(BUILD/'gemrb/libgemrb_core.dll'),
            probe_source_sha256=digest(ROOT/'tools/phase0/native/save_probe.cpp'),
            game_manifest_sha256=digest(ROOT/'docs/compatibility/evidence/bg2ee-copy-manifest.json'))
        copied = output / 'immutable-input'
        shutil.copytree(original, copied)
        if manifest(copied) != before:
            raise ValueError('Fixture copy/hash mismatch')
        select = scenario.get('select', args.select)
        resaved = output / 'resaved'
        first, initial = stage(output, 'import', copied, None if args.mode=='inspect' else resaved, args.timeout, select)
        result['stages'].append(first)
        if initial is None:
            if first.get('native_error',{}).get('error','').startswith('Unsupported effect payload'):
                result['verdict']='unsupported'
            raise ValueError('Native import/initialization failed; see stage result/log')
        # Compare a separately decoded subset of original wire fields with the
        # pre-area engine snapshot. Keep recalculation differences visible.
        from legacy_oracle import read_wire, compare_wire
        wire = read_wire(member(copied,'gam'))
        imported = json.loads((output/'import/state.json.imported.json').read_text(encoding='utf-8'))
        result['wire_oracle'] = compare_wire(wire,imported)
        write(output/'wire-oracle.json',result['wire_oracle'])
        specs = [dict(path='/party',op='length_ge',value=1), dict(path='/current_area',op='exists')]
        specs += scenario.get('assertions', [])
        result['assertions'] = [assertion(initial,spec) for spec in specs]
        result['queries'] = {pointer:query(initial,pointer) for pointer in args.query + scenario.get('queries',[])}
        if args.mode != 'inspect':
            saves = sorted((resaved/'save').glob('*'))
            if len(saves) != 1:
                raise ValueError('Expected exactly one newly written save')
            validate_fixture(saves[0])
            result['resaved_files'] = manifest(saves[0])
            write(output/'normalization-policy.json',NORMALIZATION)
            prior = initial
            for cycle in (1,2):
                target = output / f'resaved-{cycle+1}' if cycle == 1 else None
                reload_result, reloaded = stage(output,f'reload-{cycle}',saves[0],target,args.timeout,select)
                result['stages'].append(reload_result)
                if reloaded is None:
                    raise ValueError(f'Fresh-process reload-{cycle} failed')
                raw = differences(prior,reloaded)
                normalized = differences(normalize(prior),normalize(reloaded))
                write(output/f'reload-{cycle}-raw-diff.json',raw)
                write(output/f'reload-{cycle}-semantic-diff.json',normalized)
                result['comparisons'].append(dict(cycle=cycle,raw_differences=len(raw),semantic_differences=len(normalized),
                    passed=not normalized, scopes=comparison_scopes(prior,reloaded), examples=normalized[:12]))
                for spec in specs:
                    item = assertion(reloaded,spec);item['stage']=f'reload-{cycle}';result['assertions'].append(item)
                prior = reloaded
                if target:
                    saves = sorted((target/'save').glob('*'))
                    if len(saves)!=1: raise ValueError('Expected one second-generation save')
                    validate_fixture(saves[0])
            # Repeat original import distinguishes reload drift from run-to-run variability.
            repeat_result, repeated = stage(output,'repeat-import',copied,None,args.timeout,select)
            result['stages'].append(repeat_result)
            if repeated is None: raise ValueError('Repeated fresh import failed')
            repeat_diff = differences(normalize(initial),normalize(repeated))
            write(output/'repeat-import-semantic-diff.json',repeat_diff)
            result['repeat_import'] = dict(semantic_differences=len(repeat_diff),passed=not repeat_diff,
                scopes=comparison_scopes(initial,repeated))
        result['verdict'] = 'passed' if (all(item['passed'] for item in result['assertions'])
            and all(item['passed'] for item in result['comparisons'])
            and result.get('repeat_import',dict(passed=True))['passed']
            and not result['wire_oracle']['differences']) else 'differences'
    except Exception as error:
        result['error'] = str(error)
    finally:
        if any(s['process']['timed_out'] for s in result['stages']): result['verdict']='timeout'
        result['execution_verdict']='passed' if result['stages'] and all(s['passed'] for s in result['stages']) else 'failed'
        result['assertion_verdict']='passed' if result['assertions'] and all(s['passed'] for s in result['assertions']) else 'not-passed'
        result['persistence_verdict']=('passed' if all(c['passed'] for c in result['comparisons']) else 'differences') if result['comparisons'] else 'not-run'
        if original and before:
            result['source_unchanged'] = manifest(original) == before
            if not result['source_unchanged']: result['verdict']='failed'
        if (output/'immutable-input').exists() and before:
            result['input_copy_unchanged'] = manifest(output/'immutable-input') == before
            if not result['input_copy_unchanged']: result['verdict']='failed'
        write(output/'result.json',result)
    compact = {key:result[key] for key in ('run_id','verdict','error','source_unchanged') if key in result}
    compact.update({key:result[key] for key in ('execution_verdict','assertion_verdict','persistence_verdict')})
    compact['artifact_directory']=str(output)
    compact['stages']=[dict(name=s['name'],passed=s['passed'],process=s['process']) for s in result['stages']]
    compact['comparisons']=result['comparisons']
    if result.get('queries'): compact['queries']=result['queries']
    compact['assertions_passed']=sum(a['passed'] for a in result['assertions'])
    compact['assertions_total']=len(result['assertions'])
    print(json.dumps(compact,indent=2))
    return 0 if result['verdict']=='passed' else 1


if __name__=='__main__':
    raise SystemExit(main())
