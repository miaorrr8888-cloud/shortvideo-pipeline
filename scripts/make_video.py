#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""make_video.py —— 批量商品配音视频的统一入口。

用法:
    python scripts/make_video.py --check
    python scripts/make_video.py --images <图片文件夹> [--text 介绍.txt] --out <输出目录>
    python scripts/make_video.py --products <商品根目录> --out <输出目录>
    python scripts/make_video.py --images <图> --text <文案> --out <输出> --voice online --allow-online-voice

做什么:
  1. 先自检环境（Python / Pillow / ffmpeg / 中文字体 / 离线语音 / 在线语音依赖），缺什么给可复制的修复命令；
  2. 单商品：一个图片文件夹 + 一段介绍 → 竖屏 MP4（720x1280，烧录字幕，每句至少 2 张不同图片）；
  3. 多商品：商品根目录下每个子文件夹放 介绍.txt + 至少 2 张图 → 批量出片；
  4. 复用 batch_product_videos 的语音缓存与片段缓存：没改的句子不重做，改一句只重做那一段，旧成片保留。

配音与联网（重要）:
  * 默认 --voice offline：用本机 Windows SAPI 生成，纯本地，文本不外发、不联网、无费用。
  * --voice online：文本会发往微软 Edge 在线语音服务（speech.platform.bing.com），免账号免密钥，
    但**文本会离开本机**；必须同时加 --allow-online-voice 表示你已知情同意，否则直接拒绝执行。
  * 本入口不调用任何收费接口（不调用 SiliconFlow 等云端大模型）；文案由你提供，不做二次生成。
  * 图片只在本机参与渲染，不上传。

不做：不自动发布、不做版权审查、不保证读音正确、不把“已解码”当成“已人工试听”。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

VERSION = "0.2.2"
ONLINE_VOICE = "zh-CN-XiaoxiaoNeural"
OFFLINE_LABEL_PREFIX = "Windows SAPI 本地语音"
ONLINE_LABEL = "Microsoft Edge 在线语音 zh-CN-XiaoxiaoNeural"
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
TEXT_NAMES = ("介绍.txt", "介绍.md", "文案.txt", "text.txt", "narration.txt")

EXIT_OK, EXIT_PARTIAL, EXIT_INPUT, EXIT_BLOCKED = 0, 1, 2, 3


class Blocked(RuntimeError):
    """需要用户同意或补依赖才能继续。"""


def say(text: str = "") -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(text.encode(enc, "replace").decode(enc, "replace"))


# ------------------------------------------------------------------ 环境自检

def resolve_ffmpeg() -> tuple[str | None, str]:
    found = shutil.which("ffmpeg")
    if found:
        return found, "PATH"
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).is_file():
            return exe, f"imageio-ffmpeg {imageio_ffmpeg.__version__}"
    except Exception:
        pass
    return None, "未找到"


def resolve_powershell() -> str | None:
    """定位 powershell.exe（PATH 被裁剪时回落到 System32 固定路径）。

    真实踩坑：本机 PATH 里没有 WindowsPowerShell\\v1.0 目录，
    只用 shutil.which 会报「找不到 powershell.exe」，而系统里其实装着
    Microsoft Huihui 中文语音——自检说 PASS、出片却失败的错位就出在这里。
    """
    from win_env import resolve_powershell as _resolve

    return _resolve()


def chinese_sapi_voice() -> tuple[bool, str]:
    if os.name != "nt":
        return False, "非 Windows 系统"
    ps = resolve_powershell()
    if not ps:
        return False, "找不到 powershell.exe（PATH 与 System32 固定路径都没有）"
    try:
        r = subprocess.run(
            [ps, "-NoProfile", "-NonInteractive", "-Command",
             "$v=New-Object -ComObject SAPI.SpVoice;"
             "@($v.GetVoices())|Where-Object{($_.GetAttribute('Language') -split ';') -contains '804'}|"
             "ForEach-Object{$_.GetDescription()}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=25)
        names = [x.strip() for x in (r.stdout or "").splitlines() if x.strip()]
        return (bool(names), names[0] if names else "没有检测到中文离线语音")
    except Exception as exc:
        return False, f"检测失败：{type(exc).__name__}"


def doctor(verbose=True) -> dict:
    checks = []

    def add(name, ok, detail, fix=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail, "fix": fix})

    v = sys.version_info
    add("Python ≥ 3.10", v >= (3, 10), f"{v.major}.{v.minor}.{v.micro}", "安装 Python 3.10+ 后重开终端")

    try:
        import PIL
        add("Pillow", True, f"Pillow {PIL.__version__}", "")
    except Exception:
        add("Pillow", False, "未安装", "python -m pip install Pillow")

    ff, how = resolve_ffmpeg()
    add("FFmpeg", bool(ff), how if ff else "未找到（PATH 与 imageio-ffmpeg 都没有）",
        "python -m pip install imageio-ffmpeg  或安装 ffmpeg 并加入 PATH")

    font = Path("C:/Windows/Fonts/msyhbd.ttc")
    add("中文字体 msyhbd.ttc", font.exists(), str(font) if font.exists() else "缺失",
        "本模板要求 Windows 微软雅黑粗体；其他系统需自行改字体路径（未验证）")

    ok_voice, voice_detail = chinese_sapi_voice()
    if ok_voice:
        voice_fix = ""
    elif "找不到 powershell" in voice_detail:
        voice_fix = ("powershell.exe 不在 PATH：把 C:\\Windows\\System32\\WindowsPowerShell\\v1.0 "
                     "加回 PATH 后重开终端")
    else:
        voice_fix = "Windows 设置 → 时间和语言 → 语音 → 添加中文语音包"
    add("离线中文语音（SAPI）", ok_voice, voice_detail, voice_fix)

    have_edge = True
    try:
        import edge_tts  # noqa: F401
        import websocket  # noqa: F401
    except Exception:
        have_edge = False
    add("在线语音依赖（edge-tts + websocket-client）", have_edge,
        "已安装" if have_edge else "缺依赖，在线配音不可用",
        "python -m pip install edge-tts websocket-client   # 联网，且文本会发往微软")

    ready_offline = v >= (3, 10) and ff and font.exists() and ok_voice and _pillow_ok()
    ready_online = ready_offline and have_edge
    result = {
        "tool": "make_video.py", "version": VERSION,
        "checks": checks,
        "ready_offline": bool(ready_offline),
        "ready_online": bool(ready_online),
        "ffmpeg": ff, "ffmpeg_source": how,
        "voice_offline": voice_detail if ok_voice else None,
        "notice": "READY 只代表环境能跑，不代表配音好听、字幕对齐或内容正确。",
    }
    if verbose:
        say("环境自检")
        say("-" * 58)
        for c in checks:
            mark = "PASS" if c["ok"] else "FAIL"
            say(f"[{mark}] {c['check']}：{c['detail']}")
            if not c["ok"] and c["fix"]:
                say(f"       修复：{c['fix']}")
        say("-" * 58)
        say(f"离线配音可用：{'是' if ready_offline else '否'}　在线配音可用：{'是' if ready_online else '否'}")
        say(result["notice"])
    return result


def _pillow_ok() -> bool:
    try:
        import PIL  # noqa: F401
        return True
    except Exception:
        return False


# ------------------------------------------------------------------ 任务构建

def split_sentences(text: str, max_len=160, max_rows=30) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    parts = [s.strip() for s in re.findall(r"[^。！？!?]+[。！？!?]?", text) if s.strip()]
    out = []
    for p in parts:
        while len(p) > max_len:
            out.append(p[:max_len])
            p = p[max_len:]
        if p:
            out.append(p)
    if not out:
        raise ValueError("文案是空的")
    if len(out) > max_rows:
        raise ValueError(f"文案被切成 {len(out)} 句，超过单条视频 {max_rows} 句上限，请精简")
    return out


def collect_images(folder: Path) -> list[Path]:
    files = sorted(p for p in folder.iterdir()
                   if p.is_file() and not p.is_symlink() and p.suffix.lower() in IMG_EXT)
    if not files:
        raise ValueError(f"文件夹里没有可用图片（{'/'.join(sorted(IMG_EXT))}）：{folder}")
    return files


def visual_signature(path: Path) -> str:
    from PIL import Image
    with Image.open(path) as im:
        return hashlib.sha256(str(im.size).encode() + im.convert("RGB").tobytes()).hexdigest()


def assign_images(sentences: list[str], images: list[Path], base: Path, title: str, ident: str) -> dict:
    if len(images) < 2:
        raise ValueError(f"只有 {len(images)} 张图片：每句至少需要 2 张不同画面，请再补几张")
    sigs = {}
    for p in images:
        sigs.setdefault(visual_signature(p), []).append(p)
    if len(sigs) < 2:
        raise ValueError(f"{len(images)} 张图片内容完全相同（只是文件名不同），需要真正不同的画面")
    rows = []
    for i, s in enumerate(sentences):
        picks = [images[(2 * i) % len(images)], images[(2 * i + 1) % len(images)]]
        if visual_signature(picks[0]) == visual_signature(picks[1]):
            picks = [images[0], images[1]]
        rows.append({"text": s, "images": [p.relative_to(base).as_posix() for p in picks]})
    return {"id": ident, "title": title[:40] or "商品视频", "sentences": rows}


def read_intro(folder: Path) -> str:
    for name in TEXT_NAMES:
        p = folder / name
        if p.is_file() and not p.is_symlink():
            return p.read_text(encoding="utf-8-sig")
    raise ValueError(f"没找到介绍文案（{'、'.join(TEXT_NAMES)}），请用 --text 指定")


# ------------------------------------------------------------------ 配音策略

def make_offline_speaker(voice_name: str = ""):
    """返回 (text, path) -> None 的本地配音函数，全程不联网。"""
    from synthesize_voice import synthesize

    def speak(text: str, path: Path):
        path = Path(path)
        tmp_text = path.with_suffix(".src.txt")
        tmp_text.write_text(text, encoding="utf-8")
        try:
            synthesize(tmp_text, path, voice=voice_name)
        finally:
            tmp_text.unlink(missing_ok=True)
    return speak


def resolve_voice(args, env: dict) -> tuple[object, str, str, bool]:
    """返回 (speaker, label, audio_ext, needs_network)。speaker=None 表示走在线晓晓。"""
    voice = args.voice
    if voice == "auto":
        if env.get("ready_offline"):
            voice = "offline"
        else:
            missing = [c["check"] for c in env.get("checks", []) if not c["ok"]]
            raise Blocked("环境未就绪，没有开始渲染。缺失或异常：" + "、".join(missing)
                          + "\n  先跑 python scripts/make_video.py --check 按提示补齐；"
                            "自动模式不会为了绕过缺依赖而改用在线配音。")

    if voice == "offline":
        if not env.get("ready_offline"):
            raise Blocked("离线配音环境未就绪（缺 FFmpeg / Pillow / 中文字体 / 中文语音包），"
                          "先跑 --check 按提示补齐；或改用 --voice online --allow-online-voice")
        detail = env.get("voice_offline") or "Windows SAPI"
        return make_offline_speaker(args.offline_voice or ""), f"{OFFLINE_LABEL_PREFIX}（{detail}）", ".wav", False

    if voice == "online":
        if not args.allow_online_voice:
            raise Blocked(
                "在线配音需要你明确同意，本次未执行。\n"
                "  会上传什么：每句文案的文字内容（不含图片、不含文件）。\n"
                "  发到哪里：微软 Edge 在线语音服务 speech.platform.bing.com（TTS，免账号免密钥，非本机）。\n"
                "  是否收费：不收费，本工具也不会调用任何需要付费/密钥的接口。\n"
                "  要继续请加：--voice online --allow-online-voice\n"
                "  不想外发请改用：--voice offline")
        if not env.get("ready_online"):
            raise Blocked("在线配音依赖不完整（edge-tts / websocket-client 或基础环境缺失），先跑 --check")
        return None, ONLINE_LABEL, ".mp3", True

    raise ValueError(f"未知音色选项：{voice}")


# ------------------------------------------------------------------ 主流程

def run(argv=None) -> int:
    p = argparse.ArgumentParser(description="批量商品配音视频 · 统一入口（先自检，再出片）")
    p.add_argument("--check", action="store_true", help="只做环境自检")
    p.add_argument("--json", action="store_true", help="自检结果输出 JSON")
    p.add_argument("--images", help="单商品图片文件夹")
    p.add_argument("--text", help="介绍文案 .txt（不给则读文件夹里的 介绍.txt）")
    p.add_argument("--products", help="多商品根目录：每个子文件夹含 介绍.txt + ≥2 张图")
    p.add_argument("--out", help="输出文件夹（必须是新建或本工具创建的目录）")
    p.add_argument("--title", help="视频标题（默认取文件夹名）")
    p.add_argument("--voice", choices=["auto", "offline", "online"], default="auto",
                   help="auto=优先离线；offline=本机 SAPI 不联网；online=微软在线晓晓（需 --allow-online-voice）")
    p.add_argument("--allow-online-voice", action="store_true", help="同意把文案文字发送到微软在线语音服务")
    p.add_argument("--offline-voice", default="", help="指定本机 SAPI 音色全名，默认自动挑中文音色")
    p.add_argument("--pace", type=float, default=1.2, help="语速倍率 1.0~1.5，默认 1.2")
    p.add_argument("--dry-plan", action="store_true", help="只输出分句与配图计划，不渲染")
    args = p.parse_args(argv)

    env = doctor(verbose=not args.json)
    if args.json:
        say(json.dumps(env, ensure_ascii=False, indent=2))
    if args.check:
        if env["ready_offline"]:
            return EXIT_OK
        return EXIT_BLOCKED

    if not args.out:
        say("[错误] 缺 --out：请指定输出文件夹")
        return EXIT_INPUT
    if bool(args.images) == bool(args.products):
        say("[错误] --images 与 --products 必须二选一")
        return EXIT_INPUT

    out = Path(args.out).expanduser()
    try:
        speaker, voice_label, audio_ext, needs_net = resolve_voice(args, env)
    except Blocked as exc:
        say("[已阻止] " + str(exc))
        return EXIT_BLOCKED
    except ValueError as exc:
        say("[错误] " + str(exc))
        return EXIT_INPUT

    say("")
    say(f"配音方式：{voice_label}")
    say("  离线：文本留在本机，不联网、无费用。" if not needs_net
        else "  在线：文案文字会发往微软 speech.platform.bing.com；图片不上传；不调用收费接口。")
    say(f"输出目录：{out}")
    say("")

    try:
        if args.images:
            folder = Path(args.images).expanduser().resolve()
            if not folder.is_dir():
                say(f"[错误] 图片文件夹不存在：{folder}")
                return EXIT_INPUT
            text = Path(args.text).expanduser().read_text(encoding="utf-8-sig") if args.text else read_intro(folder)
            sentences = split_sentences(text)
            images = collect_images(folder)
            title = args.title or folder.name
            ident = "product-" + hashlib.sha256(str(title).encode("utf-8")).hexdigest()[:12]
            jobs = [assign_images(sentences, images, folder.parent, title, ident)]
            base = folder.parent
        else:
            root = Path(args.products).expanduser().resolve()
            if not root.is_dir():
                say(f"[错误] 商品根目录不存在：{root}")
                return EXIT_INPUT
            jobs = []
            for sub in sorted(root.iterdir()):
                if not sub.is_dir() or sub.is_symlink():
                    continue
                text = read_intro(sub)
                sentences = split_sentences(text)
                images = collect_images(sub)
                ident = "product-" + hashlib.sha256(sub.name.encode("utf-8")).hexdigest()[:12]
                jobs.append(assign_images(sentences, images, root, args.title or sub.name, ident))
            if not jobs:
                say(f"[错误] 根目录下没有可用商品子文件夹：{root}")
                return EXIT_INPUT
            base = root
    except (OSError, ValueError) as exc:
        say(f"[错误] {exc}")
        return EXIT_INPUT

    if args.dry_plan:
        say(json.dumps({"jobs": jobs, "voice": voice_label}, ensure_ascii=False, indent=2))
        say("（--dry-plan：只出计划，没有渲染视频）")
        return EXIT_OK

    ff, _ = resolve_ffmpeg()
    try:
        import batch_product_videos as engine
    except Exception as exc:
        say(f"[错误] 无法加载渲染引擎：{exc}")
        return EXIT_BLOCKED

    try:
        report = engine.batch_from_jobs(jobs, base, out, ff, args.pace, speaker, voice_label, audio_ext)
    except ValueError as exc:
        say(f"[错误] {exc}")
        return EXIT_INPUT

    bad = [r for r in report["jobs"] if r.get("status") in {"FAILED", "BLOCKED_SPEECH_SERVICE"}]
    say("")
    say("=" * 58)
    for r in report["jobs"]:
        say(f"{r['id']} → {r['status']}" + (f"　{out / r['video']}" if r.get("video") else f"　{r.get('error','')}"))
    st = report["stats"]
    say(f"配音调用 {st['speech_calls']} 次（本次新生成 {st['speech_requests']}，本次命中缓存 {st['speech_cache_hits']}）；"
        f"成片共 {st['clips_resolved']} 段（本次新渲染 {st['clips_rendered']}，本次命中缓存 {st['clip_cache_hits']}）")
    if st.get("jobs_skipped"):
        say(f"其中 {st['jobs_skipped']} 个商品与上次完全一致，整条成片直接复用，没有重新配音或渲染。")
    if not st.get("stats_consistent", True):
        say(f"注意：成片落地 {st['clips_resolved']} 段 ≠ 应有 {st['sentences_expected']} 段，"
            "差额来自失败的任务——看 batch-report.json 里 jobs 的 status 与 error。")
    say(f"结果页：{out / 'START_HERE.html'}")
    say(f"报告：{out / 'batch-report.json'}")
    say("提醒：已生成≠已试听。上传前请自己看一遍画面、听一遍读音，字幕错字要改文案重跑。")
    say("=" * 58)
    return EXIT_PARTIAL if bad else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(run())
