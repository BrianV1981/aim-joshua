#!/usr/bin/env python3
"""Surgical rolling archive cleanup and safe LanceDB compaction."""
import glob
import os
import sys
import time

_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from config_utils import CONFIG, OS_ROOT

AIM_ROOT = OS_ROOT
RAW_DIR = CONFIG.get("paths", {}).get("archive_raw_dir", os.path.join(OS_ROOT, "archive", "raw"))
MEM_ARCHIVE_DIR = os.path.join(OS_ROOT, "memory", "archive")
CONTINUITY_DIR = CONFIG.get("paths", {}).get("continuity_dir", os.path.join(OS_ROOT, "continuity"))


def clean_rolling_archive(days=None):
    """Surgical cleanup of old artifacts to prevent repo bloat."""
    if days is None:
        days = CONFIG.get("settings", {}).get("archive_retention_days", 30)

    if days == 0:
        print("--- A.I.M. MAINTENANCE: Deactivated ---")
        print("[IDLE] Archive retention is set to 0 (Permanent). Skipping purge.")
        return

    print(f"--- A.I.M. MAINTENANCE: {days}-Day Rolling Purge ---")
    now = time.time()
    cutoff = now - (days * 86400)

    targets = [
        ("Raw Transcripts", os.path.join(RAW_DIR, "*.json")),
        ("Memory Proposals", os.path.join(MEM_ARCHIVE_DIR, "*.md")),
        ("Continuity Reports", os.path.join(CONTINUITY_DIR, "REPORT_*.md")),
        ("Context Pulses", os.path.join(CONTINUITY_DIR, "202*.md")),
    ]

    total_purged = 0
    for label, pattern in targets:
        files = glob.glob(pattern)
        purged_in_category = 0
        for f in files:
            if f.endswith(".gitkeep"):
                continue
            if os.path.getmtime(f) < cutoff:
                try:
                    os.remove(f)
                    purged_in_category += 1
                except Exception as e:
                    print(f"  [ERROR] Failed to delete {os.path.basename(f)}: {e}", file=sys.stderr)

        if purged_in_category > 0:
            print(f"[OK] Purged {purged_in_category} stale {label}.")
            total_purged += purged_in_category
        else:
            print(f"[IDLE] {label} are within the retention window.")

    if total_purged > 0:
        print(f"\n[SUCCESS] Maintenance complete. {total_purged} artifacts removed.")
    else:
        print("\n[SUCCESS] System is lean. No action required.")


def _get_dir_size(path: str) -> int:
    total_size = 0
    if not os.path.isdir(path):
        return 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                try:
                    total_size += os.path.getsize(fp)
                except OSError:
                    pass
    return total_size


def compact_lance_db(immediate: bool = False) -> bool:
    """Compact LanceDB under the cross-platform write lock."""
    print("\n--- A.I.M. MAINTENANCE: LanceDB Compaction ---")
    try:
        from lance_backend import VectorBackend

        backend = VectorBackend()
        size_before = _get_dir_size(backend.path)
        print(f"[*] Size before compaction: {size_before / (1024 * 1024):.2f} MB")

        if not backend.compact(immediate=immediate):
            print("[ERROR] Failed to compact LanceDB.", file=sys.stderr)
            return False

        size_after = _get_dir_size(backend.path)
        print(f"[*] Size after compaction: {size_after / (1024 * 1024):.2f} MB")
        print("[SUCCESS] LanceDB version history compacted.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to compact LanceDB: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    retention_days = 30
    immediate_flag = "--immediate" in sys.argv
    for arg in sys.argv[1:]:
        if arg.isdigit():
            retention_days = int(arg)

    clean_rolling_archive(retention_days)
    if not compact_lance_db(immediate=immediate_flag):
        sys.exit(1)
