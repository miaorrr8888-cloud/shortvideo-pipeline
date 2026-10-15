# 文字变配音视频：用户使用指南

## 它能帮你做什么

把文字生成本地语音，再把图片按时长合成MP4；可接入自己的SRT字幕。也能单独生成脚本、分镜和字幕材料。

## 适合谁

需要做简单讲解视频的创作者、小商家、课程作者；先从Windows电脑上的演示开始。

## 具体解决什么问题

已有文案和图片，还要分别配音、安排画面时长、合成视频，容易漏步骤或截断语音。

**不适合这些目标：**复杂动态剪辑、数字人口型、自动发布和保证成片创意质量。macOS/Linux不能使用这条Windows系统配音路线。

## 下载与准备

- [打开独立仓库](https://github.com/miaorrr8888-cloud/shortvideo-pipeline)
- [直接下载源码ZIP](https://github.com/miaorrr8888-cloud/shortvideo-pipeline/archive/refs/heads/main.zip)

也可在仓库页面点 Code → Download ZIP。解压后打开包含 SKILL.md、README.md、USER_GUIDE.md 的那层文件夹。不要停在外层目录或只复制一个脚本。

建议使用Windows电脑和Python 3.12；这是本次验证环境。先在该文件夹打开PowerShell，再执行：

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe --version
```

这里直接使用虚拟环境里的Python，不需要运行激活脚本或修改系统执行策略。安装步骤及其他系统说明见[通用安装说明](https://github.com/miaorrr8888-cloud/agent-skills-worklog/blob/main/INSTALLATION.md)。

安装本示例需要的依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install Pillow imageio-ffmpeg==0.6.0
```

## 第一次使用：先跑自带示例

用仓库里的两张演示图片和一段中文文本，生成一段带中文配音的简单视频。

```powershell
$skillFfmpeg = & .\.venv\Scripts\python.exe -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
.\.venv\Scripts\python.exe scripts/make_narrated_video.py examples/slides/manifest.json examples/narration.txt reader-demo-video --ffmpeg $skillFfmpeg
```

## 结果怎么看

新建 reader-demo-video 文件夹，其中有 video.mp4、narration.wav、status.json。状态 GENERATED_REVIEW_REQUIRED 表示已生成、仍要试听和看图；不是人工验收通过。

## 换成自己的资料

examples/narration.txt 是配音稿；examples/slides/manifest.json 的 slides 数组填写图片相对路径和 seconds。图片放在清单所在目录内。

先复制 examples/slides 到自己的工作目录，换成自己的图片；另存文案，再把命令中的清单和文案路径换成自己的文件。输出目录必须换一个新名字。

## 不想手动敲命令：给AI助手的任务

以下任务适用于能读取所选目录、执行本地命令的助手。WorkBuddy需要先确认当前版本的权限与技能启用状态；本项目未完成WorkBuddy实际导入验收。

```text
请先读取我选定文件夹中的 SKILL.md 和 USER_GUIDE.md，只在该项目范围内处理。
先运行仓库自带示例，把中文文案合成带配音的图片视频。检查Python、Pillow、FFmpeg和本地中文声音，把结果写入新的 reader-demo-video 目录。不要调用云端付费模型、不要发布视频；完成后告诉我视频文件在哪里、还有什么需要试听验收。
缺少依赖时先说明用途，优先放进本项目虚拟环境；不要读取其他目录中的密码、密钥或浏览器登录数据。
```

## 常见问题

**找不到FFmpeg**

按下方先取得 imageio-ffmpeg 的可执行文件路径，再通过 --ffmpeg 传入。

**语音不自然或数字读错**

先听 narration.wav；改写文案中的数字、缩写或读音，再用新输出目录重做。

**找不到文件或脚本**

确认终端当前目录就是包含SKILL.md的技能根目录；路径含空格时加双引号。输出目录已存在时换新名字，不覆盖已有结果。

## 当前能力边界

当前以静态图片视频为主。Windows需安装对应语言的本地声音；系统声音不能初始化时先核对运行环境，不修改安全策略强行绕过。字幕轨道不是烧录在画面里的字幕。

## 验证范围

本指南示例已在Windows独立副本中运行复核，见[命令复核结果](https://github.com/miaorrr8888-cloud/agent-skills-worklog/blob/main/USER_GUIDES_VERIFICATION.md)。已有回归测试只覆盖被测试行为，不证明真实业务结果。WorkBuddy实际运行、手机端使用和所有系统版本均不在本次已验证范围内。

许可证和素材来源分别见 [LICENSE](LICENSE)、[PROVENANCE.md](PROVENANCE.md)。
