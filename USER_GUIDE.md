# 照片变配音视频：从下载到打开成片

你给几张商品图和几句介绍，这个工具把介绍读出来，配上图片，做成MP4。新版使用MeloTTS中文模型，不用Windows系统音色。以Windows + Python 3.12为本次验证环境。

## 不会安装？先用WorkBuddy协助

可以先把仓库地址交给WorkBuddy，并粘贴[WORKBUDDY.md](WORKBUDDY.md)里的任务。让它先检查环境、安装到你选定的目录，再用示例生成视频。当前没有完成WorkBuddy客户端导入及执行实测，不把“看见链接”当作安装成功。

## 自己装：按这7步做

### 1. 下载整个技能

[点这里下载ZIP](https://github.com/miaorrr8888-cloud/shortvideo-pipeline/archive/refs/heads/main.zip)。也可以打开仓库，点绿色Code，再点Download ZIP。

你应该得到 shortvideo-pipeline-main.zip。不要只保存网页或复制SKILL.md。

### 2. 解压，再打开里面的文件夹

右键压缩包 → 全部解压。进入能同时看见 SKILL.md、开始使用.cmd、scripts、examples 的那一层。
建议放在自己有权限的目录，例如“文档/我的视频工具”。不要放在系统目录。

### 3. 准备Python 3.12

若电脑没有Python 3.12，从[Python官网](https://www.python.org/downloads/windows/)下载3.12系列Windows安装器，选择“仅为当前用户安装”，勾选安装器提供的Add python.exe to PATH。不要卸载其他项目已有的Python。

不确定是否装好，可让WorkBuddy检查，或在终端输入 `py -3.12 --version`，应该看到 Python 3.12.x。没有py时，检查 `python --version`。本自动安装路线只验证了3.12。

### 4. 双击“开始使用.cmd”

它会在项目里创建 .venv，安装必要工具，再从GitHub下载约167MB的中文语音模型；模型解压后会占更多空间。首次需要联网，模型准备好后，配音在本机完成。脚本不需要管理员权限，不会自动发布。

窗口依次显示“创建运行环境”“安装工具”“检查中文语音模型”“生成视频”。下载时间受网速影响；未显示完成前不要关窗口。断网后重新运行会续传模型，失败会留下检查结果。

如果系统提示文件风险或组织限制，先核对来源或交给助手分析，不要强行绕过。

### 5. 找到刚生成的视频

窗口出现“已生成，请打开：……”才代表示例生成成功。打开其给出的 runs/demo-日期-时间/video.mp4。
同一目录的 narration.wav 是配音。runs/setup-result.json 是检查记录。自己听一遍、看一遍，确认没有念错或放错图。

### 6. 换成自己的图片和文字

先复制 examples/slides 到 examples/my-slides。把自己的图片放进去，编辑里面的 manifest.json：每张图写相对文件名和seconds；图片要在该清单目录内。把介绍另存为 examples/my-narration.txt（UTF-8）。

```json
{"slides":[{"image":"商品正面.jpg","seconds":2},{"image":"桌面场景.jpg","seconds":2}]}
```

seconds表示相对展示时长；文案更长时，工具会自动延长总时长，不把声音截断。需要严格一句两图时，先分句并为每句安排两幅画面；基础清单不会自动理解每句话的内容或自动找图。视频V5的72幅画面由本次人工分镜制作。

### 7. 再生成一次

在技能文件夹地址栏输入 powershell 回车，在打开的窗口粘贴：

```powershell
$videoFfmpeg = & .\.venv\Scripts\python.exe -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
.\.venv\Scripts\python.exe scripts/make_melo_video.py examples/my-slides/manifest.json examples/my-narration.txt runs/my-video-01 --model-dir models/vits-melo-tts-zh_en --ffmpeg $videoFfmpeg
```

做完打开 runs/my-video-01/video.mp4。重做时改为my-video-02等新目录，不会覆盖原结果。不会改文件或命令，直接让WorkBuddy根据你的图片和介绍代做，并要求读回成片位置。

## 发生问题，先看这里

读[安装与排错.md](安装与排错.md)。不要反复重装全部环境。请把报错最后几行与 runs/setup-result.json 交给助手；不要只说“不能用”。

## 当前能做什么

可以解决：图片和文字分别配音、合成步骤多；配音比画面长造成截断；第一次依赖缺失难定位；换图换稿后重复制作。
当前主要是图片轮播加解说，不是动态拍摄、数字人口型或自动运营。读音、事实和素材许可需要人检查。WorkBuddy自身可能消耗账户额度；本工具配音不用云端收费接口。
