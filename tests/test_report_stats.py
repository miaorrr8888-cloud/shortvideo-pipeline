"""batch-report.json 的统计口径回归测试。

背景：2026-11-03 实跑发现 6 句文案的报告里写「配音 1 次、命中 1 次」，
与磁盘上 6 个 wav / 6 个 mp4 对不上。根因不是计数漏加，而是上一轮运行被中断后
缓存被复用，报告只描述了最后这个进程的行为。修法：把「本进程新做了什么」和
「整份报告应该有多少段」分开写，并给出 consistency 标记。
"""
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import batch_product_videos as pipeline  # noqa: E402


class StatsSummaryTests(unittest.TestCase):
    def test_reports_both_new_work_and_totals(self):
        state = {"speech_requests": 1, "speech_cache_hits": 5,
                 "clips_rendered": 1, "clip_cache_hits": 5}
        s = pipeline.stats_summary(state, 6)
        self.assertEqual(s["speech_calls"], 6)
        self.assertEqual(s["clips_resolved"], 6)
        self.assertEqual(s["sentences_expected"], 6)
        self.assertTrue(s["stats_consistent"])
        self.assertNotIn("stats_note", s)

    def test_flags_mismatch_instead_of_staying_silent(self):
        """片段数少于句数时必须显式标记，不能让人以为 6 句都做完了。"""
        state = {"speech_requests": 1, "speech_cache_hits": 1,
                 "clips_rendered": 2, "clip_cache_hits": 4}
        s = pipeline.stats_summary(state, 9)
        self.assertEqual(s["clips_resolved"], 6)
        self.assertFalse(s["stats_consistent"])
        self.assertIn("9", s["stats_note"])

    def test_does_not_mutate_input_state(self):
        state = {"speech_requests": 2, "speech_cache_hits": 0,
                 "clips_rendered": 2, "clip_cache_hits": 0}
        pipeline.stats_summary(state, 2)
        self.assertEqual(sorted(state), ["clip_cache_hits", "clips_rendered",
                                         "speech_cache_hits", "speech_requests"])

    def test_missing_counters_default_to_zero(self):
        """旧报告缺字段时不能抛 KeyError，否则读历史结果会崩。"""
        s = pipeline.stats_summary({}, 0)
        self.assertEqual((s["speech_calls"], s["clips_resolved"]), (0, 0))
        self.assertTrue(s["stats_consistent"])


class WarmRerunStatsTests(unittest.TestCase):
    """整批重跑时每个任务都 SKIPPED_UNCHANGED，统计不能因此报成故障。

    这是 2026-11-03 实跑复现的真实缺陷：第二遍跑完，成片 4.0 秒完好、
    磁盘上 2 段都在，报告却写 clips_resolved=0、stats_consistent=false，
    并提示「可能有任务未完成」。
    """

    def test_skipped_job_still_counts_as_resolved(self):
        rows = [{"id": "a", "status": "SKIPPED_UNCHANGED",
                 "sentence_timing": [{"sentence": 1}, {"sentence": 2}]}]
        s = pipeline.stats_summary({}, 2, rows)
        self.assertEqual(s["clips_resolved"], 2)
        self.assertTrue(s["stats_consistent"])
        self.assertEqual((s["jobs_skipped"], s["jobs_generated"], s["jobs_failed"]), (1, 0, 0))
        self.assertNotIn("stats_note", s)

    def test_failed_job_is_named_as_the_gap(self):
        rows = [{"id": "a", "status": "GENERATED_REVIEW_REQUIRED",
                 "sentence_timing": [{"sentence": 1}]},
                {"id": "b", "status": "FAILED"}]
        s = pipeline.stats_summary({}, 3, rows)
        self.assertEqual(s["clips_resolved"], 1)
        self.assertFalse(s["stats_consistent"])
        self.assertEqual(s["jobs_failed"], 1)
        self.assertIn("FAILED", s["stats_note"])

    def test_this_run_and_total_are_separate_fields(self):
        """本进程工作量与整体落地数必须是两个字段，不能合并成一个含糊数字。"""
        state = {"speech_requests": 0, "speech_cache_hits": 0,
                 "clips_rendered": 0, "clip_cache_hits": 0}
        rows = [{"id": "a", "status": "SKIPPED_UNCHANGED",
                 "sentence_timing": [{"sentence": 1}] * 6}]
        s = pipeline.stats_summary(state, 6, rows)
        self.assertEqual(s["clips_rendered_this_run"], 0)
        self.assertEqual(s["clips_resolved"], 6)
        self.assertTrue(s["stats_consistent"])

    def test_resolved_sentences_ignores_non_dict_rows(self):
        self.assertEqual(pipeline.resolved_sentences([None, "junk", {"id": "x"}]), 0)


class OrphanTempTests(unittest.TestCase):
    def test_removes_leftover_temp_dirs_only(self):
        """只清理中断残留的临时目录，缓存文件一个都不能动。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clips = root / "clip-cache"
            speech = root / "speech-cache"
            prod = root / "products" / "job_a" / "abc"
            for d in (clips, speech, prod):
                d.mkdir(parents=True)
            (clips / "keep.mp4").write_bytes(b"x")
            (clips / "clip-orphan123").mkdir()
            (speech / "speech-orphan456").mkdir()
            (prod / "concat-orphan789").mkdir()
            (prod / "assembled.mp4").write_bytes(b"x")

            removed = pipeline.clean_orphan_temps(root)

            self.assertEqual(removed, 3)
            self.assertTrue((clips / "keep.mp4").is_file())
            self.assertTrue((prod / "assembled.mp4").is_file())
            self.assertFalse((clips / "clip-orphan123").exists())
            self.assertFalse((speech / "speech-orphan456").exists())
            self.assertFalse((prod / "concat-orphan789").exists())

    def test_missing_folders_are_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(pipeline.clean_orphan_temps(Path(tmp)), 0)


if __name__ == "__main__":
    unittest.main()
