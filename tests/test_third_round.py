from pathlib import Path
import importlib.util,sys,unittest,tempfile,json
ROOT=Path(__file__).resolve().parents[1]
def load(path):
    sys.path.insert(0,str(ROOT/'scripts'))
    spec=importlib.util.spec_from_file_location('third',ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class NarrationInputs(unittest.TestCase):
    def test_empty_text_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'t.txt';p.write_text(' ')
            with self.assertRaises(ValueError):load('scripts/synthesize_voice.py').synthesize(p,Path(d)/'out.wav')
    def test_existing_audio_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'t.txt').write_text('Demo');(p/'out.wav').write_bytes(b'keep')
            with self.assertRaises(ValueError):load('scripts/synthesize_voice.py').synthesize(p/'t.txt',p/'out.wav')
            self.assertEqual((p/'out.wav').read_bytes(),b'keep')
    def test_invalid_rate_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'t.txt';p.write_text('Demo')
            with self.assertRaises(ValueError):load('scripts/synthesize_voice.py').synthesize(p,Path(d)/'out.wav',rate=True)

class NarrationTiming(unittest.TestCase):
    def test_audio_fits_without_trimming(self):
        m=load("scripts/make_narrated_video.py");durations=m.timing([("a",1),("b",3)],9.8)
        self.assertGreaterEqual(sum(durations),10.2);self.assertAlmostEqual(durations[1]/durations[0],3)
