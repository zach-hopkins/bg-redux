"""Reject false baseline success, stale evidence and unreviewed changes."""
from pathlib import Path
import copy
import io
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import baseline_runner as runner


class BaselineEvidence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        runner.write(path, value)

    def native(self, kind='vanilla'):
        folder = self.root/('20260101T000000Z-test-'+kind+'-1234')
        folder.mkdir()
        names = ['import','reload-1','reload-2','repeat-import'] if kind == 'vanilla' else ['gui-save','gui-reload']
        stages = []
        for index, name in enumerate(names):
            stage = dict(name=name, passed=True, process=dict(exit_code=0, timed_out=False))
            if kind == 'vanilla':
                self.write(folder/name/'state.json', dict(schema='bg-redux-state/1'))
            else:
                self.write(folder/name/'gui-result.json', dict(completed=True))
                stage['assertions'] = [dict(passed=True)]*(13 if index == 0 else 7)
                for capture in ('00-game','01-inventory','02-record'):
                    self.write(folder/name/(capture+'.ui.json'), dict(controls=[]))
                    (folder/name/(capture+'.bmp')).write_bytes(b'BM'+b'\0'*54)
            stages.append(stage)
        data = dict(run_id=folder.name, artifacts=str(folder), stages=stages,
                    schema='bg-redux-save-run/1' if kind == 'vanilla' else 'bg-redux-gui-run/1',
                    execution_verdict='passed', assertion_verdict='passed', verdict='differences')
        if kind == 'vanilla':
            data.update(assertions=[dict(passed=True)]*24, source_unchanged=True, input_copy_unchanged=True,
                        wire_oracle=dict(checks=1,passed=0,differences=[dict(field='party/0/hp',expected=1,actual=2)]),
                        comparisons=[dict(cycle=c, semantic_differences=0, passed=True) for c in (1,2)],
                        repeat_import=dict(semantic_differences=1),
                        provenance=dict(engine_dll_sha256='engine'), fixture=dict(files={'input':'hash'}))
            self.write(folder/'wire-oracle.json', data['wire_oracle'])
            for cycle in (1,2):
                self.write(folder/f'reload-{cycle}-semantic-diff.json', [])
            self.write(folder/'repeat-import-semantic-diff.json', [dict(path='/current_area_actors/2/base_stats/208',before=1,after=2)])
        else:
            data.update(fixture_unchanged=True, created_save_unchanged_on_reload=True,
                        persistence=dict(differences=1, scopes={'current_area':dict(differences=1)}),
                        legacy_semantic_diagnostic=dict(differences=1),
                        provenance=dict(build=dict(engine_dll_sha256='engine'), fixture={'input':'hash'}))
            self.write(folder/'gui-reload-differences.json', [dict(path='/game_time',before=1,after=2)])
            self.write(folder/'legacy-semantic-differences.json', [dict(path='/current_area_actors/2/effects/length',before=7,after=14)])
        self.write(folder/'result.json', data)
        return folder, data

    def test_differences_are_not_a_pass_override(self):
        folder, data = self.native()
        result = runner.validate_native('vanilla', folder, data, dict(exit_code=1, timed_out=False))
        self.assertEqual(result['execution'], 'passed')
        self.assertEqual(result['compatibility'], 'differences')
        self.assertEqual(result['assertions']['passed'], 24)

    def test_exit_zero_cannot_contradict_reported_differences(self):
        folder, data = self.native()
        with self.assertRaisesRegex(ValueError, 'exit contradicts'):
            runner.validate_native('vanilla', folder, data, dict(exit_code=0))

    def test_success_metadata_cannot_hide_failed_assertion(self):
        folder, data = self.native()
        data['assertions'] = copy.deepcopy(data['assertions'])
        data['assertions'][0]['passed'] = False
        with self.assertRaisesRegex(ValueError, 'coverage missing or failed'):
            runner.validate_native('vanilla', folder, data, dict(exit_code=1))

    def test_missing_reload_stage_is_not_success(self):
        folder, data = self.native()
        data['stages'].pop(1)
        with self.assertRaisesRegex(ValueError, 'Missing or reordered'):
            runner.validate_native('vanilla', folder, data, dict(exit_code=1))

    def test_native_timeout_cannot_hide_behind_passed_metadata(self):
        folder, data = self.native()
        data['stages'][0]['process']['timed_out'] = True
        with self.assertRaisesRegex(ValueError, 'failed or timed out'):
            runner.validate_native('vanilla', folder, data, dict(exit_code=1))

    def test_missing_state_artifact_does_not_pass(self):
        folder, data = self.native()
        (folder/'reload-1/state.json').unlink()
        with self.assertRaises(FileNotFoundError):
            runner.validate_native('vanilla', folder, data, dict(exit_code=1))

    def test_changed_raw_comparison_cannot_hide_in_result_counts(self):
        folder, data = self.native()
        self.write(folder/'reload-1-semantic-diff.json', [dict(path='/party/0/base_stats/0',before=47,after=1)])
        with self.assertRaisesRegex(ValueError, 'artifact contradicts'):
            runner.validate_native('vanilla', folder, data, dict(exit_code=1))

    def test_gui_requires_completion_and_screenshot_artifacts(self):
        folder, data = self.native('gui')
        self.assertEqual(runner.validate_native('gui', folder, data, dict(exit_code=1))['assertions']['total'], 20)
        (folder/'gui-reload/01-inventory.bmp').write_bytes(b'not a bitmap')
        with self.assertRaisesRegex(ValueError, 'screenshot missing/invalid'):
            runner.validate_native('gui', folder, data, dict(exit_code=1))

    def test_gui_incomplete_native_artifact_is_not_success(self):
        folder, data = self.native('gui')
        self.write(folder/'gui-save/gui-result.json', dict(completed=False))
        with self.assertRaisesRegex(ValueError, 'completion artifact'):
            runner.validate_native('gui', folder, data, dict(exit_code=1))

    def test_existing_result_cannot_be_reused_as_fresh(self):
        folder, data = self.native()
        with self.assertRaisesRegex(ValueError, 'found 0'):
            runner.fresh_result(self.root, {folder.name}, 'test-vanilla', data['schema'])

    def test_result_identity_must_match_new_directory(self):
        folder, data = self.native()
        data['run_id'] = 'old-run'
        self.write(folder/'result.json', data)
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            runner.fresh_result(self.root, set(), 'test-vanilla', data['schema'])

    def test_unknown_differences_need_review_without_reference(self):
        self.assertEqual(runner.difference_disposition('gui', {})['status'], 'unreviewed-differences')

    def test_color_variability_is_known_only_with_same_wire_and_reload_evidence(self):
        evidence = dict(wire=[dict(field='party/0/hp',expected=41,actual=57)], reloads=[[],[]],
                        repeat=[dict(path='/current_area_actors/0/base_stats/208',before=1,after=2)])
        changed = copy.deepcopy(evidence)
        changed['repeat'][0]['after'] = 5
        self.assertEqual(runner.difference_disposition('vanilla', changed, evidence)['status'], 'known-differences')
        changed['wire'][0]['actual'] = 999
        self.assertEqual(runner.difference_disposition('vanilla', changed, evidence)['status'], 'unreviewed-differences')

    def test_damage_is_not_classified_as_color_variability(self):
        evidence = dict(wire=[], reloads=[[],[]], repeat=[dict(path='/current_area_actors/0/base_stats/208',before=1,after=2)])
        changed = copy.deepcopy(evidence)
        changed['repeat'][0]['path'] = '/current_area_actors/0/base_stats/0'
        self.assertEqual(runner.difference_disposition('vanilla', changed, evidence)['status'], 'unreviewed-differences')

    def test_changed_effect_parameter_exceeds_gui_reference(self):
        evidence = dict(legacy=[dict(path='/current_area_actors/2/effects/0/parameters/0',before=1,after=2)],
                        persistence_scopes={'current_area':dict(differences=1)})
        self.assertEqual(runner.difference_disposition('gui', evidence, evidence)['status'], 'known-differences')
        changed = copy.deepcopy(evidence); changed['legacy'][0]['after'] = 999
        self.assertEqual(runner.difference_disposition('gui', changed, evidence)['status'], 'unreviewed-differences')

    def test_reference_engine_mismatch_is_rejected(self):
        folder, data = self.native()
        current = copy.deepcopy(data); current['provenance']['engine_dll_sha256'] = 'other engine'
        with self.assertRaisesRegex(ValueError, 'engine/fixture/observer differs'):
            runner.load_reference('vanilla', folder, current)

    def test_manifest_detects_missing_changed_and_extra_fixture_members(self):
        fixture = self.root/'fixture'; fixture.mkdir()
        (fixture/'a').write_bytes(b'baseline')
        expected = runner.files_manifest(fixture)
        (fixture/'a').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'manifest mismatch'):
            runner.check_manifest(fixture, expected)
        (fixture/'a').write_bytes(b'baseline'); (fixture/'unexpected').write_bytes(b'new')
        with self.assertRaisesRegex(ValueError, 'manifest mismatch'):
            runner.check_manifest(fixture, expected)

    def test_external_build_source_drift_is_refused(self):
        binary = self.root/'phase0-local/native-probe/Redux_save_probe.exe'
        source = self.root/'tools/phase0/native/save_probe.cpp'
        core = self.root/'phase0-local/build/gemrb/libgemrb_core.dll'
        compiler = self.root/'phase0-local/toolchain/msys64/ucrt64/bin/g++.exe'
        for path in (binary,source,core,compiler):
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(path.name.encode())
        receipt = dict(exit_code=0, binary_sha256=runner.sha(binary), source_sha256=runner.sha(source),
                       engine_dll_sha256=runner.sha(core),compiler_sha256=runner.sha(compiler))
        self.write(binary.parent/'build.json', receipt)
        runner.check_build(self.root, 'save')
        source.write_bytes(b'new code')
        with self.assertRaisesRegex(ValueError, 'source drift'):
            runner.check_build(self.root, 'save')

    def test_owned_process_timeout_is_recorded_and_bounded(self):
        import os
        result = runner.execute([sys.executable,'-c','import time; time.sleep(20)'], self.root,
                                os.environ.copy(), self.root/'timeout.log', 0.1)
        self.assertTrue(result['timed_out'])
        self.assertNotEqual(result['exit_code'], 0)
        self.assertLess(result['elapsed_seconds'], 16)

    def test_unit_setup_error_is_not_subtracted_from_real_success_count(self):
        tests = self.root/'tools/phase0/tests'; tests.mkdir(parents=True)
        (tests/'test_worker_fixture.py').write_text('''import unittest
class Passed(unittest.TestCase):
    def test_ok(self): pass
class MissingFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls): raise RuntimeError("missing fixture")
    def test_never_runs(self): pass
''')
        report = self.root/'units.json'
        with patch.object(unittest, 'defaultTestLoader', unittest.TestLoader()), patch('sys.stderr', io.StringIO()):
            self.assertEqual(runner.run_units(self.root, report), 1)
        result = runner.read(report)
        self.assertEqual(result['executed'], 1)
        self.assertEqual(result['passed'], 1)
        self.assertEqual(result['errors'], 1)
        self.assertFalse(result['success'])


if __name__ == '__main__':
    unittest.main()
