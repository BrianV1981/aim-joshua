#!/usr/bin/env python3
"""System health check for J.O.S.H.U.A. LanceDB, Memory Wiki, and Session History."""
import glob
import os
import sys
import time

_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from config_utils import OS_ROOT, PROJECT_ROOT


def print_status(component: str, status: str, message: str = "") -> None:
    color = "\033[92m" if status == "PASS" else ("\033[93m" if status == "WARN" else "\033[91m")
    reset = "\033[0m"
    print(f"[{color}{status}{reset}] {component:<25} {message}")


def check_lancedb() -> bool:
    lance_dir = os.path.join(OS_ROOT, "memory_lance")
    if not os.path.isdir(lance_dir):
        print_status("LanceDB Engine", "FAIL", f"Missing directory: {lance_dir}")
        return False
    try:
        from lance_backend import VectorBackend

        backend = VectorBackend(db_path=lance_dir)
        rows = backend.get_table().count_rows()
        print_status("LanceDB Engine", "PASS", f"Healthy ({rows} indexed chunks)")
        return True
    except Exception as e:
        print_status("LanceDB Engine", "FAIL", f"Error opening memory_lance: {e}")
        return False


def check_history_db() -> bool:
    db_path = os.path.join(OS_ROOT, "archive", "history.db")
    if not os.path.isfile(db_path):
        print_status("Session History DB", "WARN", "No archived sessions indexed yet (run './aim sessions').")
        return True
    try:
        from blackbox_vault import connect_history_db

        conn = connect_history_db(db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        finally:
            conn.close()
        print_status("Session History DB", "PASS", f"Healthy ({count} archived sessions)")
        return True
    except Exception as e:
        print_status("Session History DB", "FAIL", f"Corruption detected: {e}")
        return False


def check_memory_wiki() -> bool:
    wiki_dir = os.path.join(PROJECT_ROOT, "memory-wiki")
    if not os.path.isdir(wiki_dir):
        print_status("Memory Wiki", "WARN", "No memory-wiki/ directory found at project root.")
        return True
    pages = glob.glob(os.path.join(wiki_dir, "**", "*.md"), recursive=True)
    if not pages:
        print_status("Memory Wiki", "WARN", "memory-wiki/ contains 0 Markdown pages.")
        return True
    newest = max(pages, key=os.path.getmtime)
    age_hours = (time.time() - os.path.getmtime(newest)) / 3600.0
    print_status("Memory Wiki", "PASS", f"{len(pages)} pages (latest: {os.path.basename(newest)}, {age_hours:.1f}h ago)")
    return True


def main() -> int:
    print("\n--- A.I.M. SYSTEM HEALTH CHECK ---")
    ok_lance = check_lancedb()
    ok_hist = check_history_db()
    check_memory_wiki()
    print("-" * 34 + "\n")
    return 0 if (ok_lance and ok_hist) else 1


if __name__ == "__main__":
    sys.exit(main())
