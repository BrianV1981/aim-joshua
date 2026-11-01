#!/usr/bin/env python3
"""
Pure-Python cross-platform bootstrap installer for J.O.S.H.U.A.
Supports Windows 10/11, macOS, Linux, and WSL across `clean`, `agent`, and `core` modes.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


REPO_CLONE_URL = "https://github.com/BrianV1981/aim-joshua.git"
CONSUMER_GITIGNORE_ENTRIES = (
    "joshua_os/",
    "aim",
    "aim.ps1",
    "aim.cmd",
    "workspace/",
    "archive/",
)


def is_unsafe_target_dir(target_dir: str, home_dir: str | None = None) -> bool:
    """Refuse installation directly inside $HOME, POSIX `/`, or Windows drive roots (`C:\\`)."""
    raw = (target_dir or "").strip()
    if not raw:
        return True
    if raw in ("/", "\\") or re.match(r"^[A-Za-z]:[/\\]?$", raw):
        return True

    resolved = os.path.abspath(os.path.expanduser(raw)).rstrip("/\\")
    if not resolved or re.match(r"^[A-Za-z]:$", resolved):
        return True

    home_resolved = os.path.abspath(os.path.expanduser(home_dir or "~")).rstrip("/\\")
    if resolved == home_resolved:
        return True
    if os.path.dirname(os.path.abspath(raw)) == os.path.abspath(raw):
        return True
    return False


def resolve_venv_python_path(os_dir: str) -> str:
    candidates = (
        [
            os.path.join(os_dir, "venv", "Scripts", "python.exe"),
            os.path.join(os_dir, "venv", "bin", "python3"),
            os.path.join(os_dir, "venv", "bin", "python"),
        ]
        if os.name == "nt"
        else [
            os.path.join(os_dir, "venv", "bin", "python3"),
            os.path.join(os_dir, "venv", "bin", "python"),
            os.path.join(os_dir, "venv", "Scripts", "python.exe"),
        ]
    )
    return next((c for c in candidates if os.path.isfile(c)), sys.executable)


def build_engine_venv(os_dir: str, python_exe: str | None = None) -> str:
    """Create `joshua_os/venv` and install `requirements.txt` natively across Windows/macOS/Linux."""
    py = python_exe or sys.executable
    os_dir_abs = os.path.abspath(os_dir)
    venv_dir = os.path.join(os_dir_abs, "venv")
    req_file = os.path.join(os_dir_abs, "requirements.txt")

    if sys.platform.startswith("linux") and shutil.which("dpkg"):
        chk = subprocess.run(["dpkg", "-s", "dbus-x11", "libdbus-1-dev"], capture_output=True)
        if chk.returncode != 0 and shutil.which("sudo"):
            sudo_chk = subprocess.run(["sudo", "-n", "true"], capture_output=True)
            if sudo_chk.returncode == 0 and shutil.which("apt-get"):
                subprocess.run(["sudo", "apt-get", "update", "-qq"], check=False)
                subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "-qq", "dbus-x11", "libdbus-1-dev"],
                    check=False,
                )

    if not os.path.isdir(venv_dir):
        print("    [*] Creating Python Virtual Environment...")
        subprocess.run([py, "-m", "venv", venv_dir], check=True)

    venv_py = resolve_venv_python_path(os_dir_abs)
    print("    [*] Installing Python dependencies...")
    subprocess.run([venv_py, "-m", "pip", "install", "-q", "--upgrade", "pip"], check=True)
    if os.path.isfile(req_file):
        subprocess.run([venv_py, "-m", "pip", "install", "-q", "-r", req_file], check=True)
    return venv_py


def _copy_if_missing(src: Path, dst: Path, executable_on_posix: bool = False) -> None:
    if not src.is_file() or dst.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    if executable_on_posix and os.name != "nt":
        os.chmod(dst, 0o755)


def _ensure_gitignore(target: Path) -> None:
    gi_path = target / ".gitignore"
    existing_lines = gi_path.read_text(encoding="utf-8", errors="ignore").splitlines() if gi_path.is_file() else []
    normalized = {ln.strip().rstrip("/") for ln in existing_lines if ln.strip() and not ln.strip().startswith("#")}
    to_append = [e for e in CONSUMER_GITIGNORE_ENTRIES if e.rstrip("/") not in normalized]
    if not to_append:
        return
    with gi_path.open("a", encoding="utf-8") as fh:
        if existing_lines and existing_lines[-1].strip() != "":
            fh.write("\n")
        for item in to_append:
            fh.write(f"{item}\n")


def _seed_memory_wiki_and_lance(target: Path, cli_name: str) -> None:
    pages_dir = target / "memory-wiki" / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    idx = target / "memory-wiki" / "index.md"
    if not idx.is_file():
        idx.write_text(f"# {cli_name} — Memory Wiki Index\n\n## Core Pages\n", encoding="utf-8")
    log = target / "memory-wiki" / "log.md"
    if not log.is_file():
        log.write_text(f"# {cli_name} — Memory Wiki Log\n", encoding="utf-8")
    readme = target / "README.md"
    if not readme.is_file():
        readme.write_text(f"# {cli_name}\n", encoding="utf-8")

    default_lance = target / "joshua_os" / "assets" / "default_lance"
    active_lance = target / "joshua_os" / "memory_lance"
    active_lance.mkdir(parents=True, exist_ok=True)
    if default_lance.is_dir():
        for item in default_lance.iterdir():
            dest_item = active_lance / item.name
            if item.is_dir():
                if dest_item.exists():
                    shutil.rmtree(dest_item)
                shutil.copytree(item, dest_item)
            else:
                shutil.copy2(item, dest_item)


def _register_windows_powershell_alias(target: Path, cli_name: str, home: Path) -> None:
    """Register a convenience PowerShell function in $PROFILE when present on Windows."""
    ps_Launcher = target / "aim.ps1"
    for ps_dir_name in ("PowerShell", "WindowsPowerShell"):
        docs_dir = home / "Documents" / ps_dir_name
        if not docs_dir.is_dir():
            continue
        profile_file = docs_dir / "Microsoft.PowerShell_profile.ps1"
        existing = profile_file.read_text(encoding="utf-8", errors="ignore") if profile_file.is_file() else ""
        fn_line = f'function {cli_name} {{ & "{ps_Launcher}" @args }}'
        marker = f"function {cli_name} "
        if marker not in existing:
            sep = "" if (not existing or existing.endswith("\n")) else "\n"
            profile_file.write_text(f"{existing}{sep}# A.I.M. CLI — {cli_name}\n{fn_line}\n", encoding="utf-8")


def install_project(
    target_dir: str,
    *,
    mode: str = "clean",
    source_dir: str | None = None,
    persona_name: str | None = None,
    skip_deps: bool = False,
    home_dir: str | None = None,
    skip_shell_rc: bool = False,
) -> Path:
    """Install J.O.S.H.U.A. (`clean`, `agent`, or `core`) into `target_dir`."""
    if mode not in ("clean", "agent", "core"):
        raise ValueError(f"Unsupported install mode: {mode!r}")

    if is_unsafe_target_dir(target_dir, home_dir=home_dir):
        raise RuntimeError(
            f"[ERROR] Refusing to install directly in {target_dir}. "
            "Create and cd into a dedicated project folder first."
        )

    target = Path(target_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    cli_name = target.name
    home = Path(home_dir).expanduser().resolve() if home_dir else Path.home()

    temp_clone: Path | None = None
    try:
        if source_dir:
            src_root = Path(source_dir).resolve()
        else:
            temp_clone = target / ".aim_temp_clone"
            if temp_clone.exists():
                shutil.rmtree(temp_clone)
            print("[*] Step 1: Cloning J.O.S.H.U.A. Operating System...")
            subprocess.run(["git", "clone", "--depth", "1", REPO_CLONE_URL, str(temp_clone)], check=True)
            src_root = temp_clone

        src_os = src_root / "joshua_os"
        if not (src_os / ".aim_core").is_dir():
            raise RuntimeError(f"Invalid J.O.S.H.U.A. source directory: {src_root}")

        dst_os = target / "joshua_os"
        print(f"[*] Step 2: Scaffolding Sovereign Environment ({mode} mode)...")

        if mode == "core":
            if src_root != target:
                for entry in src_root.iterdir():
                    if entry.name == ".aim_temp_clone":
                        continue
                    dest_entry = target / entry.name
                    if entry.is_dir():
                        if dest_entry.exists():
                            shutil.rmtree(dest_entry)
                        shutil.copytree(entry, dest_entry)
                    else:
                        shutil.copy2(entry, dest_entry)
            _seed_memory_wiki_and_lance(target, cli_name)
        else:
            excluded = {"tests", "benchmarks", "memory-wiki", "__pycache__", "venv"}
            if mode == "agent":
                excluded.update({"docs", "skills", "workspace"})

            if dst_os.exists():
                shutil.rmtree(dst_os)
            shutil.copytree(
                src_os,
                dst_os,
                ignore=shutil.ignore_patterns(*excluded),
            )

            for wrapper_name in ("aim", "aim.ps1", "aim.cmd"):
                _copy_if_missing(
                    src_root / wrapper_name,
                    target / wrapper_name,
                    executable_on_posix=(wrapper_name == "aim"),
                )

            core_mod_dir = str(dst_os / ".aim_core")
            if core_mod_dir not in sys.path:
                sys.path.insert(0, core_mod_dir)
            import aim_init

            if mode == "agent" and persona_name:
                aim_init.provision_agents_md(str(target), persona_name=persona_name)
            else:
                _copy_if_missing(src_root / "AGENTS.md", target / "AGENTS.md")
                aim_init.provision_agents_md(str(target), persona_name=None)

            _copy_if_missing(src_root / "TOOLS.md", target / "TOOLS.md")

            if not (target / ".git").exists():
                subprocess.run(["git", "init"], cwd=str(target), check=True, capture_output=True)

            _ensure_gitignore(target)
            _seed_memory_wiki_and_lance(target, cli_name)

        if not skip_deps:
            build_engine_venv(str(dst_os))

        core_mod_dir = str(dst_os / ".aim_core")
        if core_mod_dir not in sys.path:
            sys.path.insert(0, core_mod_dir)
        import register_mcp

        register_mcp.register_all_harnesses(
            project_root=str(target),
            home_dir=str(home) if home_dir else None,
            detect_path_binaries=(home_dir is None),
        )

        # Register AGY trusted workspace when running against real HOME
        if home_dir is None:
            try:
                import agy_workspace_trust

                agy_workspace_trust.ensure_workspace_trusted(str(target), quiet=True)
            except Exception:
                pass

        if not skip_shell_rc:
            if os.name == "nt":
                _register_windows_powershell_alias(target, cli_name, home)
            else:
                alias_sh = dst_os / "link_cli_alias.sh"
                if alias_sh.is_file() and shutil.which("bash"):
                    subprocess.run(["bash", str(alias_sh), str(target), cli_name], check=False)

        return target
    finally:
        if temp_clone and temp_clone.exists():
            shutil.rmtree(temp_clone, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="J.O.S.H.U.A. Cross-Platform Bootstrap Installer")
    parser.add_argument("--mode", choices=["clean", "agent", "core"], default="clean")
    parser.add_argument("--target", default=os.getcwd(), help="Target project directory (default: cwd)")
    parser.add_argument("--source", default=None, help="Optional local aim-joshua source checkout")
    parser.add_argument("--persona", default=None, help="Optional Co-Agent persona name for --mode agent")
    parser.add_argument("--skip-deps", action="store_true", help="Skip Python venv creation and pip install")
    parser.add_argument("--home", default=None, help="Override HOME directory (testing)")
    parser.add_argument("--skip-shell-rc", action="store_true", help="Skip shell RC / PowerShell profile alias registration")
    args = parser.parse_args(argv)

    try:
        installed = install_project(
            target_dir=args.target,
            mode=args.mode,
            source_dir=args.source,
            persona_name=args.persona,
            skip_deps=args.skip_deps,
            home_dir=args.home,
            skip_shell_rc=args.skip_shell_rc,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("")
    print("--- INSTALLATION COMPLETE ---")
    print(f"Installed J.O.S.H.U.A. ({args.mode}) into {installed}")
    if os.name == "nt":
        print("Next steps (PowerShell / CMD):")
        print("  1. .\\aim.ps1 doctor   (or: aim.cmd doctor)")
        print("  2. Customize AGENTS.md and run: .\\aim.ps1 index")
    else:
        print("Next steps:")
        print("  1. source ~/.bashrc   (or ~/.zshrc)")
        print(f"  2. ./aim doctor       (or: {installed.name} doctor)")
        print("  3. Customize AGENTS.md and run: ./aim index")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
