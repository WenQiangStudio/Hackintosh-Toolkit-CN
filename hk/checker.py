#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""判定引擎：给一组硬件，回答「能不能装、装到哪个版本、卡在哪」。

判据只有三条：
  1. 有没有**能驱动显示**的显卡——这是硬门槛，没有就装不了。
  2. 能驱动的那块卡支持到哪个 macOS 版本。
  3. 有没有结构性阻塞（VMD/RAID、机型不支持等），有就先把阻塞去掉。

性能好不好、驱动全不全，是第二层的事，放在 warn 里说。
"""

from dataclasses import dataclass, field

from . import data
from .data import FULL, LEGACY, PARTIAL, UNSUPPORTED

OK = "ok"
WARN = "warn"
FAIL = "fail"


@dataclass
class Hardware:
    cpu: str = ""
    gpus: list = field(default_factory=list)
    wifi: str = ""
    ethernet: str = ""
    storage: str = ""          # nvme / sata / vmd / raid
    platform: str = "laptop"   # laptop / desktop / server


@dataclass
class Finding:
    level: str
    part: str
    title: str
    detail: str = ""
    fix: str = ""

    def line(self):
        mark = {OK: "✅", WARN: "⚠️", FAIL: "❌"}[self.level]
        return f"{mark} {self.part}｜{self.title}"


@dataclass
class Verdict:
    hardware: Hardware
    findings: list = field(default_factory=list)
    macos: tuple = None          # (lo, hi)
    recommended: tuple = None
    headline: str = ""

    @property
    def ok(self):
        return not any(f.level == FAIL for f in self.findings)

    @property
    def fails(self):
        return [f for f in self.findings if f.level == FAIL]

    @property
    def warns(self):
        return [f for f in self.findings if f.level == WARN]


def _is_amd(cpu):
    c = (cpu or "").lower()
    return any(k in c for k in ("ryzen", "athlon", "threadripper", "epyc", "amd"))


def _cpu_floor(cpu):
    """CPU 侧能支撑的最低系统。返回 (最低版本, 备注)。"""
    if _is_amd(cpu):
        c = (cpu or "").lower()
        if "epyc" in c:
            return None, "EPYC 平台 macOS 基本不支持"
        return (10, 13), "AMD CPU 要打内核补丁，Adobe / 虚拟化可能不稳"
    c = (cpu or "").lower()
    for keys, floor, note in data.INTEL_GEN_RULE:
        if any(k in c for k in keys):
            return floor, note
    return (10, 13), ""


def _better(a, b):
    return a if a >= b else b


def _worse(a, b):
    return a if a <= b else b


def check(hw: Hardware) -> Verdict:
    v = Verdict(hardware=hw)

    # ---------------- CPU
    if not hw.cpu:
        v.findings.append(Finding(WARN, "CPU", "没有提供型号", "只按显卡判定，版本区间可能偏宽"))
        cpu_floor, cpu_note = (10, 13), ""
    else:
        cpu_floor, cpu_note = _cpu_floor(hw.cpu)
        if cpu_floor is None:
            v.findings.append(Finding(FAIL, "CPU", hw.cpu, cpu_note))
        elif _is_amd(hw.cpu):
            v.findings.append(Finding(WARN, "CPU", f"{hw.cpu}：需要 AMD Vanilla 补丁", cpu_note))
        else:
            v.findings.append(Finding(OK, "CPU", hw.cpu, cpu_note or "架构受支持"))

    # ---------------- 显卡（决定成败）
    supported, unsupported, unknown = [], [], []
    if not hw.gpus:
        v.findings.append(Finding(WARN, "显卡", "没有提供型号", "显卡是硬门槛，请补充"))
    for g in hw.gpus:
        rule = data.lookup_gpu(g)
        if rule is None:
            unknown.append(g)
        elif rule.status in (FULL, PARTIAL, LEGACY):
            supported.append((g, rule))
        else:
            unsupported.append((g, rule))

    for g, rule in supported:
        level = OK if rule.status == FULL else WARN
        tip = rule.note or ("免驱" if rule.status == FULL else "需要额外 kext")
        limit = "" if rule.vmax == data.LATEST else f"最高到 {data.vname(rule.vmax)}"
        v.findings.append(Finding(level, "显卡", g, tip, limit))

    # 没有可用显卡时才致命；有可用显卡时，无解的那块只是要被禁用
    for g, rule in unsupported:
        if supported:
            v.findings.append(Finding(WARN, "显卡", f"{g}（将被禁用）", rule.note,
                                      "在 EFI 里加 disable-gpu，不影响核显输出"))
        else:
            v.findings.append(Finding(FAIL, "显卡", g, rule.note or "无 macOS 驱动",
                                      "换一张能驱动的卡，或换机器"))
    for g in unknown:
        if supported:
            v.findings.append(Finding(WARN, "显卡", f"{g}（型号未识别）", "按无驱动处理，会被禁用"))
        else:
            v.findings.append(Finding(FAIL, "显卡", g, "型号没识别，无法判断是否有驱动",
                                      "用 OpCore-Simplify 导出硬件报告再核对"))

    # 版本窗口：取能驱动的那块卡
    if supported:
        best = max(supported, key=lambda x: x[1].vmax)
        gpu_name, gpu_rule = best
        lo = _better(cpu_floor or (10, 13), gpu_rule.vmin or (10, 6))
        hi = gpu_rule.vmax or data.LATEST
        v.macos = (lo, hi)
        v.recommended = hi if hi != data.LATEST else data.LATEST
        if lo > hi:
            v.findings.append(Finding(FAIL, "版本", f"无交集：最低 {data.vstr(lo)}，最高 {data.vstr(hi)}"))
    else:
        v.macos = None

    # ---------------- 结构性阻塞
    st = (hw.storage or "").lower()
    if st == "vmd":
        v.findings.append(Finding(FAIL, "存储", "Intel VMD / RST 模式",
                                  "这个模式下 macOS 安装器看不到硬盘",
                                  "进 BIOS 把 SATA/Storage 改成 AHCI"))
    elif st == "raid":
        v.findings.append(Finding(FAIL, "存储", "RAID / 阵列卡",
                                  "阵列卡在 macOS 下没有驱动",
                                  "系统盘接主板板载 SATA，或换 AHCI 扩展卡"))
    elif st in ("nvme", "sata"):
        v.findings.append(Finding(OK, "存储", st.upper(), "接口类型没问题"))
    elif st:
        v.findings.append(Finding(WARN, "存储", st, "没识别的存储类型"))

    # ---------------- 无线
    if hw.wifi:
        rule = data.lookup(data.WIFI_RULES, hw.wifi)
        if rule is None:
            v.findings.append(Finding(WARN, "无线", hw.wifi, "型号没识别，按无解处理"))
        elif rule.status == UNSUPPORTED:
            v.findings.append(Finding(WARN, "无线", hw.wifi, rule.note,
                                      "换 BCM94360 系列，或用 USB 无线网卡"))
        elif rule.status == FULL:
            v.findings.append(Finding(OK, "无线", hw.wifi, rule.note))
        else:
            v.findings.append(Finding(WARN, "无线", hw.wifi, rule.note,
                                      "想要隔空投送/接力就换 Broadcom 卡"))

    # ---------------- 机型特判
    if hw.platform == "laptop":
        has_nvidia = any("nvidia" in g.lower() or "rtx" in g.lower() or "gtx" in g.lower()
                         or "mx" in g.lower() for g in hw.gpus)
        if has_nvidia and supported:
            v.findings.append(Finding(WARN, "机型", "笔记本 + 独立显卡",
                                      "独显在笔记本上基本无法驱动，只能用核显",
                                      "BIOS 切混合模式，显示器接核显输出"))
        if not supported and hw.gpus:
            v.findings.append(Finding(FAIL, "机型", "笔记本没有可用显卡",
                                      "多数游戏本是独显直连，核显没接屏幕",
                                      "BIOS 里切回混合模式；切不了就装不了"))
    elif hw.platform == "server":
        v.findings.append(Finding(WARN, "机型", "服务器",
                                  "没有核显，必须插免驱 A 卡；阵列卡不认",
                                  "见 docs/04-server.md"))
        if supported:
            v.findings.append(Finding(OK, "机型", "已检测到可用独显", "服务器档可行"))

    # ---------------- 结论
    if not v.ok:
        v.headline = "装不了（或先解决下面的阻塞项）"
    elif v.macos:
        lo, hi = v.macos
        if lo == hi:
            v.headline = f"可以装，建议 macOS {data.vname(hi)} {data.vstr(hi)}"
        else:
            v.headline = f"可以装，建议 macOS {data.vname(hi)}；范围 {data.vstr(lo)} – {data.vstr(hi)}"
    else:
        v.headline = "信息不足，先补齐显卡型号"
    return v
