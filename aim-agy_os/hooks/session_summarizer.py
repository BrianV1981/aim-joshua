#!/usr/bin/env python3
"""
OpenCode session summarizer — deterministic memory-wiki path (no ForensicDB, no LLM required).
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time
from pathlib import Path


def find_aim_root():
    current = os.path.abspath(os.getcwd())
    while current != "/":
        if os.path.exists(os.path.join(current, "core", "CONFIG.json")):
            return current
        if os.path.exists(os.path.join(current, "aim-agy_os", "setup.sh")):
            return current
        current = os.path.dirname(current)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


VESSEL_ROOT = find_aim_root()
# Engine may live under aim-agy_os/
ENGINE = (
    os.path.join(VESSEL_ROOT, "aim-agy_os")
    if os.path.isdir(os.path.join(VESSEL_ROOT, "aim-agy_os"))
    else VESSEL_ROOT
)
sys.path.insert(0, os.path.join(ENGINE, ".aim_core"))
sys.path.insert(0, ENGINE)

WIKI = os.path.join(VESSEL_ROOT, "memory-wiki")
CONFIG_PATH = os.path.join(VESSEL_ROOT, "core", "CONFIG.json")


def _daemon_log(msg: str) -> None:
    try:
        os.makedirs(WIKI, exist_ok=True)
        with open(os.path.join(WIKI, "daemon.log"), "a", encoding="utf-8") as lf:
            lf.write(msg.rstrip() + "\n")
    except Exception:
        pass
    print(msg, flush=True)


if not os.path.isfile(CONFIG_PATH):
    _daemon_log(f"[FATAL] no CONFIG at {CONFIG_PATH}")
    sys.exit(2)

with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)
_daemon_log(f"[OK] session_summarizer loaded CONFIG from {CONFIG_PATH}")


def _slug(s: str) -> str:
    import re

    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80] or "session"


def process_transcript(md_path: str) -> bool:
    try:
        _daemon_log(f"[WATCHDOG] Beginning wiki sequence for: {os.path.basename(md_path)}")
        with open(md_path, "r", encoding="utf-8") as f:
            transcript = f.read()
        if not transcript.strip():
            _daemon_log("[FATAL] Archive empty. Refusing SUCCESS.")
            return False
        stripped = transcript.strip()
        has_user = "👤" in stripped or "user_query" in stripped.lower() or "## 👤" in stripped
        if "No conversational turns extracted" in stripped or (
            len(stripped) < 200 and not has_user
        ):
            _daemon_log("[FATAL] Archive has no usable content. Refusing SUCCESS.")
            return False

        stem = os.path.basename(md_path).replace(".md", "")
        # prefer last uuid-ish segment
        session_id = stem
        if "_" in stem:
            session_id = stem.split("_")[-1]

        pages = Path(WIKI) / "pages"
        ingest = Path(WIKI) / "_ingest"
        pages.mkdir(parents=True, exist_ok=True)
        ingest.mkdir(parents=True, exist_ok=True)
        log_path = Path(WIKI) / "log.md"
        index_path = Path(WIKI) / "index.md"

        page_name = f"reincarnate-{_slug(session_id)}.md"
        page_path = pages / page_name
        body = (
            f"# Reincarnation archive: {session_id}\n\n"
            f"*Ingested from `{os.path.basename(md_path)}`*\n\n"
            f"{transcript}\n"
        )
        page_path.write_text(body, encoding="utf-8")
        _daemon_log(f"[WATCHDOG] Wrote page {page_path}")

        # log
        from datetime import datetime, timezone

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        with open(log_path, "a", encoding="utf-8") as lf:
            lf.write(f"- [{ts}] created page `{page_name}` from reincarnate handoff\n")

        # index refresh (simple append if missing)
        idx = index_path.read_text(encoding="utf-8") if index_path.exists() else "# Wiki Index\n\n## Pages\n\n"
        link = f"- [reincarnate {session_id}](pages/{page_name})\n"
        if page_name not in idx:
            if "## Pages" not in idx:
                idx += "\n## Pages\n\n"
            idx += link
            index_path.write_text(idx, encoding="utf-8")

        _daemon_log("[SUCCESS] Deterministic wiki reincarnation sequence complete.")
        return True
    except Exception as e:
        _daemon_log(f"[FATAL] Watchdog Pipeline Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main(args):
    if "--reincarnate" not in args:
        print(json.dumps({}))
        return
    md_path = None
    for arg in args[1:]:
        if arg.endswith(".md") and os.path.exists(arg):
            md_path = arg
            break
    if not md_path:
        hist = os.path.join(VESSEL_ROOT, "archive", "history")
        if os.path.isdir(hist):
            files = glob.glob(os.path.join(hist, "*.md"))
            if files:
                md_path = max(files, key=os.path.getmtime)
    if not md_path:
        _daemon_log("[FATAL] no archive markdown")
        sys.exit(3)

    if "--bg" not in args:
        import subprocess

        log_path = os.path.join(WIKI, "daemon.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        daemon_log = open(log_path, "a", encoding="utf-8")
        cmd = [sys.executable, "-u", os.path.abspath(__file__), "--bg"] + [
            a for a in args[1:] if a != "--bg"
        ]
        if "--reincarnate" not in cmd:
            cmd.insert(1, "--reincarnate")
        subprocess.Popen(
            cmd,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=daemon_log,
            stderr=daemon_log,
            cwd=VESSEL_ROOT,
        )
        print(json.dumps({"spawned_bg": True, "archive": md_path}))
        return

    if not process_transcript(md_path):
        sys.exit(4)


if __name__ == "__main__":
    main(sys.argv)
