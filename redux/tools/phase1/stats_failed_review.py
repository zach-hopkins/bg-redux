"""Review a completed Stats rejection without changing its acceptance result."""
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('redux_stats_strict_review', Path(__file__).with_name('stats_validation.py'))
strict = importlib.util.module_from_spec(spec)
spec.loader.exec_module(strict)


def differences(before, after, path=''):
    if type(before) is not type(after):
        return [dict(path=path, before=before, after=after)]
    rows = []
    if isinstance(before, dict):
        for key in sorted(set(before) | set(after)):
            if key not in before or key not in after:
                rows.append(dict(path=path+'/'+key, before=before.get(key), after=after.get(key)))
            else:
                rows.extend(differences(before[key], after[key], path+'/'+key))
    elif isinstance(before, list):
        if len(before) != len(after):
            rows.append(dict(path=path+'/length', before=len(before), after=len(after)))
        for index, (a, b) in enumerate(zip(before, after)):
            rows.extend(differences(a, b, path+'/'+str(index)))
    elif before != after:
        rows.append(dict(path=path, before=before, after=after))
    return rows


def review_completed_world_difference(directory, resolution, *, expected_nonce, tlk_path):
    """All preceding strict checks must pass; this never returns acceptance."""
    directory = Path(directory)
    try:
        strict.validate_stage(directory, resolution, expected_nonce=expected_nonce, tlk_path=tlk_path)
    except ValueError as error:
        if str(error) != 'Stats journey changed collected world':
            raise
        rejection = str(error)
    else:
        raise ValueError('Forensic review requires the completed world-difference rejection')
    read = lambda name: json.loads((directory/name).read_text(encoding='utf8'))
    rows = differences(read('before.state.json'), read('after.state.json'))
    require_changes = [r for r in rows if r['path'] != '/selection']
    if not require_changes:
        raise ValueError('Strict world rejection has no undeclared changed fields')
    paths = [directory/name for name in ('menu-host-result.json','menu-runtime.json',
                                       'before.state.json','after.state.json','process.log')]
    paths += list(directory.glob('capture-*')) + list(directory.glob('callback-*'))
    paths += [Path(tlk_path), Path(__file__), Path(__file__).with_name('stats_validation.py')]
    pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
    return dict(schema='bg-redux-stats-completed-failure-review/1', accepted=False,
                forensic_review_completed=True, strict_rejection=rejection,
                preceding_strict_ui_numeric_callback_checks_completed=True,
                raw_differences=rows, undeclared_changes=require_changes, files=pins,
                cause_or_gameplay_equivalence_proven=False, independent_worker_audit=False)
