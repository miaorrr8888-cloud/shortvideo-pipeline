"""配置层：从环境变量 / .env 文件加载设置（零第三方依赖）。

安全约定：
- API key 仅从环境变量或 .env 读取，绝不硬编码。
- 提供 DEFAULTS，未设置时使用安全的本地默认值（mock provider）。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

DEFAULTS: Dict[str, str] = {
    "LLM_PROVIDER": "mock",  # mock | ollama | siliconflow
    "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
    "OLLAMA_MODEL": "qwen3:8b",
    "SILICONFLOW_BASE_URL": "https://api.siliconflow.cn/v1",
    "SILICONFLOW_MODEL": "Qwen/Qwen3-8B",
    "OUTPUT_DIR": "output",
    "DEFAULT_LANGUAGE": "zh",
}


def _load_dotenv(path: str = ".env") -> None:
    """极简 .env 解析：KEY=VALUE，跳过 # 注释与空行。不覆盖已存在的环境变量。"""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


@dataclass
class Settings:
    llm_provider: str
    ollama_base_url: str
    ollama_model: str
    siliconflow_base_url: str
    siliconflow_model: str
    siliconflow_api_key: str
    output_dir: str
    default_language: str
    dry_run: bool = False

    def validate(self) -> None:
        if self.llm_provider not in ("mock", "ollama", "siliconflow"):
            raise ValueError(f"不支持的 LLM_PROVIDER: {self.llm_provider}")
        if self.llm_provider == "siliconflow" and not self.siliconflow_api_key:
            raise ValueError(
                "LLM_PROVIDER=siliconflow 但未设置 SILICONFLOW_API_KEY；"
                "请在 .env 配置或通过环境变量传入，禁止硬编码。"
            )


def load_settings(env_file: Optional[str] = ".env", dry_run: bool = False) -> Settings:
    _load_dotenv(env_file or ".env")
    get = lambda k: os.environ.get(k, DEFAULTS[k])

    provider = "mock" if dry_run else get("LLM_PROVIDER")
    settings = Settings(
        llm_provider=provider,
        ollama_base_url=get("OLLAMA_BASE_URL"),
        ollama_model=get("OLLAMA_MODEL"),
        siliconflow_base_url=get("SILICONFLOW_BASE_URL"),
        siliconflow_model=get("SILICONFLOW_MODEL"),
        siliconflow_api_key=os.environ.get("SILICONFLOW_API_KEY", ""),
        output_dir=get("OUTPUT_DIR"),
        default_language=get("DEFAULT_LANGUAGE"),
        dry_run=dry_run,
    )
    settings.validate()
    return settings
