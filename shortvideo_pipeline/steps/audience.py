"""步骤 1：用户/受众分析。"""

from __future__ import annotations

from typing import Dict

from ..models import AudienceProfile, TopicBrief
from ..llm.base import LLMProvider
from .base import call_json


def generate(brief: TopicBrief, ctx: Dict, provider: LLMProvider) -> AudienceProfile:
    user = (
        f"选题方向：{brief.title}\n"
        f"目标人群提示：{brief.audience_hint or '未指定'}\n"
        f"已知痛点：{', '.join(brief.pain_points) if brief.pain_points else '未提供'}\n"
        f"平台：{brief.platform}\n"
        "请输出受众画像 JSON：description(一句话画像), "
        "pain_points(数组), desires(数组), tone(沟通语气)。"
    )
    data = call_json(provider, "audience", user)
    return AudienceProfile.from_dict(data)
