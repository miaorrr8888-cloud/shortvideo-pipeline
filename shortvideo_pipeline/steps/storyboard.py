"""步骤 6：分镜表（镜头）。时间区间由结构段落窗口确定性推导。"""

from __future__ import annotations

from typing import Dict, List

from ..models import Script, Shot, Storyboard, StructurePlan, TopicBrief
from ..llm.base import LLMProvider
from .base import call_json, fmt_time
from .structure import DEFAULT_SECTIONS


def _section_windows(plan: StructurePlan) -> Dict[str, tuple]:
    windows = {}
    start = 0
    for sec in plan.sections:
        windows[sec.key] = (start, start + sec.seconds)
        start += sec.seconds
    return windows


def generate(brief: TopicBrief, ctx: Dict, provider: LLMProvider) -> Storyboard:
    plan: StructurePlan = ctx.get("structure")
    script: Script = ctx.get("script")
    if plan is None:
        raise ValueError("分镜步骤缺少 structure 上下文")

    user = (
        f"选题方向：{brief.title}\n"
        "请为 5 个段落各给 1 个分镜 JSON：shots 数组，每项含 "
        "section(hook|pain|method|proof|cta), visual(画面描述), "
        "camera(景别/运镜), narration_ref(对应口播节选)。"
    )
    data = call_json(provider, "storyboard", user)
    remote_shots = data.get("shots", []) or []

    # 按段落聚合，保持 DEFAULT 段落顺序
    by_section: Dict[str, List[dict]] = {k: [] for k, _, _, _ in DEFAULT_SECTIONS}
    for s in remote_shots:
        if isinstance(s, dict) and s.get("section") in by_section:
            by_section[s["section"]].append(s)

    windows = _section_windows(plan)
    shots: List[Shot] = []
    idx = 0
    for key, _, _, _ in DEFAULT_SECTIONS:
        section_shots = by_section.get(key) or [
            {"visual": f"{key} 段落默认画面", "camera": "中景", "narration_ref": key}
        ]
        start, end = windows[key]
        span = max(1, end - start)
        n = len(section_shots)
        for j, sh in enumerate(section_shots):
            idx += 1
            s0 = start + span * j / n
            s1 = start + span * (j + 1) / n
            shots.append(
                Shot(
                    index=idx,
                    section=key,
                    time_range=f"{fmt_time(s0)}-{fmt_time(s1)}",
                    visual=str(sh.get("visual", "")),
                    camera=str(sh.get("camera", "")),
                    narration_ref=str(sh.get("narration_ref", "")),
                )
            )
    return Storyboard(shots=shots)
