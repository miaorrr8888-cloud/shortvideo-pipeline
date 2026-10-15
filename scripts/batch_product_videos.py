"""Batch product MP4s: two or more supplied images per sentence, burned captions, resumable caches."""
from pathlib import Path
import argparse,csv,hashlib,html,json,math,re,shutil,subprocess,tempfile,time,wave
VERSION=1
class SpeechUnavailable(RuntimeError):pass
def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def key(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def save(p,data):
    p=Path(p);tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(p)
def owned_dir(root,relative):
    p=root/relative
    if p.is_symlink() or not p.resolve().is_relative_to(root):raise ValueError('Output subfolder must stay inside this batch folder')
    p.mkdir(parents=True,exist_ok=True);return p
def command(ff,args,cwd=None):
    r=subprocess.run([ff,'-hide_banner','-loglevel','error','-n',*args],cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
    if r.returncode:raise RuntimeError('FFmpeg failed: '+r.stderr[-500:])
def safe_file(base,value):
    if not isinstance(value,str) or not value:raise ValueError('Image path required')
    raw=base/value;p=raw.resolve()
    if raw.is_symlink() or not p.is_relative_to(base) or not p.is_file():raise ValueError('Image must be a file inside the manifest folder: '+value)
    from PIL import Image
    with Image.open(p) as im:
        if im.width*im.height>40_000_000:raise ValueError('Image is too large')
        im.verify()
    return p
def validate_job(job,base):
    if not isinstance(job,dict):raise ValueError('Job must be an object')
    ident=job.get('id');title=job.get('title',ident)
    if not isinstance(ident,str) or not re.fullmatch('[a-z0-9][a-z0-9-]{0,47}',ident):raise ValueError('Use a unique lowercase job id, 1..48 characters')
    if not isinstance(title,str) or not 1<=len(title)<=40:raise ValueError('Product title must have 1..40 characters')
    sentences=job.get('sentences')
    if not isinstance(sentences,list) or not 1<=len(sentences)<=30:raise ValueError('Each product needs 1..30 sentence rows')
    rows=[]
    for i,row in enumerate(sentences,1):
        if not isinstance(row,dict):raise ValueError('Sentence row must be an object')
        text=row.get('text');pictures=row.get('images')
        if not isinstance(text,str) or not 1<=len(text.strip())<=160:raise ValueError(f'Sentence {i}: use 1..160 characters')
        text=text.strip()
        if len([s for s in re.split('[。！？!?]+',text) if s.strip()])>1:raise ValueError(f'Sentence {i}: split multiple sentences into separate rows')
        if not isinstance(pictures,list) or not 2<=len(pictures)<=6:raise ValueError(f'Sentence {i}: supply 2..6 different pictures')
        images=[safe_file(base,x) for x in pictures];hashes=[digest(p) for p in images]
        from PIL import Image
        visual_hashes=[]
        for image in images:
            with Image.open(image) as im:visual_hashes.append(hashlib.sha256(str(im.size).encode()+im.convert('RGB').tobytes()).hexdigest())
        if len(set(visual_hashes))<2:raise ValueError(f'Sentence {i}: at least two genuinely different image files are required')
        rows.append({'text':text,'images':images,'image_hashes':hashes})
    return {'id':ident,'title':title,'sentences':rows}
def read_jobs(manifest):
    p=Path(manifest).resolve();data=json.loads(p.read_text(encoding='utf-8-sig'));jobs=data.get('jobs') if isinstance(data,dict) else None
    if not isinstance(jobs,list) or not 1<=len(jobs)<=50:raise ValueError('Batch needs 1..50 jobs')
    ids=[j['id'] for j in jobs if isinstance(j,dict) and isinstance(j.get('id'),str)]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate product ids are not allowed')
    return p,jobs
def wrap(text,width=16):
    text=str(text).replace('\r',' ').replace('\n',' ')
    return [text[i:i+width] for i in range(0,len(text),width)]
def ass_time(t):
    c=round(t*100);return f'{c//360000}:{c//6000%60:02d}:{c//100%60:02d}.{c%100:02d}'
def ass_escape(s):return s.replace('\\','＼').replace('{','｛').replace('}','｝')
def captions(text,seconds,path):
    chunks=[]
    for part in re.split('(?<=[，。！？、；])',text):chunks.extend(wrap(part,16))
    chunks=[s for s in chunks if s.strip()];total=sum(map(len,chunks));at=.04;events=[]
    for s in chunks:
        end=min(seconds,at+(seconds-.04)*len(s)/total);events.append(f'Dialogue: 0,{ass_time(at)},{ass_time(end)},Default,,0,0,0,,{ass_escape(s)}');at=end
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei,36,&H00FFFFFF,&H000000FF,&H90000000,&H90000000,0,0,0,0,100,100,0,0,3,2,0,2,28,28,70,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    path.write_text(header+'\n'.join(events),encoding='utf-8')
def speech(text,root,state,speaker):
    from synthesize_xiaoxiao import synthesize_text
    provider=speaker or synthesize_text;source=Path(__file__).with_name('synthesize_xiaoxiao.py')
    fingerprint=key({'text':text,'voice':'zh-CN-XiaoxiaoNeural','rate':'+12%','version':VERSION,'provider':digest(source),'test_provider':bool(speaker)})
    folder=owned_dir(root,'speech-cache');mp3=folder/(fingerprint+'.mp3');meta=folder/(fingerprint+'.json')
    if mp3.exists():
        if not meta.exists() or json.loads(meta.read_text(encoding='utf-8'))['sha256']!=digest(mp3):raise ValueError('Speech cache damaged; preserve it and inspect before retry')
        state['speech_cache_hits']+=1;return mp3
    if state.get('speech_blocked'):raise SpeechUnavailable('Speech service unavailable earlier in this run; no repeated request')
    try:
        with tempfile.TemporaryDirectory(prefix='speech-',dir=folder) as tmp:
            tmp=Path(tmp);p=tmp/'voice.mp3';provider(text,p)
            if not p.is_file() or p.stat().st_size<128:raise RuntimeError('No usable voice file returned')
            with mp3.open('xb') as dest,p.open('rb') as src:shutil.copyfileobj(src,dest)
        save(meta,{'sha256':digest(mp3),'voice':'zh-CN-XiaoxiaoNeural','rate':'+12%','text':text});state['speech_requests']+=1;return mp3
    except Exception as e:state['speech_blocked']=True;raise SpeechUnavailable('Online voice failed: '+type(e).__name__) from e
def sentence_clip(row,title,root,ff,pace,state,speaker):
    style={'version':VERSION,'title':title,'text':row['text'],'images':row['image_hashes'],'pace':pace,'size':[720,1280],'captions':'burned','voice':'Xiaoxiao +12%','test_provider':bool(speaker)}
    fingerprint=key(style);folder=owned_dir(root,'clip-cache');clip=folder/(fingerprint+'.mp4');meta=folder/(fingerprint+'.json')
    if clip.exists():
        if not meta.exists() or json.loads(meta.read_text(encoding='utf-8'))['sha256']!=digest(clip):raise ValueError('Video cache damaged; inspect before retry')
        info=json.loads(meta.read_text(encoding='utf-8'));state['clip_cache_hits']+=1;return clip,info['seconds']
    voice=speech(row['text'],root,state,speaker)
    from PIL import Image,ImageOps,ImageDraw,ImageFont
    with tempfile.TemporaryDirectory(prefix='clip-',dir=folder) as tmp:
        tmp=Path(tmp);wav=tmp/'voice.wav'
        command(ff,['-i',str(voice),'-af',f'highpass=f=60,loudnorm=I=-16:TP=-1.5:LRA=7,atempo={pace}','-ar','44100',str(wav)])
        with wave.open(str(wav),'rb') as f:seconds=f.getnframes()/f.getframerate()
        duration=max(len(row['images'])*1.0,math.ceil((seconds+.10)*25)/25);lines=[]
        fonts=Path('C:/Windows/Fonts/msyhbd.ttc')
        if not fonts.exists():raise ValueError('This portrait template currently requires Windows Microsoft YaHei font')
        font=ImageFont.truetype(str(fonts),32)
        for n,p in enumerate(row['images']):
            frame=Image.new('RGB',(720,1280),'#fff8ee');im=ImageOps.contain(Image.open(p).convert('RGB'),(720,1030));frame.paste(im,((720-im.width)//2,115+(1030-im.height)//2))
            d=ImageDraw.Draw(frame)
            for k,line in enumerate(wrap(title,20)):d.text((30,20+k*43),line,font=font,fill='#282622')
            frame.save(tmp/f'{n:02d}.jpg',quality=94);lines.extend([f"file '{n:02d}.jpg'",f'duration {duration/len(row["images"])}'])
        lines.append(f"file '{len(row['images'])-1:02d}.jpg'");(tmp/'slides.txt').write_text('\n'.join(lines),encoding='utf-8');captions(row['text'],seconds,tmp/'captions.ass')
        command(ff,['-f','concat','-safe','1','-i','slides.txt','-i','voice.wav','-vf','fps=25,ass=captions.ass','-t',str(duration),'-c:v','libx264','-preset','fast','-crf','22','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-ar','44100','-ac','2','-af','apad','clip.mp4'],tmp)
        with clip.open('xb') as dest,(tmp/'clip.mp4').open('rb') as src:shutil.copyfileobj(src,dest)
    save(meta,{'sha256':digest(clip),'seconds':duration,'style':style});state['clips_rendered']+=1;return clip,duration
def render_job(job,root,ff,pace,state,speaker):
    fingerprint=key({'job':{'id':job['id'],'title':job['title'],'sentences':[{'text':r['text'],'images':r['image_hashes']} for r in job['sentences']]},'pace':pace,'version':VERSION,'voice_impl':digest(Path(__file__).with_name('synthesize_xiaoxiao.py')),'test_provider':bool(speaker)})
    dest=root/'products'/('job_'+job['id'])/fingerprint[:16];result=dest/'result.json';video=dest/'video.mp4'
    if result.exists():
        report=json.loads(result.read_text(encoding='utf-8'))
        if video.is_file() and report.get('video_sha256')==digest(video):return {**report,'status':'SKIPPED_UNCHANGED'}
        raise ValueError('Existing product result changed; preserve and inspect it')
    clips=[];timing=[];at=0
    for i,row in enumerate(job['sentences'],1):
        p,seconds=sentence_clip(row,job['title'],root,ff,pace,state,speaker);clips.append(p);timing.append({'sentence':i,'text':row['text'],'start':round(at,3),'seconds':seconds,'pictures':len(row['images']),'picture_seconds':seconds/len(row['images'])});at+=seconds
    dest=owned_dir(root,dest.relative_to(root))
    with tempfile.TemporaryDirectory(prefix='concat-',dir=dest) as tmp:
        tmp=Path(tmp);names=[]
        for i,p in enumerate(clips):shutil.copyfile(p,tmp/f'{i:02d}.mp4');names.append(f"file '{i:02d}.mp4'")
        (tmp/'clips.txt').write_text('\n'.join(names),encoding='utf-8');command(ff,['-f','concat','-safe','1','-i','clips.txt','-c','copy','-movflags','+faststart','assembled.mp4'],tmp)
        command(ff,['-i',str(tmp/'assembled.mp4'),'-f','null','-'])
        with video.open('xb') as dst,(tmp/'assembled.mp4').open('rb') as src:shutil.copyfileobj(src,dst)
    report={'id':job['id'],'title':job['title'],'status':'GENERATED_REVIEW_REQUIRED','video':video.relative_to(root).as_posix(),'video_sha256':digest(video),'seconds':round(at,3),'sentence_timing':timing,'burned_subtitles':True,'minimum_pictures_per_sentence':2,'voice':'Xiaoxiao +12%','pace':pace,'decode_passed':True,'human_reviewed':False}
    save(result,report);return report
def batch(manifest,output,ffmpeg,pace=1.2,speaker=None):
    if type(pace) not in {int,float} or not math.isfinite(pace) or not 1<=pace<=1.5:raise ValueError('Pace must be 1.0..1.5')
    ff=shutil.which(ffmpeg)
    if not ff:raise ValueError('FFmpeg unavailable')
    source,jobs=read_jobs(manifest)
    if Path(output).is_symlink():raise ValueError('Output folder must not be a symbolic link')
    root=Path(output).resolve();marker=root/'batch-output.json'
    if root.exists():
        if root.is_symlink() or not marker.is_file() or json.loads(marker.read_text(encoding='utf-8')).get('tool')!='batch-product-videos':raise ValueError('Refusing to reuse a folder not created by this batch tool')
    else:root.mkdir(parents=True);save(marker,{'tool':'batch-product-videos','version':VERSION})
    state={'speech_requests':0,'speech_cache_hits':0,'clips_rendered':0,'clip_cache_hits':0};rows=[];started=time.monotonic()
    for i,item in enumerate(jobs,1):
        ident=item.get('id',f'row-{i}') if isinstance(item,dict) else f'row-{i}'
        try:job=validate_job(item,source.parent);row=render_job(job,root,ff,pace,state,speaker)
        except Exception as e:row={'id':ident,'status':'BLOCKED_SPEECH_SERVICE' if isinstance(e,SpeechUnavailable) else 'FAILED','error_type':type(e).__name__,'error':str(e)[:500]}
        rows.append(row);print(f'{i}/{len(jobs)} {ident}: {row["status"]}',flush=True)
        save(root/'batch-report.json',{'jobs':rows,'stats':state,'complete':False})
    report={'tool':'batch-product-videos','version':VERSION,'jobs':rows,'stats':state,'elapsed_seconds':round(time.monotonic()-started,2),'complete':True,'published':False};save(root/'batch-report.json',report)
    with (root/'batch-report.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['id','status','video','error']);w.writeheader()
        for row in rows:w.writerow({k:row.get(k,'') for k in w.fieldnames})
    cards=[]
    for row in rows:
        card=f'<article><h2>{html.escape(str(row["id"]))}</h2><p>{html.escape(row["status"])}</p>'
        if 'video' in row:card+=f'<video controls preload="metadata" src="{html.escape(row["video"],quote=True)}"></video><p><a href="{html.escape(row["video"],quote=True)}" download>保存这条视频</a></p>'
        else:card+='<pre>'+html.escape(row.get('error',''))+'</pre>'
        cards.append(card+'</article>')
    (root/'START_HERE.html').write_text('<!doctype html><meta charset="utf-8"><style>body{max-width:1100px;margin:30px auto;padding:20px;font:19px/1.8 system-ui;background:#fff8ee}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}video{width:100%;max-height:70vh}article{background:white;padding:15px}pre{white-space:pre-wrap}</style><h1>批量商品视频结果</h1><p>同一清单重跑会跳过未改动成片；改一句只重做相关片段。生成后仍需检查读音、事实、画面和素材许可。</p><main>'+''.join(cards)+'</main>',encoding='utf-8')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('output');p.add_argument('--ffmpeg',required=True);p.add_argument('--pace',type=float,default=1.2);a=p.parse_args()
    report=batch(a.manifest,a.output,a.ffmpeg,a.pace)
    raise SystemExit(2 if any(r['status'] in {'FAILED','BLOCKED_SPEECH_SERVICE'} for r in report['jobs']) else 0)
