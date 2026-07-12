"""OpenCode harness: spawn opencode in tmux, Enter-only submit (no AGY trust menu)."""
import os
import sys
import subprocess
import signal
import shutil
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
        # Wait for TUI, then paste wake prompt (OpenCode = Enter only)
        for _ in range(20):
            time.sleep(0.4)
            result = subprocess.run(
                ["tmux", "capture-pane", "-p", "-t", session_name],
                capture_output=True,
                text=True,
            )
            out = result.stdout or ""
            if "trust" in out.lower() or "allow" in out.lower():
                # Best-effort: allow prompts
                subprocess.run(["tmux", "send-keys", "-t", session_name, "Enter"], check=False)
                time.sleep(0.3)
            # Ready-ish UI
            if any(x in out for x in ("opencode", "OpenCode", "❯", "Build", "Plan")):
                break

        tmp_file = f"/tmp/reincarnation_prompt_{session_name}.txt"
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(wake_up_prompt)
        subprocess.run(["tmux", "load-buffer", tmp_file], check=True)
        subprocess.run(["tmux", "paste-buffer", "-p", "-t", session_name], check=True)
        time.sleep(0.4)
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Enter"], check=True)
        print(f"      [Success] New agent is awake in tmux session: {session_name}")
    except FileNotFoundError:
        print("[ERROR] 'tmux' is not installed. The Reincarnation Protocol requires tmux.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to spawn tmux session: {e}")
        sys.exit(1)

    print("[3/4] Wake-up prompt injected for opencode vessel...")


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
                subprocess.run(["tmux", "kill-session", "-t", current_session], check=False)
            else:
                print(
                    f"      [Teleport] Clients still on {current_session}; not killing. "
                    f"Attach: tmux attach -t {session_name}"
                )
        except Exception as e:
            print(f"[ERROR] Teleport failed: {e}")
            print(f"    tmux attach-session -t {session_name}")
    else:
        print(
            f"\n[!] You are not in tmux. To view the new agent, run:\n"
            f"    tmux attach-session -t {session_name}"
        )
