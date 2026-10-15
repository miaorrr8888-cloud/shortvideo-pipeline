"""步骤 5：口播稿（纯文本，提词器即用；起止时间确定性计算）。"""

from __future__ import annotations

from typing import Dict, List, Tuple

from ..models import Script, ScriptLine, TopicBrief
from ..llm.base import LLMProvider
from .base import call_json, compute_line_timings


def generate(brief: TopicBrief, ctx: Dict, provider: LLMProvider) -> Script:
    user = (
        f"选题方向：{brief.title}\n"
        f"目标时长：{brief.duration_target} 秒\n"
        f"风格：{brief.style}\n"
        "请按 5 段输出口播稿 JSON：sections 数组，每段含 "
        "key(hook|pain|method|proof|cta) 与 text(该段纯口播文字，口语化、无括号提示)。"
        "整体为可直接念的连贯文稿，禁止出现 '(镜头)' 之类导演备注。"
    )
    data = call_json(provider, "script", user)
    remote = data.get("sections", [])
    pairs: List[Tuple[str, str]] = []
    for s in remote:
        if isinstance(s, dict) and s.get("text"):
            pairs.append((str(s.get("key", "")), str(s["text"])))

    if not pairs:
        raise ValueError("脚本生成失败：模型未返回任何口播文本")

    texts = [p[1] for p in pairs]
    timings = compute_line_timings(texts, brief.duration_target)
    lines: List[ScriptLine] = []
    for i, ((section, text), (start, end)) in enumerate(zip(pairs, timings), start=1):
        lines.append(
            ScriptLine(index=i, section=section, text=text, start=start, end=end)
        )
    return Script(lines=lines, estimated_seconds=brief.duration_target)
