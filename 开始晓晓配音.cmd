@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
 py -3.12 scripts\start_xiaoxiao.py --install
) else (
 python scripts\start_xiaoxiao.py --install
)
pause
