"""Fresh original combat visual attestations require exact run bindings.

Only temp fixture files are written; no preparation or game process is started.
"""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1]/'original_live_capture.py'
SPEC = importlib.util.spec_from_file_location('original_live_capture_review', MODULE)
capture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture)
NOW = datetime(2026, 10, 21, 23, 59, tzinfo=timezone.utc)


def write(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CaptureValidation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.run_id = '20261021T230000Z-original-live-0123abcd'
        self.nonce = 'ABCDEF01'
        self.case = 'ai-imoen-stock'
        self.run = self.root/self.run_id
        self.run.mkdir()
        self.game = self.root/'private-game'
        (self.game/'lang/en_US').mkdir(parents=True)
        (self.game/'override').mkdir()
        self.profile = self.root/'Documents/BGReduxLab'/self.run_id
        self.fixture = self.profile/'save'/f'000000001-{self.case}-{self.nonce}'
        self.fixture.mkdir(parents=True)
        paths = {'Baldur.exe': b'nominated binary', 'lang/en_US/dialog.tlk': b'private TLK',
                 'engine.lua': f'engine_name = "BGReduxLab/{self.run_id}"\nengine_mode = 1\n'.encode(),
                 'steam_api64.dll.phase0-retained': b'retained optional library',
                 'override/RDXL0001.bcs': b'bound live program'}
        for relative, payload in paths.items():
            (self.game/relative).write_bytes(payload)
        gam = bytearray(0x400)
        gam[:8] = b'GAMEV2.0'
        struct.pack_into('<II', gam, 0x20, 0x40, 1)
        struct.pack_into('<II', gam, 0x44, 0x100, 0x2d4)
        gam[0x100:0x108] = b'CRE V1.0'
        gam[0x348:0x350] = b'RDXL0001'
        (self.fixture/'BALDUR.gam').write_bytes(gam)
        (self.fixture/'BALDUR.SAV').write_bytes(b'fixture save bytes')
        self.image = self.run/'observed.jpg'
        self.boundary_image = self.run/'load.jpg'
        # Signature fixtures only; validator expressly does not claim image decoding/OCR.
        self.image.write_bytes(b'\xff\xd8\xff'+b'captured-image-signature-fixture'*2+b'\xff\xd9')
        self.boundary_image.write_bytes(b'\xff\xd8\xff'+b'load-image-signature-fixture'*2+b'\xff\xd9')
        self.window = dict(app='process:'+str(self.game/'Baldur.exe'), id=123,
                           title=f'BGReduxLab/{self.run_id} - v2.7.3.0')
        self.row = dict(spec=dict(id=self.case, first=115), nonce=self.nonce, script='RDXL0001',
                        script_sha256=digest(self.game/'override/RDXL0001.bcs'),
                        fixture=str(self.fixture), fixture_files=self.manifest(),
                        strings=[f'RDX {self.nonce} {self.case} SEEN',
                                 f'RDX {self.nonce} {self.case} B115 ENTER',
                                 f'RDX {self.nonce} {self.case} B115 RETURN'],
                        construction=dict(input_files={'deliberately': 'precursor metadata, not final'},
                                          ai_script_sha256='precursor'))
        self.prep = dict(schema='bg-redux-original-live-preparation/1', run_id=self.run_id,
                         directory=str(self.run), game=str(self.game), profile=str(self.profile),
                         nonce=self.nonce, cases=[self.row], executable_sha256=digest(self.game/'Baldur.exe'),
                         private_tlk_sha256=digest(self.game/'lang/en_US/dialog.tlk'),
                         engine_lua_sha256=digest(self.game/'engine.lua'),
                         retained_optional_steam_dll_sha256=digest(self.game/'steam_api64.dll.phase0-retained'))
        self.obs = dict(case=self.case, nonce=self.nonce, selected_branch=115, phase='ENTER',
                        window=self.window.copy(), screenshot_path=str(self.image), screenshot_sha256=digest(self.image),
                        observed_at_utc='2026-10-21T23:03:00Z',
                        observations=[f'RDX {self.nonce} {self.case} SEEN', f'RDX {self.nonce} {self.case} B115 ENTER',
                                      'Attack feedback and Smoke Mephit takes 7/22 slashing damage visible in same history'],
                        queue_completion_observed=False, exact_action_memory_sample=False, save_required=False)
        self.launch = dict(pid=12, started_utc='2026-10-21T23:01:00Z', executable=str(self.game/'Baldur.exe'),
                           sha256=self.prep['executable_sha256'])
        self.isolation = dict(window=self.window.copy(), captured_at_utc='2026-10-21T23:02:00Z',
                              observed=f'Exactly 1 prepared nonce {self.nonce} cases, no personal/cloud saves visible at actual load boundary',
                              path=str(self.boundary_image), sha256=digest(self.boundary_image))

    def manifest(self):
        return {p.relative_to(self.fixture).as_posix():dict(bytes=p.stat().st_size,sha256=digest(p))
                for p in self.fixture.rglob('*') if p.is_file()}

    def receipts(self):
        for name, value in [('preparation.json',self.prep),('observation.json',self.obs),
                            ('launch.json',self.launch),('load-boundary.json',self.isolation)]:
            write(self.run/name, value)

    def validate(self):
        self.receipts()
        return capture.validate_capture(self.run/'preparation.json', self.run/'observation.json', now=NOW)

    def rejected(self, pattern):
        with self.assertRaisesRegex(capture.CaptureError, pattern):
            self.validate()

    def test_fresh_entry_and_combat_feedback_accepted_without_completion_claim(self):
        result = self.validate()
        self.assertEqual(result['selected_branch'],115)
        self.assertFalse(result['queue_completion_observed'])
        self.assertFalse(result['exact_action_memory_sample'])
        self.assertFalse(result['exact_target_memory_sample'])
        self.assertFalse(result['dpr_comparison'])
        self.assertFalse(result['process_liveness_verified'])
        self.assertIn('precursor metadata only', result['fixture_manifest_authority'])

    def test_return_requires_return_marker_and_explicit_queue_attestation(self):
        self.obs['phase'] = 'RETURN'
        self.obs['queue_completion_observed'] = True
        self.obs['observations'][1] = f'RDX {self.nonce} {self.case} B115 RETURN'
        result = self.validate()
        self.assertTrue(result['queue_completion_observed'])
        self.assertFalse(result['exact_action_memory_sample'])

    def test_wrong_nonce_rejected(self):
        self.obs['nonce'] = 'DEADBEEF'
        self.rejected('nonce')

    def test_old_marker_rejected_even_with_current_metadata_nonce(self):
        self.obs['observations'][1] = f'RDX DEADBEEF {self.case} B115 ENTER'
        self.rejected('marker')

    def test_wrong_case_rejected(self):
        self.obs['case'] = 'ai-default-stock'
        self.rejected('case')

    def test_wrong_branch_rejected(self):
        self.obs['selected_branch'] = 307
        self.rejected('branch')

    def test_entry_does_not_certify_queue_completion(self):
        self.obs['queue_completion_observed'] = True
        self.rejected('queue-completion')

    def test_memory_sample_claim_rejected(self):
        self.obs['exact_action_memory_sample'] = True
        self.rejected('memory')

    def test_missing_seen_or_branch_marker_rejected(self):
        self.obs['observations'].pop(0)
        self.rejected('marker')

    def test_missing_combat_feedback_rejected(self):
        self.obs['observations'] = self.obs['observations'][:2]
        self.rejected('combat-feedback')

    def test_missing_screenshot_hash_rejected(self):
        self.obs.pop('screenshot_sha256')
        self.rejected('SHA256')

    def test_changed_screenshot_rejected(self):
        self.image.write_bytes(self.image.read_bytes()+b'altered')
        self.rejected('Hash drift')

    def test_invalid_screenshot_signature_rejected_even_when_hash_matches(self):
        self.image.write_bytes(b'not an image')
        self.obs['screenshot_sha256'] = digest(self.image)
        self.rejected('signature')

    def test_private_window_title_mismatch_rejected(self):
        self.obs['window']['title'] = 'unrelated game'
        self.rejected('window')

    def test_private_window_app_mismatch_rejected(self):
        self.obs['window']['app'] = 'process:C:/personal/Baldur.exe'
        self.rejected('window')

    def test_observation_before_launch_rejected(self):
        self.obs['observed_at_utc'] = '2026-10-21T23:00:30Z'
        self.rejected('timestamp')

    def test_observation_before_load_boundary_rejected(self):
        self.obs['observed_at_utc'] = '2026-10-21T23:01:30Z'
        self.rejected('timestamp')

    def test_future_observation_rejected(self):
        self.obs['observed_at_utc'] = '2026-10-22T00:00:00Z'
        self.rejected('timestamp')

    def test_missing_launch_hash_rejected(self):
        self.launch.pop('sha256')
        self.rejected('Launch identity/hash')

    def test_missing_isolation_observation_rejected(self):
        self.isolation.pop('observed')
        self.rejected('isolation')

    def test_explicit_number_word_in_isolation_attestation_accepted(self):
        self.isolation['observed'] = self.isolation['observed'].replace('Exactly 1 ', 'Exactly one ')
        self.assertEqual(self.validate()['verdict'], 'observed-branch-and-combat-feedback')

    def test_wrong_isolation_nonce_rejected(self):
        self.isolation['observed'] = self.isolation['observed'].replace(self.nonce, 'DEADBEEF')
        self.rejected('isolation')

    def test_different_load_window_rejected(self):
        self.isolation['window']['id'] = 456
        self.rejected('window identity')

    def test_active_optional_steam_integration_rejected(self):
        (self.game/'steam_api64.dll').write_bytes(b'active')
        self.rejected('Steam integration active')

    def test_final_fixture_drift_rejected(self):
        (self.fixture/'BALDUR.SAV').write_bytes(b'changed')
        self.rejected('Size drift|Hash drift')

    def test_final_script_assignment_rejected_even_with_rehashed_manifest(self):
        path = self.fixture/'BALDUR.gam'
        data = bytearray(path.read_bytes()); data[0x348:0x350] = b'RDXL0002'; path.write_bytes(data)
        self.row['fixture_files'] = self.manifest()
        self.rejected('script assignment')

    def test_precursor_manifest_cannot_replace_final_fixture_manifest(self):
        self.row['fixture_files'] = self.row['construction']['input_files']
        self.rejected('inventory drift')

    def test_missing_final_manifest_size_rejected(self):
        self.row['fixture_files']['BALDUR.gam'].pop('bytes')
        self.rejected('size missing')

    def test_private_binary_script_tlk_and_engine_hash_drift_rejected(self):
        for name in ['Baldur.exe','override/RDXL0001.bcs','lang/en_US/dialog.tlk','engine.lua']:
            with self.subTest(member=name):
                path = self.game/name; before = path.read_bytes()
                try:
                    path.write_bytes(before+b'changed')
                    self.rejected('Hash drift')
                finally:
                    path.write_bytes(before)

    def test_finalize_freezes_success_without_overwriting_or_editing_sources(self):
        self.receipts()
        before = {p: digest(p) for p in [self.run/'preparation.json', self.run/'observation.json', self.image,
                                        self.fixture/'BALDUR.gam', self.game/'Baldur.exe']}
        one = capture.finalize(self.run/'preparation.json', self.run/'observation.json', output_root=self.root/'captures')
        two = capture.finalize(self.run/'preparation.json', self.run/'observation.json', output_root=self.root/'captures')
        self.assertEqual(one['verdict'],'observed-branch-and-combat-feedback')
        self.assertNotEqual(one['directory'],two['directory'])
        self.assertTrue((Path(one['directory'])/'final-fixture/BALDUR.gam').is_file())
        self.assertEqual(before,{p:digest(p) for p in before})

    def test_finalize_preserves_failed_receipt(self):
        self.obs['nonce'] = 'DEADBEEF'
        self.receipts()
        result = capture.finalize(self.run/'preparation.json', self.run/'observation.json', output_root=self.root/'captures')
        self.assertEqual(result['verdict'],'failed')
        out = Path(result['directory'])
        self.assertTrue((out/'result.json').is_file())
        self.assertTrue((out/'requested-observation.json').is_file())


if __name__ == '__main__':
    unittest.main()
