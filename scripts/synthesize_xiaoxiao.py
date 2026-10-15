"""Generate the user-selected Xiaoxiao online voice using edge-tts helpers."""
from pathlib import Path
import json,urllib.request,urllib.parse,ssl,html,time,argparse
import websocket
from edge_tts.constants import WSS_URL,WSS_HEADERS,SEC_MS_GEC_VERSION
from edge_tts.communicate import connect_id,date_to_string,mkssml,ssml_headers_plus_data,get_headers_and_data
from edge_tts.data_classes import TTSConfig
from edge_tts.drm import DRM
def synthesize_text(text, p, voice="zh-CN-XiaoxiaoNeural"):
    proxy = urllib.parse.urlsplit(urllib.request.getproxies().get('https', ''))
    headers = DRM.headers_with_muid(dict(WSS_HEADERS))
    origin = headers.pop('Origin', None)
    url = f'{WSS_URL}&ConnectionId={connect_id()}&Sec-MS-GEC={DRM.generate_sec_ms_gec()}&Sec-MS-GEC-Version={SEC_MS_GEC_VERSION}'
    ws = websocket.create_connection(url, timeout=15, header=headers, origin=origin, http_proxy_host=proxy.hostname, http_proxy_port=proxy.port, sslopt={'context': ssl.create_default_context()})
    audio = []
    started = time.monotonic()
    try:
        ws.send(f'X-Timestamp:{date_to_string()}\r\nContent-Type:application/json; charset=utf-8\r\nPath:speech.config\r\n\r\n' + json.dumps({'context': {'synthesis': {'audio': {'metadataoptions': {'sentenceBoundaryEnabled': 'false', 'wordBoundaryEnabled': 'false'}, 'outputFormat': 'audio-24khz-48kbitrate-mono-mp3'}}}}) + '\r\n')
        tc = TTSConfig(voice=voice, rate='+12%', volume='+0%', pitch='+0Hz', boundary='WordBoundary')
        ws.send(ssml_headers_plus_data(connect_id(), date_to_string(), mkssml(tc, html.escape(text))))
        while time.monotonic() - started < 45:
            data = ws.recv()
            if isinstance(data, bytes):
                length = int.from_bytes(data[:2], 'big')
                h, a = get_headers_and_data(data, length)
                if h.get(b'Path') == b'audio' and a:
                    audio.append(a)
            elif 'Path:turn.end' in data:
                break
        if not audio:
            raise RuntimeError('No audio returned')
        p.write_bytes(b''.join(audio))
        return p.stat().st_size
    finally:
        ws.close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('text');p.add_argument('output');a=p.parse_args();out=Path(a.output)
 if out.exists():p.exit(2,'Choose a new output filename.\n')
 text=Path(a.text).read_text(encoding='utf-8-sig').strip()
 if not text or len(text)>4000:p.exit(2,'Use 1..4000 characters.\n')
 out.parent.mkdir(parents=True,exist_ok=True);print('Audio bytes:',synthesize_text(text,out))
