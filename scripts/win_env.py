"""Windows 工具定位。

存在的理由：容器、CI、部分 IDE 终端会裁剪 PATH，把
``C:\\Windows\\System32\\WindowsPowerShell\\v1.0`` 去掉。此时只用
``shutil.which("powershell.exe")`` 会返回 None，进而被误判成
「没装中文语音包」——用户去装语音包也修不好，因为真正缺的是 PATH 里的路径。
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path


def resolve_powershell() -> str | None:
    """返回可执行的 powershell.exe 绝对路径，找不到返回 None。"""
    found = shutil.which("powershell.exe")
    if found:
        return found
    root = os.environ.get("SystemRoot") or r"C:\Windows"
    candidates = (
        Path(root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe",
        # 32 位进程访问 64 位 System32 的别名目录
        Path(root) / "Sysnative" / "WindowsPowerShell" / "v1.0" / "powershell.exe",
    )
    for cand in candidates:
        if cand.is_file():
            return str(cand)
    return None
