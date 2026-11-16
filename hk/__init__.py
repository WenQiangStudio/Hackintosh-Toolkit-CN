#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hk —— 黑苹果可行性判定与安装计划。"""

__version__ = "2.0.0"

from .checker import Hardware, check  # noqa: F401

__all__ = ["Hardware", "check", "__version__"]
