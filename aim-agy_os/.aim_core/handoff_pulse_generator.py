#!/usr/bin/env python3
"""OpenCode vessel handoff: archive/raw session JSON → flight recorder → wiki daemon."""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import datetime

from reasoning_utils import AIM_ROOT

try:
    from extract_signal import (
        extract_signal,
        skeleton_to_markdown,
        conversational_turn_count,
    )
except ImportError:
    sys.path.append(os.path.join(AIM_ROOT, ".aim_core"))
    from extract_signal import (
        extract_signal,
        skeleton_to_markdown,
        conversational_turn_count,
    )

# Vessel root (parent of aim-agy_os when nested)
VESSEL_ROOT = os.path.dirname(AIM_ROOT) if os.path.basename(AIM_ROOT) == "aim-agy_os" else AIM_ROOT
CONFIG_PATH = os.path.join(VESSEL_ROOT, "core", "CONFIG.json")
CONFIG = {}
if os.path.isfile(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        CONFIG = json.load(f)

paths = CONFIG.get("paths") or {}
CONTINUITY_DIR = paths.get("continuity_dir") or os.path.join(VESSEL_ROOT, "continuity")
ARCHIVE_RAW_DIR = paths.get("opencode_export_dir") or paths.get(
    "archive_raw_dir"
) or os.path.join(VESSEL_ROOT, "archive", "raw")
os.makedirs(CONTINUITY_DIR, exist_ok=True)

MIN_CONVERSATIONAL_TURNS = 1


def atomic_write(file_path, content):
    temp_path = f"{file_path}.tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, file_path)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def find_session_files(explicit_session_id=None):
    """Find OpenCode session JSON under archive/raw (and nested patterns)."""
    found = []
    if not os.path.isdir(ARCHIVE_RAW_DIR):
        return found
    patterns = [
        os.path.join(ARCHIVE_RAW_DIR, "session-*.json"),
        os.path.join(ARCHIVE_RAW_DIR, "*.json"),
    ]
    for pat in patterns:
        for path in glob.glob(pat):
            if path.endswith(".json") and os.path.isfile(path):
                found.append(path)
    # de-dupe
    found = sorted(set(found), key=os.path.getmtime, reverse=True)

    if explicit_session_id:
        exclusive = []
        for path in found:
            base = os.path.basename(path)
            if explicit_session_id in base or explicit_session_id in path:
                exclusive.append(path)
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if str(data.get("sessionId", "")) == explicit_session_id:
                    exclusive.append(path)
            except Exception:
                pass
        return exclusive
    return found


def session_id_from_path(path: str, data_hint=None) -> str:
    if data_hint and isinstance(data_hint, dict) and data_hint.get("sessionId"):
        return str(data_hint["sessionId"])
    base = os.path.basename(path).replace(".json", "")
    if base.startswith("session-"):
        return base[len("session-") :]
    return base


def generate_handoff_pulse(explicit_session_id=None) -> int:
    raw_files = find_session_files(explicit_session_id)
    if not raw_files:
        print(
            f"Handoff Generator: [FATAL] No OpenCode session files "
            f"(session_id={explicit_session_id!r}, dir={ARCHIVE_RAW_DIR})"
        )
        return 1

    if explicit_session_id:
        print(f"Handoff Generator: EXCLUSIVE session_id={explicit_session_id}")
        latest = raw_files[0]
    else:
        latest = raw_files[0]
        if len(raw_files) > 1:
            try:
                with open(latest, "r") as f:
                    data = json.load(f)
                msgs = data.get("messages") or []
                if len(msgs) < 3:
                    print("Handoff Generator: newest tiny; using previous.")
                    latest = raw_files[1]
            except Exception:
                pass

    try:
        skeleton = extract_signal(latest)
        turns = conversational_turn_count(skeleton)
        try:
            with open(latest, "r", encoding="utf-8") as f:
                data_hint = json.load(f)
        except Exception:
            data_hint = None
        session_id = session_id_from_path(latest, data_hint)
        print(
            f"Handoff Generator: session_id={session_id} source={latest} "
            f"conversational_turns={turns}"
        )
        if turns < MIN_CONVERSATIONAL_TURNS:
            print(
                "Handoff Generator: [FATAL] Zero conversational turns. "
                "Refusing empty archive."
            )
            return 1

        md = skeleton_to_markdown(skeleton, session_id)
        file_ts = datetime.now().strftime("%Y-%m-%d_%H%M")
        archive_dir = os.path.join(VESSEL_ROOT, "archive", "history")
        os.makedirs(archive_dir, exist_ok=True)
        # sanitize session id for filename
        safe_sid = session_id.replace("/", "-")
        archive_path = os.path.join(archive_dir, f"{file_ts}_{safe_sid}.md")
        atomic_write(archive_path, md)
        print(f"      Historical Archive updated: {archive_path}")

        clean_path = os.path.join(CONTINUITY_DIR, "LAST_SESSION_FLIGHT_RECORDER.md")
        # also engine temp for compatibility
        os.makedirs(os.path.join(AIM_ROOT, ".aim_core", "temp"), exist_ok=True)
        engine_clean = os.path.join(
            AIM_ROOT, ".aim_core", "temp", "LAST_SESSION_FLIGHT_RECORDER.md"
        )
        header = (
            "# A.I.M. Session Flight Recorder (Full History)\n"
            "*NOT auto-injected into LLM context.*\n\n"
        )
        atomic_write(clean_path, header + md + "\n")
        atomic_write(engine_clean, header + md + "\n")

        # Wiki daemon — prefer nested hooks
        hook = os.path.join(AIM_ROOT, "hooks", "session_summarizer.py")
        if not os.path.isfile(hook):
            hook = os.path.join(VESSEL_ROOT, "hooks", "session_summarizer.py")
        log_path = os.path.join(VESSEL_ROOT, "memory-wiki", "daemon.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        try:
            import subprocess

            daemon_log = open(log_path, "a")
            daemon_log.write(
                f"\n--- handoff spawn {datetime.now().isoformat()} "
                f"archive={archive_path} ---\n"
            )
            daemon_log.flush()
            subprocess.Popen(
                [sys.executable, "-u", hook, "--reincarnate", archive_path, "--bg"],
                stdout=daemon_log,
                stderr=daemon_log,
                start_new_session=True,
                cwd=VESSEL_ROOT,
            )
            print("      [Monolithic] Triggered wiki daemon (memory-wiki/daemon.log).")
        except Exception as e:
            print(f"      daemon error: {e}")

        pulse_turns = [
            t
            for t in (skeleton if isinstance(skeleton, list) else [])
            if isinstance(t, dict)
            and (t.get("text") or "").strip()
            and (t.get("role") or "").lower()
            in ("user", "assistant", "model", "gemini")
        ][-5:]
        pulse = "## Last 5 Conversational Turns\n\n"
        for t in pulse_turns:
            label = "USER" if (t.get("role") or "").lower() == "user" else "A.I.M."
            pulse += f"### {label}\n{(t.get('text') or '').strip()}\n\n---\n\n"
        for pth in (
            os.path.join(CONTINUITY_DIR, "CURRENT_PULSE.md"),
            os.path.join(AIM_ROOT, ".aim_core", "temp", "CURRENT_PULSE.md"),
        ):
            os.makedirs(os.path.dirname(pth), exist_ok=True)
            with open(pth, "w", encoding="utf-8") as f:
                f.write(pulse)

        print("\n\033[92m--- A.I.M. HANDOFF READY ---\033[0m")
        return 0
    except Exception as e:
        print(f"Handoff Generator: failure: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--session-id", default=None)
    args = ap.parse_args()
    sys.exit(generate_handoff_pulse(explicit_session_id=args.session_id))
