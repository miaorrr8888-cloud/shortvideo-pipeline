"""数据模型层：输入 Brief 与 9 步产物的结构化定义。

设计原则：
- 所有产物均为纯 dataclass，含 from_dict / to_dict，便于 JSON 序列化与测试。
- 时间相关字段由管线确定性计算（见 pipeline / output），不依赖 LLM 做数学。
- 任何缺失/非法字段在 from_dict 或 validate() 中显式报错，不静默填空。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# 输入：选题简报
# ---------------------------------------------------------------------------
@dataclass
class TopicBrief:
    """一条短视频选题简报（用户/上游输入）。"""

    title: str  # 选题方向，例如 "noon 代开店 VAT 合规痛点"
    platform: str = "douyin"  # douyin | xiaohongshu
    duration_target: int = 120  # 目标时长（秒）
    audience_hint: str = ""  # 目标人群提示，例如 "传统外贸老板"
    style: str = "record_style"  # record_style(纪录式商业分析) | ...
    pain_points: List[str] = field(default_factory=list)
    angle: str = ""  # 切入角度/核心观点
    language: str = "zh"
    brief_id: str = ""  # 可选业务 ID

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "platform": self.platform,
            "duration_target": self.duration_target,
            "audience_hint": self.audience_hint,
            "style": self.style,
            "pain_points": list(self.pain_points),
            "angle": self.angle,
            "language": self.language,
            "brief_id": self.brief_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TopicBrief":
        if not isinstance(d, dict):
            raise TypeError("TopicBrief.from_dict 需要 dict")
        if not isinstance(d.get("title"),str) or not d["title"].strip():
            raise ValueError("TopicBrief.title 不能为空")
        dt = d.get("duration_target", 120)
        if isinstance(dt,bool) or not isinstance(dt, int) or dt <= 0:
            raise ValueError("TopicBrief.duration_target 必须为正整数")
        pains=d.get('pain_points',[]) or []
        if not isinstance(pains,list) or not all(isinstance(x,str) for x in pains):
            raise ValueError('pain_points 必须是字符串数组')
        return cls(
            title=d["title"].strip(),
            platform=str(d.get("platform", "douyin")),
            duration_target=int(dt),
            audience_hint=str(d.get("audience_hint", "")),
            style=str(d.get("style", "record_style")),
            pain_points=list(d.get("pain_points", []) or []),
            angle=str(d.get("angle", "")),
            language=str(d.get("language", "zh")),
            brief_id=str(d.get("brief_id", "")),
        )


# ---------------------------------------------------------------------------
# 步骤 1：用户/受众分析
# ---------------------------------------------------------------------------
@dataclass
class AudienceProfile:
    description: str
    pain_points: List[str]
    desires: List[str]
    tone: str  # 沟通语气，例如 "直白、共情、不卖课"

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "pain_points": list(self.pain_points),
            "desires": list(self.desires),
            "tone": self.tone,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AudienceProfile":
        return cls(
            description=str(d.get("description", "")),
            pain_points=list(d.get("pain_points", []) or []),
            desires=list(d.get("desires", []) or []),
            tone=str(d.get("tone", "")),
        )


# ---------------------------------------------------------------------------
# 步骤 2：选题提炼
# ---------------------------------------------------------------------------
@dataclass
class TopicAnalysis:
    refined_topic: str
    angle: str
    why_it_works: str  # 为什么这个角度能拿完播/转化

    def to_dict(self) -> dict:
        return {
            "refined_topic": self.refined_topic,
            "angle": self.angle,
            "why_it_works": self.why_it_works,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TopicAnalysis":
        return cls(
            refined_topic=str(d.get("refined_topic", "")),
            angle=str(d.get("angle", "")),
            why_it_works=str(d.get("why_it_works", "")),
        )


# ---------------------------------------------------------------------------
# 步骤 3：开场 Hook
# ---------------------------------------------------------------------------
@dataclass
class Hook:
    text: str
    hook_type: str  # risk_warning | question | shocking | contrast
    rationale: str  # 为什么这个钩子有效

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "hook_type": self.hook_type,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Hook":
        return cls(
            text=str(d.get("text", "")),
            hook_type=str(d.get("hook_type", "")),
            rationale=str(d.get("rationale", "")),
        )


# ---------------------------------------------------------------------------
# 步骤 4：结构规划（确定性时间分配）
# ---------------------------------------------------------------------------
@dataclass
class StructureSection:
    key: str  # hook | pain | method | proof | cta
    title: str
    purpose: str
    weight: int  # 占比权重（整数，总和=100）
    seconds: int = 0  # 由管线按 target 计算填充

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "title": self.title,
            "purpose": self.purpose,
            "weight": self.weight,
            "seconds": self.seconds,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StructureSection":
        return cls(
            key=str(d.get("key", "")),
            title=str(d.get("title", "")),
            purpose=str(d.get("purpose", "")),
            weight=int(d.get("weight", 0)),
            seconds=int(d.get("seconds", 0)),
        )


@dataclass
class StructurePlan:
    sections: List[StructureSection]
    total_seconds: int = 0

    def to_dict(self) -> dict:
        return {
            "sections": [s.to_dict() for s in self.sections],
            "total_seconds": self.total_seconds,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StructurePlan":
        return cls(
            sections=[StructureSection.from_dict(s) for s in d.get("sections", [])],
            total_seconds=int(d.get("total_seconds", 0)),
        )


# ---------------------------------------------------------------------------
# 步骤 5：口播稿（纯文本，提词器即用）
# ---------------------------------------------------------------------------
@dataclass
class ScriptLine:
    index: int
    section: str  # 对应 structure key
    text: str
    start: float = 0.0  # 由管线按时长计算
    end: float = 0.0

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "section": self.section,
            "text": self.text,
            "start": round(self.start, 2),
            "end": round(self.end, 2),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ScriptLine":
        return cls(
            index=int(d.get("index", 0)),
            section=str(d.get("section", "")),
            text=str(d.get("text", "")),
            start=float(d.get("start", 0.0)),
            end=float(d.get("end", 0.0)),
        )


@dataclass
class Script:
    lines: List[ScriptLine]
    estimated_seconds: int = 0

    def pure_text(self) -> str:
        """提词器/剪辑软件直接可用的纯口播文本。"""
        return "\n".join(line.text for line in self.lines if line.text.strip())

    def to_dict(self) -> dict:
        return {
            "lines": [l.to_dict() for l in self.lines],
            "estimated_seconds": self.estimated_seconds,
            "pure_text": self.pure_text(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Script":
        return cls(
            lines=[ScriptLine.from_dict(l) for l in d.get("lines", [])],
            estimated_seconds=int(d.get("estimated_seconds", 0)),
        )


# ---------------------------------------------------------------------------
# 步骤 6：分镜表
# ---------------------------------------------------------------------------
@dataclass
class Shot:
    index: int
    section: str
    time_range: str  # "00:00-00:08"
    visual: str  # 画面描述
    camera: str  # 运镜/景别
    narration_ref: str  # 对应口播（节选）

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "section": self.section,
            "time_range": self.time_range,
            "visual": self.visual,
            "camera": self.camera,
            "narration_ref": self.narration_ref,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Shot":
        return cls(
            index=int(d.get("index", 0)),
            section=str(d.get("section", "")),
            time_range=str(d.get("time_range", "")),
            visual=str(d.get("visual", "")),
            camera=str(d.get("camera", "")),
            narration_ref=str(d.get("narration_ref", "")),
        )


@dataclass
class Storyboard:
    shots: List[Shot]

    def to_dict(self) -> dict:
        return {"shots": [s.to_dict() for s in self.shots]}

    @classmethod
    def from_dict(cls, d: dict) -> "Storyboard":
        return cls(shots=[Shot.from_dict(s) for s in d.get("shots", [])])


# ---------------------------------------------------------------------------
# 步骤 7：字幕（SRT 时序由管线计算）
# ---------------------------------------------------------------------------
@dataclass
class SubtitleCue:
    index: int
    start: float
    end: float
    text: str

    def srt_block(self) -> str:
        def fmt(t: float) -> str:
            h = int(t // 3600)
            m = int((t % 3600) // 60)
            s = int(t % 60)
            ms = int(round((t - int(t)) * 1000))
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        return f"{self.index}\n{fmt(self.start)} --> {fmt(self.end)}\n{self.text}\n"

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SubtitleCue":
        return cls(
            index=int(d.get("index", 0)),
            start=float(d.get("start", 0.0)),
            end=float(d.get("end", 0.0)),
            text=str(d.get("text", "")),
        )


@dataclass
class SubtitleTrack:
    cues: List[SubtitleCue]

    def to_srt(self) -> str:
        return "\n".join(c.srt_block() for c in self.cues)

    def to_dict(self) -> dict:
        return {"cues": [c.to_dict() for c in self.cues]}

    @classmethod
    def from_dict(cls, d: dict) -> "SubtitleTrack":
        return cls(cues=[SubtitleCue.from_dict(c) for c in d.get("cues", [])])


# ---------------------------------------------------------------------------
# 步骤 8：封面方案
# ---------------------------------------------------------------------------
@dataclass
class CoverSpec:
    title: str
    subtitle: str
    style: str
    color_scheme: str
    layout: str
    font_hint: str

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "style": self.style,
            "color_scheme": self.color_scheme,
            "layout": self.layout,
            "font_hint": self.font_hint,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CoverSpec":
        return cls(
            title=str(d.get("title", "")),
            subtitle=str(d.get("subtitle", "")),
            style=str(d.get("style", "")),
            color_scheme=str(d.get("color_scheme", "")),
            layout=str(d.get("layout", "")),
            font_hint=str(d.get("font_hint", "")),
        )


# ---------------------------------------------------------------------------
# 步骤 9：BGM 建议
# ---------------------------------------------------------------------------
@dataclass
class BgmSuggestion:
    mood: str
    genre: str
    reference: str  # 参考曲风/关键词
    cue_points: List[str]  # 关键节点配乐提示

    def to_dict(self) -> dict:
        return {
            "mood": self.mood,
            "genre": self.genre,
            "reference": self.reference,
            "cue_points": list(self.cue_points),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BgmSuggestion":
        return cls(
            mood=str(d.get("mood", "")),
            genre=str(d.get("genre", "")),
            reference=str(d.get("reference", "")),
            cue_points=list(d.get("cue_points", []) or []),
        )


# ---------------------------------------------------------------------------
# 步骤 9（续）：发布方案
# ---------------------------------------------------------------------------
@dataclass
class PublishPlan:
    platforms: List[str]
    best_time: str
    hashtags: List[str]
    caption: str

    def to_dict(self) -> dict:
        return {
            "platforms": list(self.platforms),
            "best_time": self.best_time,
            "hashtags": list(self.hashtags),
            "caption": self.caption,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PublishPlan":
        return cls(
            platforms=list(d.get("platforms", []) or []),
            best_time=str(d.get("best_time", "")),
            hashtags=list(d.get("hashtags", []) or []),
            caption=str(d.get("caption", "")),
        )


# ---------------------------------------------------------------------------
# 汇总包
# ---------------------------------------------------------------------------
@dataclass
class VideoPackage:
    brief: TopicBrief
    audience: Optional[AudienceProfile] = None
    topic: Optional[TopicAnalysis] = None
    hook: Optional[Hook] = None
    structure: Optional[StructurePlan] = None
    script: Optional[Script] = None
    storyboard: Optional[Storyboard] = None
    subtitle: Optional[SubtitleTrack] = None
    cover: Optional[CoverSpec] = None
    bgm: Optional[BgmSuggestion] = None
    publish: Optional[PublishPlan] = None
    slug: str = ""
    computed_duration: int = 0

    def to_dict(self) -> dict:
        return {
            "slug": self.slug,
            "computed_duration": self.computed_duration,
            "brief": self.brief.to_dict(),
            "audience": self.audience.to_dict() if self.audience else None,
            "topic": self.topic.to_dict() if self.topic else None,
            "hook": self.hook.to_dict() if self.hook else None,
            "structure": self.structure.to_dict() if self.structure else None,
            "script": self.script.to_dict() if self.script else None,
            "storyboard": self.storyboard.to_dict() if self.storyboard else None,
            "subtitle": self.subtitle.to_dict() if self.subtitle else None,
            "cover": self.cover.to_dict() if self.cover else None,
            "bgm": self.bgm.to_dict() if self.bgm else None,
            "publish": self.publish.to_dict() if self.publish else None,
        }
