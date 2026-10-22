import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import weapon_query_observer as observer
import weapon_inventory_journey as journey


class PrivateObserverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root/'phase0-local/bg2ee-clean'; self.game.mkdir(parents=True)
        for name, data in [('chitin.key', b'KEY fixture'), ('engine.lua', b'config'),
                           ('GemRB.log', b'old log'), ('gemrb_path.txt', b'old path')]:
            (self.game/name).write_bytes(data)
        self.output = self.root/'result'; self.output.mkdir()

    def test_preparation_frozen_private_writes_allowed_source_exactly_unchanged(self):
        receipt = observer.prepare_private_game(self.root, self.output)
        wrapper = Path(receipt['game'])
        (wrapper/'GemRB.log').write_bytes(b'new private log')
        (wrapper/'gemrb_path.txt').write_bytes(b'new private path')
        result = observer.validate_private_game(receipt, self.output)
        self.assertEqual(set(result['allowed_private_root_changes']), {'GemRB.log', 'gemrb_path.txt'})
        self.assertEqual((self.game/'GemRB.log').read_bytes(), b'old log')
        self.assertTrue(result['clean_game_root_hashes_unchanged'])
        saved = observer.read(self.output/'private-game-preparation.json')
        saved['source'] = 'forged'; observer.write(self.output/'private-game-preparation.json', saved)
        with self.assertRaisesRegex(ValueError, 'preparation changed'):
            observer.validate_private_game(receipt, self.output)

    def test_actual_source_log_write_rejected_and_after_evidence_retained(self):
        receipt = observer.prepare_private_game(self.root, self.output)
        (self.game/'GemRB.log').write_bytes(b'unexpected source write')
        with self.assertRaisesRegex(ValueError, 'Protected clean-game'):
            observer.validate_private_game(receipt, self.output)
        after = observer.read(self.output/'private-game-source-after.json')
        self.assertNotEqual(after['root_sha256'], receipt['source_before']['root_sha256'])

    def test_owned_manifest_excludes_shared_asset_subtrees_but_keeps_private_logs(self):
        wrapper = self.output/'private-game'; (wrapper/'data').mkdir(parents=True)
        (wrapper/'data/shared-asset.bif').write_bytes(b'do not enumerate shared assets')
        (wrapper/'GemRB.log').write_bytes(b'private log')
        (self.output/'capture.json').write_bytes(b'{}')
        rows = observer.result_manifest(self.output)
        self.assertEqual(set(rows), {'capture.json', 'private-game/GemRB.log'})
        self.assertEqual(rows['private-game/GemRB.log']['sha256'], observer.sha(wrapper/'GemRB.log'))

    def test_required_sources_bind_helper_for_both_hosts_and_reject_import_escape(self):
        for kind in ('six-hand-query', 'inventory-mutation-journey'):
            self.assertIn('private_game.py', {p.name for p in observer.required_sources(kind)})
        with patch.object(observer.private_game, '__file__', str(self.root/'other/private_game.py')):
            with self.assertRaisesRegex(ValueError, 'escaped'):
                observer.required_sources()

    def _run_mocked_host(self, is_journey, source_write=False):
        fixture = self.root/'fixture'; fixture.mkdir()
        (fixture/'baldur.gam').write_bytes(b'fixed input')
        script = self.root/'script.bcs'; script.write_bytes(b'fixed script')
        binary = self.root/'host.exe'; binary.write_bytes(b'never executed')
        build_receipt = self.root/'build.json'; observer.write(build_receipt, {})
        preparation = self.root/'preparation.json'; observer.write(preparation, {})
        case_id = '02-plus-normal-pfmw'
        row = dict(spec=dict(id=case_id, main='sw1h02', off='sw1h01', defense=[120, 0, 1]),
                   fixture=str(fixture), fixture_files=observer.manifest(fixture),
                   script='P1TEST01', script_path=str(script), script_sha256=observer.sha(script))
        protected = dict(source={}, binaries={}, fixture={})
        launches = []
        def execute(command, cwd, env, log, timeout):
            # No subprocess: inspect the actual runner-generated config at its launch boundary.
            cfg = Path(command[command.index('--config')+1])
            config = dict(line.split('=', 1) for line in cfg.read_text(encoding='utf-8').splitlines())
            wrapper = Path(config['GamePath'])
            self.assertEqual(wrapper, self.output/'private-game')
            self.assertNotEqual(wrapper, self.game)
            self.assertTrue((self.output/'private-game-preparation.json').is_file())
            (wrapper/'GemRB.log').write_bytes(b'private runtime log')
            (wrapper/'gemrb_path.txt').write_bytes(b'private runtime path')
            if source_write: (self.game/'GemRB.log').write_bytes(b'bad source write')
            launches.append(config)
            return dict(exit_code=0, timed_out=False)
        api = SimpleNamespace(baseline_runner=SimpleNamespace(preflight=lambda p: {}, protected=lambda p: protected,
                              execute=execute), query_side_effects=SimpleNamespace(verify_game=lambda p: {}),
                              harness=SimpleNamespace(environment=lambda p: {}),
                              equipped_defenses=SimpleNamespace(embedded=lambda *a: (None, b'\0'*0x248+b'P1TEST01')))
        args = SimpleNamespace(project_root=self.root, engine_source_root=self.root/'source',
             engine_build_root=self.root/'build', results_root=self.root, build_receipt=build_receipt,
             preparation=preparation, repeats=1, timeout=1, cases=None, original_receipts=[],
             require_rng_observed=False, rng_control_draw=False)
        receipt = dict(binary=str(binary), sources={},
                       kind='inventory-mutation-journey' if is_journey else 'six-hand-query')
        query_observation = dict(rng_control_draw_call=None, collected_state_unchanged=True, rng_unchanged=None,
                                 stable_values=True, original_match=None, mutation_observations=[])
        journey_observation = dict(query_mutation_steps=[], unstable_query_steps=[], cache_mismatch_steps=[])
        with patch.object(observer, 'phase0', return_value=api), \
                patch.object(observer, 'candidate_inventory', return_value={}), \
                patch.object(observer, 'new_output', return_value=self.output), \
                patch.object(observer, 'check_build', return_value=receipt), \
                patch.object(observer, 'check_preparation', return_value=({'cases': [row], 'item_metadata': {}}, [row])), \
                patch.object(observer, 'equipment_guard'), \
                patch.object(observer, 'validate_capture', return_value=query_observation), \
                patch.object(journey, 'validate_journey', return_value=journey_observation):
            status = journey.run_journey(args) if is_journey else observer.run_queries(args)
        self.assertEqual(len(launches), 1)
        result = observer.read(self.output/'result.json')
        self.assertEqual(status, 1 if source_write else 0)
        self.assertTrue((self.output/'artifact-manifest.json').is_file())
        if source_write:
            self.assertEqual(result['verdict'], 'failed')
            self.assertIn('Protected clean-game', result['private_game_preservation_error'])
        else:
            self.assertTrue(result['private_game_validation']['clean_game_root_hashes_unchanged'])

    def test_query_runner_launch_boundary_uses_private_game(self): self._run_mocked_host(False)
    def test_journey_runner_launch_boundary_uses_private_game(self): self._run_mocked_host(True)
    def test_query_runner_fails_source_root_write(self): self._run_mocked_host(False, True)
    def test_journey_runner_fails_source_root_write(self): self._run_mocked_host(True, True)


class PrivateBuildBindingTests(unittest.TestCase):
    def test_omitted_helper_and_frozen_helper_drift_require_fresh_build(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); sources = observer.required_sources()
            frozen = root/'sources'; frozen.mkdir()
            rows = {}
            for source in sources:
                target = frozen/source.name; shutil.copy2(source, target)
                rows[str(source)] = dict(sha256=observer.sha(source), frozen=str(target))
            for name in ('binary', 'compiler'): (root/name).write_bytes(name.encode())
            receipt = dict(schema='bg-redux-phase1-weapon-query-build/1', verdict='built-not-executed',
                kind='six-hand-query', project=str(root), engine_source_root=str(root), engine_build_root=str(root),
                candidate_preserved=True, candidate_inventory={}, phase0_preservation=dict(source=True, binaries=True, fixture=True),
                process=dict(exit_code=0, timed_out=False), binary=str(root/'binary'), binary_sha256=observer.sha(root/'binary'),
                compiler=str(root/'compiler'), compiler_sha256=observer.sha(root/'compiler'), sources=rows)
            path = root/'build.json'; observer.write(path, receipt)
            with patch.object(observer, 'candidate_inventory', return_value={}):
                observer.check_build(path, root, root, root)
                helper = next(key for key in rows if Path(key).name == 'private_game.py')
                saved = receipt['sources'].pop(helper); observer.write(path, receipt)
                with self.assertRaisesRegex(ValueError, 'required source inventory'):
                    observer.check_build(path, root, root, root)
                receipt['sources'][helper] = saved; observer.write(path, receipt)
                Path(saved['frozen']).write_bytes(b'altered helper')
                with self.assertRaisesRegex(ValueError, 'source changed'):
                    observer.check_build(path, root, root, root)
