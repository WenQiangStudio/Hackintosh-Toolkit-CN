#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BIOS 设置清单与故障速查的短版数据。

长版在 docs/ 里；这里只放命令行需要的高频内容。
"""

# 进入方式与必改项
BIOS = {
    "lenovo": {
        "name": "联想 / ThinkPad",
        "enter": "F2 或 Fn+F2（ThinkPad 是 F1）",
        "boot_menu": "F12",
        "items": [
            ("Security → Secure Boot", "Disabled", "不关引导直接被拦"),
            ("Startup → UEFI/Legacy Boot", "UEFI Only", "macOS 只支持纯 UEFI"),
            ("Config → Storage → AHCI", "AHCI", "RAID/RST 下看不到硬盘"),
            ("Intel VMD Controller", "Disabled", "11 代以后常见"),
            ("Security → I/O Port Access → Fingerprint", "Disabled", "指纹在 macOS 无解"),
        ],
    },
    "dell": {
        "name": "戴尔",
        "enter": "F2",
        "boot_menu": "F12",
        "items": [
            ("Boot Settings → Secure Boot", "Disabled", "必关"),
            ("SATA Operation", "AHCI", "不能是 RAID On"),
            ("Fast Boot", "Disabled", "会跳过 USB 初始化"),
            ("TPM", "保留", "关了可能触发 BitLocker 恢复"),
        ],
    },
    "hp": {
        "name": "惠普",
        "enter": "F10（开机先连按 Esc）",
        "boot_menu": "F9",
        "items": [
            ("Secure Boot Configuration", "Disabled", "商用机先关 Sure Start"),
            ("Legacy Support", "Disabled", "纯 UEFI"),
            ("SATA Mode", "AHCI", ""),
        ],
    },
    "asus": {
        "name": "华硕",
        "enter": "Del 或 F2",
        "boot_menu": "F8 / Esc",
        "items": [
            ("Boot → CSM", "Disabled", "纯 UEFI"),
            ("Advanced → System Agent → VT-d", "Disabled", "减少干扰"),
            ("Above 4G Decoding", "Enabled", "A 卡不亮常见原因"),
            ("Secure Boot", "Disabled", "部分主板要先设管理员密码"),
        ],
    },
    "msi": {
        "name": "微星",
        "enter": "Del",
        "boot_menu": "F11",
        "items": [
            ("MSI Fast Boot", "Disabled", "微星特有，必须关"),
            ("Windows OS Configuration → WHQL", "Disabled", ""),
            ("CSM", "Disabled", ""),
            ("Above 4G Decoding", "Enabled", ""),
        ],
    },
    "gigabyte": {
        "name": "技嘉",
        "enter": "Del",
        "boot_menu": "F12",
        "items": [
            ("Boot → CSM Support", "Disabled", ""),
            ("Peripherals → Above 4G Decoding", "Enabled", ""),
            ("SATA Mode", "AHCI", ""),
        ],
    },
    "supermicro": {
        "name": "超微服务器",
        "enter": "Del",
        "boot_menu": "F11",
        "items": [
            ("Boot Mode", "UEFI", "不能是 Legacy"),
            ("SATA Configuration", "AHCI", "不是 RAID"),
            ("Serial Port", "Disabled", "会卡住"),
            ("Above 4G Decoding", "Enabled", ""),
            ("IPMI → Fan Mode", "调低", "否则风扇全速"),
        ],
    },
}

COMMON = [
    ("Secure Boot", "Disabled", "最高优先级"),
    ("Fast Boot", "Disabled", "U 盘识别不到时先查这个"),
    ("CSM / Legacy", "Disabled", "macOS 只支持 UEFI"),
    ("SATA / Storage", "AHCI", "RAID/RST/VMD 都看不到盘"),
    ("Above 4G Decoding", "Enabled", "A 卡黑屏的常见原因"),
    ("Re-Size BAR", "Disabled", "开了容易黑屏"),
    ("VT-d / IOMMU", "Disabled", "减少干扰"),
    ("Serial Port", "Disabled", "会占用资源"),
]

# 现象 → 原因 → 处理
TROUBLES = [
    {
        "symptom": "卡在苹果 logo，进度条不动",
        "cause": "早期初始化失败：USB 没映射 / 显卡没加载 / ACPI 有问题",
        "fix": ["加 -v 看最后几行", "换主板后置 USB 2.0 口", "先试 -x 安全模式"],
    },
    {
        "symptom": "进度条走完黑屏",
        "cause": "系统起来了但显示没切过来",
        "fix": ["换接口（DP ↔ HDMI）", "换线", "核显加 igfxonln=1", "独显接核显输出时确认线插对了"],
    },
    {
        "symptom": "出现禁行符号 ⊘",
        "cause": "找不到可启动的根设备：硬盘控制器没驱动",
        "fix": ["BIOS 关 VMD / RST，改 AHCI", "系统盘别接 RAID 卡", "U 盘换 USB 2.0 口"],
    },
    {
        "symptom": "磁盘工具看不到硬盘",
        "cause": "存储控制器模式不对",
        "fix": ["AHCI 而不是 RAID/RST/VMD", "磁盘工具左上角点「显示所有设备」", "杂牌 NVMe 试 NVMeFix.kext"],
    },
    {
        "symptom": "提示无法安装在此电脑上",
        "cause": "SMBIOS 选的机型和系统版本对不上",
        "fix": ["重跑 OpCore 让它重选 SMBIOS", "或换同代 SystemProductName", "临时可加 -no_compat_check"],
    },
    {
        "symptom": "装完进不去系统",
        "cause": "EFI 没放对，或硬盘引导和 U 盘引导不一致",
        "fix": ["先用 U 盘引导，菜单里选硬盘上的 macOS", "能把 U 盘 EFI 重新拷一次"],
    },
    {
        "symptom": "没有声音",
        "cause": "AppleALC 的 layout-id 不对",
        "fix": ["查 AppleALC 支持列表", "boot-arg 加 alcid=编号 试", "实在不行用 USB 声卡"],
    },
    {
        "symptom": "键鼠失灵 / 要插拔才认",
        "cause": "USB 端口没有映射",
        "fix": ["USBToolBox 扫描所有口，生成 USBPorts.kext", "删掉 USBInjectAll"],
    },
    {
        "symptom": "一睡就醒 / 睡不醒",
        "cause": "USB 或 RTC 在捣乱",
        "fix": ["先做 USB 映射", "关「唤醒以供网络访问」", "BIOS 关 ErP / Wake on LAN"],
    },
    {
        "symptom": "分辨率只有 1024×768",
        "cause": "显卡驱动没生效，系统在用 VESA 兜底",
        "fix": ["确认 WhateverGreen 已加载", "核显设对 ig-platform-id", "显示器直连，别用转接头"],
    },
]
