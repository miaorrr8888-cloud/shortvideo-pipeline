"""Images and text -> local MeloTTS narration -> timed MP4."""
import argparse,json,math,shutil
from pathlib import Path
from synthesize_melo import synthesize
from render_slideshow import prepare,render

def create(manifest,text,output,model_dir,ffmpeg):
    slides=prepare(manifest);out=Path(output).resolve()
    if out.exists():raise ValueError('Choose a new output directory')
    if not shutil.which(ffmpeg):raise ValueError('FFmpeg is unavailable')
    out.mkdir(parents=True)
    try:
        speech=synthesize(text,out/'narration.wav',model_dir)
        total=sum(s for _,s in slides);duration=max(total,math.ceil(speech['seconds']+.4))
        inputs=out/'slides';inputs.mkdir();rows=[]
        for i,(image,sec) in enumerate(slides):
            name=f'{i:03d}'+image.suffix;shutil.copyfile(image,inputs/name);rows.append({'image':name,'seconds':sec/total*duration})
        job=inputs/'manifest.json';job.write_text(json.dumps({'slides':rows}),encoding='utf-8')
        video=render(job,out/'video.mp4',ffmpeg,audio=out/'narration.wav')
        report={'status':'GENERATED_REVIEW_REQUIRED','speech':speech,'video':video,'windows_system_voice':False}
    except Exception:
        (out/'status.json').write_text('{"status":"FAILED"}',encoding='utf-8');raise
    (out/'status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('text');p.add_argument('output');p.add_argument('--model-dir',required=True);p.add_argument('--ffmpeg',default='ffmpeg');a=p.parse_args()
    print(json.dumps(create(a.manifest,a.text,a.output,a.model_dir,a.ffmpeg),ensure_ascii=False,indent=2))
