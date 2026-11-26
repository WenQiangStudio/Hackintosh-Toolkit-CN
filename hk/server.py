#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地 Web 界面：把 hk 的能力做成一个能点的页面。

    python -m hk serve            # 打开 http://127.0.0.1:8765

只监听本机回环地址，不对外网开放。页面是单文件静态资源，不依赖任何 CDN，
断网也能用。
"""

import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import __version__, auto, bios, data, detect, doctor, planner
from .checker import Hardware, check

ROOT = Path(__file__).resolve().parent.parent
WEBUI = Path(__file__).resolve().parent / "webui" / "index.html"
MAX_BODY = 64 * 1024


def _hardware_from(payload):
    payload = payload or {}
    gpus = payload.get("gpus") or []
    if isinstance(gpus, str):
        gpus = [gpus]
    gpus = [str(g).strip() for g in gpus if g is not None and str(g).strip()][:8]
    storage = str(payload.get("storage") or "").strip().lower()
    if storage not in ("nvme", "sata", "vmd", "raid"):
        storage = ""
    platform = str(payload.get("platform") or "laptop").strip().lower()
    if platform not in ("laptop", "desktop", "server"):
        platform = "laptop"
    return Hardware(
        cpu=str(payload.get("cpu") or "").strip()[:120],
        gpus=gpus,
        wifi=str(payload.get("wifi") or "").strip()[:120],
        storage=storage,
        platform=platform,
    )


def verdict_payload(v):
    return {
        "ok": v.ok,
        "headline": v.headline,
        "macos": list(v.macos) if v.macos else None,
        "findings": [{"level": f.level, "part": f.part, "title": f.title,
                      "detail": f.detail, "fix": f.fix} for f in v.findings],
    }


def matrix_payload():
    def rows(rules):
        out = []
        for r in rules:
            if r.vmax == data.LATEST and r.status == data.FULL:
                span = "免驱（最新）"
            elif r.vmax == data.LATEST:
                span = f"{data.vstr(r.vmin)} 起"
            elif r.vmin:
                span = f"{data.vstr(r.vmin)} – {data.vstr(r.vmax)}"
            else:
                span = f"止于 {data.vstr(r.vmax)}"
            out.append({"pattern": r.pattern, "span": span, "note": r.note,
                        "status": r.status})
        return out

    return {"igpu": rows(data.IGPU_RULES), "dgpu": rows(data.DGPU_RULES)}


class Handler(BaseHTTPRequestHandler):
    server_version = f"hk/{__version__}"

    def log_message(self, fmt, *args):  # 安静一点
        pass

    # ------------------------------------------------------------ 工具
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        raw = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _error(self, code, message):
        self._send(code, {"error": message})

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return None
        if length <= 0 or length > MAX_BODY:
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

    # ------------------------------------------------------------ 路由
    def do_GET(self):
        url = urlparse(self.path)
        path = url.path
        qs = parse_qs(url.query)

        if path in ("/", "/index.html"):
            if not WEBUI.exists():
                return self._error(500, "界面文件缺失：hk/webui/index.html")
            return self._send(200, WEBUI.read_text(encoding="utf-8"),
                              "text/html; charset=utf-8")
        if path == "/api/health":
            return self._send(200, {"ok": True, "version": __version__})
        if path == "/api/detect":
            return self._send(200, detect.detect())
        if path == "/api/matrix":
            return self._send(200, matrix_payload())
        if path == "/api/doctor":
            return self._send(200, {"items": doctor.run(with_network=False),
                                    "summary": doctor.summary(doctor.run(with_network=False))})
        if path == "/api/bios":
            vendor = (qs.get("vendor") or [""])[0].lower()
            entry = bios.BIOS.get(vendor)
            return self._send(200, {"vendor": entry or None,
                                    "common": [{"item": i, "value": v, "why": w}
                                               for i, v, w in bios.COMMON]})
        if path == "/api/troubleshoot":
            q = (qs.get("q") or [""])[0].strip()
            rows = bios.TROUBLES
            if q:
                rows = [r for r in rows if q in r["symptom"] or q in r["cause"]
                        or any(q in f for f in r["fix"])]
            return self._send(200, {"items": rows})
        return self._error(404, f"没有这个路径：{path}")

    def do_POST(self):
        url = urlparse(self.path)
        path = url.path
        payload = self._read_json()
        if payload is None:
            return self._error(400, "请求体必须是 JSON 对象")

        if path == "/api/check":
            hw = _hardware_from(payload)
            return self._send(200, verdict_payload(check(hw)))
        if path == "/api/plan":
            hw = _hardware_from(payload)
            v = check(hw)
            return self._send(200, {"verdict": v.headline,
                                    "ok": v.ok,
                                    "steps": planner.build(v)})
        if path == "/api/auto":
            return self._send(200, auto.run(write_report=False))
        return self._error(404, f"没有这个路径：{path}")


def serve(host="127.0.0.1", port=8765, open_browser=False):
    if host not in ("127.0.0.1", "localhost", "::1"):
        print(f"[警告] 监听 {host} 意味着同网段的人也能访问这个页面", file=sys.stderr)
    httpd = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}"
    print(f"hk {__version__} 已启动：{url}")
    print("按 Ctrl+C 停止")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--open", action="store_true")
    a = ap.parse_args()
    serve(a.host, a.port, a.open)
