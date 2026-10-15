"""步骤 9b：发布方案。"""

from __future__ import annotations

from typing import Dict, List

from ..models import Hook, PublishPlan, TopicAnalysis, TopicBrief
from ..llm.base import LLMProvider
from .base import call_json


def generate(brief: TopicBrief, ctx: Dict, provider: LLMProvider) -> PublishPlan:
    topic: TopicAnalysis = ctx.get("topic")
    hook: Hook = ctx.get("hook")
    platforms: List[str] = [brief.platform]
    if "xiaohongshu" not in platforms:
        platforms.append("xiaohongshu")
    user = (
        f"选题方向：{brief.title}\n"
        f"精炼主题：{topic.refined_topic if topic else brief.title}\n"
        f"开场钩子：{hook.text if hook else ''}\n"
        f"主投平台：{brief.platform}\n"
        "请输出发布方案 JSON：best_time(建议发布时段), "
        "hashtags(数组), caption(文案)。禁止刷量、禁止诱导分享等违规表述。"
    )
    data = call_json(provider, "publish", user)
    plan = PublishPlan.from_dict(data)
    if not plan.platforms:
        plan.platforms = platforms
    return plan
