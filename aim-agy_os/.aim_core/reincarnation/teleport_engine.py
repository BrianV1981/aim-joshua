"""OpenCode reincarnation spawn — use `opencode run` (TUI paste/--prompt unreliable)."""
from __future__ import annotations

import os
import shlex
import shutil
import signal
import subprocess
import sys
import time


def get_current_tmux_session():
    if not os.environ.get("TMUX"):
        return None
    try:
        result = subprocess.run(
            ["tmux", "display-message", "-p", "#S"],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def _opencode_bin() -> str:
    override = (os.environ.get("AIM_VESSEL_CLI_PATH") or "").strip()
    if override:
        return override
    found = shutil.which("opencode")
    if found:
        return found
    home = os.path.expanduser("~/.opencode/bin/opencode")
    return home if os.path.isfile(home) else "opencode"


def _pane_text(session_name: str) -> str:
    result = subprocess.run(
        ["tmux", "capture-pane", "-t", session_name, "-p", "-J", "-S", "-60"],
        capture_output=True,
        text=True,
    )
    return result.stdout or ""


def spawn_new_agent(workspace, session_name, wake_up_prompt):
    """
    Spawn OpenCode with the wake mandate as a native first user message.

    Empirical (2026-07-12 fleet e2e):
    - tmux paste-buffer into OpenCode TUI does NOT submit turns
    - `opencode --prompt` often does not surface the mandate in the TUI
    - `opencode run --auto "…"` DOES deliver the message (verified PINEAPPLE_OK)

    We start: opencode run --interactive --auto -f REINCARNATION_WAKE.md "<short>"
    """
    print("[2/4] Spawning new host vessel (tmux + opencode run)...")
    cli = _opencode_bin()
    workspace = os.path.abspath(workspace)

    wake_path = os.path.join(workspace, "REINCARNATION_WAKE.md")
    gameplan_temp = os.path.join(
        workspace, "aim-agy_os", ".aim_core", "temp", "REINCARNATION_GAMEPLAN.md"
    )
    os.makedirs(os.path.dirname(gameplan_temp), exist_ok=True)
    with open(wake_path, "w", encoding="utf-8") as f:
        f.write(wake_up_prompt)
    if "--- REINCARNATION GAMEPLAN ---" in wake_up_prompt:
        body = wake_up_prompt.split("--- REINCARNATION GAMEPLAN ---", 1)[1]
        if "--- LIVE ISSUE TRACKER ---" in body:
            body = body.split("--- LIVE ISSUE TRACKER ---", 1)[0]
        with open(gameplan_temp, "w", encoding="utf-8") as f:
            f.write(body.strip() + "\n")

    # NOTE: do NOT use -f with a free-text message — OpenCode treats the text as a filename.
    short_msg = (
        "REINCARNATION WAKE. Read the file REINCARNATION_WAKE.md in this directory "
        "and execute every step completely (doctor, wiki marker search, report "
        "HANDOFF_RECEIVED vessel=opencode WAKE_OK). "
        "Also read aim-agy_os/.aim_core/temp/REINCARNATION_GAMEPLAN.md if present. "
        "Do not invent unrelated tasks."
    )

    shell_cmd = (
        f"exec {shlex.quote(cli)} run --interactive --auto {shlex.quote(short_msg)}"
    )

    try:
        subprocess.run(
            [
                "tmux",
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                workspace,
                "bash",
                "-lc",
                shell_cmd,
            ],
            check=True,
        )
    except FileNotFoundError:
        print("[ERROR] tmux not installed")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to spawn tmux session: {e}")
        sys.exit(1)

    print(f"      [Spawn] session={session_name}")
    print(f"      [Wake] file={wake_path}")
    print("      [Method] opencode run --interactive --auto -f REINCARNATION_WAKE.md")

    ok = False
    for i in range(50):
        time.sleep(1)
        pane = _pane_text(session_name)
        low = pane.lower()
        if any(
            x in pane
            for x in (
                "HANDOFF_RECEIVED",
                "REINCARNATION_WAKE",
                "REINCARNATION GAMEPLAN",
                "FLEET_LIFE_MARKER",
                "DOCTOR COMPLETE",
                "Wake up",
                "MANDATE",
                "REINCARNATION WAKE",
            )
        ) or "reincarnation_wake.md" in low:
            ok = True
            print(f"      [Success] Wake activity visible in pane (t+{i+1}s)")
            break
        if "permission required" in low or "allow always" in low:
            subprocess.run(
                ["tmux", "send-keys", "-t", session_name, "Enter"], check=False
            )

    if ok:
        print(f"      [Success] New agent is awake in tmux session: {session_name}")
    else:
        print(
            f"      [PARTIAL] Session {session_name} up; wake not verified in capture-pane. "
            f"Attach: tmux attach -t {session_name}"
        )
    print("[3/4] Wake-up prompt handled for opencode vessel...")


def execute_teleport(current_session, session_name):
    print("[4/4] Executing Teleport Sequence...")
    time.sleep(1)

    if os.environ.get("AIM_REINCARNATE_NO_TELEPORT") == "1":
        print(
            f"      [NO_TELEPORT] Leaving current session intact. "
            f"New vessel: tmux attach -t {session_name}"
        )
        return

    if os.environ.get("TMUX") and current_session:
        print(
            f"      [Teleport] Switching clients {current_session} → {session_name}..."
        )
        try:
            clients = (
                subprocess.run(
                    [
                        "tmux",
                        "list-clients",
                        "-t",
                        current_session,
                        "-F",
                        "#{client_name}",
                    ],
                    capture_output=True,
                    text=True,
                )
                .stdout.strip()
                .split("\n")
            )
            for client in clients:
                client = client.strip()
                if client:
                    subprocess.run(
                        ["tmux", "switch-client", "-c", client, "-t", session_name],
                        check=True,
                    )
            time.sleep(1)
            remaining = subprocess.run(
                ["tmux", "list-clients", "-t", current_session],
                capture_output=True,
                text=True,
            )
            if not remaining.stdout.strip():
                subprocess.run(
                    ["tmux", "kill-session", "-t", current_session], check=False
                )
        except Exception as e:
            print(f"[ERROR] Teleport failed: {e}")
            print(f"    tmux attach-session -t {session_name}")
    else:
        print(f"\n[!] Attach: tmux attach-session -t {session_name}")
        try:
            input("\nPress Enter to exit parent...")
        except (EOFError, KeyboardInterrupt):
            pass
        try:
            os.kill(os.getppid(), signal.SIGTERM)
        except Exception as e:
            print(f"[ERROR] self-terminate: {e}")
