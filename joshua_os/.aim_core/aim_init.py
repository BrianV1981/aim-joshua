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
    while True:
        if os.path.exists(os.path.join(current, "joshua_os", ".aim_core")) or os.path.exists(os.path.join(current, "setup.sh")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = find_project_root(os.getcwd())
OS_DIR = os.path.join(BASE_DIR, "joshua_os")
CORE_DIR = os.path.join(OS_DIR, "core")
DOCS_DIR = os.path.join(OS_DIR, "docs")
ARCHIVE_DIR = os.path.join(OS_DIR, "archive")
HOOKS_DIR = os.path.join(OS_DIR, "hooks")
AIM_CORE_DIR = os.path.join(OS_DIR, ".aim_core")
VENV_PYTHON = (
    os.path.join(OS_DIR, "venv", "Scripts", "python.exe")
    if os.name == "nt" and os.path.isfile(os.path.join(OS_DIR, "venv", "Scripts", "python.exe"))
    else (
        os.path.join(OS_DIR, "venv", "bin", "python3")
        if os.path.isfile(os.path.join(OS_DIR, "venv", "bin", "python3"))
        else sys.executable
    )
)

# --- INTERNAL TEMPLATES ---



def _load_default_agents_template() -> str:
    """Single source of truth for the full 10-section J.O.S.H.U.A. AGENTS.md blueprint."""
    tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "default_AGENTS.md")
    if os.path.isfile(tpl):
        with open(tpl, "r", encoding="utf-8") as f:
            return f.read()
    root_agents = os.path.join(BASE_DIR, "AGENTS.md")
    if os.path.isfile(root_agents):
        with open(root_agents, "r", encoding="utf-8") as f:
            return f.read()
    return "# 🤖 J.O.S.H.U.A. - Universal Operating System\n"


def _resolve_persona_blueprint(persona_name: str) -> str | None:
    """Resolves a Co-Agent persona blueprint from local ~/aim-coagents or GitHub without ever returning a 7-line stub."""
    safe_name = os.path.basename(persona_name.strip())
    if not safe_name:
        return None
    local_candidates = [
        os.path.expanduser(f"~/aim-coagents/blueprints/{safe_name}/AGENTS.md"),
        os.path.join(os.path.dirname(BASE_DIR), "aim-coagents", "blueprints", safe_name, "AGENTS.md"),
    ]
    for candidate in local_candidates:
        if os.path.isfile(candidate):
            with open(candidate, "r", encoding="utf-8") as f:
                content = f.read()
            if len(content.splitlines()) >= 15:
                return content

    import urllib.request
    url = f"https://raw.githubusercontent.com/BrianV1981/aim-coagents/main/blueprints/{safe_name}/AGENTS.md"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            if resp.status == 200:
                content = resp.read().decode("utf-8")
                if len(content.splitlines()) >= 15:
                    return content
    except Exception:
        pass
    return None


def provision_agents_md(base_dir: str, persona_name: str | None = None) -> str:
    """Ensures base_dir/AGENTS.md contains a full J.O.S.H.U.A. or Co-Agent blueprint and never a truncated stub."""
    agents_md_path = os.path.join(base_dir, "AGENTS.md")
    default_tpl = _load_default_agents_template()

    if persona_name:
        blueprint = _resolve_persona_blueprint(persona_name)
        if blueprint:
            with open(agents_md_path, "w", encoding="utf-8") as f:
                f.write(blueprint)
            return "persona_blueprint"
        # Fallback: preserve existing full AGENTS.md or install full default_AGENTS.md customized with persona designation
        existing = ""
        if os.path.isfile(agents_md_path):
            with open(agents_md_path, "r", encoding="utf-8") as f:
                existing = f.read()
        if len(existing.splitlines()) < 15:
            customized = default_tpl.replace(
                "- **Designation:** J.O.S.H.U.A.",
                f"- **Designation:** J.O.S.H.U.A. ({persona_name})",
                1,
            )
            with open(agents_md_path, "w", encoding="utf-8") as f:
                f.write(customized)
            return "default_with_persona"
        return "preserved_existing"

    # Standard init (no persona): restore full default_AGENTS.md if missing or truncated stub (<15 lines)
    existing = ""
    if os.path.isfile(agents_md_path):
        with open(agents_md_path, "r", encoding="utf-8") as f:
            existing = f.read()
    if len(existing.splitlines()) < 15:
        with open(agents_md_path, "w", encoding="utf-8") as f:
            f.write(default_tpl)
        return "restored_default"
    return "preserved_existing"





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

    config_path = os.path.join(AIM_CORE_DIR, "CONFIG.json")
    if not os.path.exists(config_path):
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


_AIM_HOOK_NAMES = {
    "cognitive-mantra",
    "session-summarizer",
    "failsafe-context-snapshot",
    "coreference-rewriter",
}


def _is_aim_hook_entry(hook_obj: dict) -> bool:
    if not isinstance(hook_obj, dict):
        return False
    if hook_obj.get("name") in _AIM_HOOK_NAMES:
        return True
    cmd = str(hook_obj.get("command") or "")
    return "aim_router.py" in cmd or "joshua_os/hooks" in cmd or "joshua_os\\hooks" in cmd


def register_hooks(is_light_mode=False):
    if AIM_CORE_DIR not in sys.path:
        sys.path.insert(0, AIM_CORE_DIR)
    from config_utils import get_agy_roots, get_agy_settings_paths

    router_src = os.path.join(OS_DIR, ".aim_core", "aim_router.py")
    for agy_root in get_agy_roots():
        if os.path.isdir(agy_root) and os.path.exists(router_src):
            router_dest = os.path.join(agy_root, "aim_router.py")
            shutil.copy2(router_src, router_dest)
            if os.name != "nt":
                os.chmod(router_dest, 0o755)

    existing_settings = get_agy_settings_paths(existing_only=True)
    if not existing_settings:
        return
    try:
        for settings_path in existing_settings:
            with open(settings_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
            if not raw_text.strip():
                settings = {}
            else:
                try:
                    settings = json.loads(raw_text)
                except json.JSONDecodeError as exc:
                    print(
                        f"[WARN] Skipping hook registration in {settings_path}: non-standard JSON/JSONC preserved ({exc})",
                        file=sys.stderr,
                    )
                    continue
                if not isinstance(settings, dict):
                    print(
                        f"[WARN] Skipping hook registration in {settings_path}: top-level JSON is not an object",
                        file=sys.stderr,
                    )
                    continue

            if not isinstance(settings.get("hooks"), dict):
                settings["hooks"] = {}

            # Enforce global Memory Boundary Marker for A.I.M. Isolation
            if not isinstance(settings.get("context"), dict):
                settings["context"] = {}
            settings["context"]["memoryBoundaryMarkers"] = ["AGENTS.md", ".git"]
            settings["context"]["discoveryMaxDirs"] = 0
            settings["context"]["fileName"] = ["AGENTS.md"]

            router_dest = os.path.join(os.path.dirname(settings_path), "aim_router.py")
            if os.path.exists(router_src):
                shutil.copy2(router_src, router_dest)
                if os.name != "nt":
                    os.chmod(router_dest, 0o755)

            # Remove stale A.I.M. hook entries while preserving all user-configured third-party hooks
            cleaned_hooks = {}
            for event_name, groups in settings["hooks"].items():
                if not isinstance(groups, list):
                    cleaned_hooks[event_name] = groups
                    continue
                kept_groups = []
                for grp in groups:
                    if isinstance(grp, dict) and isinstance(grp.get("hooks"), list):
                        remaining = [h for h in grp["hooks"] if not _is_aim_hook_entry(h)]
                        if remaining:
                            grp_copy = dict(grp)
                            grp_copy["hooks"] = remaining
                            kept_groups.append(grp_copy)
                    elif not _is_aim_hook_entry(grp):
                        kept_groups.append(grp)
                if kept_groups:
                    cleaned_hooks[event_name] = kept_groups
            settings["hooks"] = cleaned_hooks

            aim_hooks = {
                "AfterTool": [
                    ("cognitive-mantra", "cognitive_mantra.py")
                ]
            }

            py_cmd = f'"{VENV_PYTHON}"' if " " in VENV_PYTHON else VENV_PYTHON
            router_cmd = f'"{router_dest}"' if " " in router_dest else router_dest
            for event, hooks in aim_hooks.items():
                settings["hooks"].setdefault(event, [])
                for h in hooks:
                    entry = {"name": h[0], "type": "command", "command": f"{py_cmd} {router_cmd} {h[1]}"}
                    if len(h) > 2:
                        entry["matcher"] = h[2]
                    settings["hooks"][event].append({"hooks": [entry]})

            tmp_settings = settings_path + ".tmp"
            with open(tmp_settings, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
                f.write("\n")
            os.replace(tmp_settings, settings_path)

        print("[OK] Hooks registered via Universal Router.")
    except Exception as e:
        print(f"[ERROR] Hook registration failed: {e}", file=sys.stderr)
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
            "continuity/private", "continuity", "workstreams", "hooks", "scripts", "projects", "foundry", ".aim_core", "workspace"]
    for d in dirs: os.makedirs(os.path.join(OS_DIR, d), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, ".gemini"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "memory-wiki", "pages"), exist_ok=True)

    is_light_mode = "--light" in args
    register_hooks(is_light_mode)

    # Base settings and ignores (no empty 0-byte CHANGELOG/CONTRIBUTING/VERSION stubs)
    files = {
        "README.md": f"# {os.path.basename(BASE_DIR)}\n",
        ".geminiignore": """workspace/
archive/
memory_lance/
foundry/
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
        "joshua_os/.aim_core/CONFIG.json": json.dumps({
            "agent_identity": {
                "name": "J.O.S.H.U.A.",
                "role": "Universal Operating Agent and Systems Orchestrator.",
                "version": "1.1.3"
            },
            "paths": {
                "project_root": BASE_DIR,
                "os_root": OS_DIR,
                "aim_root": OS_DIR,
                "core_dir": os.path.join(OS_DIR, "core"),
                "docs_dir": os.path.join(OS_DIR, "docs"),
                "hooks_dir": os.path.join(OS_DIR, "hooks"),
                "archive_dir": os.path.join(OS_DIR, "archive"),
                "archive_raw_dir": os.path.join(OS_DIR, "archive", "raw"),
                "memory_dir": os.path.join(OS_DIR, "memory_lance"),
                "continuity_dir": os.path.join(OS_DIR, "continuity"),
                "src_dir": os.path.join(OS_DIR, ".aim_core"),
                "wiki_dir": os.path.join(BASE_DIR, "memory-wiki")
            },
            "settings": {
                "obsidian_vault_path": os.path.join(BASE_DIR, "memory-wiki"),
                "allowed_root": BASE_DIR
            }
        }, indent=2) + "\n"
    }
    
    for fp, content in files.items():
        full_path = os.path.join(BASE_DIR, fp)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if not os.path.exists(full_path):
            with open(full_path, "w") as f: f.write(content)

    # 1.5. Ensure consumer .gitignore excludes OS exoskeleton (never ignoring memory-wiki/)
    gitignore_path = os.path.join(BASE_DIR, ".gitignore")
    required_ignores = ["joshua_os/", "aim", "aim.ps1", "aim.cmd", "workspace/", "archive/"]
    existing_lines = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            existing_lines = [line.strip() for line in f.read().splitlines()]
    missing = [e for e in required_ignores if e not in existing_lines and e.rstrip("/") not in existing_lines]
    if missing:
        with open(gitignore_path, "a", encoding="utf-8") as f:
            if existing_lines and existing_lines[-1] != "":
                f.write("\n")
            for entry in missing:
                f.write(f"{entry}\n")

    # 1.6. Guarantee full AGENTS.md blueprint (never overwrite with a 7-line stub)
    provision_status = provision_agents_md(BASE_DIR, persona_name=persona_name)

    # 2. Spawn the Agentic Interview (Or Headless Setup)
    if not is_interactive:
        print(f"[SUCCESS] J.O.S.H.U.A. OS Headless Provisioning Complete ({provision_status}).")
        if persona_name:
            print(f"[SUCCESS] Persona '{persona_name}' provisioned in AGENTS.md.")
        return

    bootstrap_file = os.path.join(OS_DIR, "BOOTSTRAP.md")
    if not os.path.exists(bootstrap_file):
        print(f"[ERROR] {bootstrap_file} not found. Please run the installer.")
        sys.exit(1)

    if shutil.which("tmux") is None:
        print(f"[SUCCESS] J.O.S.H.U.A. OS Scaffolding Complete ({provision_status}).")
        print("[INFO] 'tmux' is not installed on this platform (POSIX Swarm add-on).")
        print("       Open this folder in your preferred IDE/CLI (Antigravity, Grok, OpenCode, Codex) —")
        print("       AGENTS.md will automatically prompt for your Operator Name on Turn 1,")
        print(f"       or paste {bootstrap_file} into your agent chat to run the full interview.")
        return
        
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
                time.sleep(0.3)
                # AGY 1.4.4+ / 2.0 rule: NEVER send Escape before Enter (Escape wipes [Pasted text] chip)
                subprocess.run(
                    ["tmux", "send-keys", "-t", session_name, "Enter"],
                    check=True,
                )
                injected = True
                break

            time.sleep(0.5)
            
        if not injected:
            print("[WARNING] Could not deterministically confirm CLI ready state. Falling back to blind injection.")
            subprocess.run(["tmux", "set-buffer", bootstrap_content], check=True)
            subprocess.run(["tmux", "paste-buffer", "-p", "-t", session_name], check=True)
            time.sleep(0.3)
            subprocess.run(["tmux", "send-keys", "-t", session_name, "Enter"], check=True)
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