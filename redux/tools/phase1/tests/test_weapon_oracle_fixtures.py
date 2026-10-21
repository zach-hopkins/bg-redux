import copy
import importlib.util
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest


spec = importlib.util.spec_from_file_location('weapon_oracle_fixtures', Path(__file__).parents[1]/'weapon_oracle_fixtures.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def cre():
    value = bytearray(0x2d4)
    value[:8] = b'CRE V1.0'
    return value


class ScriptAPI:
    PLAYER2 = 'PLAYER2'
    def __init__(self):
        self.triggers = []
        self.responses = []
    def trigger(self, opcode, value=0, name='', obj=None):
        self.triggers.append((opcode, value, name, obj))
        return f'TR({opcode},{value},{name},{obj})'
    def action(self, opcode, value=0, name=''):
        return (opcode, value, name)
    def response(self, condition, actions):
        self.responses.append((condition, actions))
        return repr((condition, actions))+'\n'


class OracleFixtureTests(unittest.TestCase):
    def test_declared_groups_and_exact_selection(self):
        self.assertEqual(len(m.selected_cases('hands')), 8)
        self.assertEqual(len(m.selected_cases('ammo')), 8)
        self.assertEqual(len(m.selected_cases('damage')), 6)
        self.assertEqual(len(m.selected_cases('all')), 22)
        self.assertEqual(len(m.selected_cases('hands', ['ammo-plus-pfmw'])), 1)
        for ids in [['missing'], ['05-normal-empty', '05-normal-empty']]:
            with self.assertRaises(ValueError):
                m.selected_cases('all', ids)

    def test_rejects_undeclared_ammo_or_twohand_offhand(self):
        for update in [dict(main='bow01'), dict(ammo='arow01'), dict(main='bow01', ammo='arow01', off='sw1h01')]:
            row = m.cases()[4] | update
            with self.assertRaises(ValueError):
                m.validate_spec(row)

    def test_exact_dual_wield_slots_and_independent_refs(self):
        value = cre(); row = m.cases()[0]
        guard = m.replace_equipment(value, row)
        self.assertEqual(guard['items'], ['sw1h01', 'sw1h02'])
        self.assertEqual(guard['selected'], 0)
        slot_at = struct.unpack_from('<I', value, 0x2b8)[0]
        self.assertEqual(struct.unpack_from('<H', value, slot_at+4)[0], 1)
        self.assertEqual(struct.unpack_from('<H', value, slot_at+18)[0], 0)

    def test_shield_is_explicit_item_not_empty_hand(self):
        value = cre(); row = m.cases()[5]
        m.replace_equipment(value, row)
        self.assertEqual(m.equipment_guard(value, row)['items'], ['sw1h01', 'shld01'])
        with self.assertRaises(ValueError):
            m.equipment_guard(value, m.cases()[4])

    def test_two_identical_refs_still_use_two_distinct_item_records(self):
        value = cre(); row = m.cases()[0] | dict(off='sw1h01')
        m.replace_equipment(value, row)
        slot_at = struct.unpack_from('<I', value, 0x2b8)[0]
        self.assertEqual(struct.unpack_from('<H', value, slot_at+4)[0], 1)
        self.assertEqual(m.equipment_guard(value, row)['items'], ['sw1h01', 'sw1h01'])

    def test_ammo_slot_selection_and_charge_guard(self):
        row = m.selected_cases('ammo')[0]; value = cre()
        guard = m.replace_equipment(value, row)
        self.assertEqual(guard['selected'], -24)
        item_at = struct.unpack_from('<I', value, 0x2bc)[0]
        struct.pack_into('<H', value, item_at+20+10, 39)
        with self.assertRaisesRegex(ValueError, 'charges'):
            m.equipment_guard(value, row)

    def test_missing_and_changed_equipment_rejected(self):
        row = m.cases()[0]; original = cre(); m.replace_equipment(original, row)
        slot_at = struct.unpack_from('<I', original, 0x2b8)[0]
        item_at = struct.unpack_from('<I', original, 0x2bc)[0]
        for at, data in [(slot_at+4, b'\xff\xff'), (slot_at+76, b'\x01\x00'),
                         (slot_at+78, b'\x01\x00'), (item_at, b'XXXXXX')]:
            value = original.copy(); value[at:at+len(data)] = data
            with self.assertRaises(ValueError):
                m.equipment_guard(value, row)

    def test_rejects_bad_offsets_and_duplicate_baseline_inventory(self):
        value = cre(); struct.pack_into('<I', value, 0x2c0, 1)
        with self.assertRaises(ValueError):
            m.replace_equipment(value, m.cases()[0])
        value = cre(); m.replace_equipment(value, m.cases()[0])
        struct.pack_into('<I', value, 0x2b8, 0xffffffff)
        with self.assertRaises(ValueError):
            m.equipment_guard(value, m.cases()[0])

    def test_program_queries_both_predicates_for_each_exact_hand(self):
        api = ScriptAPI(); raw = m.program(api, 2, 12345)
        queries = [(op, hand, obj) for op, hand, _, obj in api.triggers if op in (0x40ec, 0x40f2)]
        self.assertEqual(queries, [(op, hand, 'PLAYER2') for hand in (1, 2, 3) for op in (0x40ec, 0x40f2)])
        self.assertEqual(len(api.responses), 13)
        for stage, key in enumerate(m.QUERY_KEYS):
            for truth in (True, False):
                condition, actions = api.responses[stage*2+int(not truth)]
                self.assertEqual(actions, [(30, int(truth), 'GLOBAL'+key),
                    (30, 2, 'GLOBALRDXCASE'), (30, 12345, 'GLOBALRDXNONCE'),
                    (30, stage+1, 'GLOBALRDXSTAGE')])
                self.assertIn(f'TR(16399,{stage},GLOBALRDXSTAGE,None)', condition)
        self.assertEqual(api.responses[-1][1], [(30, 1, 'GLOBALRDXDONE'), (30, 7, 'GLOBALRDXSTAGE'), (190, 0, '')])
        self.assertTrue(raw.startswith(b'SC\n') and raw.endswith(b'SC\n'))

    def test_invalid_script_identity_rejected(self):
        for number, nonce in [(0, 1), (10000, 1), (1, 0), (1, 0x80000000)]:
            with self.assertRaises(ValueError):
                m.program(ScriptAPI(), number, nonce)

    def test_six_false_results_are_explicit_valid_evidence(self):
        values = dict.fromkeys(m.QUERY_KEYS, 0) | dict(RDXCASE=3, RDXNONCE=123, RDXDONE=1, RDXSTAGE=7)
        self.assertEqual(m.output_values(values, 3, 123), dict.fromkeys(m.QUERY_KEYS, 0))

    def test_stale_missing_incomplete_or_nonboolean_output_rejected(self):
        valid = dict.fromkeys(m.QUERY_KEYS, 1) | dict(RDXCASE=3, RDXNONCE=123, RDXDONE=1, RDXSTAGE=7)
        mutations = [dict(RDXCASE=2), dict(RDXNONCE=122), dict(RDXDONE=0), dict(RDXSTAGE=6),
                     dict(RDXE1=2), dict(RDXD2=True), dict(RDXNONCE=True)]
        for change in mutations:
            with self.assertRaises(ValueError):
                m.output_values(valid | change, 3, 123)
        for key in valid:
            changed = copy.copy(valid); del changed[key]
            with self.assertRaises(ValueError):
                m.output_values(changed, 3, 123)

    def test_manifest_paths_are_bounded(self):
        for path in ['../escape', 'C:/escape', '/escape', 'C:relative', '']:
            with self.assertRaises(ValueError):
                m.safe_relative(path)
        self.assertEqual(m.safe_relative('lang/en_US/dialog.tlk').parts, ('lang', 'en_US', 'dialog.tlk'))

    def test_output_ingestion_checks_script_identity_equipment_defense_and_globals(self):
        row = dict(spec=m.cases()[0], script='P1AB0001', number=1, nonce=123)
        pc = cre(); m.replace_equipment(pc, row['spec'])
        pc[0x248:0x250] = b'p1ab0001'  # resrefs are case-insensitive
        globals_ = dict.fromkeys(m.QUERY_KEYS, 0) | dict(RDXCASE=1, RDXNONCE=123, RDXDONE=1, RDXSTAGE=7)
        defenses = [dict(opcode=120, p1=0xffffffff, p2=1, timing=9)]
        api = SimpleNamespace(equipped_defenses=SimpleNamespace(
            embedded=lambda data, index: (0, pc),
            observe=lambda path: [{}, dict(defense_effects=defenses)]),
            legacy_oracle=SimpleNamespace(read_wire=lambda path: dict(globals=globals_)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'output.gam'; path.write_bytes(b'isolated mock wire payload')
            self.assertEqual(m.inspect_output(api, path, row)['values'], dict.fromkeys(m.QUERY_KEYS, 0))
            globals_['RDXNONCE'] = 122
            with self.assertRaisesRegex(ValueError, 'Stale'):
                m.inspect_output(api, path, row)
            globals_['RDXNONCE'] = 123
            defenses[0]['p2'] = 2
            with self.assertRaisesRegex(ValueError, 'defense'):
                m.inspect_output(api, path, row)
            defenses[0]['p2'] = 1
            slot_at = struct.unpack_from('<I', pc, 0x2b8)[0]
            struct.pack_into('<H', pc, slot_at+4, 0xffff)
            with self.assertRaisesRegex(ValueError, 'Physical'):
                m.inspect_output(api, path, row)
            struct.pack_into('<H', pc, slot_at+4, 1)
            pc[0x248:0x250] = b'P1AB0002'
            with self.assertRaisesRegex(ValueError, 'script identity'):
                m.inspect_output(api, path, row)


if __name__ == '__main__':
    unittest.main()
