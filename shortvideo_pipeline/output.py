"""输出层：按时长命名规则落盘产物，便于 Finder/文件管理器浏览。

命名约定（遵循用户规范：文件以时长秒数后缀命名）：
- 顶层文件夹：{时长}s_{slug}/
- 文件：口播稿_{时长}s.txt / 分镜_{时长}s.md / 字幕_{时长}s.srt /
       封面方案_{时长}s.md / BGM_{时长}s.md / 发布方案_{时长}s.md /
       metadata_{时长}s.json / README_{时长}s.md
"""

from __future__ import annotations

import json
import os
from typing import List

from .models import VideoPackage


def _md_table(headers: List[str], rows: List[List[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for r in rows:
        lines.append("| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in r) + " |")
    return "\n".join(lines)


def write_package(pkg: VideoPackage, output_dir: str) -> str:
    """写入一个视频包，返回生成的文件夹路径。"""
    dur = pkg.computed_duration
    if not pkg.slug or os.path.basename(pkg.slug) != pkg.slug or pkg.slug in {'.','..'} or '/' in pkg.slug or '\\' in pkg.slug:
        raise ValueError('Invalid output slug')
    os.makedirs(output_dir, exist_ok=True)
    folder = os.path.join(output_dir, pkg.slug)
    number=1
    while True:
        try:
            os.mkdir(folder)
            break
        except FileExistsError:
            number+=1
            folder=os.path.join(output_dir,pkg.slug+'_'+str(number))

    # 1) 口播稿（纯文本，提词器即用）
    if pkg.script:
        with open(os.path.join(folder, f"口播稿_{dur}s.txt"), "w", encoding="utf-8") as fh:
            fh.write(pkg.script.pure_text())

    # 2) 分镜表
    if pkg.storyboard:
        rows = [
            [s.index, s.time_range, s.section, s.visual, s.camera, s.narration_ref]
            for s in pkg.storyboard.shots
        ]
        md = "# 分镜表\n\n" + _md_table(
            ["#", "时间", "段落", "画面", "运镜", "口播节选"], rows
        )
        with open(os.path.join(folder, f"分镜_{dur}s.md"), "w", encoding="utf-8") as fh:
            fh.write(md + "\n")

    # 3) 字幕 SRT
    if pkg.subtitle:
        with open(os.path.join(folder, f"字幕_{dur}s.srt"), "w", encoding="utf-8") as fh:
            fh.write(pkg.subtitle.to_srt())

    # 4) 封面方案
    if pkg.cover:
        c = pkg.cover
        md = (
            "# 封面方案\n\n"
            f"- **大标题**：{c.title}\n"
            f"- **副标题**：{c.subtitle}\n"
            f"- **风格**：{c.style}\n"
            f"- **配色**：{c.color_scheme}\n"
            f"- **版式**：{c.layout}\n"
            f"- **字体**：{c.font_hint}\n"
        )
        with open(os.path.join(folder, f"封面方案_{dur}s.md"), "w", encoding="utf-8") as fh:
            fh.write(md)

    # 5) BGM
    if pkg.bgm:
        b = pkg.bgm
        md = (
            "# BGM 建议\n\n"
            f"- **情绪**：{b.mood}\n"
            f"- **曲风**：{b.genre}\n"
            f"- **参考**：{b.reference}\n"
            f"- **配乐节点**：{', '.join(b.cue_points)}\n"
        )
        with open(os.path.join(folder, f"BGM_{dur}s.md"), "w", encoding="utf-8") as fh:
            fh.write(md)

    # 6) 发布方案
    if pkg.publish:
        p = pkg.publish
        md = (
            "# 发布方案\n\n"
            f"- **平台**：{', '.join(p.platforms)}\n"
            f"- **时段**：{p.best_time}\n"
            f"- **话题**：{' '.join('#' + h for h in p.hashtags)}\n"
            f"- **文案**：{p.caption}\n"
        )
        with open(os.path.join(folder, f"发布方案_{dur}s.md"), "w", encoding="utf-8") as fh:
            fh.write(md)

    # 7) 元数据 JSON（完整包，便于二次处理/校验）
    with open(os.path.join(folder, f"metadata_{dur}s.json"), "w", encoding="utf-8") as fh:
        json.dump(pkg.to_dict(), fh, ensure_ascii=False, indent=2)

    # 8) 总览 README
    _write_readme(pkg, folder, dur)
    return folder


def _write_readme(pkg: VideoPackage, folder: str, dur: int) -> None:
    b = pkg.brief
    lines = [
        f"# 短视频生产包：{b.title}",
        "",
        f"- 目标时长：{b.duration_target}s ｜ 实际分配：{pkg.computed_duration}s",
        f"- 平台：{b.platform} ｜ 风格：{b.style}",
        "",
        "## 文件清单",
        f"- 口播稿_{dur}s.txt —— 纯口播文本，提词器/剪映直接可用",
        f"- 分镜_{dur}s.md —— 分镜表（时间/画面/运镜）",
        f"- 字幕_{dur}s.srt —— 字幕文件",
        f"- 封面方案_{dur}s.md —— 封面标题/配色/版式",
        f"- BGM_{dur}s.md —— 配乐情绪与节点",
        f"- 发布方案_{dur}s.md —— 平台/时段/话题/文案",
        f"- metadata_{dur}s.json —— 完整结构化数据",
        "",
        "## 使用建议",
        "1. 用 口播稿 配合提词器录制；",
        "2. 按 分镜表 在剪映图文成片/手动对齐画面；",
        "3. 导入 字幕 SRT；",
        "4. 按 封面方案 出封面；",
        "5. 参考 发布方案 定时发布。",
    ]
    with open(os.path.join(folder, f"README_{dur}s.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
