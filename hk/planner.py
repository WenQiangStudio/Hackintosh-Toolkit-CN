#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""安装计划生成：按机型和判定结果，列出该做的步骤和每步的验收标准。

不是把文档抄一遍，而是**按你的情况裁剪**——比如电池那一节只有笔记本才有，
iDRAC 只有服务器才有，独显无解才提醒禁用。
"""

from . import data
from .checker import FAIL, WARN


def _has_laptop_stuff(v):
    return v.hardware.platform == "laptop"


def build(v):
    """返回 [{'title','why','actions':[...],'done':...}]。"""
    hw = v.hardware
    steps = []

    steps.append({
        "title": "备份，把目标硬盘腾出来",
        "why": "分区和格式化几乎不可逆。这一步做错，后面每一步都是白费。",
        "actions": [
            "重要文件拷到另一块硬盘或云盘",
            "确认目标硬盘上有多少要保留的数据",
            "台式机建议另备一块 SSD 专装 macOS，和 Windows 物理隔离",
        ],
        "done": "目标盘上没有任何「丢了会心疼」的文件",
    })

    steps.append({
        "title": "跑 OpCore-Simplify，导出硬件报告",
        "why": "它读的是你机器的真实硬件，比手填准确。后面的判断都基于这份报告。",
        "actions": [
            "双击 tools/OpCore-Simplify/OpCore-Simplify.bat",
            "菜单选 E. Export hardware report",
            "看输出里的兼容性列表，记下哪些是 Supported / Not supported",
        ],
        "done": "拿到 Report.json，且显卡一行是 Supported（或已确认要禁用它）",
    })

    gpu_hint = ""
    bad = [g for g in hw.gpus if any(k in g.lower() for k in ("rtx", "gtx", "mx", "rx 6"))]
    if bad:
        gpu_hint = "报告里无解的那块卡，确认 OpCore 给它加了 disable-gpu"
    steps.append({
        "title": "生成 EFI",
        "why": "EFI 决定了能不能引导、能不能点亮屏幕，是整个流程的核心产物。",
        "actions": [
            "OpCore 里选它推荐的 macOS 版本，第一次不要改 ACPI / kext",
            "选 Build OpenCore EFI，等它联网下载 OpenCorePkg 和 kext",
            "把生成出来的 EFI 文件夹单独拷一份收好",
        ],
        "done": "有一个完整的 EFI 文件夹（含 BOOT/ 和 OC/）",
        "note": gpu_hint,
    })

    steps.append({
        "title": "做启动 U 盘",
        "why": "U 盘要同时装引导和恢复镜像，缺一个都进不去安装器。",
        "actions": [
            "U 盘格式化成 FAT32，单个分区",
            "把 EFI 文件夹放到 U 盘根目录",
            "用 macrecovery 下恢复镜像，把 com.apple.recovery.boot 放到根目录",
        ],
        "done": "U 盘根目录同时有 EFI/ 和 com.apple.recovery.boot/",
    })

    bios_extra = []
    if hw.platform == "laptop":
        bios_extra.append("关掉指纹相关的 I/O 选项（装不上也用不了）")
    if hw.platform == "server":
        bios_extra.append("Boot Mode 设成 UEFI，SATA 设成 AHCI，关串口")
    steps.append({
        "title": "改 BIOS",
        "why": "安全启动拦引导，VMD/RST 让安装器看不到硬盘。这两项是最高频的翻车点。",
        "actions": [
            "Secure Boot → Disabled",
            "SATA / Storage → AHCI（不是 RAID / RST / VMD）",
            "Above 4G Decoding → Enabled",
            "CSM → Disabled",
            "VT-d → Disabled（装完可再开）",
        ] + bios_extra,
        "done": "U 盘在启动菜单里以 UEFI: 开头出现",
    })

    steps.append({
        "title": "进安装器装系统",
        "why": "到这一步硬件基本都通了，剩下的主要是耐心。",
        "actions": [
            "启动菜单选 U 盘，进 OpenCore，选 macOS Base System",
            "磁盘工具 → 显示所有设备 → 抹掉目标盘（APFS / GUID）",
            "装 macOS，中途重启几次，每次都选「macOS Installer」",
        ],
        "done": "能进到桌面",
    })

    steps.append({
        "title": "把 EFI 挪到硬盘",
        "why": "现在系统还依赖 U 盘引导，拔了盘就起不来。",
        "actions": [
            "给硬盘 ESP 分区分配盘符（DiskGenius 或 diskpart）",
            "把 U 盘的 EFI 拷进去，不要覆盖已有的 Microsoft 文件夹",
            "BIOS 里把 OpenCore 调到启动项第一位",
        ],
        "done": "拔掉 U 盘也能正常开机进 macOS",
    })

    finish = ["声卡：AppleALC + 正确的 layout-id",
              "网络：按网卡型号装对应 kext",
              "USB：用 USBToolBox 做端口映射（顺便修睡眠）"]
    if _has_laptop_stuff(v):
        finish += ["电池：SMCBatteryManager，看电量是否正常",
                   "触摸板：I2C 机型需要 VoodooI2C",
                   "亮度：SSDT-PNLF + BrightnessKeys"]
    if hw.platform == "desktop":
        finish.append("双系统：Windows 时间会差 8 小时，改 RealTimeIsUniversal")
    if hw.platform == "server":
        finish += ["风扇：iDRAC / iLO 里调低，否则全速噪音",
                   "关自动更新，服务器稳定优先"]
    steps.append({
        "title": "安装后收尾",
        "why": "能进桌面只完成了 60%，驱动不齐会很别扭。",
        "actions": finish,
        "done": "声音、网络、睡眠都正常，且 EFI 有备份",
    })

    return steps


def summary_lines(v):
    """一句话摘要，给 CLI 用。"""
    out = [v.headline]
    if v.macos:
        lo, hi = v.macos
        out.append(f"版本窗口：{data.vstr(lo)} – {data.vstr(hi)}")
    if v.fails:
        out.append(f"阻塞项 {len(v.fails)} 个，先解决再往下走")
    elif v.warns:
        out.append(f"提醒 {len(v.warns)} 条，不影响安装但会影响体验")
    return out
