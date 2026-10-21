"""Check this audit's local links, pinned source anchors and truthful run flags."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

root = Path(__file__).resolve().parents[2]
docs = root / 'docs'
repo = root / 'gemrb'
evidence_path = docs / 'phase0-evidence.json'
evidence = json.loads(evidence_path.read_text(encoding='utf-8'))
revision = evidence['revision']
# A documentation check must never manufacture or rewrite runtime outcomes.
# Historical declarations remain bound to their linked execution receipts.
recorded_build_run = evidence.get('build_executed') is True
recorded_runtime_run = evidence.get('runtime_tests_executed') is True
files = [docs / 'BG_REDUX_PHASE0_AUDIT.md', docs / 'charter/BG_REDUX_CODEX_PROJECT_CHARTER.md',
         docs / 'compatibility/bg2ee-baseline.md', docs / 'compatibility/upstream-issue-roadmap.md',
         docs / 'risks/modernization-risk-register.md', docs / 'roadmap/first-native-change.md']
files += sorted((docs / 'architecture').glob('*.md'))
files += sorted((docs / 'testing').glob('*.md'))
links = citations = 0
for path in files:
    content = path.read_text(encoding='utf-8')
    assert content.count('```') % 2 == 0, path
    for url in re.findall(r'\]\(([^)]+)\)', content):
        if url.startswith('http'):
            marker = f'https://github.com/gemrb/gemrb/blob/{revision}/'
            if url.startswith(marker):
                relative, _, anchor = url[len(marker):].partition('#L')
                source = repo / relative
                assert source.is_file(), url
                if anchor:
                    assert 1 <= int(anchor) <= len(source.read_text(encoding='utf-8').splitlines()), url
                citations += 1
        elif not url.startswith('#'):
            assert (path.parent / url).resolve().exists(), (path, url)
            links += 1
for anchor in evidence['source_anchors'].values():
    actual = (repo / anchor['path']).read_text(encoding='utf-8').splitlines()[anchor['line'] - 1].strip()
    assert actual == anchor['text'].strip(), anchor
charter_copy = docs / 'charter/BG_REDUX_CODEX_PROJECT_CHARTER.md'
charter_original = Path('C:/Users/zach/Downloads/BG_REDUX_CODEX_PROJECT_CHARTER (1).md')
charter_digest = hashlib.sha256(charter_copy.read_bytes()).hexdigest()
assert charter_digest == evidence['charter_sha256'], 'Charter differs from recorded original hash'
if charter_original.is_file():
    assert charter_digest == hashlib.sha256(charter_original.read_bytes()).hexdigest()
status = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain=v1'], text=True)
diff = subprocess.check_output(['git', '-C', str(repo), 'diff', '--stat'], text=True)
assert not status.strip() and not diff.strip()
validation = dict(revision=revision, audit_date='2026-10-20', documentation_files_checked=len(files),
    source_anchor_definitions_checked=len(evidence['source_anchors']), source_citation_occurrences_checked=citations,
    internal_links_checked=links, charter_copy_byte_identical=True,
    charter_comparison_source='Original attachment' if charter_original.is_file() else 'Recorded original SHA256',
    engine_git_status_porcelain=status,
    engine_git_diff_stat=diff, engine_build_run=recorded_build_run, engine_runtime_tests_run=recorded_runtime_run,
    execution_flags_source='Historical phase0-evidence.json declarations; this validation does not execute builds or runtime tests',
    result_inventory='compatibility/evidence/baseline-results.json',
    vanilla_save_import_run=evidence.get('save_harness_update',{}).get('original_fixture_import_succeeded',False),
    normal_gui_save_load_run=evidence.get('gui_harness_update',{}).get('normal_gui_create_cancel_overwrite_and_fresh_reload_executed',False),
    note='Documentation/link/source checks plus explicit run status. Library import/reload and normal GUI create/cancel/overwrite/fresh reload executed; expanded core locale failure/skips remain. GUI content coverage passes while incomplete EE presentation, IMMCLOUD effect differences, controlled timing and native-like gates remain open.')
(docs / 'phase0-validation.json').write_text(json.dumps(validation, indent=2) + '\n', encoding='utf-8')
print(json.dumps(validation, indent=2))
