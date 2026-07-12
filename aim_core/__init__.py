"""Deprecated flat package: inject nested aim-agy_os/.aim_core onto sys.path."""
from __future__ import annotations

import sys
from pathlib import Path

_NESTED = Path(__file__).resolve().parents[1] / "aim-agy_os" / ".aim_core"
_OS = Path(__file__).resolve().parents[1] / "aim-agy_os"
for p in (_OS, _NESTED):
    s = str(p)
    if p.is_dir() and s not in sys.path:
        sys.path.insert(0, s)
