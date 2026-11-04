---
name: shortvideo-pipeline
description: 给商品图片和一段介绍，一条命令做出带中文配音、烧录字幕的竖屏视频；支持批量、缓存复用和局部改稿，配音默认本机离线，联网配音必须先经用户同意。
license: MIT
version: 0.2.3
display_name: "批量商品配音视频"
agent_created: true

---
# 批量商品配音视频

用户要「照片 + 介绍 → 有配音的视频」时，只走这一个入口：

```sh
python scripts/make_video.py --check
python scripts/make_video.py --images "<图片文件夹>" --out "<输出目录>"
python scripts/make_video.py --products "<商品根目录>" --out "<输出目录>"
```

先跑 `--check`，把 PASS/FAIL 如实转述给用户，缺什么给可复制的修复命令。环境没过就不要开始渲染。

## 输入约定

- 单商品：一个文件夹放图片（png/jpg/jpeg/webp/bmp，≥2 张且画面不同）+ `介绍.txt`；也可用 `--text` 指定文案文件。
- 多商品：根目录下每个子文件夹各放 `介绍.txt` + ≥2 张图，一条命令批量出片。
- 文案按 `。！？` 切句，每句 ≤160 字、单条视频 ≤30 句；每句自动分配 2 张图。
- 字幕**整句同屏**显示：每行 ≤13 字、每屏最多 3 行，优先在逗号/句号后断行（不会把「不出门」拆成「不出 / 门」）；超过 39 字的长句才分成几屏依次显示。
- **配图是按文件名顺序轮流分配，不是按内容语义匹配**。要精确对图，用 `--dry-plan` 看计划再改。

## 配音与联网（必须按此口径向用户说明）

| 模式 | 命令 | 文本去向 | 费用 |
| --- | --- | --- | --- |
| 离线（默认） | `--voice offline` | 不出本机，Windows SAPI 本地合成 | 免费 |
| 在线 | `--voice online --allow-online-voice` | 发往微软 Edge 在线语音服务 `speech.platform.bing.com` 做 TTS；只发文字，不发图片；免账号免密钥 | 免费，但文本离开本机 |

- `--voice auto` 只会选离线；**环境不满足时不会偷偷改用在线配音**，会直接停下让你补依赖。
- 用户没明确同意时，`--voice online` 会被拒绝（退出码 3），并打印「发什么、发到哪、是否收费」。
- 本入口**不调用任何收费接口**，也不调用云端大模型；文案由用户提供，工具不做二次创作。
- 不要声称已验证在线配音：本机缺 `websocket-client`，且未获用户同意，所以在线路线**未验证**。

## 会产出什么

`<输出>/` 下：`START_HERE.html`（带播放器的结果页）、`batch-report.json` / `batch-report.csv`（逐任务状态、每句起止时间、`decode_passed`、`human_reviewed=false`）、`products/job_<id>/<指纹>/video.mp4`（720×1280、H.264、AAC、烧录字幕）。

成片默认 720×1280、25fps、字幕白色 44px 带黑描边、顶部标题。**已解码 ≠ 已人工试听**，交付时要说明这一点。

`batch-report.json` 的 `stats` 分两层：`speech_requests` / `clips_rendered` 是**本次进程新做的量**，`speech_calls` / `clips_resolved` 是**总调用量**（新做 + 复用缓存），`sentences_expected` 是应做的句数。若 `stats_consistent=false`，说明有句子复用了上一轮中断留下的缓存、或有任务未完成，此时看 `stats_note` 与 `jobs` 逐条核对，不要只引用 `stats`。（0.2.2 之前的版本在句数 ≥4 时只报新做量、容易被误读成漏做，现已修正。）

## 缓存与改稿

- 语音缓存 `speech-cache/`、片段缓存 `clip-cache/` 都是按内容指纹命名：同一句再次运行直接命中，不再请求配音。
- 整条任务没变 → `SKIPPED_UNCHANGED`；改一句 → 只重做那一个片段（`clips_rendered=1`），旧成片保留，新成片进新指纹目录。
- 缓存被写坏（上次崩溃留下半截文件）时，会把它改名成 `*.stale-<时间戳>` 留现场并自动重做一次，不会永久卡死；`stats.cache_repaired` 会记录次数。

## 环境依赖

Python 3.10+、Pillow、FFmpeg（PATH 里有，或装 `imageio-ffmpeg` 自带二进制）、Windows 字体 `C:/Windows/Fonts/msyhbd.ttc`、中文 SAPI 语音包（离线配音用）。
在线配音另需 `edge-tts` + `websocket-client`。

退出码：`0` 全部成功；`1` 有任务失败；`2` 输入错误（路径不存在、图片不足 2 张、两张图完全相同等）；`3` 需同意或补依赖。

## 其他路线（保留，按需选用）

- **MeloTTS 本地大模型配音**：`scripts/start_here.py --install --demo`，需下载约 167MB 模型。本机未安装该模型，**未验证**。
- **在线晓晓旧脚本**：`scripts/start_xiaoxiao.py` / `make_xiaoxiao_video.py`，等价于 `--voice online`，同样受同意约束。
- **纯文字生产（口播稿/分镜/字幕）**：`python -m shortvideo_pipeline.cli single --brief examples/brief.json --dry-run --out output`，mock provider 只演示结构。

细节见 [README.md](README.md)、[批量商品视频.md](批量商品视频.md)、[晓晓使用指南.md](晓晓使用指南.md)、[安装与排错.md](安装与排错.md)；用户视角的教程在 [USER_GUIDE.md](USER_GUIDE.md)。

## 不要做的事

不自动发布到任何平台；不替用户判断素材版权；不保证读音、断句和字幕时序正确；不把 mock 产物或合成示例当成真实业务效果；示例里的商品图和「视频」都是程序生成的合成素材。
