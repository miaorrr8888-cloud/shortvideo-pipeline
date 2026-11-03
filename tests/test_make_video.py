# -*- coding: utf-8 -*-
"""make_video.py 统一入口的回归测试：环境自检、配音同意闸门、任务构建、真实出片与缓存自愈。"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import make_video  # noqa: E402


def have_pillow():
    try:
        import PIL  # noqa: F401
        return True
    except Exception:
        return False


def make_images(folder: Path, colors=((210, 220, 235), (235, 225, 210))):
    from PIL import Image
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for i, c in enumerate(colors):
        p = folder / f"0{i + 1}-图.jpg"
        Image.new("RGB", (400, 500), c).save(p, quality=90)
        out.append(p)
    return out


class Unit(unittest.TestCase):
    def test_doctor_reports_structure_and_is_honest(self):
        env = make_video.doctor(verbose=False)
        names = [c["check"] for c in env["checks"]]
        self.assertIn("FFmpeg", names)
        self.assertIn("Pillow", names)
        self.assertIsInstance(env["ready_offline"], bool)
        self.assertIsInstance(env["ready_online"], bool)
        self.assertIn("不代表", env["notice"])

    def test_split_sentences(self):
        s = make_video.split_sentences("第一句。第二句！第三句？")
        self.assertEqual(s, ["第一句。", "第二句！", "第三句？"])
        long = make_video.split_sentences("啊" * 400)
        self.assertTrue(all(len(x) <= 160 for x in long))

    def test_split_sentences_limits(self):
        with self.assertRaises(ValueError):
            make_video.split_sentences("   ")
        with self.assertRaisesRegex(ValueError, "上限"):
            make_video.split_sentences("。".join(["一"] * 40))

    @unittest.skipUnless(have_pillow(), "需要 Pillow")
    def test_assign_images_needs_two_distinct(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            one = make_images(d / "one", [(200, 200, 200)])
            with self.assertRaisesRegex(ValueError, "至少需要 2 张"):
                make_video.assign_images(["一句。"], one, d, "t", "x")
            same = make_images(d / "same", [(200, 200, 200)])
            shutil.copy2(same[0], d / "same" / "copy.jpg")
            with self.assertRaisesRegex(ValueError, "完全相同"):
                make_video.assign_images(["一句。"], sorted((d / "same").iterdir()), d, "t", "x")

    @unittest.skipUnless(have_pillow(), "需要 Pillow")
    def test_assign_images_round_robin(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            imgs = make_images(d, [(200, 0, 0), (0, 200, 0), (0, 0, 200)])
            job = make_video.assign_images(["一。", "二。", "三。"], imgs, d, "商品", "p1")
            self.assertEqual(len(job["sentences"]), 3)
            for row in job["sentences"]:
                self.assertEqual(len(row["images"]), 2)
                self.assertNotEqual(row["images"][0], row["images"][1])

    def test_online_voice_requires_consent(self):
        class A:
            voice = "online"
            allow_online_voice = False
            offline_voice = ""
        with self.assertRaises(make_video.Blocked) as ctx:
            make_video.resolve_voice(A(), {"ready_online": True})
        text = str(ctx.exception)
        self.assertIn("speech.platform.bing.com", text)
        self.assertIn("不会调用任何需要付费", text)

    def test_auto_voice_does_not_silently_go_online(self):
        class A:
            voice = "auto"
            allow_online_voice = False
            offline_voice = ""
        with self.assertRaisesRegex(make_video.Blocked, "环境未就绪"):
            make_video.resolve_voice(A(), {"ready_offline": False, "checks": [{"check": "Pillow", "ok": False}]})

    def test_offline_voice_is_local(self):
        class A:
            voice = "offline"
            allow_online_voice = False
            offline_voice = ""
        speaker, label, ext, net = make_video.resolve_voice(A(), {"ready_offline": True, "voice_offline": "Huihui"})
        self.assertTrue(callable(speaker))
        self.assertEqual(ext, ".wav")
        self.assertFalse(net)
        self.assertIn("SAPI", label)


class Entry(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "商品"
        self.out = self.tmp / "输出"
        self._doc = make_video.doctor
        make_video.doctor = lambda verbose=True: {
            "checks": [{"check": "fake", "ok": True, "detail": "", "fix": ""}],
            "ready_offline": True, "ready_online": False,
            "voice_offline": "Microsoft Huihui Desktop", "notice": "测试替身",
        }

    def tearDown(self):
        make_video.doctor = self._doc
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_missing_images_folder_exits_2(self):
        self.assertEqual(make_video.run(["--images", str(self.tmp / "没有"), "--out", str(self.out)]), 2)

    def test_missing_out_exits_2(self):
        self.assertEqual(make_video.run(["--images", str(self.src)]), 2)

    def test_both_modes_rejected(self):
        self.assertEqual(make_video.run(["--images", str(self.src), "--products", str(self.src),
                                         "--out", str(self.out)]), 2)

    @unittest.skipUnless(have_pillow(), "需要 Pillow")
    def test_single_image_folder_exits_2(self):
        make_images(self.src, [(210, 210, 210)])
        (self.src / "介绍.txt").write_text("一句话。", encoding="utf-8")
        self.assertEqual(make_video.run(["--images", str(self.src), "--out", str(self.out), "--voice", "offline"]), 2)

    def test_online_without_consent_exits_3(self):
        self.assertEqual(make_video.run(["--images", str(self.src), "--out", str(self.out), "--voice", "online"]), 3)

    @unittest.skipUnless(have_pillow(), "需要 Pillow")
    def test_dry_plan_writes_no_video(self):
        make_images(self.src, [(10, 20, 30), (30, 20, 10)])
        (self.src / "介绍.txt").write_text("第一句。第二句。", encoding="utf-8")
        code = make_video.run(["--images", str(self.src), "--out", str(self.out), "--dry-plan"])
        self.assertEqual(code, 0)
        self.assertFalse(self.out.exists(), "只出计划时不应创建输出目录")


@unittest.skipUnless(have_pillow(), "需要 Pillow")
class RealRender(unittest.TestCase):
    """真跑一遍离线配音 + FFmpeg 渲染；环境不满足时跳过，不伪造结果。"""

    @classmethod
    def setUpClass(cls):
        env = make_video.doctor(verbose=False)
        if not env["ready_offline"]:
            raise unittest.SkipTest("本机离线配音环境未就绪")

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "榨汁杯"
        self.out = self.tmp / "输出"
        make_images(self.src, [(215, 225, 240), (235, 225, 205), (200, 210, 200)])
        (self.src / "介绍.txt").write_text("第一句介绍产品。第二句讲用法。", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_render_then_reuse_then_edit_one_sentence(self):
        code = make_video.run(["--images", str(self.src), "--out", str(self.out), "--voice", "offline",
                               "--title", "测试杯"])
        self.assertEqual(code, 0)
        report = json.loads((self.out / "batch-report.json").read_text(encoding="utf-8"))
        job = report["jobs"][0]
        self.assertEqual(job["status"], "GENERATED_REVIEW_REQUIRED")
        self.assertIn("SAPI", job["voice"])
        video = self.out / job["video"]
        self.assertTrue(video.is_file() and video.stat().st_size > 20000)
        self.assertTrue(job["decode_passed"])
        self.assertFalse(job["human_reviewed"])

        # 一模一样再跑：应全部命中缓存，不再请求配音
        make_video.run(["--images", str(self.src), "--out", str(self.out), "--voice", "offline", "--title", "测试杯"])
        again = json.loads((self.out / "batch-report.json").read_text(encoding="utf-8"))
        self.assertEqual(again["jobs"][0]["status"], "SKIPPED_UNCHANGED")
        self.assertEqual(again["stats"]["speech_requests"], 0)

        # 改一句：只重做 1 个片段，旧成片保留
        (self.src / "介绍.txt").write_text("第一句改了。第二句讲用法。", encoding="utf-8")
        make_video.run(["--images", str(self.src), "--out", str(self.out), "--voice", "offline", "--title", "测试杯"])
        edited = json.loads((self.out / "batch-report.json").read_text(encoding="utf-8"))
        self.assertEqual(edited["stats"]["clips_rendered"], 1)
        self.assertEqual(edited["stats"]["clip_cache_hits"], 1)
        self.assertTrue(video.is_file(), "旧成片必须保留")

    def test_corrupted_clip_cache_is_repaired_not_fatal(self):
        make_video.run(["--images", str(self.src), "--out", str(self.out), "--voice", "offline", "--title", "测试杯"])
        report = json.loads((self.out / "batch-report.json").read_text(encoding="utf-8"))
        job = report["jobs"][0]
        result = self.out / job["video"]
        result = result.parent / "result.json"
        clip = sorted((self.out / "clip-cache").glob("*.mp4"))[0]
        clip.write_bytes(b"half-written-by-a-crash")
        result.unlink()  # 模拟上次崩溃：成片记录没了，片段缓存是半截
        code = make_video.run(["--images", str(self.src), "--out", str(self.out), "--voice", "offline", "--title", "测试杯"])
        self.assertEqual(code, 0)
        repaired = json.loads((self.out / "batch-report.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(repaired["stats"].get("cache_repaired", 0), 1)
        self.assertTrue(list((self.out / "clip-cache").glob("*.stale-*")), "坏缓存要留现场，不能静默删除")
        self.assertEqual(repaired["jobs"][0]["status"], "GENERATED_REVIEW_REQUIRED")


FONT = Path(r"C:\Windows\Fonts\msyhbd.ttc")


@unittest.skipUnless(have_pillow() and FONT.exists(), "需要 Pillow 与微软雅黑字体")
class TitleWrapping(unittest.TestCase):
    """回归：标题原来按固定 20 字折行，会把 registry-video-20261018 切成
    「registry-video-20261」+「018」，断在数字中间。"""

    def setUp(self):
        from PIL import Image, ImageDraw, ImageFont
        import batch_product_videos as bpv
        self.bpv = bpv
        self.draw = ImageDraw.Draw(Image.new("RGB", (720, 200), "white"))
        self.font = ImageFont.truetype(str(FONT), 32)

    def test_long_ascii_title_stays_on_one_line(self):
        lines = self.bpv.wrap_px(self.draw, "registry-video-20261018", self.font, 660)
        self.assertEqual(lines, ["registry-video-20261018"])

    def test_lines_never_exceed_max_width(self):
        for title in ("保温杯 316 不锈钢 双层真空 大容量", "registry-video-20261018-giftbox"):
            for line in self.bpv.wrap_px(self.draw, title, self.font, 660):
                self.assertLessEqual(self.draw.textlength(line, font=self.font), 660.5, line)

    def test_wraps_at_separator_not_inside_word(self):
        """溢出点紧跟分隔符（浪费 ≤12 字）时，断在分隔符后而不是切进单词。"""
        lines = self.bpv.wrap_px(self.draw, "aaaaaaaaaa-bbbbbbbbbb", self.font, 200)
        self.assertEqual(lines[0], "aaaaaaaaaa-")
        self.assertTrue(lines[1].startswith("b"), lines)

    def test_greedy_fill_keeps_lines_full(self):
        """放得下就继续填，不为了对齐分隔符而浪费整行空间。"""
        lines = self.bpv.wrap_px(self.draw, "a" * 20 + "-" + "b" * 20, self.font, 660)
        self.assertGreater(len(lines), 1)
        self.assertGreater(self.draw.textlength(lines[0], font=self.font), 600)


if __name__ == "__main__":
    unittest.main(verbosity=2)
