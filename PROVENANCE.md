# 来源与范围

维护者：miaorrr8888-cloud。该技能来自维护者在 AI 辅助下积累并于 2026-10-15 整理的公开版本，现按用户要求拆为独立仓库。
许可见 LICENSE，保留已有署名。目录日期不代表独立证明开发时间。

本仓库只包含 shortvideo_pipeline。可用范围和限制见 SKILL.md 和 README.md；本地离线测试不等于真实平台或业务效果验证。

[阶段性工作记录](https://github.com/miaorrr8888-cloud/agent-skills-worklog/blob/main/WORK_LOG.md)

新增本地语音：MeloTTS（https://github.com/myshell-ai/MeloTTS，MIT），通过sherpa-onnx（https://github.com/k2-fsa/sherpa-onnx，Apache-2.0）运行官方vits-melo-tts-zh_en模型。第三方权重和运行库不打包进仓库，首次由安装器下载；各自许可保留。

晓晓在线配音通过edge-tts（https://github.com/rany2/edge-tts，LGPL-3.0）及websocket-client运行；调用该项目的请求/解析函数，遵循其许可证及服务自身条款。

## 1.0.0 修订说明（衍生自上述公开版本）

- 原作者署名、MIT 许可证与项目链接原样保留，`LICENSE` 未改动。
- 本次新增 `scripts/make_video.py`、`tests/test_make_video.py`、`examples/演示商品`、`examples/示例输出`；修改 `scripts/batch_product_videos.py`（统一入口所需参数、音色标注、缓存自愈、字幕样式）、`scripts/synthesize_melo.py`（依赖导入顺序）；重写 SKILL / README / USER_GUIDE / CHANGELOG / INTRODUCTION。
- 示例图由 1254px PNG 压到 720px JPEG（同一张合成素材，仅缩小），示例成片为合成素材的真实运行产物。
- 本次修订于 2026-10-18 在 Windows 11 + Python 3.13 实测；在线配音与 MeloTTS 路线未验证。
