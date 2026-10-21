"""Validate/freeze an explicitly observed private original-game combat capture.

Visual text is an operator attestation, not OCR or a native memory sample.
Never launches or modifies the game, profile, installed assets or old receipts.
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


class CaptureError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise CaptureError(message)


def _read(path):
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as error:
        raise CaptureError(f'Cannot read JSON receipt {path}: {error}') from error
    _require(isinstance(value, dict), f'Receipt must be an object: {path}')
    return value


def _sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _time(value, name):
    _require(isinstance(value, str), f'Missing timestamp: {name}')
    try:
        instant = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise CaptureError(f'Invalid timestamp: {name}') from error
    _require(instant.tzinfo is not None, f'Timestamp lacks timezone: {name}')
    return instant.astimezone(timezone.utc)


def _path(value, name):
    _require(isinstance(value, str) and value, f'Missing path: {name}')
    return Path(value).resolve()


def _member(folder, relative):
    _require(isinstance(relative, str) and relative and ':' not in relative,
             'Unsafe manifest member')
    path = Path(relative.replace('\\', '/'))
    _require(not path.is_absolute() and '..' not in path.parts, 'Unsafe manifest member')
    target = (folder/path).resolve()
    _require(target.is_relative_to(folder.resolve()), 'Manifest member escapes fixture')
    return target


def _bind(path, expected_hash, name, expected_size=None):
    _require(isinstance(expected_hash, str) and re.fullmatch('[0-9a-f]{64}', expected_hash),
             f'Missing/invalid SHA256: {name}')
    try:
        _require(path.is_file(), f'Missing file: {name}')
        size = path.stat().st_size
        if expected_size is not None:
            _require(type(expected_size) is int and expected_size >= 0 and size == expected_size,
                     f'Size drift: {name}')
        _require(_sha(path) == expected_hash, f'Hash drift: {name}')
    except OSError as error:
        raise CaptureError(f'Cannot inspect {name}: {error}') from error
    return dict(source=str(path), bytes=size, sha256=expected_hash)


def _screenshot(path, expected_hash, name):
    bound = _bind(path, expected_hash, name)
    data = path.read_bytes()
    if data.startswith(b'\xff\xd8\xff') and data.endswith(b'\xff\xd9') and len(data) >= 32:
        bound['signature'] = 'jpeg'
    elif (len(data) >= 33 and data.startswith(b'\x89PNG\r\n\x1a\n') and data[12:16] == b'IHDR'
          and all(struct.unpack_from('>II', data, 16)) and data.endswith(b'IEND\xaeB`\x82')):
        bound['signature'] = 'png'
    else:
        raise CaptureError(f'Unsupported/incomplete screenshot signature: {name}')
    return bound


def _window(value, expected, name):
    _require(isinstance(value, dict), f'Missing window: {name}')
    _require(type(value.get('id')) is int and value['id'] > 0, f'Invalid window ID: {name}')
    _require(value.get('app') == expected['app'] and value.get('title') == expected['title'],
             f'Wrong private game window: {name}')
    return value


def _fixture(folder, expected, script):
    _require(isinstance(expected, dict) and expected, 'Final fixture manifest missing')
    actual_names = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    _require(actual_names == set(expected), 'Final fixture file inventory drift')
    files = {}
    for name, entry in expected.items():
        _require(isinstance(entry, dict), 'Invalid final fixture manifest entry')
        _require(type(entry.get('bytes')) is int and entry['bytes'] >= 0, 'Final fixture size missing/invalid')
        files[name] = _bind(_member(folder, name), entry.get('sha256'), f'fixture/{name}', entry.get('bytes'))
    games = [p for p in folder.iterdir() if p.name.lower() == 'baldur.gam']
    _require(len(games) == 1, 'Final fixture GAM missing/ambiguous')
    data = games[0].read_bytes()
    _require(len(data) >= 0x28 and data[:8] == b'GAMEV2.0', 'Unsupported/truncated final GAM')
    row = struct.unpack_from('<I', data, 0x20)[0]
    _require(row + 12 <= len(data), 'Truncated final party entry')
    creature, size = struct.unpack_from('<II', data, row+4)
    _require(size >= 0x250 and creature + size <= len(data), 'Truncated final embedded CRE')
    _require(data[creature:creature+8] == b'CRE V1.0', 'Unsupported final embedded CRE')
    _require(data[creature+0x248:creature+0x250].rstrip(b'\0') == script.encode('ascii'),
             'Final fixture script assignment mismatch')
    return files


def validate_capture(preparation_path, observation_path, *, launch_path=None, isolation_path=None, now=None):
    """Read-only validation against recorded session identity; no process liveness claim."""
    preparation_path, observation_path = Path(preparation_path).resolve(), Path(observation_path).resolve()
    prep, obs = _read(preparation_path), _read(observation_path)
    _require(prep.get('schema') == 'bg-redux-original-live-preparation/1', 'Unsupported preparation schema')
    run_id, nonce = prep.get('run_id'), prep.get('nonce')
    _require(isinstance(run_id, str) and re.fullmatch(r'\d{8}T\d{6}Z-original-live-[0-9a-f]{8}', run_id),
             'Invalid prepared run identity')
    _require(isinstance(nonce, str) and re.fullmatch('[0-9A-F]{8}', nonce), 'Invalid prepared nonce')
    directory = _path(prep.get('directory'), 'preparation directory')
    _require(directory == preparation_path.parent and directory.name == run_id, 'Preparation directory/run mismatch')
    game, profile = _path(prep.get('game'), 'private game'), _path(prep.get('profile'), 'private profile')
    _require(profile.name == run_id and profile.parent.name == 'BGReduxLab', 'Wrong private profile identity')
    _require(preparation_path != observation_path and observation_path.is_relative_to(directory),
             'Observation must belong to prepared run')
    case, branch, phase = obs.get('case'), obs.get('selected_branch'), obs.get('phase')
    rows = prep.get('cases')
    _require(isinstance(rows, list) and rows, 'Prepared cases missing')
    _require(all(isinstance(row, dict) and isinstance(row.get('spec'), dict)
                 and isinstance(row['spec'].get('id'), str) and isinstance(row.get('script'), str)
                 for row in rows), 'Malformed prepared case/script')
    ids = [row.get('spec', {}).get('id') for row in rows]
    scripts = [row.get('script') for row in rows]
    _require(len(set(ids)) == len(rows) and len(set(scripts)) == len(rows), 'Ambiguous prepared case/script')
    matches = [row for row in rows if row.get('spec', {}).get('id') == case]
    _require(len(matches) == 1, 'Unknown/ambiguous observed case')
    row = matches[0]
    _require(obs.get('nonce') == nonce and row.get('nonce') == nonce, 'Wrong/stale capture nonce')
    first = row.get('spec', {}).get('first')
    _require(type(first) is int and type(branch) is int and first <= branch < first+4,
             'Observed branch outside prepared tail')
    _require(phase in ('ENTER', 'RETURN'), 'Missing/unsupported observed phase')
    _require(obs.get('queue_completion_observed') is (phase == 'RETURN'),
             'Entry/return queue-completion claim mismatch')
    _require(obs.get('exact_action_memory_sample') is False and obs.get('save_required') is False,
             'Unsupported exact-memory/save-dependent observation claim')
    lines = obs.get('observations')
    _require(isinstance(lines, list) and all(isinstance(line, str) for line in lines), 'Explicit observed lines missing')
    seen, marker = f'RDX {nonce} {case} SEEN', f'RDX {nonce} {case} B{branch} {phase}'
    _require(seen in lines and marker in lines, 'Fresh exact seen/branch marker missing')
    strings = row.get('strings')
    _require(isinstance(strings, list) and all(isinstance(s, str) for s in strings), 'Prepared marker strings missing')
    declared = set(strings)
    _require(seen in declared and marker in declared, 'Observed marker absent from prepared strings')
    for line in lines:
        if line.startswith('RDX '):
            _require(line in declared, 'Wrong nonce/case/branch in observed marker lines')
    feedback = [line for line in lines if line.startswith('Attack') and 'visible' in line.lower()
                and re.search(r'\btakes \d+(?:/\d+)* slashing damage\b', line, re.I)]
    _require(feedback, 'Positive visible combat-feedback attestation missing')

    executable = game/'Baldur.exe'
    artifacts = dict(executable=_bind(executable, prep.get('executable_sha256'), 'private executable'),
                     tlk=_bind(game/'lang/en_US/dialog.tlk', prep.get('private_tlk_sha256'), 'private TLK'),
                     engine_lua=_bind(game/'engine.lua', prep.get('engine_lua_sha256'), 'private engine.lua'),
                     retained_steam=_bind(game/'steam_api64.dll.phase0-retained',
                                          prep.get('retained_optional_steam_dll_sha256'), 'retained optional Steam DLL'))
    _require(not (game/'steam_api64.dll').exists(), 'Optional Steam integration active in private copy')
    engine_lua = (game/'engine.lua').read_text(encoding='ascii')
    _require(f'engine_name = "BGReduxLab/{run_id}"' in engine_lua, 'Private engine profile binding mismatch')
    script = row.get('script')
    _require(isinstance(script, str) and re.fullmatch('RDXL[0-9]{4}', script), 'Invalid unique script reference')
    artifacts['script'] = _bind(game/'override'/(script+'.bcs'), row.get('script_sha256'), 'final live script')
    fixture = _path(row.get('fixture'), 'final fixture')
    _require(fixture.parent == profile/'save' and fixture.name.endswith(f'-{case}-{nonce}'), 'Final fixture profile/case binding mismatch')
    fixtures = _fixture(fixture, row.get('fixture_files'), script)

    launch_path = Path(launch_path or directory/'launch.json').resolve()
    isolation_path = Path(isolation_path or directory/'load-boundary.json').resolve()
    _require(launch_path.is_relative_to(directory) and isolation_path.is_relative_to(directory), 'Session receipts outside prepared run')
    launch, isolation = _read(launch_path), _read(isolation_path)
    _require(_path(launch.get('executable'), 'launch executable') == executable, 'Launch executable path mismatch')
    _require(launch.get('sha256') == prep.get('executable_sha256') and type(launch.get('pid')) is int and launch['pid'] > 0,
             'Launch identity/hash missing or mismatched')
    started = _time(launch.get('started_utc'), 'launch')
    observed = _time(obs.get('observed_at_utc'), 'observation')
    loaded = _time(isolation.get('captured_at_utc'), 'load boundary')
    prepared = datetime.strptime(run_id[:16], '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    _require(prepared <= started <= loaded <= observed <= now, 'Stale/future or unordered session/capture timestamp')
    expected_window = dict(app='process:'+str(executable), title=f'BGReduxLab/{run_id} - v2.7.3.0')
    observed_window = _window(obs.get('window'), expected_window, 'observation')
    loaded_window = _window(isolation.get('window'), expected_window, 'load boundary')
    _require(loaded_window['id'] == observed_window['id'], 'Load/capture window identity mismatch')
    counts = {str(len(rows))}
    number_words = {1:'one',2:'two',3:'three',4:'four',5:'five',6:'six',7:'seven',8:'eight',9:'nine',10:'ten'}
    if len(rows) in number_words:
        counts.add(number_words[len(rows)])
    isolation_expected = {f'Exactly {count} prepared nonce {nonce} cases, no personal/cloud saves visible at actual load boundary'
                          for count in counts}
    _require(isolation.get('observed') in isolation_expected, 'Load-boundary isolation visual attestation missing/mismatched')
    capture = _path(obs.get('screenshot_path'), 'capture screenshot')
    boundary_capture = _path(isolation.get('path'), 'load-boundary screenshot')
    _require(capture.is_relative_to(directory) and boundary_capture.is_relative_to(directory), 'Screenshot outside prepared run')
    artifacts['screenshot'] = _screenshot(capture, obs.get('screenshot_sha256'), 'observed screenshot')
    artifacts['load_boundary_screenshot'] = _screenshot(boundary_capture, isolation.get('sha256'), 'load-boundary screenshot')
    for key, path in [('preparation',preparation_path), ('observation',observation_path), ('launch',launch_path), ('isolation',isolation_path)]:
        artifacts[key] = _bind(path, _sha(path), key)
    return dict(schema='bg-redux-original-live-capture/1', verdict='observed-branch-and-combat-feedback',
                run_id=run_id, nonce=nonce, case=case, selected_branch=branch, phase=phase,
                observed_at_utc=obs['observed_at_utc'], validated_at_utc=now.isoformat(),
                window=observed_window, operator_visual_attestation=lines,
                queue_completion_observed=phase == 'RETURN', exact_action_memory_sample=False,
                exact_target_memory_sample=False, dpr_comparison=False, save_required=False,
                process_liveness_verified=False, artifacts=artifacts, fixture_files=fixtures,
                fixture_manifest_authority='Final row.fixture_files plus embedded unique script assignment; construction.input_files/ai_script_sha256 are precursor metadata only.',
                limits='Explicit operator visual attestation, not automatic OCR. ENTER proves selected response; RETURN proves retained queue returned. Neither samples exact native action/target memory or proves damage parity, causal defense outcomes, whole-AI/campaign behavior or DPR.')


def finalize(preparation_path, observation_path, *, output_root=None, launch_path=None, isolation_path=None):
    preparation_path, observation_path = Path(preparation_path).resolve(), Path(observation_path).resolve()
    destination = Path(output_root or preparation_path.parent.parent).resolve()
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-original-live-capture-'+uuid.uuid4().hex[:8]
    out = destination/run_id
    out.mkdir(parents=True, exist_ok=False)
    result = dict(schema='bg-redux-original-live-capture/1', verdict='failed', directory=str(out),
                  requested_preparation=str(preparation_path), requested_observation=str(observation_path))
    try:
        result = validate_capture(preparation_path, observation_path, launch_path=launch_path, isolation_path=isolation_path)
        result['directory'] = str(out)
        frozen = {}
        for key, entry in result['artifacts'].items():
            source = Path(entry['source'])
            target = out/'bound-inputs'/key/source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            _require(_sha(source) == entry['sha256'] and _sha(target) == entry['sha256'], f'Artifact changed during freeze: {key}')
            frozen[key] = dict(entry, frozen=str(target))
        for name, entry in result['fixture_files'].items():
            target = _member(out/'final-fixture', name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry['source'], target)
            _require(_sha(Path(entry['source'])) == entry['sha256'] and _sha(target) == entry['sha256'], f'Fixture changed during freeze: {name}')
        shutil.copy2(Path(__file__), out/'original_live_capture.py')
        result['frozen_artifacts'] = frozen
        result['validator_sha256'] = _sha(out/'original_live_capture.py')
    except (CaptureError, OSError, ValueError, KeyError, TypeError, struct.error) as error:
        result.update(verdict='failed', error=str(error), directory=str(out))
        for label, path in [('requested-preparation.json', preparation_path), ('requested-observation.json', observation_path)]:
            if path.is_file():
                shutil.copy2(path, out/label)
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['finalize'])
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--observation', type=Path, action='append', required=True)
    parser.add_argument('--launch', type=Path)
    parser.add_argument('--isolation', type=Path)
    parser.add_argument('--output-root', type=Path)
    args = parser.parse_args(argv)
    results = [finalize(args.preparation, path, output_root=args.output_root,
                        launch_path=args.launch, isolation_path=args.isolation) for path in args.observation]
    print(json.dumps([dict(case=r.get('case'), verdict=r['verdict'], directory=r['directory'],
                           error=r.get('error')) for r in results], indent=2))
    return int(any(r['verdict'] == 'failed' for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
