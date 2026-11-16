#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打包发布：把仓库打成带版本号的 zip，并校验内容。

    python scripts/package_release.py            # 生成 dist/Hackintosh-Toolkit-CN-v<版本>.zip
    python scripts/package_release.py --check    # 只校验必要文件在不在（CI 用）
"""

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hk import __version__  # noqa: E402

REQUIRED = [
    "README.md",
    "LICENSE",
    "hk/__init__.py",
    "hk/checker.py",
    "hk/data.py",
    "hk/cli.py",
    "tools/OpCore-Simplify/OpCore-Simplify.py",
    "tools/gibMacOS/gibMacOS.py",
    "docs/00-prepare.md",
    "docs/hardware-matrix.md",
]

SKIP_DIRS = {".git", "__pycache__", "dist", ".github", "tests"}


def check():
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    if missing:
        print("缺少必要文件：")
        for m in missing:
            print("  -", m)
        return 1
    print(f"必要文件齐全（{len(REQUIRED)} 项），版本 {__version__}")
    return 0


def build():
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    out = dist / f"Hackintosh-Toolkit-CN-v{__version__}.zip"

    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(ROOT.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            if p.suffix in (".pyc",):
                continue
            z.write(p, str(Path("Hackintosh-Toolkit-CN") / rel))
            count += 1

    data = out.read_bytes()
    print(f"已生成 {out}")
    print(f"  {count} 个文件，{len(data) / 1048576:.2f} MB")
    print(f"  SHA256 {hashlib.sha256(data).hexdigest()}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验，不打包")
    args = ap.parse_args()
    return check() if args.check else build()


if __name__ == "__main__":
    sys.exit(main())
