"""Batch product MP4s: two or more supplied images per sentence, burned captions, resumable caches."""
from pathlib import Path
import argparse,csv,hashlib,html,json,math,re,shutil,subprocess,tempfile,time,wave
VERSION=5  # 渲染行为改动必须升这个号，否则旧片段缓存会被命中、看不到修复效果
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
def wrap_px(draw,text,font,max_width):
    """按真实像素宽度折行。固定字数折行会把「registry-video-20261018」切成
    「registry-video-20261」+「018」，断在数字中间；按宽度算就不会。"""
    text=str(text).replace('\r',' ').replace('\n',' ').strip()
    if not text:return ['']
    lines,cur=[],''
    for ch in text:
        if draw.textlength(cur+ch,font=font)<=max_width:
            cur+=ch;continue
        # 需要断行：当前行里有分隔符就尽量断在分隔符后，不切在单词或数字中间
        cut=max((cur.rfind(s) for s in '-_/ ' if s in cur),default=-1)
        if cut>0 and len(cur)-cut<=12:
            lines.append(cur[:cut+1].rstrip());cur=cur[cut+1:]+ch
        else:
            lines.append(cur);cur=ch
    if cur:lines.append(cur)
    return lines
def ass_time(t):
    c=round(t*100);return f'{c//360000}:{c//6000%60:02d}:{c//100%60:02d}.{c%100:02d}'
def ass_escape(s):return s.replace('\\','＼').replace('{','｛').replace('}','｝')
def caption_screens(text,per_line=13,max_lines=3):
    """把一句文案折成若干「屏」，每屏内多行同屏显示，行间用 ASS 的 \\N 换行。

    旧实现按 13 字硬切再逐块轮流显示，16 字的一句话会变成
    「前 13 字显示 3 秒 + 剩 2 字闪 0.46 秒」；长句更会碎成十几个闪块，
    观众读不完整句。现在短句一屏内折行同时显示，只有超过 max_lines 行的
    超长句才分屏（每屏仍是完整可读的若干行）。
    注意：先做 ass_escape 再插入 \\N，否则反斜杠会被转义成全角、换行失效。
    """
    text=ass_escape(str(text).replace('\r',' ').replace('\n',' ')).strip()
    if not text:return ['']
    parts=[s for s in re.split('(?<=[，。！？、；])',text) if s.strip()]
    cap=per_line*max_lines;screens=[];cur=''
    for part in parts:
        while len(part)>cap:
            if cur:screens.append(cur);cur=''
            screens.append(part[:cap]);part=part[cap:]
        if len(cur)+len(part)>cap:
            screens.append(cur);cur=part
        else:cur+=part
    if cur:screens.append(cur)
    return ['\\N'.join(_rows(s,per_line)) for s in screens]
def _rows(s,per_line):
    """行内折行：优先在标点后断，避免把「不出门」拆成「不出 / 门」。

    中文没有空格，按字数硬切会稳定断在词中间；先按标点切成小段再贪心装行，
    在不超过 per_line 的前提下尽量整段放进一行。
    """
    parts=[p for p in re.split('(?<=[，。！？、；：])',s) if p]
    rows=[];cur=''
    for p in parts:
        while len(p)>per_line:
            if cur:rows.append(cur);cur=''
            rows.append(p[:per_line]);p=p[per_line:]
        if len(cur)+len(p)<=per_line:cur+=p
        else:
            if cur:rows.append(cur)
            cur=p
    if cur:rows.append(cur)
    # 末行只剩一两个字（常常只是一个句号）时，从上一行借最少的字
    if len(rows)>1 and len(rows[-1])<4:
        take=min(4-len(rows[-1]),len(rows[-2])-per_line//2)
        if take>0:
            rows[-1]=rows[-2][-take:]+rows[-1];rows[-2]=rows[-2][:-take]
    return rows
def captions(text,seconds,path):
    chunks=caption_screens(text);visible=lambda s:len(s.replace('\\N',''));total=sum(map(visible,chunks)) or 1;at=.04;events=[]
    for s in chunks:
        end=min(seconds,at+(seconds-.04)*visible(s)/total);events.append(f'Dialogue: 0,{ass_time(at)},{ass_time(end)},Default,,0,0,0,,{s}');at=end
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei,44,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3,1,2,28,28,70,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    path.write_text(header+'\n'.join(events),encoding='utf-8')
def stash_stale(path,state):
    """缓存不完整时保留现场并让流程继续，而不是永久卡死。"""
    stamp=time.strftime('%Y%m%d-%H%M%S')
    target=path.with_name(path.name+'.stale-'+stamp)
    path.replace(target)
    state['cache_repaired']=state.get('cache_repaired',0)+1
TEMP_DIR_PREFIXES=('clip-','speech-','concat-')
def clean_orphan_temps(root):
    """清掉上一次运行被中断时残留的临时目录，返回清理个数。

    这些目录由 tempfile.TemporaryDirectory 创建，正常结束会自动删除；
    只有进程被杀才会残留（表现为 clip-cache/clip-xxxxxx 之类）。
    它们只是 ffmpeg 中间文件，删掉不影响任何可复用的缓存。
    """
    removed=0
    for folder in ('clip-cache','speech-cache','products'):
        base=Path(root)/folder
        if not base.is_dir():continue
        for p in base.rglob('*'):
            if p.is_dir() and p.name.startswith(TEMP_DIR_PREFIXES):
                shutil.rmtree(p,ignore_errors=True);removed+=1
    return removed
def resolved_sentences(rows):
    """从每个任务的真实结果里数出已经落地的片段数（含上一轮跳过未改动的成片）。

    为什么不能只数本进程的计数器：整批重跑时每个任务都走 SKIPPED_UNCHANGED，
    既不配音也不渲染，计数器全是 0，但磁盘上 6 段成片都在。旧口径据此写出
    「片段数 0 ≠ 句数 6」并暗示任务没做完——把一次正常的缓存复用报成了故障。

    只数 sentence_timing：那是这个任务实际拼进成片的句子清单。
    GENERATED_REVIEW_REQUIRED 和 SKIPPED_UNCHANGED 都带它；FAILED / BLOCKED 不带，
    自然计 0，正好是"这段没落地"。
    """
    total=0
    for row in rows or ():
        if not isinstance(row,dict):continue
        timing=row.get('sentence_timing')
        if isinstance(timing,list):total+=len(timing)
    return total
def status_counts(rows):
    """按状态分类计数。报告里要能一眼看出「没改动的」和「失败的」各几条。"""
    counts={'jobs_total':0,'jobs_generated':0,'jobs_skipped':0,'jobs_failed':0}
    for row in rows or ():
        counts['jobs_total']+=1
        status=row.get('status') if isinstance(row,dict) else None
        if status=='SKIPPED_UNCHANGED':counts['jobs_skipped']+=1
        elif status=='GENERATED_REVIEW_REQUIRED':counts['jobs_generated']+=1
        else:counts['jobs_failed']+=1
    return counts
def stats_summary(state,expected_sentences,rows=None):
    """把「本进程新做了什么」和「这份报告最终落地了多少段」分成两件事说清楚。

    只报 speech_requests 会让人误以为 6 句只配了 1 次音：若上一轮运行被中断，
    大部分片段已经是缓存命中，本进程确实只新做了几条。所以这里同时给出
    本进程工作量（*_this_run）、整体落地数（clips_resolved）和一致性标记。

    rows 给出时以「每个任务实际拼进去的句子数」为准（含缓存跳过的任务）；
    老调用点不传 rows 时退回按本进程计数器求和，行为与旧版一致。
    """
    rendered=state.get('clips_rendered',0);cache_hits=state.get('clip_cache_hits',0)
    requests=state.get('speech_requests',0);speech_hits=state.get('speech_cache_hits',0)
    clips=resolved_sentences(rows) if rows is not None else rendered+cache_hits
    out=dict(state)
    out.update({'sentences_expected':expected_sentences,'clips_resolved':clips,
                'speech_calls':requests+speech_hits,           # 兼容旧字段名：本进程总调用数
                'speech_calls_this_run':requests,
                'speech_from_cache_this_run':speech_hits,
                'clips_rendered_this_run':rendered,
                'clips_from_cache_this_run':cache_hits,
                'stats_consistent':clips==expected_sentences})
    if rows is not None:out.update(status_counts(rows))
    if not out['stats_consistent']:
        out['stats_note']=('已落地 %d 段 ≠ 应有 %d 段：逐条看 jobs 字段里的 status，'
                           'FAILED/BLOCKED 的那几条就是缺口' % (clips,expected_sentences))
    return out
def speech(text,root,state,speaker,voice_label='zh-CN-XiaoxiaoNeural',audio_ext='.mp3'):
    if speaker is None:
        # 只有真的要调用在线语音时才导入 edge-tts，离线配音不依赖它。
        from synthesize_xiaoxiao import synthesize_text as provider
        provider_tag=digest(Path(__file__).with_name('synthesize_xiaoxiao.py'))
    else:
        provider=speaker;provider_tag='injected:'+str(voice_label)
    fingerprint=key({'text':text,'voice':voice_label,'rate':'+12%','version':VERSION,'provider':provider_tag,'audio_ext':audio_ext})
    folder=owned_dir(root,'speech-cache');mp3=folder/(fingerprint+audio_ext);meta=folder/(fingerprint+'.json')
    if mp3.exists():
        intact=False
        try:intact=meta.exists() and json.loads(meta.read_text(encoding='utf-8'))['sha256']==digest(mp3)
        except (OSError,ValueError,KeyError):intact=False
        if intact:
            state['speech_cache_hits']+=1;return mp3
        stash_stale(mp3,state)
        if meta.exists():stash_stale(meta,state)
    if state.get('speech_blocked'):raise SpeechUnavailable('Speech service unavailable earlier in this run; no repeated request')
    try:
        with tempfile.TemporaryDirectory(prefix='speech-',dir=folder) as tmp:
            tmp=Path(tmp);p=tmp/('voice'+audio_ext);provider(text,p)
            if not p.is_file() or p.stat().st_size<128:raise RuntimeError('No usable voice file returned')
            with mp3.open('xb') as dest,p.open('rb') as src:shutil.copyfileobj(src,dest)
        save(meta,{'sha256':digest(mp3),'voice':voice_label,'rate':'+12%','text':text});state['speech_requests']+=1;return mp3
    except Exception as e:state['speech_blocked']=True;raise SpeechUnavailable('Voice generation failed: '+type(e).__name__) from e
def sentence_clip(row,title,root,ff,pace,state,speaker,voice_label='zh-CN-XiaoxiaoNeural',audio_ext='.mp3'):
    style={'version':VERSION,'title':title,'text':row['text'],'images':row['image_hashes'],'pace':pace,'size':[720,1280],'captions':'burned','voice':voice_label,'audio_ext':audio_ext}
    fingerprint=key(style);folder=owned_dir(root,'clip-cache');clip=folder/(fingerprint+'.mp4');meta=folder/(fingerprint+'.json')
    if clip.exists():
        intact=False;info=None
        try:
            info=json.loads(meta.read_text(encoding='utf-8'));intact=info['sha256']==digest(clip)
        except (OSError,ValueError,KeyError):intact=False
        if intact:
            state['clip_cache_hits']+=1;return clip,info['seconds']
        stash_stale(clip,state)
        if meta.exists():stash_stale(meta,state)
    voice=speech(row['text'],root,state,speaker,voice_label,audio_ext)
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
            for k,line in enumerate(wrap_px(d,title,font,660)):d.text((30,20+k*43),line,font=font,fill='#282622')
            frame.save(tmp/f'{n:02d}.jpg',quality=94);lines.extend([f"file '{n:02d}.jpg'",f'duration {duration/len(row["images"])}'])
        lines.append(f"file '{len(row['images'])-1:02d}.jpg'");(tmp/'slides.txt').write_text('\n'.join(lines),encoding='utf-8');captions(row['text'],seconds,tmp/'captions.ass')
        command(ff,['-f','concat','-safe','1','-i','slides.txt','-i','voice.wav','-vf','fps=25,ass=captions.ass','-t',str(duration),'-c:v','libx264','-preset','fast','-crf','22','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-ar','44100','-ac','2','-af','apad','clip.mp4'],tmp)
        with clip.open('xb') as dest,(tmp/'clip.mp4').open('rb') as src:shutil.copyfileobj(src,dest)
    save(meta,{'sha256':digest(clip),'seconds':duration,'style':style});state['clips_rendered']+=1;return clip,duration
def render_job(job,root,ff,pace,state,speaker,voice_label='zh-CN-XiaoxiaoNeural',audio_ext='.mp3'):
    fingerprint=key({'job':{'id':job['id'],'title':job['title'],'sentences':[{'text':r['text'],'images':r['image_hashes']} for r in job['sentences']]},'pace':pace,'version':VERSION,'voice_label':voice_label,'audio_ext':audio_ext,'provider':('injected' if speaker else digest(Path(__file__).with_name('synthesize_xiaoxiao.py')))})
    dest=root/'products'/('job_'+job['id'])/fingerprint[:16];result=dest/'result.json';video=dest/'video.mp4'
    if result.exists():
        report=json.loads(result.read_text(encoding='utf-8'))
        if video.is_file() and report.get('video_sha256')==digest(video):return {**report,'status':'SKIPPED_UNCHANGED'}
        raise ValueError('Existing product result changed; preserve and inspect it')
    clips=[];timing=[];at=0
    for i,row in enumerate(job['sentences'],1):
        p,seconds=sentence_clip(row,job['title'],root,ff,pace,state,speaker,voice_label,audio_ext);clips.append(p);timing.append({'sentence':i,'text':row['text'],'start':round(at,3),'seconds':seconds,'pictures':len(row['images']),'picture_seconds':seconds/len(row['images'])});at+=seconds
    dest=owned_dir(root,dest.relative_to(root))
    with tempfile.TemporaryDirectory(prefix='concat-',dir=dest) as tmp:
        tmp=Path(tmp);names=[]
        for i,p in enumerate(clips):shutil.copyfile(p,tmp/f'{i:02d}.mp4');names.append(f"file '{i:02d}.mp4'")
        (tmp/'clips.txt').write_text('\n'.join(names),encoding='utf-8');command(ff,['-f','concat','-safe','1','-i','clips.txt','-c','copy','-movflags','+faststart','assembled.mp4'],tmp)
        command(ff,['-i',str(tmp/'assembled.mp4'),'-f','null','-'])
        if video.exists():
            # result.json 丢了但成片还在（上次崩溃在写记录之前）：先留现场再重出，避免永久 FAILED。
            stash_stale(video,state)
        with video.open('xb') as dst,(tmp/'assembled.mp4').open('rb') as src:shutil.copyfileobj(src,dst)
    report={'id':job['id'],'title':job['title'],'status':'GENERATED_REVIEW_REQUIRED','video':video.relative_to(root).as_posix(),'video_sha256':digest(video),'seconds':round(at,3),'sentence_timing':timing,'burned_subtitles':True,'minimum_pictures_per_sentence':2,'voice':voice_label,'pace':pace,'decode_passed':True,'human_reviewed':False}
    save(result,report);return report
def batch(manifest,output,ffmpeg,pace=1.2,speaker=None,voice_label='zh-CN-XiaoxiaoNeural',audio_ext='.mp3'):
    source,jobs=read_jobs(manifest)
    return batch_from_jobs(jobs,source.parent,output,ffmpeg,pace,speaker,voice_label,audio_ext)


def batch_from_jobs(jobs,base,output,ffmpeg,pace=1.2,speaker=None,voice_label='zh-CN-XiaoxiaoNeural',audio_ext='.mp3'):
    """直接接收 jobs 列表（图片路径相对 base），供统一入口在内存里组织任务，不必先写 manifest。"""
    if type(pace) not in {int,float} or not math.isfinite(pace) or not 1<=pace<=1.5:raise ValueError('Pace must be 1.0..1.5')
    ff=shutil.which(ffmpeg)
    if not ff:raise ValueError('FFmpeg unavailable')
    base=Path(base).resolve()
    if not isinstance(jobs,list) or not 1<=len(jobs)<=50:raise ValueError('Batch needs 1..50 jobs')
    if Path(output).is_symlink():raise ValueError('Output folder must not be a symbolic link')
    root=Path(output).resolve();marker=root/'batch-output.json'
    if root.exists():
        if root.is_symlink() or not marker.is_file() or json.loads(marker.read_text(encoding='utf-8')).get('tool')!='batch-product-videos':raise ValueError('Refusing to reuse a folder not created by this batch tool')
    else:root.mkdir(parents=True);save(marker,{'tool':'batch-product-videos','version':VERSION})
    state={'speech_requests':0,'speech_cache_hits':0,'clips_rendered':0,'clip_cache_hits':0};rows=[];started=time.monotonic()
    state['temp_cleaned']=clean_orphan_temps(root)
    for i,item in enumerate(jobs,1):
        ident=item.get('id',f'row-{i}') if isinstance(item,dict) else f'row-{i}'
        try:job=validate_job(item,base);row=render_job(job,root,ff,pace,state,speaker,voice_label,audio_ext)
        except Exception as e:row={'id':ident,'status':'BLOCKED_SPEECH_SERVICE' if isinstance(e,SpeechUnavailable) else 'FAILED','error_type':type(e).__name__,'error':str(e)[:500]}
        rows.append(row);print(f'{i}/{len(jobs)} {ident}: {row["status"]}',flush=True)
        # 中途落盘也要有可信统计：进程被杀时这份文件是唯一线索
        save(root/'batch-report.json',{'tool':'batch-product-videos','version':VERSION,'jobs':rows,
                                      'stats':stats_summary(state,sum(len(x.get('sentences') or []) for x in jobs if isinstance(x,dict)),rows),
                                      'complete':False})
    expected=sum(len(item.get('sentences') or []) for item in jobs if isinstance(item,dict))
    stats=stats_summary(state,expected,rows)
    report={'tool':'batch-product-videos','version':VERSION,'jobs':rows,'stats':stats,'elapsed_seconds':round(time.monotonic()-started,2),'complete':True,'published':False,'voice':voice_label};save(root/'batch-report.json',report)

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
