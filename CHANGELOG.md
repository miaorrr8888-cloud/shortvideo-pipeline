# 更新记录

## 2026-11-03 · v0.2.3

### 修复

- **`batch-report.json` 统计错误（实跑复现后修）**：整批重跑时每个任务都走 `SKIPPED_UNCHANGED`，
  计数器全为 0，报告却写 `clips_resolved: 0` + `stats_consistent: false`，并提示「可能有任务未完成」——
  把一次正常的缓存复用报成了故障。
  改为按每个任务实际拼进成片的句数统计（`resolved_sentences`），并区分
  `clips_rendered_this_run` / `clips_from_cache_this_run` / `clips_resolved`。
- 新增任务状态计数：`jobs_total` / `jobs_generated` / `jobs_skipped` / `jobs_failed`。
- 中途落盘的那份 `batch-report.json` 现在也带完整统计，进程被杀时不会再留下一份没数的报告。
- 删掉 `stats_summary` 末尾一行永远执行不到的 `return target` 死代码。
- CLI 汇总行改为「成片共 N 段（本次新渲染 A，本次命中缓存 B）」，
  并显式说明「其中 K 个商品与上次完全一致，整条成片直接复用」。

### 实测（本机 Windows 11 + Python 3.13 + 微软 Huihui 离线语音）

- 单商品 3 句：11.32 秒成片，720×1280 H.264 + AAC，`volumedetect` 均值 -21.8 dB（有人声，非静音）；
  抽帧确认中文字幕已烧录、未被裁切。
- 缓存：同参数第二次运行 → `SKIPPED_UNCHANGED`，报告自洽。
- 批处理：2 商品 4 句 → 两条成片；改其中 1 句 → 只重渲 1 段、命中缓存 1 段、另一商品整条复用。
- 测试：83 项通过（新增 6 项针对统计口径与落盘一致性）。

## 2026-11-03 · v0.2.2 修掉报告统计误读（原「已知未修」问题的真正根因）

### 根因：不是漏计数，是报告只描述了「最后一个进程」

- 现象：6 句文案的 `batch-report.json` 写「配音 1 次 + 命中 1 次」，磁盘上却有 6 个 wav、6 个 mp4。
- 排查：在 `sentence_clip` / `speech` 入口打点，同一 `state` 对象（id 一致）逐次自增无误；
  真实情况是前 4 句在本次进程里就是**缓存命中**（上一轮运行被中断，片段已经落盘），
  本进程确实只新渲染了 2 段。报告数字对「本进程」是诚实的，但对「这条视频一共做了多少活」是误导。
- 修法：新增 `stats_summary()`，报告同时给出 `speech_calls` / `clips_resolved`（总数）、
  `sentences_expected`（应做句数）与 `stats_consistent`（一致性标记），不一致时附 `stats_note` 说明原因。
  CLI 输出改为「配音调用 N 次（新生成 A，复用缓存 B）」，不再让人误以为漏做。

### 顺带修：中断残留的临时目录没人清

- 现象：`clip-cache/clip-xxxxxx`、`products/.../concat-xxxxxx` 这类目录在进程被杀后会一直留着。
- 修法：`clean_orphan_temps()` 在每次批量开始时清理（只删这三类临时目录，缓存文件和成片不动），
  清理个数记在 `stats.temp_cleaned`。

### 回归测试

新增 `tests/test_report_stats.py`（6 项）：统计口径、缺失字段容错、不改动输入、只清临时目录。全套 77 项通过。

## 2026-11-03 · v0.2.1 实跑修复（两个真 bug + 一条已知问题）

本轮不是改文档，是把技能真的跑起来做演示片时撞出来的问题。

### 修复 1：`--check` 说语音可用，出片却直接失败

- **现象**：`--check` 报「找不到 powershell.exe」，修复建议却写「去装中文语音包」——
  装了也修不好；强行走 `--voice offline` 会得到 `BLOCKED_SPEECH_SERVICE / Voice generation failed: ValueError`。
- **根因**：`make_video.py` 与 `synthesize_voice.py` 各自用 `shutil.which("powershell.exe")` 探测，
  PATH 被裁剪（本机 PATH 缺 `System32\WindowsPowerShell\v1.0`）时误判「没有中文语音」，
  而系统里实际装着 Microsoft Huihui。
- **修法**：新增 `scripts/win_env.py` 统一探测（PATH → `System32` → `Sysnative`），两处共用；
  `--check` 的修复建议按真实原因分流（PATH 缺失 vs 语音包缺失）。

### 修复 2：字幕超长不换行，且被切成碎片依次闪现

- **现象**：一句 16 字被切成「前 13 字显示 3 秒 + 剩 2 字闪 0.46 秒」，长句碎成十几个闪块。
- **根因**：`captions()` 用 `wrap(part, 13)` 按字数硬切，每个切片是**独立 ASS 事件**轮流显示。
- **修法**：新增 `caption_screens()`，长句用 ASS `\N` **同屏折行**（每行 ≤13 字、每屏 ≤3 行）；
  行内**优先在标点后断行**，不把「不出门」拆成「不出 / 门」；末行不足 4 字时从上一行借字。
- **测试**：新增 `tests/test_captions.py` 12 项，锁住不碎屏、不孤字、不超宽、不串行、转义不破坏换行。

### 其它

- `batch_product_videos.VERSION` 3 → 5：渲染行为改动必须升版本号，
  否则旧片段缓存会被命中，看不到修复效果（首次踩到）。
- `SKILL.md` 补充字幕折行规则；同步版本号到 0.2.1（`pyproject.toml` 同步）。

### 已知未修（如实记录，不是已解决）

- `batch-report.json` 的 `stats` 在**句数 ≥4** 时会低估工作量：实际做 6 段配音，报告显示 1 次请求 + 1 次命中。
  已核实缓存**没有串用别的文案**、成片内容正确；2 句/3 句场景计数 100% 准确，≥4 句才复现，根因未定位。
  交付时以 `sentence_timing` 与缓存目录文件数为准，别拿 `stats` 当工作量证据。

## 2026-11-03 · v0.2.0 发布规范整改

### 内容补齐

- **补齐实现与测试**：本地已实现但从未推送的 `scripts/make_video.py`、`tests/test_make_video.py`（2 个文件）。此前仓库里只有文档，装下去跑不起来。
- **补齐示例素材与示例输出**：12 个文件（`examples/`），让使用者不用自备素材就能跑通。
- 新增 `icon.svg`（技能图标）。

### 规范整改

- `name` 改为 ASCII slug（= 目录名），中文名保留在 `display_name`。与已发布仓库的写法对齐，消除本地与远端的命名漂移。
- `LICENSE` 替换为完整 MIT 全文。旧版免责条款被截断，GitHub 因此识别为 `NOASSERTION`（等于没声明许可证）。
- 补充 `version` 与 `agent_created` 字段，满足技能市场打包校验。
- 同步更新 11 个已变动文件（含 `examples/batch-products/jobs.json`、`pyproject.toml`、`requirements.txt`、`scripts/batch_product_videos.py`）。

### 测试

- `python -m unittest discover -s tests` 全部通过（详见发布审计报告）。

## 2026-10-18 · 1.0.1 标题折行修正（发布候选）

修掉一个肉眼可见的画面缺陷：顶部标题原来按**固定 20 字**硬折行，`registry-video-20261018`
被切成 `registry-video-20261` + `018`，断在数字中间。720px 画面实际能放下约 39 个 ASCII
字符，固定字数折行等于浪费了一半宽度。

- 新增 `wrap_px()`：按 `textlength` 实测像素宽度折行，一行的宽度上限 660px；
- 溢出点紧跟分隔符（`-` `_` `/` 空格，且浪费不超过 12 字）时，断在分隔符后，不切进单词或数字；
- 放得下就继续填满当前行，不为了对齐分隔符而整行留白；
- 中文标题行为基本不变（32px 汉字约 20 字/行，与原来的 20 字一致）；
- `batch_product_videos.py` 版本 2 → 3，旧片段缓存指纹自动失效并重渲染，不会混用旧画面；
- 新增 4 项回归测试（长 ASCII 标题单行、任何行不超宽、分隔符处断行、贪心填满），
  测试总数 56 → 60，全部通过。

未改动的部分：字幕仍按固定 13 字折行（汉字宽度均匀，问题不明显）；配音与字幕时序仍
按句均分，不保证与语音逐字对齐。

## 2026-10-18 · 1.0.0 统一入口版（发布候选）

新增 `scripts/make_video.py` 作为唯一入口，`--check` 自检 + 单商品 + 多商品批量。

- 环境自检：Python / Pillow / FFmpeg（PATH 或 imageio-ffmpeg 自带）/ 中文字体 / 离线中文语音 / 在线语音依赖，逐项 PASS-FAIL 并给修复命令；
- 配音知情同意：`--voice online` 必须配 `--allow-online-voice`，否则拒绝并说明「发什么、发到哪、是否收费」；`--voice auto` 只选离线，环境不满足时不会偷偷改用联网；
- 音色如实标注：报告、缓存指纹、结果页记录真实音色（离线 = Windows SAPI + 具体音色名），修掉了「离线配音也写成晓晓」的误导；
- 缓存自愈：语音/片段/成片残留半截文件时改名 `*.stale-<时间戳>` 留现场并重做一次，不再永久 FAILED；`stats.cache_repaired` 计数；
- 修复 result.json 丢失但成片还在时 `File exists` 导致的永久失败；
- 字幕可读性：字号 36→44、每行 16→13 字、白字黑描边（原为半透明灰底）；
- 离线配音不再依赖 edge-tts（只在走在线时才导入）；
- `synthesize_melo.py` 先校验输入再导入依赖，缺依赖不再被误报成参数错误；
- 示例图 1254px PNG（3.8MB）压成 720px JPEG，新增 `examples/演示商品` 与真实运行结果 `examples/示例输出`；
- 新增 16 项测试（合计 56 项通过）：同意闸门、auto 不偷偷联网、分句与配图、异常退出码、真实出片与缓存复用、坏缓存自愈。

未验证：在线晓晓实际合成（缺 websocket-client 且未获同意）、MeloTTS 模型路线（未下载模型）、macOS/Linux。

## 2026-10-15 · 使用者完善版

重复导出自动建立新目录；检查标题、时长和痛点字段；dry-run 始终走离线 mock；补正式简报示例。

仍需改进：没有视频渲染、剪映集成、真实配音和成片验收；真实模型质量、素材版权与平台发布仍需单独验证。

## 2026-10-15 第二轮补齐

新增图片序列转竖屏 MP4，可接入本人提供的录音和 SRT 字幕；限定本地文件，新输出不覆盖旧文件。

当前边界：仍需安装 FFmpeg 和 Pillow；字幕为可切换字幕轨道，不是烧录到画面。尚无自动配音、剪映工程、动态剪辑或平台发布；真实素材和成片仍需人工验收。

## 2026-10-15 第三轮

新增 Windows SAPI 中文/英文离线配音，以及文本→配音→图片视频的一键流程；画面时长自动延长以完整容纳语音，失败保留阶段状态。已实际生成中文配音并合成视频。

边界：配音依赖 Windows 已安装的声音；Linux/macOS 仍需提供外部录音。受限运行环境可能无法初始化系统声音，不应修改安全策略来绕过。生成声音需要试听；静态图片视频不等于复杂动态剪辑或平台验收。
