"""OpenCode harness: spawn opencode in tmux; reliable Enter-only wake injection."""
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
        ["tmux", "capture-pane", "-t", session_name, "-p", "-J", "-S", "-40"],
        capture_output=True,
        text=True,
    )
    return result.stdout or ""


def _wait_for_opencode_ready(session_name: str, timeout_s: float = 45.0) -> bool:
    """Poll until OpenCode looks idle enough to accept a paste (not just started)."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        out = _pane_text(session_name).lower()
        # Permission / trust UI — confirm with Enter
        if any(
            x in out
            for x in (
                "permission required",
                "allow once",
                "allow always",
                "trust this",
                "do you trust",
            )
        ):
            # Prefer Allow always when present (Right then Enter is fragile; Enter often confirms default)
            subprocess.run(
                ["tmux", "send-keys", "-t", session_name, "Enter"], check=False
            )
            time.sleep(0.8)
            continue
        # Idle composer / ready markers for OpenCode TUI
        if any(
            x in out
            for x in (
                "ctrl+p commands",
                "build ·",
                "plan ·",
                "what's the next",
                "standing by",
            )
        ):
            # Avoid injecting while a tool is clearly mid-run
            if "esc interrupt" in out and "■" in out:
                time.sleep(0.5)
                continue
            return True
        time.sleep(0.5)
    return False


def inject_prompt(session_name: str, wake_up_prompt: str, retries: int = 3) -> bool:
    """
    Paste wake prompt into OpenCode with bracketed paste + Enter (never Escape).
    Verify a distinctive fragment appears in the pane; retry if not.
    """
    tmp_file = f"/tmp/reincarnation_prompt_{session_name}.txt"
    with open(tmp_file, "w", encoding="utf-8") as f:
        f.write(wake_up_prompt)

    # Short distinctive fingerprint for verify
    fingerprint = "REINCARNATION GAMEPLAN"
    if fingerprint not in wake_up_prompt:
        fingerprint = wake_up_prompt.strip().splitlines()[0][:40] if wake_up_prompt.strip() else "Wake up"

    for attempt in range(1, retries + 1):
        print(f"      [Inject] attempt {attempt}/{retries} → {session_name}")
        # Clear half-typed input
        subprocess.run(["tmux", "send-keys", "-t", session_name, "C-u"], check=False)
        time.sleep(0.2)
        subprocess.run(["tmux", "load-buffer", "-b", "aim_reinc_wake", tmp_file], check=True)
        # Bracketed paste (-p) is required for reliable multi-line injection
        subprocess.run(
            ["tmux", "paste-buffer", "-b", "aim_reinc_wake", "-p", "-t", session_name],
            check=True,
        )
        time.sleep(0.6)
        # OpenCode / Grok family: Enter only (Escape cancels)
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Enter"], check=True)
        time.sleep(1.2)

        pane = _pane_text(session_name)
        if fingerprint in pane or "Wake up" in pane or "MANDATE" in pane:
            print(f"      [Inject] verified fingerprint in pane: {fingerprint!r}")
            return True
        print("      [Inject] fingerprint not visible yet; retrying…")
        time.sleep(1.0)

    print("[WARNING] Wake prompt injection could not be verified in pane.")
    return False


def spawn_new_agent(workspace, session_name, wake_up_prompt):
    print("[2/4] Spawning new host vessel (tmux session) with OpenCode...")
    cli = _opencode_bin()
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
                cli,
            ],
            check=True,
        )
    except FileNotFoundError:
        print("[ERROR] 'tmux' is not installed. The Reincarnation Protocol requires tmux.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to spawn tmux session: {e}")
        sys.exit(1)

    print("      [Wait] OpenCode TUI ready for input…")
    ready = _wait_for_opencode_ready(session_name, timeout_s=50.0)
    if not ready:
        print("[WARNING] OpenCode readiness timeout — injecting anyway.")

    ok = inject_prompt(session_name, wake_up_prompt, retries=3)
    if ok:
        print(f"      [Success] New agent is awake in tmux session: {session_name}")
    else:
        print(
            f"      [PARTIAL] Session {session_name} exists but wake prompt may not have submitted. "
            f"Manual: tmux attach -t {session_name}"
        )
    print("[3/4] Wake-up prompt handled for opencode vessel...")


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
            f"      [Teleport] TMUX detected. Switching clients from {current_session} to {session_name}..."
        )
        try:
            clients_result = subprocess.run(
                ["tmux", "list-clients", "-t", current_session, "-F", "#{client_name}"],
                capture_output=True,
                text=True,
            )
            clients = clients_result.stdout.strip().split("\n")
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
        print(
            f"\n[!] You are not in tmux. To view the new agent, run:\n"
            f"    tmux attach-session -t {session_name}"
        )
        try:
            input("\nPress Enter to safely exit this session and kill the current agent...")
        except (EOFError, KeyboardInterrupt):
            pass
        parent_pid = os.getppid()
        try:
            os.kill(parent_pid, signal.SIGTERM)
        except Exception as e:
            print(f"[ERROR] Could not self-terminate: {e}")
