"""步骤 4：结构规划（时间分配由管线确定性计算）。"""

from __future__ import annotations

from typing import Dict, List

from ..models import StructurePlan, StructureSection, TopicBrief
from ..llm.base import LLMProvider
from .base import allocate_durations, call_json

# 固定段落骨架：key 不可变，weight 为默认占比（总和 100）
DEFAULT_SECTIONS = [
    ("hook", "风险钩子", "3 秒留人", 8),
    ("pain", "痛点共鸣", "放大焦虑", 22),
    ("method", "方法交付", "给可落地步骤", 40),
    ("proof", "证据背书", "增信防骗", 15),
    ("cta", "行动号召", "引导咨询", 15),
]


def generate(brief: TopicBrief, ctx: Dict, provider: LLMProvider) -> StructurePlan:
    user = (
        f"选题方向：{brief.title}\n"
        f"目标时长：{brief.duration_target} 秒\n"
        "请输出 5 段结构 JSON（sections 数组），每段含 "
        "key(hook|pain|method|proof|cta 之一), title, purpose, weight(整数占比)。"
        "5 段 weight 之和应为 100。"
    )
    data = call_json(provider, "structure", user)
    remote = {s.get("key"): s for s in data.get("sections", []) if isinstance(s, dict)}

    sections: List[StructureSection] = []
    weights = []
    for key, def_title, def_purpose, def_weight in DEFAULT_SECTIONS:
        r = remote.get(key, {})
        title = r.get("title") or def_title
        purpose = r.get("purpose") or def_purpose
        weight = int(r.get("weight") or def_weight)
        weights.append(weight)
        sections.append(StructureSection(key=key, title=title, purpose=purpose, weight=weight))

    seconds = allocate_durations(brief.duration_target, weights)
    for sec, secs in zip(sections, seconds):
        sec.seconds = secs

    total = sum(sec.seconds for sec in sections)
    return StructurePlan(sections=sections, total_seconds=total)
