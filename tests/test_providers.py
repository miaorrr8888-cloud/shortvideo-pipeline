import unittest

from shortvideo_pipeline.llm.base import LLMError, LLMParseError, extract_json
from shortvideo_pipeline.llm.mock import MockProvider
from shortvideo_pipeline.llm.ollama import OllamaProvider
from shortvideo_pipeline.llm.siliconflow import SiliconFlowProvider


class TestMockProvider(unittest.TestCase):
    def test_returns_valid_json_per_step(self):
        p = MockProvider()
        for step in ("audience", "topic", "hook", "structure", "script",
                    "storyboard", "cover", "bgm", "publish"):
            sys_prompt = f"指令\n[STEP:{step}]"
            data = p.complete_json("选题方向：测试选题", system=sys_prompt)
            self.assertIsInstance(data, dict)
            self.assertIn("ok", data) if step == "unknown" else None


class TestExtractJson(unittest.TestCase):
    def test_code_fence(self):
        text = '```json\n{"a": 1}\n```'
        self.assertEqual(extract_json(text), {"a": 1})

    def test_empty_raises(self):
        with self.assertRaises(LLMParseError):
            extract_json("")

    def test_garbage_raises(self):
        with self.assertRaises(LLMParseError):
            extract_json("没有任何 json 在这里")


class TestProviderErrors(unittest.TestCase):
    def test_siliconflow_requires_key(self):
        with self.assertRaises(LLMError):
            SiliconFlowProvider("", "m", "https://api.siliconflow.cn/v1")

    def test_ollama_bad_url_raises(self):
        # 连接一个必然不可达的地址，应在超时内以 LLMError 失败（不静默）
        p = OllamaProvider("http://127.0.0.1:9", "x", timeout=2.0)
        with self.assertRaises(LLMError):
            p.complete("x", system="[STEP:hook]")


if __name__ == "__main__":
    unittest.main()
