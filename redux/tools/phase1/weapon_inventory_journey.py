"""Explicit build/run and evidence ingestion for an external inventory journey.

Never repairs engine caches. Deliberate API mutations are separated from
read-only query calls. No worker invocation of build/run is required by tests.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import math
import os
from pathlib import Path
import shutil

import weapon_query_observer as observer
import weapon_query_validation as evidence


STEPS = [
    ('00-initial', 'sw1h01'), ('01-remove', None), ('02-restore', 'sw1h01'),
    ('03-shield', 'shld01'), ('04-create-normal', 'sw1h01'), ('05-create-plus', 'sw1h02'),
    ('06-reset-normal', 'sw1h01'), ('07-transform-plus', 'sw1h02'),
    ('08-reset-plus', 'sw1h02'), ('09-create-normal', 'sw1h01')]


def validate_journey(folder, row, metadata, repeats):
    return _validate_journey(folder, row, metadata, repeats, allow_incomplete_prefix=False)


def review_completed_prefix(folder, row, metadata, repeats):
    """Forensic review only; never promotes an incomplete native run to success."""
    return _validate_journey(folder, row, metadata, repeats, allow_incomplete_prefix=True)


def _validate_journey(folder, row, metadata, repeats, allow_incomplete_prefix):
    folder = Path(folder); data = evidence.read(folder/'journey.json')
    complete = data.get('completed') is True and not data.get('error')
    if (data.get('schema') != 'bg-redux-phase1-inventory-journey-native/1'
            or data.get('case_id') != row['spec']['id'] or data.get('repeats') != repeats
            or not complete and not (allow_incomplete_prefix and data.get('completed') is False and data.get('error'))):
        raise ValueError('Native journey incomplete/wrong identity')
    parsed = data.get('parsed_queries', [])
    if len(parsed) != 6:
        raise ValueError('Six parsed queries missing')
    for index, query in enumerate(parsed):
        if (query.get('expression') != evidence.QUERIES[index] or query.get('hand') != index//2+1
                or query.get('trigger_id') != (0xf2 if index % 2 else 0xec) or query.get('target_count') != 1
                or query.get('target_runtime_id') != data['target_runtime_id']):
            raise ValueError('Journey actual query parser/target mismatch')
    expected_steps = STEPS if complete else STEPS[:len(data.get('steps', []))]
    if (not expected_steps or not complete and len(expected_steps) >= len(STEPS)
            or [(s.get('id'), s.get('expected_off')) for s in data.get('steps', [])] != expected_steps):
        raise ValueError('Actual mutation journey coverage/order incomplete')
    previous_state = previous_cache = None
    results = []
    for index, ((identity, expected_off), step) in enumerate(zip(expected_steps, data['steps'])):
        location = folder/identity
        if evidence.read(location/'step.json') != step or step.get('completed') is not True:
            raise ValueError('Journey step receipt contradicts root/completion')
        before_mutation = evidence.read(location/'before-mutation.state.json')
        cache_before_mutation = evidence.read(location/'before-mutation.weapons.json')
        state = evidence.read(location/'initialized.state.json'); cache = evidence.read(location/'initialized.weapons.json')
        evidence.require_state(before_mutation); evidence.require_state(state)
        if index and (before_mutation != previous_state or cache_before_mutation != previous_cache):
            raise ValueError('State/cache continuity broken between journey stages')
        if not index and (before_mutation != state or cache_before_mutation != cache):
            raise ValueError('Initial journey stage unexpectedly mutates')
        if len(state['party']) != 2 or state['party'][0]['runtime_id'] != data['sender_runtime_id'] or state['party'][1]['runtime_id'] != data['target_runtime_id']:
            raise ValueError('Journey sender/target identity changed')
        sender, target = state['party']; inventory = sender['inventory']
        items = {item['slot']: item['resref'].lower() for item in inventory['items'] if item['slot'] != inventory['fist_slot']}
        expected_items = {35: 'sw1h02'} | ({9: expected_off} if expected_off else {})
        if (items != expected_items or inventory['equipped'] != 0 or inventory['equipped_header'] != 0
                or len({item['slot'] for item in inventory['items']}) != len(inventory['items'])):
            raise ValueError('Actual mutation did not produce exact main/off-hand inventory')
        dynamic_row = dict(row, spec=row['spec'] | dict(off=expected_off))
        if not index:
            evidence.runtime_guard(dynamic_row, metadata, state, cache)
            initial_target = target
        elif target != initial_target:
            raise ValueError('Inventory journey unexpectedly changed target state')
        cache_issue = None
        try:
            evidence.runtime_guard(dynamic_row, metadata, state, cache)
        except ValueError as error:
            # Exact inventory and target were checked independently above.
            # Preserve mismatching cache metadata as the observation, never repair it.
            cache_issue = str(error)
        state_after_mutation, cache_after_mutation = state, cache
        expected_order = [('True()', 0), ('False()', 0)]+[(q, r) for r in range(1, repeats+1) for q in evidence.QUERIES]
        if len(step.get('observations', [])) != len(expected_order):
            raise ValueError('Journey repeated query coverage incomplete')
        values = {q: [] for q in evidence.QUERIES}; mutations = []
        expected_files = {'before-mutation.state.json', 'before-mutation.weapons.json',
                          'initialized.state.json', 'initialized.weapons.json', 'final.state.json', 'final.weapons.json', 'step.json'}
        if identity == '07-transform-plus':
            action = evidence.read(location/'transform-action.json')
            if (action.get('parsed') is not True or action.get('action_id') != 356 or action.get('has_objects') is not False
                    or action.get('expression') != 'TransformItem("sw1h01","sw1h02")'
                    or action.get('old_item', '').lower() != 'sw1h01' or action.get('new_item', '').lower() != 'sw1h02'
                    or type(action.get('target_count')) is not int or action['target_count'] < 1
                    or action.get('resolved_runtime_id') != data['sender_runtime_id']
                    or type(action.get('flags')) is not int or action['flags'] & 0x2000):
                raise ValueError('Actual TransformItem action/implicit-sender resolution differs')
            expected_files.add('transform-action.json')
        for call, (query, (expression, repetition)) in enumerate(zip(step['observations'], expected_order), 1):
            if (query.get('call') != call or query.get('expression') != expression or query.get('repetition') != repetition
                    or type(query.get('value')) is not int or query['value'] not in (0, 1)):
                raise ValueError('Journey query call/order/Boolean mismatch')
            streams = {}
            for key, side, surface in [('before', 'before', 'state'), ('after', 'after', 'state'),
                                       ('weapons_before', 'before', 'weapons'), ('weapons_after', 'after', 'weapons')]:
                name = f'call-{call}-{side}.{surface}.json'
                if query.get(key) != name:
                    raise ValueError('Journey snapshot missing/reused identity')
                expected_files.add(name); streams[key] = evidence.read(location/name)
            evidence.require_state(streams['before']); evidence.require_state(streams['after'])
            if streams['before'] != state or streams['weapons_before'] != cache:
                raise ValueError('Journey per-query state/cache discontinuity')
            changes = evidence.diff(streams['before'], streams['after'])
            cache_changes = evidence.diff(streams['weapons_before'], streams['weapons_after'])
            if query.get('native_equal') is not (not changes) or query.get('weapons_equal') is not (not cache_changes):
                raise ValueError('Journey native equality contradicts independent diff')
            if changes or cache_changes:
                mutations.append(dict(call=call, expression=expression, changes=changes, cache_changes=cache_changes))
            if expression == 'True()' and query['value'] != 1 or expression == 'False()' and query['value'] != 0:
                raise ValueError('Journey evaluator controls failed')
            if expression in values:
                values[expression].append(query['value'])
            state, cache = streams['after'], streams['weapons_after']
        final, final_cache = evidence.read(location/'final.state.json'), evidence.read(location/'final.weapons.json')
        if final != state or final_cache != cache:
            raise ValueError('Journey final snapshot mismatch')
        if set(evidence.manifest(location)) != expected_files:
            raise ValueError('Journey raw artifact inventory missing/extra')
        results.append(dict(id=identity, route=step['route'], expected_off=expected_off, actual_inventory=items,
                            cache_coherent=cache_issue is None, cache_issue=cache_issue, cached_weapons=cache_after_mutation,
                            intentional_state_changes=evidence.diff(before_mutation, state_after_mutation),
                            intentional_cache_changes=evidence.diff(cache_before_mutation, cache_after_mutation),
                            query_values=values, stable_values=all(len(set(v)) == 1 for v in values.values()),
                            query_mutations=mutations))
        previous_state, previous_cache = final, final_cache
    return dict(native_completed=complete, native_error=data.get('error'), reviewed_completed_steps=len(results),
                expected_full_step_count=len(STEPS), partial_review_only=not complete,
                steps=results, cache_mismatch_steps=[s['id'] for s in results if not s['cache_coherent']],
                query_mutation_steps=[s['id'] for s in results if s['query_mutations']],
                unstable_query_steps=[s['id'] for s in results if not s['stable_values']],
                hidden_state_unchanged=None, scope=evidence.LIMIT,
                original_journey_parity=None)


def build_journey(args):
    project, source, build = args.project_root.resolve(), args.engine_source_root.resolve(), args.engine_build_root.resolve()
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=False)
    result = dict(schema='bg-redux-phase1-weapon-query-build/1', kind='inventory-mutation-journey', verdict='failed',
                  project=str(project), engine_source_root=str(source), engine_build_root=str(build))
    before = candidate = None
    try:
        api = observer.phase0(project); baseline = api.baseline_runner
        result['phase0_preflight'] = baseline.preflight(project)
        before = baseline.protected(project); observer.write(output/'phase0-before.json', before)
        candidate = observer.candidate_inventory(source, build); observer.write(output/'candidate-before.json', candidate)
        tool = Path(__file__).resolve().parent
        if evidence.sha(tool/'native/phase0_save_probe_snapshot.cpp') != evidence.sha(project/'tools/phase0/native/save_probe.cpp'):
            raise ValueError('Frozen Phase 0 serializer differs')
        sources = observer.required_sources('inventory-mutation-journey')
        result['sources'] = {str(p): observer.frozen_copy(p, output/'sources'/p.name) for p in sources}
        prefix = project/'phase0-local/toolchain/msys64/ucrt64'; compiler = prefix/'bin/g++.exe'
        binary = output/'Redux_inventory_journey.exe'
        command = [str(compiler), '-std=gnu++17', '-g', '-O0', '-DHAVE_CONFIG_H', '-DUSE_OPENGL_API',
                   '-D_USE_MATH_DEFINES', '-DFMT_HEADER_ONLY', '-DFMT_USE_CONSTEVAL=0', '-DFMT_EXCEPTIONS=0', '-DFMT_UNICODE=1', '-fno-strict-aliasing']
        for folder in [build, source/'gemrb/includes', source/'gemrb/core', source/'platforms/Windows', build/'gemrb/includes',
                       prefix/'include/SDL2', prefix/'include/python3.14', source/'includes/fmt']:
            command += ['-I', str(folder)]
        command += [str(output/'sources/weapon_inventory_journey.cpp'), str(build/'gemrb/core/libgemrb_core.dll.a'),
                    str(prefix/'lib/libiconv.dll.a'), '-lshlwapi', '-o', str(binary)]
        env = os.environ.copy(); env['PATH'] = str(prefix/'bin')+os.pathsep+env.get('PATH', '')
        result['process'] = baseline.execute(command, project, env, output/'build.log', args.timeout)
        result.update(binary=str(binary), compiler=str(compiler), compiler_sha256=evidence.sha(compiler), candidate_inventory=candidate)
        observer.require_process(result['process'])
        result['binary_sha256'] = evidence.sha(binary); result['verdict'] = 'built-not-executed'
    except Exception as error: result['error'] = str(error); result['verdict'] = 'failed'
    finally:
        try:
            if before is not None:
                after = baseline.protected(project); observer.write(output/'phase0-after.json', after)
                result['phase0_preservation'] = {k: before[k] == after[k] for k in before}
                if not all(result['phase0_preservation'].values()): raise ValueError('Phase 0 inventory changed')
            if candidate is not None:
                after = observer.candidate_inventory(source, build); observer.write(output/'candidate-after.json', after)
                result['candidate_preserved'] = candidate == after
                if not result['candidate_preserved']: raise ValueError('Candidate inventory changed')
        except Exception as error: result['preservation_error'] = str(error); result['verdict'] = 'failed'
        observer.write(output/'build.json', result); observer.write(output/'artifact-manifest.json', dict(files=evidence.manifest(output)))
    print(output/'build.json', result['verdict'], flush=True)
    return 0 if result['verdict'] == 'built-not-executed' else 1


def run_journey(args):
    project, source, build = args.project_root.resolve(), args.engine_source_root.resolve(), args.engine_build_root.resolve()
    output = observer.new_output(args.results_root.resolve(), 'inventory-journey')
    result = dict(schema='bg-redux-phase1-inventory-journey/1', directory=str(output), verdict='failed',
                  execution='not-run', scope=evidence.LIMIT, original_journey_parity=None)
    before = candidate = private = None
    try:
        api = observer.phase0(project); baseline = api.baseline_runner
        result['phase0_preflight'] = baseline.preflight(project)
        before = baseline.protected(project); observer.write(output/'phase0-before.json', before)
        candidate = observer.candidate_inventory(source, build); observer.write(output/'candidate-before.json', candidate)
        result['game_before'] = api.query_side_effects.verify_game(project)
        receipt = observer.check_build(args.build_receipt.resolve(), project, source, build)
        if receipt.get('kind') != 'inventory-mutation-journey': raise ValueError('Wrong external host kind')
        private = observer.prepare_private_game(project, output)
        result['private_game_preparation_sha256'] = evidence.sha(output/'private-game-preparation.json')
        prep, rows = observer.check_preparation(args.preparation.resolve(), ['02-plus-normal-pfmw'])
        row = rows[0]
        if row['spec']['main'] != 'sw1h02' or row['spec']['off'] != 'sw1h01' or row['spec']['defense'] != [120, 0, 1]:
            raise ValueError('Required isolated mutation input differs')
        result['preparation_sha256'] = evidence.sha(args.preparation)
        observer.frozen_copy(args.preparation, output/'preparation.json')
        shutil.copytree(row['fixture'], output/'input')
        if evidence.manifest(output/'input') != row['fixture_files']: raise ValueError('Copied input changed')
        override = output/'override'; override.mkdir(); observer.frozen_copy(Path(row['script_path']), override/(row['script']+'.bcs'))
        driver = output/'driver'; driver.mkdir(); binary = driver/Path(receipt['binary']).name
        observer.frozen_copy(Path(receipt['binary']), binary); observer.frozen_copy(args.build_receipt, driver/'build.json')
        for item in receipt['sources'].values(): observer.frozen_copy(Path(item['frozen']), driver/'sources'/Path(item['frozen']).name)
        for name in ('cache', 'engine-profile', 'capture'): (output/name).mkdir()
        observer.validate_private_game(private, output)
        config = dict(GameType='bg2ee', GamePath=Path(private['game']), GemRBPath=source/'gemrb',
                      PluginsPath=build/'gemrb/plugins', CachePath=output/'cache', SavePath=output/'engine-profile',
                      UseAsLibrary=1, AudioDriver='none', GameLanguagePath='lang/en_US', ModPath=override,
                      Logging=1, LogColor=0, PathfinderThreadsCount=0, PathfinderMainThreadMode='immediate')
        cfg = output/'probe.cfg'; cfg.write_text(''.join(f'{k}={str(v).replace(chr(92), chr(47))}\n' for k, v in config.items()), encoding='utf-8')
        command = [str(binary), '--config', str(cfg), '--output', str(output/'capture'), '--save-dir', str(output/'input'),
                   '--case-id', row['spec']['id'], '--repeats', str(args.repeats)]
        env = api.harness.environment(output); prefix = project/'phase0-local/toolchain/msys64/ucrt64'
        env['PATH'] = os.pathsep.join([str(build/'gemrb'), str(prefix/'bin'), env.get('PATH', '')]); env['PYTHONDONTWRITEBYTECODE'] = '1'
        result['process'] = baseline.execute(command, build, env, output/'process.log', args.timeout)
        result['private_game_validation'] = observer.validate_private_game(private, output)
        result['execution'] = ('passed' if result['process'].get('exit_code') == 0
                               and result['process'].get('timed_out') is False else 'failed')
        observer.require_process(result['process']); result['execution'] = 'passed'
        result['observation'] = validate_journey(output/'capture', row, prep['item_metadata'], args.repeats)
        observation = result['observation']
        result['verdict'] = ('query-state-mutation' if observation['query_mutation_steps'] else 'unstable-query-values'
                             if observation['unstable_query_steps'] else 'cache-mismatch-observed' if observation['cache_mismatch_steps']
                             else 'journey-observed-cache-coherent')
        if evidence.manifest(output/'input') != row['fixture_files']: raise ValueError('Immutable input changed')
    except Exception as error: result['error'] = str(error); result['verdict'] = 'failed'
    finally:
        if private is not None:
            try:
                result['private_game_validation'] = observer.validate_private_game(private, output)
            except Exception as error:
                result['private_game_preservation_error'] = str(error)
                result['private_game_validation'] = dict(verdict='failed', error=str(error))
                result['verdict'] = 'failed'
        try:
            if before is not None:
                after = baseline.protected(project); observer.write(output/'phase0-after.json', after)
                result['phase0_preservation'] = {k: before[k] == after[k] for k in before}
                if not all(result['phase0_preservation'].values()): raise ValueError('Phase 0 inventory changed')
            if candidate is not None:
                after = observer.candidate_inventory(source, build); observer.write(output/'candidate-after.json', after)
                result['candidate_preserved'] = candidate == after
                if not result['candidate_preserved']: raise ValueError('Candidate inventory changed')
            if 'game_before' in result:
                result['game_after'] = api.query_side_effects.verify_game(project)
                if result['game_before'] != result['game_after']: raise ValueError('Clean game changed')
        except Exception as error: result['preservation_error'] = str(error); result['verdict'] = 'failed'
        result['completed_utc'] = datetime.now(timezone.utc).isoformat()
        observer.write(output/'result.json', result); observer.write(output/'artifact-manifest.json', dict(
            files=observer.result_manifest(output), scope='Owned outputs and private root copies; shared asset links excluded'))
    print(output, result['verdict'], result.get('error', ''), flush=True)
    return 0 if result['verdict'] == 'journey-observed-cache-coherent' else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='mode', required=True)
    for mode in ('build', 'run'):
        item = sub.add_parser(mode)
        for name in ('project-root', 'engine-source-root', 'engine-build-root'): item.add_argument('--'+name, type=Path, required=True)
        item.add_argument('--timeout', type=float, default=240)
        if mode == 'build': item.add_argument('--output-dir', type=Path, required=True)
        else:
            for name in ('build-receipt', 'preparation', 'results-root'): item.add_argument('--'+name, type=Path, required=True)
            item.add_argument('--repeats', type=int, default=2)
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0 or args.mode == 'run' and not 1 <= args.repeats <= 8:
        parser.error('Positive finite timeout and repeats in [1,8] required')
    return build_journey(args) if args.mode == 'build' else run_journey(args)


if __name__ == '__main__': raise SystemExit(main())
