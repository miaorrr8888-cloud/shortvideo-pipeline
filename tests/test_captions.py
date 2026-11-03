"""字幕折行回归测试。

背景：旧实现按 13 字硬切后逐块轮流显示，一句 16 字会被切成
「前 13 字 3 秒 + 剩 2 字 0.46 秒」，长句碎成十几个闪块。
这组测试锁住「同屏折行、不留孤字、不碎屏」这三件事。
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import batch_product_videos as pipeline

NL = chr(92) + "N"  # ASS 的换行标记


def rows_of(screen):
    return screen.split(NL)


class CaptionLayout(unittest.TestCase):
    def test_short_sentence_stays_one_line(self):
        self.assertEqual(pipeline.caption_screens("短句。"), ["短句。"])

    def test_medium_sentence_wraps_in_one_screen(self):
        """16 字的一句话应当一屏两行，而不是分成两个先后闪现的碎片。"""
        screens = pipeline.caption_screens("这道演示只用了三张图和两句话。")
        self.assertEqual(len(screens), 1, screens)
        rows = rows_of(screens[0])
        self.assertEqual(len(rows), 2, rows)
        self.assertEqual("".join(rows), "这道演示只用了三张图和两句话。")

    def test_no_orphan_tail_row(self):
        """末行不能只剩一两个字（例如只有一个句号）。"""
        for text in (
            "这道演示只用了三张图和两句话。",
            "一二三四五六七八九十甲乙丙丁戊。",
            "这是一句特别长的文案" * 6 + "。",
        ):
            for screen in pipeline.caption_screens(text):
                rows = rows_of(screen)
                if len(rows) > 1:
                    self.assertGreaterEqual(len(rows[-1]), 4, (text, rows))

    def test_every_row_within_width_budget(self):
        """44px 字号下 720 宽最多约放 15 字，这里按 13 字折，留出描边余量。"""
        for screen in pipeline.caption_screens("这是一句特别长的文案" * 6 + "。"):
            for row in rows_of(screen):
                self.assertLessEqual(len(row), 13, row)

    def test_wraps_after_punctuation_not_mid_word(self):
        """「文案不出门」不能被拆成「文案不出 / 门」。"""
        screens = pipeline.caption_screens("配音在本机合成，文案不出门，也不产生费用。")
        self.assertEqual(len(screens), 1, screens)
        rows = rows_of(screens[0])
        self.assertEqual(rows, ["配音在本机合成，", "文案不出门，也不产生费用。"])

    def test_long_sentence_splits_into_screens_of_at_most_three_rows(self):
        screens = pipeline.caption_screens("这是一句特别长的文案" * 6 + "。")
        self.assertGreaterEqual(len(screens), 2)
        for screen in screens:
            self.assertLessEqual(len(rows_of(screen)), 3, screen)

    def test_no_text_is_lost_across_screens(self):
        text = "换成你自己的图片和介绍，就能做出同样的视频。这句话专门用来检查有没有掉字。"
        joined = "".join(r for s in pipeline.caption_screens(text) for r in rows_of(s))
        self.assertEqual(joined, text)

    def test_backslash_and_braces_escaped_but_newline_survives(self):
        """ass_escape 会把反斜杠换成全角，必须在插入换行标记之前做。"""
        screens = pipeline.caption_screens("含反斜杠 \\ 与 {花括号} 的说明文字。")
        self.assertTrue(any(NL in s for s in screens), screens)
        joined = "".join(screens)
        self.assertNotIn("\\ 与", joined)      # 原始反斜杠已被转义
        self.assertIn("｛", joined)             # 花括号转全角，避免被当成 ASS 标签
        self.assertIn(NL, joined)              # 换行标记仍是半角 \N

    def test_empty_text_is_safe(self):
        self.assertEqual(pipeline.caption_screens(""), [""])

    def test_captions_writes_one_event_per_screen_and_covers_duration(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "c.ass"
            pipeline.captions("这道演示只用了三张图和两句话。", 3.0, path)
            body = [l for l in path.read_text(encoding="utf-8").splitlines() if l.startswith("Dialogue:")]
            self.assertEqual(len(body), 1, body)
            self.assertIn(NL, body[0])
            self.assertIn("0:00:00.04", body[0])

    def test_no_screen_is_a_flash_fragment(self):
        """回归断言：任何一屏的可见字数都不能少到像「闪一下」。"""
        for text in ("这道演示只用了三张图和两句话。", "换成你自己的图片和介绍，就能做出同样的视频。"):
            for screen in pipeline.caption_screens(text):
                visible = screen.replace(NL, "")
                self.assertGreaterEqual(len(visible), 3, (text, screen))


if __name__ == "__main__":
    unittest.main()
