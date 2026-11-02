import copy
import json
import os
import sys
import tempfile
from pathlib import Path


def _merge_defaults(target, defaults):
    changed = False
    for key, value in defaults.items():
        if key not in target:
            target[key] = copy.deepcopy(value)
            changed = True
        elif isinstance(value, dict) and isinstance(target.get(key), dict):
            if _merge_defaults(target[key], value):
                changed = True
    return changed


def find_project_root(start_dir=None):
    """
    Dynamically discovers the J.O.S.H.U.A. project root directory across POSIX and Windows.
    Checks `start_dir` (default `os.getcwd()`) and its parents first to support isolated
    workspaces/worktrees, then falls back to the physical installation path.
    """
    start = Path(start_dir or os.getcwd()).resolve()
    for candidate in (start, *start.parents):
        if (candidate / "joshua_os" / ".aim_core").is_dir():
            return str(candidate)
    return str(Path(__file__).resolve().parent.parent.parent)


def find_os_root(start_dir=None):
    """
    Discover the `joshua_os` engine directory from `start_dir` (or physical module location).
    Supports both nested `<project>/joshua_os/.aim_core` and flat `<root>/.aim_core` layouts.
    """
    start = Path(start_dir or os.getcwd()).resolve()
    for candidate in (start, *start.parents):
        if (candidate / "joshua_os" / ".aim_core").is_dir():
            return str(candidate / "joshua_os")
        if (candidate / ".aim_core").is_dir() and (candidate / "setup.sh").is_file():
            return str(candidate)
    return str(Path(__file__).resolve().parent.parent)


PROJECT_ROOT = find_project_root()
OS_ROOT = os.path.join(PROJECT_ROOT, "joshua_os")
AIM_ROOT = OS_ROOT
CONFIG_PATH = os.path.join(OS_ROOT, ".aim_core", "CONFIG.json")


def get_agy_roots(home_dir=None):
    """Return ordered Antigravity root directories: AGY 2.0 (~/.gemini/antigravity) first, legacy CLI (~/.gemini/antigravity-cli) second."""
    home = os.path.expanduser(home_dir) if home_dir else os.path.expanduser("~")
    return [
        os.path.join(home, ".gemini", "antigravity"),
        os.path.join(home, ".gemini", "antigravity-cli"),
    ]


def get_primary_agy_root(home_dir=None):
    """Return the first existing Antigravity root directory, defaulting to ~/.gemini/antigravity."""
    roots = get_agy_roots(home_dir=home_dir)
    for r in roots:
        if os.path.isdir(r):
            return r
    return roots[0]


def get_agy_brain_dirs(home_dir=None, existing_only=False):
    """Return ordered Antigravity brain directories across AGY 2.0 and legacy CLI."""
    dirs = [os.path.join(r, "brain") for r in get_agy_roots(home_dir=home_dir)]
    if existing_only:
        return [d for d in dirs if os.path.isdir(d)]
    return dirs


def find_agy_transcript(session_id, home_dir=None):
    """Locate transcript.jsonl for session_id across AGY 2.0 and legacy CLI roots. Returns (found_path_or_None, probed_paths)."""
    probed = []
    for brain_dir in get_agy_brain_dirs(home_dir=home_dir):
        cand = os.path.join(brain_dir, session_id, ".system_generated", "logs", "transcript.jsonl")
        probed.append(cand)
        if os.path.isfile(cand):
            return cand, probed
    return None, probed


def get_agy_settings_paths(home_dir=None, existing_only=False):
    """Return ordered Antigravity settings.json paths across AGY 2.0 and legacy CLI."""
    paths = [os.path.join(r, "settings.json") for r in get_agy_roots(home_dir=home_dir)]
    if existing_only:
        return [p for p in paths if os.path.isfile(p)]
    return paths


def save_config_atomic(config, config_path=None):
    """Atomically write CONFIG.json via temporary file + os.replace to prevent concurrent truncation."""
    target = config_path or CONFIG_PATH
    parent = os.path.dirname(os.path.abspath(target))
    os.makedirs(parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=parent, prefix=".config_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(config, fh, indent=2)
            fh.write("\n")
        os.replace(tmp_path, target)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        raise


def build_default_config(project_root=None, os_root=None, home_dir=None):
    proj = project_root or PROJECT_ROOT
    os_dir = os_root or OS_ROOT
    home = os.path.expanduser(home_dir) if home_dir else os.path.expanduser("~")
    primary_agy_brain = os.path.join(get_primary_agy_root(home_dir=home), "brain")
    return {
        "paths": {
            "project_root": proj,
            "os_root": os_dir,
            "aim_root": os_dir,
            "core_dir": os.path.join(os_dir, "core"),
            "docs_dir": os.path.join(os_dir, "docs"),
            "hooks_dir": os.path.join(os_dir, "hooks"),
            "archive_dir": os.path.join(os_dir, "archive"),
            "archive_raw_dir": os.path.join(os_dir, "archive", "raw"),
            "memory_dir": os.path.join(os_dir, "memory_lance"),
            "continuity_dir": os.path.join(os_dir, "continuity"),
            "src_dir": os.path.join(os_dir, ".aim_core"),
            "wiki_dir": os.path.join(proj, "memory-wiki"),
            "tmp_chats_dir": primary_agy_brain,
        },
        "models": {
            "embedding_provider": "local",
            "embedding": "nomic-embed-text",
            "embedding_endpoint": "http://127.0.0.1:11434/api/embeddings",
            "default_reasoning": {
                "provider": "google",
                "model": "agy-flash-latest",
                "endpoint": "https://generativelanguage.googleapis.com",
                "auth_type": "API Key",
            },
        },
        "settings": {
            "allowed_root": home,
            "semantic_pruning_threshold": 0.85,
            "scrivener_interval_minutes": 30,
            "archive_retention_days": 30,
            "sentinel_mode": "full",
            "obsidian_vault_path": "",
            "auto_distill_tier": "T4",
            "auto_rebirth": False,
            "github_projects": {
                "owner": "",
                "number": 0,
                "status_field": "Status",
            },
        },
    }


def _remap_paths(paths_dict, project_root, os_root, primary_agy_brain):
    paths_dict["project_root"] = project_root
    paths_dict["os_root"] = os_root
    paths_dict["aim_root"] = os_root
    paths_dict["core_dir"] = os.path.join(os_root, "core")
    paths_dict["docs_dir"] = os.path.join(os_root, "docs")
    paths_dict["hooks_dir"] = os.path.join(os_root, "hooks")
    paths_dict["archive_dir"] = os.path.join(os_root, "archive")
    paths_dict["archive_raw_dir"] = os.path.join(os_root, "archive", "raw")
    paths_dict["memory_dir"] = os.path.join(os_root, "memory_lance")
    paths_dict["continuity_dir"] = os.path.join(os_root, "continuity")
    paths_dict["src_dir"] = os.path.join(os_root, ".aim_core")
    paths_dict["wiki_dir"] = os.path.join(project_root, "memory-wiki")
    paths_dict["tmp_chats_dir"] = primary_agy_brain


def load_config(config_path=None):
    """Loads, validates, and repairs CONFIG.json paths only when the workspace actually moves."""
    home = os.path.expanduser("~")
    primary_agy_brain = os.path.join(get_primary_agy_root(home_dir=home), "brain")
    default_config = build_default_config(PROJECT_ROOT, OS_ROOT, home_dir=home)
    cfg_file = config_path or CONFIG_PATH

    if not os.path.exists(cfg_file):
        return default_config

    try:
        with open(cfg_file, "r", encoding="utf-8") as f:
            disk_config = json.load(f)
        if not isinstance(disk_config, dict):
            return default_config

        saved_paths = disk_config.get("paths")
        norm_os = os.path.normcase(os.path.abspath(OS_ROOT))
        norm_proj = os.path.normcase(os.path.abspath(PROJECT_ROOT))
        disk_dirty = False

        if isinstance(saved_paths, dict):
            saved_os = saved_paths.get("os_root")
            saved_aim = saved_paths.get("aim_root")
            norm_saved_os = os.path.normcase(os.path.abspath(saved_os)) if saved_os else None
            norm_saved_aim = os.path.normcase(os.path.abspath(saved_aim)) if saved_aim else None

            relocated = False
            if norm_saved_os and norm_saved_os != norm_os:
                relocated = True
            elif not norm_saved_os and norm_saved_aim and norm_saved_aim not in (norm_os, norm_proj):
                relocated = True

            if relocated:
                sys.stderr.write("[PORTABILITY] System shift detected. Re-mapping paths for this machine...\n")
                _remap_paths(saved_paths, PROJECT_ROOT, OS_ROOT, primary_agy_brain)
                settings_block = disk_config.setdefault("settings", {})
                old_vault = settings_block.get("obsidian_vault_path", "")
                if isinstance(old_vault, str) and old_vault.startswith("/home/"):
                    parts = old_vault.split("/")
                    if len(parts) > 3:
                        settings_block["obsidian_vault_path"] = os.path.join(home, *parts[3:])
                disk_dirty = True
            elif (
                norm_saved_aim == norm_proj
                or saved_paths.get("archive_raw_dir") == os.path.join(OS_ROOT, "archive_raw")
            ):
                # One-time silent repair for legacy v1.1.1 split-root entries on the same host
                _remap_paths(saved_paths, PROJECT_ROOT, OS_ROOT, primary_agy_brain)
                disk_dirty = True

        if disk_dirty:
            save_config_atomic(disk_config, config_path=cfg_file)

        merged = copy.deepcopy(disk_config)
        _merge_defaults(merged, default_config)
        return merged
    except Exception:
        return default_config


CONFIG = load_config()


def resolve_venv_python(os_root=None):
    """Cross-platform venv Python resolver (supports Linux/macOS venv/bin and Windows venv/Scripts + worktree fallbacks)."""
    root = os_root or OS_ROOT
    candidates = (
        (
            os.path.join("venv", "Scripts", "python.exe"),
            os.path.join("..", "..", "venv", "Scripts", "python.exe"),
            os.path.join("..", "..", "..", "joshua_os", "venv", "Scripts", "python.exe"),
            os.path.join("venv", "bin", "python3"),
            os.path.join("..", "..", "venv", "bin", "python3"),
            os.path.join("..", "..", "..", "joshua_os", "venv", "bin", "python3"),
        )
        if os.name == "nt"
        else (
            os.path.join("venv", "bin", "python3"),
            os.path.join("..", "..", "venv", "bin", "python3"),
            os.path.join("..", "..", "..", "joshua_os", "venv", "bin", "python3"),
            os.path.join("venv", "Scripts", "python.exe"),
            os.path.join("..", "..", "venv", "Scripts", "python.exe"),
            os.path.join("..", "..", "..", "joshua_os", "venv", "Scripts", "python.exe"),
        )
    )
    for rel in candidates:
        cand = os.path.abspath(os.path.join(root, rel))
        if os.path.exists(cand):
            return cand
    return sys.executable
