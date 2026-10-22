import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dialogue_render_comparison as render


class RenderComparisonTests(unittest.TestCase):
    def fixture(self,folder,ghost=False):
        width,height=772,113;stride=(width*3+3)&~3
        header=b'BM'+struct.pack('<IHHI',54+stride*height,0,0,54)+struct.pack('<IiiHHIIiiII',40,width,height,1,24,0,stride*height,0,0,0,0)
        for step in range(11):
            method='ordinary' if step<4 else 'dirty' if step<7 else 'clear' if step==7 else 'after-clear-dirty'
            name='render-'+str(step)+'-'+method
            raw=bytearray(stride*height)
            if ghost and step<4:raw[(height-1-30)*stride+100*3+2]=73
            (folder/(name+'.bmp')).write_bytes(header+raw)
            (folder/(name+'.text.json')).write_text(json.dumps(dict(message_text='same NPC',method=method,acceptance_run=False,window_flags=8)))

    def test_stable_repaint_matches_clear(self):
        with tempfile.TemporaryDirectory()as tmp:
            folder=Path(tmp);self.fixture(folder);result=render.compare(folder)
            self.assertTrue(result['ordinary_equals_cleared']);self.assertTrue(result['repeated_dirty_equals_cleared'])

    def test_old_pixel_is_detected_even_when_text_is_identical(self):
        with tempfile.TemporaryDirectory()as tmp:
            folder=Path(tmp);self.fixture(folder,True);result=render.compare(folder)
            self.assertFalse(result['ordinary_equals_cleared']);self.assertTrue(result['repeated_dirty_equals_cleared'])
            self.assertEqual(result['rows'][0]['different_text_crop_pixels'],1)
            self.assertEqual(result['rows'][0]['max_channel_difference'],73)

    def test_different_transcript_cannot_certify_render_equality(self):
        with tempfile.TemporaryDirectory()as tmp:
            folder=Path(tmp);self.fixture(folder)
            path=folder/'render-1-ordinary.text.json';text=json.loads(path.read_text());text['message_text']='different NPC';path.write_text(json.dumps(text))
            with self.assertRaisesRegex(ValueError,'transcript changed'):render.compare(folder)


if __name__=='__main__':unittest.main()
