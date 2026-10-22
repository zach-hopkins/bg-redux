"""Read-only Windows FreeType metric evidence for private BG2EE font candidates.

Exports names, hashes and numeric metrics only, never font data or glyph images.
The narrow KEY/BIFF reader is not GemRB provider selection or an EE renderer.
"""
import argparse
import ctypes as C
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import struct


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compare_runtime(candidate, runtime):
    """Compare actual numeric fingerprint, without promoting it to provenance."""
    differences = []
    for observed, predicted in (('baseline', 'predicted_current_baseline'),
                                ('line_height', 'predicted_current_lineheight')):
        if runtime.get(observed) != candidate[predicted]:
            differences.append(observed)
    if runtime.get('sample_width') != candidate['sample_pen_advances'][0]['predicted_current_pen_advance_px']:
        differences.append('sample_width')
    glyphs = {r['char']: r for r in candidate['glyphs']}
    for observed in runtime.get('glyphs', []):
        expected = glyphs.get(observed['char'])
        if expected is None or expected['missing']:
            differences.append('glyph:' + observed['char'])
        elif (observed['size'] != [expected['bitmap_width'], expected['bitmap_rows']]
              or observed['position'] != expected['current_pipeline_position']):
            differences.append('glyph:' + observed['char'])
    if not runtime.get('glyphs'):
        differences.append('missing_glyph_observations')
    return dict(metric_fingerprint_matches=not differences, differences=differences,
                actual_provider_proven=False)


class Assets:
    def __init__(self, game):
        self.game = Path(game)
        self.key = (self.game / 'chitin.key').read_bytes()
        if self.key[:8] != b'KEY V1  ':
            raise ValueError('Not an uncompressed KEY V1 fixture')
        count, resources, offset, res_offset = struct.unpack_from('<4I', self.key, 8)
        self.bifs = []
        for i in range(count):
            _, start, length, _ = struct.unpack_from('<IIHH', self.key, offset + i * 12)
            self.bifs.append(self.key[start:start + length].rstrip(b'\0').decode('ascii').replace('\\', '/'))
        self.resources = {}
        for i in range(resources):
            ref, kind, locator = struct.unpack_from('<8sHI', self.key, res_offset + i * 14)
            self.resources.setdefault((ref.rstrip(b'\0').decode('ascii').lower(), kind), locator)

    def read_resource(self, ref, extension, resource_type):
        for directory in ('override', 'lang/en_US'):
            path = self.game / directory / (ref.lower() + '.' + extension)
            if path.is_file():
                return path.read_bytes(), str(path.relative_to(self.game))
        loc = self.resources.get((ref.lower(), resource_type))
        if loc is None:
            return None, None
        path = self.game / self.bifs[loc >> 20]
        with path.open('rb') as f:
            header = f.read(20)
            if header[:8] != b'BIFFV1  ':
                raise ValueError('Compressed BIFF is outside this probe')
            count, _, offset = struct.unpack_from('<III', header, 8)
            f.seek(offset)
            entries = f.read(count * 16)
            for i in range(count):
                rloc, start, length, kind, _ = struct.unpack_from('<IIIHH', entries, i * 16)
                if rloc & 0x3fff == loc & 0x3fff:
                    if kind != resource_type:
                        raise ValueError('Font locator type mismatch')
                    f.seek(start)
                    data = f.read(length)
                    if len(data) != length:
                        raise ValueError('Truncated font resource')
                    return data, str(path.relative_to(self.game))
        raise ValueError('Unresolved font locator')

    def read_ttf(self, ref):
        return self.read_resource(ref, 'ttf', 0x40a)


class Generic(C.Structure):
    _fields_ = [('data', C.c_void_p), ('finalizer', C.c_void_p)]


class Vector(C.Structure):
    _fields_ = [('x', C.c_long), ('y', C.c_long)]


class Bitmap(C.Structure):
    _fields_ = [('rows', C.c_uint), ('width', C.c_uint), ('pitch', C.c_int),
                ('buffer', C.c_void_p), ('num_grays', C.c_ushort),
                ('pixel_mode', C.c_ubyte), ('palette_mode', C.c_ubyte), ('palette', C.c_void_p)]


class Slot(C.Structure):
    _fields_ = [('library', C.c_void_p), ('face', C.c_void_p), ('next', C.c_void_p),
                ('glyph_index', C.c_uint), ('generic', Generic), ('metrics', C.c_long * 8),
                ('linear_hori', C.c_long), ('linear_vert', C.c_long), ('advance', Vector),
                ('format', C.c_uint), ('bitmap', Bitmap), ('left', C.c_int), ('top', C.c_int)]


class SizeMetrics(C.Structure):
    _fields_ = [('x_ppem', C.c_ushort), ('y_ppem', C.c_ushort)] + [
        (n, C.c_long) for n in ('x_scale', 'y_scale', 'ascender', 'descender', 'height', 'max_advance')]


class FontSize(C.Structure):
    _fields_ = [('face', C.c_void_p), ('generic', Generic), ('metrics', SizeMetrics)]


class Face(C.Structure):
    _fields_ = [(n, C.c_long) for n in ('num_faces', 'face_index', 'face_flags', 'style_flags', 'num_glyphs')] + [
        ('family', C.c_char_p), ('style', C.c_char_p), ('num_fixed_sizes', C.c_int),
        ('available_sizes', C.c_void_p), ('num_charmaps', C.c_int), ('charmaps', C.c_void_p),
        ('generic', Generic), ('bbox', C.c_long * 4), ('units_per_em', C.c_ushort),
    ] + [(n, C.c_short) for n in ('ascender', 'descender', 'height', 'max_advance_width',
                                 'max_advance_height', 'underline_position', 'underline_thickness')] + [
        ('glyph', C.POINTER(Slot)), ('size', C.POINTER(FontSize)), ('charmap', C.c_void_p)]


class FreeType:
    def __init__(self, dll):
        if os.name != 'nt' or C.sizeof(C.c_long) != 4:
            raise RuntimeError('This evidence adapter requires the Windows FreeType ABI')
        self.dll_directory = os.add_dll_directory(str(Path(dll).resolve().parent))
        self.ft = C.CDLL(str(Path(dll).resolve()))
        signatures = {
            'FT_Init_FreeType': ([C.POINTER(C.c_void_p)], C.c_int),
            'FT_Done_FreeType': ([C.c_void_p], C.c_int),
            'FT_New_Memory_Face': ([C.c_void_p, C.c_void_p, C.c_long, C.c_long, C.POINTER(C.POINTER(Face))], C.c_int),
            'FT_Done_Face': ([C.POINTER(Face)], C.c_int),
            'FT_Set_Pixel_Sizes': ([C.POINTER(Face), C.c_uint, C.c_uint], C.c_int),
            'FT_Select_Charmap': ([C.POINTER(Face), C.c_uint], C.c_int),
            'FT_Get_Char_Index': ([C.POINTER(Face), C.c_ulong], C.c_uint),
            'FT_Load_Glyph': ([C.POINTER(Face), C.c_uint, C.c_int32], C.c_int),
            'FT_Render_Glyph': ([C.POINTER(Slot), C.c_int], C.c_int),
            'FT_Get_Advance': ([C.POINTER(Face), C.c_uint, C.c_int32, C.POINTER(C.c_long)], C.c_int),
            'FT_Get_Kerning': ([C.POINTER(Face), C.c_uint, C.c_uint, C.c_uint, C.POINTER(Vector)], C.c_int),
            'FT_MulFix': ([C.c_long, C.c_long], C.c_long),
            'FT_Library_Version': ([C.c_void_p, C.POINTER(C.c_int), C.POINTER(C.c_int), C.POINTER(C.c_int)], None),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.ft, name)
            fn.argtypes, fn.restype = args, result
        self.library = C.c_void_p()
        self.check(self.ft.FT_Init_FreeType(C.byref(self.library)))

    @staticmethod
    def check(error):
        if error:
            raise RuntimeError(f'FreeType error {error}')

    def measure(self, data, px, text):
        buffer = C.create_string_buffer(data)
        face = C.POINTER(Face)()
        self.check(self.ft.FT_New_Memory_Face(self.library, buffer, len(data), 0, C.byref(face)))
        try:
            self.check(self.ft.FT_Select_Charmap(face, int.from_bytes(b'unic', 'big')))
            self.check(self.ft.FT_Set_Pixel_Sizes(face, 0, px))
            rec = face.contents
            scale = rec.size.contents.metrics.y_scale
            baseline = (self.ft.FT_MulFix(rec.ascender, scale) + 63) // 64
            descent = (self.ft.FT_MulFix(rec.descender, scale) + 63) // 64
            lineheight = baseline - descent
            rows = []
            for char in dict.fromkeys(text + 'Strength Armor Class 123AV To'):
                index = self.ft.FT_Get_Char_Index(face, ord(char))
                row = dict(char=char, codepoint=ord(char), glyph_index=index, missing=index == 0)
                if index:
                    advance = C.c_long()
                    self.check(self.ft.FT_Get_Advance(face, index, 2 << 16, C.byref(advance)))
                    self.check(self.ft.FT_Load_Glyph(face, index, 2 << 16))
                    self.check(self.ft.FT_Render_Glyph(rec.glyph, 0))
                    glyph = rec.glyph.contents
                    if glyph.advance.x * 1024 != advance.value:
                        raise ValueError('Independent advance APIs disagree')
                    row.update(advance_26_6=glyph.advance.x, advance_16_16=advance.value,
                               bitmap_width=glyph.bitmap.width, bitmap_rows=glyph.bitmap.rows,
                               bitmap_left=glyph.left, bitmap_top=glyph.top,
                               current_pipeline_position=[0, baseline - glyph.top],
                               advance_minus_bitmap_px=advance.value / 65536 - glyph.bitmap.width)
                rows.append(row)
            bychar = {r['char']: r for r in rows}
            pairs = []
            for left, right in ('AV', 'To', 'Wa', ' g'):
                kern = Vector()
                self.check(self.ft.FT_Get_Kerning(face, bychar[left]['glyph_index'], bychar[right]['glyph_index'], 0, C.byref(kern)))
                pairs.append(dict(pair=left + right, kerning_26_6=kern.x,
                                  current_get_kerning_offset_px=int(-kern.x / 64)))
            samples = []
            for sample in ('Strength Armor Class 123', 'AV To Wa', 'A A', 'gggg', 'WWW'):
                ft_width, current_width, prev = 0, 0, None
                for char in sample:
                    row = bychar[char]
                    if prev is not None:
                        kern = Vector()
                        self.check(self.ft.FT_Get_Kerning(face, bychar[prev]['glyph_index'], row['glyph_index'], 0, C.byref(kern)))
                        ft_width += kern.x / 64
                        current_width += int(kern.x / 64)
                    ft_width += row.get('advance_26_6', 0) / 64
                    current_width += int(lineheight * .25) if char == ' ' or row['missing'] else row['bitmap_width']
                    prev = char
                samples.append(dict(text=sample, hinted_pen_advance_px=ft_width,
                                    predicted_current_pen_advance_px=current_width))
            return dict(family=rec.family.decode('utf-8', 'replace'),
                        face_style=rec.style.decode('utf-8', 'replace'), style_flags=rec.style_flags,
                        units_per_em=rec.units_per_em, face_ascender=rec.ascender,
                        face_descender=rec.descender, face_height=rec.height,
                        actual_x_ppem=rec.size.contents.metrics.x_ppem,
                        actual_y_ppem=rec.size.contents.metrics.y_ppem,
                        predicted_current_baseline=baseline, predicted_current_lineheight=lineheight,
                        predicted_current_space=int(lineheight * .25), glyphs=rows,
                        kerning=pairs, sample_pen_advances=samples)
        finally:
            self.ft.FT_Done_Face(face)

    def close(self):
        self.ft.FT_Done_FreeType(self.library)
        self.dll_directory.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--fonts-table', type=Path, required=True)
    parser.add_argument('--freetype', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runtime-fonts', type=Path)
    parser.add_argument('--provenance-only', action='store_true', help='Keep compact identity/face metrics, omit glyph/pair/sample rows')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Evidence output must be new')
    assets, ft = Assets(args.game), FreeType(args.freetype)
    runtime = json.loads(args.runtime_fonts.read_text()) if args.runtime_fonts else None
    rows = []
    try:
        for line in args.fonts_table.read_text().splitlines()[3:]:
            cols = line.split()
            if len(cols) != 7 or cols[0].startswith('#'):
                continue
            _, ref, role, px, style, background, flags = cols
            row = dict(role=role, resource=ref, requested_px=int(px), requested_style=int(style),
                       requested_background=int(background), prefer_bam=bool(int(flags) & 1))
            data, origin = assets.read_ttf(ref)
            row['ttf_candidate_available'] = data is not None
            bam_data, bam_origin = assets.read_resource(ref, 'bam', 0x3e8)
            row['bam_candidate_available'] = bam_data is not None
            if bam_data is not None:
                row.update(bam_candidate_origin=bam_origin, bam_candidate_sha256=sha(bam_data),
                           bam_candidate_bytes=len(bam_data))
            if data is not None:
                row.update(candidate_origin=origin, candidate_sha256=sha(data), candidate_bytes=len(data))
                row.update(ft.measure(data, int(px), 'Aa0gW jAV—½'))
                if runtime:
                    observed = next((r for r in runtime['fonts'] if r['name'] == role), None)
                    if observed and 'TTF' in observed.get('runtime_type', ''):
                        row['historical_runtime_comparison'] = compare_runtime(row, observed)
            rows.append(row)
        if args.provenance_only:
            for row in rows:
                for field in ('glyphs', 'kerning', 'sample_pen_advances'):
                    row.pop(field, None)
        versions = [C.c_int() for _ in range(3)]
        ft.ft.FT_Library_Version(ft.library, *(C.byref(v) for v in versions))
        report = dict(schema='bg-redux-font-metrics/1', created_utc=datetime.now(timezone.utc).isoformat(),
                      scope=__doc__, game=str(args.game.resolve()), key_sha256=sha(assets.key),
                      fonts_table=str(args.fonts_table.resolve()), fonts_table_sha256=sha(args.fonts_table.read_bytes()),
                      freetype=str(args.freetype.resolve()), freetype_sha256=sha(args.freetype.read_bytes()),
                      freetype_version=[v.value for v in versions], load_flags='FT_LOAD_DEFAULT | FT_LOAD_TARGET_MONO',
                      render_mode='FT_RENDER_MODE_NORMAL', actual_engine_provider_observed=False,
                      original_ee_pixels_compared=False, fonts=rows)
        if runtime:
            report['historical_runtime'] = dict(path=str(args.runtime_fonts.resolve()),
                                                sha256=sha(args.runtime_fonts.read_bytes()))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as output:
            json.dump(report, output, indent=2, ensure_ascii=False)
            output.write('\n')
        print(args.output)
    finally:
        ft.close()


if __name__ == '__main__':
    main()
