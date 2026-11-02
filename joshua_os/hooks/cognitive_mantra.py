#!/usr/bin/env python3
import json
import os
import subprocess
import sys

# --- VENV BOOTSTRAP ---
hook_dir = os.path.dirname(os.path.abspath(__file__))
aim_root = os.path.dirname(hook_dir)
venv_python = (
    os.path.join(aim_root, "venv", "Scripts", "python.exe")
    if os.name == "nt"
    else os.path.join(aim_root, "venv", "bin", "python3")
)

input_data = "" if (sys.stdin is None or sys.stdin.closed or sys.stdin.isatty()) else sys.stdin.read()

if os.path.exists(venv_python) and os.path.abspath(sys.executable) != os.path.abspath(venv_python):
    try:
        process = subprocess.run([venv_python] + sys.argv, input=input_data, text=True, capture_output=True)
        if process.stdout.strip():
            print(process.stdout)
        else:
            print(json.dumps({}))
        sys.exit(0)
    except Exception:
        print(json.dumps({}))
        sys.exit(0)

core_dir = os.path.join(aim_root, ".aim_core")
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

try:
    from config_utils import CONFIG
except ImportError:
    CONFIG = {"settings": {}}


def count_tool_calls(history):
    count = 0
    for msg in history:
        calls = msg.get("toolCalls") or msg.get("tool_calls") or []
        count += len(calls)
    return count


def main():
    try:
        mantra_cfg = CONFIG.get("settings", {}).get("cognitive_mantra", {"enabled": True, "mantra_interval": 50})
        if not mantra_cfg.get("enabled", True):
            print(json.dumps({}))
            return
        mantra_interval = mantra_cfg.get("mantra_interval", 50)

        if not input_data:
            print(json.dumps({}))
            return

        data = json.loads(input_data)
        history = data.get("messages", []) or data.get("session_history", [])

        if not history and "transcript_path" in data:
            try:
                with open(data["transcript_path"], "r", encoding="utf-8") as f:
                    transcript = json.load(f)
                    history = transcript.get("messages", [])
            except Exception as e:
                print(f"Transcript load error: {e}", file=sys.stderr)

        if not history:
            print(json.dumps({}))
            return

        tool_count = count_tool_calls(history)
        private_dir = os.path.join(aim_root, "hooks", ".state")
        os.makedirs(private_dir, exist_ok=True)
        state_file = os.path.join(private_dir, "mantra_state.json")

        state = {"last_mantra": 0, "session_id": data.get("sessionId", "")}
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as sf:
                    disk_state = json.load(sf)
                    if disk_state.get("session_id") == state["session_id"]:
                        state = disk_state
            except Exception as e:
                print(f"State load error: {e}", file=sys.stderr)

        if tool_count > 0 and (tool_count - state["last_mantra"] >= mantra_interval):
            state["last_mantra"] = tool_count
            with open(state_file, "w", encoding="utf-8") as sf:
                json.dump(state, sf)

            project_agents = os.path.join(os.path.dirname(aim_root), "AGENTS.md")
            os_agents = os.path.join(aim_root, "AGENTS.md")
            agents_path = project_agents if os.path.isfile(project_agents) else os_agents
            agents_content = ""
            if os.path.isfile(agents_path):
                try:
                    with open(agents_path, "r", encoding="utf-8") as gf:
                        agents_content = gf.read()
                except Exception as e:
                    print(f"AGENTS.md load error: {e}", file=sys.stderr)

            mantra = (
                f"\n\n[A.I.M. MANTRA PROTOCOL]: You have executed {tool_count} autonomous tool calls. "
                "To prevent behavioral drift, review and adhere strictly to the system instructions below "
                "before continuing.\n\n--- SYSTEM INSTRUCTIONS ---\n"
                f"{agents_content}"
            )
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {"additionalContext": mantra},
                        "systemMessage": f"A.I.M. Mantra Protocol triggered at {tool_count} tool calls.",
                    }
                )
            )
            return

        print(json.dumps({}))
    except Exception:
        print(json.dumps({}))


if __name__ == "__main__":
    main()
