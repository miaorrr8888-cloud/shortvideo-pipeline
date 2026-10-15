"""步骤 3：开场 Hook。"""

from __future__ import annotations

from typing import Dict

from ..models import Hook, TopicAnalysis, TopicBrief
from ..llm.base import LLMProvider
from .base import call_json


def generate(brief: TopicBrief, ctx: Dict, provider: LLMProvider) -> Hook:
    topic: TopicAnalysis = ctx.get("topic")
    topic_note = topic.refined_topic if topic else brief.title
    user = (
        f"选题方向：{brief.title}\n"
        f"精炼主题：{topic_note}\n"
        f"风格：{brief.style}\n"
        "请输出开场钩子 JSON：text(钩子原文，1-2 句), "
        "hook_type(risk_warning|question|shocking|contrast 之一), "
        "rationale(为什么有效)。禁止夸张承诺与违禁词。"
    )
    data = call_json(provider, "hook", user)
    return Hook.from_dict(data)
