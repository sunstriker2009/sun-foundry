#!/usr/bin/env python3
"""Compatibility entry point: merged branding is approved; synchronize directly."""
import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.argv.extend(["--source", "branding/assets/symbol.png"])
    runpy.run_path(str(Path(__file__).with_name("sync-approved-symbol.py")), run_name="__main__")
