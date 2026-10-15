"""Ollama Provider：本地大模型（默认 qwen3:8b），离线可用。

依赖：本地已启动 Ollama 服务且已拉取对应模型。
调用 /api/generate，format=json 强制 JSON 输出。
"""

from __future__ import annotations

import json
import urllib.request
from typing import Optional

from .base import LLMError, LLMProvider


def _sanitize(system: Optional[str]) -> Optional[str]:
    if not system:
        return system
    import re

    return re.sub(r"\[STEP:\w+\]", "", system).strip()


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def complete(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        if system:
            payload["system"] = _sanitize(system)
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status != 200:
                    raise LLMError(f"Ollama 返回非 200：{resp.status}")
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise LLMError(f"无法连接 Ollama（{self.base_url}）：{exc}") from exc
        text = body.get("response")
        if not text:
            raise LLMError("Ollama 返回为空")
        return text
