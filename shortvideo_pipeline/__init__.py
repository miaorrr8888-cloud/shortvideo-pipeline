"""短视频内容批量生成流水线。

给定一个选题简报，按 9 步框架（用户分析→选题→Hook→结构→口播稿→分镜→字幕→封面→发布）
产出完整生产包：口播稿、分镜、字幕 SRT、封面方案、BGM、发布方案、元数据 JSON。

LLM 调用可插拔：mock（测试/dry-run，离线）｜ ollama（本地）｜ siliconflow（云端）。
"""

from __future__ import annotations

from .config import Settings, load_settings
from .models import (
    AudienceProfile,
    BgmSuggestion,
    CoverSpec,
    Hook,
    PublishPlan,
    Script,
    Storyboard,
    StructurePlan,
    SubtitleTrack,
    TopicAnalysis,
    TopicBrief,
    VideoPackage,
)
from .pipeline import Pipeline, slugify
from .output import write_package

__version__ = "0.1.0"

__all__ = [
    "Settings",
    "load_settings",
    "AudienceProfile",
    "BgmSuggestion",
    "CoverSpec",
    "Hook",
    "PublishPlan",
    "Script",
    "Storyboard",
    "StructurePlan",
    "SubtitleTrack",
    "TopicAnalysis",
    "TopicBrief",
    "VideoPackage",
    "Pipeline",
    "slugify",
    "write_package",
    "__version__",
]
