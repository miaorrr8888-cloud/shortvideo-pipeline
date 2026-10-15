from pathlib import Path
import importlib.util,unittest,tempfile,json,sys,subprocess,os
ROOT=Path(__file__).resolve().parents[1]
def load(path):
    sys.path.insert(0,str(ROOT/'scripts'))
    spec=importlib.util.spec_from_file_location('extension',ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class LocalRenderInputs(unittest.TestCase):
    def manifest(self,d,seconds=1):
        from PIL import Image
        p=Path(d);Image.new('RGB',(10,10),'red').save(p/'a.png');(p/'slides.json').write_text(json.dumps({'slides':[{'image':'a.png','seconds':seconds}]}));return p/'slides.json'
    def test_real_image_and_duration(self):
        with tempfile.TemporaryDirectory() as d:self.assertEqual(load('scripts/render_slideshow.py').prepare(self.manifest(d))[0][1],1)
    def test_invalid_duration(self):
        for value in [True,0,float('nan')]:
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(ValueError):load('scripts/render_slideshow.py').prepare(self.manifest(d,value))
    def test_existing_output_never_replaced(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'out.mp4';p.write_bytes(b'preserve')
            with self.assertRaises(ValueError):load('scripts/render_slideshow.py').render(self.manifest(d),p)
            self.assertEqual(p.read_bytes(),b'preserve')
