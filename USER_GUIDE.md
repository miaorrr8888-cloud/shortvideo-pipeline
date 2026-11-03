# 照片变配音视频：从下载到打开成片

你给几张商品图和几句介绍，这个工具把介绍读出来、配上图片、烧上字幕，做成 720×1280 的竖屏 MP4。以 Windows 11 + Python 3.13 为本次验证环境。

## 不会安装？先用 WorkBuddy 协助

把仓库地址交给 WorkBuddy，并粘贴 [WORKBUDDY.md](WORKBUDDY.md) 里的任务。让它先跑环境自检、装到你选定的目录，再用示例生成一条视频。WorkBuddy 客户端内的导入执行已在本机实测过（见 README 的“本次完善”），但其他客户端未实测。

## 第 1 步：准备 Python

```powershell
python --version
```

需要 3.10 或更高。装完 Python 重开一次 PowerShell，否则命令可能找不到。

## 第 2 步：进到技能目录

解压后打开**包含 SKILL.md、README.md 的那一层**文件夹，在地址栏输入 `powershell` 回车，就在这个目录打开了终端。

## 第 3 步：装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install Pillow imageio-ffmpeg
```

`Pillow` 用来排版画面，`imageio-ffmpeg` 自带 FFmpeg 二进制，不用另外装 FFmpeg、也不用改 PATH。

## 第 4 步：环境自检

```powershell
.\.venv\Scripts\python.exe scripts/make_video.py --check
```

会逐项告诉你 PASS / FAIL。常见的两个 FAIL：

- **中文字体 msyhbd.ttc 缺失**：非 Windows 系统，本模板不支持（未验证）。
- **离线中文语音缺失**：Windows 设置 → 时间和语言 → 语音 → 添加中文语音包。

自检通过（`离线配音可用：是`）再往下做。

## 第 5 步：先用自带示例跑通

```powershell
.\.venv\Scripts\python.exe scripts/make_video.py --images examples/演示商品 --out .\示例成片 --voice offline
```

约十几秒后出结果，打开 `示例成片\START_HERE.html` 就能播放。想直接看效果、不想跑代码：`examples\示例输出` 里已经放了这条示例的真实成片。

## 第 6 步：换成自己的商品

在素材目录里建一个文件夹，比如 `D:\素材\榨汁杯`，放进去：

- 至少 2 张图（最好 4–6 张：主图、细节、场景）；
- 一个 `介绍.txt`，一句话一行，每行不超过 160 字。

然后：

```powershell
.\.venv\Scripts\python.exe scripts/make_video.py --images "D:\素材\榨汁杯" --out "D:\成片\榨汁杯" --voice offline --title "便携榨汁杯 350ml"
```

**先看计划再渲染**（不确定配图对不对时）：

```powershell
.\.venv\Scripts\python.exe scripts/make_video.py --images "D:\素材\榨汁杯" --out "D:\成片\榨汁杯" --dry-plan
```

## 第 7 步：多个商品一起做

`D:\素材\全部商品\` 下每个子文件夹放 `介绍.txt` + ≥2 张图，然后：

```powershell
.\.venv\Scripts\python.exe scripts/make_video.py --products "D:\素材\全部商品" --out "D:\成片\批次001" --voice offline
```

改动后的重跑：整条没改会跳过，改一句只重做那一段，旧成片不会被覆盖。

## 关于在线配音（晓晓）

```powershell
.\.venv\Scripts\python.exe -m pip install edge-tts websocket-client
.\.venv\Scripts\python.exe scripts/make_video.py --images "..." --out "..." --voice online --allow-online-voice
```

**你加这个参数，就意味着同意**：每句文案的文字会发往微软 Edge 在线语音服务 `speech.platform.bing.com`（TTS，免账号免密钥，只发文字不发图片）。它免费，但文本确实离开了你的电脑。不想外发就用 `--voice offline`。

不加 `--allow-online-voice` 时，工具会直接停下并说明这些内容，不会偷偷联网。

## 成片之后还要做什么

1. **听一遍**：型号、数字、专有名词最容易读错，读错就改文案重跑。
2. **看一遍**：字幕有没有错字、图片和这句话对不对得上。
3. 本工具**不会**自动发布到任何平台，也不判断素材版权。

## 常见问题

**提示“每句至少需要 2 张不同画面”**
只有 1 张图，或者几张图其实完全一样（只是文件名不同）。

**提示“环境未就绪”**
先跑 `--check`，按 FAIL 项修复。工具不会为了绕过缺依赖而自动改用联网配音。

**改完文案重跑，成片没变**
整条内容没变时是 `SKIPPED_UNCHANGED`，属正常。改了才出新版本，旧成片仍在。

**上次运行中断，现在一直报缓存问题**
本版会自动把坏缓存改名成 `*.stale-<时间戳>` 再重做一次，不会永久卡住；报告里 `stats.cache_repaired` 记录了几次。

**想用 MeloTTS 本地大模型配音**
需要额外下载约 167MB 模型，走 `scripts/start_here.py`。本机**未验证**这条路线。

## 验证范围

Windows 11 + Python 3.13 实跑：离线配音出片、重跑命中缓存、改一句只重做一段、坏缓存自愈、在线配音同意闸门、缺依赖/缺文件/单图等异常。macOS、Linux、MeloTTS 模型、在线晓晓实际合成均**未验证**。

许可证与来源见 [LICENSE](LICENSE)、[PROVENANCE.md](PROVENANCE.md)。
