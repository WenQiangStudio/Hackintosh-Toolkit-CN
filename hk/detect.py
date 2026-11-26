#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动检测本机硬件。

目标是「少让用户手填」：能读到的就填上，读不到的留空并说明原因。

跨平台策略：
- Windows：PowerShell CIM 查询（wmic 在新系统上已移除）
- Linux：/proc、/sys、lspci
- macOS：system_profiler

所有解析都拆成纯函数，方便用固定文本测；真正的命令调用只负责取回文本。
任何一步失败都不抛异常，记进 notes 继续往下走——检测不全也有价值，
总比让用户对着一整屏空白发呆强。
"""

import platform
import re
import shutil
import subprocess
import sys


def _run(cmd, timeout=15):
    """跑命令返回 stdout 文本；失败返回空串。"""
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=timeout,
                             text=True, errors="replace")
        return out.stdout if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


# ---------------------------------------------------------------- 解析器
def parse_wmic_cpu(text):
    """从 Win32_Processor 的名称里取一行。"""
    for line in (text or "").splitlines():
        s = line.strip()
        if s and not s.lower().startswith("name"):
            return s
    return ""


def parse_gpu_lines(text):
    """通用：每行一个显卡名，过滤空行和表头。"""
    out = []
    for line in (text or "").splitlines():
        s = line.strip()
        if not s or s.lower() in ("name", "caption"):
            continue
        if s not in out:
            out.append(s)
    return out


def parse_meminfo(text):
    """/proc/meminfo → GB（取整数）。"""
    m = re.search(r"MemTotal:\s*(\d+)\s*kB", text or "")
    return round(int(m.group(1)) / 1024 / 1024) if m else 0


def parse_cpuinfo(text):
    """x86 取 model name；ARM 设备没有这一行，退回 Hardware / Processor。"""
    for key in ("model name", "Hardware", "Processor"):
        m = re.search(rf"^{key}\s*:\s*(.+)", text or "", re.M)
        if m:
            return m.group(1).strip()
    return ""


def parse_system_profiler_chip(text):
    m = re.search(r"Chip\s*:\s*(.+)", text or "")
    if m:
        return m.group(1).strip()
    m = re.search(r"Processor Name\s*:\s*(.+)", text or "")
    return m.group(1).strip() if m else ""


def guess_storage(names):
    """根据块设备名猜存储类型。names 是设备名列表。"""
    names = [n for n in names if n]
    if any(n.startswith("nvme") for n in names):
        return "nvme"
    if any(n.startswith(("sd", "hd", "ata")) for n in names):
        return "sata"
    return ""


# ---------------------------------------------------------------- 各平台
def _detect_windows(notes):
    info = {"cpu": "", "gpus": [], "memory_gb": 0, "storage": "", "platform": "desktop"}
    if not shutil.which("powershell") and not shutil.which("pwsh"):
        notes.append("找不到 PowerShell，无法自动读取硬件")
        return info
    ps = shutil.which("powershell") or shutil.which("pwsh")

    cpu_txt = _run([ps, "-NoProfile", "-Command",
                    "(Get-CimInstance Win32_Processor).Name"])
    info["cpu"] = parse_wmic_cpu(cpu_txt)

    gpu_txt = _run([ps, "-NoProfile", "-Command",
                    "(Get-CimInstance Win32_VideoController).Name"])
    info["gpus"] = parse_gpu_lines(gpu_txt)

    mem_txt = _run([ps, "-NoProfile", "-Command",
                    "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB)"])
    m = re.search(r"\d+", mem_txt or "")
    info["memory_gb"] = int(m.group(0)) if m else 0

    disk_txt = _run([ps, "-NoProfile", "-Command",
                     "(Get-PhysicalDisk | Select-Object -ExpandProperty BusType) -join ','"])
    bus = (disk_txt or "").upper()
    if "NVME" in bus:
        info["storage"] = "nvme"
    elif "SATA" in bus:
        info["storage"] = "sata"

    bat = _run([ps, "-NoProfile", "-Command",
                "(Get-CimInstance Win32_Battery).Status"])
    if (bat or "").strip():
        info["platform"] = "laptop"
    notes.append("Intel VMD / RST 模式无法自动判断，请到 BIOS 确认")
    return info


def _detect_linux(notes):
    info = {"cpu": "", "gpus": [], "memory_gb": 0, "storage": "", "platform": "desktop"}
    try:
        with open("/proc/cpuinfo", encoding="utf-8", errors="replace") as fh:
            info["cpu"] = parse_cpuinfo(fh.read())
    except OSError:
        notes.append("读不到 /proc/cpuinfo")
    try:
        with open("/proc/meminfo", encoding="utf-8", errors="replace") as fh:
            info["memory_gb"] = parse_meminfo(fh.read())
    except OSError:
        pass

    if shutil.which("lspci"):
        txt = _run(["lspci"])
        for line in txt.splitlines():
            low = line.lower()
            if ("vga compatible" in low or "3d controller" in low
                    or "display controller" in low):
                name = line.split(":", 2)[-1].strip()
                name = re.sub(r"^.*?\[[0-9a-f]{4}\]\s*", "", name)
                if name:
                    info["gpus"].append(name)
    else:
        notes.append("没有 lspci，显卡型号无法读取")

    try:
        import glob
        names = [p.rsplit("/", 1)[-1] for p in glob.glob("/sys/block/*")]
        info["storage"] = guess_storage(names)
    except Exception:  # noqa: BLE001
        pass

    try:
        import glob
        if glob.glob("/sys/class/power_supply/BAT*"):
            info["platform"] = "laptop"
    except Exception:  # noqa: BLE001
        pass
    return info


def _detect_macos(notes):
    info = {"cpu": "", "gpus": [], "memory_gb": 0, "storage": "nvme", "platform": "laptop"}
    hw = _run(["system_profiler", "SPHardwareDataType"])
    info["cpu"] = parse_system_profiler_chip(hw)
    m = re.search(r"Memory:\s*(\d+)\s*GB", hw)
    if m:
        info["memory_gb"] = int(m.group(1))
    disp = _run(["system_profiler", "SPDisplaysDataType"])
    for m in re.finditer(r"Chipset Model:\s*(.+)", disp):
        info["gpus"].append(m.group(1).strip())
    if "MacBook" not in (_run(["system_profiler", "SPHardwareDataType"]) or ""):
        info["platform"] = "desktop"
    return info


# ---------------------------------------------------------------- 入口
def detect():
    """返回检测结果。字段缺失用空值，不抛异常。"""
    system = platform.system()
    notes = []
    if system == "Windows":
        info = _detect_windows(notes)
    elif system == "Darwin":
        info = _detect_macos(notes)
    else:
        info = _detect_linux(notes)

    arch = platform.machine()
    # 黑苹果只适用 x86。ARM（手机、Apple Silicon、树莓派）没有可用的 macOS
    # 驱动，也不是本工具的适用范围，这里显式标出来，避免用户白折腾。
    compatible = arch.lower() in ("x86_64", "amd64", "i386", "i686")
    if not compatible:
        notes.append(f"当前是 {arch}（ARM），黑苹果只支持 x86 电脑")

    return {
        "os": system,
        "arch": arch,
        "cpu": info.get("cpu") or "",
        "gpus": info.get("gpus") or [],
        "memory_gb": info.get("memory_gb") or 0,
        "storage": info.get("storage") or "",
        "platform": info.get("platform") or "desktop",
        "wifi": "",
        "compatible": compatible,
        "notes": notes,
    }


def to_hardware(d):
    """把检测结果转成 checker.Hardware。"""
    from .checker import Hardware
    storage = d.get("storage") or ""
    if storage not in ("nvme", "sata", "vmd", "raid"):
        storage = ""
    plat = d.get("platform") or "desktop"
    if plat not in ("laptop", "desktop", "server"):
        plat = "desktop"
    return Hardware(cpu=d.get("cpu") or "", gpus=list(d.get("gpus") or []),
                    wifi=d.get("wifi") or "", storage=storage, platform=plat)


if __name__ == "__main__":
    import json
    print(json.dumps(detect(), ensure_ascii=False, indent=2))
