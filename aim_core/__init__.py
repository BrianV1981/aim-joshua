"""Bootstrap: prefer nested aim-agy_os package alias."""
from __future__ import annotations
import sys
from pathlib import Path
_os = Path(__file__).resolve().parents[1] / "aim-agy_os"
_core = _os / ".aim_core"
for p in (_os, _core):
    s = str(p)
    if p.is_dir() and s not in sys.path:
        sys.path.insert(0, s)
