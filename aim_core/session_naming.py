"""Vessel-scoped tmux session names for spawned agents."""
from __future__ import annotations

import os
import re
import time


def vessel_cli_id(env: dict | None = None) -> str:
    """Return sanitized vessel id used as the session prefix.

    aim-opencode default is ``opencode``. Override with ``AIM_VESSEL_CLI`` (e.g. agy, grok).
    """
    source = env if env is not None else os.environ
    raw = (source.get("AIM_VESSEL_CLI") or "opencode").strip().lower()
    cleaned = "".join(c if c.isalnum() or c in "-_" else "_" for c in raw)
    return cleaned or "opencode"


def get_project_slug(workspace_dir: str | None = None) -> str:
    """Derive a safe project slug from the given directory (default CWD)."""
    if not workspace_dir:
        workspace_dir = os.getcwd()
    basename = os.path.basename(os.path.abspath(workspace_dir))
    cleaned = "".join(c if c.isalnum() or c in "-_" else "_" for c in basename)
    return cleaned or "unknown_project"


def build_agent_session_name(
    role: str,
    workspace_dir: str | None = None,
    env: dict | None = None,
    *,
    timestamp: int | None = None,
) -> str:
    """Build ``{vessel}_{role}_{project_slug}_{unix_ts}`` for a new tmux session."""
    vessel = vessel_cli_id(env)
    slug = get_project_slug(workspace_dir)
    ts = int(time.time()) if timestamp is None else int(timestamp)
    # Sanitize role just in case
    clean_role = "".join(c if c.isalnum() or c in "-_" else "_" for c in role)
    return f"{vessel}_{clean_role}_{slug}_{ts}"


def is_agent_session_role(name: str, role: str, env: dict | None = None) -> bool:
    """True if *name* matches this vessel's pattern for a specific role."""
    vessel = vessel_cli_id(env)
    clean_role = "".join(c if c.isalnum() or c in "-_" else "_" for c in role)
    prefix = f"{vessel}_{clean_role}_"
    if not name.startswith(prefix):
        return False
    # Format is {vessel}_{role}_{slug}_{ts}. We check if it ends with _[0-9]+
    parts = name.split('_')
    return bool(re.fullmatch(r"[0-9]+", parts[-1]))


def reincarnation_session_name(
    workspace_dir: str | None = None,
    env: dict | None = None,
    *,
    timestamp: int | None = None,
) -> str:
    """Build session name for reincarnation (legacy compat wrap)."""
    return build_agent_session_name("reincarnate", workspace_dir, env, timestamp=timestamp)


def is_reincarnation_session(name: str, env: dict | None = None) -> bool:
    """True if *name* matches this vessel's reincarnation session pattern."""
    return is_agent_session_role(name, "reincarnate", env)
