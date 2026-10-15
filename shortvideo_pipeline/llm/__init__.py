"""LLM Provider 包：工厂函数与统一导出。"""

from __future__ import annotations

from .base import LLMError, LLMParseError, LLMProvider, extract_json
from .mock import MockProvider
from .ollama import OllamaProvider
from .siliconflow import SiliconFlowProvider


def build_provider(settings) -> LLMProvider:
    """根据 Settings 构造对应 Provider。

    - mock：离线确定性夹具，用于测试 / dry-run。
    - ollama / siliconflow：真实模型，连接失败或鉴权缺失时显式抛错。
    """
    if settings.llm_provider == "mock":
        return MockProvider()
    if settings.llm_provider == "ollama":
        return OllamaProvider(settings.ollama_base_url, settings.ollama_model)
    if settings.llm_provider == "siliconflow":
        return SiliconFlowProvider(
            settings.siliconflow_api_key,
            settings.siliconflow_model,
            settings.siliconflow_base_url,
        )
    raise LLMError(f"未知 provider: {settings.llm_provider}")


__all__ = [
    "LLMProvider",
    "LLMError",
    "LLMParseError",
    "extract_json",
    "MockProvider",
    "OllamaProvider",
    "SiliconFlowProvider",
    "build_provider",
]
