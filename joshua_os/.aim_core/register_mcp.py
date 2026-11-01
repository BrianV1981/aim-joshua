#!/usr/bin/env python3
"""
Cross-platform, multi-harness MCP registration for J.O.S.H.U.A. (`search_lancedb`).

Registers the project's `joshua_os/venv` Python + `mcp_lancedb.py` across detected
LLM harnesses (Antigravity IDE/CLI, Grok CLI, OpenAI Codex CLI, OpenCode, and
existing Cursor / Claude Code configs) without polluting unconfigured tools.
Automatically self-heals relative or broken paths from deleted sandboxes while
preserving healthy existing absolute registrations unless `--force` is passed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    tomllib = None  # type: ignore


SERVER_NAME = "search_lancedb"


def resolve_mcp_target(project_root: str | None = None) -> tuple[str, str]:
    """Return `(venv_python_path, mcp_lancedb_script_path)` for `project_root`."""
    if project_root:
        proj = os.path.abspath(project_root)
    else:
        proj = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    os_root = os.path.join(proj, "joshua_os")
    candidates = (
        [
            os.path.join(os_root, "venv", "Scripts", "python.exe"),
            os.path.join(os_root, "venv", "bin", "python3"),
            os.path.join(os_root, "venv", "bin", "python"),
        ]
        if os.name == "nt"
        else [
            os.path.join(os_root, "venv", "bin", "python3"),
            os.path.join(os_root, "venv", "bin", "python"),
            os.path.join(os_root, "venv", "Scripts", "python.exe"),
        ]
    )
    venv_py = next((c for c in candidates if os.path.isfile(c)), sys.executable)
    mcp_script = os.path.join(os_root, ".aim_core", "mcp_lancedb.py")
    return os.path.abspath(venv_py), os.path.abspath(mcp_script)


def _is_healthy_existing_entry(cmd: str | None, script: str | None) -> bool:
    if not cmd or not script:
        return False
    if not (os.path.isabs(cmd) and os.path.isabs(script)):
        return False
    return os.path.isfile(cmd) and os.path.isfile(script)


def _load_json_dict(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _upsert_standard_mcp_json(path: Path, venv_py: str, mcp_script: str, force: bool = False) -> bool:
    """Update `{"mcpServers": {"search_lancedb": {"command": ..., "args": [...]}}}`."""
    data = _load_json_dict(path)
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        servers = {}
        data["mcpServers"] = servers

    existing = servers.get(SERVER_NAME)
    if not force and isinstance(existing, dict):
        ex_cmd = existing.get("command")
        ex_args = existing.get("args") or []
        ex_script = ex_args[0] if isinstance(ex_args, list) and ex_args else None
        if _is_healthy_existing_entry(ex_cmd, ex_script):
            return False

    servers[SERVER_NAME] = {
        "command": venv_py,
        "args": [mcp_script],
    }
    _write_json_atomic(path, data)
    return True


def _upsert_opencode_json(path: Path, venv_py: str, mcp_script: str, force: bool = False) -> bool:
    """Update OpenCode `{"mcp": {"search_lancedb": {"type": "local", "command": [...], "enabled": true}}}`."""
    data = _load_json_dict(path)
    if "$schema" not in data:
        data["$schema"] = "https://opencode.ai/config.json"
    mcp_map = data.get("mcp")
    if not isinstance(mcp_map, dict):
        mcp_map = {}
        data["mcp"] = mcp_map

    existing = mcp_map.get(SERVER_NAME)
    if not force and isinstance(existing, dict):
        ex_cmd_list = existing.get("command") or []
        if isinstance(ex_cmd_list, list) and len(ex_cmd_list) >= 2:
            if _is_healthy_existing_entry(str(ex_cmd_list[0]), str(ex_cmd_list[1])):
                return False

    mcp_map[SERVER_NAME] = {
        "type": "local",
        "command": [venv_py, mcp_script],
        "enabled": True,
    }
    _write_json_atomic(path, data)
    return True


_TOML_SECTION_RE = re.compile(
    r"(?ms)^\[mcp_servers\.search_lancedb\]\s*\n.*?(?=^\[|\Z)"
)


def _extract_existing_toml_entry(text: str) -> tuple[str | None, str | None]:
    if tomllib is not None:
        try:
            parsed = tomllib.loads(text)
            entry = (parsed.get("mcp_servers") or {}).get(SERVER_NAME)
            if isinstance(entry, dict):
                cmd = entry.get("command")
                args = entry.get("args") or []
                script = args[0] if isinstance(args, list) and args else None
                return (str(cmd) if cmd else None, str(script) if script else None)
        except Exception:
            pass

    m = _TOML_SECTION_RE.search(text)
    if not m:
        return None, None
    block = m.group(0)
    cmd_m = re.search(r'^\s*command\s*=\s*(".*?")', block, re.M)
    args_m = re.search(r"^\s*args\s*=\s*(\[.*?\])", block, re.M)
    try:
        cmd = json.loads(cmd_m.group(1)) if cmd_m else None
        args_list = json.loads(args_m.group(1)) if args_m else []
        script = args_list[0] if args_list else None
        return cmd, script
    except Exception:
        return None, None


def _upsert_toml_mcp_section(
    path: Path,
    venv_py: str,
    mcp_script: str,
    *,
    include_enabled: bool = False,
    force: bool = False,
) -> bool:
    """Update `[mcp_servers.search_lancedb]` in Grok or Codex `config.toml`."""
    existing_text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if not force and existing_text:
        ex_cmd, ex_script = _extract_existing_toml_entry(existing_text)
        if _is_healthy_existing_entry(ex_cmd, ex_script):
            return False

    lines = [
        f"[mcp_servers.{SERVER_NAME}]",
        f"command = {json.dumps(venv_py)}",
        f"args = [{json.dumps(mcp_script)}]",
    ]
    if include_enabled:
        lines.append("enabled = true")
    new_block = "\n".join(lines) + "\n"

    if _TOML_SECTION_RE.search(existing_text):
        updated_text = _TOML_SECTION_RE.sub(new_block, existing_text, count=1)
    else:
        sep = "" if (not existing_text or existing_text.endswith("\n\n")) else ("\n" if existing_text.endswith("\n") else "\n\n")
        updated_text = existing_text + sep + new_block

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(updated_text, encoding="utf-8")
    os.replace(tmp, path)
    return True


def detect_harnesses(home: Path, detect_path_binaries: bool = True) -> list[str]:
    """Detect installed CLI/IDE harnesses without creating configs for absent tools."""
    found: list[str] = ["agy"]  # Canonical default config (~/.gemini/config/mcp_config.json)

    def _has_bin(name: str) -> bool:
        return bool(detect_path_binaries and shutil.which(name))

    if (home / ".grok").is_dir() or _has_bin("grok"):
        found.append("grok")
    if (home / ".codex").is_dir() or _has_bin("codex"):
        found.append("codex")
    if (home / ".config" / "opencode").is_dir() or (home / ".opencode").is_dir() or _has_bin("opencode"):
        found.append("opencode")
    if (home / ".cursor").is_dir():
        found.append("cursor")
    if (home / ".claude.json").is_file() or (home / ".claude").is_dir():
        found.append("claude")
    return found


def register_all_harnesses(
    project_root: str | None = None,
    home_dir: str | None = None,
    *,
    force: bool = False,
    harnesses: Iterable[str] | None = None,
    detect_path_binaries: bool = True,
) -> list[str]:
    """Register `search_lancedb` across `harnesses` (or auto-detected harnesses). Returns touched harness IDs."""
    home = Path(home_dir).expanduser() if home_dir else Path.home()
    venv_py, mcp_script = resolve_mcp_target(project_root)

    target_list = list(harnesses) if harnesses is not None else detect_harnesses(home, detect_path_binaries=detect_path_binaries)
    registered: list[str] = []

    for h in target_list:
        key = h.strip().lower()
        if key == "agy":
            cfg_path = home / ".gemini" / "config" / "mcp_config.json"
            _upsert_standard_mcp_json(cfg_path, venv_py, mcp_script, force=force)
            registered.append("agy")
        elif key == "grok":
            cfg_path = home / ".grok" / "config.toml"
            _upsert_toml_mcp_section(cfg_path, venv_py, mcp_script, include_enabled=True, force=force)
            registered.append("grok")
        elif key == "codex":
            cfg_path = home / ".codex" / "config.toml"
            _upsert_toml_mcp_section(cfg_path, venv_py, mcp_script, include_enabled=False, force=force)
            registered.append("codex")
        elif key == "opencode":
            cfg_path = home / ".config" / "opencode" / "opencode.json"
            _upsert_opencode_json(cfg_path, venv_py, mcp_script, force=force)
            registered.append("opencode")
        elif key == "cursor":
            cfg_path = home / ".cursor" / "mcp.json"
            _upsert_standard_mcp_json(cfg_path, venv_py, mcp_script, force=force)
            registered.append("cursor")
        elif key == "claude":
            cfg_path = home / ".claude.json"
            _upsert_standard_mcp_json(cfg_path, venv_py, mcp_script, force=force)
            registered.append("claude")

    return registered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register J.O.S.H.U.A. search_lancedb MCP server across harnesses.")
    parser.add_argument("--project-root", default=None, help="Target project root containing joshua_os/")
    parser.add_argument("--home", default=None, help="Override HOME directory (for testing)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing healthy MCP registrations")
    parser.add_argument(
        "--harnesses",
        default="auto",
        help="Comma-separated list (agy,grok,codex,opencode,cursor,claude) or 'auto' / 'all'",
    )
    args = parser.parse_args(argv)

    if args.harnesses == "auto":
        selected = None
    elif args.harnesses == "all":
        selected = ["agy", "grok", "codex", "opencode", "cursor", "claude"]
    else:
        selected = [x.strip() for x in args.harnesses.split(",") if x.strip()]

    touched = register_all_harnesses(
        project_root=args.project_root,
        home_dir=args.home,
        force=args.force,
        harnesses=selected,
    )
    print(f"    [*] Registered search_lancedb MCP server for harnesses: {', '.join(touched)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
