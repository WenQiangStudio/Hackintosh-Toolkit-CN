#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hk 的单元测试。

只测判定逻辑和输出结构，不测颜色和排版细节。
运行：python -m unittest discover -s tests -v
"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hk import cli, data, planner  # noqa: E402
from hk.checker import FAIL, WARN, Hardware, check  # noqa: E402


def verdict(**kw):
    return check(Hardware(**kw))


class TestLookup(unittest.TestCase):
    def test_uhd_beats_hd(self):
        """UHD 620 不能被 HD 620 的规则抢先命中。"""
        self.assertEqual(data.lookup_gpu("UHD 620").status, data.FULL)
        self.assertIn("Comet", data.lookup_gpu("UHD 620").note)

    def test_navi24_is_unsupported(self):
        """RX 6400/6500 属于 Navi 24，虽然叫 RX 6 系但不支持。"""
        self.assertEqual(data.lookup_gpu("RX 6400").status, data.UNSUPPORTED)
        self.assertEqual(data.lookup_gpu("RX 6500 XT").status, data.UNSUPPORTED)

    def test_navi23_supported(self):
        rule = data.lookup_gpu("RX 6600")
        self.assertEqual(rule.status, data.FULL)
        self.assertEqual(rule.vmin, (12, 2))

    def test_polaris(self):
        self.assertEqual(data.lookup_gpu("RX 580").vmin, (10, 13))

    def test_rtx_never(self):
        self.assertEqual(data.lookup_gpu("RTX 4090").status, data.UNSUPPORTED)

    def test_iris_xe_unsupported(self):
        self.assertEqual(data.lookup_gpu("Iris Xe Graphics").status, data.UNSUPPORTED)

    def test_unknown_gpu(self):
        self.assertIsNone(data.lookup_gpu("某牌显卡 9999"))


class TestVerdict(unittest.TestCase):
    def test_laptop_igpu_with_dead_dgpu_is_ok(self):
        """有可用核显时，无解的独显只是被禁用，不是装不了。"""
        v = verdict(cpu="i5-10210U", gpus=["UHD 620", "MX250"],
                    wifi="AX201", storage="nvme", platform="laptop")
        self.assertTrue(v.ok)
        self.assertIn("可以装", v.headline)
        self.assertTrue(any("MX250" in f.title and f.level == WARN for f in v.findings))

    def test_gaming_laptop_no_gpu(self):
        """12 代核显 + RTX，没有能驱动的 GPU。"""
        v = verdict(cpu="i7-12700H", gpus=["RTX 3060"], platform="laptop")
        self.assertFalse(v.ok)
        self.assertIsNone(v.macos)

    def test_vmd_blocks(self):
        v = verdict(cpu="i5-12400", gpus=["RX 6600"], storage="vmd", platform="desktop")
        self.assertFalse(v.ok)
        self.assertTrue(any("VMD" in f.title for f in v.fails))

    def test_raid_blocks(self):
        v = verdict(cpu="Xeon E5-2680 v4", gpus=["RX 580"], storage="raid", platform="server")
        self.assertFalse(v.ok)

    def test_desktop_amd_ok(self):
        v = verdict(cpu="i5-10400", gpus=["RX 6600"], storage="sata", platform="desktop")
        self.assertTrue(v.ok)
        self.assertEqual(v.macos, ((12, 2), data.LATEST))

    def test_legacy_gpu_caps_version(self):
        v = verdict(cpu="i7-8700K", gpus=["GTX 1080"], platform="desktop")
        self.assertTrue(v.ok)
        self.assertEqual(v.macos[1], (10, 13))

    def test_epyc_blocked(self):
        v = verdict(cpu="EPYC 7763", gpus=["RX 6600"], platform="server")
        self.assertFalse(v.ok)

    def test_version_intersection(self):
        """显卡最低版本和 CPU 最低版本取更高者。"""
        v = verdict(cpu="i7-4790K", gpus=["RX 6600"], platform="desktop")
        self.assertEqual(v.macos[0], (12, 2))

    def test_no_gpu_info(self):
        v = verdict(cpu="i5-10400", platform="desktop")
        self.assertIsNone(v.macos)

    def test_amd_cpu_warns(self):
        v = verdict(cpu="Ryzen 5 5600X", gpus=["RX 6600"], platform="desktop")
        self.assertTrue(v.ok)
        self.assertTrue(any("AMD" in f.title for f in v.warns))


class TestPlanner(unittest.TestCase):
    def test_laptop_has_battery_step(self):
        v = verdict(cpu="i5-10210U", gpus=["UHD 620"], platform="laptop")
        text = json.dumps(planner.build(v), ensure_ascii=False)
        self.assertIn("电池", text)

    def test_desktop_has_dual_boot_step(self):
        v = verdict(cpu="i5-10400", gpus=["RX 6600"], platform="desktop")
        text = json.dumps(planner.build(v), ensure_ascii=False)
        self.assertIn("双系统", text)
        self.assertNotIn("SMCBatteryManager", text)

    def test_server_has_fan_step(self):
        v = verdict(cpu="Xeon E5-2680 v4", gpus=["RX 580"], platform="server")
        text = json.dumps(planner.build(v), ensure_ascii=False)
        self.assertIn("风扇", text)

    def test_steps_are_complete(self):
        v = verdict(cpu="i5-10400", gpus=["RX 6600"], platform="desktop")
        steps = planner.build(v)
        self.assertGreaterEqual(len(steps), 8)
        for s in steps:
            for key in ("title", "why", "actions", "done"):
                self.assertIn(key, s)
            self.assertTrue(s["actions"])


class TestCli(unittest.TestCase):
    def test_check_runs(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(["check", "--cpu", "i5-10400", "--gpu", "RX 6600",
                           "--storage", "sata", "--platform", "desktop"])
        self.assertEqual(rc, 0)
        self.assertIn("可以装", buf.getvalue())

    def test_check_json(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            cli.main(["check", "--cpu", "i5-12400", "--gpu", "RTX 3060",
                      "--platform", "desktop", "--json"])
        payload = json.loads(buf.getvalue())
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["findings"])

    def test_troubleshoot_filter(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            cli.main(["troubleshoot", "禁行"])
        self.assertIn("禁行", buf.getvalue())

    def test_bios_unknown_vendor(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            cli.main(["bios", "--vendor", "nokia"])
        self.assertIn("没有这个品牌的预设", buf.getvalue())

    def test_module_entrypoint(self):
        """python -m hk 能跑起来（Windows CI 上也能）。"""
        r = subprocess.run([sys.executable, "-m", "hk", "matrix"],
                           cwd=str(ROOT), capture_output=True, text=True,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("核显", r.stdout)


if __name__ == "__main__":
    unittest.main()
