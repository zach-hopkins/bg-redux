"""Private TLK/stock-tail instrumentation must preserve source evidence.

Imports the coordinator's external module; never prepares or launches a game.
"""
from pathlib import Path
import hashlib
import re
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import original_live as live


def tlk(payloads, *, language=3):
    text = bytearray()
    records = bytearray()
    for number, payload in enumerate(payloads):
        records.extend(struct.pack('<H8sIIII', 3, f'SND{number}'.encode().ljust(8, b'\0'),
                                   number + 1, number + 9, len(text), len(payload)))
        text.extend(payload)
    return b'TLK V1  ' + struct.pack('<HII', language, len(payloads), 18 + 26*len(payloads)) + records + text


def entries(data):
    count, offset = struct.unpack_from('<II', data, 10)
    result = []
    for number in range(count):
        record = data[18 + number*26:18 + (number+1)*26]
        start, length = struct.unpack_from('<II', record, 18)
        result.append((record, data[offset+start:offset+start+length]))
    return result


class TLKAppend(unittest.TestCase):
    def test_existing_records_sound_fields_and_text_preserved(self):
        original = tlk([b'Old text', b'\xff\x80 non-ASCII bytes', b'A\0B', b''])
        added = ['RDX A1B2C3D4 ai-imoen-stock B118 ENTER', 'RDX A1B2C3D4 ai-imoen-stock B118 RETURN']
        output, refs = live.append_tlk(original, added)
        self.assertEqual(refs, [4, 5])
        self.assertEqual(output[:10], original[:10])
        self.assertEqual(entries(output)[:4], entries(original))
        self.assertEqual([text for _, text in entries(output)[4:]], [s.encode('ascii') for s in added])
        count, offset = struct.unpack_from('<II', output, 10)
        self.assertEqual((count, offset), (6, 18 + 6*26))
        for record, _ in entries(output)[4:]:
            flags, sound, volume, pitch, _, _ = struct.unpack('<H8sIIII', record)
            self.assertEqual((flags, sound, volume, pitch), (1, b'\0'*8, 0, 0))

    def test_empty_append_is_byte_identical(self):
        original = tlk([b'Old text'])
        output, refs = live.append_tlk(original, [])
        self.assertEqual((output, refs), (original, []))

    def test_empty_table_appends_reference_zero(self):
        output, refs = live.append_tlk(tlk([]), ['RDX ABCDEF01 SEEN'])
        self.assertEqual(refs, [0])
        self.assertEqual(entries(output)[0][1], b'RDX ABCDEF01 SEEN')

    def test_mutable_input_is_not_changed(self):
        original = bytearray(tlk([b'untouched']))
        before = bytes(original)
        live.append_tlk(original, ['new'])
        self.assertEqual(bytes(original), before)

    def test_bad_signature_rejected(self):
        original = bytearray(tlk([b'text']))
        original[:8] = b'INVALID!'
        with self.assertRaises(ValueError):
            live.append_tlk(bytes(original), ['new'])

    def test_truncated_header_rejected(self):
        with self.assertRaises((ValueError, struct.error)):
            live.append_tlk(b'TLK V1  ', ['new'])

    def test_truncated_record_table_rejected(self):
        with self.assertRaises(ValueError):
            live.append_tlk(tlk([b'text'])[:30], ['new'])

    def test_noncanonical_table_offset_rejected(self):
        original = bytearray(tlk([b'text']))
        struct.pack_into('<I', original, 14, 45)
        with self.assertRaises(ValueError):
            live.append_tlk(bytes(original), ['new'])

    def test_truncated_existing_text_rejected(self):
        with self.assertRaises(ValueError):
            live.append_tlk(tlk([b'original text'])[:-1], ['new'])

    def test_existing_text_start_out_of_bounds_rejected(self):
        original = bytearray(tlk([b'text']))
        struct.pack_into('<I', original, 18+18, 99)
        with self.assertRaises(ValueError):
            live.append_tlk(bytes(original), ['new'])

    def test_existing_text_length_out_of_bounds_rejected(self):
        original = bytearray(tlk([b'text']))
        struct.pack_into('<I', original, 18+22, 0xffffffff)
        with self.assertRaises(ValueError):
            live.append_tlk(bytes(original), ['new'])

    def test_new_nonascii_strings_are_explicitly_rejected(self):
        with self.assertRaises(UnicodeError):
            live.append_tlk(tlk([b'text']), ['non-ASCII \u00e9'])


class StockTailInstrumentation(unittest.TestCase):
    @staticmethod
    def references(spec):
        result = {'seen': 900000}
        for number in range(spec['first'], spec['first']+4):
            result[str(number)] = {'enter': 900001 + 2*(number-spec['first']),
                                   'return': 900002 + 2*(number-spec['first'])}
        return result

    def test_all_four_tails_retain_stock_attack_payloads_and_conditions(self):
        for spec in live.CASES:
            with self.subTest(case=spec['id']):
                output, receipt = live.live_program(spec, self.references(spec))
                source, _ = live.read_resource(spec['source'], 'bcs')
                original_blocks = list(live.BLOCK.finditer(source.decode('ascii').replace('\r\n', '\n')))
                blocks = list(live.BLOCK.finditer(output.decode('ascii')))
                self.assertEqual(len(blocks), 9)  # seen + four stock branches + four return heartbeats
                self.assertEqual(receipt['source_sha256'], hashlib.sha256(source).hexdigest())
                self.assertEqual(receipt['removed_query_records'], 6 if spec['remove_queries'] else 0)
                for local_index, number in enumerate(range(spec['first'], spec['first']+4)):
                    original_condition, original_response = original_blocks[number].groups()
                    condition, response = blocks[local_index+1].groups()
                    if spec['remove_queries']:
                        expected_condition = live.TRIGGER.sub(
                            lambda m: '' if int(m[1]) in (0x40ec, 0x40f2) else m[0], original_condition)
                    else:
                        expected_condition = original_condition
                    self.assertEqual(condition, live.trigger(0x400f, 0, 'GLOBALRDXAIDONE') + expected_condition)
                    chunks = re.findall(r'(?ms)^\d+OB\n.*? AC\n', original_response)
                    self.assertTrue(chunks, 'Original action payload must be observed')
                    for chunk in chunks:
                        self.assertIn(chunk, response, 'Stock action bytes must remain unchanged')
                    self.assertEqual(receipt['original_responses'][local_index]['response_sha256'],
                                     hashlib.sha256(original_response.encode()).hexdigest())
                    action_ids = re.findall(r'(?m)^(\d+)OB$', response)
                    self.assertEqual(action_ids.count('105'), 1)
                    self.assertEqual(action_ids.count('262'), 2)
                    first_display = response.find('262OB\n')
                    attack = response.find('105OB\n')
                    last_display = response.rfind('262OB\n')
                    self.assertLess(first_display, attack)
                    self.assertLess(attack, last_display)
                    self.assertIn('GLOBALRDXAFTER', response[attack:])
                self.assertIn('not exact native action/target identity or DPR', receipt['limits'])


if __name__ == '__main__':
    unittest.main()
