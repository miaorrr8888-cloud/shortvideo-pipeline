"""步骤 9a：BGM 建议。"""

from __future__ import annotations

from typing import Dict

from ..models import BgmSuggestion, StructurePlan, TopicAnalysis, TopicBrief
from ..llm.base import LLMProvider
from .base import call_json


def generate(brief: TopicBrief, ctx: Dict, provider: LLMProvider) -> BgmSuggestion:
    topic: TopicAnalysis = ctx.get("topic")
    plan: StructurePlan = ctx.get("structure")
    sections = " / ".join(s.title for s in plan.sections) if plan else ""
    user = (
        f"选题方向：{brief.title}\n"
        f"精炼主题：{topic.refined_topic if topic else brief.title}\n"
        f"段落结构：{sections}\n"
        "请输出 BGM 建议 JSON：mood(情绪), genre(曲风), "
        "reference(参考关键词), cue_points(数组，关键节点配乐提示)。"
    )
    data = call_json(provider, "bgm", user)
    return BgmSuggestion.from_dict(data)
