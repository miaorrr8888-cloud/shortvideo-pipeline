"""User pictures and text -> selected online Xiaoxiao voice -> new MP4."""
from pathlib import Path
import argparse,json,math,shutil,subprocess,wave
from render_slideshow import prepare,render
from synthesize_xiaoxiao import synthesize_text
def create(manifest,text_file,output,ffmpeg):
    slides=prepare(manifest);text=Path(text_file).read_text(encoding='utf-8-sig').strip();out=Path(output).resolve()
    if not text or len(text)>4000:raise ValueError('Use 1..4000 characters')
    if out.exists():raise ValueError('Choose a new output directory')
    if not shutil.which(ffmpeg):raise ValueError('FFmpeg unavailable')
    out.mkdir(parents=True);stage='ONLINE_SPEECH'
    try:
        synthesize_text(text,out/'voice-raw.mp3')
        stage='AUDIO';r=subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-n','-i',str(out/'voice-raw.mp3'),'-af','highpass=f=60,loudnorm=I=-16:TP=-1.5:LRA=7','-ar','44100',str(out/'narration.wav')],capture_output=True,timeout=120)
        if r.returncode:raise RuntimeError('Audio conversion failed')
        with wave.open(str(out/'narration.wav'),'rb') as wav:seconds=wav.getnframes()/wav.getframerate()
        stage='RENDER';total=sum(sec for _,sec in slides);target=max(total,math.ceil(seconds+.25));inputs=out/'slides';inputs.mkdir();rows=[]
        for i,(image,sec) in enumerate(slides):
            name=f'{i:03d}'+image.suffix;shutil.copyfile(image,inputs/name);rows.append({'image':name,'seconds':sec/total*target})
        job=inputs/'manifest.json';job.write_text(json.dumps({'slides':rows}),encoding='utf-8')
        video=render(job,out/'video.mp4',ffmpeg,audio=out/'narration.wav')
        report={'status':'GENERATED_REVIEW_REQUIRED','voice':'zh-CN-XiaoxiaoNeural','rate':'+12%','online_service':True,'windows_system_voice':False,'voice_seconds':seconds,'video':video}
    except Exception:
        (out/'status.json').write_text(json.dumps({'status':'FAILED','stage':stage}),encoding='utf-8');raise
    (out/'status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('text');p.add_argument('output');p.add_argument('--ffmpeg',required=True);a=p.parse_args();print(json.dumps(create(a.manifest,a.text,a.output,a.ffmpeg),ensure_ascii=False,indent=2))
