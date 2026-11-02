#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path


def find_aim_root(start_dir=None):
    """
    Discover the active workspace's `joshua_os` directory across POSIX and Windows.
    Terminates safely at filesystem/drive roots (`p.parent == p`).
    """
    start = Path(start_dir or os.getcwd()).resolve()
    for candidate in (start, *start.parents):
        nested = candidate / "joshua_os"
        if (nested / ".aim_core" / "aim_cli.py").is_file() or (nested / "setup.sh").is_file():
            return str(nested)
        if (candidate / ".aim_core" / "aim_cli.py").is_file() or (candidate / "setup.sh").is_file():
            return str(candidate)
    return None


def _resolve_python(aim_root: str) -> str:
    candidates = (
        [
            os.path.join(aim_root, "venv", "Scripts", "python.exe"),
            os.path.join(aim_root, "venv", "bin", "python3"),
            os.path.join(aim_root, "venv", "bin", "python"),
        ]
        if os.name == "nt"
        else [
            os.path.join(aim_root, "venv", "bin", "python3"),
            os.path.join(aim_root, "venv", "bin", "python"),
            os.path.join(aim_root, "venv", "Scripts", "python.exe"),
        ]
    )
    for cand in candidates:
        if os.path.isfile(cand):
            return cand
    return sys.executable


def _read_stdin_nonblocking() -> str:
    if sys.stdin is None or sys.stdin.closed:
        return ""
    try:
        if sys.stdin.isatty():
            return ""
    except Exception:
        pass

    if os.name != "nt":
        try:
            import fcntl
            import select

            if select.select([sys.stdin], [], [], 0.0)[0]:
                fd = sys.stdin.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
                return sys.stdin.read() or ""
            return ""
        except Exception:
            return ""

    # Windows: piped stdin from hook runner reaches EOF once payload is sent
    try:
        return sys.stdin.read() or ""
    except Exception:
        return ""


def main():
    if len(sys.argv) < 2:
        print("{}")
        sys.exit(0)

    hook_script_name = sys.argv[1]
    aim_root = find_aim_root()
    if not aim_root:
        print("{}")
        sys.exit(0)

    script_path = os.path.join(aim_root, "hooks", hook_script_name)
    if not os.path.exists(script_path):
        print("{}")
        sys.exit(0)

    venv_python = _resolve_python(aim_root)
    input_data = _read_stdin_nonblocking()
    cmd = [venv_python, script_path]

    try:
        process = subprocess.run(cmd, input=input_data, text=True, capture_output=True)
        if process.stderr:
            sys.stderr.write(f"\n[A.I.M. HOOK DIAGNOSTIC] {hook_script_name} stderr:\n{process.stderr}\n")

        if process.returncode != 0:
            sys.stderr.write(
                f"[A.I.M. HOOK DIAGNOSTIC] {hook_script_name} failed with exit code {process.returncode}.\n"
            )
            print("{}")
            return

        if process.stdout:
            try:
                json.loads(process.stdout)
                print(process.stdout, end="")
            except json.JSONDecodeError:
                sys.stderr.write(
                    f"[A.I.M. HOOK DIAGNOSTIC] {hook_script_name} returned invalid JSON. Masking output.\n"
                )
                print("{}")
        else:
            print("{}")
    except Exception as e:
        sys.stderr.write(f"\n[A.I.M. HOOK DIAGNOSTIC] Core Router Exception executing {hook_script_name}: {e}\n")
        print("{}")


if __name__ == "__main__":
    main()
