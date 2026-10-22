import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('font_provenance_test', Path(__file__).resolve().parents[1] / 'font_provenance.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class ImportedFontEvidenceTests(unittest.TestCase):
    def setUp(self):
        # Independent receipt inputs: actual importer observations and a trusted
        # private fixture manifest. No game or font asset is required by tests.
        self.expected = dict(schema='bg-redux-font-metrics/1', game=r'C:\Fixture', fonts=[
            dict(role='NORMAL', resource='NORMAL', requested_px=14, requested_style=0,
                 requested_background=1, prefer_bam=False, ttf_candidate_available=True,
                 candidate_origin='data/Patch2.bif', candidate_bytes=42196,
                 family='R PostAntiqua Roman', face_style='Roman 05554', style_flags=0,
                 actual_x_ppem=14, actual_y_ppem=14),
            dict(role='STATES', resource='STATES', requested_px=14, requested_style=0,
                 requested_background=0, prefer_bam=True, bam_candidate_available=True,
                 bam_candidate_origin='data/GUIBam.bif', bam_candidate_bytes=1000)])
        common = dict(requested_px=14, requested_style=0, synthesized_style=0,
                      resource_hash_observed=False)
        self.report = dict(schema='bg-redux-fonts/2', fonts=[
            dict(name='NORMAL', loaded=True, import_provenance=dict(common,
                 importer='TTFImporter', original_file=r'C:\Fixture\data\Patch2.bif',
                 resource_name='normal.ttf', resource_bytes=42196, requested_background=True,
                 face_metrics_available=True, family='R PostAntiqua Roman', face_style='Roman 05554',
                 face_index=0, intrinsic_style_flags=0, actual_px_x=14, actual_px_y=14)),
            dict(name='STATES', loaded=True, import_provenance=dict(common,
                 importer='BAMImporter', original_file=r'C:\Fixture\data\GUIBam.bif',
                 resource_name='states.bam', resource_bytes=1000, requested_background=False,
                 face_metrics_available=False, actual_px_x=0, actual_px_y=0))])

    def source(self, index=0):
        return self.report['fonts'][index]['import_provenance']

    def test_actual_import_metadata_does_not_inflate_hash_or_visual_proof(self):
        result = adapter.validate(self.report, self.expected)
        self.assertTrue(result['all_import_metadata_bound'])
        for key in ('resource_bytes_identity_proven', 'requested_style_fidelity_proven', 'original_ee_pixel_fidelity'):
            self.assertIs(result[key], False)

    def test_old_schema_and_role_presence_alone_cannot_pass(self):
        self.report['schema'] = 'bg-redux-fonts/1'
        with self.assertRaisesRegex(ValueError, 'schema'):
            adapter.validate(self.report, self.expected)
        self.report['schema'] = 'bg-redux-fonts/2'
        del self.report['fonts'][0]['import_provenance']
        with self.assertRaisesRegex(ValueError, 'provenance missing'):
            adapter.validate(self.report, self.expected)

    def test_missing_critical_observations_rejected_individually(self):
        baseline = copy.deepcopy(self.report)
        for key in tuple(self.source()):
            with self.subTest(field=key):
                self.report = copy.deepcopy(baseline)
                del self.source()[key]
                with self.assertRaises(ValueError):
                    adapter.validate(self.report, self.expected)

    def test_generic_font_with_same_role_and_metrics_cannot_pass(self):
        self.source()['importer'] = 'SystemFallback'
        with self.assertRaisesRegex(ValueError, 'unknown font importer'):
            adapter.validate(self.report, self.expected)

    def test_wrong_provider_and_same_basename_rejected(self):
        for path in (r'C:\OtherFixture\data\Patch2.bif', r'C:\Fixture\override\normal.ttf',
                     r'Patch2.bif', r'C:\Fixture\data\..\Other\Patch2.bif'):
            with self.subTest(path=path):
                self.source()['original_file'] = path
                with self.assertRaisesRegex(ValueError, 'source path'):
                    adapter.validate(self.report, self.expected)

    def test_different_resource_or_stream_length_rejected(self):
        self.source()['resource_name'] = 'normal.bam'
        with self.assertRaisesRegex(ValueError, 'resource name'):
            adapter.validate(self.report, self.expected)
        self.source()['resource_name'] = 'normal.ttf'
        self.source()['resource_bytes'] -= 1
        with self.assertRaisesRegex(ValueError, 'length'):
            adapter.validate(self.report, self.expected)

    def test_requested_size_is_not_actual_face_size_proof(self):
        self.source()['actual_px_x'] = 18
        with self.assertRaisesRegex(ValueError, 'face/size'):
            adapter.validate(self.report, self.expected)

    def test_other_face_or_intrinsic_style_cannot_pass_same_role(self):
        for field, value in (('family', 'Arial'), ('face_style', 'Bold'), ('face_index', 1),
                             ('intrinsic_style_flags', True)):
            with self.subTest(field=field):
                old = self.source()[field]
                self.source()[field] = value
                with self.assertRaises(ValueError):
                    adapter.validate(self.report, self.expected)
                self.source()[field] = old

    def test_bam_keeps_embedded_metrics_without_claiming_ttf_size(self):
        self.source(1)['actual_px_y'] = 14
        with self.assertRaisesRegex(ValueError, 'embedded metrics'):
            adapter.validate(self.report, self.expected)
        self.source(1)['actual_px_y'] = 0
        self.source(1)['face_metrics_available'] = True
        with self.assertRaisesRegex(ValueError, 'BAM must not claim'):
            adapter.validate(self.report, self.expected)

    def test_available_preferred_font_cannot_silently_be_bypassed(self):
        self.expected['fonts'][0]['prefer_bam'] = True
        self.expected['fonts'][0]['bam_candidate_available'] = True
        with self.assertRaisesRegex(ValueError, 'preferred candidate'):
            adapter.validate(self.report, self.expected)

    def test_duplicate_missing_and_extra_roles_rejected(self):
        baseline = copy.deepcopy(self.report)
        for rows in ([baseline['fonts'][0]], baseline['fonts'] + [baseline['fonts'][0]],
                     baseline['fonts'] + [dict(name='UNKNOWN', loaded=True)]):
            with self.subTest(rows=len(rows)):
                self.report['fonts'] = rows
                with self.assertRaises(ValueError):
                    adapter.validate(self.report, self.expected)

    def test_uncollected_resource_hash_cannot_be_claimed(self):
        self.source()['resource_hash_observed'] = True
        with self.assertRaisesRegex(ValueError, 'resource-hash claim'):
            adapter.validate(self.report, self.expected)

    def test_only_validated_receipt_bound_wrapper_links_can_map_provider(self):
        wrapper = dict(source=r'C:\Fixture', game=r'C:\Run\game',
                       asset_links={'data': r'C:\Fixture\data'}, copied_root_sha256={})
        for row in self.report['fonts']:
            row['import_provenance']['original_file'] = row['import_provenance']['original_file'].replace(r'C:\Fixture', r'C:\Run\game')
        with self.assertRaisesRegex(ValueError, 'source path'):
            adapter.validate(self.report, self.expected)
        with patch.object(adapter.private_game, 'validate', return_value={}) as guard:
            result = adapter.validate(self.report, self.expected, wrapper)
            self.assertTrue(result['private_game_mapping_validated'])
            guard.assert_called_once_with(wrapper)
            wrapper['asset_links']['data'] = r'C:\Other\data'
            with self.assertRaisesRegex(ValueError, 'receipt-bound asset link'):
                adapter.validate(self.report, self.expected, wrapper)
        with patch.object(adapter.private_game, 'validate', side_effect=ValueError('asset link changed')):
            with self.assertRaisesRegex(ValueError, 'asset link changed'):
                adapter.validate(self.report, self.expected, wrapper)


if __name__ == '__main__':
    unittest.main()
