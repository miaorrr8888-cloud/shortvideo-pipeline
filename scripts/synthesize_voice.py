"""Offline Windows SAPI narration; no account, uploads, network, or voice cloning."""
import argparse,json,os,shutil,subprocess,tempfile,wave
from pathlib import Path

def synthesize(text_file,output,language='zh-CN',voice='',rate=0):
    text_file=Path(text_file).resolve();output=Path(output).resolve()
    text=text_file.read_text(encoding='utf-8-sig')
    if not text.strip() or len(text)>10000:raise ValueError('Text must contain 1..10000 characters')
    if type(rate)!=int or not -10<=rate<=10:raise ValueError('rate must be -10..10')
    if output.exists() or output.suffix.lower()!='.wav':raise ValueError('output must be a new .wav file')
    if os.name!='nt':raise ValueError('Windows SAPI requires Windows; supply an external narration file on other systems')
    executable=shutil.which('powershell.exe')
    if not executable:raise ValueError('Windows PowerShell unavailable')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='narration-',dir=output.parent) as d:
        d=Path(d);source=d/'text.txt';source.write_text(text,encoding='utf-8');temp=d/'voice.wav'
        argv=[executable,'-NoProfile','-NonInteractive','-File',str(Path(__file__).with_name('sapi_speech.ps1')),
              '-TextFile',str(source),'-OutputFile',str(temp),'-Language',language,'-Rate',str(rate)]
        if voice:argv+=['-VoiceName',voice]
        r=subprocess.run(argv,capture_output=True,encoding='utf-8',timeout=180)
        if r.returncode:raise ValueError('Local voice generation failed; check installed voices and locale')
        with wave.open(str(temp),'rb') as f:
            seconds=f.getnframes()/f.getframerate();channels=f.getnchannels();frames=f.getnframes()
        if frames==0:raise ValueError('Speech engine returned empty audio')
        meta=json.loads(r.stdout.lstrip('\ufeff').strip())
        with output.open('xb') as dest,temp.open('rb') as src:shutil.copyfileobj(src,dest)
    return {**meta,'seconds':round(seconds,3),'channels':channels,'output':str(output),'status':'SYNTHESIZED_LISTEN_REQUIRED'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('text');p.add_argument('output');p.add_argument('--language',default='zh-CN');p.add_argument('--voice',default='');p.add_argument('--rate',type=int,default=0);a=p.parse_args()
    try:r=synthesize(a.text,a.output,a.language,a.voice,a.rate)
    except (OSError,ValueError,subprocess.TimeoutExpired) as e:p.exit(2,'Speech error: '+str(e)+'\n')
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
