#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环境体检：在动手装之前，先确认这台机器具备条件。

检查的都是「会让你白忙一场」的东西：Python 太旧、路径带中文、磁盘不够、
工具文件缺失、网络连不上 GitHub。
"""

import shutil
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MIN_PY = (3, 9)
GITHUB_HOSTS = [("github.com", 443), ("api.github.com", 443)]


def _free_gb(path):
    try:
        return round(shutil.disk_usage(path).free / 1024 ** 3, 1)
    except OSError:
        return -1


def check_network(hosts=None, timeout=3.0):
    """能否连上 GitHub。返回 (ok, 失败的主机列表)。"""
    hosts = hosts or GITHUB_HOSTS
    bad = []
    for host, port in hosts:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                continue
        except OSError:
            bad.append(host)
    return (not bad), bad


def run(with_network=True):
    """返回 [{'level','title','detail','fix'}]。"""
    out = []

    # Python 版本
    ver = sys.version_info[:3]
    if ver[:2] >= MIN_PY:
        out.append({"level": "ok", "title": f"Python {'.'.join(map(str, ver))}",
                    "detail": "版本满足要求", "fix": ""})
    else:
        out.append({"level": "fail", "title": f"Python {'.'.join(map(str, ver))} 太旧",
                    "detail": f"需要 {'.'.join(map(str, MIN_PY))} 或更新",
                    "fix": "https://www.python.org/downloads/"})

    # 路径
    text = str(ROOT)
    bad_chars = [c for c in text if ord(c) > 127]
    if bad_chars:
        out.append({"level": "warn", "title": "工具包路径含中文",
                    "detail": f"{text}",
                    "fix": "挪到纯英文路径，例如 D:\\Tools\\Hackintosh"})
    elif " " in text:
        out.append({"level": "warn", "title": "工具包路径含空格",
                    "detail": f"{text}",
                    "fix": "挪到不含空格的路径"})
    else:
        out.append({"level": "ok", "title": "路径是纯英文、无空格", "detail": text, "fix": ""})

    # 写权限
    probe = ROOT / ".hk_write_test"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        out.append({"level": "ok", "title": "工具包目录可写", "detail": "", "fix": ""})
    except OSError as exc:
        out.append({"level": "fail", "title": "工具包目录不可写", "detail": str(exc),
                    "fix": "别放在 C:\\Program Files 这类受保护目录"})

    # 磁盘
    free = _free_gb(ROOT)
    if free < 0:
        out.append({"level": "warn", "title": "读不到磁盘空间", "detail": "", "fix": ""})
    elif free < 30:
        out.append({"level": "fail", "title": f"剩余空间只有 {free} GB",
                    "detail": "安装 macOS 至少需要 30 GB 空闲",
                    "fix": "清理磁盘或换一块盘"})
    elif free < 60:
        out.append({"level": "warn", "title": f"剩余空间 {free} GB",
                    "detail": "能装，但装完会比较紧", "fix": "建议留 60 GB 以上"})
    else:
        out.append({"level": "ok", "title": f"剩余空间 {free} GB", "detail": "", "fix": ""})

    # 工具文件
    for label, rel in [("OpCore-Simplify", "tools/OpCore-Simplify/OpCore-Simplify.py"),
                       ("gibMacOS", "tools/gibMacOS/gibMacOS.py")]:
        p = ROOT / rel
        if p.exists():
            out.append({"level": "ok", "title": f"{label} 已就位", "detail": rel, "fix": ""})
        else:
            out.append({"level": "fail", "title": f"{label} 缺失", "detail": rel,
                        "fix": "重新解压完整的工具包"})

    # 网络
    if with_network:
        ok, bad = check_network()
        if ok:
            out.append({"level": "ok", "title": "能连上 GitHub", "detail": "", "fix": ""})
        else:
            out.append({"level": "warn", "title": "连不上 GitHub",
                        "detail": "、".join(bad),
                        "fix": "检查代理/VPN；离线也能用 hk，只是没法自动下载"})

    return out


def summary(items):
    fails = [i for i in items if i["level"] == "fail"]
    warns = [i for i in items if i["level"] == "warn"]
    if fails:
        return f"有 {len(fails)} 项阻塞，先解决再继续"
    if warns:
        return f"基本可用，{len(warns)} 项建议处理"
    return "全部通过"


if __name__ == "__main__":
    for it in run(with_network="--offline" not in sys.argv):
        mark = {"ok": "✅", "warn": "⚠️", "fail": "❌"}[it["level"]]
        print(f"{mark} {it['title']}" + (f"：{it['detail']}" if it["detail"] else ""))
        if it["fix"]:
            print(f"    → {it['fix']}")
    print()
    print(summary(run(with_network="--offline" not in sys.argv)))
