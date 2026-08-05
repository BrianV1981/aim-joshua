#!/usr/bin/env python3
"""
Antigravity CLI workspace trust helper.

HARD TRUTH (verified 2026-07-15):
  - `agy --dangerously-skip-permissions` skips *tool* permission prompts, NOT the
    "Do you trust the contents of this project" folder gate.
  - Trust is stored in ~/.gemini/antigravity-cli/settings.json → trustedWorkspaces[]
  - Matching is EXACT path (parent entry does NOT trust children).
  - UI is a list with "> Yes, I trust this folder" — send Enter only, not "y".

Every spawn of agy in a new cwd MUST call ensure_workspace_trusted(cwd) first.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Iterable, List, Optional

SETTINGS_PATH = Path.home() / ".gemini" / "antigravity-cli" / "settings.json"
LEGACY_TRUSTED = Path.home() / ".gemini" / "trustedFolders.json"

TRUST_PROMPT_MARKERS = (
    "trust the contents",
    "trust this folder",
    "yes, i trust this folder",
    "do you trust",
)


def _normalize(path: str) -> str:
    return str(Path(path).expanduser().resolve())


def _load_settings() -> dict:
    if not SETTINGS_PATH.is_file():
        return {"trustedWorkspaces": []}
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8") or "{}")
        if not isinstance(data, dict):
            return {"trustedWorkspaces": []}
        return data
    except Exception:
        return {"trustedWorkspaces": []}


def _save_settings(data: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    # atomic write
    tmp = SETTINGS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, SETTINGS_PATH)


def list_trusted_workspaces() -> List[str]:
    data = _load_settings()
    tw = data.get("trustedWorkspaces") or []
    return [str(x) for x in tw if x]


def is_workspace_trusted(path: str) -> bool:
    target = _normalize(path)
    trusted = {_normalize(p) for p in list_trusted_workspaces()}
    if target in trusted:
        return True
    # Also accept trailing-dot / trailing-slash variants already present
    for t in list(trusted):
        if t.rstrip("/.") == target.rstrip("/."):
            return True
    return False


def ensure_workspace_trusted(
    path: str,
    *,
    also_parents: bool = False,
    quiet: bool = False,
) -> bool:
    """
    Ensure exact path is in antigravity-cli trustedWorkspaces.
    Returns True if already trusted or successfully added.
    """
    try:
        target = _normalize(path)
        if not os.path.isdir(target):
            # still register intended cwd (will be created by caller)
            os.makedirs(target, exist_ok=True)
            target = _normalize(path)

        data = _load_settings()
        tw = list(data.get("trustedWorkspaces") or [])
        # normalize existing for membership
        tw_norm = {_normalize(p) if os.path.exists(p) else str(Path(p).resolve()) for p in tw}
        # simpler: string set as stored
        tw_set = set(str(p) for p in tw)

        to_add = [target]
        if also_parents:
            p = Path(target)
            home = Path.home().resolve()
            while p != p.parent:
                if p == home or p == Path("/"):
                    break
                to_add.append(str(p))
                p = p.parent

        changed = False
        for p in to_add:
            # store resolved absolute form without trailing slash
            p = str(Path(p).resolve())
            if p not in tw_set:
                tw.append(p)
                tw_set.add(p)
                changed = True

        if changed:
            data["trustedWorkspaces"] = tw
            _save_settings(data)
            if not quiet:
                print(f"[TRUST] registered workspace(s) in {SETTINGS_PATH}: {to_add}")
        else:
            if not quiet:
                print(f"[TRUST] already trusted: {target}")

        # Keep legacy trustedFolders.json in sync (parent TRUST_FOLDER for home subtree)
        try:
            _sync_legacy_trusted_folders(target)
        except Exception:
            pass

        return True
    except Exception as e:
        if not quiet:
            print(f"[TRUST] WARN failed to update trustedWorkspaces: {e}")
        return False


def _sync_legacy_trusted_folders(path: str) -> None:
    """Best-effort: ensure ~/.gemini/trustedFolders.json notes the path."""
    if not LEGACY_TRUSTED.parent.is_dir():
        return
    data = {}
    if LEGACY_TRUSTED.is_file():
        try:
            data = json.loads(LEGACY_TRUSTED.read_text(encoding="utf-8") or "{}")
        except Exception:
            data = {}
    if not isinstance(data, dict):
        data = {}
    # TRUST_FOLDER on exact path; keep existing /home/kingb entry
    data[str(Path(path).resolve())] = "TRUST_FOLDER"
    LEGACY_TRUSTED.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def pane_shows_trust_prompt(text: str) -> bool:
    low = (text or "").lower()
    return any(m in low for m in TRUST_PROMPT_MARKERS)


def dismiss_trust_prompt_tmux(session_name: str, *, max_rounds: int = 20) -> bool:
    """
    If tmux pane shows trust UI, send Enter (Yes is pre-selected with '>').
    Do NOT send 'y' — this is a list, not a y/n prompt.
    Returns True if prompt was seen and dismissed (or gone).
    """
    dismissed = False
    for _ in range(max_rounds):
        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-p", "-J", "-t", session_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            out = result.stdout or ""
        except Exception:
            time.sleep(0.3)
            continue

        if pane_shows_trust_prompt(out):
            # Ensure selection on first item: Home/Up then Enter
            subprocess.run(
                ["tmux", "send-keys", "-t", session_name, "Escape"],
                capture_output=True,
            )
            time.sleep(0.1)
            # Up a few times to be on first option
            for _u in range(3):
                subprocess.run(
                    ["tmux", "send-keys", "-t", session_name, "Up"],
                    capture_output=True,
                )
            time.sleep(0.1)
            subprocess.run(
                ["tmux", "send-keys", "-t", session_name, "Enter"],
                capture_output=True,
            )
            dismissed = True
            time.sleep(0.5)
            continue

        if dismissed:
            return True
        # never saw prompt
        if "Antigravity" in out or "❯" in out or "Enter your" in out:
            return True
        time.sleep(0.3)
    return dismissed


def prepare_agy_spawn(cwd: str, *, quiet: bool = False) -> str:
    """
    Call before every `tmux … agy` spawn. Returns normalized cwd.
    """
    cwd = _normalize(cwd)
    ensure_workspace_trusted(cwd, also_parents=False, quiet=quiet)
    return cwd


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: agy_workspace_trust.py <path> [path2...]")
        print("       agy_workspace_trust.py --check <path>")
        sys.exit(2)
    if sys.argv[1] == "--check":
        p = sys.argv[2]
        print("trusted" if is_workspace_trusted(p) else "NOT trusted", p)
        sys.exit(0 if is_workspace_trusted(p) else 1)
    for p in sys.argv[1:]:
        ensure_workspace_trusted(p)
        print("ok", _normalize(p), "trusted=", is_workspace_trusted(p))
