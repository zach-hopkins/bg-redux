"""External Phase 0 core-test runner and native save/query client dispatcher.

Runs existing tests in a bounded child process and keeps assertion, fixture, and
process outcomes separate. All writable artifacts stay under phase0-local.
The native client is stateless across processes; it is not an interactive RPC.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / 'phase0-local'
BUILD = LOCAL / 'build'
PREFIX = LOCAL / 'toolchain/msys64/ucrt64'


def digest(path):
    if not path.is_file():
        return None
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def environment(output):
    env = os.environ.copy()
    env.update(PATH=os.pathsep.join([str(PREFIX / 'bin'), str(BUILD / 'gemrb'), env['PATH']]),
               PYTHONHOME=str(PREFIX), PYTHONPATH=str(PREFIX / 'lib/python3.14'),
               GTEST_OUTPUT='xml:' + output.as_posix() + '/')
    # Match the engine's Windows HomePath/UserProfilePath lookup without using
    # the person's Documents game profile. This is child-process scoped.
    home = output / 'profile'
    (home / 'Documents').mkdir(parents=True)
    env.pop('HOME', None)
    env['HOMEDRIVE'] = home.drive
    env['HOMEPATH'] = str(home)[len(home.drive):]
    return env


def assertions(output):
    counts = dict(discovered=0, executed=0, passed=0, failed=0, skipped=0, disabled=0)
    details = []
    reports = []
    parse_errors = []
    for path in sorted(output.glob('*.xml')):
        try:
            tree = ET.parse(path)
        except ET.ParseError as error:
            parse_errors.append(dict(file=path.name, error=str(error)))
            continue
        if tree.getroot().tag not in ('testsuites', 'testsuite'):
            continue
        reports.append(path.name)
        for case in tree.iter('testcase'):
            counts['discovered'] += 1
            name = case.get('classname', '') + '.' + case.get('name', '')
            if case.get('status') == 'notrun':
                verdict = 'disabled'
            elif case.find('skipped') is not None:
                verdict = 'skipped'
                counts['executed'] += 1
            elif case.find('failure') is not None or case.find('error') is not None:
                verdict = 'failed'
                counts['executed'] += 1
            else:
                verdict = 'passed'
                counts['executed'] += 1
            counts[verdict] += 1
            if verdict != 'passed':
                details.append(dict(test=name, verdict=verdict))
    return dict(counts=counts, reports=reports, exceptions=details, parse_errors=parse_errors,
                scope='Only emitted GoogleTest XML; missing reports are not passes.')


def run_process(command, cwd, env, log_path, timeout):
    """Bound one owned process tree and always return a process outcome."""
    started = time.monotonic()
    with log_path.open('wb') as log:
        try:
            proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        except OSError as error:
            return dict(exit_code=None, timed_out=False, launch_error=str(error), elapsed_seconds=0)
        timed_out = False
        cleanup = 'not required'
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                               stdout=log, stderr=subprocess.STDOUT, check=False, timeout=10)
            except subprocess.TimeoutExpired:
                pass
            try:
                proc.wait(timeout=3)
                cleanup = 'child tree termination completed'
            except subprocess.TimeoutExpired:
                cleanup = 'termination requested; process still pending at deadline'
    return dict(pid=proc.pid, exit_code=proc.returncode, timeout_seconds=timeout,
                timed_out=timed_out, cleanup=cleanup,
                elapsed_seconds=round(time.monotonic()-started, 3))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'query-matrix':
        from query_matrix import main as matrix_main
        return matrix_main()
    if len(sys.argv) > 1 and sys.argv[1] == 'capture-original-matrix':
        from capture_original_matrix import main as matrix_capture_main
        return matrix_capture_main()
    if len(sys.argv) > 1 and sys.argv[1] == 'capture-original-query':
        from capture_original_query import main as capture_main
        return capture_main()
    if len(sys.argv) > 1 and sys.argv[1] == 'script-query':
        from script_query_probe import main as script_main
        return script_main()
    if len(sys.argv) > 1 and sys.argv[1] == 'weapon-triggers':
        from scan_weapon_triggers import main as weapon_main
        return weapon_main()
    if len(sys.argv) > 1 and sys.argv[1] == 'cre-loadouts':
        from scan_cre_loadouts import main as loadout_main
        return loadout_main()
    if len(sys.argv) > 1 and sys.argv[1] == 'live-clock':
        from live_clock import main as clock_main
        return clock_main()
    if len(sys.argv) > 1 and sys.argv[1] == 'string-challenge':
        from string_challenge import main as challenge_main
        return challenge_main()
    if len(sys.argv) > 1 and sys.argv[1] == 'equip-scan':
        from scan_equipping import main as scan_main
        return scan_main()
    if len(sys.argv) > 1 and sys.argv[1] == 'original-reference':
        from original_reference import main as reference_main
        return reference_main(sys.argv[2:])
    if len(sys.argv) > 1 and sys.argv[1] == 'effects':
        from effect_cycle import main as effects_main
        return effects_main()
    if len(sys.argv) > 1 and sys.argv[1] == 'gui':
        from gui_harness import main as gui_main
        return gui_main(sys.argv[1:])
    if len(sys.argv) > 1 and sys.argv[1] in ('save', 'inspect', 'scenario'):
        from save_harness import main as save_main
        return save_main(sys.argv[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite', choices=['core', 'ctest', 'capabilities'])
    parser.add_argument('--filter', default='*', help='Existing GoogleTest or CTest expression')
    parser.add_argument('--timeout', type=float, default=30)
    parser.add_argument('--name', default='baseline')
    parser.add_argument('--managed', action='store_true', help='Use the separately linked explicit-logger-cleanup test entry')
    args = parser.parse_args()
    if args.suite == 'capabilities':
        print(json.dumps(dict(protocol='bg-redux-external-tests/1',
            available=['existing-core-tests', 'existing-ctest', 'timeout', 'logs', 'gtest-xml', 'provenance',
                       'native-save-import', 'ordinary-resave', 'fresh-process-reload',
                       'fresh-process-state-snapshot', 'json-pointer-query', 'party-selection-command',
                       'declarative-scenario-assertions', 'selected-original-wire-field-oracle',
                       'full-loop-stock-gui-load-save-callbacks','scoped-ui-control-text','engine-buffer-screenshots',
                       'effect-reload-lifecycle-characterization','permanent-equip-exposure-scan',
                       'human-created-original-save-reference-comparison','bounded-displaystring-protection-challenge',
                       'actual-main-loop-pause-resume','packaged-cre-item-reference-scan',
                       'packaged-weapon-query-stub-exposure','generated-bcs-query-autosave',
                       'observed-original-script-query-capture'],
            unavailable=['engine-rpc', 'universal-semantic-ui-tree', 'tick-step', 'controlled-rng',
                         'active-player-session-attachment', 'general-original-executable-runtime-oracle',
                         'automated-bg2ee-playthrough']), indent=2))
        return 0
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.name) or args.timeout <= 0:
        parser.error('Use a simple run name and a positive timeout.')
    run_id = time.strftime('%Y%m%d-%H%M%S') + '-' + args.name + '-' + uuid.uuid4().hex[:8]
    output = LOCAL / 'results' / run_id
    output.mkdir(parents=True)
    env = environment(output)
    executable = BUILD / ('gemrb/Redux_phase0_core.exe' if args.managed else 'gemrb/Test_gemrb_core.exe')
    if args.suite == 'core':
        cwd = BUILD / 'gemrb/core'
        (cwd / 'tests').mkdir(parents=True, exist_ok=True)
        if not (cwd / 'tests/resources').exists():
            shutil.copytree(BUILD / 'gemrb/tests/resources', cwd / 'tests/resources')
        command = [str(executable), '--gtest_filter=' + args.filter,
                   '--gtest_output=xml:' + (output / 'core.xml').as_posix()]
    else:
        cwd = BUILD
        command = [str(PREFIX / 'bin/ctest.exe'), '--output-on-failure',
                   '--timeout', str(args.timeout), '--output-junit', str(output / 'ctest.xml')]
        if args.filter != '*':
            command += ['-R', args.filter]
    started = time.time()
    timed_out = False
    cleanup = 'not required'
    with (output / 'process.log').open('wb') as log:
        proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            rc = proc.wait(timeout=args.timeout + (5 if args.suite == 'ctest' else 0))
        except subprocess.TimeoutExpired:
            timed_out = True
            # Windows child trees (CTest/GTest death tests) must also be bounded.
            try:
                subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                               stdout=log, stderr=subprocess.STDOUT, check=False, timeout=10)
            except subprocess.TimeoutExpired:
                pass  # Still attempt the bounded exit check and persist a result.
            try:
                proc.wait(timeout=3)
                cleanup = 'child tree termination completed'
            except subprocess.TimeoutExpired:
                # A Windows process already inside DLL process teardown can
                # remain in the process list despite TerminateProcess. Never
                # hang the orchestrator or report a successful exit for it.
                cleanup = 'termination requested; process still pending at deadline'
            rc = proc.returncode
    measured = assertions(output) if args.suite == 'core' else None
    try:
        revision = subprocess.check_output(['git', '-C', str(ROOT / 'gemrb'), 'rev-parse', 'HEAD'], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = None
    verdict = 'timeout' if timed_out else ('passed' if rc == 0 else 'failed')
    if verdict == 'passed' and measured and not (measured['counts']['passed'] + measured['counts']['failed']):
        verdict = 'incomplete'
    if verdict == 'passed' and measured and measured['parse_errors']:
        verdict = 'incomplete'
    result = dict(schema='bg-redux-external-tests/1', run_id=run_id, command=command,
        working_directory=str(cwd), process=dict(pid=proc.pid, exit_code=rc,
        timeout_seconds=args.timeout, timed_out=timed_out, cleanup=cleanup,
        elapsed_seconds=round(time.time()-started, 3)),
        verdict=verdict,
        assertions=measured, provenance=dict(source_revision=revision,
            core_test_sha256=digest(executable), core_dll_sha256=digest(BUILD / 'gemrb/libgemrb_core.dll'),
            test_config_sha256=digest(BUILD / 'tester.cfg'),
            save_testing_ini_sha256=digest(BUILD / 'gemrb/core/tests/resources/saves/saveTesting.ini'),
            cmake_cache_sha256=digest(BUILD / 'CMakeCache.txt'),
            managed_entry_sha256=digest(ROOT / 'tools/phase0/managed-test-main.cpp') if args.managed else None,
            package_inventory_sha256=digest(LOCAL / 'logs/msys-package-versions.txt'),
            data_manifest_sha256=digest(ROOT / 'docs/compatibility/evidence/bg2ee-copy-manifest.json'),
            note='Data manifest is provenance only; synthetic tests do not validate BG2EE content.'),
        artifacts=dict(directory=str(output), log='process.log', summary='result.json'))
    (output / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if result['verdict'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
