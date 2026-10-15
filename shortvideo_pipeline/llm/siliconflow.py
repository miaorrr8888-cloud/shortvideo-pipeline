"""SiliconFlow Provider：通义千问等云端模型，OpenAI 兼容接口。

安全：api_key 必须通过参数/环境变量传入，禁止硬编码。
调用 {base}/chat/completions，response_format=json_object 强制 JSON。
"""

from __future__ import annotations

import json
import urllib.request
from typing import Optional

from .base import LLMError, LLMProvider
from .ollama import _sanitize


class SiliconFlowProvider(LLMProvider):
    name = "siliconflow"

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float = 120.0):
        if not api_key:
            raise LLMError("SiliconFlow 需要 api_key，请通过环境变量 SILICONFLOW_API_KEY 传入")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": _sanitize(system)})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status != 200:
                    raise LLMError(f"SiliconFlow 返回非 200：{resp.status}")
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise LLMError(f"无法连接 SiliconFlow：{exc}") from exc
        try:
            text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"SiliconFlow 返回结构异常：{exc}") from exc
        if not text:
            raise LLMError("SiliconFlow 返回为空")
        return text
