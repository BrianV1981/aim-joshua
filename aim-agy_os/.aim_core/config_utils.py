import os
import json
import sys
import getpass

def _merge_defaults(target, defaults):
    changed = False
    for key, value in defaults.items():
        if key not in target:
            target[key] = value
            changed = True
        elif isinstance(value, dict) and isinstance(target.get(key), dict):
            if _merge_defaults(target[key], value):
                changed = True
    return changed

def find_aim_root():
    """
    Dynamically discovers the A.I.M. *vessel* project root (host repo hosting the OS).
    Prefers nested aim-agy_os/.aim_core (lockstep with soul #99); falls back to legacy
    core/CONFIG.json and setup.sh markers without treating aim-agy_os itself as root.
    """
    current = os.path.abspath(os.getcwd())
    while current != '/':
        if os.path.isdir(os.path.join(current, "aim-agy_os", ".aim_core")):
            return current
        if os.path.isfile(os.path.join(current, "core", "CONFIG.json")):
            return current
        if os.path.isfile(os.path.join(current, "setup.sh")) and os.path.basename(current) not in (
            "aim-agy_os", "aim_os", "aim-opencode_os"
        ):
            return current
        current = os.path.dirname(current)

    here = os.path.abspath(__file__)
    if os.path.basename(os.path.dirname(os.path.dirname(here))) in ("aim-agy_os", "aim_os"):
        return os.path.dirname(os.path.dirname(os.path.dirname(here)))
    return os.path.dirname(os.path.dirname(here))

AIM_ROOT = find_aim_root()
_nested_cfg = os.path.join(AIM_ROOT, "aim-agy_os", ".aim_core", "CONFIG.json")
_legacy_cfg = os.path.join(AIM_ROOT, "core", "CONFIG.json")
if os.path.isfile(_nested_cfg) or os.path.isdir(os.path.join(AIM_ROOT, "aim-agy_os", ".aim_core")):
    CONFIG_PATH = _nested_cfg
else:
    CONFIG_PATH = _legacy_cfg

def load_config():
    """Loads, validates, and auto-repairs paths for the current machine."""
    home = os.path.expanduser("~")
    
    # Baseline defaults for a fresh system
    default_config = {
        "paths": {
            "aim_root": AIM_ROOT,
            "core_dir": os.path.join(AIM_ROOT, "core"),
            "docs_dir": os.path.join(AIM_ROOT, "docs"),
            "hooks_dir": os.path.join(AIM_ROOT, "hooks"),
            "archive_raw_dir": os.path.join(AIM_ROOT, "archive/raw"),
            "opencode_export_dir": os.path.join(AIM_ROOT, "archive/raw"),
            "continuity_dir": os.path.join(AIM_ROOT, "continuity"),
            "src_dir": os.path.join(AIM_ROOT, ".aim_core") if os.path.isdir(os.path.join(AIM_ROOT, ".aim_core")) else os.path.join(AIM_ROOT, "aim_core"),
            "tmp_chats_dir": os.path.join(home, f".gemini/tmp/{os.path.basename(AIM_ROOT)}/chats")
        },
        "models": {
            "embedding_provider": "local",
            "embedding": "nomic-embed-text",
            "embedding_endpoint": "http://127.0.0.1:11434/api/embeddings",
            "default_reasoning": {
                "provider": "openai-compat",
                "model": "deepseek-chat",
                "endpoint": "https://api.deepseek.com/v1/chat/completions",
                "auth_type": "API Key"
            }
        },
        "settings": {
            "allowed_root": home,
            "semantic_pruning_threshold": 0.85,
            "scrivener_interval_minutes": 30,
            "archive_retention_days": 30,
            "sentinel_mode": "full",
            "obsidian_vault_path": "",
            "auto_distill_tier": "T4",
            "auto_rebirth": False
        }
    }

    if not os.path.exists(CONFIG_PATH):
        return default_config

    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        changed = False
        
        # --- THE PORTABILITY SHIELD ---
        # If the root in the file doesn't match the current directory, 
        # we RE-CALCULATE everything based on the current system.
        if config.get('paths', {}).get('aim_root') != AIM_ROOT:
            sys.stderr.write(f"[PORTABILITY] System shift detected. Re-mapping paths for this machine...\n")
            
            config['paths']['aim_root'] = AIM_ROOT
            for key in ['core_dir', 'docs_dir', 'hooks_dir', 'memory_dir', 'archive_raw_dir', 'archive_index_dir', 'continuity_dir', 'src_dir']:
                config['paths'][key] = os.path.join(AIM_ROOT, key.replace('_dir', ''))
            
            # opencode_export_dir mirrors archive_raw_dir for the session bridge
            config['paths']['opencode_export_dir'] = os.path.join(AIM_ROOT, "archive/raw")

            # Recalculate home-based paths
            config['paths']['tmp_chats_dir'] = os.path.join(home, f".gemini/tmp/{os.path.basename(AIM_ROOT)}/chats")
            
            # If we have an Obsidian path, we only update it if it started with /home/
            old_vault = config['settings'].get('obsidian_vault_path', "")
            if old_vault.startswith("/home/"):
                # Extract the old user part and replace it with current
                parts = old_vault.split('/')
                if len(parts) > 2:
                    new_vault = os.path.join(home, *parts[3:])
                    config['settings']['obsidian_vault_path'] = new_vault

            changed = True

        if _merge_defaults(config, default_config):
            changed = True

        if changed:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(config, f, indent=2)
                
        return config
    except Exception:
        return default_config

CONFIG = load_config()


_SENTINEL = object()


def resolve_session_sources(aim_root=None, opencode_export_dir=_SENTINEL):
    """
    Returns a prioritized list of session source paths for signal extraction.

    Each entry is a 3-tuple: (source_type, directory_path, file_pattern)

    Priority:
      1. OpenCode export directory (archive/raw/ or configured opencode_export_dir) — *.json
      2. Gemini CLI native tmp dir (~/.gemini/tmp/<project>/chats/) — *.jsonl (backward compat)

    Used by: handoff_pulse_generator, daemon ghost auditor, log recovery, and session bridge.
    """
    home = os.path.expanduser("~")

    if aim_root is None:
        aim_root = AIM_ROOT

    if opencode_export_dir is _SENTINEL:
        opencode_export_dir = CONFIG.get('paths', {}).get(
            'opencode_export_dir',
            CONFIG.get('paths', {}).get('archive_raw_dir', '')
        )

    project_name = os.path.basename(aim_root)

    sources = []

    # Primary: OpenCode export directory
    if opencode_export_dir:
        sources.append(('opencode', opencode_export_dir, '*.json'))

    # Fallback: Gemini CLI native temp directory
    gemini_dir = os.path.join(home, f'.gemini/tmp/{project_name}/chats')
    sources.append(('gemini', gemini_dir, '*.jsonl'))

    return sources
