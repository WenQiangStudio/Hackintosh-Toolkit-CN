#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容性数据表。

数据来源：OpCore-Simplify 的兼容性判定逻辑（BSD-3）、Dortania 官方指南、
以及 macOS 各版本实际驱动情况。判据是「macOS 有没有原生驱动」，不是「性能好不好」。

版本用 (major, minor) 元组表示：(10,13) = High Sierra， (12,2) = Monterey 12.2。
LATEST 跟着苹果当前的发行版本走，升级 macOS 时可以只改这一个常量。
"""

LATEST = (26, 0)  # macOS Tahoe

VERSION_NAMES = {
    (10, 13): "High Sierra",
    (10, 14): "Mojave",
    (10, 15): "Catalina",
    (11, 0): "Big Sur",
    (12, 0): "Monterey",
    (13, 0): "Ventura",
    (14, 0): "Sonoma",
    (15, 0): "Sequoia",
    (26, 0): "Tahoe",
}

# 状态
FULL = "full"            # 免驱，全功能
PARTIAL = "partial"      # 能用，但缺功能（比如没有隔空投送）
LEGACY = "legacy"        # 只能停在很老的系统
UNSUPPORTED = "unsupported"


def vname(v):
    if v is None:
        return "—"
    return VERSION_NAMES.get(v, f"{v[0]}.{v[1]}")


def vstr(v):
    if v is None:
        return "—"
    return f"{v[0]}.{v[1]}" if v[1] else f"{v[0]}"


class Rule:
    """一条硬件规则。pattern 是大小写不敏感的子串。"""

    def __init__(self, pattern, status, vmin=None, vmax=LATEST,
                 note="", vendor="", kind=""):
        self.pattern = pattern.lower()
        self.status = status
        self.vmin = vmin
        self.vmax = vmax
        self.note = note
        self.vendor = vendor
        self.kind = kind

    def hit(self, name):
        return self.pattern in (name or "").lower()

    def __repr__(self):
        return f"<Rule {self.pattern} {self.status}>"


# ---------------------------------------------------------------- 核显
IGPU_RULES = [
    # 11 代及以后：无驱动，必须排前面，否则会被老规则误命中
    Rule("iris xe", UNSUPPORTED, note="11 代及以后的核显在 macOS 没有驱动"),
    Rule("uhd 770", UNSUPPORTED, note="12 代核显，无驱动"),
    Rule("uhd 750", UNSUPPORTED, note="11/12 代核显，无驱动"),
    Rule("uhd 730", UNSUPPORTED, note="11/12 代核显，无驱动"),
    Rule("arc", UNSUPPORTED, note="Intel Arc 独显无驱动"),
    # 能驱动的：先写带 U 的，避免 "uhd 620" 被 "hd 620" 截胡
    Rule("uhd 630", FULL, (10, 13), LATEST, "Coffee Lake 核显，最成熟的一档"),
    Rule("uhd 620", FULL, (10, 13), LATEST, "Comet/Coffee Lake 核显，最成熟的一档"),
    Rule("iris plus", FULL, (10, 15), LATEST, "Ice Lake 核显，核显支持的最后一档"),
    Rule("hd 630", FULL, (10, 12), LATEST, "Kaby Lake 核显，免驱"),
    Rule("hd 620", FULL, (10, 12), LATEST, "Kaby Lake 核显，免驱"),
    Rule("hd 530", FULL, (10, 11), LATEST, "Skylake 核显，免驱"),
    Rule("iris 6000", LEGACY, None, (12, 0), "Broadwell 核显"),
    Rule("hd 5500", LEGACY, None, (12, 0), "Broadwell 核显"),
    Rule("hd 5000", LEGACY, None, (12, 0), "Broadwell 核显"),
    Rule("hd 4600", LEGACY, None, (12, 0), "Haswell 核显，Monterey 是原生上限"),
    Rule("hd 4400", LEGACY, None, (12, 0), "Haswell 核显，Monterey 是原生上限"),
    Rule("hd 4000", LEGACY, None, (11, 0), "Ivy Bridge 核显，Big Sur 之后要 OCLP 补丁"),
    Rule("hd 3000", LEGACY, None, (10, 13), "Sandy Bridge 核显，只能停在 High Sierra"),
]

# ---------------------------------------------------------------- 独显
DGPU_RULES = [
    # NVIDIA
    Rule("rtx", UNSUPPORTED, note="RTX 20/30/40/50 系永远没有 macOS 驱动"),
    Rule("gtx 16", UNSUPPORTED, note="GTX 16 系（Turing）无驱动"),
    Rule("gtx 10", LEGACY, None, (10, 13), "Pascal 只能到 High Sierra + Web Driver"),
    Rule("gtx 9", LEGACY, None, (10, 13), "Maxwell 只能到 High Sierra"),
    Rule("gtx 7", LEGACY, None, (11, 0), "Kepler 能到 Big Sur"),
    Rule("gtx 6", LEGACY, None, (11, 0), "Kepler 能到 Big Sur"),
    Rule("quadro", LEGACY, None, (10, 13), "专业卡同样受架构限制"),
    Rule("mx", UNSUPPORTED, note="MX 系列笔记本独显没有 macOS 驱动，装上也用不了"),
    # AMD
    Rule("rx 6", FULL, (12, 2), LATEST, "Navi 2x，Monterey 12.2 起免驱"),
    Rule("rx 5", FULL, (10, 15), LATEST, "Navi 1x / Polaris，免驱"),
    Rule("rx 4", FULL, (10, 13), LATEST, "Polaris，性价比之王"),
    Rule("vega", FULL, (10, 14), LATEST, "Vega 免驱"),
    Rule("radeon vii", FULL, (10, 14), LATEST, "Vega 20 免驱"),
    Rule("rx 7", UNSUPPORTED, note="RDNA3 无驱动"),
    Rule("wx", LEGACY, None, (12, 0), "专业卡看具体架构"),
]

# 需要更精细判断的（先匹配具体型号，再落到通用规则）
AMD_SPECIFIC = [
    # RDNA3 / Navi 24：明确不支持，必须排在通用规则前面
    Rule("rx 7900", UNSUPPORTED, note="RDNA3 无驱动"),
    Rule("rx 7800", UNSUPPORTED, note="RDNA3 无驱动"),
    Rule("rx 7700", UNSUPPORTED, note="RDNA3 无驱动"),
    Rule("rx 7600", UNSUPPORTED, note="RDNA3 无驱动"),
    Rule("rx 6500", UNSUPPORTED, note="Navi 24，虽然叫 RX 6 系但不支持，别买"),
    Rule("rx 6400", UNSUPPORTED, note="Navi 24，虽然叫 RX 6 系但不支持，别买"),
    # Navi 2x
    Rule("rx 6950", FULL, (11, 4), LATEST, "Navi 21 免驱"),
    Rule("rx 6900", FULL, (11, 4), LATEST, "Navi 21 免驱，性能强"),
    Rule("rx 6800", FULL, (11, 4), LATEST, "Navi 21 免驱，性能强"),
    Rule("rx 6750", FULL, (12, 2), LATEST, "Navi 22 免驱"),
    Rule("rx 6700", FULL, (12, 2), LATEST, "Navi 22 免驱"),
    Rule("rx 6650", FULL, (12, 2), LATEST, "Navi 23 免驱"),
    Rule("rx 6600", FULL, (12, 2), LATEST, "Navi 23 免驱"),
    # Navi 1x
    Rule("rx 5700", FULL, (10, 15), LATEST, "Navi 10 免驱"),
    Rule("rx 5600", FULL, (10, 15), LATEST, "Navi 10 免驱"),
    Rule("rx 5500", FULL, (10, 15), LATEST, "Navi 14 免驱"),
    # Polaris（3 位数）
    Rule("rx 590", FULL, (10, 13), LATEST, "Polaris，性价比之王"),
    Rule("rx 580", FULL, (10, 13), LATEST, "Polaris，性价比之王"),
    Rule("rx 570", FULL, (10, 13), LATEST, "Polaris"),
    Rule("rx 560", FULL, (10, 13), LATEST, "Polaris"),
    Rule("rx 550", FULL, (10, 13), LATEST, "Polaris"),
    Rule("rx 480", FULL, (10, 13), LATEST, "Polaris"),
    Rule("rx 470", FULL, (10, 13), LATEST, "Polaris"),
    Rule("rx 460", FULL, (10, 13), LATEST, "Polaris"),
]

# ---------------------------------------------------------------- 无线网卡
WIFI_RULES = [
    Rule("bcm94360", FULL, note="Broadcom，免驱，隔空投送/接力全功能"),
    Rule("bcm94352", PARTIAL, note="Broadcom，需要 kext，大部分功能可用"),
    Rule("bcm94350", PARTIAL, note="Broadcom，需要 kext"),
    Rule("ax210", PARTIAL, note="Intel，能上网；隔空投送不可用"),
    Rule("ax201", PARTIAL, note="Intel，能上网；隔空投送不可用"),
    Rule("ax200", PARTIAL, note="Intel，能上网；隔空投送不可用"),
    Rule("ax211", PARTIAL, note="Intel 新卡，看驱动版本，可能不稳"),
    Rule("9560", PARTIAL, note="Intel，能上网；隔空投送不可用"),
    Rule("9260", PARTIAL, note="Intel，能上网；隔空投送不可用"),
    Rule("8265", PARTIAL, note="Intel，能上网；隔空投送不可用"),
    Rule("8260", PARTIAL, note="Intel，能上网；隔空投送不可用"),
    Rule("realtek", UNSUPPORTED, note="多数 Realtek 无线无解，换卡或买 USB 网卡"),
    Rule("rtl8", UNSUPPORTED, note="Realtek 无线多数无解"),
    Rule("qualcomm", UNSUPPORTED, note="高通无线多数无解"),
    Rule("atheros", LEGACY, None, (11, 0), note="Atheros 不推荐"),
]

# ---------------------------------------------------------------- 有线网卡
ETH_RULES = [
    Rule("i219", FULL, note="Intel I219，IntelMausi.kext"),
    Rule("i225", PARTIAL, (10, 15), LATEST, note="Intel I225，需要补丁，Ventura 后基本可用"),
    Rule("i226", PARTIAL, (10, 15), LATEST, note="Intel I226，同 I225"),
    Rule("i210", FULL, note="Intel I210，基本免驱"),
    Rule("rtl8111", FULL, note="Realtek RTL8111，RealtekRTL8111.kext"),
    Rule("rtl8125", FULL, note="Realtek 2.5G，LucyRTL8125Ethernet.kext"),
    Rule("aquantia", PARTIAL, (11, 0), LATEST, note="万兆，Big Sur 起支持"),
    Rule("aQC107", PARTIAL, (11, 0), LATEST, note="万兆，Big Sur 起支持"),
]

# ---------------------------------------------------------------- 平台
INTEL_GEN_RULE = [
    # (代际关键词, 最低, 备注)
    (["core ultra", "ultra 5", "ultra 7", "ultra 9"], (10, 13), "Core Ultra 较新，补丁还不成熟"),
    (["14", "13", "12"], (10, 13), "12–14 代 CPU 支持，但核显无解，要配 A 卡"),
    (["11"], (10, 13), "11 代 CPU 支持，核显无解"),
    (["10", "ice lake"], (10, 13), "10 代是最舒服的一档"),
    (["8", "9", "coffee", "comet"], (10, 13), "8–9 代，社区验证最充分"),
    (["6", "7", "skylake", "kaby"], (10, 11), "6–7 代，稳定但系统偏老"),
    (["4", "5", "haswell", "broadwell"], (10, 8), "4–5 代，只能到 Monterey"),
    (["2", "3", "sandy", "ivy"], (10, 6), "2–3 代，系统很老"),
]


def lookup(rules, name):
    """按顺序返回第一条命中的规则。"""
    for r in rules:
        if r.hit(name):
            return r
    return None


def lookup_gpu(name):
    """独显有多条通用规则，先看具体型号表。"""
    n = (name or "").lower()
    if "rx" in n or "radeon" in n:
        r = lookup(AMD_SPECIFIC, name)
        if r:
            return r
    return lookup(IGPU_RULES, name) or lookup(DGPU_RULES, name)
