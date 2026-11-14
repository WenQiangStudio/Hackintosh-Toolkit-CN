#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""黑苹果工具包 · 环境自检

在开始之前跑一遍，确认 Python、路径、文件都就位。
没有任何第三方依赖，Python 3.8+ 即可。

用法：
    python check_env.py
"""

import sys
from pathlib import Path

MIN_PYTHON = (3, 8)

PASS = "[ OK ]"
WARN = "[警告]"
FAIL = "[失败]"

failures = []
warnings = []


def say(status, message, detail=""):
    print(f"  {status} {message}" + (f"  ({detail})" if detail else ""))


def check_python():
    print("\n[1/4] Python 版本")
    ok = sys.version_info[:2] >= MIN_PYTHON
    version = ".".join(str(n) for n in sys.version_info[:3])
    if ok:
        say(PASS, f"Python {version}")
    else:
        say(FAIL, f"Python {version} 太旧", "需要 3.8 或更新")
        say("", "下载地址: https://www.python.org/downloads/")
        say("", "Windows 安装时务必勾选 'Add python.exe to PATH'")
        failures.append(True)
    return ok


def check_path():
    print("\n[2/4] 路径检查")
    root = Path(__file__).resolve().parent.parent
    problems = []
    for label, p in (("工具包目录", root), ("当前目录", Path.cwd())):
        text = str(p)
        bad = [c for c in text if ord(c) > 127]
        if bad:
            problems.append((label, text, "包含中文或特殊字符"))
        elif " " in text:
            problems.append((label, text, "包含空格"))

    if not problems:
        say(PASS, "路径是纯英文、无空格")
        return True

    for label, text, why in problems:
        say(WARN, f"{label} {why}")
        print(f"         当前: {text}")
    print("\n  建议把整个文件夹移动到类似 D:\\Tools\\Hackintosh 的位置。")
    print("  含中文/空格的路径会让 OpCore-Simplify 和 gibMacOS 无法正常运行。")
    warnings.append(True)
    return False


def check_files():
    print("\n[3/4] 工具文件完整性")
    root = Path(__file__).resolve().parent.parent
    required = [
        ("OpCore-Simplify 主程序", "tools/OpCore-Simplify/OpCore-Simplify.py"),
        ("OpCore-Simplify 启动器", "tools/OpCore-Simplify/OpCore-Simplify.bat"),
        ("兼容性数据库", "tools/OpCore-Simplify/Scripts/datasets/pci_data.py"),
        ("gibMacOS 主程序", "tools/gibMacOS/gibMacOS.py"),
        ("gibMacOS 启动器", "tools/gibMacOS/gibMacOS.bat"),
    ]
    missing = 0
    for label, rel in required:
        p = root / rel
        if p.exists():
            size = p.stat().st_size
            say(PASS, f"{label}", f"{size:,} 字节")
        else:
            say(FAIL, f"{label} 缺失", rel)
            missing += 1

    if missing:
        failures.append(True)
        print("\n  文件不完整，请重新解压整个压缩包。")
        return False
    return True


def check_writable():
    print("\n[4/4] 写入权限")
    root = Path(__file__).resolve().parent.parent
    probe = root / ".write_test"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        say(PASS, "工具包目录可写")
        return True
    except OSError as exc:
        say(FAIL, "工具包目录不可写", str(exc))
        print("  如果放在 C:\\Program Files 等受保护目录，请换个位置。")
        failures.append(True)
        return False


def summary():
    print("\n" + "=" * 46)
    if failures:
        print("  自检未通过，请先解决上面的 [失败] 项。")
        print("=" * 46)
        return 1
    if warnings:
        print("  自检基本通过，但 [警告] 项建议处理后再继续。")
        print("=" * 46)
        return 0
    print("  全部通过，可以开始下一步了。")
    print("  下一步: 运行 tools/OpCore-Simplify/OpCore-Simplify.bat")
    print("=" * 46)
    return 0


def main():
    # Windows 控制台默认 GBK，输出中文可能报错
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    print("=" * 46)
    print("  黑苹果工具包 · 环境自检")
    print("=" * 46)

    check_python()
    check_path()
    check_files()
    check_writable()

    return summary()


if __name__ == "__main__":
    sys.exit(main())
