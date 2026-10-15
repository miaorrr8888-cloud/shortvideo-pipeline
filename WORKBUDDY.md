# 交给WorkBuddy的话

**视频同款晓晓女声：先读[晓晓使用指南](晓晓使用指南.md)，下载解压后双击“开始晓晓配音.cmd”。** 下方MeloTTS是另一种离线配音方案。

复制下面整段，连仓库地址一起发给WorkBuddy。它需要你授权一个本地工作目录；如果出现登录、系统确认或权限提示，由你本人处理。

```text
请帮我把这个技能安装好，并用示例做出一个有中文配音的小视频：
https://github.com/miaorrr8888-cloud/shortvideo-pipeline

先下载并阅读最新 SKILL.md、USER_GUIDE.md 和 安装与排错.md，检查脚本后，只在我选定的项目目录操作。
使用新版MeloTTS本地配音，运行 scripts/start_here.py --install --demo；不要使用旧SAPI/Windows系统音色。使用Python 3.12，在项目.venv里安装依赖，不修改系统安全策略，不调用收费语音接口。
如果当前WorkBuddy能导入本地技能包，按当前版本技能页面操作；不能导入时，仍可在授权目录读取说明并执行，不要把“下载”说成“已安装”。
先做仓库自带示例，确认video.mp4存在、包含声音、能解码。告诉我完整成片路径、怎样打开、怎样换成自己的图和文字。再让我试听。
遇到错误先读取 runs/setup-result.json，说明卡在哪一步，按排错指南做最小修复；不要不断重复相同失败步骤。
需要我验证或授权时，告诉我具体要点哪里。不要自动发布视频，不要读取无关目录的凭据。
```

官方依据：[WorkBuddy技能说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)说明支持导入本地技能包；[官方产品介绍](https://cloud.tencent.com/product/workbuddy)说明支持在授权目录内读写本地文件。仅发送链接不等于已完成安装；本项目尚未完成WorkBuddy端实测。

## 一批商品或反复改稿

使用[批量商品视频.md](批量商品视频.md)里的完整任务，先整理清单、检查逐句图片，再批量生成。不要把旧单条制作入口当成批处理。
