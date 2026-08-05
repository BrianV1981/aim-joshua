import subprocess
import time
import os

def spawn_coagent(name, project_dir, prompt):
    if not os.path.isdir(project_dir):
        return {"error": f"Project directory not found: {project_dir}"}

    result = subprocess.run(["tmux", "has-session", "-t", name], capture_output=True)
    if result.returncode == 0:
        return {"error": f"Session '{name}' already exists."}

    # Folder trust is NOT covered by --dangerously-skip-permissions
    try:
        from agy_workspace_trust import prepare_agy_spawn, dismiss_trust_prompt_tmux

        project_dir = prepare_agy_spawn(project_dir)
    except Exception as te:
        print(f"[TRUST] WARN prepare_agy_spawn: {te}")
        dismiss_trust_prompt_tmux = None  # type: ignore

    cmd = [
        "tmux",
        "new-session",
        "-d",
        "-s",
        name,
        "-c",
        project_dir,
        "agy",
        "--dangerously-skip-permissions",
    ]
    subprocess.run(cmd, check=True)

    if dismiss_trust_prompt_tmux:
        try:
            dismiss_trust_prompt_tmux(name)
        except Exception:
            pass
    time.sleep(1)

    if prompt:
        send_message(name, prompt)

    return {"status": "spawned", "session": name, "cwd": project_dir}

def check_idle(session_name):
    result = subprocess.run(["tmux", "capture-pane", "-t", session_name, "-p", "-S", "-5"], capture_output=True, text=True)
    if result.returncode != 0:
        return False
    lines = result.stdout.strip().split('\n')
    if not lines:
        return False
    last_line = lines[-1].strip()
    return last_line.endswith('$') or last_line.endswith('>') or last_line.endswith('#') or last_line.endswith(':')

def send_message(session_name, message):
    max_retries = 6
    idle = False
    for _ in range(max_retries):
        if check_idle(session_name):
            idle = True
            break
        time.sleep(5)
        
    if not idle:
        return {"error": f"Session '{session_name}' is busy executing a command. Knock Protocol aborted to prevent terminal clobbering."}

    tmpfile = f"/tmp/coagent_{session_name}_{int(time.time())}.txt"
    with open(tmpfile, "w") as f:
        f.write(message)
    subprocess.run(["tmux", "load-buffer", tmpfile], check=True)
    subprocess.run(["tmux", "paste-buffer", "-t", session_name], check=True)
    time.sleep(0.5)
    subprocess.run(["tmux", "send-keys", "-t", session_name, "Enter"], check=True)
    try:
        os.remove(tmpfile)
    except:
        pass
    return {"status": "sent", "session": session_name, "length": len(message)}

def capture_output(session_name, lines=500):
    result = subprocess.run(["tmux", "capture-pane", "-t", session_name, "-p", "-S", f"-{lines}"], capture_output=True, text=True)
    return {"session": session_name, "output": result.stdout}

def check_coagent(session_name):
    result = subprocess.run(["tmux", "has-session", "-t", session_name], capture_output=True)
    return {"session": session_name, "alive": result.returncode == 0}

def kill_coagent(session_name):
    result = subprocess.run(["tmux", "has-session", "-t", session_name], capture_output=True)
    if result.returncode != 0:
        return {"error": f"Session '{session_name}' does not exist."}
    subprocess.run(["tmux", "kill-session", "-t", session_name], check=True)
    return {"status": "killed", "session": session_name}

def list_sessions():
    result = subprocess.run(["tmux", "list-sessions", "-F", "#{session_name}"], capture_output=True, text=True)
    sessions = [s for s in result.stdout.strip().split("\n") if s]
    return {"sessions": sessions}
