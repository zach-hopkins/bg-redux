"""Observe collected state around fixed EE queries in eight equipped fixtures.

Library-mode characterization only. No hidden-state/RNG side-effect claim,
simulation ticks, save operation, original runtime or engine edits.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import uuid

from baseline_runner import execute, files_manifest, preflight, protected, read, safe_member, sha, write

QUERIES = ('WeaponEffectiveVs(Player2,MAINHAND)', 'WeaponCanDamage(Player2,MAINHAND)')
LIMIT = 'Collected same-process state only, after library-mode initialization; hidden state, RNG internals, caches, action queues and normal-loop behavior are not proven unchanged.'


def diff(before, after, path=''):
    if type(before) is not type(after):
        return [dict(path=path, before=before, after=after)]
    if isinstance(before, dict):
        rows = []
        for key in sorted(before.keys() | after.keys()):
            pointer = path+'/'+key.replace('~','~0').replace('/','~1')
            if key not in before or key not in after:
                rows.append(dict(path=pointer, before=before.get(key), after=after.get(key), missing='before' if key not in before else 'after'))
            else:
                rows += diff(before[key], after[key], pointer)
        return rows
    if isinstance(before, list):
        rows = []
        if len(before) != len(after):
            rows.append(dict(path=path+'/length', before=len(before), after=len(after)))
        for index, (a, b) in enumerate(zip(before, after)):
            rows += diff(a, b, path+'/'+str(index))
        return rows
    return [] if before == after else [dict(path=path, before=before, after=after)]


def require_state(state):
    if state.get('schema') != 'bg-redux-state/1':
        raise ValueError('Required state snapshot schema missing')
    for key in ('game_time','globals','area_locals','party','stored_npcs','current_area_actors','journal'):
        if key not in state:
            raise ValueError('State surface incomplete: '+key)
    for group in ('party','stored_npcs','current_area_actors'):
        for actor in state[group]:
            if len(actor.get('base_stats', [])) != 256 or len(actor.get('modified_stats', [])) != 256:
                raise ValueError('Actor stat surface incomplete')
            for key in ('inventory','effects','spellbook','locals','runtime_id','position'):
                if key not in actor:
                    raise ValueError('Actor state surface incomplete: '+key)


def runtime_guard(spec, state):
    require_state(state)
    if state['current_area'].upper() != 'AR0602' or len(state['party']) != 2 or state.get('selection') != 1:
        raise ValueError('Expected selected protagonist and two actors in AR0602')
    sender, target = state['party']
    if (target['script_name'].lower() != 'imoen' or sender['runtime_id'] == target['runtime_id']
            or sender['area'].upper() != 'AR0602' or target['area'].upper() != 'AR0602'):
        raise ValueError('Declared sender/Player2 target identity not initialized')
    inventory = sender['inventory']
    items = {item['slot']: item for item in inventory['items']}
    selected = -24 if spec['weapon'] == 'bow01' else 0
    if (inventory['equipped'] != selected or inventory['equipped_header'] != 0
            or items.get(35,{}).get('resref','').lower() != spec['weapon']):
        raise ValueError('Actual weapon, selection or ability differs from fixture')
    if spec['weapon'] == 'bow01':
        ammo = items.get(11,{})
        if ammo.get('resref','').lower() != 'arow01' or ammo.get('usages',[None])[0] != 40:
            raise ValueError('Actual selected bow ammunition/charge preflight failed')
    effects = [f for f in target['effects'] if f.get('source_ref','').upper() == 'RDXDEF']
    defense = spec['defense']
    if defense is None:
        if effects:
            raise ValueError('Unexpected synthetic defense')
    else:
        opcode, p1, p2 = defense
        if len(effects) != 1 or effects[0]['opcode'] != opcode or effects[0]['parameters'][1] != p2:
            raise ValueError('Required exact defense opcode/mode absent')
        actual = effects[0]['parameters'][0]
        if actual not in ([p1, 0xffffffff] if opcode == 120 else [p1]):
            raise ValueError('Defense magnitude changed')
        stat = {86: (21,100),218:(88,3),159:(254,3)}.get(opcode)
        if stat and target['modified_stats'][stat[0]] != stat[1]:
            raise ValueError('Required derived defense stat absent')
    return dict(sender_runtime_id=sender['runtime_id'], target_runtime_id=target['runtime_id'],
                equipped=inventory['equipped'], ability=inventory['equipped_header'],
                weapon=items[35]['resref'], ammo=items.get(11), defense_effects=effects)


def validate_capture(folder, spec, repeats, log_path):
    data = read(folder/'query-result.json')
    if (data.get('schema') != 'bg-redux-query-side-effects-native/1' or not data.get('completed')
            or data.get('case_id') != spec['id'] or data.get('repeats') != repeats):
        raise ValueError('Native completion/case/repeat identity mismatch')
    initialized = read(folder/'initialized.state.json')
    guard = runtime_guard(spec, initialized)
    if data.get('sender_runtime_id') != guard['sender_runtime_id'] or data.get('target_runtime_id') != guard['target_runtime_id']:
        raise ValueError('Native sender/target does not match initialized snapshot')
    parsed = data.get('parsed_queries', [])
    if len(parsed) != 2:
        raise ValueError('Fixed query parser evidence missing')
    for row, expression, trigger_id in zip(parsed, QUERIES, (0xec,0xf2)):
        if (row.get('expression') != expression or row.get('trigger_id') != trigger_id or row.get('hand') != 1
                or row.get('target_count') != 1 or row.get('target_runtime_id') != guard['target_runtime_id']):
            raise ValueError('Parsed EE trigger/MAINHAND/Player2 evidence changed')
    expected = [('True()',0),('False()',0)]+[(q,i) for i in range(1,repeats+1) for q in QUERIES]
    observations = data.get('observations', [])
    if len(observations) != len(expected):
        raise ValueError('Repeated query observation coverage incomplete')
    previous = initialized
    mutation_rows, values = [], {q:[] for q in QUERIES}
    for call, (row, (expression, repetition)) in enumerate(zip(observations, expected), 1):
        if (row.get('call') != call or row.get('expression') != expression or row.get('repetition') != repetition
                or type(row.get('value')) is not int or row['value'] not in (0,1)):
            raise ValueError('Observation order/Boolean value mismatch')
        before = read(safe_member(folder, row['before']))
        after = read(safe_member(folder, row['after']))
        require_state(before); require_state(after)
        if before != previous:
            raise ValueError('State discontinuity between captured query calls')
        changes = diff(before,after)
        if row.get('native_equal') is not (not changes):
            raise ValueError('Native equality flag contradicts independent state diff')
        if changes:
            mutation_rows.append(dict(call=call,expression=expression,repetition=repetition,changes=changes))
        if expression == 'True()' and row['value'] != 1 or expression == 'False()' and row['value'] != 0:
            raise ValueError('Positive/negative evaluator control failed')
        if expression in values:
            values[expression].append(row['value'])
        previous = after
    final = read(folder/'final.state.json'); require_state(final)
    if final != previous:
        raise ValueError('Final snapshot differs from last captured query state')
    # The frozen implementations log only after resolving valid Actor sender/target.
    # A parse failure returning zero must not masquerade as a called stub.
    log = log_path.read_text(errors='replace')
    for name in ('WeaponEffectiveVs','WeaponCanDamage'):
        if log.count(name+' has not been implemented yet!') != repeats:
            raise ValueError('Expected actual resolved stub invocation count missing: '+name)
    return dict(runtime_preflight=guard, observations=len(observations), repeated_queries=2*repeats,
                predicate_values=values, expected_frozen_stub_values=all(v == 0 for rows in values.values() for v in rows),
                mutation_observations=mutation_rows, collected_state_unchanged=not mutation_rows,
                final_equals_initialized=final == initialized, hidden_state_unchanged=None, scope=LIMIT)


def check_build(project, receipt_path):
    receipt = read(receipt_path)
    binary = Path(receipt['binary'])
    if receipt.get('schema') != 'bg-redux-query-side-effect-build/1' or receipt['process'].get('exit_code') != 0 or receipt['process'].get('timed_out'):
        raise ValueError('External side-effect host build failed/incomplete')
    if not receipt.get('engine_dll_unchanged') or receipt.get('binary_sha256') != sha(binary):
        raise ValueError('External side-effect host binary drift')
    if receipt['engine_dll_sha256'] != sha(project/'phase0-local/build/gemrb/libgemrb_core.dll'):
        raise ValueError('External host engine DLL mismatch')
    if receipt['compiler_sha256'] != sha(project/'phase0-local/toolchain/msys64/ucrt64/bin/g++.exe'):
        raise ValueError('External host compiler mismatch')
    for source, expected in receipt['sources'].items():
        if sha(Path(source)) != expected:
            raise ValueError('External observer source drift: '+source)
    return binary, receipt


def verify_game(project):
    manifest = read(project/'docs/compatibility/evidence/bg2ee-copy-manifest.json')
    game = project/'phase0-local/bg2ee-clean'
    for entry in manifest['files']:
        path = safe_member(game,entry['path'])
        if path.stat().st_size != entry['bytes'] or sha(path) != entry['sha256']:
            raise ValueError('Reference game data drift: '+entry['path'])
    return dict(files_checked=len(manifest['files']), manifest_sha256=sha(project/'docs/compatibility/evidence/bg2ee-copy-manifest.json'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--build-receipt', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=8)
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args(argv)
    if not 1 <= args.repeats <= 32 or args.timeout <= 0:
        parser.error('Repeats in [1,32] and positive timeout required')
    project = args.project_root.resolve()
    sys.path.insert(0,str(project/'tools/phase0'))
    local = project/'phase0-local'
    output = local/'results'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-query-side-effects-'+uuid.uuid4().hex[:8])
    output.mkdir(parents=True)
    report = dict(schema='bg-redux-query-side-effects/1', directory=str(output), hostname=socket.gethostname(),
                  captured_utc=datetime.now(timezone.utc).isoformat(), repeats=args.repeats, cases=[],
                  verdict='failed', scope=LIMIT, original_runtime_executed=False)
    before = None
    try:
        report['preflight'] = preflight(project)
        report['game'] = verify_game(project)
        from equipped_defenses import CASES, construct, observe, validate_observation
        from harness import environment
        from save_harness import member
        before = protected(project); write(output/'protected-before.json', before)
        binary, receipt = check_build(project,args.build_receipt.resolve())
        frozen = output/'driver'; frozen.mkdir()
        shutil.copy2(binary,frozen/binary.name)
        shutil.copy2(args.build_receipt,frozen/'build.json')
        for source in receipt['sources']:
            path = Path(source); target = frozen/'sources'/path.name; target.parent.mkdir(exist_ok=True)
            shutil.copy2(path,target)
        for path in (Path(__file__).resolve(), project/'tools/phase0/equipped_defenses.py',project/'tools/phase0/script_query_probe.py',
                     project/'tools/phase0/baseline_runner.py'):
            shutil.copy2(path,frozen/'sources'/path.name)
        report['driver'] = dict(receipt=receipt, frozen_files=files_manifest(frozen))
        for spec in CASES:
            case = dict(spec=spec, verdict='failed'); report['cases'].append(case)
            folder = output/spec['id']; folder.mkdir()
            try:
                fixture, override, construction = construct(folder,spec)
                validate_observation(spec,observe(member(fixture,'gam')))
                case['construction'] = construction
                config = dict(GameType='bg2ee',GamePath=local/'bg2ee-clean',GemRBPath=project/'gemrb/gemrb',
                              PluginsPath=local/'build/gemrb/plugins',CachePath=folder/'cache',SavePath=folder/'engine-profile',
                              UseAsLibrary=1,AudioDriver='none',GameLanguagePath='lang/en_US',ModPath=override,
                              Logging=1,LogColor=0,PathfinderThreadsCount=0,PathfinderMainThreadMode='immediate')
                (folder/'cache').mkdir(); (folder/'engine-profile').mkdir()
                config_path = folder/'probe.cfg'
                config_path.write_text(''.join(f'{key}={str(value).replace(chr(92),chr(47))}\n' for key,value in config.items()))
                captures = folder/'capture'; captures.mkdir()
                command = [str(frozen/binary.name),'--config',str(config_path),'--output',str(captures),'--save-dir',str(fixture),
                           '--case-id',spec['id'],'--repeats',str(args.repeats)]
                env = environment(folder); env['PYTHONDONTWRITEBYTECODE']='1'
                case['process'] = execute(command,local/'build',env,folder/'process.log',args.timeout)
                if case['process']['exit_code'] != 0 or case['process']['timed_out']:
                    raise ValueError('Native query observation did not complete')
                case['observation'] = validate_capture(captures,spec,args.repeats,folder/'process.log')
                if files_manifest(fixture) != construction['input_files']:
                    raise ValueError('Disposable fixture changed during read-only query test')
                case['verdict'] = ('unexpected-frozen-query-values' if not case['observation']['expected_frozen_stub_values']
                                   else ('characterized' if case['observation']['collected_state_unchanged'] else 'collected-state-mutation'))
            except (OSError, ValueError, KeyError, TypeError) as error:
                case['error'] = str(error)
            write(folder/'result.json',case); write(output/'result.json',report)
            print(spec['id'],case['verdict'],case.get('error',''),flush=True)
        if all(case['verdict'] == 'characterized' for case in report['cases']) and len(report['cases']) == 8:
            report['verdict'] = 'characterized-no-collected-state-mutation'
        elif len(report['cases']) == 8 and all(case['verdict'] in ('characterized','collected-state-mutation') for case in report['cases']):
            report['verdict'] = 'collected-state-mutation'
    except (OSError, ValueError, KeyError, TypeError, ImportError) as error:
        report['error'] = str(error)
    finally:
        if before is not None:
            try:
                after = protected(project); write(output/'protected-after.json',after)
                report['preservation'] = {key:before[key] == after[key] for key in before}
                if not all(report['preservation'].values()):
                    raise ValueError('Engine source/binary/original fixture changed')
                report['game_after'] = verify_game(project)
            except (OSError, ValueError) as error:
                report['verdict']='failed';report['preservation_error']=str(error)
        report['completed_utc']=datetime.now(timezone.utc).isoformat()
        write(output/'result.json',report)
        write(output/'artifact-manifest.json',dict(files=files_manifest(output)))
    print(json.dumps(dict(directory=str(output),verdict=report['verdict'],cases=len(report['cases']),scope=LIMIT),indent=2))
    return 0 if report['verdict'] == 'characterized-no-collected-state-mutation' else 1


if __name__ == '__main__':
    raise SystemExit(main())
