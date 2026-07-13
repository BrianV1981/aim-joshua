"""OpenCode harness: spawn reincarnated vessel with native --prompt (not fragile TUI paste)."""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time


def get_current_tmux_session():
    current_session = None
    if os.environ.get("TMUX"):
        try:
            result = subprocess.run(
                ["tmux", "display-message", "-p", "#S"],
                capture_output=True,
                text=True,
            )
            current_session = result.stdout.strip()
        except Exception:
            pass
    return current_session


def _opencode_bin():
    override = (os.environ.get("AIM_VESSEL_CLI_PATH") or "").strip()
    if override:
        return override
    found = shutil.which("opencode")
    if found:
        return found
    home = os.path.expanduser("~/.opencode/bin/opencode")
    if os.path.isfile(home):
        return home
    return "opencode"


def _pane_text(session_name: str) -> str:
    result = subprocess.run(
        ["tmux", "capture-pane", "-t", session_name, "-p", "-J", "-S", "-50"],
        capture_output=True,
        text=True,
    )
    return result.stdout or ""


def spawn_new_agent(workspace, session_name, wake_up_prompt):
    """
    Start OpenCode with the wake mandate as a *native* first message.

    OpenCode's TUI does not reliably accept multi-line tmux paste-buffer as a
    submitted user turn (fleet e2e 2026-07-12). Use CLI --prompt / run instead.
    """
    print("[2/4] Spawning new host vessel (tmux session) with OpenCode...")
    cli = _opencode_bin()
    workspace = os.path.abspath(workspace)

    # Persist mandate on disk so the agent can re-read if UI truncates
    wake_path = os.path.join(workspace, "REINCARNATION_WAKE.md")
    gameplan_temp = os.path.join(
        workspace, "aim-agy_os", ".aim_core", "temp", "REINCARNATION_GAMEPLAN.md"
    )
    os.makedirs(os.path.dirname(gameplan_temp), exist_ok=True)
    with open(wake_path, "w", encoding="utf-8") as f:
        f.write(wake_up_prompt)
    # Also keep gameplan extract for disk readers
    if "--- REINCARNATION GAMEPLAN ---" in wake_up_prompt:
        body = wake_up_prompt.split("--- REINCARNATION GAMEPLAN ---", 1)[1]
        if "--- LIVE ISSUE TRACKER ---" in body:
            body = body.split("--- LIVE ISSUE TRACKER ---", 1)[0]
        with open(gameplan_temp, "w", encoding="utf-8") as f:
            f.write(body.strip() + "\n")

    # Prefer interactive TUI with initial prompt + auto-approve (reincarnation YOLO)
    # Fall back to: opencode run --interactive with file attach
    cmd = [
        "tmux",
        "new-session",
        "-d",
        "-s",
        session_name,
        "-c",
        workspace,
        cli,
        "--auto",
        "--prompt",
        wake_up_prompt,
    ]

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("[ERROR] 'tmux' is not installed.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to spawn with --prompt: {e}; trying run --interactive")
        # Fallback: run interactive with short pointer + file
        short = (
            "Wake up. Read REINCARNATION_WAKE.md in the workspace root and execute it fully. "
            "Also read aim-agy_os/.aim_core/temp/REINCARNATION_GAMEPLAN.md. "
            "Report HANDOFF_RECEIVED vessel=opencode when doctor/wiki checks done."
        )
        fallback = [
            "tmux",
            "new-session",
            "-d",
            "-s",
            session_name,
            "-c",
            workspace,
            cli,
            "run",
            "--interactive",
            "--auto",
            "-f",
            wake_path,
            short,
        ]
        try:
            subprocess.run(fallback, check=True)
        except subprocess.CalledProcessError as e2:
            print(f"[ERROR] Fallback spawn failed: {e2}")
            sys.exit(1)

    print(f"      [Spawn] session={session_name} wake_file={wake_path}")

    # Wait and verify mandate landed (fingerprint in pane or agent working)
    fingerprint = "REINCARNATION GAMEPLAN"
    if fingerprint not in wake_up_prompt:
        fingerprint = "HANDOFF_RECEIVED"
    ok = False
    for i in range(30):
        time.sleep(1.0)
        pane = _pane_text(session_name)
        if any(
            x in pane
            for x in (
                fingerprint,
                "Wake up",
                "MANDATE",
                "REINCARNATION_WAKE",
                "HANDOFF_RECEIVED",
                "doctor",
            )
        ):
            ok = True
            print(f"      [Success] Wake content/activity visible in pane (t+{i+1}s)")
            break
        # Permission modal
        if "allow" in pane.lower() or "permission" in pane.lower():
            subprocess.run(
                ["tmux", "send-keys", "-t", session_name, "Enter"], check=False
            )

    if not ok:
        # Last-resort: short paste of disk pointer (not full novel)
        print("      [Fallback] Native --prompt not visible; pasting disk pointer…")
        short = (
            "Read and execute REINCARNATION_WAKE.md in this workspace. "
            "Then report HANDOFF_RECEIVED vessel=opencode."
        )
        tmp = f"/tmp/reinc_ptr_{session_name}.txt"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(short)
        subprocess.run(["tmux", "send-keys", "-t", session_name, "C-u"], check=False)
        time.sleep(0.2)
        subprocess.run(["tmux", "load-buffer", "-b", "aim_wake", tmp], check=False)
        subprocess.run(
            ["tmux", "paste-buffer", "-b", "aim_wake", "-p", "-t", session_name],
            check=False,
        )
        time.sleep(0.4)
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Enter"], check=False)
        time.sleep(2)
        pane = _pane_text(session_name)
        if "REINCARNATION_WAKE" in pane or "HANDOFF" in pane or "Wake" in pane:
            ok = True
            print("      [Success] Fallback pointer accepted")
        else:
            print(
                f"      [PARTIAL] Session {session_name} is up but wake not verified. "
                f"Attach and run: open REINCARNATION_WAKE.md"
            )

    print("[3/4] Wake-up prompt handled for opencode vessel...")
    if ok:
        print(f"      [Success] New agent is awake in tmux session: {session_name}")


def execute_teleport(current_session, session_name):
    print("[4/4] Executing Teleport Sequence...")
    time.sleep(2)

    if os.environ.get("AIM_REINCARNATE_NO_TELEPORT") == "1":
        print(
            f"      [NO_TELEPORT] Leaving current session intact. "
            f"New vessel: tmux attach -t {session_name}"
        )
        return

    if os.environ.get("TMUX") and current_session:
        print(
            f"      [Teleport] TMUX detected. Switching from {current_session} to {session_name}..."
        )
        try:
            clients_result = subprocess.run(
                ["tmux", "list-clients", "-t", current_session, "-F", "#{client_name}"],
                capture_output=True,
                text=True,
            )
            for client in clients_result.stdout.strip().split("\n"):
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
        print(
            f"\n[!] Not in tmux. Attach with:\n    tmux attach-session -t {session_name}"
        )
        try:
            input("\nPress Enter to exit parent agent...")
        except (EOFError, KeyboardInterrupt):
            pass
        try:
            os.kill(os.getppid(), signal.SIGTERM)
        except Exception as e:
            print(f"[ERROR] Could not self-terminate: {e}")
