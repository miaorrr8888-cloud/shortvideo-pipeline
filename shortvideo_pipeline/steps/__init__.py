"""9 步内容生成模块包。"""

from __future__ import annotations

from .audience import generate as audience
from .topic import generate as topic
from .hook import generate as hook
from .structure import generate as structure
from .script import generate as script
from .storyboard import generate as storyboard
from .subtitle import generate as subtitle
from .cover import generate as cover
from .bgm import generate as bgm
from .publish import generate as publish

# 执行顺序即 9 步框架顺序
STEP_ORDER = [
    ("audience", audience),
    ("topic", topic),
    ("hook", hook),
    ("structure", structure),
    ("script", script),
    ("storyboard", storyboard),
    ("subtitle", subtitle),
    ("cover", cover),
    ("bgm", bgm),
    ("publish", publish),
]

__all__ = [
    "audience",
    "topic",
    "hook",
    "structure",
    "script",
    "storyboard",
    "subtitle",
    "cover",
    "bgm",
    "publish",
    "STEP_ORDER",
]
