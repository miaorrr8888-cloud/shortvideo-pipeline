"""Install project dependencies and generate a sample with the selected Xiaoxiao voice."""
import argparse,json,os,subprocess,sys,time,venv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--install',action='store_true');p.add_argument('--inside',action='store_true',help=argparse.SUPPRESS);a=p.parse_args();stage='ENVIRONMENT'
    try:
        if sys.version_info[:2]!=(3,12):raise ValueError('请准备Python 3.12，详见晓晓使用指南.md。')
        if a.install and not a.inside:
            py=ROOT/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
            if not py.exists():print('1/3 创建项目环境。',flush=True);venv.create(ROOT/'.venv',with_pip=True)
            print('2/3 安装项目工具。',flush=True)
            subprocess.run([str(py),'-m','pip','install','edge-tts==7.3.1','websocket-client==1.9.2','Pillow','imageio-ffmpeg==0.6.0'],cwd=ROOT,check=True)
            subprocess.run([str(py),str(Path(__file__).resolve()),'--inside'],cwd=ROOT,check=True);return
        import imageio_ffmpeg
        from make_xiaoxiao_video import create
        stage='SYNTHESIS_AND_RENDER';print('3/3 使用晓晓在线配音生成示例。',flush=True)
        out=ROOT/'runs'/time.strftime('xiaoxiao-%Y%m%d-%H%M%S')
        result=create(ROOT/'examples/slides/manifest.json',ROOT/'examples/narration.txt',out,imageio_ffmpeg.get_ffmpeg_exe())
        print('已生成，请打开：'+str(out/'video.mp4'),flush=True)
        target=ROOT/'runs/setup-xiaoxiao.json';target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    except Exception as e:
        target=ROOT/'runs/setup-xiaoxiao.json';target.parent.mkdir(exist_ok=True);target.write_text(json.dumps({'status':'FAILED','stage':stage,'error_type':type(e).__name__},ensure_ascii=False),encoding='utf-8')
        p.exit(2,'未完成：'+str(e)+'\n请读取晓晓使用指南.md；错误阶段见runs/setup-xiaoxiao.json。不要反复请求或自动换声音。\n')
if __name__=='__main__':main()
