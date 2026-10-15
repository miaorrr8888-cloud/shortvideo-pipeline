"""LLM Provider 抽象层。

所有 Provider 实现统一的 complete() 接口。complete_json() 在 complete() 之上
做 JSON 提取与解析，失败时显式抛 LLMParseError（不静默填空、不伪造）。
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Optional


class LLMError(RuntimeError):
    """Provider 调用层面的错误（网络、鉴权、非 200 等）。"""


class LLMParseError(ValueError):
    """Provider 返回了文本但无法解析为目标 JSON。"""


_JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


def extract_json(text: str) -> dict:
    """从模型输出中提取第一个 JSON 对象。支持 ```json 代码块与裸 JSON。

    解析失败时抛出 LLMParseError，绝不返回空 dict 伪造成功。
    """
    if not text or not text.strip():
        raise LLMParseError("模型返回为空，无法解析 JSON")
    cleaned = text.strip()
    # 去掉可能的 ```json ... ``` 代码围栏
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned).strip()
    match = _JSON_OBJ_RE.search(cleaned)
    if not match:
        raise LLMParseError("模型输出中未找到 JSON 对象")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise LLMParseError(f"JSON 解析失败: {exc}") from exc


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def complete(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """返回模型文本输出。"""
        raise NotImplementedError

    def complete_json(self, prompt: str, system: Optional[str] = None, **kwargs) -> dict:
        """调用 complete 并解析为 dict。失败抛 LLMParseError。"""
        raw = self.complete(prompt, system=system, **kwargs)
        return extract_json(raw)
