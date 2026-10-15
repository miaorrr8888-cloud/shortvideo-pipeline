---
name: shortvideo-pipeline
description: 生成短视频脚本、分镜、字幕及发布准备材料，支持离线 mock 演示；不渲染或自动发布视频。
license: MIT
---

# 短视频生产材料

在该包目录运行 `python -m shortvideo_pipeline.cli --help` 查看命令，`python -m shortvideo_pipeline.cli demo` 生成离线 mock 示例，`python -m unittest discover -s tests -v` 运行测试。

先明确选题、观众、平台、目标时长与事实素材。single 与 batch 接受简报并产出脚本、分镜、字幕和准备材料。对真实模型的调用需先配置所选 provider；凭据只从本地环境或 .env 读取，禁止提交真实 .env。

mock 结果仅用于结构演示，不能当成真实模型创意。成片渲染、版权审查、真实创意质量、平台验收与自动发布不包含在本包内。对外使用前检查事实、字幕时序与素材许可。

## 上手示例与当前限制

先读 [README.md](README.md) 的快速开始、输入输出和未完成项；可运行例子在 examples/，本次修订见 CHANGELOG.md。不要把合成演示或离线检查当成真实平台验证。

## 扩展能力

新增图片序列转竖屏 MP4，可接入本人提供的录音和 SRT 字幕；限定本地文件，新输出不覆盖旧文件。 使用前阅读 [README.md](README.md) 的“第二轮”命令和当前限制。不要把本地检查、人工声明或模拟响应解释为实时平台验证。
