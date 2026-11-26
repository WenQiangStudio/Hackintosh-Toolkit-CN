#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动化能力（检测 / 体检 / 一键流程 / 本地服务）的测试。

跑法：python -m unittest discover -s tests -v
"""

import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hk import auto, detect, doctor, server  # noqa: E402


class TestParsers(unittest.TestCase):
    def test_meminfo(self):
        text = "MemTotal:       16384000 kB\nMemFree:  100 kB"
        self.assertEqual(detect.parse_meminfo(text), 16)

    def test_meminfo_missing(self):
        self.assertEqual(detect.parse_meminfo("nonsense"), 0)

    def test_cpuinfo_x86(self):
        text = "processor\t: 0\nmodel name\t: Intel(R) Core(TM) i5-10210U CPU @ 1.60GHz\n"
        self.assertIn("i5-10210U", detect.parse_cpuinfo(text))

    def test_cpuinfo_arm_fallback(self):
        text = "processor\t: 0\nHardware\t: BCM2711\n"
        self.assertEqual(detect.parse_cpuinfo(text), "BCM2711")

    def test_cpuinfo_arm_unknown(self):
        """有些 ARM 内核既不写 model name 也不写 Hardware。"""
        self.assertEqual(detect.parse_cpuinfo("processor\t: 0\nCPU part\t: 0xd81\n"), "")

    def test_gpu_lines(self):
        text = "Name\nIntel UHD Graphics 620\nNVIDIA MX250\n"
        self.assertEqual(detect.parse_gpu_lines(text),
                         ["Intel UHD Graphics 620", "NVIDIA MX250"])

    def test_wmic_cpu(self):
        self.assertEqual(detect.parse_wmic_cpu("Name\nIntel Core i7-8700K\n"),
                         "Intel Core i7-8700K")

    def test_system_profiler(self):
        self.assertEqual(detect.parse_system_profiler_chip("Chip: Apple M2"), "Apple M2")

    def test_guess_storage(self):
        self.assertEqual(detect.guess_storage(["nvme0n1", "sda"]), "nvme")
        self.assertEqual(detect.guess_storage(["sda", "sdb"]), "sata")
        self.assertEqual(detect.guess_storage([]), "")


class TestDetect(unittest.TestCase):
    def test_shape(self):
        d = detect.detect()
        for key in ("os", "arch", "cpu", "gpus", "memory_gb", "storage",
                    "platform", "notes", "compatible"):
            self.assertIn(key, d)
        self.assertIsInstance(d["gpus"], list)
        self.assertIsInstance(d["notes"], list)

    def test_to_hardware_sanitizes(self):
        hw = detect.to_hardware({"cpu": "x", "gpus": ["a"], "storage": "bogus",
                                 "platform": "toaster"})
        self.assertEqual(hw.storage, "")
        self.assertEqual(hw.platform, "desktop")


class TestDoctor(unittest.TestCase):
    def test_levels_valid(self):
        items = doctor.run(with_network=False)
        self.assertTrue(items)
        for it in items:
            self.assertIn(it["level"], ("ok", "warn", "fail"))
            self.assertTrue(it["title"])

    def test_summary_variants(self):
        self.assertIn("阻塞", doctor.summary([{"level": "fail"}]))
        self.assertIn("建议", doctor.summary([{"level": "warn"}]))
        self.assertIn("全部通过", doctor.summary([{"level": "ok"}]))

    def test_network_check_returns_tuple(self):
        ok, bad = doctor.check_network([("127.0.0.1", 1)], timeout=1)
        self.assertFalse(ok)
        self.assertEqual(bad, ["127.0.0.1"])


class TestAuto(unittest.TestCase):
    def test_run_without_report(self):
        out = auto.run(write_report=False)
        self.assertIn("detected", out)
        self.assertIn("verdict", out)
        self.assertTrue(out["steps"])
        self.assertTrue(out["env"])
        self.assertEqual(out["report"], "")

    def test_markdown_has_sections(self):
        d = {"os": "Linux", "arch": "x86_64", "cpu": "i5-10400",
             "gpus": ["RX 6600"], "memory_gb": 16, "storage": "sata", "platform": "desktop"}
        from hk.checker import Hardware, check
        from hk import planner
        v = check(Hardware(cpu="i5-10400", gpus=["RX 6600"], storage="sata",
                           platform="desktop"))
        md = auto.render_markdown(d, v, planner.build(v), doctor.run(with_network=False))
        for part in ("# 黑苹果可行性报告", "## 结论", "## 逐项检查", "## 安装计划", "## 环境体检"):
            self.assertIn(part, md)
        self.assertIn("RX 6600", md)


class TestServerHelpers(unittest.TestCase):
    def test_hardware_from_sanitizes(self):
        hw = server._hardware_from({
            "cpu": "  i5-10400  ", "gpus": "RX 6600", "storage": "NVME ",
            "platform": "DESKTOP", "wifi": "AX201",
        })
        self.assertEqual(hw.cpu, "i5-10400")
        self.assertEqual(hw.gpus, ["RX 6600"])
        self.assertEqual(hw.storage, "nvme")
        self.assertEqual(hw.platform, "desktop")

    def test_hardware_from_bad_values(self):
        hw = server._hardware_from({"storage": "zfs", "platform": "car",
                                    "gpus": [None, "", "  "], "cpu": "x" * 500})
        self.assertEqual(hw.storage, "")
        self.assertEqual(hw.platform, "laptop")
        self.assertEqual(hw.gpus, [])
        self.assertLessEqual(len(hw.cpu), 120)

    def test_verdict_payload(self):
        from hk.checker import Hardware, check
        p = server.verdict_payload(
            check(Hardware(cpu="i5-10400", gpus=["RTX 3060"], platform="desktop")))
        self.assertFalse(p["ok"])
        self.assertTrue(p["findings"])

    def test_matrix_payload(self):
        m = server.matrix_payload()
        self.assertTrue(m["igpu"])
        self.assertTrue(m["dgpu"])
        self.assertIn("pattern", m["igpu"][0])


class TestHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def _get(self, path):
        url = f"http://127.0.0.1:{self.port}{path}"
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.status, json.loads(r.read().decode())

    def _post(self, path, payload):
        url = f"http://127.0.0.1:{self.port}{path}"
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode())

    def test_health(self):
        status, body = self._get("/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

    def test_check(self):
        status, body = self._post("/api/check", {
            "cpu": "i5-10210U", "gpus": ["UHD 620"], "storage": "nvme",
            "platform": "laptop"})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

    def test_plan(self):
        status, body = self._post("/api/plan", {
            "cpu": "i5-10400", "gpus": ["RX 6600"], "platform": "desktop"})
        self.assertEqual(status, 200)
        self.assertTrue(body["steps"])

    def test_bad_json(self):
        url = f"http://127.0.0.1:{self.port}/api/check"
        req = urllib.request.Request(url, data=b"not json",
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 400)

    def test_unknown_path(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(f"http://127.0.0.1:{self.port}/nope", timeout=10)
        self.assertEqual(ctx.exception.code, 404)

    def test_index_served(self):
        """界面文件存在时首页应返回 HTML；不存在时应给出明确错误而不是崩溃。"""
        path = ROOT / "hk" / "webui" / "index.html"
        url = f"http://127.0.0.1:{self.port}/"
        if path.exists():
            with urllib.request.urlopen(url, timeout=10) as r:
                self.assertEqual(r.status, 200)
                self.assertIn("text/html", r.headers.get("Content-Type", ""))
        else:
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(url, timeout=10)
            self.assertEqual(ctx.exception.code, 500)


if __name__ == "__main__":
    unittest.main()
