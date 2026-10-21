"""Mutation checks grounded in an executed stock GUI save/load run."""
from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gui_comparison import compare
from gui_harness import check_ui
from harness import LOCAL

class GUIOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidates=list((LOCAL/'results').glob('*gui-stock-verified*'))
        if not candidates: raise RuntimeError('Executed stock GUI fixture required; no silent skip')
        cls.fixture_run=max(candidates,key=lambda p:p.stat().st_mtime)
        cls.before=json.loads((cls.fixture_run/'gui-save/overwrite-persisted.state.json').read_text())
        cls.after=json.loads((cls.fixture_run/'gui-reload/00-game.state.json').read_text())

    def test_damage_remains_visible(self):
        state=copy.deepcopy(self.after)
        state['party'][0]['base_stats'][0]-=1
        _,diff=compare(self.before,state)
        self.assertTrue(any(d['path']=='/party/0/base_stats/0' for d in diff))

    def test_changed_variable_remains_visible(self):
        state=copy.deepcopy(self.after)
        key=next(iter(state['globals']))
        state['globals'][key]+=1
        _,diff=compare(self.before,state)
        self.assertTrue(any(d['path'].startswith('/globals/') for d in diff))

    def test_unmatched_variable_marker_is_not_discarded(self):
        state=copy.deepcopy(self.after)
        marker=next(f for f in state['party'][1]['effects'] if f['opcode']==187)
        marker['parameters'][0]+=99
        _,diff=compare(self.before,state)
        self.assertTrue(any(d['path'].startswith('/party/1/effects/') for d in diff))

    def test_extra_reload_time_is_not_discarded(self):
        state=copy.deepcopy(self.after)
        state['game_time']+=15
        _,diff=compare(self.before,state)
        self.assertTrue(any(d['path']=='/game_time' for d in diff))

    def test_unexplained_effect_difference_stays_red(self):
        result,diff=compare(self.before,self.after)
        self.assertFalse(result['passed'])
        self.assertTrue(any('/effects/' in d['path'] for d in diff))

    def ui_fixture(self, directory):
        for name in ['00-game.state.json','01-inventory.ui.json','02-record.ui.json']:
            (directory/name).write_bytes((self.fixture_run/'gui-save'/name).read_bytes())

    def test_blank_record_overview_fails_content_check(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder)
            self.ui_fixture(directory)
            file=directory/'02-record.ui.json'
            ui=json.loads(file.read_text())
            next(c for c in ui['controls'] if c['pack']=='GUIREC' and c['id']==45)['text']=''
            file.write_text(json.dumps(ui))
            self.assertTrue(any(c['name']=='record-overview-populated' and not c['passed'] for c in check_ui(directory)))

    def test_missing_name_control_cannot_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder)
            self.ui_fixture(directory)
            file=directory/'01-inventory.ui.json'
            ui=json.loads(file.read_text())
            ui['controls']=[c for c in ui['controls'] if not (c['pack']=='GUIINV' and c['id']==0x10000032)]
            file.write_text(json.dumps(ui))
            with self.assertRaises(ValueError): check_ui(directory)

if __name__=='__main__': unittest.main()
