# 来源与范围

维护者：miaorrr8888-cloud。该技能来自维护者在 AI 辅助下积累并于 2026-10-15 整理的公开版本，现按用户要求拆为独立仓库。
许可见 LICENSE，保留已有署名。目录日期不代表独立证明开发时间。

本仓库只包含 shortvideo_pipeline。可用范围和限制见 SKILL.md 和 README.md；本地离线测试不等于真实平台或业务效果验证。

[阶段性工作记录](https://github.com/miaorrr8888-cloud/agent-skills-worklog/blob/main/WORK_LOG.md)

新增本地语音：MeloTTS（https://github.com/myshell-ai/MeloTTS，MIT），通过sherpa-onnx（https://github.com/k2-fsa/sherpa-onnx，Apache-2.0）运行官方vits-melo-tts-zh_en模型。第三方权重和运行库不打包进仓库，首次由安装器下载；各自许可保留。

晓晓在线配音通过edge-tts（https://github.com/rany2/edge-tts，LGPL-3.0）及websocket-client运行；调用该项目的请求/解析函数，遵循其许可证及服务自身条款。
