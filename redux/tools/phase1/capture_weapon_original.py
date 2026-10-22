"""Freeze one explicitly observed original EE six-query autosave; never launch a game."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import uuid

from weapon_oracle_fixtures import digest, inspect_output, load_api, write


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(preparation, observation):
    prep, obs = read(preparation), read(observation)
    require(obs.get('schema') == 'bg-redux-phase1-original-weapon-observation/1', 'Wrong observation schema')
    require(type(obs.get('number')) is int and type(obs.get('nonce')) is int, 'Invalid case identity types')
    require(isinstance(obs.get('method'), str) and bool(obs['method'].strip()), 'Missing operator observation')
    require(prep['phase'] == 'prepared-not-executed' and prep['original_prepared'], 'Unprepared original inputs')
    rows = [r for r in prep['cases'] if r['number'] == obs['number'] and r['spec']['id'] == obs['case_id']]
    require(len(rows) == 1 and obs['nonce'] == prep['nonce'], 'Case/nonce mismatch')
    row = rows[0]
    game, profile = Path(prep['game']), Path(prep['profile'])
    require(Path(obs['loaded_fixture']).resolve() == Path(row['original_fixture']).resolve(), 'Wrong loaded fixture')
    window = obs['window']
    expected = 'process:'+str(game/'Baldur.exe')
    require(window['app'].replace('/', '\\').casefold() == expected.replace('/', '\\').casefold(), 'Wrong executable window')
    require(prep['run_id'] in window['title'] and type(window['id']) is int, 'Wrong profile window identity')
    boundary = read(preparation.parent/'load-boundary.json')
    require(boundary['window'] == window and boundary['nonce'] == prep['nonce'], 'Wrong isolation boundary')
    expected_folders = {Path(r['original_fixture']).name for r in prep['cases']}
    folders = boundary.get('profile_save_folders')
    require(isinstance(folders, list) and all(isinstance(v, str) for v in folders)
            and len(folders) == len(set(folders)) and set(folders) == expected_folders,
            'Isolation boundary contains missing or unexpected saves')
    require(isinstance(boundary.get('observation'), str) and bool(boundary['observation'].strip()),
            'Missing isolation observation')
    launch = read(preparation.parent/'launch.json')
    require(Path(launch['executable']).resolve() == (game/'Baldur.exe').resolve(), 'Wrong launch executable')
    instant = datetime.fromisoformat(obs['captured_utc'].replace('Z', '+00:00'))
    started = datetime.fromisoformat(launch['started_utc'].replace('Z', '+00:00'))
    isolated = datetime.fromisoformat(boundary['captured_utc'].replace('Z', '+00:00'))
    age = (datetime.now(timezone.utc)-instant).total_seconds()
    require(instant.tzinfo is not None and started <= instant and -30 <= age <= 600, 'Stale/future observation')
    require(isolated.tzinfo is not None and started <= isolated <= instant, 'Stale/future isolation boundary')
    require(digest(game/'Baldur.exe') == prep['executable_sha256'] == launch['executable_sha256'], 'Executable drift')
    require(digest(game/'engine.lua') == prep['engine_lua_sha256'], 'Profile configuration drift')
    require(digest(game/'override'/(row['script']+'.bcs')) == row['script_sha256'], 'Script drift')
    api = load_api(Path(prep['project']))
    require(api.save_harness.manifest(Path(row['original_fixture'])) == row['fixture_files'], 'Original input drift')
    require(api.save_harness.manifest(Path(row['fixture'])) == row['fixture_files'], 'Prepared input drift')
    for path, expected_hash in [(obs['screenshot_path'], obs['screenshot_sha256']),
                                (obs['selected_screenshot_path'], obs['selected_screenshot_sha256']),
                                (boundary['screenshot_path'], boundary['screenshot_sha256'])]:
        image = Path(path)
        require(digest(image) == expected_hash, 'Screenshot drift')
        signature = image.read_bytes()
        require(signature.startswith(b'\xff\xd8\xff') or signature.startswith(b'\x89PNG\r\n\x1a\n'), 'Invalid screenshot signature')
    saved = profile/'save/000000000-Auto-Save'
    values = inspect_output(api, saved/'BALDUR.gam', row)
    return prep, obs, row, api, saved, values, boundary


def finalize(preparation, observation, results):
    folder = (results/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-original-weapon-case-'+uuid.uuid4().hex[:8])).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    result = dict(schema='bg-redux-phase1-original-weapon-case/1', verdict='failed', directory=str(folder),
                  preparation=str(preparation.resolve()))
    try:
        primary = {name: (path, digest(path)) for name, path in [
            ('preparation.json', preparation), ('observation.json', observation),
            ('launch.json', preparation.parent/'launch.json'),
            ('load-boundary.json', preparation.parent/'load-boundary.json')]}
        result['preparation_sha256'] = primary['preparation.json'][1]
        prep, obs, row, api, saved, values, boundary = validate(preparation, observation)
        require(all(digest(path) == expected for path, expected in primary.values()),
                'Receipt changed during validation')
        before = api.save_harness.manifest(saved)
        frozen = folder/'autosave'
        shutil.copytree(saved, frozen)
        require(api.save_harness.manifest(saved) == before == api.save_harness.manifest(frozen), 'Autosave changed while freezing')
        require(inspect_output(api, frozen/'BALDUR.gam', row) == values, 'Frozen observation differs')
        ancillary = dict(primary)
        ancillary.update({
            'loaded.jpg': (Path(obs['screenshot_path']), obs['screenshot_sha256']),
            'selected.jpg': (Path(obs['selected_screenshot_path']), obs['selected_screenshot_sha256']),
            'load-boundary.jpg': (Path(boundary['screenshot_path']), boundary['screenshot_sha256']),
            'case.bcs': (Path(prep['game'])/'override'/(row['script']+'.bcs'), row['script_sha256'])})
        for name, (source, expected) in ancillary.items():
            require(digest(source) == expected, 'Validated evidence changed before freezing: '+name)
            shutil.copy2(source, folder/name)
            require(digest(source) == expected == digest(folder/name), 'Ancillary evidence changed while freezing: '+name)
        result.update(verdict='original-case-observed', case_id=row['spec']['id'], number=row['number'],
                      nonce=prep['nonce'], executable_sha256=prep['executable_sha256'],
                      script_sha256=row['script_sha256'], input_files=row['fixture_files'],
                      values=values['values'], serialized_observation=values,
                      autosave_files=before, autosave_directory=str(frozen.resolve()),
                      observation=dict(window_id=obs['window']['id'], window_app=obs['window']['app'],
                          window_title=obs['window']['title'], loaded_fixture=obs['loaded_fixture'],
                          captured_utc=obs['captured_utc'], method=obs['method'],
                          load_boundary_screenshot_sha256=boundary['screenshot_sha256']),
                      scope='Observed GUI load plus hash-bound serialized query results. No runtime cache, target-memory or query side-effect proof.')
    except (OSError, ValueError, KeyError, TypeError) as error:
        result['error'] = str(error)
    shutil.copy2(Path(__file__), folder/'capture_weapon_original.py')
    write(folder/'result.json', result)
    write(folder/'artifact-manifest.json', {'files': api_manifest(folder)})
    print(json.dumps({k: result[k] for k in ('directory', 'verdict', 'case_id', 'values', 'error') if k in result}, indent=2))
    return 0 if result['verdict'] == 'original-case-observed' else 1


def api_manifest(folder):
    return {p.relative_to(folder).as_posix(): dict(bytes=p.stat().st_size, sha256=digest(p))
            for p in sorted(folder.rglob('*')) if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--observation', type=Path, required=True)
    parser.add_argument('--results-root', type=Path, required=True)
    args = parser.parse_args()
    return finalize(args.preparation, args.observation, args.results_root)


if __name__ == '__main__':
    raise SystemExit(main())
