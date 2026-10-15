import json
import os
import tempfile
import unittest

from shortvideo_pipeline.llm.mock import MockProvider
from shortvideo_pipeline.models import TopicBrief
from shortvideo_pipeline.output import write_package
from shortvideo_pipeline.pipeline import Pipeline, slugify


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = Pipeline(MockProvider())

    def test_full_run_all_artifacts(self):
        brief = TopicBrief.from_dict(
            {"title": "自检选题", "duration_target": 90, "platform": "douyin"}
        )
        pkg = self.pipeline.run(brief)
        for attr in (
            "audience",
            "topic",
            "hook",
            "structure",
            "script",
            "storyboard",
            "subtitle",
            "cover",
            "bgm",
            "publish",
        ):
            self.assertIsNotNone(getattr(pkg, attr), attr)

    def test_duration_allocation_exact(self):
        brief = TopicBrief.from_dict({"title": "时长校验", "duration_target": 137})
        pkg = self.pipeline.run(brief)
        self.assertEqual(pkg.computed_duration, 137)
        self.assertEqual(sum(s.seconds for s in pkg.structure.sections), 137)

    def test_script_end_aligned(self):
        brief = TopicBrief.from_dict({"title": "时间对齐", "duration_target": 120})
        pkg = self.pipeline.run(brief)
        self.assertAlmostEqual(pkg.script.lines[-1].end, 120, places=1)
        # 每行起点递增
        starts = [l.start for l in pkg.script.lines]
        self.assertEqual(starts, sorted(starts))

    def test_json_serializable(self):
        brief = TopicBrief.from_dict({"title": "序列化", "duration_target": 100})
        pkg = self.pipeline.run(brief)
        text = json.dumps(pkg.to_dict(), ensure_ascii=False)
        self.assertIn("slug", text)  # 顶层键存在
        self.assertIn("script", text)
        # 重新解析不抛错
        json.loads(text)

    def test_slug_format(self):
        s = slugify("noon 开店 VAT 合规!")
        self.assertTrue(s)  # 非空
        self.assertIn("noon", s)
        self.assertIn("开店", s)
        self.assertIn("VAT", s)


class TestOutput(unittest.TestCase):
    def test_write_package_naming(self):
        pipeline = Pipeline(MockProvider())
        brief = TopicBrief.from_dict(
            {"title": "命名规则测试", "duration_target": 110, "platform": "douyin"}
        )
        pkg = pipeline.run(brief)
        with tempfile.TemporaryDirectory() as tmp:
            folder = write_package(pkg, tmp)
            self.assertTrue(os.path.basename(folder).startswith("110s_"))
            files = os.listdir(folder)
            # 按时长命名的关键文件都在
            self.assertIn("口播稿_110s.txt", files)
            self.assertIn("分镜_110s.md", files)
            self.assertIn("字幕_110s.srt", files)
            self.assertIn("封面方案_110s.md", files)
            self.assertIn("BGM_110s.md", files)
            self.assertIn("发布方案_110s.md", files)
            self.assertIn("metadata_110s.json", files)
            self.assertIn("README_110s.md", files)
            # 口播稿非空且为纯文本
            with open(os.path.join(folder, "口播稿_110s.txt"), encoding="utf-8") as fh:
                self.assertTrue(fh.read().strip())


if __name__ == "__main__":
    unittest.main()
