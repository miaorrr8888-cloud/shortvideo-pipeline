# 文字变配音视频

已有文案和图片，还要分别配音、安排画面时长、合成视频，容易漏步骤或截断语音。

这个开源技能可以帮助你：把文字生成本地语音，再把图片按时长合成MP4；可接入自己的SRT字幕。也能单独生成脚本、分镜和字幕材料。

**适合谁：**需要做简单讲解视频的创作者、小商家、课程作者；先从Windows电脑上的演示开始。

**怎么开始：**下载并解压独立仓库，按USER_GUIDE先跑自带示例，再换成自己的资料。需要电脑和相应运行环境。

**能看到的结果：**新建 reader-demo-video 文件夹，其中有 video.mp4、narration.wav、status.json。状态 GENERATED_REVIEW_REQUIRED 表示已生成、仍要试听和看图；不是人工验收通过。

**使用前知道：**当前以静态图片视频为主。Windows需安装对应语言的本地声音；系统声音不能初始化时先核对运行环境，不修改安全策略强行绕过。字幕轨道不是烧录在画面里的字幕。

[项目与下载入口](https://github.com/miaorrr8888-cloud/shortvideo-pipeline) · [逐步使用指南](https://github.com/miaorrr8888-cloud/shortvideo-pipeline/blob/main/USER_GUIDE.md)

说明：示例、演示与实际业务结果分开记录；介绍文案已准备，尚未发布到自媒体平台。
