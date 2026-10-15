"""步骤 7：字幕（SRT 时序由口播稿起止时间确定性推导，无需 LLM）。"""

from __future__ import annotations

from typing import Dict

from ..models import Script, SubtitleCue, SubtitleTrack, TopicBrief
from ..llm.base import LLMProvider


def generate(brief: TopicBrief, ctx: Dict, provider: LLMProvider) -> SubtitleTrack:
    script: Script = ctx.get("script")
    if script is None:
        raise ValueError("字幕步骤缺少 script 上下文")
    cues: list = []
    for i, line in enumerate(script.lines, start=1):
        cues.append(
            SubtitleCue(
                index=i,
                start=line.start,
                end=line.end,
                text=line.text,
            )
        )
    return SubtitleTrack(cues=cues)
