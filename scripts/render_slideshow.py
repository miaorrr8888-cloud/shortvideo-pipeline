"""Render a narrated still-image slideshow with local FFmpeg; no model/API calls."""
import argparse,json,math,shutil,subprocess,tempfile
from pathlib import Path

def prepare(manifest):
    manifest=Path(manifest).resolve();data=json.loads(manifest.read_text(encoding='utf-8-sig'))
    slides=data.get('slides') if isinstance(data,dict) else None
    if not isinstance(slides,list) or not slides or len(slides)>100:raise ValueError('slides must contain 1..100 entries')
    from PIL import Image
    prepared=[]
    for slide in slides:
        if not isinstance(slide,dict) or not isinstance(slide.get('image'),str):raise ValueError('slide image required')
        raw=manifest.parent/slide['image'];image=raw.resolve();duration=slide.get('seconds')
        if raw.is_symlink() or not image.is_relative_to(manifest.parent) or not image.is_file():raise ValueError('image must be inside manifest directory')
        if type(duration) not in {int,float} or not math.isfinite(duration) or not 0<duration<=300:raise ValueError('seconds must be finite, positive and <=300')
        with Image.open(image) as im:im.verify()
        prepared.append((image,duration))
    if sum(d for _,d in prepared)>1800:raise ValueError('total duration must not exceed 30 minutes')
    return prepared

def render(manifest,output,ffmpeg='ffmpeg',audio=None,subtitles=None,width=720,height=1280):
    from PIL import Image,ImageOps
    slides=prepare(manifest);output=Path(output).resolve()
    if output.exists() or output.suffix.lower()!='.mp4':raise ValueError('output must be a new .mp4 file')
    if type(width)!=int or type(height)!=int or not 16<=width<=3840 or not 16<=height<=3840 or width%2 or height%2:raise ValueError('dimensions must be even integers 16..3840')
    engine=shutil.which(ffmpeg)
    if not engine:raise ValueError('FFmpeg is unavailable; install locally or pass --ffmpeg executable')
    for optional in (audio,subtitles):
        if optional and not Path(optional).is_file():raise ValueError('audio/subtitle file missing')
    output.parent.mkdir(parents=True,exist_ok=True)
    # All FFmpeg inputs use generated local names. External protocols are disabled for image list.
    with tempfile.TemporaryDirectory(prefix='slideshow-',dir=output.parent) as temp:
        temp=Path(temp);lines=['ffconcat version 1.0']
        for i,(image,seconds) in enumerate(slides):
            with Image.open(image) as im:
                frame=ImageOps.pad(im.convert('RGB'),(width,height),color='black');frame.save(temp/f'{i:03d}.png')
            lines.extend([f"file '{i:03d}.png'",f'duration {seconds}'])
        lines.append(f"file '{len(slides)-1:03d}.png'");(temp/'slides.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        cmd=[engine,'-hide_banner','-loglevel','error','-n','-protocol_whitelist','file,pipe','-safe','1','-f','concat','-i','slides.txt']
        if audio:shutil.copyfile(audio,temp/'voice.audio');cmd+=['-i','voice.audio']
        if subtitles:shutil.copyfile(subtitles,temp/'captions.srt');cmd+=['-i','captions.srt']
        cmd+=['-map','0:v:0']
        if audio:cmd+=['-map','1:a:0','-c:a','aac','-af','apad']
        if subtitles:cmd+=['-map',f'{2 if audio else 1}:s:0','-c:s','mov_text']
        cmd+=['-t',str(sum(d for _,d in slides)),'-r','25','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart','result.mp4']
        run=subprocess.run(cmd,cwd=temp,capture_output=True,timeout=600)
        if run.returncode:raise ValueError('FFmpeg failed; verify codecs and optional media files')
        # Exclusive creation avoids overwriting another process's result.
        with output.open('xb') as dest,(temp/'result.mp4').open('rb') as src:shutil.copyfileobj(src,dest)
    return {'output':str(output),'seconds':sum(d for _,d in slides),'audio_included':bool(audio),'subtitle_track_included':bool(subtitles),'status':'RENDERED_REVIEW_REQUIRED'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('output');p.add_argument('--ffmpeg',default='ffmpeg');p.add_argument('--audio');p.add_argument('--subtitles');p.add_argument('--width',type=int,default=720);p.add_argument('--height',type=int,default=1280);p.add_argument('--check',action='store_true');a=p.parse_args()
    try:
        if a.check:r={'slides':len(prepare(a.manifest)),'status':'INPUT_VALIDATED_NOT_RENDERED'}
        else:r=render(a.manifest,a.output,a.ffmpeg,a.audio,a.subtitles,a.width,a.height)
    except (OSError,ValueError,ImportError,subprocess.TimeoutExpired) as e:p.exit(2,'Render error: '+str(e)+'\n')
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
