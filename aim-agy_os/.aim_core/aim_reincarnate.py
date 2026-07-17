#!/usr/bin/env python3
import os
import sys
import time
import argparse

def find_aim_root():
    current = os.path.abspath(os.getcwd())
    while current != '/':
        if os.path.exists(os.path.join(current, "aim-agy_os", "setup.sh")): return os.path.join(current, "aim-agy_os")
        if os.path.exists(os.path.join(current, "setup.sh")): return current
        current = os.path.dirname(current)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AIM_ROOT = find_aim_root()

# Ensure .aim_core is in python path to load our new package
sys.path.append(os.path.join(AIM_ROOT, ".aim_core"))

from reincarnation.gameplan_manager import load_and_validate_gameplan, cleanup_gameplan
from reincarnation.background_tasks import trigger_background_pipelines
from reincarnation.context_builder import fetch_issue_context, build_wakeup_prompt
from reincarnation.teleport_engine import get_current_tmux_session, spawn_new_agent, execute_teleport

def main():
    parser = argparse.ArgumentParser(description="A.I.M. Reincarnation Protocol")
    parser.add_argument("--session-id", type=str, default=None, help="The explicit conversation UUID of the active agent.")
    parser.add_argument(
        "--no-teleport",
        action="store_true",
        help="Run pulse + vault + wake-prompt only; skip tmux spawn/teleport (CI / E2E safe).",
    )
    args = parser.parse_args()

    # Env override for automation (AIM_REINCARNATE_NO_TELEPORT=1)
    no_teleport = bool(args.no_teleport) or (
        os.environ.get("AIM_REINCARNATE_NO_TELEPORT", "").strip() in ("1", "true", "yes")
    )

    print("--- A.I.M. REINCARNATION PROTOCOL ---")
    print("\n[!] CONTEXT FADE DETECTED: We are initiating Reincarnation.")
    
    workspace = os.environ.get("AIM_WORKSPACE", ".")

    # 1. Verification
    gameplan = load_and_validate_gameplan(AIM_ROOT)
    
    print("[0/4] Giving the CLI filesystem time to sync the final agent turn...")
    # Shorter sleep in no-teleport / CI mode
    time.sleep(0.5 if no_teleport else 3)
    
    current_tmux = get_current_tmux_session()
    
    # 2. Background Dispatch & Context Building (pulse → vault seal → scraper)
    trigger_background_pipelines(AIM_ROOT, workspace, args.session_id)
    issues = fetch_issue_context(AIM_ROOT)
    prompt = build_wakeup_prompt(gameplan, issues)

    # Persist wake prompt for Operator audit even when not teleporting
    temp_dir = os.path.join(AIM_ROOT, ".aim_core", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    wake_path = os.path.join(temp_dir, "LAST_WAKE_PROMPT.md")
    try:
        with open(wake_path, "w", encoding="utf-8") as f:
            f.write(prompt if isinstance(prompt, str) else str(prompt))
        print(f"      Wake prompt saved: {wake_path}")
    except OSError as e:
        print(f"      [WARNING] could not write wake prompt: {e}")
    
    # 3. Spawn & Teleport (optional)
    if no_teleport:
        print("[2/4] --no-teleport: skipping tmux spawn")
        print("[3/4] --no-teleport: skipping teleport switch")
        cleanup_gameplan(AIM_ROOT)
        print("\n--- REINCARNATION PIPELINE COMPLETE (no teleport) ---")
        print("    Pulse + vault seal ran; wake prompt on disk; no new agent session.")
        return

    from session_naming import reincarnation_session_name
    session_name = reincarnation_session_name(workspace_dir=workspace)
    spawn_new_agent(workspace, session_name, prompt)
    cleanup_gameplan(AIM_ROOT)
    execute_teleport(current_tmux, session_name)

if __name__ == "__main__":
    main()
