from pathlib import Path
import sys,tempfile,json,unittest,wave,math,struct
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import batch_product_videos as pipeline
import imageio_ffmpeg
from PIL import Image
FF=imageio_ffmpeg.get_ffmpeg_exe()
def fake_voice(text,path):
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000)
        f.writeframes(b''.join(struct.pack('<h',int(8000*math.sin(2*math.pi*330*i/24000))) for i in range(12000)))
class BatchBehavior(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);Image.new('RGB',(90,120),'red').save(self.base/'a.png');Image.new('RGB',(90,120),'blue').save(self.base/'b.png')
        self.job={'id':'one','title':'测试商品','sentences':[{'text':'这是第一句。','images':['a.png','b.png']},{'text':'这是第二句。','images':['b.png','a.png']}]};self.manifest=self.base/'jobs.json';self.output=self.base/'results'
    def tearDown(self):self.tmp.cleanup()
    def write(self,jobs):self.manifest.write_text(json.dumps({'jobs':jobs},ensure_ascii=False),encoding='utf-8')
    def run_batch(self):return pipeline.batch(self.manifest,self.output,FF,speaker=fake_voice)
    def test_duplicate_ids_rejected_before_writes(self):
        self.write([self.job,self.job])
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.run_batch()
        self.assertFalse(self.output.exists())
    def test_unowned_folder_never_modified(self):
        self.write([self.job]);self.output.mkdir();(self.output/'keep.txt').write_text('keep')
        with self.assertRaisesRegex(ValueError,'Refusing'):self.run_batch()
        self.assertEqual((self.output/'keep.txt').read_text(),'keep')
    def test_identical_pictures_and_multiple_sentences_rejected(self):
        self.job['sentences'][0]['images']=['a.png','a.png']
        with self.assertRaisesRegex(ValueError,'genuinely different'):pipeline.validate_job(self.job,self.base)
        self.job['sentences'][0]={'text':'一句。另一句。','images':['a.png','b.png']}
        with self.assertRaisesRegex(ValueError,'split multiple'):pipeline.validate_job(self.job,self.base)
    def test_input_cannot_escape_manifest(self):
        self.job['sentences'][0]['images']=['../outside.png','b.png']
        with self.assertRaisesRegex(ValueError,'inside'):pipeline.validate_job(self.job,self.base)
    def test_metadata_change_does_not_count_as_second_picture(self):
        from PIL.PngImagePlugin import PngInfo
        info=PngInfo();info.add_text('label','different metadata')
        Image.open(self.base/'a.png').save(self.base/'a-copy.png',pnginfo=info)
        self.job['sentences'][0]['images']=['a.png','a-copy.png']
        with self.assertRaisesRegex(ValueError,'genuinely different'):pipeline.validate_job(self.job,self.base)
    def test_failed_job_does_not_block_valid_job_and_resume(self):
        bad={'id':'bad','title':'缺图','sentences':[{'text':'测试。','images':['missing.png','b.png']}]};self.write([bad,self.job]);r=self.run_batch()
        self.assertEqual([x['status'] for x in r['jobs']],['FAILED','GENERATED_REVIEW_REQUIRED'])
        self.assertTrue((self.output/r['jobs'][1]['video']).is_file());again=self.run_batch();self.assertEqual(again['jobs'][1]['status'],'SKIPPED_UNCHANGED');self.assertEqual(again['stats']['speech_requests'],0)
    def test_edit_one_sentence_only_rebuilds_one_clip(self):
        self.write([self.job]);first=self.run_batch();old=self.output/first['jobs'][0]['video'];oldhash=pipeline.digest(old)
        self.job['sentences'][1]['text']='现在只改第二句。';self.write([self.job]);second=self.run_batch()
        self.assertEqual(second['stats']['clips_rendered'],1);self.assertEqual(second['stats']['clip_cache_hits'],1);self.assertEqual(second['stats']['speech_requests'],1);self.assertNotEqual(first['jobs'][0]['video'],second['jobs'][0]['video']);self.assertEqual(pipeline.digest(old),oldhash)
    def test_voice_failure_not_repeated_for_each_job(self):
        other={**self.job,'id':'two'};self.write([self.job,other]);calls=[]
        def broken(text,path):calls.append(text);raise ConnectionError('offline')
        r=pipeline.batch(self.manifest,self.output,FF,speaker=broken)
        self.assertEqual(len(calls),1);self.assertTrue(all(x['status']=='BLOCKED_SPEECH_SERVICE' for x in r['jobs']))
    def test_changed_existing_video_is_not_overwritten(self):
        self.write([self.job]);r=self.run_batch();p=self.output/r['jobs'][0]['video'];p.write_bytes(b'user changed this video');again=self.run_batch()
        self.assertEqual(again['jobs'][0]['status'],'FAILED');self.assertEqual(p.read_bytes(),b'user changed this video')
if __name__=='__main__':unittest.main()
