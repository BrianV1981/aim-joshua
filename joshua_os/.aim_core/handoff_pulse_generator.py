#!/usr/bin/env python3
"""Handoff / pulse for aim-joshua: AGY brain transcripts → archive → wiki daemon."""
from config_utils import PROJECT_ROOT
import os
import json
import sys
import glob
from datetime import datetime
from reasoning_utils import AIM_ROOT
import argparse

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

CONFIG_PATH = os.path.join(PROJECT_ROOT, ".aim_core/CONFIG.json")
CONFIG = {}
if os.path.isfile(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r") as f:
            CONFIG = json.load(f) or {}
    except Exception as e:
        print(f"Handoff Generator: Warning loading CONFIG.json: {e}")
else:
    print(f"Handoff Generator: No CONFIG at {CONFIG_PATH}; using defaults")

CONTINUITY_DIR = os.path.join(AIM_ROOT, ".aim_core", "temp")
ARCHIVE_RAW_DIR = os.path.join(AIM_ROOT, "archive/raw")
os.makedirs(CONTINUITY_DIR, exist_ok=True)
os.makedirs(ARCHIVE_RAW_DIR, exist_ok=True)

MIN_CONVERSATIONAL_TURNS = 1
AGY_BRAIN = os.path.expanduser("~/.gemini/antigravity-cli/brain")


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


def session_id_from_agy_path(path: str) -> str:
    """.../brain/<uuid>/.system_generated/logs/transcript.jsonl → uuid"""
    base = os.path.basename(path)
    if base == "transcript.jsonl":
        # logs -> .system_generated -> uuid
        return os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path))))
    return base.replace(".jsonl", "")


def find_agy_transcripts(explicit_session_id=None, project_dir=None):
    found = []
    if explicit_session_id:
        path = os.path.join(
            AGY_BRAIN,
            explicit_session_id,
            ".system_generated",
            "logs",
            "transcript.jsonl",
        )
        if os.path.isfile(path):
            found.append(path)
        return found

    history_file = os.path.expanduser("~/.gemini/antigravity-cli/history.jsonl")
    if os.path.isfile(history_file) and project_dir:
        try:
            with open(history_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    if data.get("workspace") != project_dir:
                        continue
                    cid = data.get("conversationId")
                    if not cid:
                        continue
                    path = os.path.join(
                        AGY_BRAIN,
                        cid,
                        ".system_generated",
                        "logs",
                        "transcript.jsonl",
                    )
                    if os.path.isfile(path) and path not in found:
                        found.append(path)
        except Exception as e:
            print(f"Handoff Generator: Warning reading history: {e}")

    if not found and os.path.isdir(AGY_BRAIN):
        found = glob.glob(
            os.path.join(AGY_BRAIN, "*", ".system_generated", "logs", "transcript.jsonl")
        )
    found.sort(key=os.path.getmtime, reverse=True)
    return found


def generate_handoff_pulse(explicit_session_id=None) -> int:
    project_dir = os.path.abspath(PROJECT_ROOT if PROJECT_ROOT else AIM_ROOT)
    raw_files = find_agy_transcripts(explicit_session_id, project_dir)

    if not raw_files and not explicit_session_id:
        raw_files = glob.glob(os.path.join(ARCHIVE_RAW_DIR, "*.jsonl"))

    if not raw_files:
        print(
            f"Handoff Generator: [FATAL] No AGY transcripts "
            f"(session_id={explicit_session_id!r})."
        )
        return 1

    if explicit_session_id:
        print(f"Handoff Generator: EXCLUSIVE session_id={explicit_session_id}")
        latest_transcript = raw_files[0]
    else:
        raw_files.sort(key=os.path.getmtime, reverse=True)
        latest_transcript = raw_files[0]
        if len(raw_files) > 1:
            try:
                with open(latest_transcript, "r") as f:
                    n = sum(1 for line in f if line.strip())
                if n < 5:
                    print(
                        "Handoff Generator: newest transcript tiny; "
                        "using previous (anti-cannibalization)."
                    )
                    latest_transcript = raw_files[1]
            except Exception:
                pass

    try:
        skeleton = extract_signal(latest_transcript)
        turn_count = conversational_turn_count(skeleton)
        session_id = session_id_from_agy_path(latest_transcript)
        print(
            f"Handoff Generator: session_id={session_id} source={latest_transcript} "
            f"conversational_turns={turn_count}"
        )

        if turn_count < MIN_CONVERSATIONAL_TURNS:
            print(
                "Handoff Generator: [FATAL] Zero conversational turns. "
                "Refusing empty archive / false HANDOFF READY."
            )
            with open(
                os.path.join(CONTINUITY_DIR, "CURRENT_PULSE.md"), "w", encoding="utf-8"
            ) as f:
                f.write(
                    f"# HANDOFF FAILED — empty signal\n\n"
                    f"- session_id: `{session_id}`\n"
                    f"- source: `{latest_transcript}`\n"
                )
            return 1

        if explicit_session_id and session_id != explicit_session_id:
            print(
                f"Handoff Generator: [FATAL] resolved {session_id} "
                f"!= requested {explicit_session_id}"
            )
            return 1

        md_content = skeleton_to_markdown(skeleton, session_id)
        clean_path = os.path.join(CONTINUITY_DIR, "LAST_SESSION_FLIGHT_RECORDER.md")
        file_ts = datetime.now().strftime("%Y-%m-%d_%H%M")
        archive_dir = os.path.join(AIM_ROOT, "archive/history")
        os.makedirs(archive_dir, exist_ok=True)
        archive_path = os.path.join(archive_dir, f"{file_ts}_{session_id}.md")
        atomic_write(archive_path, md_content)
        print(f"      Historical Archive updated: {archive_path}")

        clean_content = (
            "# A.I.M. Session Flight Recorder (Full History)\n"
            "*NOT automatically injected into LLM context.*\n\n"
            + md_content
            + "\n"
        )
        atomic_write(clean_path, clean_content)

        cognitive_mode = (CONFIG.get("settings") or {}).get(
            "cognitive_mode", "monolithic"
        )
        if cognitive_mode == "monolithic":
            import subprocess

            try:
                log_path = os.path.join(AIM_ROOT, "memory-wiki", "daemon.log")
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                daemon_log = open(log_path, "a")
                daemon_log.write(
                    f"\n--- handoff spawn {datetime.now().isoformat()} "
                    f"archive={archive_path} ---\n"
                )
                daemon_log.flush()
                subprocess.Popen(
                    [
                        sys.executable,
                        "-u",
                        os.path.join(AIM_ROOT, "hooks", "session_summarizer.py"),
                        "--reincarnate",
                        archive_path,
                        "--bg",
                    ],
                    stdout=daemon_log,
                    stderr=daemon_log,
                    start_new_session=True,
                )
                print("      [Monolithic] Triggered wiki daemon (memory-wiki/daemon.log).")
            except Exception as e:
                print(f"      [Monolithic] daemon error: {e}")

        pulse_turns = []
        if isinstance(skeleton, list):
            for turn in skeleton:
                role = (turn.get("role") or "").upper()
                text = (turn.get("text") or "").strip()
                if role in ("USER", "ASSISTANT", "MODEL", "AGY", "GEMINI") and text:
                    pulse_turns.append(turn)
        last_5 = pulse_turns[-5:]
        pulse_content = "## Last 5 Conversational Turns\n\n"
        for turn in last_5:
            role_label = (
                "USER" if (turn.get("role") or "").upper() == "USER" else "A.I.M."
            )
            pulse_content += (
                f"### {role_label} ({turn.get('timestamp','')})\n"
                f"{(turn.get('text') or '').strip()}\n\n---\n\n"
            )
        with open(
            os.path.join(CONTINUITY_DIR, "CURRENT_PULSE.md"), "w", encoding="utf-8"
        ) as f:
            f.write(pulse_content)

        print("\n\033[92m--- A.I.M. HANDOFF READY ---\033[0m")
        return 0
    except Exception as e:
        print(f"Handoff Generator: failure: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A.I.M. Handoff Pulse Generator (AGY)")
    parser.add_argument("--session-id", type=str, default=None)
    args = parser.parse_args()
    sys.exit(generate_handoff_pulse(explicit_session_id=args.session_id))
