"""Validate actual imported font metadata against a trusted private metric receipt.

Matching paths, lengths and faces binds metadata, not resource-byte identity or
visual fidelity. No filesystem probing, font loading, fallback or game mutation.
"""
import argparse
import json
import ntpath
from pathlib import Path


def normalize(path):
    return ntpath.normcase(ntpath.normpath(path))


def validate(report, expected):
    if report.get('schema') != 'bg-redux-fonts/2':
        raise ValueError('Unknown or missing font provenance schema')
    if expected.get('schema') != 'bg-redux-font-metrics/1' or not expected.get('game'):
        raise ValueError('Missing trusted metric fixture')
    actual, candidates = {}, {}
    for row in report.get('fonts', []):
        role = row.get('name')
        if not role or role in actual:
            raise ValueError('Missing or duplicated observed font role')
        actual[role] = row
    for row in expected.get('fonts', []):
        role = row.get('role')
        if not role or role in candidates:
            raise ValueError('Missing or duplicated expected font role')
        candidates[role] = row
    if not candidates or set(actual) != set(candidates):
        raise ValueError('Font role inventory differs from trusted table')
    results = []
    for role, wanted in candidates.items():
        observed = actual[role]
        source = observed.get('import_provenance')
        if observed.get('loaded') is not True or not isinstance(source, dict):
            raise ValueError(role + ': font/import provenance missing')
        importer = source.get('importer')
        if importer not in ('TTFImporter', 'BAMImporter'):
            raise ValueError(role + ': unknown font importer')
        ttf = importer == 'TTFImporter'
        if type(wanted.get('prefer_bam')) is not bool:
            raise ValueError(role + ': missing trusted importer preference')
        preferred = 'bam_candidate_available' if wanted['prefer_bam'] else 'ttf_candidate_available'
        if wanted.get(preferred) is True and ttf == wanted['prefer_bam']:
            raise ValueError(role + ': selected importer bypassed the available preferred candidate')
        prefix = '' if ttf else 'bam_'
        available = 'ttf_candidate_available' if ttf else 'bam_candidate_available'
        if wanted.get(available) is not True:
            raise ValueError(role + ': no trusted candidate for selected importer')
        origin = wanted.get(prefix + 'candidate_origin')
        length = wanted.get(prefix + 'candidate_bytes')
        if not origin or type(length) is not int or length <= 0:
            raise ValueError(role + ': incomplete candidate origin/length')
        expected_path = ntpath.join(expected['game'], origin)
        actual_path = source.get('original_file')
        if (not isinstance(actual_path, str) or not ntpath.isabs(actual_path)
                or normalize(actual_path) != normalize(expected_path)):
            raise ValueError(role + ': imported source path differs or is unknown')
        filename = wanted['resource'].lower() + ('.ttf' if ttf else '.bam')
        resource_name = source.get('resource_name')
        if not isinstance(resource_name, str) or resource_name.lower() != filename:
            raise ValueError(role + ': resource name differs or is unknown')
        if type(source.get('resource_bytes')) is not int or source['resource_bytes'] != length:
            raise ValueError(role + ': imported resource length differs or is missing')
        for key in ('requested_px', 'requested_style'):
            if type(source.get(key)) is not int or source[key] != wanted[key]:
                raise ValueError(role + ': loaded request differs from expected table')
        if source.get('requested_background') is not bool(wanted['requested_background']):
            raise ValueError(role + ': requested background missing/different')
        if type(source.get('synthesized_style')) is not int or source['synthesized_style'] != 0:
            raise ValueError(role + ': unknown synthesized style policy')
        if source.get('resource_hash_observed') is not False:
            raise ValueError(role + ': unsupported resource-hash claim')
        if ttf:
            if source.get('face_metrics_available') is not True:
                raise ValueError(role + ': actual FT face metrics unavailable')
            for actual_key, expected_key in (('family', 'family'), ('face_style', 'face_style'),
                                             ('intrinsic_style_flags', 'style_flags'),
                                             ('actual_px_x', 'actual_x_ppem'),
                                             ('actual_px_y', 'actual_y_ppem')):
                if (expected_key not in wanted or source.get(actual_key) != wanted[expected_key]
                        or type(source.get(actual_key)) is not type(wanted[expected_key])):
                    raise ValueError(role + ': actual face/size differs or is unknown')
            if (type(source.get('face_index')) is not int or source['face_index'] != 0
                    or type(source.get('actual_px_x')) is not int or source['actual_px_x'] <= 0):
                raise ValueError(role + ': incomplete actual face index/size')
        else:
            if source.get('face_metrics_available') is not False:
                raise ValueError(role + ': BAM must not claim FT face metrics')
            for key in ('actual_px_x', 'actual_px_y'):
                if type(source.get(key)) is not int or source[key] != 0:
                    raise ValueError(role + ': BAM must retain embedded metrics')
        results.append(dict(role=role, importer=importer, imported_metadata_bound=True,
                            actual_resource_sha256_observed=False))
    return dict(schema='bg-redux-font-provenance-validation/1', fonts=results,
                all_import_metadata_bound=True, resource_bytes_identity_proven=False,
                requested_style_fidelity_proven=False, original_ee_pixel_fidelity=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonts', type=Path, required=True)
    parser.add_argument('--expected', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = validate(json.loads(args.fonts.read_text(encoding='utf-8')),
                      json.loads(args.expected.read_text(encoding='utf-8')))
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
