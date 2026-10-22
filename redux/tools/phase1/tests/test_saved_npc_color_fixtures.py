import copy
from pathlib import Path
import struct
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
import zlib

sys.path.insert(0,str(Path(__file__).parents[1]))
import saved_npc_color_fixtures as c


def cre():
    data=bytearray(0x2d4+80+264)
    data[:8]=b'CRE V1.0';data[0x33]=1;data[0x272]=1
    struct.pack_into('<I',data,0x28,0x6100)
    data[0x2c:0x33]=bytes([30,91,93,12,23,93,2])
    data[0x248:0x270]=b'ORIGINAL'*5
    struct.pack_into('<I',data,0x2b8,0x2d4)
    struct.pack_into('<38HhH',data,0x2d4,*([0xffff]*38),1000,0)
    struct.pack_into('<II',data,0x2c4,0x2d4+80,1)
    data[0x2cc:0x2d4]=b'TALKTEST'
    return bytes(data)


def gam():
    data=bytearray(0xb4+2*0x160);data[:8]=b'GAMEV2.0'
    struct.pack_into('<II',data,0x20,0xb4,2)
    for i in range(2):
        source=cre();row=0xb4+i*0x160
        struct.pack_into('<II',data,row+4,len(data),len(source))
        struct.pack_into('<HH',data,row+0x20,3741,2801)
        data.extend(source)
    return bytes(data)


def area(duplicate_position=False):
    data=bytearray(0x11c+2*272);data[:8]=b'AREAV1.0'
    struct.pack_into('<IH',data,0x54,0x11c,2)
    for i in range(2):
        row=0x11c+i*272;source=cre()
        struct.pack_into('<HH',data,row+32,2573 if not i or duplicate_position else 100,2461 if not i or duplicate_position else 100)
        data[row+72:row+128]=b'ORIGINAL'*7
        struct.pack_into('<II',data,row+136,len(data),len(source));data.extend(source)
    return bytes(data)


def record(name,data):
    name=name.encode('ascii')+b'\0';packed=zlib.compress(data)
    return struct.pack('<I',len(name))+name+struct.pack('<II',len(data),len(packed))+packed


def sav(a=None): return b'SAV V1.0'+record('AR0602.ARE',a or area())+record('OTHER.WMP',b'unchanged bytes')


TABLE=b'2DA V1.0\r\n0\r\n       Leather Other Hair\r\n0      228     237   200\r\n1      23      19    3\r\n2      87      49    4\r\n'


class ColorBinaryFixtureTests(unittest.TestCase):
    def test_inert_clone_preserves_source_and_declared_regions_only(self):
        source=cre();npc=c.inert_cre(source,228)
        self.assertEqual(source,cre())
        self.assertEqual(npc[0x30],228)
        self.assertEqual(npc[0x270],128)
        self.assertEqual(npc[0x248:0x270],c.NONE*5)
        self.assertEqual(npc[0x2cc:0x2d4],c.NONE)
        self.assertEqual(npc[0x280:0x2a0].rstrip(b'\0'),b'RDXCOLOR')
        self.assertEqual(c.u32(npc,0x2c8),0)
        self.assertEqual(c.u32(npc,0x2c0),0)
        self.assertEqual(npc[0x2d4+80:],source[0x2d4+80:]) # obsolete effects preserved, unreferenced

    def test_invalid_cre_tables_palette_and_physical_slots_rejected(self):
        for offset,fmt,value in [(0x2b8,'I',2),(0x2c8,'I',10001),(0x2c4,'I',0xfffffff0),
                                  (0x28,'I',0xe200),(0x272,'B',2),(0x2d4,'H',0)]:
            raw=bytearray(cre());struct.pack_into('<'+fmt,raw,offset,value)
            with self.assertRaises(ValueError): c.inert_cre(raw,228)
        with self.assertRaises(ValueError): c.inert_cre(cre(),True)
        with self.assertRaises(ValueError): c.inert_cre(cre(),256)

    def test_party_bounds_and_overlapping_cre_rejected(self):
        source=gam();row,pc=c.party_cre(source,0)
        self.assertEqual(row,0xb4);self.assertEqual(pc,cre())
        for offset,value in [(0x24,9),(0x20,8),(0xb4+8,0xffffffff),
                              (0xb4+0x160+4,c.u32(source,0xb4+4))]:
            raw=bytearray(source);struct.pack_into('<I',raw,offset,value)
            with self.assertRaises(ValueError): c.party_cre(raw,0)

    def test_only_mephit_row_changes_and_other_compressed_members_remain_exact(self):
        source=sav();idle=c.inert_cre(cre(),46,'RDXIDLE')
        changed,guard=c.install_idle(source,idle)
        old=c.sav_records(source);new=c.sav_records(changed)
        self.assertEqual(old[1]['raw'],new[1]['raw'])
        a,b=c.inflate(old[0]),c.inflate(new[0]);row=0x11c
        self.assertEqual(b[len(a):],idle)
        c.only_changes(a,b[:len(a)],[(row,row+32),(row+72,row+128),(row+136,row+144)])
        self.assertEqual(b[row+72:row+128],c.NONE*7)
        self.assertTrue(guard['other_members_byte_identical'])
        # The diagnostic RDXCOLOR resource must be created, not planted in the input save.
        with self.assertRaisesRegex(ValueError,'absent/ambiguous'): c.inspect_npc_wire(changed)

    def test_persisted_wire_reader_distinguishes_serialized_byte_from_runtime(self):
        # Synthetic output save: a runtime-created actor has been serialized.
        a=bytearray(area());npc=c.inert_cre(cre(),237)
        struct.pack_into('<II',a,0x11c+136,len(a),len(npc));a.extend(npc)
        value=c.inspect_npc_wire(sav(a))
        self.assertEqual(value['leather_wire_byte'],237)
        self.assertIn('runtime palette is not observed',value['scope'])
        with self.assertRaisesRegex(ValueError,'placeholder may be embedded'):
            c.install_idle(sav(),npc)

    def test_ambiguous_location_or_existing_npc_rejected(self):
        with self.assertRaisesRegex(ValueError,'ambiguous'):
            c.install_idle(sav(area(True)),c.inert_cre(cre(),46,'RDXIDLE'))
        first,_=c.install_idle(sav(),c.inert_cre(cre(),46,'RDXIDLE'))
        with self.assertRaisesRegex(ValueError,'identity already present'):
            c.install_idle(first,c.inert_cre(cre(),46,'RDXIDLE'))

    def test_sav_traversal_duplicate_truncation_and_compression_bomb_rejected(self):
        for name in ['../AR0602.ARE','C:AR0602.ARE','dir/AR0602.ARE','dir\\AR0602.ARE']:
            with self.assertRaises(ValueError):c.sav_records(b'SAV V1.0'+record(name,area()))
        with self.assertRaises(ValueError): c.sav_records(sav()+record('ar0602.are',area()))
        with self.assertRaises(ValueError): c.sav_records(sav()[:-1])
        r=dict(size=4,payload=zlib.compress(b'X'*100000))
        with self.assertRaises(ValueError): c.inflate(r)
        with self.assertRaises(ValueError): c.inflate(dict(size=4,payload=zlib.compress(b'abcd')+b'trailing'))


class ColorTableTests(unittest.TestCase):
    def test_deterministic_two_columns_only_preserve_other_columns_and_selectors(self):
        changed,meta=c.controlled_table(TABLE)
        _,header,old=c.parse_table(TABLE);_,newheader,new=c.parse_table(changed)
        self.assertEqual(header,newheader);self.assertEqual(old[0],new[0])
        self.assertEqual(new[1:],[[237,46,3],[237,46,4]])
        self.assertIn(b'Hair\r\n',changed)
        self.assertEqual(meta['leather_selector'],228)
        self.assertFalse(meta['fallback_used'])
        self.assertNotEqual(meta['source_sha256'],meta['override_sha256'])

    def test_no_silent_unknown_selector_fallback_or_ragged_table(self):
        for raw in [TABLE.replace(b'237',b'236'),TABLE.replace(b'228',b'227'),
                    TABLE.replace(b'    4',b'    999'),TABLE.replace(b'49    4',b'49'),
                    TABLE.replace(b'Other',b'Leather')]:
            with self.assertRaises(ValueError): c.controlled_table(raw)

    def test_script_uses_fresh_create_then_visibility_ready_without_save_or_reload(self):
        q=SimpleNamespace(EMPTY='0 0 0 0 0 0 0 0 0 0 0 0 ""')
        q.trigger=Mock(return_value='condition\n')
        q.action=Mock(side_effect=lambda opcode,value,name:f'{opcode}:{value}:{name}\n')
        q.response=Mock(side_effect=lambda gate,actions:gate+''.join(actions))
        program=c.script(SimpleNamespace(script_query_probe=q),1,123,(3781,2801)).decode()
        self.assertIn('0 3781 2801 0 0"RDXCOLOR" "" AC',program)
        self.assertEqual(program.count('7OB\n'),1)
        self.assertEqual([call.args[0] for call in q.action.call_args_list],[30]*5)
        self.assertIn('GLOBALRDXCSTAGE',q.trigger.call_args_list[0].args)
        self.assertEqual(q.trigger.call_args_list[0].args[:2],(0x400f,0))
        self.assertEqual(q.trigger.call_args_list[-1].args,(0x401c,))
        self.assertIn('rdxcolor',q.trigger.call_args_list[-1].kwargs['obj'])


if __name__=='__main__': unittest.main()
