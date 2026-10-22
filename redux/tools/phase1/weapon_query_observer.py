"""Build or run an isolated Phase 1 external six-hand query observer.

Compilation/owned bounded launches occur only on explicit coordinator command.
Phase 0 engine/source/fixture inventories are pinned separately from candidate
source/core/plugins. All outputs are new private directories.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib
import json
import math
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import uuid
import private_game

from weapon_oracle_fixtures import load_api, equipment_guard
from weapon_query_validation import LIMIT, bind_original_reference, manifest, member, read, sha, validate_capture, verify_original_artifacts


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def phase0(project):
    api = load_api(project)
    api.baseline_runner = importlib.import_module('baseline_runner')
    api.query_side_effects = importlib.import_module('query_side_effects')
    for name in ('baseline_runner', 'query_side_effects'):
        if not Path(getattr(api, name).__file__).resolve().is_relative_to(project/'tools/phase0'):
            raise ValueError('Phase 0 validator import escaped project root')
    return api


def candidate_inventory(source, build):
    files = subprocess.check_output(['git', '-C', str(source), 'ls-files', '-z'])
    sources = {}
    for raw in files.split(b'\0'):
        if not raw:
            continue
        name = raw.decode('utf-8')
        if name.startswith('redux/') or name == 'README_BG_REDUX.md':
            continue
        path = member(source, name)
        if not path.is_file():
            raise ValueError('Tracked candidate source missing: '+name)
        sources[name] = dict(bytes=path.stat().st_size, sha256=sha(path))
    dlls = list((build/'gemrb').glob('*.dll'))+list((build/'gemrb/plugins').glob('*.dll'))
    binaries = dlls+[build/'gemrb/core/libgemrb_core.dll.a', build/'config.h']
    if not (build/'gemrb/libgemrb_core.dll').is_file() or not list((build/'gemrb/plugins').glob('*.dll')):
        raise ValueError('Candidate core/plugins missing')
    return dict(source=sources, binaries={str(p.relative_to(build)): dict(bytes=p.stat().st_size, sha256=sha(p))
                                        for p in sorted(binaries)})


def new_output(root, tag):
    output = root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+tag+'-'+uuid.uuid4().hex[:8])
    output.mkdir(parents=True, exist_ok=False)
    return output


def frozen_copy(path, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    before = sha(path); shutil.copy2(path, destination)
    if sha(path) != before or sha(destination) != before:
        raise ValueError('Source changed while freezing: '+str(path))
    return dict(source=str(path), frozen=str(destination), sha256=before)


def required_sources(kind='six-hand-query'):
    tool = Path(__file__).resolve().parent
    if Path(private_game.__file__).resolve() != tool/'private_game.py':
        raise ValueError('Private game helper import escaped tool directory')
    names = ['native/weapon_query_probe.cpp', 'native/phase0_save_probe_snapshot.cpp',
             'weapon_query_observer.py', 'weapon_query_validation.py', 'weapon_oracle_fixtures.py', 'private_game.py']
    if kind == 'inventory-mutation-journey':
        names += ['native/weapon_inventory_journey.cpp', 'weapon_inventory_journey.py']
    elif kind != 'six-hand-query':
        raise ValueError('Unknown external observer host kind')
    return [tool/name for name in names]


def prepare_private_game(project, output):
    required_sources() # verify the imported helper identity before any use
    receipt = private_game.prepare(project/'phase0-local/bg2ee-clean', output/'private-game')
    write(output/'private-game-preparation.json', receipt)
    validate_private_game(receipt, output)
    return receipt


def validate_private_game(receipt, output):
    required_sources()
    if read(output/'private-game-preparation.json') != receipt:
        raise ValueError('Frozen private game preparation changed')
    write(output/'private-game-source-after.json', private_game.source_inventory(receipt['source']))
    validation = private_game.validate(receipt)
    write(output/'private-game-validation.json', validation)
    return validation


def result_manifest(output):
    """Hash owned outputs/root copies, without traversing shared asset links."""
    output = Path(output)
    wrapper = output/'private-game'
    files = {}
    for parent, directories, names in os.walk(output, followlinks=False):
        directories[:] = [name for name in directories if Path(parent)/name != wrapper]
        for name in names:
            path = Path(parent)/name
            files[path.relative_to(output).as_posix()] = dict(bytes=path.stat().st_size, sha256=sha(path))
    if wrapper.is_dir():
        for path in wrapper.iterdir():
            if path.is_file() and not path.is_symlink():
                files[path.relative_to(output).as_posix()] = dict(bytes=path.stat().st_size, sha256=sha(path))
    return dict(sorted(files.items()))


def build_host(args):
    project, source, build = args.project_root.resolve(), args.engine_source_root.resolve(), args.engine_build_root.resolve()
    output = args.output_dir.resolve()
    if output.exists():
        raise ValueError('External build destination must be new')
    output.mkdir(parents=True)
    report = dict(schema='bg-redux-phase1-weapon-query-build/1', directory=str(output),
                  project=str(project), engine_source_root=str(source), engine_build_root=str(build),
                  kind='six-hand-query', verdict='failed')
    before = candidate = None
    try:
        api = phase0(project); baseline = api.baseline_runner
        report['phase0_preflight'] = baseline.preflight(project)
        before = baseline.protected(project); write(output/'phase0-before.json', before)
        candidate = candidate_inventory(source, build); write(output/'candidate-before.json', candidate)
        tool = Path(__file__).resolve().parent
        serializer = tool/'native/phase0_save_probe_snapshot.cpp'
        if sha(serializer) != sha(project/'tools/phase0/native/save_probe.cpp'):
            raise ValueError('Frozen serializer differs from read-only Phase 0 original')
        files = required_sources()
        report['sources'] = {str(p): frozen_copy(p, output/'sources'/p.name) for p in files}
        binary = output/'Redux_phase1_weapon_query.exe'
        prefix = project/'phase0-local/toolchain/msys64/ucrt64'
        compiler = prefix/'bin/g++.exe'
        command = [str(compiler), '-std=gnu++17', '-g', '-O0', '-DHAVE_CONFIG_H', '-DUSE_OPENGL_API',
                   '-D_USE_MATH_DEFINES', '-DFMT_HEADER_ONLY', '-DFMT_USE_CONSTEVAL=0', '-DFMT_EXCEPTIONS=0',
                   '-DFMT_UNICODE=1', '-fno-strict-aliasing']
        for folder in [build, source/'gemrb/includes', source/'gemrb/core', source/'platforms/Windows',
                       build/'gemrb/includes', prefix/'include/SDL2', prefix/'include/python3.14', source/'includes/fmt']:
            command += ['-I', str(folder)]
        command += [str(output/'sources/weapon_query_probe.cpp'), str(build/'gemrb/core/libgemrb_core.dll.a'),
                    str(prefix/'lib/libiconv.dll.a'), '-lshlwapi', '-o', str(binary)]
        env = os.environ.copy(); env['PATH'] = str(prefix/'bin')+os.pathsep+env.get('PATH', '')
        report['process'] = baseline.execute(command, project, env, output/'build.log', args.timeout)
        report.update(binary=str(binary), compiler=str(compiler), compiler_sha256=sha(compiler),
                      candidate_inventory=candidate, serializer_origin_sha256=sha(project/'tools/phase0/native/save_probe.cpp'))
        if report['process']['exit_code'] != 0 or report['process']['timed_out'] or not binary.is_file():
            raise ValueError('External observer build did not complete')
        report['binary_sha256'] = sha(binary)
        report['verdict'] = 'built-not-executed'
    except Exception as error:
        report['error'] = str(error)
    finally:
        try:
            if before is not None:
                after = baseline.protected(project); write(output/'phase0-after.json', after)
                report['phase0_preservation'] = {key: before[key] == after[key] for key in before}
                if not all(report['phase0_preservation'].values()):
                    raise ValueError('Pinned Phase 0 inventory changed')
            if candidate is not None:
                after = candidate_inventory(source, build); write(output/'candidate-after.json', after)
                report['candidate_preserved'] = after == candidate
                if not report['candidate_preserved']:
                    raise ValueError('Candidate source/binaries changed')
        except Exception as error:
            report['verdict'] = 'failed'; report['preservation_error'] = str(error)
        report['completed_utc'] = datetime.now(timezone.utc).isoformat()
        write(output/'build.json', report); write(output/'artifact-manifest.json', dict(files=manifest(output)))
    print(json.dumps(dict(directory=str(output), verdict=report['verdict']), indent=2), flush=True)
    return 0 if report['verdict'] == 'built-not-executed' else 1


def check_build(receipt_path, project, source, build):
    receipt = read(receipt_path)
    if (receipt.get('schema') != 'bg-redux-phase1-weapon-query-build/1' or receipt.get('verdict') != 'built-not-executed'
            or Path(receipt['project']).resolve() != project or Path(receipt['engine_source_root']).resolve() != source
            or Path(receipt['engine_build_root']).resolve() != build or not receipt.get('candidate_preserved')
            or receipt.get('phase0_preservation') != dict(source=True, binaries=True, fixture=True)
            or receipt.get('process', {}).get('exit_code') != 0 or receipt['process'].get('timed_out')):
        raise ValueError('External build receipt failed/stale/source mismatch')
    if sha(receipt['binary']) != receipt['binary_sha256'] or sha(receipt['compiler']) != receipt['compiler_sha256']:
        raise ValueError('External build binary/compiler changed')
    if receipt['candidate_inventory'] != candidate_inventory(source, build):
        raise ValueError('Candidate source/binaries drifted since observer build')
    expected_sources = {str(path) for path in required_sources(receipt.get('kind', 'six-hand-query'))}
    if set(receipt.get('sources', {})) != expected_sources:
        raise ValueError('External observer required source inventory differs (fresh build required)')
    for path, row in receipt['sources'].items():
        if sha(path) != row['sha256'] or sha(row['frozen']) != row['sha256']:
            raise ValueError('External observer source changed: '+path)
    return receipt


def check_preparation(path, selected_ids=None):
    prep = read(path)
    if (prep.get('schema') != 'bg-redux-phase1-weapon-oracle-preparation/1'
            or prep.get('phase') != 'prepared-not-executed' or prep.get('executed') is not False):
        raise ValueError('Fixture preparation failed/incomplete')
    rows = prep.get('cases', [])
    ids = [row['spec']['id'] for row in rows]
    if not rows or len(ids) != len(set(ids)) or len({r['script'] for r in rows}) != len(rows):
        raise ValueError('Prepared case/script identity duplicate/missing')
    if selected_ids and (len(selected_ids) != len(set(selected_ids)) or set(selected_ids)-set(ids)):
        raise ValueError('Unknown/duplicate selected cases')
    chosen = [row for row in rows if not selected_ids or row['spec']['id'] in selected_ids]
    for row in chosen:
        if row['nonce'] != prep['nonce'] or manifest(Path(row['fixture'])) != row['fixture_files']:
            raise ValueError('Prepared fixture nonce/manifest drift')
        if sha(row['script_path']) != row['script_sha256']:
            raise ValueError('Prepared case script drift')
    return prep, chosen


def require_process(process):
    if process.get('exit_code') != 0 or process.get('timed_out') is not False:
        raise ValueError('Native observer failed/timed out/incomplete receipt')


def observation_verdict(observation, reference, rng_control_draw=False):
    if observation['rng_control_draw_call'] != (3 if rng_control_draw else None):
        raise ValueError('Native RNG controlled-draw marker differs from requested mode')
    if not observation['collected_state_unchanged']:
        return 'collected-state-mutation'
    if observation['rng_unchanged'] is False:
        return 'calling-thread-rng-mutation'
    if rng_control_draw:
        return 'rng-control-not-detected'
    if not observation['stable_values']:
        return 'unstable-query-values'
    if observation['original_match'] is False:
        return 'original-differences'
    return 'original-match' if reference else 'observed-not-compared'


def run_queries(args):
    project, source, build = args.project_root.resolve(), args.engine_source_root.resolve(), args.engine_build_root.resolve()
    output = new_output(args.results_root.resolve(), 'phase1-weapon-query')
    report = dict(schema='bg-redux-phase1-weapon-query-run/1', directory=str(output), hostname=socket.gethostname(),
                  started_utc=datetime.now(timezone.utc).isoformat(), repeats=args.repeats, cases=[],
                  require_rng_observed=args.require_rng_observed, rng_control_draw=args.rng_control_draw,
                  verdict='failed', execution='not-run', compatibility='not-compared', scope=LIMIT)
    before = candidate = game_before = private = None
    try:
        api = phase0(project); baseline = api.baseline_runner
        report['phase0_preflight'] = baseline.preflight(project)
        before = baseline.protected(project); write(output/'phase0-before.json', before)
        candidate = candidate_inventory(source, build); write(output/'candidate-before.json', candidate)
        game_before = api.query_side_effects.verify_game(project); report['game_before'] = game_before
        receipt = check_build(args.build_receipt.resolve(), project, source, build)
        if receipt.get('kind') != 'six-hand-query':
            raise ValueError('Wrong external host kind')
        private = prepare_private_game(project, output)
        report['private_game_preparation_sha256'] = sha(output/'private-game-preparation.json')
        prep, rows = check_preparation(args.preparation.resolve(), args.cases)
        report['selected_cases'] = [r['spec']['id'] for r in rows]
        report['unselected_cases'] = [r['spec']['id'] for r in prep['cases'] if r not in rows]
        report['preparation_sha256'] = sha(args.preparation)
        frozen_copy(args.preparation, output/'preparation.json')
        driver = output/'driver'; driver.mkdir()
        binary = driver/Path(receipt['binary']).name
        frozen_copy(Path(receipt['binary']), binary)
        frozen_copy(args.build_receipt, driver/'build.json')
        for row in receipt['sources'].values():
            frozen_copy(Path(row['frozen']), driver/'sources'/Path(row['frozen']).name)
        references = {}
        for reference_path in args.original_receipts or []:
            raw = read(reference_path); identity = raw.get('case_id')
            if identity in references or identity not in {r['spec']['id'] for r in rows}:
                raise ValueError('Duplicate/unselected original reference')
            row = next(r for r in rows if r['spec']['id'] == identity)
            reference = bind_original_reference(api, reference_path, args.preparation, prep, row)
            reference['capture_artifacts'] = verify_original_artifacts(reference_path, prep, row)
            folder = output/'original-references'/identity; folder.mkdir(parents=True)
            shutil.copytree(reference_path.parent, folder/'capture')
            frozen_inventory = manifest(folder/'capture'); frozen_inventory.pop('artifact-manifest.json', None)
            if frozen_inventory != reference['capture_artifacts']['files']:
                raise ValueError('Original reference changed while freezing')
            references[identity] = reference
        for row in rows:
            identity = row['spec']['id']; case = dict(id=identity, verdict='failed', execution='not-run')
            report['cases'].append(case)
            folder = output/identity; folder.mkdir()
            try:
                fixture = folder/'input'; shutil.copytree(row['fixture'], fixture)
                if manifest(fixture) != row['fixture_files']:
                    raise ValueError('Copied prepared fixture differs')
                gam = [p for p in fixture.iterdir() if p.name.lower() == 'baldur.gam']
                if len(gam) != 1:
                    raise ValueError('Fixture GAM missing/ambiguous')
                _, pc = api.equipped_defenses.embedded(gam[0].read_bytes(), 0)
                equipment_guard(pc, row['spec'])
                if pc[0x248:0x250].upper() != row['script'].encode().upper():
                    raise ValueError('Prepared unique script assignment differs')
                override = folder/'override'; override.mkdir()
                frozen_copy(Path(row['script_path']), override/(row['script']+'.bcs'))
                if sha(override/(row['script']+'.bcs')) != row['script_sha256']:
                    raise ValueError('Copied fixed script differs')
                for directory in ('cache', 'engine-profile', 'capture'):
                    (folder/directory).mkdir()
                validate_private_game(private, output)
                config = dict(GameType='bg2ee', GamePath=Path(private['game']), GemRBPath=source/'gemrb',
                              PluginsPath=build/'gemrb/plugins', CachePath=folder/'cache', SavePath=folder/'engine-profile',
                              UseAsLibrary=1, AudioDriver='none', GameLanguagePath='lang/en_US', ModPath=override,
                              Logging=1, LogColor=0, PathfinderThreadsCount=0, PathfinderMainThreadMode='immediate')
                config_path = folder/'probe.cfg'
                config_path.write_text(''.join(f'{key}={str(value).replace(chr(92), chr(47))}\n' for key, value in config.items()), encoding='utf-8')
                command = [str(binary), '--config', str(config_path), '--output', str(folder/'capture'),
                           '--save-dir', str(fixture), '--case-id', identity, '--repeats', str(args.repeats)]
                if args.rng_control_draw:
                    command += ['--rng-control-draw', '1']
                env = api.harness.environment(folder)
                prefix = project/'phase0-local/toolchain/msys64/ucrt64'
                env['PATH'] = os.pathsep.join([str(build/'gemrb'), str(prefix/'bin'), env.get('PATH', '')])
                env['PYTHONDONTWRITEBYTECODE'] = '1'
                case['process'] = baseline.execute(command, build, env, folder/'process.log', args.timeout)
                case['private_game_validation'] = validate_private_game(private, output)
                require_process(case['process'])
                case['execution'] = 'passed'
                reference = references.get(identity)
                observation = validate_capture(folder/'capture', row, prep['item_metadata'], args.repeats,
                                               reference['values'] if reference else None, args.require_rng_observed)
                case['observation'] = observation
                if reference:
                    case['original_reference'] = reference
                if manifest(fixture) != row['fixture_files']:
                    raise ValueError('Input fixture changed during read-only queries')
                case['verdict'] = observation_verdict(observation, reference, args.rng_control_draw)
            except Exception as error:
                case['error'] = str(error)
            write(folder/'result.json', case); write(output/'result.json', report)
            print(identity, case['verdict'], case.get('error', ''), flush=True)
        if all(c['verdict'] in ('original-match', 'original-differences', 'observed-not-compared') for c in report['cases']) and len(report['cases']) == len(rows):
            report['execution'] = 'passed'
            report['compatibility'] = ('differences' if any(c['verdict'] == 'original-differences' for c in report['cases'])
                                       else 'not-fully-compared' if any(c['verdict'] == 'observed-not-compared' for c in report['cases'])
                                       else 'matched-selected-original-cases')
            report['verdict'] = report['compatibility']
    except Exception as error:
        report['error'] = str(error)
    finally:
        if private is not None:
            try:
                report['private_game_validation'] = validate_private_game(private, output)
            except Exception as error:
                report['private_game_preservation_error'] = str(error)
                report['private_game_validation'] = dict(verdict='failed', error=str(error))
                report['verdict'] = 'failed'
        if report['cases']:
            report['execution'] = ('passed' if all(c.get('process', {}).get('exit_code') == 0
                                   and c.get('process', {}).get('timed_out') is False for c in report['cases']) else 'failed')
            report['validation'] = ('passed' if all(c['verdict'] in ('original-match', 'original-differences', 'observed-not-compared')
                                     for c in report['cases']) else 'failed')
            observed = [c['observation'] for c in report['cases'] if 'observation' in c]
            report['collected_state_status'] = ('not-observed' if not observed else 'mutation-observed'
                                                if any(o['mutation_observations'] for o in observed)
                                                else 'unchanged-in-completed-captures')
        if 'private_game_preservation_error' in report:
            report['validation'] = 'failed'
        try:
            if before is not None:
                after = baseline.protected(project); write(output/'phase0-after.json', after)
                report['phase0_preservation'] = {key: before[key] == after[key] for key in before}
                if not all(report['phase0_preservation'].values()):
                    raise ValueError('Pinned Phase 0 source/binaries/fixture changed')
            if candidate is not None:
                after = candidate_inventory(source, build); write(output/'candidate-after.json', after)
                report['candidate_preserved'] = candidate == after
                if not report['candidate_preserved']:
                    raise ValueError('Candidate source/binaries changed during observer run')
            if game_before is not None:
                report['game_after'] = api.query_side_effects.verify_game(project)
                if report['game_after'] != game_before:
                    raise ValueError('Clean game inventory changed')
        except Exception as error:
            report['preservation_error'] = str(error); report['verdict'] = 'failed'
        report['completed_utc'] = datetime.now(timezone.utc).isoformat()
        write(output/'result.json', report)
        (output/'REPORT.md').write_text(f'Phase 1 weapon query observer: {report["verdict"]}\n\nExecution: {report["execution"]}. Compatibility: {report["compatibility"]}.\n\n{LIMIT}\n', encoding='utf-8')
        write(output/'artifact-manifest.json', dict(files=result_manifest(output),
            scope='Owned outputs and private root copies; shared asset links excluded'))
    print(json.dumps(dict(directory=str(output), verdict=report['verdict']), indent=2), flush=True)
    return 0 if report['verdict'] in ('matched-selected-original-cases', 'not-fully-compared') else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    for name in ('build', 'run'):
        item = sub.add_parser(name)
        item.add_argument('--project-root', type=Path, required=True)
        item.add_argument('--engine-source-root', type=Path, required=True)
        item.add_argument('--engine-build-root', type=Path, required=True)
        item.add_argument('--timeout', type=float, default=240 if name == 'build' else 120)
        if name == 'build':
            item.add_argument('--output-dir', type=Path, required=True)
        else:
            item.add_argument('--results-root', type=Path, required=True)
            item.add_argument('--build-receipt', type=Path, required=True)
            item.add_argument('--preparation', type=Path, required=True)
            item.add_argument('--cases', nargs='+')
            item.add_argument('--repeats', type=int, default=8)
            item.add_argument('--original-receipts', nargs='+', type=Path)
            item.add_argument('--require-rng-observed', action='store_true')
            item.add_argument('--rng-control-draw', action='store_true',
                              help='Deliberate failing control: one real draw during first weapon-query interval')
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0 or args.mode == 'run' and not 1 <= args.repeats <= 32:
        parser.error('Positive timeout and repeats in [1,32] required')
    return build_host(args) if args.mode == 'build' else run_queries(args)


if __name__ == '__main__':
    raise SystemExit(main())
