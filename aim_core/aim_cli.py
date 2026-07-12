#!/usr/bin/env python3
"""Thin launcher → nested aim_cli (legacy path compat)."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
os_root = root / "aim-agy_os"
core = os_root / ".aim_core"
sys.path.insert(0, str(os_root))
sys.path.insert(0, str(core))
cli = core / "aim_cli.py"
if not cli.is_file():
    sys.stderr.write(f"[aim-opencode] missing nested CLI: {cli}\n")
    sys.exit(1)
runpy.run_path(str(cli), run_name="__main__")
