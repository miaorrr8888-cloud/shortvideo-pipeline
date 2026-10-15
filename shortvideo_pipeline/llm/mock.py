"""Mock Provider：确定性、离线、用于测试与 dry-run。

重要：
- 本 Provider 仅用于验证管线接线与产物结构，输出内容标注 [MOCK]，
  不构成任何真实创意/数据，禁止在真实发布链路中使用。
- 通过 system 中的 [STEP:xxx] 标记返回对应步骤的合法 JSON 结构。
"""

from __future__ import annotations

import json
import re
from typing import Optional

from .base import LLMProvider

_STEP_RE = re.compile(r"\[STEP:(\w+)\]")
_TITLE_RE = re.compile(r"选题方向[:：]\s*(.+)")
_SECTION_KEYS = ["hook", "pain", "method", "proof", "cta"]


def _title_from(prompt: str) -> str:
    m = _TITLE_RE.search(prompt or "")
    return m.group(1).strip() if m else "未命名选题"


class MockProvider(LLMProvider):
    name = "mock"

    def complete(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        step = "unknown"
        if system:
            m = _STEP_RE.search(system)
            if m:
                step = m.group(1)
        title = _title_from(prompt)
        return json.dumps(_fixture(step, title), ensure_ascii=False)

    def complete_json(self, prompt: str, system: Optional[str] = None, **kwargs) -> dict:
        return json.loads(self.complete(prompt, system=system, **kwargs))


def _fixture(step: str, title: str) -> dict:
    if step == "audience":
        return {
            "description": f"[MOCK] 关注「{title}」的传统外贸老板与转型跨境的创业者",
            "pain_points": ["开店门槛不清楚", "VAT 合规怕踩坑", "流程繁琐耗时"],
            "desires": ["低成本稳妥入驻", "合规不踩雷", "有人手把手带"],
            "tone": "直白、共情、不卖课",
        }
    if step == "topic":
        return {
            "refined_topic": f"[MOCK] {title}：用风险提醒切入的方法交付",
            "angle": "先讲踩坑风险，再给可落地步骤",
            "why_it_works": "[MOCK] 风险钩子拉停留，方法交付换信任",
        }
    if step == "hook":
        return {
            "text": f"[MOCK] 做{title}前，这 3 个坑先看清，不然钱白花。",
            "hook_type": "risk_warning",
            "rationale": "[MOCK] 风险前置，制造紧迫感与停留",
        }
    if step == "structure":
        return {
            "sections": [
                {"key": "hook", "title": "风险钩子", "purpose": "3 秒留人", "weight": 8},
                {"key": "pain", "title": "痛点共鸣", "purpose": "放大焦虑", "weight": 22},
                {"key": "method", "title": "方法交付", "purpose": "给步骤", "weight": 40},
                {"key": "proof", "title": "证据背书", "purpose": "增信", "weight": 15},
                {"key": "cta", "title": "行动号召", "purpose": "引导咨询", "weight": 15},
            ]
        }
    if step == "script":
        return {
            "sections": [
                {"key": "hook", "text": f"[MOCK] 想做{title}的朋友，先停一下，这三个坑绝大多数人都踩过。"},
                {"key": "pain", "text": "[MOCK] 第一，资料准备不齐直接被拒；第二，VAT 没搞清楚后期被罚；第三，平台规则看不懂白忙活。"},
                {"key": "method", "text": "[MOCK] 正确做法是：先核资质，再走合规开店流程，VAT 提前备案，步骤我整理在评论区。"},
                {"key": "proof", "text": "[MOCK] 我们已帮上百个商家稳妥落地，平均周期可控。"},
                {"key": "cta", "text": "[MOCK] 想少走弯路的，主页找我，发你一份开店清单。"},
            ]
        }
    if step == "storyboard":
        return {
            "shots": [
                {"section": "hook", "visual": "[MOCK] 主播正视镜头，背景简洁", "camera": "近景固定", "narration_ref": "风险钩子"},
                {"section": "pain", "visual": "[MOCK] 三张坑点字卡快切", "camera": "中景+字卡", "narration_ref": "痛点共鸣"},
                {"section": "method", "visual": "[MOCK] 步骤清单特写", "camera": "推镜", "narration_ref": "方法交付"},
                {"section": "proof", "visual": "[MOCK] 数据/案例截图", "camera": "画中画", "narration_ref": "证据背书"},
                {"section": "cta", "visual": "[MOCK] 主页指引箭头", "camera": "近景", "narration_ref": "行动号召"},
            ]
        }
    if step == "cover":
        return {
            "title": f"[MOCK] {title}",
            "subtitle": "3 个坑别踩",
            "style": "纪录式 / 大字标题",
            "color_scheme": "深底白字 + 警示红",
            "layout": "上标题下副标题，居中",
            "font_hint": "粗黑体，高对比",
        }
    if step == "bgm":
        return {
            "mood": "稳重、略紧张",
            "genre": "轻电子 / 低频铺底",
            "reference": "[MOCK] 商业解说类无歌词 BGM",
            "cue_points": ["开头 0-3s 轻入", "方法段渐强", "结尾收束"],
        }
    if step == "publish":
        return {
            "platforms": ["douyin", "xiaohongshu"],
            "best_time": "工作日 19:00-22:00 / 周末 10:00-12:00",
            "hashtags": ["跨境电商", "noon开店", "VAT合规"],
            "caption": "[MOCK] 收藏这份清单，开店少走弯路。",
        }
    # 未知步骤：返回最小合法对象，便于测试不崩
    return {"note": f"[MOCK] 未定义步骤 {step}", "ok": True}
