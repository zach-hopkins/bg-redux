"""Validate actual imported font metadata against a trusted private metric receipt.

Matching paths, lengths and faces binds metadata, not resource-byte identity or
visual fidelity. No filesystem probing, font loading, fallback or game mutation.
"""
import argparse
import json
import ntpath
from pathlib import Path
import importlib.util
import hashlib

_spec = importlib.util.spec_from_file_location('font_private_game', Path(__file__).with_name('private_game.py'))
private_game = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(private_game)


def normalize(path):
    if not isinstance(path, str) or '\0' in path:
        raise ValueError('Invalid NUL in filesystem identity')
    return ntpath.normcase(ntpath.normpath(path))


def import_path(value, origin):
    """KEY BIF names retain one ASCIIZ terminator in DataStream.originalfile.

    Do not truncate at an embedded NUL or normalize arbitrary invalid paths.
    The raw observation remains in the source receipt, unchanged.
    """
    if not isinstance(value, str):
        raise ValueError('Missing imported source path')
    if '\0' not in value:
        return value, False
    if (value.count('\0') == 1 and value.endswith('\0') and value[:-1].lower().endswith('.bif')
            and origin.lower().endswith('.bif')):
        return value[:-1], True
    raise ValueError('Unsupported embedded/multiple/nonarchive NUL in imported source path')


def validate(report, expected, wrapper=None):
    if report.get('schema') != 'bg-redux-fonts/2':
        raise ValueError('Unknown or missing font provenance schema')
    if expected.get('schema') != 'bg-redux-font-metrics/1' or not expected.get('game'):
        raise ValueError('Missing trusted metric fixture')
    if wrapper is not None:
        private_game.validate(wrapper)
        if normalize(wrapper['source']) != normalize(expected['game']):
            raise ValueError('Private game mapping targets a different trusted fixture')
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
        if wrapper is not None:
            parts = origin.replace('\\', '/').split('/')
            if any(part in ('', '.', '..') for part in parts) or ntpath.isabs(origin):
                raise ValueError(role + ': unsafe candidate origin')
            if len(parts) > 1:
                target = wrapper['asset_links'].get(parts[0])
                if not target or normalize(target) != normalize(ntpath.join(expected['game'], parts[0])):
                    raise ValueError(role + ': candidate is not in a receipt-bound asset link')
            elif parts[0] not in wrapper['copied_root_sha256']:
                raise ValueError(role + ': candidate is not an unchanged copied root input')
            expected_path = ntpath.join(wrapper['game'], origin)
        actual_path, terminal_nul = import_path(source.get('original_file'), origin)
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
                            key_archive_terminal_nul_observed=terminal_nul,
                            actual_resource_sha256_observed=False))
    return dict(schema='bg-redux-font-provenance-validation/1', fonts=results,
                all_import_metadata_bound=True, resource_bytes_identity_proven=False,
                private_game_mapping_validated=wrapper is not None,
                requested_style_fidelity_proven=False, original_ee_pixel_fidelity=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonts', type=Path, required=True)
    parser.add_argument('--expected', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--private-game', type=Path)
    args = parser.parse_args()
    result = validate(json.loads(args.fonts.read_text(encoding='utf-8')),
                      json.loads(args.expected.read_text(encoding='utf-8')),
                      json.loads(args.private_game.read_text(encoding='utf-8')) if args.private_game else None)
    if args.private_game:
        result['private_game_receipt'] = dict(path=str(args.private_game.resolve()),
            sha256=hashlib.sha256(args.private_game.read_bytes()).hexdigest())
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
