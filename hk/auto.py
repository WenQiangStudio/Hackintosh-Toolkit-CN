#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键流程：检测 → 判定 → 计划 → 出报告。

给不想一步步敲命令的人用的。跑完在 `reports/` 下留一份 Markdown，
可以直接发给别人看，或者打印出来照着做。
"""

import time
from pathlib import Path

from . import data, detect, doctor, planner
from .checker import check

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports"


def render_markdown(d, verdict, steps, env):
    lines = []
    lines.append("# 黑苹果可行性报告")
    lines.append("")
    lines.append(f"> 生成时间：{time.strftime('%Y-%m-%d %H:%M')}　"
                 f"工具：hk {__import__('hk').__version__}")
    lines.append("")

    lines.append("## 检测到的硬件")
    lines.append("")
    lines.append("| 项目 | 值 |")
    lines.append("| --- | --- |")
    lines.append(f"| 系统 | {d.get('os')} / {d.get('arch')} |")
    lines.append(f"| CPU | {d.get('cpu') or '未检测到'} |")
    lines.append(f"| 显卡 | {', '.join(d.get('gpus') or []) or '未检测到'} |")
    lines.append(f"| 内存 | {d.get('memory_gb') or '?'} GB |")
    lines.append(f"| 存储接口 | {d.get('storage') or '未检测到'} |")
    lines.append(f"| 机型 | {d.get('platform')} |")
    lines.append("")

    lines.append("## 结论")
    lines.append("")
    lines.append(f"**{verdict.headline}**")
    lines.append("")
    if verdict.macos:
        lo, hi = verdict.macos
        lines.append(f"版本窗口：{data.vstr(lo)} – {data.vstr(hi)}"
                     f"（{data.vname(lo)} – {data.vname(hi)}）")
        lines.append("")

    lines.append("## 逐项检查")
    lines.append("")
    lines.append("| 结论 | 部位 | 说明 | 处理 |")
    lines.append("| --- | --- | --- | --- |")
    icon = {"ok": "✅", "warn": "⚠️", "fail": "❌"}
    for f in verdict.findings:
        detail = (f.detail or "").replace("|", "\\|")
        fix = (f.fix or "").replace("|", "\\|")
        lines.append(f"| {icon[f.level]} | {f.part}｜{f.title} | {detail} | {fix} |")
    lines.append("")

    if steps:
        lines.append("## 安装计划")
        lines.append("")
        for i, s in enumerate(steps, 1):
            lines.append(f"### {i}. {s['title']}")
            lines.append("")
            lines.append(f"**为什么**：{s['why']}")
            lines.append("")
            for a in s["actions"]:
                lines.append(f"- {a}")
            if s.get("note"):
                lines.append("")
                lines.append(f"> 提示：{s['note']}")
            lines.append("")
            lines.append(f"**完成标准**：{s['done']}")
            lines.append("")

    lines.append("## 环境体检")
    lines.append("")
    for it in env:
        icon = {"ok": "✅", "warn": "⚠️", "fail": "❌"}[it["level"]]
        line = f"- {icon} {it['title']}"
        if it["detail"]:
            line += f"：{it['detail']}"
        if it["fix"]:
            line += f"（{it['fix']}）"
        lines.append(line)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("本报告由 hk 自动生成，只给建议，不替代你自己的判断。"
                 "分区和格式化操作不可逆，动手前先备份。")
    return "\n".join(lines)


def run(write_report=True, with_network=False):
    """跑完整流程，返回 dict。"""
    d = detect.detect()
    hw = detect.to_hardware(d)
    verdict = check(hw)
    steps = planner.build(verdict)
    env = doctor.run(with_network=with_network)

    path = ""
    if write_report:
        REPORT_DIR.mkdir(exist_ok=True)
        fname = f"hk-report-{time.strftime('%Y%m%d-%H%M%S')}.md"
        p = REPORT_DIR / fname
        p.write_text(render_markdown(d, verdict, steps, env), encoding="utf-8")
        path = str(p)

    return {
        "detected": d,
        "hardware": {"cpu": hw.cpu, "gpus": hw.gpus, "storage": hw.storage,
                     "platform": hw.platform},
        "verdict": {
            "ok": verdict.ok,
            "headline": verdict.headline,
            "macos": list(verdict.macos) if verdict.macos else None,
            "findings": [{"level": f.level, "part": f.part, "title": f.title,
                          "detail": f.detail, "fix": f.fix} for f in verdict.findings],
        },
        "steps": steps,
        "env": env,
        "report": path,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), ensure_ascii=False, indent=2))
