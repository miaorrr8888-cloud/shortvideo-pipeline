"""One local command: text -> Windows narration -> timed still-image MP4."""
import argparse,json,math,shutil
from pathlib import Path
from synthesize_voice import synthesize
from render_slideshow import prepare,render

def timing(slides,voice_seconds):
    if not math.isfinite(voice_seconds) or voice_seconds<=0:raise ValueError('voice duration must be finite and positive')
    total=sum(seconds for _,seconds in slides)
    if total<=0:raise ValueError('slides must have a positive duration')
    target=max(total,math.ceil(voice_seconds+.4))
    return [seconds/total*target for _,seconds in slides]

def create(manifest,text,output,ffmpeg='ffmpeg',language='zh-CN',voice='',subtitles=None):
    slides=prepare(manifest);output=Path(output).resolve()
    if subtitles and not Path(subtitles).is_file():raise ValueError('subtitle file missing')
    if output.exists():raise ValueError('output must be a new directory')
    # Dependency check before producing audio; no partially rendered false success.
    if not shutil.which(ffmpeg):raise ValueError('FFmpeg unavailable')
    output.mkdir(parents=True);stage='SPEECH'
    try:
        spoken=synthesize(text,output/'narration.wav',language,voice)
        durations=timing(slides,spoken['seconds']);stage='RENDER'
        inputs=output/'slides';inputs.mkdir();rows=[]
        for i,((image,_),duration) in enumerate(zip(slides,durations)):
            name=f'{i:03d}'+image.suffix.lower();shutil.copyfile(image,inputs/name)
            rows.append({'image':name,'seconds':duration})
        job=inputs/'manifest.json';job.write_text(json.dumps({'slides':rows},indent=2),encoding='utf-8')
        video=render(job,output/'video.mp4',ffmpeg,audio=output/'narration.wav',subtitles=subtitles)
        report={'status':'GENERATED_REVIEW_REQUIRED','speech':spoken,'video':video,'timing':'SLIDES_EXTENDED_TO_FIT_NARRATION','listening_and_visual_review_required':True}
    except Exception:
        (output/'status.json').write_text(json.dumps({'status':'FAILED','stage':stage}),encoding='utf-8')
        raise
    (output/'status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('text');p.add_argument('output');p.add_argument('--ffmpeg',default='ffmpeg');p.add_argument('--language',default='zh-CN');p.add_argument('--voice',default='');p.add_argument('--subtitles');a=p.parse_args()
    try:r=create(a.manifest,a.text,a.output,a.ffmpeg,a.language,a.voice,a.subtitles)
    except Exception as e:p.exit(2,'Narrated video failed: '+type(e).__name__+'; inspect local dependencies and status.json if created.\n')
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
