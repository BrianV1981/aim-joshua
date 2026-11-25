#!/usr/bin/env python3
"""Shared, versioned MCP engine (Issue #141).

One engine copy is installed under ``~/.aim/engine`` (override with
``AIM_ENGINE_ROOT``) and every harness registers *that* path. Project data
(``<project>/joshua_os/memory_lance``) stays strictly per-project: the MCP
server resolves the database from the active workspace and fails closed when
the project has no index. The engine never stores or borrows another
project's memory.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ENGINE_DIRNAME = "engine"
ENGINE_META = "engine.json"
REQUIREMENTS_STAMP = "requirements.sha256"

_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "temp", "CONFIG.json", ".DS_Store")
_PAYLOAD_FILES = ("requirements.txt", "setup.sh", "VERSION")


def engine_root(home_dir: str | None = None, explicit: str | None = None) -> str:
    """Resolve the shared engine root: explicit arg -> AIM_ENGINE_ROOT -> ~/.aim/engine."""
    chosen = explicit or os.environ.get("AIM_ENGINE_ROOT", "").strip()
    if chosen:
        return os.path.abspath(os.path.expanduser(chosen))
    home = os.path.abspath(os.path.expanduser(home_dir or "~"))
    return os.path.join(home, ".aim", ENGINE_DIRNAME)


def engine_os_dir(root: str | None = None) -> str:
    return os.path.join(root or engine_root(), "joshua_os")


def mcp_script_path(root: str | None = None) -> str:
    return os.path.join(engine_os_dir(root), ".aim_core", "mcp_lancedb.py")


def venv_python_path(root: str | None = None) -> str:
    """Return the engine venv interpreter or '' when the venv is missing."""
    os_dir = engine_os_dir(root)
    candidates = (
        ("venv", "Scripts", "python.exe"),
        ("venv", "bin", "python3"),
        ("venv", "bin", "python"),
    )
    if os.name != "nt":
        candidates = (
            ("venv", "bin", "python3"),
            ("venv", "bin", "python"),
            ("venv", "Scripts", "python.exe"),
        )
    for parts in candidates:
        candidate = os.path.join(os_dir, *parts)
        if os.path.isfile(candidate):
            return candidate
    return ""


def engine_paths(root: str | None = None) -> tuple[str, str]:
    """Return ``(venv_python, mcp_script)`` for the shared engine."""
    return venv_python_path(root), mcp_script_path(root)


def _read_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _read_version(source_os_dir: str) -> str:
    for candidate in (
        os.path.join(source_os_dir, "VERSION"),
        os.path.join(os.path.dirname(os.path.abspath(source_os_dir)), "VERSION"),
    ):
        version = _read_text(candidate)
        if version:
            return version
    return "0.0.0"


def _version_tuple(version: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", version or "")
    return tuple(int(n) for n in numbers[:4]) if numbers else (0,)


def installed_version(root: str | None = None) -> str:
    engine_os = engine_os_dir(root)
    return (
        _read_text(os.path.join(engine_os, "VERSION"))
        or _read_text(os.path.join(root or engine_root(), "VERSION"))
        or ""
    )


def is_installed(root: str | None = None) -> bool:
    return bool(venv_python_path(root)) and os.path.isfile(mcp_script_path(root))


def _requirements_hash(path: str) -> str:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return ""


def status(root: str | None = None) -> dict:
    resolved = root or engine_root()
    return {
        "root": resolved,
        "os_dir": engine_os_dir(resolved),
        "version": installed_version(resolved) or "missing",
        "venv": venv_python_path(resolved),
        "script": mcp_script_path(resolved),
        "installed": is_installed(resolved),
    }


def install_engine(
    source_os_dir: str,
    root: str | None = None,
    *,
    force: bool = False,
    build: bool = True,
    python_exe: str | None = None,
) -> dict:
    """Install/refresh the shared engine from ``source_os_dir``.

    Copies the engine code (never a project's ``CONFIG.json`` or database),
    rebuilds the venv only when dependencies changed, refuses silent
    downgrades, and records the installed version in ``engine.json``.
    """
    source = os.path.abspath(source_os_dir)
    source_core = os.path.join(source, ".aim_core")
    if not os.path.isfile(os.path.join(source_core, "mcp_lancedb.py")):
        raise ValueError(f"Invalid engine source '{source}': missing .aim_core/mcp_lancedb.py")

    dest_root = engine_root(explicit=root)
    dest_os = engine_os_dir(dest_root)
    source_version = _read_version(source)
    current_version = installed_version(dest_root)

    if current_version and _version_tuple(source_version) < _version_tuple(current_version) and not force:
        raise RuntimeError(
            f"Refusing to downgrade shared engine {current_version} -> {source_version} "
            f"(re-run with --force to override)"
        )

    os.makedirs(dest_os, exist_ok=True)
    dest_core = os.path.join(dest_os, ".aim_core")
    if os.path.isdir(dest_core):
        shutil.rmtree(dest_core)
    shutil.copytree(source_core, dest_core, ignore=_IGNORE)

    for filename in _PAYLOAD_FILES:
        source_file = os.path.join(source, filename)
        if os.path.isfile(source_file):
            shutil.copy2(source_file, os.path.join(dest_os, filename))

    Path(os.path.join(dest_os, "VERSION")).write_text(source_version, encoding="utf-8")

    built = False
    if build:
        requirements = os.path.join(dest_os, "requirements.txt")
        stamp_path = os.path.join(dest_root, REQUIREMENTS_STAMP)
        wanted_hash = _requirements_hash(requirements)
        have_venv = bool(venv_python_path(dest_root))
        if force or not have_venv or _read_text(stamp_path) != wanted_hash:
            from bootstrap_install import build_engine_venv

            build_engine_venv(dest_os, python_exe=python_exe)
            Path(stamp_path).write_text(wanted_hash, encoding="utf-8")
            built = True

    metadata = {
        "version": source_version,
        "source": source,
        "engine_root": dest_root,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "built": built,
    }
    Path(os.path.join(dest_root, ENGINE_META)).write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )

    return {
        "root": dest_root,
        "os_dir": dest_os,
        "version": source_version,
        "venv": venv_python_path(dest_root),
        "script": mcp_script_path(dest_root),
        "built": built,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Manage the shared J.O.S.H.U.A. MCP engine.")
    parser.add_argument("action", nargs="?", default="status", choices=("status", "sync", "install", "update"))
    parser.add_argument("--source", default=None, help="Engine source joshua_os/ directory (defaults to this install)")
    parser.add_argument("--engine-root", default=None, help="Override the shared engine root")
    parser.add_argument("--force", action="store_true", help="Allow downgrades / rebuild the venv")
    parser.add_argument("--skip-deps", action="store_true", help="Copy code without touching the venv")
    args = parser.parse_args(argv)

    if args.action == "status":
        info = status(args.engine_root)
        print("--- SHARED MCP ENGINE ---")
        print(f"Root:    {info['root']}")
        print(f"Version: {info['version']}")
        print(f"Venv:    {info['venv'] or '[missing]'}")
        print(f"Script:  {info['script']}")
        print(f"Status:  {'OK' if info['installed'] else 'NOT INSTALLED'}")
        if not info["installed"]:
            print("Fix: ./aim engine sync")
        return 0

    source = args.source or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    info = install_engine(
        source,
        root=args.engine_root,
        force=args.force,
        build=not args.skip_deps,
    )
    print(f"[SUCCESS] Shared MCP engine {info['version']} at {info['root']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
