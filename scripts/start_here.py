"""Project-local installation, diagnosis and demo for the MeloTTS video route."""
import argparse,hashlib,importlib,json,os,shutil,subprocess,sys,tarfile,time,urllib.request,venv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
URL='https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-melo-tts-zh_en.tar.bz2'
SHA='e58351ed7149f290a54534538badd4077cdbe6fddc964b24d0bee870415d1514'
PACKAGES=['sherpa-onnx==1.13.8','soundfile==0.14.0','Pillow','imageio-ffmpeg==0.6.0']
def launch(args):subprocess.run(args,check=True,cwd=ROOT)
def vpython():return ROOT/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
def ensure_model(folder):
    if all((folder/x).is_file() for x in ['model.onnx','tokens.txt','lexicon.txt','LICENSE']):return
    store=ROOT/'models';store.mkdir(exist_ok=True);archive=store/'melo.tar.bz2';part=archive.with_suffix('.part')
    if not archive.exists():
        start=part.stat().st_size if part.exists() else 0
        request=urllib.request.Request(URL,headers={'User-Agent':'shortvideo-pipeline-local-setup/1.0',**({'Range':f'bytes={start}-'} if start else {})})
        print('正在下载中文语音模型（约167MB）。中断后重新运行可继续。',flush=True)
        with urllib.request.urlopen(request,timeout=60) as response:
            resume=start>0 and response.status==206
            with part.open('ab' if resume else 'wb') as dest:shutil.copyfileobj(response,dest)
        if hashlib.sha256(part.read_bytes()).hexdigest()!=SHA:raise ValueError('MODEL_CHECKSUM: 下载不完整或文件版本变化；保留文件供检查，未解压。')
        part.rename(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=SHA:raise ValueError('MODEL_CHECKSUM: 模型压缩包校验失败。')
    with tarfile.open(archive) as t:
        for m in t.getmembers():
            dest=(store/m.name).resolve()
            if not dest.is_relative_to(store.resolve()) or m.issym() or m.islnk():raise ValueError('UNSAFE_ARCHIVE: 不安全压缩包成员。')
        t.extractall(store,filter='data')
def doctor(model):
    rows=[{'check':'python','ok':sys.version_info[:2]==(3,12),'detail':sys.version.split()[0]}]
    for mod in ['sherpa_onnx','soundfile','PIL','imageio_ffmpeg']:
        try:importlib.import_module(mod);rows.append({'check':mod,'ok':True})
        except Exception as e:rows.append({'check':mod,'ok':False,'detail':str(e)})
    for f in ['model.onnx','tokens.txt','lexicon.txt','LICENSE']:rows.append({'check':'model/'+f,'ok':(model/f).is_file()})
    if rows[4]['ok']:
        import imageio_ffmpeg
        binary=imageio_ffmpeg.get_ffmpeg_exe();check=subprocess.run([binary,'-version'],capture_output=True)
        rows.append({'check':'ffmpeg','ok':check.returncode==0})
    return {'status':'READY' if all(x['ok'] for x in rows) else 'MISSING_REQUIREMENTS','checks':rows}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--install',action='store_true');p.add_argument('--demo',action='store_true');p.add_argument('--doctor',action='store_true');p.add_argument('--model-dir');p.add_argument('--output');p.add_argument('--inside',action='store_true',help=argparse.SUPPRESS);a=p.parse_args()
    if sys.version_info[:2]!=(3,12):p.exit(2,'请安装Python 3.12后重试：https://www.python.org/downloads/windows/\n本自动安装路线仅在3.12验证。\n')
    if a.install and not a.inside:
        py=vpython()
        try:
            if not py.exists():print('1/4 正在本项目创建运行环境。',flush=True);venv.create(ROOT/'.venv',with_pip=True)
            print('2/4 正在安装本项目需要的工具。',flush=True);launch([str(py),'-m','pip','install',*PACKAGES])
            forwarded=sys.argv[1:]
            if a.model_dir:forwarded[forwarded.index('--model-dir')+1]=str(Path(a.model_dir).resolve())
            if a.output:forwarded[forwarded.index('--output')+1]=str(Path(a.output).resolve())
            launch([str(py),str(Path(__file__).resolve()),*forwarded,'--inside']);return
        except Exception as e:
            resultfile=ROOT/'runs/setup-result.json';resultfile.parent.mkdir(exist_ok=True);resultfile.write_text(json.dumps({'status':'FAILED','stage':'DEPENDENCIES_OR_CHILD','error':str(e)},ensure_ascii=False,indent=2),encoding='utf-8')
            p.exit(2,'安装或演示未完成。请把 runs/setup-result.json 交给助手检查；成功输出不会被覆盖。\n')
    model=Path(a.model_dir).expanduser().resolve() if a.model_dir else ROOT/'models/vits-melo-tts-zh_en'
    stage='MODEL'
    try:
        if a.install:
            print('3/4 检查中文语音模型。',flush=True)
            if a.model_dir and not all((model/f).is_file() for f in ['model.onnx','tokens.txt','lexicon.txt','LICENSE']):raise ValueError('指定的模型目录不完整。')
            ensure_model(model)
        report=doctor(model);print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
        if report['status']!='READY':raise ValueError('缺少项目环境。请运行 python scripts/start_here.py --install --demo；已安装时用 .venv 中的Python运行。')
        if a.demo:
            stage='DEMO';import imageio_ffmpeg
            from make_melo_video import create
            output=Path(a.output).resolve() if a.output else ROOT/'runs'/time.strftime('demo-%Y%m%d-%H%M%S')
            print('4/4 正在用两张示例图生成视频。',flush=True)
            result=create(ROOT/'examples/slides/manifest.json',ROOT/'examples/narration.txt',output,model,imageio_ffmpeg.get_ffmpeg_exe())
            print('已生成，请打开：'+str(output/'video.mp4'),flush=True)
            report['demo']=result
        resultfile=ROOT/'runs/setup-result.json';resultfile.parent.mkdir(exist_ok=True);resultfile.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    except Exception as e:
        fail=ROOT/'runs/setup-result.json';fail.parent.mkdir(exist_ok=True);fail.write_text(json.dumps({'status':'FAILED','stage':stage,'error':str(e)},ensure_ascii=False,indent=2),encoding='utf-8')
        p.exit(2,f'未完成：{e}\n详情已保存：{fail}\n把该文件和“安装与排错.md”交给助手排查。\n')
if __name__=='__main__':main()
