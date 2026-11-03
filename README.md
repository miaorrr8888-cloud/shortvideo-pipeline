# 照片加文字，做成配音小视频

一个商品文件夹 + 一段介绍，一条命令出竖屏 MP4：带中文配音、烧录字幕、批量排队、改一句只重做那一段。

[从下载到打开成片：7步教程](USER_GUIDE.md) · [安装与排错](安装与排错.md) · [批量与改稿细节](批量商品视频.md) · [晓晓在线女声](晓晓使用指南.md) · [用途与适用人群介绍](INTRODUCTION.md)

`shortvideo-pipeline` · 独立技能仓库 · MIT

适合：需要给商品图配口播视频的小商家、电商运营、内容创作者

## 安装

**方式一：作为 WorkBuddy 技能安装（推荐）**

```sh
# 把整个目录放进技能目录，重开对话即可被识别
xcopy /E /I shortvideo-pipeline "%USERPROFILE%\.workbuddy\skills\shortvideo-pipeline"
```

**方式二：当作普通 Python 包用**

```sh
python -m pip install -r requirements.txt    # Pillow + imageio-ffmpeg（自带 ffmpeg 二进制）
python scripts/make_video.py --check         # 先自检，全 PASS 再出片
```

**环境要求（实测过的组合）**

| 项 | 要求 | 不满足会怎样 |
|---|---|---|
| Python | 3.10+（实测 3.13） | 启动即报语法错 |
| Pillow | >=10 | 合成画面失败 |
| ffmpeg | imageio-ffmpeg 自带，或系统 PATH | `--check` 报 FFmpeg 不可用 |
| 中文字体 | Windows 微软雅黑 `msyhbd.ttc` | 标题渲染抛错（其他系统需改字体路径） |
| 中文语音 | Windows SAPI 中文音色（如 Huihui） | 离线配音不可用，只能走在线 |
| 在线配音（可选） | `pip install edge-tts websocket-client` | 晓晓音色不可用，需加 `--allow-online-voice` |

## 快速开始（三条命令）

```sh
# 1. 先自检：缺什么会直接告诉你修什么
python scripts/make_video.py --check

# 2. 单商品：文件夹里放图片 + 介绍.txt
python scripts/make_video.py --images "D:\素材\榨汁杯" --out "D:\成片\榨汁杯"

# 3. 多商品：根目录下每个子文件夹各放 介绍.txt + ≥2 张图
python scripts/make_video.py --products "D:\素材\全部商品" --out "D:\成片\批次001"
```

跑完打开 `<输出>/START_HERE.html`，里面直接能播放每条成片。

> 示例素材与示例成片都在 `examples/`：`examples/演示商品` 可直接跑，`examples/示例输出` 是它的真实运行结果。

## 输入与输出

**输入**：图片（png/jpg/jpeg/webp/bmp，每句至少 2 张且画面真的不同）+ 介绍文案（`介绍.txt` 或 `--text`）。文案按 `。！？` 切句，每句 ≤160 字、单条 ≤30 句。

**输出**：

| 文件 | 内容 |
| --- | --- |
| `products/job_<id>/<指纹>/video.mp4` | 720×1280、H.264 + AAC、烧录字幕的成片 |
| `START_HERE.html` | 结果页，带播放器与下载链接 |
| `batch-report.json` / `.csv` | 逐任务状态、每句起止时间、`decode_passed`、`human_reviewed=false` |
| `speech-cache/` `clip-cache/` | 配音与片段缓存，按内容指纹命名 |

## 配音：默认离线，联网要先问你

| 模式 | 命令 | 文字去向 | 费用 |
| --- | --- | --- | --- |
| 离线（默认） | `--voice offline` | 留在本机，Windows SAPI 合成 | 免费 |
| 在线 | `--voice online --allow-online-voice` | 发往微软 Edge 在线语音服务 `speech.platform.bing.com`（只发文字，不发图片） | 免费，但文本离开本机 |

- 不给 `--allow-online-voice` 就选在线，会被直接拒绝（退出码 3），并说明发什么、发到哪、是否收费。
- `--voice auto` 只选离线；环境不满足时停下让你补依赖，**不会偷偷切成联网配音**。
- 本工具不调用任何收费接口、不调用云端大模型；文案由你提供。

## 批量、缓存与局部改稿

- 同一句话再跑：命中语音缓存，不再请求合成。
- 整条没改：`SKIPPED_UNCHANGED`，不会重做。
- 只改一句：只重做那一个片段（`clips_rendered=1`），旧成片保留，新成片进新指纹目录。
- 缓存被写坏（断电、上次崩溃留下半截文件）：自动改名成 `*.stale-<时间戳>` 留现场后重做一次，不会永久卡住。

## 参数

| 参数 | 说明 |
| --- | --- |
| `--images` / `--products` | 二选一：单个商品文件夹 / 商品根目录 |
| `--out` | 输出目录（新建，或本工具创建过的目录） |
| `--text` | 文案文件；不给则读文件夹里的 `介绍.txt` |
| `--title` | 视频顶部标题，默认取文件夹名 |
| `--voice` | `auto` / `offline` / `online` |
| `--allow-online-voice` | 同意把文案文字发往微软在线语音 |
| `--offline-voice` | 指定本机 SAPI 音色全名 |
| `--pace` | 语速倍率 1.0–1.5，默认 1.2 |
| `--dry-plan` | 只打印分句与配图计划，不渲染 |

退出码：`0` 全成功；`1` 有任务失败；`2` 输入错误；`3` 需同意或补依赖。

## 本次完善（1.0.0）

原有缺口：入口分散（批量脚本要手写 manifest、还要自己传 `--ffmpeg`），没有环境自检，联网配音没有知情同意闸门，音色被硬编码成晓晓（离线配音也写成晓晓，报告会误导），缓存半截文件会让输出目录永久失败。

已补：

1. **统一入口** `scripts/make_video.py`：`--check` 自检 + 单商品 + 多商品批量，自动定位 FFmpeg（PATH 找不到时用 `imageio-ffmpeg` 自带二进制）。
2. **配音知情同意**：在线配音必须显式 `--allow-online-voice`，否则拒绝并说明数据去向；`auto` 不会偷偷联网。
3. **音色如实标注**：报告、缓存指纹、结果页记录真实音色（离线 = Windows SAPI + 具体音色名），不再一律写晓晓。
4. **缓存自愈**：语音/片段/成片任一环节残留半截文件，改名 `*.stale-*` 留现场后重做，不再永久 FAILED。
5. **字幕可读性**：字号 36→44、每行 16→13 字、改为白字黑描边（原来是半透明灰底），浅色背景上也能看清。
6. **离线配音不再依赖 edge-tts**：只在真要走在线时才导入，缺依赖不影响离线出片。
7. **MeloTTS 报错归因修正**：先校验输入再导入依赖，缺依赖时报「缺依赖」而不是把参数错误误报成别的问题。
8. **示例瘦身**：示例图 1254px PNG（3.8MB）→ 720px JPEG，安装包能压进 3MB 以内。

## 适用用户

**适合：**

- 抖音 / 视频号 / 小红书上做商品带货，需要按 SKU 批量出竖屏口播视频的人；
- 手上只有供应商白底图和一段卖点文案，没有剪辑能力、也不想学剪辑的人；
- 在意文案不外传的人——默认走本机离线配音，文字不出本机。

**不适合：**

- 需要真人出镜、剧情拍摄的账号（本工具只做图片 + 配音 + 烧录字幕的图文视频）；
- 追求一键成片、不愿核对读音和字幕错字的人——工具明确要求人工复核后才发布；
- 非 Windows 环境且不愿改字体与语音配置的人（Linux/macOS 未实测）。

## 当前限制

- 模板固定 720×1280、25fps，字体硬依赖 Windows `msyhbd.ttc`；换尺寸/字体属于改造，未提供开关。
- 配图按文件名顺序轮流分配，**不是按画面内容语义匹配**；要精确对图用 `--dry-plan` 核对。
- 不给视频封面帧单独导出，标题只显示在画面顶部。
- 读音与断句由语音引擎决定，专有名词、型号、数字容易读错，必须人工试听。
- 在线配音（含晓晓）**未验证**：本机缺 `websocket-client`，且未取得用户同意，没有发起过联网请求。
- MeloTTS 路线**未验证**：模型未下载（约 167MB），本机未安装。
- macOS / Linux 未验证：离线配音依赖 Windows SAPI，模板依赖 Windows 字体。
- `python -m shortvideo_pipeline.cli` 的纯文字生产（口播稿/分镜/字幕）仍是 mock provider，只演示结构，不是真实模型创意。

## 验证与使用注意

```sh
python -m unittest discover -s tests -v
```

56 项测试，其中新增 16 项覆盖：环境自检结构、分句与配图分配、在线配音同意闸门、`auto` 不偷偷联网、缺文件夹/缺 `--out`/单图/两种模式同用、`--dry-plan` 不产出、真实离线出片 + 重跑命中缓存 + 改一句只重做一段、坏缓存自愈。

测试只覆盖可断言的离线行为，不等于平台验收或业务效果；`examples/示例输出` 是真实运行产物（合成素材）。

## 来源与工作记录

由 miaorrr8888-cloud 在 AI 辅助下积累和维护，来源与边界见 [PROVENANCE.md](PROVENANCE.md)，许可见 [LICENSE](LICENSE)。本版在其公开版本基础上扩展了统一入口与配音同意机制，署名与许可证保留不变。

[全部独立技能与阶段性工作记录](https://github.com/miaorrr8888-cloud/agent-skills-worklog)

## 其他路线（保留）

```sh
# 文字生产（口播稿/分镜/字幕，mock）
python -m shortvideo_pipeline.cli single --brief examples/brief.json --dry-run --out output

# 图片序列 → MP4（可接自己的录音和 SRT）
python scripts/render_slideshow.py examples/slides/manifest.json demo.mp4 --subtitles examples/slides/captions.srt

# 旧批量入口（手写 jobs.json）
python scripts/batch_product_videos.py examples/batch-products/jobs.json out-batch --ffmpeg <ffmpeg路径>

# MeloTTS 本地大模型配音（需下载约 167MB 模型，本机未验证）
python scripts/start_here.py --install --demo
```

[FFmpeg 官方文档](https://ffmpeg.org/ffmpeg.html)。渲染只以本地素材为输入，不下载素材、不发布。

## 运行环境

| 项 | 状态 |
|---|---|
| Windows 11 + Python 3.12 / 3.13 | ✅ 实测通过 |
| Linux / macOS | ⚠️ **未实测**。代码用 `pathlib`，无硬编码分隔符，理论上可跑，但测试只在 Windows 跑过，不声称支持 |

诚实标注：没实跑过的平台，不要在对外文案里写「已支持」。
