#!/usr/bin/env python3
import os
import json
import subprocess
import shutil
import sys
import re
from datetime import datetime

# --- CONFIG BOOTSTRAP ---
def find_project_root(start_dir):
    current = os.path.abspath(start_dir)
    while current != '/':
        if os.path.exists(os.path.join(current, "joshua_os", ".aim_core")) or os.path.exists(os.path.join(current, "setup.sh")): return current
        current = os.path.dirname(current)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = find_project_root(os.getcwd())
OS_DIR = os.path.join(BASE_DIR, "joshua_os")
CORE_DIR = os.path.join(OS_DIR, "core")
DOCS_DIR = os.path.join(OS_DIR, "docs")
ARCHIVE_DIR = os.path.join(OS_DIR, "archive")
HOOKS_DIR = os.path.join(OS_DIR, "hooks")
AIM_CORE_DIR = os.path.join(OS_DIR, ".aim_core")
VENV_PYTHON = os.path.join(OS_DIR, "venv/bin/python3")

# --- INTERNAL TEMPLATES ---



def _load_wiki_agents_template() -> str:
    """Single source of truth: templates/memory_wiki_AGENTS.md (lockstep B)."""
    tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "memory_wiki_AGENTS.md")
    if os.path.isfile(tpl):
        with open(tpl, "r", encoding="utf-8") as f:
            return f.read()
    # Fallback if template missing from package
    return (
        "<!-- Schema-Version: 1-interim -->\n"
        "# 🧠 SUB-AGENT DIRECTIVE: WIKI MAINTAINER\n\n"
        "Process `_ingest/` into the wiki. Read this schema and index.md first.\n"
    )


T_WIKI_AGENT = _load_wiki_agents_template()





def get_default_config(aim_root, gemini_tmp, allowed_root, obsidian_path):
    return {
      "paths": {
        "aim_root": aim_root,
        "core_dir": f"{aim_root}/core",
        "docs_dir": f"{aim_root}/docs",
        "hooks_dir": f"{aim_root}/hooks",
        "archive_raw_dir": f"{aim_root}/archive/raw",
        "continuity_dir": f"{aim_root}/continuity",
        "src_dir": f"{aim_root}/src",
        "tmp_chats_dir": gemini_tmp
      },
      "models": {
        "embedding_provider": "local",
        "embedding": "nomic-embed-text",
        "embedding_endpoint": "http://127.0.0.1:11434/api/embeddings",
        "default_reasoning": {
          "provider": "google",
          "model": "agy-3.1-pro-preview",
          "endpoint": "https://generativelanguage.googleapis.com",
          "auth_type": "OAuth"
        }
      },
      "settings": {
        "allowed_root": allowed_root,
        "semantic_pruning_threshold": 0.85,
        "scrivener_interval_minutes": 60,
        "archive_retention_days": 0,
        "sentinel_mode": "full",
        "obsidian_vault_path": obsidian_path,
        "auto_distill_tier": "T5",
        "auto_rebirth": False
      }
    }


def _extract_md_field(content, label, default=""):
    match = re.search(rf"- \*\*{re.escape(label)}:\*\* (.*)", content)
    return match.group(1).strip() if match else default

def _extract_section(content, heading, next_heading=None, default=""):
    if next_heading:
        pattern = rf"## {re.escape(heading)}\n(.*?)\n## {re.escape(next_heading)}"
    else:
        pattern = rf"## {re.escape(heading)}\n(.*)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else default

def load_existing_identity_defaults():
    defaults = {}

    gemini_path = os.path.join(BASE_DIR, "AGENTS.md")
    if os.path.exists(gemini_path):
        with open(gemini_path, "r", encoding="utf-8") as f:
            agy = f.read()
        defaults["name"] = _extract_md_field(agy, "Operator", defaults.get("name", ""))
        defaults["exec_mode"] = _extract_md_field(agy, "Execution Mode", defaults.get("exec_mode", ""))
        defaults["cog_level"] = _extract_md_field(agy, "Cognitive Level", defaults.get("cog_level", ""))
        defaults["concise_mode"] = _extract_md_field(agy, "Conciseness", defaults.get("concise_mode", ""))
        if "## ⚠️ EXPLICIT GUARDRAILS" in agy:
            defaults["guardrails_block"] = T_EXPLICIT_GUARDRAILS

    operator_path = os.path.join(CORE_DIR, "OPERATOR.md")
    if os.path.exists(operator_path):
        with open(operator_path, "r", encoding="utf-8") as f:
            operator = f.read()
        defaults["name"] = _extract_md_field(operator, "Name", defaults.get("name", ""))
        defaults["stack"] = _extract_md_field(operator, "Tech Stack", defaults.get("stack", ""))
        defaults["style"] = _extract_md_field(operator, "Style", defaults.get("style", ""))
        defaults["physical"] = _extract_md_field(operator, "Age/Height/Weight", defaults.get("physical", ""))
        defaults["rules"] = _extract_md_field(operator, "Life Rules", defaults.get("rules", ""))
        defaults["goals"] = _extract_md_field(operator, "Primary Goal", defaults.get("goals", ""))
        business = _extract_section(operator, "🏢 Business Intelligence", "🤖 Grok/Social Archetype", "")
        if business:
            defaults["business"] = business

    operator_profile_path = os.path.join(CORE_DIR, "OPERATOR_PROFILE.md")
    if os.path.exists(operator_profile_path):
        with open(operator_profile_path, "r", encoding="utf-8") as f:
            defaults["grok_profile"] = f.read().strip() or defaults.get("grok_profile", "")

    config_path = os.path.join(CORE_DIR, "CONFIG.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            defaults["obsidian_path"] = config.get("settings", {}).get("obsidian_vault_path", defaults.get("obsidian_path", ""))
            defaults["allowed_root"] = config.get("settings", {}).get("allowed_root", defaults.get("allowed_root", ""))
        except Exception:
            pass

    return defaults
def register_hooks(is_light_mode=False):
    settings_path = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")
    router_src = os.path.join(OS_DIR, ".aim_core/aim_router.py")
    router_dest = os.path.expanduser("~/.gemini/antigravity-cli/aim_router.py")

    if os.path.exists(router_src):
        import shutil
        shutil.copy2(router_src, router_dest)
        os.chmod(router_dest, 0o755)

    if not os.path.exists(settings_path): return
    try:
        with open(settings_path, 'r') as f: settings = json.load(f)
        if "hooks" not in settings: settings["hooks"] = {}

        # Enforce global Memory Boundary Marker for A.I.M. Isolation
        if "context" not in settings: settings["context"] = {}
        settings["context"]["memoryBoundaryMarkers"] = ["AGENTS.md", ".git"]
        settings["context"]["discoveryMaxDirs"] = 0
        settings["context"]["fileName"] = ["AGENTS.md"]


        # [REMOVED] SessionEnd hook for session_summarizer.py
        # The Scribe/Wiki Ingester should ONLY run on /reincarnate, not every single CLI exit.
        # It is explicitly called by .aim_core/handoff_pulse_generator.py during handoff.

        aim_hooks = {
            "AfterTool": [
                ("cognitive-mantra", "cognitive_mantra.py")
            ]
        }
        
        # Clear old A.I.M. hooks to prevent ghost executions (e.g. legacy SessionStart)
        settings["hooks"] = {}

        # Actually write the hooks to the settings dictionary
        for event, hooks in aim_hooks.items():
            settings["hooks"][event] = []
            for h in hooks:
                entry = { "name": h[0], "type": "command", "command": f"python3 {router_dest} {h[1]}" }
                if len(h) > 2: entry["matcher"] = h[2]
                settings["hooks"][event].append({"hooks": [entry]})
                
        # Save to disk
        with open(settings_path, 'w') as f: json.dump(settings, f, indent=2)
        
        print("[OK] Hooks registered via Universal Router.")
    except Exception as e:
        print(f"[ERROR] Hook registration failed: {e}")
        sys.exit(1)

def trigger_bootstrap():
    print("\n--- PROJECT SINGULARITY: BOOTSTRAPPING BRAIN ---")
    bootstrap_path = os.path.join(AIM_CORE_DIR, "bootstrap_brain.py")
    try:
        subprocess.run([VENV_PYTHON, bootstrap_path], check=True)
    except: print("[CRITICAL] Foundation Bootstrap failed.")

def init_workspace(args=None):
    if args is None: args = []
    is_interactive = "--headless" not in args
    persona_name = None
    if "--persona" in args:
        try:
            persona_name = args[args.index("--persona") + 1]
        except ValueError:
            pass

    print("""
--- A.I.M. SOVEREIGN INSTALLER ---""")
    
    # 1. Mechanical Provisioning (Folders & Settings)
    dirs = ["archive/raw", "archive/history", "archive/sync", "archive/cartridges",
            "continuity/private", "continuity", "workstreams", "hooks", "scripts", "projects", "foundry", ".aim_core", "memory-wiki", "memory-wiki/_ingest", "planning-artifacts", "workspace"]
    for d in dirs: os.makedirs(os.path.join(OS_DIR, d), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, ".gemini"), exist_ok=True)

    is_light_mode = "--light" in args
    register_hooks(is_light_mode)

    # Base settings and ignores
    files = {
        "README.md": "",
        "CHANGELOG.md": "",
        "VERSION": "",
        "CONTRIBUTING.md": "",
        ".geminiignore": """workspace/
archive/
memory_lance/
memory-wiki/
foundry/
planning-artifacts/
engrams/
""",
        ".gemini/settings.json": """{
  "context": {
    "memoryBoundaryMarkers": ["AGENTS.md", ".git"],
    "discoveryMaxDirs": 0,
    "fileName": ["AGENTS.md"]
  }
}
""",
        f"joshua_os/memory-wiki/.gemini/settings.json": """{
  "context": {
    "memoryBoundaryMarkers": ["AGENT.md"],
    "discoveryMaxDirs": 0,
    "fileName": ["AGENT.md"],
    "ignoreGlobal": true
  }
}
""",
        f"joshua_os/memory-wiki/AGENTS.md": T_WIKI_AGENT,
        "joshua_os/.aim_core/CONFIG.json": json.dumps({
            "agent_identity": {
                "name": "A.I.M.",
                "role": "High-context technical lead and sovereign orchestrator.",
                "version": "1.0.0"
            },
            "paths": {
                "continuity_dir": os.path.join(OS_DIR, "continuity"),
                "archive_dir": os.path.join(OS_DIR, "archive"),
                "memory_dir": os.path.join(OS_DIR, "memory_lance"),
                "wiki_dir": os.path.join(OS_DIR, "memory-wiki")
            },
            "settings": {
                "obsidian_vault_path": os.path.join(OS_DIR, "memory-wiki"),
                "allowed_root": BASE_DIR
            }
        }, indent=2) + "\n"
    }
    
    for fp, content in files.items():
        full_path = os.path.join(BASE_DIR, fp)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if not os.path.exists(full_path):
            with open(full_path, "w") as f: f.write(content)

    # 1.5. Make A.I.M. OS Invisible (Append to .gitignore)
    gitignore_path = os.path.join(BASE_DIR, ".gitignore")
    ignore_entries = "\n# --- A.I.M. OS Exoskeleton ---\n.gemini/\nAGENTS.md\njoshua_os/\n.grok/\n.opencode/\nmemory-wiki/\nworkspace/\n"
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            existing_ignore = f.read()
        if "--- A.I.M. OS Exoskeleton ---" not in existing_ignore:
            with open(gitignore_path, "a") as f:
                f.write(ignore_entries)
    else:
        with open(gitignore_path, "w") as f:
            f.write(ignore_entries.strip() + "\n")

    # 2. Spawn the Agentic Interview (Or Headless Setup)
    if not is_interactive:
        print(f"[SUCCESS] A.I.M. OS Headless Provisioning Complete.")
        if persona_name:
            print(f"[*] Downloading Persona Blueprint: {persona_name}")
            # In a full production setup, this would fetch from aim-coagents
            agents_md_path = os.path.join(BASE_DIR, "AGENTS.md")
            persona_content = f"# 🤖 Sovereign Co-Agent: {persona_name.title()}\n\nThis is a headless background node.\n\n## 1. IDENTITY\n- **Role:** Autonomous {persona_name}\n- **Execution Mode:** YOLO\n"
            with open(agents_md_path, "w") as f:
                f.write(persona_content)
            print(f"[SUCCESS] Persona '{persona_name}' linked and ready for autonomous execution.")
        return

    bootstrap_file = os.path.join(OS_DIR, "BOOTSTRAP.md")
    if not os.path.exists(bootstrap_file):
        print(f"[ERROR] {bootstrap_file} not found. Please run the curl installer.")
        sys.exit(1)
        
    import time
    from session_naming import build_agent_session_name
    session_name = build_agent_session_name("onboarding", BASE_DIR)
    
    check_cmd = subprocess.run(["tmux", "has-session", "-t", session_name], capture_output=True)
    if check_cmd.returncode == 0:
        print(f"[!] Onboarding session {session_name} is already running.")
        print(f"Attach with: tmux attach-session -t {session_name}")
        return

    try:
        print(f"Spawning the Onboarding Architect in {session_name}...")
        with open(bootstrap_file, "r") as f:
            bootstrap_content = f.read()
            bootstrap_content = bootstrap_content.replace("aim_onboarding", session_name)
            
        try:
            from agy_workspace_trust import prepare_agy_spawn, dismiss_trust_prompt_tmux

            base_cwd = prepare_agy_spawn(BASE_DIR)
        except Exception:
            base_cwd = BASE_DIR
            dismiss_trust_prompt_tmux = None  # type: ignore

        subprocess.run(
            [
                "tmux",
                "new-session",
                "-d",
                "-s",
                session_name,
                "-c",
                base_cwd,
                "agy",
                "--dangerously-skip-permissions",
            ],
            check=True,
        )

        # Deterministic polling for trust prompt and ready state
        max_retries = 20
        trusted = False
        injected = False

        if dismiss_trust_prompt_tmux:
            if dismiss_trust_prompt_tmux(session_name):
                trusted = True

        for _ in range(max_retries):
            result = subprocess.run(
                ["tmux", "capture-pane", "-p", "-t", session_name],
                capture_output=True,
                text=True,
            )
            out = result.stdout or ""

            if "trust the contents" in out or "trust this folder" in out or "Yes, I trust" in out:
                if not trusted:
                    # List UI: Enter confirms pre-selected Yes (do not send "y")
                    subprocess.run(
                        ["tmux", "send-keys", "-t", session_name, "Enter"], check=True
                    )
                    trusted = True
                    time.sleep(1)
                    continue

            # Wait for the CLI to fully load (it usually prints "Antigravity" or an agent prompt)
            if "Antigravity" in out or "Enter your" in out:
                subprocess.run(["tmux", "set-buffer", bootstrap_content], check=True)
                subprocess.run(
                    ["tmux", "paste-buffer", "-p", "-t", session_name], check=True
                )
                subprocess.run(
                    ["tmux", "send-keys", "-t", session_name, "Escape", "Enter"],
                    check=True,
                )
                injected = True
                break

            time.sleep(0.5)
            
        if not injected:
            print("[WARNING] Could not deterministically confirm CLI ready state. Falling back to blind injection.")
            subprocess.run(["tmux", "set-buffer", bootstrap_content], check=True)
            subprocess.run(["tmux", "paste-buffer", "-p", "-t", session_name], check=True)
            subprocess.run(["tmux", "send-keys", "-t", session_name, "Escape", "Enter"], check=True)
        print(f"[SUCCESS] The A.I.M. Architect has awakened in the background.")
        print(f"""
Please attach to the session to complete your interview:""")
        print(f"""    tmux attach-session -t {session_name}
""")
    except Exception as e:
        print(f"[ERROR] Failed to spawn onboarding agent: {e}")

if __name__ == "__main__":
    try: init_workspace(sys.argv)
    except KeyboardInterrupt: sys.exit(0)