---
name: shortvideo-pipeline
description: 把用户图片与介绍文字合成带中文配音的MP4，支持MeloTTS本地声音、环境检查与安装排错；也可生成脚本分镜，不自动发布。
license: MIT
---

# 短视频生产材料

在该包目录运行 `python -m shortvideo_pipeline.cli --help` 查看命令，`python -m shortvideo_pipeline.cli demo` 生成离线 mock 示例，`python -m unittest discover -s tests -v` 运行测试。

先明确选题、观众、平台、目标时长与事实素材。single 与 batch 接受简报并产出脚本、分镜、字幕和准备材料。对真实模型的调用需先配置所选 provider；凭据只从本地环境或 .env 读取，禁止提交真实 .env。

mock 结果仅用于结构演示，不能当成真实模型创意。本包提供简单图片视频渲染；版权审查、真实创意质量、平台验收与自动发布仍需另行完成。对外使用前检查事实、字幕时序与素材许可。

## 上手示例与当前限制

先读 [README.md](README.md) 的快速开始、输入输出和未完成项；可运行例子在 examples/，本次修订见 CHANGELOG.md。不要把合成演示或离线检查当成真实平台验证。

## 扩展能力

新增图片序列转竖屏 MP4，可接入本人提供的录音和 SRT 字幕；限定本地文件，新输出不覆盖旧文件。 使用前阅读 [README.md](README.md) 的“第二轮”命令和当前限制。不要把本地检查、人工声明或模拟响应解释为实时平台验证。

## 第三轮可执行能力

新增 Windows SAPI 中文/英文离线配音，以及文本→配音→图片视频的一键流程；画面时长自动延长以完整容纳语音，失败保留阶段状态。已实际生成中文配音并合成视频。

执行命令和当前限制见 [README.md](README.md) 的第三轮章节。

## 面向使用者的说明

解释用途、适用人群、下载和第一次运行时，读 [USER_GUIDE.md](USER_GUIDE.md)；需要中文对外介绍时参考 [INTRODUCTION.md](INTRODUCTION.md)，不要把介绍稿等同于已发布。

## 新版本地配音与代安装

用户要做“照片+介绍→有配音视频”时，优先读USER_GUIDE.md并走MeloTTS路线，不默认选旧Windows系统声音。安装/失败时读安装与排错.md；用户希望WorkBuddy协助时提供WORKBUDDY.md的任务，不声称已在该客户端跑通。

入口：`python scripts/start_here.py --install --demo`。它在项目.venv安装依赖并下载固定校验值的官方模型，生成不覆盖已有目录的示例。已安装时用.venv里的Python执行`--doctor`检查；READY只表示环境通过。

换成用户素材时使用scripts/make_melo_video.py；保留清单相对路径限制和新输出目录要求。画面时长自动覆盖配音长度；逐句多图需要另做分镜，不把基础轮播当作自动语义配图。完成后返回真实MP4路径、检查音轨与解码，再请用户试听。

## 用户已选晓晓女声

用户要视频同款或明确选D/晓晓时，先读[晓晓使用指南.md](晓晓使用指南.md)，用scripts/start_xiaoxiao.py安装并运行，不走MeloTTS/Windows路线。此模式将文本发往在线语音服务，需联网；遇到拒绝或验证停止处理，不绕过。脚本生成成功后返回MP4实际路径，并请用户试听。

## 多商品与反复改稿

用户有多个商品或反复改稿时，读[批量商品视频.md](批量商品视频.md)。先用plan_product_batch.py从授权商品文件夹生成清单并检查，再用batch_product_videos.py制作。每句要求至少两张内容不同的图片；按商品范围顺序分配，不声称自动识图选片。输出统一晓晓声音、标题和烧录字幕。

默认复用已验证的配音和片段缓存，未改任务跳过；修改内容形成新版本，保留旧成片。逐任务报告错误，语音服务失败后不对每个任务重复请求。查看批次HTML/CSV/JSON，返回真实MP4位置；已解码不等于已人工试听。
