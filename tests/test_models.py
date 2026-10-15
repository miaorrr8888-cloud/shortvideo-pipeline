import unittest

from shortvideo_pipeline.models import (
    SubtitleCue,
    SubtitleTrack,
    TopicBrief,
)


class TestTopicBrief(unittest.TestCase):
    def test_empty_title_raises(self):
        with self.assertRaises(ValueError):
            TopicBrief.from_dict({"title": ""})

    def test_bad_duration_raises(self):
        with self.assertRaises(ValueError):
            TopicBrief.from_dict({"title": "x", "duration_target": -5})
        with self.assertRaises(ValueError):
            TopicBrief.from_dict({"title": "x", "duration_target": "abc"})

    def test_roundtrip(self):
        d = {
            "title": "noon开店",
            "platform": "douyin",
            "duration_target": 120,
            "pain_points": ["a", "b"],
        }
        b = TopicBrief.from_dict(d)
        self.assertEqual(b.to_dict()["title"], "noon开店")
        self.assertEqual(b.duration_target, 120)


class TestSubtitle(unittest.TestCase):
    def test_srt_format(self):
        track = SubtitleTrack(
            cues=[
                SubtitleCue(1, 0.0, 3.5, "第一句"),
                SubtitleCue(2, 3.5, 7.0, "第二句"),
            ]
        )
        srt = track.to_srt()
        self.assertIn("1\n00:00:00,000 --> 00:00:03,500\n第一句", srt)
        self.assertIn("2\n00:00:03,500 --> 00:00:07,000\n第二句", srt)


if __name__ == "__main__":
    unittest.main()
