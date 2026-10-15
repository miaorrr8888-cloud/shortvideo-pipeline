# 短视频生产材料流水线

[新手逐步使用指南](USER_GUIDE.md) · [用途与适用人群介绍](INTRODUCTION.md)

`shortvideo-pipeline` · 独立技能仓库 · MIT

适合：需要写口播稿、分镜和字幕的创作者、小商家

## 解决什么问题

输入选题、观众与时长，得到可以继续拍摄、录音和剪辑的文本生产包。

## 快速开始

Python 3.10+，离线 mock 只用标准库。真实模型另行配置；本次不测试或收费调用云端模型。

在本仓库根目录运行：

```sh
python -m shortvideo_pipeline.cli single --brief examples/brief.json --dry-run --out output
python -m shortvideo_pipeline.cli self-test
```

## 输入与输出

**输入**：examples/brief.json：title（非空字符串）、duration_target（正整数）、pain_points（字符串数组），其余字段见示例。

**输出**：output 下的新目录，含口播稿、Markdown 分镜、SRT 字幕、封面/BGM/发布建议及 JSON 元数据。mock 只演示结构。

## 本次完善

原有缺口：只有工程和基础示例，重复导出可能覆盖文件，dry-run 还能被 provider 参数覆盖。

已补：重复导出自动建立新目录；检查标题、时长和痛点字段；dry-run 始终走离线 mock；补正式简报示例。

## 当前限制

配音依赖 Windows 已安装的声音；Linux/macOS 仍需提供外部录音。受限运行环境可能无法初始化系统声音，不应修改安全策略来绕过。生成声音需要试听；静态图片视频不等于复杂动态剪辑或平台验收。

## 验证与使用注意

```sh
python -m unittest discover -s tests -v
```

测试覆盖被断言的离线行为，不等于真实平台、生产模型或业务效果验证。

示例数据和图片均为合成演示，不是真实客户、交易、销量或模型成绩。不要提交真实凭据和私有输入。

## 来源与工作记录

由 miaorrr8888-cloud 在 AI 辅助下积累和维护，来源与边界见 [PROVENANCE.md](PROVENANCE.md)，许可见 [LICENSE](LICENSE)。

[全部独立技能与阶段性工作记录](https://github.com/miaorrr8888-cloud/agent-skills-worklog)

## 第二轮：本地视频渲染

新增图片序列转竖屏 MP4，可接入本人提供的录音和 SRT 字幕；限定本地文件，新输出不覆盖旧文件。

在仓库根目录运行：

```sh
python -m pip install Pillow
python scripts/render_slideshow.py examples/slides/manifest.json demo.mp4 --subtitles examples/slides/captions.srt
# 接入自己的录音：追加 --audio narration.wav
# FFmpeg 未加入 PATH 时：追加 --ffmpeg /path/to/ffmpeg
```

新增工具的输入字段见脚本参数与 examples/。快照示例采用固定日期，过期后正常返回 HOLD；需要检查新采集的页面时填写真实带时区的采集时间，不要改日期伪装新证据。

## 接入依据

[FFmpeg 官方文档](https://ffmpeg.org/ffmpeg.html)。渲染以本地提供的音视频素材为输入，没有下载素材或发布操作。

## 第三轮：本地配音与一键成片

新增 Windows SAPI 中文/英文离线配音，以及文本→配音→图片视频的一键流程；画面时长自动延长以完整容纳语音，失败保留阶段状态。已实际生成中文配音并合成视频。

```sh
python -m pip install Pillow
python scripts/synthesize_voice.py examples/narration.txt narration.wav --language zh-CN
python scripts/make_narrated_video.py examples/slides/manifest.json examples/narration.txt narrated-output
# FFmpeg 未在 PATH：追加 --ffmpeg /path/to/ffmpeg
# 接入自己的字幕：追加 --subtitles captions.srt
```
