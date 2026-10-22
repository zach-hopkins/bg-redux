import json
import struct
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import window_render_comparison as renderer


class WindowComparisonTests(unittest.TestCase):
    def image(self,path,data):
        path.write_bytes(data)
        bgr=bytearray(data);bgr[0::3]=data[2::3];bgr[2::3]=data[0::3]
        header=b'BM'+struct.pack('<IHHI',57654,0,0,54)+struct.pack('<IiiHHIIiiII',40,160,120,1,24,0,57600,0,0,0,0)
        path.with_suffix('.bmp').write_bytes(header+b''.join(bgr[y*480:(y+1)*480]for y in range(119,-1,-1)))

    def fixture(self,folder):
        cases=[];stems=['removed-final','dirty-0','dirty-1','dirty-2','partial-dirty','full-after-partial']
        for alpha in (202,255):
            for channel in (False,True):
                for scale in (75,100,125):
                    name='bg%d-alpha%d-scale%d'%(alpha,channel,scale);path=folder/name;path.mkdir()
                    transmission=255-alpha if channel else 0
                    black=[10,20,30];white=[v+transmission for v in black]
                    for stem in ['old','fresh-final']+stems:
                        data=bytearray(bytes([25,30,40])*19200)
                        if stem=='old':data[0]=99
                        self.image(path/(stem+'.rgb'),data)
                        self.image(path/(stem+'.black.rgb'),bytes(black)*19200)
                        self.image(path/(stem+'.white.rgb'),bytes(white)*19200)
                        (path/(stem+'.composite.json')).write_text(json.dumps(dict(probe=[80,80],black_rgb=black,white_rgb=white,transmission_rgb=[transmission]*3,direct_alpha_readback=False)))
                    cases.append(dict(id=name,background_alpha=alpha,window_alpha_channel=channel,scale_percent=scale,
                        reference='fresh-final.rgb',comparison_suffixes=['.rgb','.black.rgb','.white.rgb'],must_equal_reference_stems=stems,
                        expected_background_probe_transmission=transmission,transmission_rounding_tolerance=1,
                        partial_clip=[8,20,60,50],outside_sentinel=[130,90,15,15]))
        fixture=dict(schema='bg-redux-window-render-fixture/2',completed=True,game_mutations_requested=False,width=160,height=120,rgb_bytes_per_capture=57600,
            direct_alpha_readback=False,opacity_observation='paired-opaque-black-white-composition',cases=cases)
        (folder/'fixture.json').write_text(json.dumps(fixture))

    def test_complete_rgb_and_opacity_comparison(self):
        with tempfile.TemporaryDirectory()as tmp:
            folder=Path(tmp);self.fixture(folder);result=renderer.compare(folder)
            self.assertTrue(result['passed']);self.assertFalse(result['direct_alpha_readback'])

    def test_clipped_pixel_loss_is_a_failure(self):
        with tempfile.TemporaryDirectory()as tmp:
            folder=Path(tmp);self.fixture(folder);path=folder/'bg202-alpha1-scale100/partial-dirty.rgb'
            data=bytearray(path.read_bytes());data[12]=0;self.image(path,data)
            self.assertFalse(renderer.compare(folder)['passed'])

    def test_opacity_claim_must_match_backdrop_pixels(self):
        with tempfile.TemporaryDirectory()as tmp:
            folder=Path(tmp);self.fixture(folder);path=folder/'bg202-alpha1-scale100/dirty-0.composite.json'
            probe=json.loads(path.read_text());probe['transmission_rgb']=[0]*3;path.write_text(json.dumps(probe))
            with self.assertRaisesRegex(ValueError,'probe differs from pixels'):renderer.compare(folder)

    def test_missing_bmp_cannot_pass_raw_rgb_only(self):
        with tempfile.TemporaryDirectory()as tmp:
            folder=Path(tmp);self.fixture(folder)
            (folder/'bg202-alpha1-scale100/partial-dirty.bmp').unlink()
            with self.assertRaises(FileNotFoundError):renderer.compare(folder)


if __name__=='__main__':unittest.main()
