#!/usr/bin/env python3
import traceback
import argparse
import subprocess
import sys
import os
import json
import glob
import shutil
import re
import sqlite3
from datetime import datetime

# --- VENV BOOTSTRAP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
aim_root = os.path.dirname(current_dir)
venv_python = os.path.join(aim_root, "venv", "bin", "python3")

if os.path.exists(venv_python) and sys.executable != venv_python:
    os.execv(venv_python, [venv_python] + sys.argv)

# --- CONFIG BOOTSTRAP ---
src_dir = os.path.join(aim_root, ".aim_core")
if src_dir not in sys.path: sys.path.append(src_dir)

from config_utils import CONFIG, PROJECT_ROOT, OS_ROOT

BASE_DIR = PROJECT_ROOT
OS_DIR = OS_ROOT
CLI_NAME = os.path.basename(BASE_DIR)
VENV_PYTHON = os.path.join(OS_DIR, "venv/bin/python3")
if not os.path.exists(VENV_PYTHON):
    # Support for worktrees (workspace/issue-<id>/joshua_os -> ../../../joshua_os/venv/bin/python3)
    for _rel in ("../../venv/bin/python3", "../../../joshua_os/venv/bin/python3"):
        _cand = os.path.abspath(os.path.join(OS_DIR, _rel))
        if os.path.exists(_cand):
            VENV_PYTHON = _cand
            break
    else:
        VENV_PYTHON = sys.executable
AIM_CORE_DIR = os.path.join(OS_DIR, ".aim_core")

def run_script(script_path, args):
    """Executes an A.I.M. script with the provided arguments."""
    cmd = [VENV_PYTHON, script_path] + args
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Command '{' '.join(cmd)}' failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)

def run_bash_script(script_path, args):
    """Executes a bash script with the provided arguments."""
    cmd = ["bash", script_path] + args
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Bash script '{' '.join(cmd)}' failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)

def cmd_core_memory(args):
    """Opens the CORE_MEMORY.md file in the user's default editor."""
    core_mem_file = os.path.join(OS_DIR, "continuity/CORE_MEMORY.md")
    if not os.path.exists(core_mem_file):
        os.makedirs(os.path.join(OS_DIR, "continuity"), exist_ok=True)
        with open(core_mem_file, 'w') as f:
            f.write("# A.I.M. Core Memory (RAM)\n\n*This file acts as the Agent's writable RAM. The agent can use the `aim core-memory` command to save critical facts, state, or observations here that must survive across context windows and cannot wait for the background summarizer.*\n\n- [Empty]\n")
    
    editor = os.environ.get('EDITOR', 'nano')
    subprocess.call([editor, core_mem_file])

def cmd_status(args):
    """Displays the current A.I.M. operational pulse."""
    # handoff_pulse_generator writes .aim_core/temp/CURRENT_PULSE.md (canonical).
    # continuity/ is legacy doc path — still accepted as fallback.
    candidates = [
        os.path.join(OS_DIR, ".aim_core", "temp", "CURRENT_PULSE.md"),
        os.path.join(OS_DIR, "continuity", "CURRENT_PULSE.md"),
        os.path.join(PROJECT_ROOT, "continuity", "CURRENT_PULSE.md"),
    ]
    status_file = next((p for p in candidates if os.path.isfile(p)), None)
    if status_file:
        with open(status_file, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print(
            "Error: CURRENT_PULSE.md not found. Run 'aim handoff' / 'aim pulse' to generate "
            f"(looked under {candidates[0]}).",
            file=sys.stderr,
        )

def cmd_search(args):
    """Dispatches to retriever.py."""
    query = " ".join(args.query)
    retriever_args = [query]
    if args.top_k: retriever_args += ["--top-k", str(args.top_k)]
    if args.full: retriever_args += ["--full"]
    if args.session: retriever_args += ["--session", args.session]
    if getattr(args, "json", False): retriever_args += ["--json"]
    run_script(os.path.join(AIM_CORE_DIR, "retriever.py"), retriever_args)



def cmd_map(args):
    """Prints the surgical Index of Keys."""
    run_script(os.path.join(AIM_CORE_DIR, "retriever.py"), ["--map"])

def cmd_index(args):
    """Dispatches to bootstrap_brain.py."""
    cmd_args = []
    if getattr(args, 'dir', None):
        cmd_args.extend(["--dir", args.dir])
    run_script(os.path.join(AIM_CORE_DIR, "bootstrap_brain.py"), cmd_args)

def cmd_doctor(args):
    """Dispatches to aim_doctor.py to validate environment dependencies."""
    run_script(os.path.join(AIM_CORE_DIR, "aim_doctor.py"), [])

def cmd_health(args):
    """Dispatches to heartbeat.py."""
    run_script(os.path.join(AIM_CORE_DIR, "heartbeat.py"), [])

def cmd_projects(args):
    """GitHub Projects (kanban) GitOps — thin wrapper over aim_projects.py / gh project."""
    from aim_projects import main as projects_main

    # Rebuild argv for aim_projects: drop 'projects' and global aim flags already parsed
    # subcommand lives on args.projects_command; forward remaining via namespace → list
    fwd = []
    # Global project targeting flags (optional overrides)
    if getattr(args, "projects_owner", None):
        fwd += ["--owner", args.projects_owner]
    if getattr(args, "projects_number", None) is not None:
        fwd += ["--number", str(args.projects_number)]
    if getattr(args, "projects_status_field", None):
        fwd += ["--status-field", args.projects_status_field]
    if getattr(args, "projects_repo", None):
        fwd += ["--repo", args.projects_repo]

    action = getattr(args, "projects_command", None)
    if not action:
        projects_main([])
        return

    fwd.append(action)

    if action == "board":
        if getattr(args, "board_status", None):
            fwd += ["--status", args.board_status]
        if getattr(args, "board_limit", None) is not None:
            fwd += ["--limit", str(args.board_limit)]
        if getattr(args, "board_json", False):
            fwd.append("--json")
    elif action in ("in-progress", "done", "ready", "todo", "blocked", "view"):
        if getattr(args, "issue", None) is None:
            print(f"Usage: {CLI_NAME} projects {action} <issue_number>", file=sys.stderr)
            sys.exit(1)
        fwd.append(str(args.issue))
    elif action == "set":
        if getattr(args, "issue", None) is None or not getattr(args, "set_status", None):
            print(f"Usage: {CLI_NAME} projects set <issue_number> <status>", file=sys.stderr)
            sys.exit(1)
        fwd += [str(args.issue), args.set_status]
    # list / fields / doctor need no extra args

    projects_main(fwd)


def cmd_bug(args):
    """Creates a highly-structured GitHub Issue using the gh CLI. Strict agent-driven version."""
    print("--- A.I.M. ISSUE TRACKER ---")
    title = args.title

    context = getattr(args, 'context', "").strip()
    failure = getattr(args, 'failure', "").strip()
    intent = getattr(args, 'intent', "").strip()

    if not (context or failure or intent):
        print("\n[MANDATE VIOLATION] Commander's Intent Required.")
        print("You MUST NOT call `aim bug` without the explicit context flags (--context, --failure, --intent).")
        print("This ticket requires sufficient context for the next agent to resolve the issue with full epistemic certainty.")
        print("Please read the TICKET_SOP.md and rerun the command with highly detailed flags.")
        sys.exit(1)    
    
    # Construct the high-fidelity markdown body
    body = f"## Description\n{title}\n\n"
    
    if context or failure or intent:
        body += "### 🧠 Commander's Intent\n"
        if context:
            body += f"**Context:**\n{context}\n\n"
        if failure:
            body += f"**The Goal/Failure:**\n{failure}\n\n"
        if intent:
            body += f"**Action Items:**\n{intent}\n\n"
    else:
        body += "*No explicit Commander's Intent provided.*\n\n"
        
    try:
        print("\n[1/1] Dispatching to GitHub CLI...")
        # Determine label based on title heuristic (optional, but nice)
        label = "enhancement" if "feature" in title.lower() or "epic" in title.lower() else "bug"
        subprocess.run(["gh", "issue", "create", "--title", title, "--body", body, "--label", label], check=True)
        print(f"[SUCCESS] {label.capitalize()} ticket created. Run '{CLI_NAME} fix <id>' to branch out.")
    except FileNotFoundError:
        print(f"[ERROR] GitHub CLI ('gh') is not installed. Please install it to use '{CLI_NAME} bug'.")
    except Exception as e:
        traceback.print_exc()
        print(f"[ERROR] Failed to create issue: {e}")

def cmd_bug_operator(args):
    """Creates a highly-structured GitHub Issue using the gh CLI with interactive prompts for operators."""
    print("--- A.I.M. ISSUE TRACKER (Operator Mode) ---")
    title = args.title

    context = getattr(args, 'context', "").strip()
    failure = getattr(args, 'failure', "").strip()
    intent = getattr(args, 'intent', "").strip()

    if not (context or failure or intent):
        print("\n[MANDATE] Commander's Intent Required.")
        print("To ensure a 'blind' agent can resolve this ticket, you must provide explicit context per the TICKET_SOP.md.")

        # Prompt the user/agent for the three critical components
        context = input("\n1. The Context (What were you trying to do? Reference specific files/architecture): ").strip()
        failure = input("\n2. The Failure/Goal (Provide exact error strings or specific capability required): ").strip()
        intent = input("\n3. Action Items (Provide a prescriptive, step-by-step implementation plan): ").strip()    
    
    # Construct the high-fidelity markdown body
    body = f"## Description\n{title}\n\n"
    
    if context or failure or intent:
        body += "### 🧠 Commander's Intent\n"
        if context:
            body += f"**Context:**\n{context}\n\n"
        if failure:
            body += f"**The Goal/Failure:**\n{failure}\n\n"
        if intent:
            body += f"**Action Items:**\n{intent}\n\n"
    else:
        body += "*No explicit Commander's Intent provided.*\n\n"
        
    try:
        print("\n[1/1] Dispatching to GitHub CLI...")
        # Determine label based on title heuristic (optional, but nice)
        label = "enhancement" if "feature" in title.lower() or "epic" in title.lower() else "bug"
        subprocess.run(["gh", "issue", "create", "--title", title, "--body", body, "--label", label], check=True)
        print(f"[SUCCESS] {label.capitalize()} ticket created. Run '{CLI_NAME} fix <id>' to branch out.")
    except FileNotFoundError:
        print(f"[ERROR] GitHub CLI ('gh') is not installed. Please install it to use '{CLI_NAME} bug'.")
    except Exception as e:
        traceback.print_exc()
        print(f"[ERROR] Failed to create issue: {e}")


def cmd_fix(args):
    """Spawns a Git Worktree for a specific GitHub Issue ID."""
    issue_id = args.id
    branch_name = f"fix/issue-{issue_id}"
    worktree_path = os.path.join(PROJECT_ROOT, "workspace", f"issue-{issue_id}")
    print(f"--- A.I.M. FACTORY FLOOR (Issue #{issue_id}) ---")
    try:
        subprocess.run(["git", "worktree", "add", worktree_path, "-b", branch_name], cwd=BASE_DIR, check=True)
        
        # Copy the gitignored local CONFIG.json so the worktree can run tests natively
        import shutil
        config_src = os.path.join(PROJECT_ROOT, ".aim_core", "CONFIG.json")
        config_dest_dir = os.path.join(worktree_path, ".aim_core")
        if os.path.exists(config_src):
            os.makedirs(config_dest_dir, exist_ok=True)
            shutil.copy2(config_src, os.path.join(config_dest_dir, "CONFIG.json"))
            
        print(f"[SUCCESS] Worktree created at {worktree_path} on branch {branch_name}")
        print(f"[ACTION] To start working, run: cd workspace/issue-{issue_id}")
        print(f"[ACTION] When the bug is resolved, run: {CLI_NAME} push \"Fix: <description> (Closes #{issue_id})\"")
    except Exception as e:
        traceback.print_exc()
        print(f"[ERROR] Failed to create worktree: {e}")

def cmd_prune_remote(args):
    """Prunes remote tracking branches like archive-fix/* and fix/issue-* that are no longer needed."""
    print("--- A.I.M. REMOTE BRANCH PRUNE ---")
    try:
        result = subprocess.run(["git", "branch", "-r"], cwd=BASE_DIR, capture_output=True, text=True, check=True)
        branches = [b.strip() for b in result.stdout.split('\n') if b.strip()]
        
        # Get open PR heads to protect them
        open_prs = set()
        pr_result = subprocess.run(["gh", "pr", "list", "--state", "open", "--json", "headRefName"], cwd=BASE_DIR, capture_output=True, text=True)
        if pr_result.returncode == 0:
            import json
            try:
                pr_data = json.loads(pr_result.stdout)
                open_prs = {pr["headRefName"] for pr in pr_data}
            except Exception:
                pass
        else:
            if getattr(args, 'confirm', False):
                print("[ERROR] Could not fetch open PRs from GitHub. Aborting unsafe remote prune.")
                return
            else:
                print("[WARNING] Could not fetch open PRs from GitHub. Proceeding with dry-run caution.")
            
        to_delete = []
        skipped = []
        for b in branches:
            if b.startswith("origin/archive-fix/") or b.startswith("origin/fix/issue-"):
                branch_name = b.replace("origin/", "", 1)
                if branch_name in open_prs:
                    skipped.append(branch_name)
                else:
                    to_delete.append(branch_name)
        
        if skipped:
            print(f"[INFO] Skipping {len(skipped)} branches that have open PRs:")
            for b in skipped:
                print(f"  - [PROTECTED] {b}")
                
        if not to_delete:
            print("[INFO] No stale remote branches found to delete.")
            return
            
        print(f"\n[INFO] Found {len(to_delete)} stale remote branches:")
        for b in to_delete:
            print(f"  - {b}")
            
        if not getattr(args, 'confirm', False):
            print("\n[DRY RUN] This was a dry run. To actually delete these branches from the remote, run with --confirm")
            return
            
        print("\n[ACTION] Deleting branches from origin...")
        for branch in to_delete:
            try:
                subprocess.run(["git", "push", "origin", "--delete", branch], cwd=BASE_DIR, capture_output=True, text=True, check=True)
                print(f"  [DELETED] {branch}")
            except subprocess.CalledProcessError as e:
                print(f"  [ERROR] Failed to delete {branch}: {e.stderr.strip()}")
                
        print("\n[SUCCESS] Remote cleanup complete.")
    except Exception as e:
        print(f"\n[ERROR] Failed to prune remote branches: {e}")

def cmd_promote(args):
    """Automates the Phase Protocol: Archives main, merges current dev branch, and cleans up the worktree."""
    print("--- A.I.M. PHASE PROMOTION ---")
    try:
        current_dir = os.getcwd()
        in_worktree = "workspace/issue-" in current_dir
        
        # Determine the main repository root dynamically by finding the common .git directory
        common_dir = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=current_dir, capture_output=True, text=True, check=True).stdout.strip()
        repo_root = os.path.dirname(os.path.abspath(os.path.join(current_dir, common_dir)))
        
        if not os.path.isdir(os.path.join(repo_root, ".git")):
            print(f"[ERROR] CRITICAL: Computed repo_root '{repo_root}' does not contain a .git directory. Aborting promote.")
            return
        # Determine default branch (main or master)
        branches = subprocess.run(["git", "branch", "--list"], cwd=repo_root, capture_output=True, text=True).stdout
        default_branch = "master" if "master" in branches and "main" not in branches else "main"
        
        # The dev branch is where the command is run (the worktree)
        result = subprocess.run(["git", "branch", "--show-current"], cwd=current_dir, capture_output=True, text=True, check=True)
        current_branch = result.stdout.strip()
        
        if current_branch == default_branch:
            print(f"[ERROR] You are already on '{default_branch}'. Please run 'aim promote' from your dev branch.")
            return
            
        print(f"[1/5] Preparing to promote '{current_branch}' to {default_branch}...")
        
        print('\n[CRITICAL INTERVENTION REQUIRED]')
        print('[WARNING TO AGENT] You are strictly forbidden from guessing this answer.')
        print('[WARNING TO AGENT] You MUST use your ask_question / UI modal tool to prompt the Operator.')
        print('[WARNING TO AGENT] Once the Operator confirms, stream their answer to stdin (yes/no).')

        confirm = input(f"\nMerge branch '{current_branch}' to {default_branch}? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print('\n[ABORTED] Promotion cancelled. Branch remains isolated.')
            return
        
        # 1. Fetch latest (run in repo_root)
        subprocess.run(["git", "fetch", "origin"], cwd=repo_root, check=True, capture_output=True, text=True)
        
        # 2. Archive current main
        date_str = datetime.now().strftime("%Y%m%d-%H%M")
        archive_branch = f"archive-{current_branch}-{date_str}"
        print(f"[2/5] Backing up current '{default_branch}' to '{archive_branch}'...")
        subprocess.run(["git", "checkout", default_branch], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "checkout", "-b", archive_branch], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "push", "-u", "origin", archive_branch], cwd=repo_root, check=True, capture_output=True, text=True)
        
        # 3. Merge dev branch into main
        print(f"[3/5] Merging '{current_branch}' into {default_branch}...")
        subprocess.run(["git", "checkout", default_branch], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "merge", current_branch, "--no-edit"], cwd=repo_root, check=True, capture_output=True, text=True)
        
        # 4. Push main
        print(f"[4/5] Deploying new baseline to GitHub...")
        subprocess.run(["git", "push", "origin", default_branch], cwd=repo_root, check=True, capture_output=True, text=True)
        
        # 5. Cleanup
        print(f"[5/5] Cleaning up local workspace...")
        if in_worktree:
            # We must leave the worktree directory before we can remove it
            os.chdir(repo_root)
            subprocess.run(["git", "worktree", "remove", current_dir, "--force"], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "branch", "-D", current_branch], cwd=repo_root, check=True, capture_output=True, text=True)
        
        print(f"\n[SUCCESS] Promotion complete. You are now on a clean '{default_branch}' branch in the root repository.")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Git operation failed. Promotion aborted. Please check your git status.")
        print(f"Command: {e.cmd}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
    except Exception as e:
        traceback.print_exc()
        print(f"\\n[ERROR] Failed to promote: {e}")

def cmd_merge_batch(args):
    """Executes the aim_batch_merge.py script to cleanly merge an entire Phase of tickets."""
    print('\n[CRITICAL INTERVENTION REQUIRED]')
    print('[WARNING TO AGENT] You are strictly forbidden from guessing this answer.')
    print('[WARNING TO AGENT] You MUST use your ask_question / UI modal tool to prompt the Operator.')
    print('[WARNING TO AGENT] Once the Operator confirms, stream their answer to stdin (yes/no).')

    confirm = input("\nExecute batch merge to main? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print('\n[ABORTED] Batch merge cancelled. Main remains isolated.')
        return

    merge_args = []
    if args.push:
        merge_args.append("--push")
    run_script(os.path.join(AIM_CORE_DIR, "aim_batch_merge.py"), merge_args)

def cmd_push(args):
    """Dispatches to aim_push.sh with Sovereign Sync and Semantic Release."""
    msg = args.message
    
    # 1. SEMANTIC RELEASE PIPELINE (Phase 23)
    print("--- A.I.M. SEMANTIC RELEASE ---")
    version_file = os.path.join(BASE_DIR, "VERSION")
    changelog_file = os.path.join(BASE_DIR, "CHANGELOG.md")
    
    try:
        current_version = "v1.0.0"
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                current_version = f.read().strip()
                
        # Fallback if the old date-based versioning is in place
        if len(current_version.split('.')) != 3 or "202" in current_version:
            current_version = "v1.5.0"
            
        major, minor, patch = map(int, current_version.replace('v', '').split('.'))
        
        bump_type = "none"
        if msg.startswith("BREAKING CHANGE:"): bump_type = "major"
        elif msg.startswith("Feature:") or msg.startswith("feat:"): bump_type = "minor"
        elif msg.startswith("Fix:") or msg.startswith("fix:"): bump_type = "patch"
        
        if bump_type == "major":
            major += 1; minor = 0; patch = 0
        elif bump_type == "minor":
            minor += 1; patch = 0
        elif bump_type == "patch":
            patch += 1
            
        new_version = f"v{major}.{minor}.{patch}"
        
        if bump_type != "none":
            print(f"[1/3] Bumping version: {current_version} -> {new_version}")
            with open(version_file, 'w') as f: f.write(new_version)
            
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_entry = f"## [{new_version}] - {date_str}\n- {msg}\n\n"
            
            if not os.path.exists(changelog_file):
                with open(changelog_file, 'w') as f:
                    f.write(f"# Changelog\n\n{log_entry}")
            else:
                with open(changelog_file, 'r') as f: content = f.read()
                content = content.replace("# Changelog\n", f"# Changelog\n\n{log_entry}")
                with open(changelog_file, 'w') as f: f.write(content)
        else:
            print(f"[1/3] No semantic prefix found (Feature/Fix/BREAKING CHANGE). Version remains {new_version}.")
    except Exception as e:
        traceback.print_exc()
        print(f"[WARNING] Semantic Release failed: {e}")

    # 2. SOVEREIGN SYNC (Decoupled Background Task)
    try:
        print("[2/3] Spawning background Engram DB translation...")
        # Fire and forget the sync so it doesn't block the push or crash the CLI if the DB is locked
        subprocess.Popen(
            [VENV_PYTHON, os.path.join(AIM_CORE_DIR, "sovereign_sync.py"), "export"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        traceback.print_exc()
        print(f"[WARNING] Background Sovereign Sync spawn failed: {e}")
        
    print("[3/3] Deploying to GitHub...")
    run_bash_script(os.path.join(AIM_CORE_DIR, "aim_push.sh"), [msg])

def cmd_sync_issues(args):
    """Synchronizes remote GitHub issues to the local ISSUE_TRACKER.md file."""
    run_script(os.path.join(AIM_CORE_DIR, "sync_issue_tracker.py"), [])


def cmd_delegate(args):
    """Dispatches to aim_delegate.py to spawn parallel sub-agents."""
    delegate_args = [args.instruction, "--files"] + args.files
    run_script(os.path.join(AIM_CORE_DIR, "aim_delegate.py"), delegate_args)


def cmd_handoff(args):
    """Dispatches to handoff_pulse_generator.py and syncs remote issues."""
    run_script(os.path.join(AIM_CORE_DIR, "handoff_pulse_generator.py"), [])
    run_script(os.path.join(AIM_CORE_DIR, "sync_issue_tracker.py"), [])


def cmd_init(args):
    """Dispatches to aim_init.py (New User Setup)."""
    init_args = []
    if args.reinstall: init_args.append("--reinstall")
    if args.uninstall: init_args.append("--uninstall")
    if args.light: init_args.append("--light")
    if getattr(args, "headless", False): init_args.append("--headless")
    if getattr(args, "persona", None): init_args.extend(["--persona", args.persona])
    if getattr(args, "clean", False): init_args.append("--clean")
    try:
        subprocess.run([VENV_PYTHON, os.path.join(AIM_CORE_DIR, "aim_init.py")] + init_args, check=True)
    except subprocess.CalledProcessError as e:
        import sys; print(f"[ERROR] 'aim init' failed: {e}", file=sys.stderr)


def cmd_config(args):
    """Dispatches to aim_config.py (TUI Cockpit)."""
    try:
        subprocess.run([VENV_PYTHON, os.path.join(AIM_CORE_DIR, "aim_config.py")], check=True)
    except subprocess.CalledProcessError as e:
        import sys; print(f"[ERROR] 'aim config' failed: {e}", file=sys.stderr)


from cli_vault import (
    cmd_handoff_vnext,
    cmd_vault,
    cmd_agy_blackbox,
    cmd_grok_blackbox,
    cmd_codex_blackbox,
    cmd_opencode_blackbox,
)
from cli_memory import (
    cmd_clean,
    cmd_sync,
    cmd_audit,
    cmd_recall,
    cmd_mail,
    cmd_sessions,
    cmd_search_sessions,
    cmd_scrape,
    cmd_bake,
    cmd_export,
    cmd_exchange,
    cmd_jack_in,
    cmd_unplug,
    cmd_purge,
    cmd_uninstall,
    cmd_import,
)


def cmd_update(args):
    """Safely pulls the latest A.I.M. core engine files into the local isolated project while preserving Co-Agent blueprint and tenant state."""
    print("--- A.I.M. SOVEREIGN ENGINE UPDATE ---")
    source_arg = getattr(args, "source", None)
    skip_deps = getattr(args, "skip_deps", False)
    temp_dir = None

    if source_arg:
        source_root = os.path.abspath(source_arg)
        candidate_os = os.path.join(source_root, "joshua_os") if os.path.isdir(os.path.join(source_root, "joshua_os")) else source_root
        if not os.path.isdir(os.path.join(candidate_os, ".aim_core")):
            print(f"[ERROR] Invalid local update source '{source_arg}': missing .aim_core directory.", file=sys.stderr)
            sys.exit(1)
        source_os_dir = candidate_os
        print(f"[*] Using local engine source: {source_os_dir}")
    else:
        print("[*] Contacting remote Swarm network...")
        temp_dir = os.path.join(OS_DIR, ".aim_temp_update")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        try:
            import urllib.request
            import zipfile
            import io

            zip_url = "https://github.com/BrianV1981/aim-joshua/archive/refs/heads/main.zip"
            req = urllib.request.Request(zip_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                with zipfile.ZipFile(io.BytesIO(response.read())) as z:
                    z.extractall(temp_dir)
            print("    [SUCCESS] Remote payload secured.")
        except Exception as e:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            traceback.print_exc()
            print(f"[ERROR] Failed to connect to Swarm network: {e}", file=sys.stderr)
            sys.exit(1)

        extracted_root = os.path.join(temp_dir, "aim-joshua-main")
        source_os_dir = os.path.join(extracted_root, "joshua_os")

    # Preserve local .aim_core/CONFIG.json across engine swap
    local_core = os.path.join(OS_DIR, ".aim_core")
    config_path = os.path.join(local_core, "CONFIG.json")
    preserved_config = None
    if os.path.isfile(config_path):
        with open(config_path, "rb") as cf:
            preserved_config = cf.read()

    # Surgically overwrite core logic folders (strictly preserving tenant AGENTS.md, TOOLS.md, manifest.json, memory-wiki/, artifacts/, memory_lance/)
    print("[*] Hot-swapping local execution engine...")
    for subdir in (".aim_core", "joshua_os_docs", "handoff", "scripts", "hooks"):
        src_sub = os.path.join(source_os_dir, subdir)
        dst_sub = os.path.join(OS_DIR, subdir)
        if os.path.isdir(src_sub):
            if os.path.exists(dst_sub):
                shutil.rmtree(dst_sub)
            shutil.copytree(src_sub, dst_sub)

    if preserved_config is not None:
        os.makedirs(local_core, exist_ok=True)
        with open(config_path, "wb") as cf:
            cf.write(preserved_config)

    for fname in ("setup.sh", "requirements.txt", "link_cli_alias.sh", "VERSION"):
        src_file = os.path.join(source_os_dir, fname)
        if os.path.isfile(src_file):
            shutil.copy2(src_file, os.path.join(OS_DIR, fname))

    # Cleanup deprecated background daemons (Active Memory Protocol)
    deprecated_wiki_agents = os.path.join(OS_DIR, "memory-wiki", "AGENTS.md")
    if os.path.exists(deprecated_wiki_agents):
        os.remove(deprecated_wiki_agents)
    deprecated_ingest = os.path.join(OS_DIR, "memory-wiki", "_ingest")
    if os.path.exists(deprecated_ingest):
        shutil.rmtree(deprecated_ingest)

    if not skip_deps and os.path.isfile(os.path.join(OS_DIR, "setup.sh")):
        print("[*] Rebuilding dependencies...")
        subprocess.run(["bash", os.path.join(OS_DIR, "setup.sh")], check=True, cwd=BASE_DIR, stdout=subprocess.DEVNULL)

    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    print("\n[SUCCESS] Sovereign Engine Update Complete. You are running the latest A.I.M. OS.")


def ensure_hooks_mapped():
    """Silently self-heals stale hook paths in the global Antigravity CLI settings when the workspace is moved or cloned."""
    settings_path = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")
    if not os.path.exists(settings_path): return
    try:
        import json
        with open(settings_path, "r") as f:
            settings = json.load(f)
        
        needs_update = False
        after_hooks = settings.get("hooks", {}).get("AfterTool", [])
        for entry in after_hooks:
            for hook in entry.get("hooks", []):
                if hook.get("name") == "cognitive-mantra":
                    if "aim_router.py" not in hook.get("command", ""):
                        needs_update = True
                        break
        
        if needs_update:
            try:
                import sys
                sys.path.append(AIM_CORE_DIR)
                import aim_init
                aim_init.register_hooks()
            except:
                pass
    except:
        pass


def main():
    ensure_hooks_mapped()
    parser = argparse.ArgumentParser(description="A.I.M. CLI")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Initialize or update A.I.M. workspace")
    init_parser.add_argument("--reinstall", action="store_true", help="Perform a total reinstall with backup")
    init_parser.add_argument("--uninstall", action="store_true", help="Show uninstallation instructions")
    init_parser.add_argument('--light', action='store_true', help='Install the Lightweight AOS Mode (Zero-RAG, continuity only)')
    init_parser.add_argument('--headless', action='store_true', help='Run the installer silently without interactive prompts')
    init_parser.add_argument('--persona', type=str, help='Persona blueprint name for headless co-agent deployment')
    init_parser.add_argument('--clean', action='store_true', help='Force a clean sweep during headless mode (wipes docs, resets brain, provides OS engram)')

    subparsers.add_parser("status", help="Show current project momentum")
    subparsers.add_parser("config", aliases=["tui"])
    subparsers.add_parser("core-memory", help="Open the Core Memory block for instant invariant tracking")
    update_parser = subparsers.add_parser("update", help="Update the A.I.M. engine or the target project")
    update_parser.add_argument("target", choices=["engine", "project"], nargs="?", default="engine", help="Which component to update")
    update_parser.add_argument("--source", type=str, default=None, help="Optional local path to aim-joshua source repository")
    update_parser.add_argument("--skip-deps", action="store_true", help="Skip running setup.sh dependency rebuild after engine file sync")
    subparsers.add_parser("doctor", help="Run a diagnostic check on system dependencies")
    subparsers.add_parser("health")
    
    prune_remote_parser = subparsers.add_parser("prune-remote", help="Garbage collect stale remote branches (fix/issue-* and archive-fix/*)")
    prune_remote_parser.add_argument("--confirm", action="store_true", help="Execute the deletions instead of dry-run")
    
    subparsers.add_parser("purge")
    subparsers.add_parser("uninstall")
    index_parser = subparsers.add_parser("index", help="Bootstrap and ingest documents into the A.I.M. Brain")
    index_parser.add_argument("--dir", type=str, help="Custom target directory to ingest")
    scrape_parser = subparsers.add_parser("scrape", help="Scrape Forum/Issues into Synapse Markdown docs.")
    scrape_parser.add_argument("--source", choices=["github", "stackoverflow"], default="github", help="Source to scrape from")
    scrape_parser.add_argument("--repo", default=None, help="Target repository for github source")
    scrape_parser.add_argument("--query", default=None, help="Search query for stackoverflow source")
    scrape_parser.add_argument("--limit", type=int, default=10, help="Number of threads to fetch")
    scrape_parser.add_argument("--outdir", default="synapse", help="Output directory")


    subparsers.add_parser("handoff", aliases=["pulse"])
    subparsers.add_parser("sync")
    subparsers.add_parser("sync-issues", help="Synchronize remote GitHub issues to local ledger")

    
    vault_parser = subparsers.add_parser(
        "vault",
        help="Operator black-box forensic seal (audit/verify; seal is reincarnate-policy)",
    )
    vault_sub = vault_parser.add_subparsers(dest="vault_command")
    vault_audit = vault_sub.add_parser("audit", help="Decrypt sealed session to stdout")
    vault_audit.add_argument("session_id")
    vault_audit.add_argument("--vessel", default=None, help="Vessel root (default cwd)")
    vault_verify = vault_sub.add_parser("verify", help="Compare sealed sha256 to live file")
    vault_verify.add_argument("session_id")
    vault_verify.add_argument("--vessel", default=None)
    vault_verify.add_argument("--live", default=None, help="Path to live transcript")
    vault_seal = vault_sub.add_parser(
        "seal", help="Manual seal (Operator); same reincarnate-only reason string"
    )
    vault_seal.add_argument("--session-id", default=None)
    vault_seal.add_argument("--path", default=None, help="Explicit raw transcript path")
    vault_seal.add_argument("--vessel", default=None)

    vault_doctor = vault_sub.add_parser("doctor", help="Run vault diagnostics and key recovery info")

    agy_bb_parser = subparsers.add_parser("agy-blackbox", help="Seal AGY transcript to vault")
    agy_bb_parser.add_argument("--session-id", required=True)

    grok_bb_parser = subparsers.add_parser("grok-blackbox", help="Seal Grok transcript to vault")
    grok_bb_parser.add_argument("--session-id", required=True)

    codex_bb_parser = subparsers.add_parser("codex-blackbox", help="Seal Codex transcript to vault")
    codex_bb_parser.add_argument("--session-id", required=True)

    oc_bb_parser = subparsers.add_parser("opencode-blackbox", help="Seal OpenCode SQLite db to vault")
    oc_bb_parser.add_argument("--session-id", required=True)

    hv_parser = subparsers.add_parser(
        "handoff-vnext",
        help="Handoff vNext: handoff | wiki-batch | blackbox-cron | cron-all | e2e-staged",
    )
    hv_parser.add_argument(
        "vnext_command",
        choices=["handoff", "wiki-batch", "blackbox-cron", "cron-all", "e2e-staged"],
    )
    hv_parser.add_argument("--session-id", default=None)
    hv_parser.add_argument("--adapter", default="agy", help="agy|grok|fixture")
    hv_parser.add_argument("--fixture-root", default=None)
    hv_parser.add_argument("--marker", default=None)
    hv_parser.add_argument("--limit", type=int, default=50)
    hv_parser.add_argument("--json", action="store_true")
    
    delegate_parser = subparsers.add_parser("delegate", help="Spawn parallel sub-agents to analyze multiple files (The RLM Pattern)")
    delegate_parser.add_argument("instruction", help="The prompt to give each sub-agent")
    delegate_parser.add_argument("--files", nargs="+", required=True, help="List of files to analyze")

    import_parser = subparsers.add_parser("import", help="Manually ingest files into the LLM Wiki")
    import_parser.add_argument("file", help="Path to the .jsonl or .md file")
    
    subparsers.add_parser("clean")
    subparsers.add_parser("exchange", help="Export/Import .engram cartridges")
    
    export_parser = subparsers.add_parser("export", help="Package and seed local .engram files")
    export_parser.add_argument("file", help="Path to the .engram file to seed")

    bake_parser = subparsers.add_parser("bake", help="Manufacture an atomic .engram cartridge directly from a docs folder")
    bake_parser.add_argument("directory", help="The raw documentation directory to vectorize")
    bake_parser.add_argument("output", help="The name of the resulting .engram file (e.g. pytest.engram)")
    bake_parser.add_argument("--author", help="Author of the cartridge (Manifest metadata)", default="Unknown")
    bake_parser.add_argument("--version", help="Version of the cartridge (e.g., 1.0.0)", default="1.0.0")
    bake_parser.add_argument("--description", help="Description of the cartridge contents", default="No description provided.")

    jackin_parser = subparsers.add_parser("jack-in", help="Alias for aim exchange import")
    jackin_parser.add_argument("file", help="Path to the .engram file")
    
    unplug_parser = subparsers.add_parser("unplug", help=f"Alias for {CLI_NAME} exchange unplug")
    unplug_parser.add_argument("keyword", help="The keyword to delete (e.g., 'python314')")



    subparsers.add_parser("map", help="Print the Index of Keys (Knowledge Map)")

    audit_parser = subparsers.add_parser("audit", help="Generate a strategic synthesis report from recent sessions")
    audit_parser.add_argument("-n", type=int, default=5, help="Number of recent sessions to audit")

    recall_parser = subparsers.add_parser("recall", help="Bypass Engram DB and directly recall synthesis from session history")
    recall_parser.add_argument("query", nargs="+", help="The recall query")

    subparsers.add_parser("mail", help="Sync the Unread Mail tracker from the Swarm Post Office")

    subparsers.add_parser("sessions", help="List recent noise-reduced historical sessions")
    search_sessions_parser = subparsers.add_parser("search-sessions", help="Search the full session history database")
    search_sessions_parser.add_argument("query", nargs="+", help="The search query")

    bug_parser = subparsers.add_parser("bug", help="Report a bug and create a GitHub Issue (Agent strict mode)")
    bug_parser.add_argument("title", help="Description of the bug")
    bug_parser.add_argument("--context", help="The Context (What were you trying to do?)", default="")
    bug_parser.add_argument("--failure", help="The Failure/Goal (What went wrong / What needs to be built?)", default="")
    bug_parser.add_argument("--intent", help="Action Items (What are the precise steps to fix this?)", default="")

    bug_operator_parser = subparsers.add_parser("bug-operator", help="Report a bug and create a GitHub Issue (Interactive mode)")
    bug_operator_parser.add_argument("title", help="Description of the bug")
    bug_operator_parser.add_argument("--context", help="The Context (What were you trying to do?)", default="")
    bug_operator_parser.add_argument("--failure", help="The Failure/Goal (What went wrong / What needs to be built?)", default="")
    bug_operator_parser.add_argument("--intent", help="Action Items (What are the precise steps to fix this?)", default="")
    
    fix_parser = subparsers.add_parser("fix", help="Checkout a branch to fix a specific GitHub Issue")
    fix_parser.add_argument("id", help="The GitHub Issue ID")

    # --- GitHub Projects (kanban) GitOps ---
    projects_parser = subparsers.add_parser(
        "projects",
        aliases=["project"],
        help="GitHub Projects kanban GitOps (board / in-progress / done / …)",
    )
    projects_parser.add_argument("--owner", dest="projects_owner", default=None, help="Project owner (@me or login)")
    projects_parser.add_argument("--number", dest="projects_number", type=int, default=None, help="Project number")
    projects_parser.add_argument(
        "--status-field",
        dest="projects_status_field",
        default=None,
        help="Status single-select field name (default: Status)",
    )
    projects_parser.add_argument(
        "--repo",
        dest="projects_repo",
        default=None,
        help="nameWithOwner for auto-adding issues (e.g. BrianV1981/aim-ld)",
    )
    projects_sub = projects_parser.add_subparsers(dest="projects_command")

    p_board = projects_sub.add_parser("board", help="Kanban snapshot grouped by Status")
    p_board.add_argument("--status", dest="board_status", default=None, help='Filter e.g. "In Progress"')
    p_board.add_argument("-L", "--limit", dest="board_limit", type=int, default=100)
    p_board.add_argument("--json", dest="board_json", action="store_true")

    projects_sub.add_parser("list", help="List projects for owner")
    projects_sub.add_parser("fields", help="List fields / Status options")
    projects_sub.add_parser("doctor", help="Validate gh project scopes + config")

    for _name in ("in-progress", "done", "ready", "todo", "blocked"):
        _p = projects_sub.add_parser(_name, help=f"Set issue Status ({_name})")
        _p.add_argument("issue", type=int, help="GitHub issue number")

    p_set = projects_sub.add_parser("set", help="Set issue Status to a name/alias")
    p_set.add_argument("issue", type=int)
    p_set.add_argument("set_status", help='Status e.g. "In Progress" or done')

    p_view = projects_sub.add_parser("view", help="Show board row + issue detail")
    p_view.add_argument("issue", type=int)

    subparsers.add_parser("promote", help="Automate the Phase Protocol: Archive main, merge current dev branch, and cleanup")

    merge_batch_parser = subparsers.add_parser("merge-batch", help="Automate the Phase Protocol: Merge all open fix branches into main")
    merge_batch_parser.add_argument("--push", action="store_true", help="Automatically push unified main to origin")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query", nargs="+")
    search_parser.add_argument("--top-k", type=int)
    search_parser.add_argument("--full", action="store_true")
    search_parser.add_argument("--session", type=str)
    search_parser.add_argument("--json", action="store_true")

    push_parser = subparsers.add_parser("push")
    push_parser.add_argument("message")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.command == "init": cmd_init(args)
    elif args.command == "status": cmd_status(args)
    elif args.command == "core-memory": cmd_core_memory(args)
    elif args.command == "search": cmd_search(args)
    elif args.command == "map": cmd_map(args)
    elif args.command == "update": cmd_update(args)
    elif args.command in ["config", "tui"]: cmd_config(args)
    elif args.command == "index": cmd_index(args)
    elif args.command == "scrape": cmd_scrape(args)
    elif args.command in ["handoff", "pulse"]: cmd_handoff(args)
    elif args.command == "push": cmd_push(args)
    elif args.command == "sync": cmd_sync(args)
    elif args.command == "sync-issues": cmd_sync_issues(args)

    elif args.command == "handoff-vnext": cmd_handoff_vnext(args)

    elif args.command == "vault": cmd_vault(args)
    elif args.command == "clean": cmd_clean(args)
    elif args.command == "bake": cmd_bake(args)
    elif args.command == "exchange": cmd_exchange(args)
    elif args.command == "export": cmd_export(args)
    elif args.command == "import": cmd_import(args)
    elif args.command == "jack-in": cmd_jack_in(args)
    elif args.command == "unplug": cmd_unplug(args)

    elif args.command == "agy-blackbox": cmd_agy_blackbox(args)
    elif args.command == "grok-blackbox": cmd_grok_blackbox(args)
    elif args.command == "codex-blackbox": cmd_codex_blackbox(args)
    elif args.command == "opencode-blackbox": cmd_opencode_blackbox(args)

    elif args.command == "audit": cmd_audit(args)
    elif args.command == "recall": cmd_recall(args)
    elif args.command == "mail": cmd_mail(args)
    elif args.command == "sessions": cmd_sessions(args)
    elif args.command == "search-sessions": cmd_search_sessions(args)
    elif args.command == "doctor": cmd_doctor(args)
    elif args.command == "health": cmd_health(args)
    elif args.command == "bug": cmd_bug(args)
    elif args.command == "bug-operator": cmd_bug_operator(args)
    elif args.command in ("projects", "project"): cmd_projects(args)
    elif args.command == "fix": cmd_fix(args)
    elif args.command == "promote": cmd_promote(args)
    elif args.command == "merge-batch": cmd_merge_batch(args)
    elif args.command == "purge": cmd_purge(args)
    elif args.command == "prune-remote": cmd_prune_remote(args)
    elif args.command == "uninstall": cmd_uninstall(args)
    else: parser.print_help()

if __name__ == "__main__":
    main()
