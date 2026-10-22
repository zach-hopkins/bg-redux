"""Raw acceptance rejects incomplete pages and self-consistent wrong numbers."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('stats_validation_test', Path(__file__).resolve().parents[1] / 'stats_validation.py')
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)
NONCE = '0123456789abcdef0123456789abcdef'


class StatsValidationTests(unittest.TestCase):
    def write(self, name, data):
        (self.path / name).write_text(json.dumps(data), encoding='utf8')

    def read(self, name):
        return json.loads((self.path / name).read_text(encoding='utf8'))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.tlk = self.path / 'dialog.tlk'
        refs = {17379, 32204} | {r for rows in validation.NUMERIC_ROWS.values() for r, _ in rows}
        count = max(refs) + 1
        table = bytearray(18 + 26*count)
        table[:8] = b'TLK V1  '
        struct.pack_into('<II', table, 10, count, len(table))
        strings = bytearray()
        for ref in sorted(refs):
            text = ('label%d' % ref).encode()
            struct.pack_into('<II', table, 18 + 26*ref + 18, len(strings), len(text))
            strings.extend(text)
        self.tlk.write_bytes(table + strings)
        self.party = []
        for pc in range(1, 5):
            stats = [0]*256
            stats[0], stats[232], stats[34] = 20, pc, 7
            self.party.append(dict(name='Actor%d' % pc, base_stats=list(stats), modified_stats=list(stats)))
        self.world = dict(selection=1, gold=100, party=self.party)
        self.checks, self.callbacks, self.captures = [], [], 0
        self.actions = []
        (self.path / 'process.log').write_text('normal native output\n')
        self.add('stats.prepare')
        self.add('stats.record.open')
        for pc in range(1, 5):
            self.add('stats.actor-%d.portrait' % pc, callback=('PORTWIN', 0, pc-1))
            self.checks.append(dict(name='stats.actor-selected', passed=True, actor=pc,
                actor_class=pc, levels=[7,0,0], states=[]))
            self.checks[-1]['actor_name'] = 'Actor%d' % pc
            self.add('stats.actor-%d.selected' % pc, capture=(pc, 'Overview', 0, 1))
            for section in range(6):
                prefix = 'stats.actor-%d.section-%d' % (pc, section)
                self.add(prefix + '.select', callback=('GUIREC', 2, 0x7fff0210+section))
                if section in validation.NUMERIC_ROWS:
                    lines = ['label%d' % (17379 if section == 2 else 32204)]
                    lines += ['label%d: 0%s' % (ref, '%' if section == 3 else '')
                              for ref, _ in validation.NUMERIC_ROWS[section]]
                    pages = ['\n'.join(lines[:11]), '\n'.join(lines[11:])] if section == 3 else ['\n'.join(lines)]
                else:
                    pages = ['Actor%d section%d' % (pc, section)]
                self.checks.append(dict(name='stats.actor-section-contract', actor=pc, section=section,
                                        pages=pages, raw='\n'.join(pages)))
                sequence = [0] + list(range(1,len(pages))) + list(range(len(pages)-2,-1,-1))
                for index, page in enumerate(sequence):
                    name = prefix + ('.observed' if index == 0 else '.page-%d.visit-%d.observed' % (page, index-1))
                    if index:
                        self.add(name.replace('.observed','.press'), callback=('GUIREC',2,
                            0x7fff0203 if index < len(pages) else 0x7fff0202))
                    self.checks.append(dict(name='stats.actor-page', passed=True, actor=pc, section=section,
                                            page=page, pages=len(pages), content=pages[page]))
                    self.add(name, capture=(pc, pages[page], page, len(pages)))
        self.add('stats.record.close')
        self.add('stats.record.closed', capture=(4, '', 0, 1), closed=True)
        self.save()
        self.write('before.state.json', self.world)
        self.write('after.state.json', dict(self.world, selection=4))

    def add(self, name, callback=None, capture=None, closed=False):
        row = dict(action=name, step=len(self.actions), capture=None)
        if callback:
            sequence = len(self.callbacks)+1
            pack, wid, cid = callback
            call = dict(sequence=sequence, runtime_step=row['step']+1, nonce=NONCE,
                        performed=True, pack=pack, window=wid, control=cid)
            self.callbacks.append(call)
            self.write('callback-%d.json' % sequence, call)
            for side in ('before','after'):
                self.write('callback-%d-%s.state.json' % (sequence,side), self.world)
        if capture:
            self.captures += 1
            row['capture'] = self.captures
            pc, text, page, pages = capture
            controls = [] if closed else [dict(pack='GUIREC', window=2, id=cid, text=value, visible=True)
                for cid,value in ((45,text),(0x7fff0201,'%d / %d' % (page+1,pages)),
                                  (0x1000000e,'Actor%d'%pc),(0x10000029,'20'),(0x10000040,'14'))]
            self.write('capture-%d.ui.json' % self.captures, dict(controls=controls))
            self.write('capture-%d.state.json' % self.captures, dict(self.world,selection=pc))
            self.write('capture-%d.observer.json' % self.captures,
                       dict(actors=[dict(party_index=a,cached_thac0=14) for a in range(1,5)]))
            bmp = bytearray(58)
            bmp[:2] = b'BM'
            struct.pack_into('<I',bmp,2,len(bmp))
            struct.pack_into('<I',bmp,10,54)
            struct.pack_into('<ii',bmp,18,1,1)
            (self.path / ('capture-%d.bmp' % self.captures)).write_bytes(bmp)
        self.actions.append(row)
        self.checks.append(row)

    def save(self):
        self.write('menu-runtime.json', dict(nonce=NONCE, steps=len(self.actions), planned_steps=len(self.actions), checks=self.checks))
        self.write('menu-host-result.json',dict(nonce=NONCE,journey='stats',completed=True,captures=self.captures,callbacks=len(self.callbacks)))

    def validate(self, nonce=NONCE):
        return validation.validate_stage(self.path,(1,1),expected_nonce=nonce,tlk_path=self.tlk)

    def observed(self, actor=1, section=3):
        prefix = 'stats.actor-%d.section-%d.observed' % (actor,section)
        return next(a['capture'] for a in self.actions if a['action']==prefix)

    def test_complete_four_actor_journey(self):
        result = self.validate()
        self.assertEqual(result['actor_sections'],24)
        self.assertTrue(result['numeric_saves_and_resistances_validated'])
        self.assertFalse(result['independent_class_mechanics_oracle'])

    def test_stale_or_invalid_nonce_fails(self):
        for nonce in ('',None,'a'*32):
            with self.subTest(nonce=nonce), self.assertRaisesRegex(ValueError,'nonce'):
                self.validate(nonce)

    def test_missing_actor_section_fails(self):
        self.checks.remove(next(r for r in self.checks if r.get('name')=='stats.actor-section-contract'))
        self.save()
        with self.assertRaisesRegex(ValueError,'coverage'):
            self.validate()

    def test_wrong_later_page_fails(self):
        row = next(r for r in self.checks if r.get('name')=='stats.actor-page' and r['page']==1)
        row['page'] = 0
        self.save()
        with self.assertRaisesRegex(ValueError,'traversal'):
            self.validate()

    def test_native_number_mismatch_fails_even_with_consistent_runtime_and_ui(self):
        name = 'capture-%d.state.json' % self.observed()
        state = self.read(name)
        state['party'][0]['modified_stats'][14] = 25
        self.write(name,state)
        with self.assertRaisesRegex(ValueError,'numeric'):
            self.validate()

    def test_native_saving_throw_adjustment_is_required(self):
        name = 'capture-%d.state.json' % self.observed(section=2)
        state = self.read(name)
        state['party'][0]['base_stats'][9] = 2
        self.write(name,state)
        with self.assertRaisesRegex(ValueError,'numeric'):
            self.validate()

    def test_hidden_field_fails(self):
        name = 'capture-%d.ui.json' % self.observed()
        ui = self.read(name)
        ui['controls'][0]['visible'] = False
        self.write(name,ui)
        with self.assertRaisesRegex(ValueError,'visible field'):
            self.validate()

    def test_wrong_portrait_callback_fails(self):
        call = self.read('callback-1.json')
        call['control'] = 5
        self.write('callback-1.json',call)
        with self.assertRaisesRegex(ValueError,'callback'):
            self.validate()

    def test_callback_world_change_fails(self):
        state = copy.deepcopy(self.world)
        state['gold'] = 99
        self.write('callback-1-after.state.json',state)
        with self.assertRaisesRegex(ValueError,'callback changed'):
            self.validate()

    def test_whole_run_world_change_fails(self):
        self.write('after.state.json',dict(self.world,gold=99))
        with self.assertRaisesRegex(ValueError,'journey changed'):
            self.validate()

    def test_wrong_screenshot_resolution_fails(self):
        name = self.path / 'capture-1.bmp'
        bmp = bytearray(name.read_bytes())
        struct.pack_into('<i',bmp,18,2)
        name.write_bytes(bmp)
        with self.assertRaisesRegex(ValueError,'resolution'):
            self.validate()

    def test_native_callback_traceback_fails(self):
        (self.path/'process.log').write_text('[Python/ERROR]: Traceback (most recent call last):\n')
        with self.assertRaisesRegex(ValueError,'callback error'):
            self.validate()


if __name__ == '__main__':
    unittest.main()
