"""命令行入口。

子命令：
  single    生成单条视频生产包（可指定 --brief 文件或用 --title 直接建简报）
  batch     批量生成（读取含多条 brief 的 JSON 数组）
  demo      用 mock provider 跑一条样例（dry-run，不联网、不产生真实创意）
  self-test 管线自检：用 mock 跑通并断言产物结构（"批量前的测试闸门"）

示例：
  python -m shortvideo_pipeline.cli demo
  python -m shortvideo_pipeline.cli single --title "noon代开店VAT合规" --duration 120
  python -m shortvideo_pipeline.cli single --brief data/briefs_sample.json --index 0
  python -m shortvideo_pipeline.cli batch --briefs data/briefs_sample.json --out output
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List

from .config import load_settings
from .models import TopicBrief
from .output import write_package
from .pipeline import Pipeline


def _build_brief(args) -> TopicBrief:
    brief = None
    if getattr(args, "brief", None):
        with open(args.brief, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            idx = getattr(args, "index", 0) or 0
            data = data[idx]
        brief = TopicBrief.from_dict(data)
    if getattr(args, "title", None):
        brief = TopicBrief.from_dict(
            {
                "title": args.title,
                "platform": args.platform or "douyin",
                "duration_target": args.duration or 120,
                "audience_hint": args.audience or "",
                "angle": args.angle or "",
                "pain_points": args.pain.split("|") if args.pain else [],
            }
        )
    if brief is None:
        raise SystemExit("必须提供 --brief 文件或 --title")
    return brief


def _make_pipeline(args) -> Pipeline:
    settings = load_settings(env_file=args.env, dry_run=args.dry_run)
    if getattr(args, "provider", None) and not args.dry_run:
        settings.llm_provider = args.provider
        settings.validate()
    return Pipeline.from_settings(settings)


def _cmd_single(args) -> int:
    brief = _build_brief(args)
    pipeline = _make_pipeline(args)
    pkg = pipeline.run(brief)
    folder = write_package(pkg, args.out)
    print(f"[OK] 已生成：{folder}")
    print(f"     时长={pkg.computed_duration}s  provider={pipeline.settings.llm_provider}")
    return 0


def _cmd_batch(args) -> int:
    with open(args.briefs, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        data = [data]
    pipeline = _make_pipeline(args)
    ok = 0
    for i, item in enumerate(data):
        brief = TopicBrief.from_dict(item)
        try:
            pkg = pipeline.run(brief)
            folder = write_package(pkg, args.out)
            ok += 1
            print(f"[{i}] OK  {brief.title} -> {folder}")
        except Exception as exc:  # 单条失败不影响整体，但显式报错
            print(f"[{i}] FAIL {brief.title}: {exc}", file=sys.stderr)
    print(f"[DONE] 成功 {ok}/{len(data)}")
    return 0 if ok == len(data) else 1


def _cmd_demo(args) -> int:
    # demo 固定走 mock，安全、离线、不伪造真实创意
    settings = load_settings(env_file=args.env, dry_run=True)
    pipeline = Pipeline.from_settings(settings)
    brief = TopicBrief.from_dict(
        {
            "title": "noon代开店VAT合规3个坑",
            "platform": "douyin",
            "duration_target": 120,
            "audience_hint": "传统外贸老板",
            "pain_points": ["开店门槛", "VAT合规", "流程繁琐"],
        }
    )
    pkg = pipeline.run(brief)
    folder = write_package(pkg, args.out)
    print("[DEMO] 使用 mock provider（dry-run，未联网、未生成真实创意）")
    print(f"[OK] 样例已生成：{folder}")
    return 0


def _cmd_self_test(args) -> int:
    from .llm.mock import MockProvider

    pipeline = Pipeline(MockProvider())
    brief = TopicBrief.from_dict(
        {"title": "自检选题", "duration_target": 90, "platform": "douyin"}
    )
    pkg = pipeline.run(brief)
    # 断言：所有产物非空、时长分配正确、JSON 可序列化
    assert pkg.audience and pkg.topic and pkg.hook
    assert pkg.structure and pkg.script and pkg.storyboard
    assert pkg.subtitle and pkg.cover and pkg.bgm and pkg.publish
    assert pkg.computed_duration == 90, pkg.computed_duration
    assert sum(s.seconds for s in pkg.structure.sections) == 90
    assert abs(pkg.script.lines[-1].end - 90) < 0.01
    json.dumps(pkg.to_dict(), ensure_ascii=False)
    print("[SELF-TEST] 通过：9 步产物齐全，时长分配一致，JSON 可序列化")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="shortvideo_pipeline", description="短视频内容批量生成流水线")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("single", help="生成单条视频生产包")
    sp.add_argument("--brief", help="brief JSON 文件（单对象或数组）")
    sp.add_argument("--index", type=int, default=0, help="brief 为数组时取第几条")
    sp.add_argument("--title", help="直接指定选题方向（无需文件）")
    sp.add_argument("--platform", default="douyin")
    sp.add_argument("--duration", type=int, default=120)
    sp.add_argument("--audience", default="")
    sp.add_argument("--angle", default="")
    sp.add_argument("--pain", default="", help="痛点用 | 分隔")
    sp.add_argument("--out", default="output")
    sp.add_argument("--env", default=".env")
    sp.add_argument("--provider", default=None, help="覆盖 LLM_PROVIDER")
    sp.add_argument("--dry-run", action="store_true", help="强制 mock provider")
    sp.set_defaults(func=_cmd_single)

    bp = sub.add_parser("batch", help="批量生成")
    bp.add_argument("--briefs", required=True, help="含多条 brief 的 JSON 数组文件")
    bp.add_argument("--out", default="output")
    bp.add_argument("--env", default=".env")
    bp.add_argument("--provider", default=None)
    bp.add_argument("--dry-run", action="store_true")
    bp.set_defaults(func=_cmd_batch)

    dp = sub.add_parser("demo", help="mock 样例（dry-run）")
    dp.add_argument("--out", default="output")
    dp.add_argument("--env", default=".env")
    dp.set_defaults(func=_cmd_demo)

    st = sub.add_parser("self-test", help="管线自检（mock）")
    st.set_defaults(func=_cmd_self_test)
    return p


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
