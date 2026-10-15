"""管线编排：按 9 步框架顺序执行，累积上下文，组装 VideoPackage。"""

from __future__ import annotations

import re
from typing import Dict, Optional

from .config import Settings
from .llm import LLMProvider, build_provider
from .models import TopicBrief, VideoPackage
from . import steps


def slugify(text: str, max_len: int = 24) -> str:
    """生成安全的文件夹/文件名片段：保留中文与字母数字，其余转 '-'。"""
    keep = re.sub(r"[^\w一-鿿]+", "-", text.strip())
    keep = re.sub(r"-+", "-", keep).strip("-")
    return keep[:max_len] or "untitled"


class Pipeline:
    def __init__(self, provider: LLMProvider, settings: Optional[Settings] = None):
        self.provider = provider
        self.settings = settings

    @classmethod
    def from_settings(cls, settings: Settings) -> "Pipeline":
        return cls(build_provider(settings), settings)

    def run(self, brief: TopicBrief) -> VideoPackage:
        ctx: Dict = {}
        pkg = VideoPackage(brief=brief)

        for name, fn in steps.STEP_ORDER:
            artifact = fn(brief, ctx, self.provider)
            ctx[name] = artifact
            setattr(pkg, name, artifact)

        # 时长以结构规划为准（确定性分配后总和严格等于 target）
        plan = pkg.structure
        pkg.computed_duration = plan.total_seconds if plan else brief.duration_target
        pkg.slug = f"{pkg.computed_duration}s_{slugify(brief.title)}"
        return pkg
