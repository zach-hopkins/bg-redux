"""Run the bounded LAB baseline; keep execution and compatibility separate."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
import unittest
import uuid

STEPS = ('units', 'capabilities', 'vanilla', 'gui')
BASELINE = 'bcb5cfaa9f19ffbe8a51f25a3c014fa344173351'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def files_manifest(folder):
    return {p.relative_to(folder).as_posix(): dict(bytes=p.stat().st_size, sha256=sha(p))
            for p in sorted(folder.rglob('*')) if p.is_file()}


def safe_member(root, relative):
    path = (root/relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Manifest member escapes root: '+relative)
    return path


def check_manifest(folder, expected):
    actual = files_manifest(folder)
    if actual != expected:
        changed = sorted(n for n in actual.keys() | expected.keys() if actual.get(n) != expected.get(n))
        raise ValueError('Required manifest mismatch: '+', '.join(changed[:12]))
    return actual


class CountsResult(unittest.TextTestResult):
    """Machine output includes setup/import failures, which testsRun alone misses."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed = 0

    def addSuccess(self, test):
        self.passed += 1
        super().addSuccess(test)


def run_units(project, report_path):
    sys.path.insert(0, str(project/'tools/phase0'))
    suite = unittest.defaultTestLoader.discover(str(project/'tools/phase0/tests'))
    result = unittest.TextTestRunner(verbosity=2, resultclass=CountsResult).run(suite)
    errors, failures, skipped = len(result.errors), len(result.failures), len(result.skipped)
    write(report_path, dict(schema='bg-redux-harness-unit-result/1', executed=result.testsRun,
                           passed=result.passed, errors=errors, failures=failures, skipped=skipped,
                           expected_failures=len(result.expectedFailures), unexpected_successes=len(result.unexpectedSuccesses),
                           success=result.wasSuccessful(),
                           exceptions=[dict(test=str(test), trace=trace) for test, trace in result.errors+result.failures]))
    return 0 if result.wasSuccessful() else 1


def execute(command, cwd, env, log, timeout):
    started = time.monotonic()
    record = dict(command=command, cwd=str(cwd), timeout_seconds=timeout,
                  timed_out=False, exit_code=None, cleanup='not required')
    with log.open('wb') as output:
        try:
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT)
        except OSError as error:
            record['launch_error'] = str(error)
        else:
            record['pid'] = process.pid
            try:
                record['exit_code'] = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                record['timed_out'] = True
                if os.name == 'nt':
                    try:
                        subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'], stdout=output,
                                       stderr=subprocess.STDOUT, check=False, timeout=10)
                    except subprocess.TimeoutExpired:
                        record['cleanup'] = 'taskkill timed out'
                else:
                    process.kill()
                try:
                    record['exit_code'] = process.wait(timeout=5)
                    record['cleanup'] = 'owned process tree termination completed'
                except subprocess.TimeoutExpired:
                    record['cleanup'] = 'termination pending; not a successful run'
    record['elapsed_seconds'] = round(time.monotonic()-started, 3)
    record['log_sha256'] = sha(log)
    return record


def fresh_result(results, previous, token, schema):
    candidates = [p for p in results.iterdir() if p.is_dir() and p.name not in previous and f'-{token}-' in p.name]
    if len(candidates) != 1:
        raise ValueError(f'Expected one fresh {schema} result, found {len(candidates)}')
    folder = candidates[0]
    data = read(folder/'result.json')
    if data.get('schema') != schema or data.get('run_id') != folder.name:
        raise ValueError('Result schema/run identity mismatch')
    if Path(data.get('artifacts', '')).resolve() != folder.resolve():
        raise ValueError('Result artifact directory mismatch')
    return folder, data


def validate_native(kind, folder, data, process):
    if process.get('timed_out'):
        raise ValueError('Baseline command timed out')
    if process.get('exit_code') not in (0, 1):
        raise ValueError('Unexpected baseline command exit')
    stages = data.get('stages', [])
    expected = ['import','reload-1','reload-2','repeat-import'] if kind == 'vanilla' else ['gui-save','gui-reload']
    if [s.get('name') for s in stages] != expected:
        raise ValueError('Missing or reordered native stages')
    for stage in stages:
        native_process = stage.get('process', {})
        if native_process.get('timed_out') or native_process.get('exit_code') != 0 or not stage.get('passed'):
            raise ValueError('Native stage failed or timed out: '+str(stage.get('name')))
        artifact = folder/stage['name']/('state.json' if kind == 'vanilla' else 'gui-result.json')
        observed = read(artifact)
        if kind == 'gui' and observed.get('completed') is not True:
            raise ValueError('GUI native completion artifact missing')
        if kind == 'vanilla' and observed.get('schema') != 'bg-redux-state/1':
            raise ValueError('Native state snapshot schema missing')
        if kind == 'gui':
            for capture in ('00-game','01-inventory','02-record'):
                read(folder/stage['name']/(capture+'.ui.json'))
                with (folder/stage['name']/(capture+'.bmp')).open('rb') as stream:
                    if stream.read(2) != b'BM':
                        raise ValueError('GUI screenshot missing/invalid: '+capture)
    if data.get('execution_verdict') != 'passed' or data.get('assertion_verdict') != 'passed':
        raise ValueError('Native execution/assertions did not pass')
    assertions = data.get('assertions', []) if kind == 'vanilla' else [a for s in stages for a in s.get('assertions', [])]
    expected_count = 24 if kind == 'vanilla' else 20
    if len(assertions) != expected_count or not all(a.get('passed') is True for a in assertions):
        raise ValueError('Required baseline assertion coverage missing or failed')
    flags = ['source_unchanged','input_copy_unchanged'] if kind == 'vanilla' else ['fixture_unchanged','created_save_unchanged_on_reload']
    if not all(data.get(flag) is True for flag in flags):
        raise ValueError('Input/save preservation flag failed or absent')
    verdict = data.get('verdict')
    if verdict not in ('passed', 'differences') or process['exit_code'] != (0 if verdict == 'passed' else 1):
        raise ValueError('Command exit contradicts compatibility verdict')
    if kind == 'vanilla':
        if len(data.get('comparisons', [])) != 2 or 'wire_oracle' not in data or 'repeat_import' not in data:
            raise ValueError('Persistence evidence missing')
        for name in ['wire-oracle.json','reload-1-semantic-diff.json','reload-2-semantic-diff.json','repeat-import-semantic-diff.json']:
            read(folder/name)
        if read(folder/'wire-oracle.json') != data['wire_oracle']:
            raise ValueError('Wire-oracle artifact contradicts result')
        for comparison, cycle in zip(data['comparisons'], (1, 2)):
            delta = read(folder/f'reload-{cycle}-semantic-diff.json')
            if comparison.get('cycle') != cycle or comparison.get('semantic_differences') != len(delta) or comparison.get('passed') != (not delta):
                raise ValueError('Reload comparison artifact contradicts result')
        if len(read(folder/'repeat-import-semantic-diff.json')) != data['repeat_import'].get('semantic_differences'):
            raise ValueError('Repeat-import artifact contradicts result')
    else:
        for name in ['gui-reload-differences.json','legacy-semantic-differences.json']:
            read(folder/name)
        if 'persistence' not in data or 'legacy_semantic_diagnostic' not in data:
            raise ValueError('GUI persistence evidence missing')
        if (len(read(folder/'gui-reload-differences.json')) != data['persistence'].get('differences')
                or len(read(folder/'legacy-semantic-differences.json')) != data['legacy_semantic_diagnostic'].get('differences')):
            raise ValueError('GUI difference artifacts contradict result')
    return dict(execution='passed', assertions=dict(passed=len(assertions), total=len(assertions)),
                compatibility=verdict, skipped=0)


def difference_evidence(kind, folder, data):
    if kind == 'vanilla':
        return dict(wire=read(folder/'wire-oracle.json')['differences'],
                    reloads=[read(folder/f'reload-{cycle}-semantic-diff.json') for cycle in (1, 2)],
                    repeat=read(folder/'repeat-import-semantic-diff.json'))
    return dict(legacy=read(folder/'legacy-semantic-differences.json'),
                persistence_scopes=data['persistence']['scopes'])


def difference_disposition(kind, current, reference=None):
    """Known means matches an explicit frozen reference, never compatibility pass."""
    if reference is None:
        return dict(status='unreviewed-differences', reason='No explicit reference run supplied')
    if kind == 'vanilla':
        color = lambda entries: all(re.fullmatch(r'/current_area_actors/\d+/(base_stats|modified_stats)/(20[8-9]|21[0-4])', d.get('path','')) for d in entries)
        known = (current['wire'] == reference['wire'] and current['reloads'] == reference['reloads']
                 and color(current['repeat']) and color(reference['repeat']))
        reason = 'Wire/reload differences match reference; repeat-import differences confined to previously observed color stats'
    else:
        known = current == reference
        reason = 'Exact legacy residuals and persistence scopes match explicit reference'
    return dict(status='known-differences' if known else 'unreviewed-differences',
                reason=reason if known else 'Differences exceed or change the explicit reference; review required')


def protected(project):
    engine = project/'gemrb'
    source = {p.relative_to(engine).as_posix(): dict(bytes=p.stat().st_size, sha256=sha(p))
              for p in sorted(engine.rglob('*')) if p.is_file()
              and not any(part in ('.git','redux','__pycache__') for part in p.relative_to(engine).parts)
              and p.name != 'README_BG_REDUX.md'}
    build = project/'phase0-local/build/gemrb'
    binaries = {p.relative_to(project).as_posix(): dict(bytes=p.stat().st_size, sha256=sha(p)) for p in
                [build/name for name in ['gemrb.exe','libgemrb_core.dll','Test_gemrb_core.exe','Redux_phase0_core.exe']]
                + sorted((build/'plugins').glob('*.dll')) + [build/'core/libgemrb_core.dll.a']}
    fixture = files_manifest(project/'phase0-local/fixtures/original-bg2ee-20261020/GemRB')
    return dict(source=source, binaries=binaries, fixture=fixture)


def preflight(project):
    tool = project/'tools/phase0'
    if not (tool/'harness.py').is_file():
        raise ValueError('Project root must contain tools/phase0/harness.py (not the nested publication directory)')
    fixture = project/'phase0-local/fixtures/original-bg2ee-20261020/GemRB'
    check_manifest(fixture, read(project/'docs/compatibility/evidence/vanilla-save-fixture.json')['files'])
    baseline = read(project/'docs/compatibility/evidence/baseline-results.json')
    for row in baseline['binaries']:
        path = safe_member(project, row['path'])
        if not path.is_file() or sha(path) != row['sha256']:
            raise ValueError('Engine baseline binary mismatch: '+row['path'])
    expected_plugins = read(project/'docs/compatibility/evidence/gui-harness-results.json')['plugins']
    plugins = {p.name: sha(p) for p in (project/'phase0-local/build/gemrb/plugins').glob('*.dll')}
    if plugins != expected_plugins:
        raise ValueError('Engine plugin baseline inventory mismatch')
    changes = subprocess.check_output(['git','-C',str(project/'gemrb'),'diff','--name-only',BASELINE,'--','.',
                                       ':(exclude)redux',':(exclude)README_BG_REDUX.md'], text=True)
    if changes.strip():
        raise ValueError('Engine tracked source differs from pinned baseline: '+changes.strip())
    return dict(engine_baseline=BASELINE, engine_commit=subprocess.check_output(['git','-C',str(project/'gemrb'),'rev-parse','HEAD'],text=True).strip(),
                plugins_checked=len(plugins), fixture_files=len(files_manifest(fixture)))


def check_build(project, kind):
    folder = project/'phase0-local'/('native-probe' if kind == 'save' else 'gui-probe')
    receipt = read(folder/'build.json')
    binary = folder/('Redux_save_probe.exe' if kind == 'save' else 'Redux_gui_probe.exe')
    if receipt.get('exit_code') != 0 or receipt.get('binary_sha256') != sha(binary):
        raise ValueError('Failed/stale external '+kind+' build')
    if receipt.get('engine_dll_sha256') != sha(project/'phase0-local/build/gemrb/libgemrb_core.dll'):
        raise ValueError('External '+kind+' build core DLL drift')
    if receipt.get('compiler_sha256') != sha(project/'phase0-local/toolchain/msys64/ucrt64/bin/g++.exe'):
        raise ValueError('External '+kind+' build compiler drift')
    sources = {'tools/phase0/native/save_probe.cpp': receipt.get('source_sha256')} if kind == 'save' else receipt['sources']
    for relative, expected in sources.items():
        if sha(safe_member(project, relative)) != expected:
            raise ValueError('External '+kind+' build source drift: '+relative)
    return folder


def load_reference(kind, folder, current):
    data = read(folder/'result.json')
    validate_native(kind, folder, data, dict(exit_code=0 if data.get('verdict') == 'passed' else 1))
    if kind == 'vanilla':
        if (data['provenance']['engine_dll_sha256'] != current['provenance']['engine_dll_sha256']
                or data['provenance'].get('probe_source_sha256') != current['provenance'].get('probe_source_sha256')
                or data['fixture']['files'] != current['fixture']['files']):
            raise ValueError('Reference vanilla engine/fixture/observer differs')
    elif (data['provenance']['build']['engine_dll_sha256'] != current['provenance']['build']['engine_dll_sha256']
          or data['provenance']['build'].get('sources') != current['provenance']['build'].get('sources')
          or data['provenance'].get('tool_files') != current['provenance'].get('tool_files')
          or data['provenance']['fixture'] != current['provenance']['fixture']):
        raise ValueError('Reference GUI engine/fixture/observer differs')
    return difference_evidence(kind, folder, data)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--steps', nargs='+', choices=STEPS, default=list(STEPS))
    parser.add_argument('--rebuild-hosts', action='store_true', help='Archive prior external outputs; rebuild external hosts only')
    parser.add_argument('--reference-vanilla', type=Path, help='Explicit frozen run for known-difference labeling, never a pass override')
    parser.add_argument('--reference-gui', type=Path)
    parser.add_argument('--native-timeout', type=float, default=90)
    parser.add_argument('--gui-timeout', type=float, default=150)
    parser.add_argument('--unit-timeout', type=float, default=90)
    parser.add_argument('--unit-worker-output', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    project = args.project_root.resolve()
    if args.unit_worker_output:
        return run_units(project, args.unit_worker_output)
    if min(args.native_timeout, args.gui_timeout, args.unit_timeout) <= 0:
        parser.error('All timeouts must be positive')
    steps = [step for step in STEPS if step in args.steps]
    local = project/'phase0-local'
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-baseline-'+uuid.uuid4().hex[:8]
    output = local/'results'/run_id
    output.mkdir(parents=True)
    report = dict(schema='bg-redux-baseline-run/1', run_id=run_id, hostname=socket.gethostname(),
                  started_utc=datetime.now(timezone.utc).isoformat(), project=str(project), steps=steps,
                  unselected=[s for s in STEPS if s not in steps], commands=[], verdict='failed',
                  execution_verdict='not-run', compatibility_verdict='not-run', phase0_complete=False)
    lock = local/'baseline-runner.lock'
    token = uuid.uuid4().hex
    owns_lock = False
    before = None
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    python = local/'toolchain/msys64/ucrt64/bin/python.exe'
    env['PATH'] = str(python.parent)+os.pathsep+env.get('PATH','')
    script = Path(__file__).resolve()
    try:
        with lock.open('x', encoding='utf-8') as stream:
            json.dump(dict(pid=os.getpid(), hostname=socket.gethostname(), token=token, run_id=run_id), stream)
        owns_lock = True
        report['preflight'] = preflight(project)
        before = protected(project)
        write(output/'protected-before.json', before)
        if args.rebuild_hosts:
            for kind, dirname in [('save','native-probe'),('gui','gui-probe')]:
                src = local/dirname
                if src.exists():
                    shutil.copytree(src, output/'prior-external-builds'/dirname)
                folder = output/('build-'+kind); folder.mkdir()
                proc = execute([str(python),'-B',str(project/f'tools/phase0/build-{kind}-probe.py')], project, env, folder/'stdout.log', 240)
                write(folder/'command.json', proc)
                report['commands'].append(dict(step='build-'+kind, process=proc,
                                                verdict='passed' if proc['exit_code'] == 0 and not proc['timed_out'] else 'failed'))
                if proc['exit_code'] != 0 or proc['timed_out']:
                    raise ValueError('External '+kind+' rebuild failed')
        for kind in ('save','gui'):
            src = check_build(project, kind)
            shutil.copytree(src, output/'external-builds'/kind)
        for path in sorted((project/'tools/phase0').rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                target = output/'tool-source'/path.relative_to(project/'tools/phase0')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        shutil.copy2(script, output/'baseline_runner.py')
        for step in steps:
            folder = output/step; folder.mkdir()
            name = 'baseline-'+token[:12]+'-'+step
            previous = {p.name for p in (local/'results').iterdir()}
            if step == 'units':
                cmd = [str(python),'-B',str(script),'--project-root',str(project),'--unit-worker-output',str(folder/'units.json')]
                timeout = args.unit_timeout
            elif step == 'capabilities':
                cmd = [str(python),'-B',str(project/'tools/phase0/harness.py'),'capabilities']; timeout = 30
            elif step == 'vanilla':
                cmd = [str(python),'-B',str(project/'tools/phase0/harness.py'),'scenario','--scenario',
                       str(project/'tools/phase0/scenarios/vanilla-opening.json'),'--name',name,'--timeout',str(args.native_timeout)]
                timeout = args.native_timeout*4+30
            else:
                cmd = [str(python),'-B',str(project/'tools/phase0/harness.py'),'gui','--name',name,'--timeout',str(args.gui_timeout)]
                timeout = args.gui_timeout*2+30
            print('Running '+step, flush=True)
            proc = execute(cmd, project, env, folder/'stdout.log', timeout)
            command = dict(step=step, process=proc, verdict='failed')
            report['commands'].append(command)
            write(folder/'command.json', proc)
            if proc.get('timed_out'):
                command['verdict'] = 'timeout'
                raise ValueError(step+' command timed out')
            if step == 'units':
                units = read(folder/'units.json')
                command['units'] = units
                if proc['exit_code'] != 0 or not units.get('success') or units.get('executed',0) == 0 or units.get('errors') or units.get('failures'):
                    raise ValueError('Harness unit execution failed or incomplete')
                command['verdict'] = 'skipped' if units['skipped'] else ('expected-failures' if units['expected_failures'] else 'passed')
            elif step == 'capabilities':
                capabilities = read(folder/'stdout.log')
                if proc['exit_code'] != 0 or capabilities.get('protocol') != 'bg-redux-external-tests/1':
                    raise ValueError('Capabilities execution/protocol failed')
                write(folder/'capabilities.json', capabilities)
                command['verdict'] = 'passed'
                command['scope'] = 'Declaration only; other selected steps independently test operations'
            else:
                schema = 'bg-redux-save-run/1' if step == 'vanilla' else 'bg-redux-gui-run/1'
                artifact, data = fresh_result(local/'results', previous, name, schema)
                command['artifact_directory'] = str(artifact)
                command.update(validate_native(step, artifact, data, proc))
                command['verdict'] = data['verdict']
                if data['verdict'] == 'differences':
                    refpath = args.reference_vanilla if step == 'vanilla' else args.reference_gui
                    reference = load_reference(step, refpath.resolve(), data) if refpath else None
                    if refpath:
                        refdest = folder/'reference-evidence'
                        if output.resolve().is_relative_to(refpath.resolve()):
                            raise ValueError('Reference must be a separate frozen run')
                        shutil.copytree(refpath, refdest)
                        command['reference'] = dict(directory=str(refpath.resolve()), files=files_manifest(refdest))
                    command['difference_disposition'] = difference_disposition(step, difference_evidence(step, artifact, data), reference)
            write(output/'result.json', report)
        report['execution_verdict'] = 'passed'
        difference_commands = [c for c in report['commands'] if c['verdict'] == 'differences']
        skipped = any(c.get('units',{}).get('skipped',0) or c.get('units',{}).get('expected_failures',0) for c in report['commands'])
        report['compatibility_verdict'] = 'differences' if difference_commands else 'passed'
        report['verdict'] = 'differences' if difference_commands else ('incomplete-skips' if skipped else 'passed')
    except Exception as error:
        report['error'] = str(error)
        report['execution_verdict'] = 'failed'
        if any(c.get('verdict') == 'timeout' for c in report['commands']):
            report['verdict'] = 'timeout'
    finally:
        if before is not None:
            try:
                after = protected(project)
                write(output/'protected-after.json', after)
                report['preservation'] = {key: before[key] == after[key] for key in before}
                report['preservation_changes'] = {key: sorted(n for n in before[key].keys() | after[key].keys() if before[key].get(n) != after[key].get(n)) for key in before}
                if not all(report['preservation'].values()):
                    raise ValueError('Protected source/binary/fixture changed')
            except (OSError, ValueError) as error:
                report['verdict'] = 'failed'; report['execution_verdict'] = 'failed'
                report['preservation_error'] = str(error)
        if owns_lock:
            try:
                if read(lock).get('token') != token:
                    raise ValueError('Lock ownership changed; lock retained')
                lock.unlink()
            except (OSError, ValueError) as error:
                report['verdict'] = 'failed'; report['lock_error'] = 'Lock ownership changed; lock retained'
                report['lock_error'] = str(error)
        report['not_run'] = [s for s in steps if s not in {c['step'] for c in report['commands']}]
        if any(c.get('compatibility') == 'differences' for c in report['commands']):
            report['compatibility_verdict'] = 'differences'
        report['completed_utc'] = datetime.now(timezone.utc).isoformat()
        write(output/'result.json', report)
        lines = ['# Bounded baseline result', '', f"Run: `{run_id}` on `{report['hostname']}`.", '',
                 f"Execution: **{report['execution_verdict']}**. Compatibility: **{report['compatibility_verdict']}**. Overall: **{report['verdict']}**.", '',
                 '| Step | Result | Process exit | Detail |', '|---|---|---:|---|']
        for command in report['commands']:
            detail = command.get('difference_disposition',{}).get('status','')
            lines.append(f"| {command['step']} | {command.get('verdict','failed')} | {command['process'].get('exit_code')} | {detail} |")
        lines += ['', 'Known differences remain differences; no exit-code or persistence result is converted to a pass.',
                  'Unselected steps: '+(', '.join(report['unselected']) or 'none')+'.',
                  'Selected steps not run: '+(', '.join(report['not_run']) or 'none')+'.',
                  'Raw command logs, frozen external builds/tool sources, before/after preservation manifests and native run paths are retained.',
                  'This bounded runner does not establish campaign parity, player-input isolation, recovery snapshots, or Phase 0 acceptance.']
        if report.get('error'):
            lines += ['', 'Error: '+report['error']]
        (output/'REPORT.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
        native_artifacts = {}
        for command in report['commands']:
            if command.get('artifact_directory'):
                folder = Path(command['artifact_directory'])
                for relative, entry in files_manifest(folder).items():
                    native_artifacts[(folder/relative).relative_to(project).as_posix()] = entry
        write(output/'native-artifacts.json', dict(files=native_artifacts, file_count=len(native_artifacts)))
        artifacts = files_manifest(output)
        write(output/'artifact-manifest.json', dict(files=artifacts, file_count=len(artifacts)))
    print(json.dumps(dict(directory=str(output), verdict=report['verdict'], execution=report['execution_verdict'],
                          compatibility=report['compatibility_verdict'], error=report.get('error')), indent=2))
    return 0 if report['verdict'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
