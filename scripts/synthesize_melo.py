"""Local Chinese narration with the official sherpa-onnx MeloTTS model bundle."""
import argparse,json,wave
from pathlib import Path

def synthesize(text_file,output,model_dir,speed=.95):
    import sherpa_onnx,soundfile as sf
    model=Path(model_dir).resolve();target=Path(output).resolve()
    text=Path(text_file).read_text(encoding='utf-8-sig').strip()
    if not text or len(text)>10000:raise ValueError('Use 1..10000 characters')
    if not .5<=speed<=2:raise ValueError('Speed must be 0.5..2')
    if target.exists():raise ValueError('Choose a new WAV filename')
    for name in ['model.onnx','tokens.txt','lexicon.txt']:
        if not (model/name).is_file():raise ValueError('Missing model file: '+name)
    cfg=sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=str(model/'model.onnx'),tokens=str(model/'tokens.txt'),lexicon=str(model/'lexicon.txt'),dict_dir=str(model/'dict')),num_threads=4,provider='cpu'),max_num_sentences=1)
    if not cfg.validate():raise ValueError('Invalid model bundle')
    tts=sherpa_onnx.OfflineTts(cfg);gen=sherpa_onnx.GenerationConfig();gen.sid=0;gen.speed=speed;gen.silence_scale=.4
    audio=tts.generate(text,gen)
    if len(audio.samples)==0:raise RuntimeError('No audio generated')
    target.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive creation preserves existing user files.
    with target.open('xb') as dest:
        sf.write(dest,audio.samples,audio.sample_rate,format='WAV',subtype='PCM_16')
    return {'engine':'MeloTTS via sherpa-onnx','seconds':len(audio.samples)/audio.sample_rate,'windows_system_voice':False,'output':str(target),'status':'SYNTHESIZED_REVIEW_REQUIRED'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('text');p.add_argument('output');p.add_argument('--model-dir',required=True);p.add_argument('--speed',type=float,default=.95);a=p.parse_args()
    print(json.dumps(synthesize(a.text,a.output,a.model_dir,a.speed),ensure_ascii=False,indent=2))
