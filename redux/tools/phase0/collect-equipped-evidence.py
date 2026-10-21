"""Compare frozen, independently observed equipped-query saves without launching a game."""
import datetime
import json
from pathlib import Path
from harness import ROOT, digest
from save_harness import manifest, member, write
from script_query_probe import query_values
from legacy_oracle import read_wire
from equipped_defenses import CASES, observe, validate_observation


def main():
    evidence = ROOT / 'docs/compatibility/evidence'
    native_path = evidence / 'equipped-defense-results.json'
    native = json.loads(native_path.read_text())
    if native['verdict'] != 'gemrb-cases-executed':
        raise ValueError('Native suite incomplete')
    rows = []
    for spec in json.loads(json.dumps(CASES)):
        matches = [c for c in native['cases'] if c['spec'] == spec]
        if len(matches) != 1:
            raise ValueError('Native case absent/ambiguous')
        n = matches[0]
        path = evidence / ('original-equipped-' + spec['id'] + '.json')
        original = json.loads(path.read_text())
        if original['verdict'] != 'original-case-observed' or original['case']['spec'] != spec:
            raise ValueError('Original case incomplete')
        if original['case']['files'] != n['construction']['input_files']:
            raise ValueError('Original/native inputs differ')
        frozen = Path(original['directory']) / 'autosave'
        if manifest(frozen) != original['autosave_files']:
            raise ValueError('Frozen original output drift')
        if manifest(Path(n['output']['folder'])) != n['output']['files']:
            raise ValueError('Native output drift')
        for folder, recorded in ((frozen, original['values']), (Path(n['output']['folder']), n['output']['values'])):
            gam = member(folder, 'gam')
            if query_values(read_wire(gam)['globals']) != recorded:
                raise ValueError('Recorded query values differ from output')
            validate_observation(spec, observe(gam))
        if n['process']['exit_code'] != 0 or n['process']['timed_out']:
            raise ValueError('Native process did not complete')
        rows.append(dict(id=spec['id'], original=original['values'], gemrb=n['output']['values'],
                         mismatching_predicates=[k for k in ('RDXVE', 'RDXVD') if original['values'][k] != n['output']['values'][k]],
                         original_receipt=path.name, original_receipt_sha256=digest(path)))
    result = dict(schema='bg-redux-equipped-comparison/1', utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  cases=rows, cases_with_mismatches=sum(bool(r['mismatching_predicates']) for r in rows),
                  mismatching_predicates=sum(len(r['mismatching_predicates']) for r in rows),
                  native_receipt_sha256=digest(native_path), source_sha256=digest(Path(__file__)),
                  scope='Synthetic equipped MAINHAND queries against party member 2; not damage or full predicate parity',
                  verdict='comparison-executed-with-differences')
    write(evidence / 'original-equipped-comparison.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
