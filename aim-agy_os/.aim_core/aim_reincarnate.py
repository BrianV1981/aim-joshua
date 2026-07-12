#!/usr/bin/env python3
import os
import sys
import time
import argparse


def find_aim_root():
    current = os.path.abspath(os.getcwd())
    while current != "/":
        if os.path.exists(os.path.join(current, "aim-agy_os", "setup.sh")):
            return os.path.join(current, "aim-agy_os")
        if os.path.exists(os.path.join(current, "setup.sh")) and os.path.isdir(
            os.path.join(current, ".aim_core")
        ):
            return current
        current = os.path.dirname(current)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


AIM_ROOT = find_aim_root()
sys.path.append(os.path.join(AIM_ROOT, ".aim_core"))

from reincarnation.gameplan_manager import load_and_validate_gameplan, cleanup_gameplan
from reincarnation.background_tasks import trigger_background_pipelines
from reincarnation.context_builder import fetch_issue_context, build_wakeup_prompt
from reincarnation.teleport_engine import (
    get_current_tmux_session,
    spawn_new_agent,
    execute_teleport,
)
from session_naming import reincarnation_session_name


def main():
    parser = argparse.ArgumentParser(description="A.I.M. Reincarnation Protocol (opencode)")
    parser.add_argument(
        "--session-id",
        type=str,
        default=None,
        help="The explicit conversation UUID of the active agent.",
    )
    args = parser.parse_args()

    print("--- A.I.M. REINCARNATION PROTOCOL ---")
    print("\n[!] CONTEXT FADE DETECTED: We are initiating Reincarnation.")

    workspace = os.environ.get("AIM_WORKSPACE", ".")
    # Prefer vessel root (parent of aim-agy_os) for cwd when nested
    vessel_root = (
        os.path.dirname(AIM_ROOT)
        if os.path.basename(AIM_ROOT) == "aim-agy_os"
        else AIM_ROOT
    )
    if workspace == ".":
        workspace = vessel_root

    gameplan = load_and_validate_gameplan(AIM_ROOT)

    print("[0/4] Giving the CLI filesystem time to sync the final agent turn...")
    time.sleep(3)

    current_tmux = get_current_tmux_session()
    trigger_background_pipelines(AIM_ROOT, workspace, args.session_id)
    issues = fetch_issue_context(AIM_ROOT)
    prompt = build_wakeup_prompt(gameplan, issues)

    os.environ.setdefault("AIM_VESSEL_CLI", "opencode")
    session_name = reincarnation_session_name(workspace_dir=workspace)
    spawn_new_agent(workspace, session_name, prompt)
    cleanup_gameplan(AIM_ROOT)
    execute_teleport(current_tmux, session_name)


if __name__ == "__main__":
    main()
