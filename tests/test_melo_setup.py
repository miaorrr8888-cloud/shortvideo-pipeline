import unittest,tempfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import start_here
from synthesize_melo import synthesize

class NewVoiceFailures(unittest.TestCase):
    def test_missing_model_is_diagnosable(self):
        with tempfile.TemporaryDirectory() as d:
            report=start_here.doctor(Path(d))
            self.assertEqual(report['status'],'MISSING_REQUIREMENTS')
            self.assertTrue(any(not x['ok'] and x['check'].startswith('model/') for x in report['checks']))
    def test_corrupt_archive_not_extracted(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'models').mkdir();(root/'models/melo.tar.bz2').write_bytes(b'bad archive')
            before=start_here.ROOT;start_here.ROOT=root
            try:
                with self.assertRaisesRegex(ValueError,'MODEL_CHECKSUM'):start_here.ensure_model(root/'models/vits-melo-tts-zh_en')
                self.assertFalse((root/'models/vits-melo-tts-zh_en').exists())
            finally:start_here.ROOT=before
    def test_existing_audio_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);(d/'text.txt').write_text('测试',encoding='utf-8');(d/'voice.wav').write_bytes(b'original')
            with self.assertRaisesRegex(ValueError,'new WAV'):synthesize(d/'text.txt',d/'voice.wav',d)
            self.assertEqual((d/'voice.wav').read_bytes(),b'original')
    def test_incomplete_model_creates_no_audio(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);(d/'text.txt').write_text('测试',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Missing model'):synthesize(d/'text.txt',d/'voice.wav',d)
            self.assertFalse((d/'voice.wav').exists())
if __name__=='__main__':unittest.main()
