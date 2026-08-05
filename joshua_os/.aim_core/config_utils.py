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

def find_project_root():
    """
    Dynamically discovers the A.I.M. project root directory.
    First checks the current working directory to support isolated workspaces.
    Falls back to the physical installation directory.
    """
    # 1. Check current directory and parents (Dynamic Workspace Isolation)
    current = os.path.abspath(os.getcwd())
    while current != '/':
        if os.path.exists(os.path.join(current, "joshua_os", ".aim_core")):
            return current
        current = os.path.dirname(current)
        
    # 2. Fallback to physical installation path (Global Execution)
    # Note: If this file is at joshua_os/.aim_core/config_utils.py, 
    # dirname(dirname(abspath)) points to joshua_os. 
    # So we go up one more directory to get the project root.
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = find_project_root()
OS_ROOT = os.path.join(PROJECT_ROOT, "joshua_os")
AIM_ROOT = OS_ROOT  # Default for most scripts
CONFIG_PATH = os.path.join(OS_ROOT, ".aim_core/CONFIG.json")

def load_config():
    """Loads, validates, and auto-repairs paths for the current machine."""
    home = os.path.expanduser("~")
    
    # Baseline defaults for a fresh system
    default_config = {
        "paths": {
            "aim_root": AIM_ROOT,
            "os_root": OS_ROOT,
            "core_dir": os.path.join(OS_ROOT, "core"),
            "docs_dir": os.path.join(OS_ROOT, "docs"),
            "hooks_dir": os.path.join(OS_ROOT, "hooks"),
            "archive_raw_dir": os.path.join(OS_ROOT, "archive/raw"),
            "continuity_dir": os.path.join(OS_ROOT, "continuity"),
            "src_dir": os.path.join(OS_ROOT, ".aim_core"),
            "tmp_chats_dir": os.path.expanduser("~/.gemini/antigravity-cli/brain")
        },
        "models": {
            "embedding_provider": "local",
            "embedding": "nomic-embed-text",
            "embedding_endpoint": "http://127.0.0.1:11434/api/embeddings",
            "default_reasoning": {
                "provider": "google",
                "model": "agy-flash-latest",
                "endpoint": "https://generativelanguage.googleapis.com",
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
            
            config['paths']['aim_root'] = PROJECT_ROOT
            config['paths']['os_root'] = OS_ROOT
            for key in ['core_dir', 'docs_dir', 'hooks_dir', 'memory_dir', 'archive_raw_dir', 'archive_index_dir', 'continuity_dir', 'src_dir']:
                if key == 'src_dir':
                    config['paths'][key] = os.path.join(OS_ROOT, ".aim_core")
                else:
                    config['paths'][key] = os.path.join(OS_ROOT, key.replace('_dir', ''))
            
            # Recalculate home-based paths
            config['paths']['tmp_chats_dir'] = os.path.expanduser("~/.gemini/antigravity-cli/brain")
            
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
