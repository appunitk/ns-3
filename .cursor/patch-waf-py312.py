#!/usr/bin/env python3
"""Patch extracted waflib for Python 3.12+ (stdlib imp removed)."""
from __future__ import annotations

import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WAF_DIRS = glob.glob(os.path.join(ROOT, ".waf3-*"))

IMP_SHIM = """import types
try:
    import imp  # noqa: F401
except ModuleNotFoundError:
    import sys

    class imp:  # type: ignore[no-redef]
        @staticmethod
        def new_module(name):
            return types.ModuleType(name)

        @staticmethod
        def get_tag():
            return getattr(sys.implementation, "cache_tag", "") or ""
"""

CONTEXT_IMPORT = "import os,re,imp,sys"
CONTEXT_REPLACEMENT = "import os,re,sys\n" + IMP_SHIM


def patch_rU_modes(waf_dir: str) -> int:
    count = 0
    waflib = os.path.join(waf_dir, "waflib")
    for dirpath, _, filenames in os.walk(waflib):
        for name in filenames:
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            if "'rU'" not in text and '"rU"' not in text:
                continue
            new = text.replace("'rU'", "'r'").replace('"rU"', '"r"')
            with open(path, encoding="utf-8", mode="w") as f:
                f.write(new)
            count += 1
    return count


def patch_context(path: str) -> bool:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if "class imp:" in text and "ModuleNotFoundError" in text:
        return False
    if CONTEXT_IMPORT not in text:
        return False
    text = text.replace(CONTEXT_IMPORT, CONTEXT_REPLACEMENT, 1)
    with open(path, encoding="utf-8", mode="w") as f:
        f.write(text)
    return True


def patch_stopiteration(waf_dir: str) -> bool:
    path = os.path.join(waf_dir, "waflib", "Node.py")
    if not os.path.isfile(path):
        return False
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if "raise StopIteration" not in text:
        return False
    text = re.sub(r"^\t+raise StopIteration\s*$", "\t\treturn", text, count=1, flags=re.M)
    with open(path, encoding="utf-8", mode="w") as f:
        f.write(text)
    return True


def patch_tools_python(path: str) -> bool:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    old = 'import imp;print(imp.get_tag())'
    new = "import sys; print(getattr(sys.implementation, 'cache_tag', '') or '')"
    if old not in text:
        return False
    text = text.replace(old, new, 1)
    with open(path, encoding="utf-8", mode="w") as f:
        f.write(text)
    return True


def main() -> None:
    if not WAF_DIRS:
        print("No .waf3-* directory yet; run ./waf once to extract waflib.")
        return
    for waf_dir in WAF_DIRS:
        print("patch rU modes:", patch_rU_modes(waf_dir))
        print("patch StopIteration:", patch_stopiteration(waf_dir))
        ctx = os.path.join(waf_dir, "waflib", "Context.py")
        tools_py = os.path.join(waf_dir, "waflib", "Tools", "python.py")
        if os.path.isfile(ctx):
            print("patch Context.py:", patch_context(ctx))
        if os.path.isfile(tools_py):
            print("patch Tools/python.py:", patch_tools_python(tools_py))


if __name__ == "__main__":
    main()
