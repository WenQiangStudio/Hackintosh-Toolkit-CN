#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hk 命令行入口。

    python -m hk check   --cpu i5-10210U --gpu "UHD 620" --gpu MX250 --wifi AX201 --storage nvme
    python -m hk plan    --platform laptop --cpu ... --gpu ...
    python -m hk bios    --vendor lenovo
    python -m hk troubleshoot [关键词]
    python -m hk matrix
"""

import argparse
import json
import sys

from . import __version__, bios, data, planner
from .checker import FAIL, WARN, Hardware, check

_COLOR = sys.stdout.isatty()


def _c(text, code):
    return f"\033[{code}m{text}\033[0m" if _COLOR else text


def _kw(text, code=36):
    return _c(text, code)


def _build_hw(a):
    return Hardware(cpu=a.cpu or "", gpus=a.gpu or [], wifi=a.wifi or "",
                    ethernet=a.ethernet or "", storage=a.storage or "",
                    platform=a.platform)


def _print_verdict(v, as_json=False):
    if as_json:
        print(json.dumps({
            "ok": v.ok,
            "headline": v.headline,
            "macos": list(v.macos) if v.macos else None,
            "findings": [{"level": f.level, "part": f.part, "title": f.title,
                          "detail": f.detail, "fix": f.fix} for f in v.findings],
        }, ensure_ascii=False, indent=2))
        return

    print()
    print(_c("判定结果", 1))
    print("  " + _c(v.headline, 32 if v.ok else 31))
    print()
    for f in v.findings:
        mark = {"ok": _c("✅", 32), "warn": _c("⚠️ ", 33), "fail": _c("❌", 31)}[f.level]
        print(f"  {mark} {f.part}｜{f.title}")
        if f.detail:
            print(f"      {f.detail}")
        if f.fix:
            print(f"      → {f.fix}")

    if v.fails:
        print()
        print(_c("先解决这些，再谈安装：", 31))
        for f in v.fails:
            print(f"  · {f.title}" + (f"：{f.fix}" if f.fix else ""))
    elif v.macos:
        print()
        lo, hi = v.macos
        print(f"  建议系统：{_c(data.vname(hi), 36)}（{data.vstr(lo)} – {data.vstr(hi)} 之间都行）")
        extra = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        print("  下一步：python -m hk plan " + extra)


def cmd_check(a):
    _print_verdict(check(_build_hw(a)), a.json)


def cmd_plan(a):
    v = check(_build_hw(a))
    steps = planner.build(v)

    if a.json:
        print(json.dumps({"verdict": v.headline, "steps": steps},
                         ensure_ascii=False, indent=2))
        return

    print()
    print(_c("安装计划", 1))
    for line in planner.summary_lines(v):
        print("  " + line)
    if v.fails:
        print()
        print(_c("注意：下面有阻塞项，先把它们解决掉再按计划走。", 31))
        for f in v.fails:
            print(f"  · {f.title} → {f.fix}")

    for i, s in enumerate(steps, 1):
        print()
        print(_c(f"{i}. {s['title']}", 1))
        print(f"   为什么：{s['why']}")
        for act in s["actions"]:
            print(f"   · {act}")
        if s.get("note"):
            print(f"   {_c('提示', 33)}：{s['note']}")
        print(f"   {_c('完成标准', 32)}：{s['done']}")


def cmd_bios(a):
    key = (a.vendor or "").lower()
    entry = bios.BIOS.get(key)
    if a.vendor and not entry:
        print(f"没有这个品牌的预设：{a.vendor}")
        print("可用：" + "、".join(bios.BIOS.keys()))
        print("通用项仍然适用：")
        entry = None
    if entry:
        print()
        print(_c(entry["name"], 1))
        print(f"  进 BIOS：{entry['enter']}    启动菜单：{entry['boot_menu']}")
        for item, val, why in entry["items"]:
            print(f"  · {item} → {_c(val, 32)}" + (f"（{why}）" if why else ""))
    print()
    print(_c("所有机型都要改的", 1))
    for item, val, why in bios.COMMON:
        print(f"  · {item} → {_c(val, 32)}" + (f"（{why}）" if why else ""))


def cmd_troubleshoot(a):
    kws = " ".join(a.keyword or []).strip()
    rows = bios.TROUBLES
    if kws:
        rows = [r for r in rows if kws in r["symptom"] or kws in r["cause"]
                or any(kws in f for f in r["fix"])]
    if not rows:
        print(f"没找到和「{kws}」相关的条目。试试更短的关键词，比如「黑屏」「禁行」「声」。")
        return
    for r in rows:
        print()
        print(_c("▸ " + r["symptom"], 1))
        print(f"  原因：{r['cause']}")
        for f in r["fix"]:
            print(f"  · {f}")


def cmd_matrix(a):
    groups = [("核显", data.IGPU_RULES), ("独显", data.DGPU_RULES)]
    for title, rules in groups:
        print()
        print(_c(title, 1))
        for r in rules:
            if r.vmax == data.LATEST and r.status == data.FULL:
                span = "免驱（最新）"
            elif r.vmax == data.LATEST:
                span = f"{data.vstr(r.vmin)} 起"
            elif r.vmin:
                span = f"{data.vstr(r.vmin)} – {data.vstr(r.vmax)}"
            else:
                span = f"止于 {data.vstr(r.vmax)}"
            print(f"  {r.pattern:14s} {span:22s} {r.note}")


def cmd_usb(a):
    steps = [
        "U 盘 ≥ 16GB，USB 3.0 更好（会被完全格式化）",
        "格式化成 FAT32，单个分区，分配单元 4096",
        "把 EFI 文件夹放到根目录",
        "下载 OpenCorePkg，进 Utilities/macrecovery，执行：",
        "    python macrecovery.py -b Mac-E43C1C25D4880AD6 -m 00000000000000000 -os latest download",
        "把生成的 com.apple.recovery.boot 文件夹放到 U 盘根目录",
        "拔盘前确认：根目录同时有 EFI/ 和 com.apple.recovery.boot/",
    ]
    print()
    print(_c("制作启动 U 盘", 1))
    for i, s in enumerate(steps, 1):
        print(f"  {i}. {s}" if not s.startswith("    ") else s)
    print()
    print("  提示：有 Mac 的话可以直接用完整安装器，不用联网：")
    print("  sudo /Applications/Install\\ macOS\\ Sonoma.app/Contents/Resources/createinstallmedia --volume /Volumes/USB")


def cmd_detect(a):
    from .detect import detect, to_hardware

    d = detect()
    print()
    print(_c("自动检测结果", 1))
    rows = [("系统", f"{d.get('os')} / {d.get('arch')}"),
            ("CPU", d.get("cpu") or "未检测到"),
            ("显卡", ", ".join(d.get("gpus") or []) or "未检测到"),
            ("内存", f"{d.get('memory_gb')} GB" if d.get("memory_gb") else "未检测到"),
            ("存储", d.get("storage") or "未检测到"),
            ("机型", d.get("platform"))]
    for k, v in rows:
        print(f"  {k:6s}{v}")
    for n in d.get("notes") or []:
        print(f"  {_c('提示', 33)}：{n}")

    if not a.no_check:
        v = check(to_hardware(d))
        print()
        print("  " + _c(v.headline, 32 if v.ok else 31))
        for f in v.findings:
            mark = {"ok": _c("✅", 32), "warn": _c("⚠️ ", 33), "fail": _c("❌", 31)}[f.level]
            print(f"  {mark} {f.part}｜{f.title}")


def cmd_doctor(a):
    from . import doctor

    items = doctor.run(with_network=not a.offline)
    print()
    print(_c("环境体检", 1))
    for it in items:
        mark = {"ok": _c("✅", 32), "warn": _c("⚠️ ", 33), "fail": _c("❌", 31)}[it["level"]]
        line = f"  {mark} {it['title']}"
        if it["detail"]:
            line += f"：{it['detail']}"
        print(line)
        if it["fix"]:
            print(f"       → {it['fix']}")
    print()
    print("  " + doctor.summary(items))


def cmd_auto(a):
    from . import auto as auto_mod

    print(_c("正在检测硬件…", 36))
    result = auto_mod.run(write_report=not a.no_report, with_network=a.network)
    d = result["detected"]
    v = result["verdict"]

    print()
    print(_c("检测到", 1))
    print(f"  {d.get('os')} / {d.get('arch')}　{d.get('cpu') or 'CPU 未识别'}")
    print(f"  显卡：{', '.join(d.get('gpus') or []) or '未识别'}")
    print(f"  内存：{d.get('memory_gb') or '?'} GB　存储：{d.get('storage') or '未识别'}")

    print()
    print(_c("结论", 1))
    print("  " + _c(v["headline"], 32 if v["ok"] else 31))
    for f in v["findings"]:
        if f["level"] == "ok":
            continue
        mark = _c("⚠️ ", 33) if f["level"] == "warn" else _c("❌", 31)
        print(f"  {mark} {f['part']}｜{f['title']}" + (f" → {f['fix']}" if f["fix"] else ""))

    print()
    print(f"安装计划共 {len(result['steps'])} 步，环境体检：{doctor_summary(result['env'])}")
    if result["report"]:
        print(f"报告已写入：{_c(result['report'], 36)}")


def doctor_summary(items):
    from . import doctor as d
    return d.summary(items)


def cmd_serve(a):
    from .server import serve as serve_ui
    serve_ui(host=a.host, port=a.port, open_browser=a.open)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="hk", description="黑苹果可行性判定与安装计划（离线、零依赖）")
    ap.add_argument("--version", action="version", version=f"hk {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_hw(p):
        p.add_argument("--cpu", help="CPU 型号，如 i5-10210U")
        p.add_argument("--gpu", action="append", help="显卡型号，可重复：--gpu 'UHD 620' --gpu RTX3060")
        p.add_argument("--wifi", help="无线网卡，如 AX201 / BCM94360")
        p.add_argument("--ethernet", help="有线网卡")
        p.add_argument("--storage", choices=["nvme", "sata", "vmd", "raid"], help="存储模式")
        p.add_argument("--platform", choices=["laptop", "desktop", "server"], default="laptop")

    p_check = sub.add_parser("check", help="判定能不能装")
    add_hw(p_check)
    p_check.add_argument("--json", action="store_true")
    p_check.set_defaults(func=cmd_check)

    p_plan = sub.add_parser("plan", help="生成安装计划")
    add_hw(p_plan)
    p_plan.add_argument("--json", action="store_true")
    p_plan.set_defaults(func=cmd_plan)

    p_bios = sub.add_parser("bios", help="BIOS 设置清单")
    p_bios.add_argument("--vendor", help="lenovo / dell / hp / asus / msi / gigabyte / supermicro")
    p_bios.set_defaults(func=cmd_bios)

    p_tr = sub.add_parser("troubleshoot", help="按现象查故障")
    p_tr.add_argument("keyword", nargs="*")
    p_tr.set_defaults(func=cmd_troubleshoot)

    p_m = sub.add_parser("matrix", help="兼容性速查")
    p_m.set_defaults(func=cmd_matrix)

    p_u = sub.add_parser("usb", help="U 盘制作清单")
    p_u.set_defaults(func=cmd_usb)

    p_d = sub.add_parser("detect", help="自动检测本机硬件")
    p_d.add_argument("--no-check", action="store_true", help="只检测，不判定")
    p_d.set_defaults(func=cmd_detect)

    p_doc = sub.add_parser("doctor", help="环境体检")
    p_doc.add_argument("--offline", action="store_true", help="跳过网络检查")
    p_doc.set_defaults(func=cmd_doctor)

    p_a = sub.add_parser("auto", help="一键：检测 + 判定 + 计划 + 报告")
    p_a.add_argument("--no-report", action="store_true", help="不写报告文件")
    p_a.add_argument("--network", action="store_true", help="体检时也检查网络")
    p_a.set_defaults(func=cmd_auto)

    p_s = sub.add_parser("serve", help="启动本地 Web 界面")
    p_s.add_argument("--host", default="127.0.0.1")
    p_s.add_argument("--port", type=int, default=8765)
    p_s.add_argument("--open", action="store_true", help="自动打开浏览器")
    p_s.set_defaults(func=cmd_serve)

    args = ap.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
