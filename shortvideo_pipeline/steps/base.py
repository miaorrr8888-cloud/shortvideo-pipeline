"""9 步内容生成模块的公共助手。

约定：
- 每个步骤在 system prompt 中嵌入 [STEP:xxx] 标记，MockProvider 据此返回对应夹具。
- 真实 Provider 会忽略该标记（已被 sanitize 去除）。
- 所有步骤返回结构化 dataclass；JSON 解析失败由 base.extract_json 显式抛出。
"""

from __future__ import annotations

from typing import Dict

from ..llm.base import LLMProvider

JSON_INSTRUCTION = (
    "你是一位资深商业短视频导演。请只输出一个 JSON 对象，"
    "不要输出任何解释性文字、不要使用 markdown 代码围栏。"
    "字段必须齐全，缺失字段用空字符串或空数组，禁止编造不存在的数据。"
)


def build_system(step: str, extra: str = "") -> str:
    return f"{JSON_INSTRUCTION}\n{extra}\n[STEP:{step}]"


def call_json(provider: LLMProvider, step: str, user: str, system_extra: str = "") -> Dict:
    """统一调用：构建 system、请求 JSON、返回 dict（解析失败向上抛）。"""
    system = build_system(step, system_extra)
    return provider.complete_json(user, system=system)


# ---------------------------------------------------------------------------
# 确定性时间计算（不依赖 LLM 做数学，保证时长一致、可测试）
# ---------------------------------------------------------------------------
def allocate_durations(total: int, weights) -> list:
    """按权重把 total 秒分配到各段，返回整数列表，总和严格等于 total。"""
    weights = [int(w) for w in weights]
    s = sum(weights)
    if s <= 0:
        raise ValueError("权重和必须为正")
    raw = [total * w / s for w in weights]
    floor = [int(x) for x in raw]
    remainder = total - sum(floor)
    # 把剩余秒数分给小数部分最大者，避免丢秒
    order = sorted(range(len(weights)), key=lambda i: raw[i] - floor[i], reverse=True)
    for i in range(remainder):
        floor[order[i % len(order)]] += 1
    return floor


def fmt_time(seconds: float) -> str:
    """秒 -> MM:SS。"""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def compute_line_timings(texts: list, total: int) -> list:
    """按字符长度把 total 秒分配给每行，返回 [(start, end), ...]，总和=total。"""
    n = len(texts)
    if n == 0:
        return []
    lens = [max(1, len(t)) for t in texts]
    total_chars = sum(lens)
    raw = [total * l / total_chars for l in lens]
    floor_start = []
    acc = 0.0
    for x in raw:
        floor_start.append(acc)
        acc += x
    # 末尾对齐 total
    ends = [floor_start[i] + raw[i] for i in range(n)]
    ends[-1] = float(total)
    # 用整数秒边界更稳妥：start/end 用浮点保留 2 位
    result = []
    for i in range(n):
        start = round(floor_start[i], 2)
        end = round(ends[i], 2)
        result.append((start, end))
    return result
