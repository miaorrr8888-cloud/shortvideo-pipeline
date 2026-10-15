@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3.12 scripts\start_here.py --install --demo
) else (
  python scripts\start_here.py --install --demo
)
if errorlevel 1 (
  echo 安装或运行未完成。先看上面的提示；没有Python时安装Python 3.12。
  echo https://www.python.org/downloads/windows/
  echo 不需要管理员权限。不要关闭安全软件或修改系统执行策略。
)
pause
