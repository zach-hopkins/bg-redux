"""Read-only metadata probe for this BG2EE fixture, not a general IE importer.

Inspects uncompressed BIFF resources and packaged CHU label references. It does
not reproduce GemRB's full provider precedence or execute EE Lua/menu assembly.
Only metadata/counts and short table headers are saved, never extracted assets.
"""
from pathlib import Path
import hashlib
import json
import struct
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / 'phase0-local/bg2ee-clean'
TYPES = {'bam': 0x3e8, 'chu': 0x3ea, '2da': 0x3f4, 'ttf': 0x40a, 'menu': 0x408, 'lua': 0x409}


def name(value):
    return value.split(b'\0')[0].decode('ascii').lower()


key = (GAME / 'chitin.key').read_bytes()
assert key[:8] == b'KEY V1  '
bif_count, resource_count, bif_offset, resource_offset = struct.unpack_from('<4I', key, 8)
bifs = []
for index in range(bif_count):
    _, offset, length, _ = struct.unpack_from('<IIHH', key, bif_offset + index * 12)
    bifs.append(key[offset:offset + length].rstrip(b'\0').decode('ascii').replace('\\', '/'))
resources = {}
for index in range(resource_count):
    ref, kind, locator = struct.unpack_from('<8sHI', key, resource_offset + index * 14)
    resources.setdefault((name(ref), kind), locator)


def read_resource(ref, ext):
    # Game override and English loose data only. Packaged language BIF merging
    # and engine providers are deliberately not asserted by this probe.
    for directory in [GAME / 'override', GAME / 'lang/en_US']:
        path = directory / f'{ref}.{ext}'
        if path.is_file():
            return path.read_bytes(), str(path.relative_to(GAME))
    loc = resources.get((ref, TYPES[ext]))
    if loc is None:
        return None, None
    path = GAME / bifs[loc >> 20]
    with path.open('rb') as stream:
        header = stream.read(20)
        if header[:8] != b'BIFFV1  ':
            raise ValueError(f'Unsupported compressed archive: {path.name}')
        count, _, offset = struct.unpack_from('<III', header, 8)
        stream.seek(offset)
        entries = stream.read(count * 16)
        for index in range(count):
            rloc, start, length, kind, _ = struct.unpack_from('<IIIHH', entries, index * 16)
            if (rloc & 0x3fff) == (loc & 0x3fff):
                assert kind == TYPES[ext]
                stream.seek(start)
                return stream.read(length), str(path.relative_to(GAME))
    raise ValueError('Resource locator not found')


tlk = (GAME / 'lang/en_US/dialog.tlk').read_bytes()
assert tlk[:8] == b'TLK V1  '
tlk_count, tlk_offset = struct.unpack_from('<II', tlk, 10)


def tlk_length(ref):
    if ref >= tlk_count:
        return None
    return struct.unpack_from('<I', tlk, 18 + ref * 26 + 22)[0]


def main():
    report = dict(scope=__doc__, resource_count=resource_count, tlk_entries=tlk_count,
                  fonts=[], windows=[], table_headers=[])
    for ref in ['normal', 'floattxt', 'number', 'initials', 'stonebig', 'stonesml', 'toolfont', 'tooltip', 'stonsml']:
        for ext in ['ttf', 'bam']:
            data, origin = read_resource(ref, ext)
            if data is not None:
                report['fonts'].append(dict(name=ref, type=ext, origin=origin, bytes=len(data),
                    signature_hex=data[:8].hex(), sha256=hashlib.sha256(data).hexdigest()))
    for ref in ['guiinv', 'guirec']:
        data, origin = read_resource(ref, 'chu')
        assert data[:8] == b'CHUIV1  '
        count, control_offset, window_offset = struct.unpack_from('<III', data, 8)
        for index in range(count):
            pos = window_offset + index * 28
            wid = struct.unpack_from('<H', data, pos)[0]
            controls = struct.unpack_from('<H', data, pos + 14)[0]
            first = struct.unpack_from('<H', data, pos + 24)[0]
            labels = []
            control_types = Counter()
            for control in range(first, first + controls):
                offset, length = struct.unpack_from('<II', data, control_offset + control * 8)
                cid, x, y, width, height, kind = struct.unpack_from('<IhhhhB', data, offset)
                control_types[kind] += 1
                if kind == 6:
                    strref, font = struct.unpack_from('<I8s', data, offset + 14)
                    labels.append(dict(id=hex(cid), rect=[x, y, width, height], strref=strref,
                        font=name(font), tlk_bytes=tlk_length(strref)))
            report['windows'].append(dict(resource=ref, origin=origin, window=wid,
                controls=controls, control_types=dict(control_types), labels=labels))
    for ref in ['stylbonu', 'racethac', 'clasthac', 'statdesc', 'dualclas', 'abdcscrq', 'abdcdsrq']:
        data, origin = read_resource(ref, '2da')
        first_line = data.splitlines()[0].decode('ascii', errors='replace') if data else None
        report['table_headers'].append(dict(resource=ref, origin=origin,
            first_16_bytes_hex=data[:16].hex() if data else None,
            signature_normalized=first_line.split() if first_line else None))
    output = ROOT / 'docs/compatibility/evidence/ui-resource-probe.json'
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(output)
    for window in report['windows']:
        if window['window'] == 2:
            print(window['resource'], 'labels', len(window['labels']),
                  'invalid strrefs', sum(label['tlk_bytes'] is None for label in window['labels']),
                  'empty strings', sum(label['tlk_bytes'] == 0 for label in window['labels']))
    print('fonts:', [(font['name'], font['type']) for font in report['fonts']])


if __name__ == "__main__":
    main()
