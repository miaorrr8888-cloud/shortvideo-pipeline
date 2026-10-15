"""步骤 2：选题提炼。"""

from __future__ import annotations

from typing import Dict

from ..models import AudienceProfile, TopicAnalysis, TopicBrief
from ..llm.base import LLMProvider
from .base import call_json


def generate(brief: TopicBrief, ctx: Dict, provider: LLMProvider) -> TopicAnalysis:
    audience: AudienceProfile = ctx.get("audience")
    audience_note = audience.description if audience else "未分析"
    user = (
        f"选题方向：{brief.title}\n"
        f"切入角度/核心观点：{brief.angle or '未指定'}\n"
        f"受众画像：{audience_note}\n"
        "请输出选题提炼 JSON：refined_topic(精炼后的主题), "
        "angle(本片角度), why_it_works(为什么能拿完播/转化)。"
    )
    data = call_json(provider, "topic", user)
    return TopicAnalysis.from_dict(data)
