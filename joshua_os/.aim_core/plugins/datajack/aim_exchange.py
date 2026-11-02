#!/usr/bin/env python3
"""Mount ('import') and unmount ('unplug') local Parquet ROM cartridges."""
import glob
import os
import shutil
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE_DIR = os.path.dirname(os.path.dirname(_HERE))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from config_utils import OS_ROOT

AIM_ROOT = OS_ROOT


def import_cartridge(cartridge_path: str) -> None:
    print("--- A.I.M. DATAJACK: IMPORT (Native ROM) ---")
    print(f"[INFO] Mounting Parquet Cartridge: {os.path.basename(cartridge_path)}")

    if not os.path.exists(cartridge_path):
        print(f"[ERROR] Cartridge not found: {cartridge_path}", file=sys.stderr)
        sys.exit(1)

    if not cartridge_path.endswith(".parquet") and not cartridge_path.endswith(".engram"):
        print("[ERROR] Invalid Cartridge: Must be a .parquet file.", file=sys.stderr)
        sys.exit(1)

    cartridges_dir = os.path.join(AIM_ROOT, "archive", "cartridges")
    os.makedirs(cartridges_dir, exist_ok=True)

    target_name = os.path.basename(cartridge_path)
    if target_name.endswith(".engram"):
        target_name = target_name[:-7] + ".parquet"
    target_path = os.path.join(cartridges_dir, target_name)

    try:
        shutil.copy2(cartridge_path, target_path)
        print(f"[SUCCESS] Native ROM Cartridge mounted successfully at {target_path}.")
    except Exception as e:
        print(f"[ERROR] Failed to mount cartridge: {e}", file=sys.stderr)
        sys.exit(1)


def unplug_cartridge(keyword: str) -> None:
    print("--- A.I.M. DATAJACK: UNPLUG (Unmount ROM) ---")
    clean_kw = os.path.basename((keyword or "").strip())
    if not clean_kw:
        print("[ERROR] Cartridge keyword or filename required.", file=sys.stderr)
        sys.exit(1)

    cartridges_dir = os.path.join(AIM_ROOT, "archive", "cartridges")
    if not os.path.isdir(cartridges_dir):
        print(f"[ERROR] No mounted cartridges found in {cartridges_dir}.", file=sys.stderr)
        sys.exit(1)

    candidates = []
    for path in sorted(glob.glob(os.path.join(cartridges_dir, "*.parquet"))):
        base = os.path.basename(path)
        stem = base[:-8] if base.endswith(".parquet") else base
        if clean_kw in (base, stem) or base.startswith(clean_kw):
            candidates.append(path)

    if not candidates:
        print(f"[ERROR] No mounted cartridge matching '{clean_kw}' in {cartridges_dir}.", file=sys.stderr)
        sys.exit(1)

    for path in candidates:
        os.remove(path)
        print(f"[SUCCESS] Unplugged cartridge: {os.path.basename(path)}")


def list_cartridges() -> None:
    cartridges_dir = os.path.join(AIM_ROOT, "archive", "cartridges")
    files = sorted(glob.glob(os.path.join(cartridges_dir, "*.parquet"))) if os.path.isdir(cartridges_dir) else []
    print("--- A.I.M. DATAJACK: MOUNTED CARTRIDGES ---")
    if not files:
        print("  (none)")
        return
    for path in files:
        size_kb = os.path.getsize(path) / 1024.0
        print(f"  - {os.path.basename(path)} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: aim_exchange.py {import <file.parquet> | unplug <keyword> | list}", file=sys.stderr)
        sys.exit(1)

    sub = sys.argv[1]
    if sub == "import":
        if len(sys.argv) < 3:
            print("Usage: aim_exchange.py import <file.parquet>", file=sys.stderr)
            sys.exit(1)
        import_cartridge(sys.argv[2])
    elif sub == "unplug":
        if len(sys.argv) < 3:
            print("Usage: aim_exchange.py unplug <keyword>", file=sys.stderr)
            sys.exit(1)
        unplug_cartridge(sys.argv[2])
    elif sub == "list":
        list_cartridges()
    else:
        print(f"Unknown subcommand '{sub}'. Expected: import, unplug, or list.", file=sys.stderr)
        sys.exit(1)
