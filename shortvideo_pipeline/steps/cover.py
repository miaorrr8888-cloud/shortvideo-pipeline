"""步骤 8：封面方案。"""

from __future__ import annotations

from typing import Dict

from ..models import CoverSpec, Hook, TopicAnalysis, TopicBrief
from ..llm.base import LLMProvider
from .base import call_json


def generate(brief: TopicBrief, ctx: Dict, provider: LLMProvider) -> CoverSpec:
    topic: TopicAnalysis = ctx.get("topic")
    hook: Hook = ctx.get("hook")
    user = (
        f"选题方向：{brief.title}\n"
        f"精炼主题：{topic.refined_topic if topic else brief.title}\n"
        f"开场钩子：{hook.text if hook else ''}\n"
        f"平台：{brief.platform}\n"
        "请输出封面方案 JSON：title(封面大标题), subtitle(副标题), "
        "style(风格), color_scheme(配色), layout(版式), font_hint(字体建议)。"
    )
    data = call_json(provider, "cover", user)
    return CoverSpec.from_dict(data)
