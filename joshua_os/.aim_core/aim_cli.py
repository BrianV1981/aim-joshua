#!/usr/bin/env python3
import argparse
from datetime import datetime
import io
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
import urllib.parse
import urllib.request
import zipfile

# --- VENV BOOTSTRAP ---
os.environ.setdefault("NODE_OPTIONS", "--max-old-space-size=8192")
current_dir = os.path.dirname(os.path.abspath(__file__))
aim_root = os.path.dirname(current_dir)
venv_python = (
    os.path.join(aim_root, "venv", "Scripts", "python.exe")
    if os.name == "nt"
    else os.path.join(aim_root, "venv", "bin", "python3")
)

if (
    __name__ == "__main__"
    and os.path.exists(venv_python)
    and os.path.abspath(sys.executable) != os.path.abspath(venv_python)
):
    if os.name == "nt":
        sys.exit(subprocess.call([venv_python] + sys.argv))
    else:
        os.execv(venv_python, [venv_python] + sys.argv)

# --- CONFIG BOOTSTRAP ---
src_dir = os.path.join(aim_root, ".aim_core")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from config_utils import CONFIG, OS_ROOT, PROJECT_ROOT, resolve_venv_python

BASE_DIR = PROJECT_ROOT
OS_DIR = OS_ROOT
CLI_NAME = os.path.basename(BASE_DIR)
VENV_PYTHON = resolve_venv_python(OS_DIR)
AIM_CORE_DIR = os.path.join(OS_DIR, ".aim_core")


def run_script(script_path, args):
    """Executes an A.I.M. Python script with the engine virtual environment."""
    cmd = [VENV_PYTHON, script_path] + args
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Command '{' '.join(cmd)}' failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)


def cmd_core_memory(args):
    """Opens the CORE_MEMORY.md file in the user's default editor."""
    core_mem_file = os.path.join(OS_DIR, "continuity", "CORE_MEMORY.md")
    if not os.path.exists(core_mem_file):
        os.makedirs(os.path.join(OS_DIR, "continuity"), exist_ok=True)
        with open(core_mem_file, "w", encoding="utf-8") as f:
            f.write(
                "# A.I.M. Core Memory (RAM)\n\n"
                "*This file acts as the Agent's writable scratchpad across context windows.*\n\n"
                "- [Empty]\n"
            )

    editor = os.environ.get("EDITOR", "notepad" if os.name == "nt" else "nano")
    rc = subprocess.call([editor, core_mem_file])
    if rc != 0:
        sys.exit(rc)


def cmd_status(args):
    """Displays the current A.I.M. operational pulse."""
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
        sys.exit(1)


def cmd_search(args):
    """Dispatches to retriever.py."""
    query = " ".join(args.query)
    retriever_args = [query]
    if args.top_k:
        retriever_args += ["--top-k", str(args.top_k)]
    if args.full:
        retriever_args += ["--full"]
    if args.session:
        retriever_args += ["--session", args.session]
    if getattr(args, "json", False):
        retriever_args += ["--json"]
    run_script(os.path.join(AIM_CORE_DIR, "retriever.py"), retriever_args)


def cmd_map(args):
    """Prints the surgical Index of Keys."""
    run_script(os.path.join(AIM_CORE_DIR, "retriever.py"), ["--map"])


def cmd_index(args):
    """Dispatches to bootstrap_brain.py."""
    cmd_args = []
    if getattr(args, "dir", None):
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

    fwd = []
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

    projects_main(fwd)


def _format_issue_body(title: str, context: str, failure: str, intent: str) -> str:
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
    return body


def cmd_bug(args):
    """Creates a structured GitHub Issue using the gh CLI (strict agent-driven mode)."""
    print("--- A.I.M. ISSUE TRACKER ---")
    title = args.title

    context = getattr(args, "context", "").strip()
    failure = getattr(args, "failure", "").strip()
    intent = getattr(args, "intent", "").strip()

    if not (context or failure or intent):
        print("\n[MANDATE VIOLATION] Commander's Intent Required.", file=sys.stderr)
        print(
            "You MUST pass explicit context flags (--context, --failure, --intent) when calling 'aim bug'.",
            file=sys.stderr,
        )
        sys.exit(1)

    body = _format_issue_body(title, context, failure, intent)
    try:
        print("\n[1/1] Dispatching to GitHub CLI...")
        label = "enhancement" if "feature" in title.lower() or "epic" in title.lower() else "bug"
        subprocess.run(["gh", "issue", "create", "--title", title, "--body", body, "--label", label], check=True)
        print(f"[SUCCESS] {label.capitalize()} ticket created. Run '{CLI_NAME} fix <id>' to branch out.")
    except FileNotFoundError:
        print(f"[ERROR] GitHub CLI ('gh') is not installed. Install 'gh' to use '{CLI_NAME} bug'.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to create issue: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_bug_operator(args):
    """Creates a structured GitHub Issue using the gh CLI with interactive prompts for operators."""
    print("--- A.I.M. ISSUE TRACKER (Operator Mode) ---")
    title = args.title

    context = getattr(args, "context", "").strip()
    failure = getattr(args, "failure", "").strip()
    intent = getattr(args, "intent", "").strip()

    if not (context or failure or intent):
        print("\n[MANDATE] Commander's Intent Required.")
        try:
            context = input("\n1. The Context (What were you trying to do? Reference files/architecture): ").strip()
            failure = input("\n2. The Failure/Goal (Exact error strings or capability required): ").strip()
            intent = input("\n3. Action Items (Step-by-step implementation plan): ").strip()
        except EOFError:
            print("[ERROR] Interactive input unavailable; pass --context, --failure, and --intent.", file=sys.stderr)
            sys.exit(1)

    if not (context or failure or intent):
        print("[ERROR] At least one of --context, --failure, or --intent is required.", file=sys.stderr)
        sys.exit(1)

    body = _format_issue_body(title, context, failure, intent)
    try:
        print("\n[1/1] Dispatching to GitHub CLI...")
        label = "enhancement" if "feature" in title.lower() or "epic" in title.lower() else "bug"
        subprocess.run(["gh", "issue", "create", "--title", title, "--body", body, "--label", label], check=True)
        print(f"[SUCCESS] {label.capitalize()} ticket created. Run '{CLI_NAME} fix <id>' to branch out.")
    except FileNotFoundError:
        print(f"[ERROR] GitHub CLI ('gh') is not installed. Install 'gh' to use '{CLI_NAME} bug-operator'.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to create issue: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_fix(args):
    """Spawns a Git Worktree for a specific Issue or task ID."""
    issue_id = args.id
    branch_name = f"fix/issue-{issue_id}"
    worktree_path = os.path.join(PROJECT_ROOT, "workspace", f"issue-{issue_id}")
    print(f"--- A.I.M. FACTORY FLOOR (Issue #{issue_id}) ---")
    head_chk = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
    )
    if head_chk.returncode != 0:
        print(
            f"[ERROR] Repository at '{BASE_DIR}' has no commits yet (unborn HEAD).\n"
            f"Create an initial commit first (e.g., 'git add README.md .gitignore && git commit -m \"Initial commit\"') "
            f"before running '{CLI_NAME} fix {issue_id}'.",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        subprocess.run(["git", "worktree", "add", worktree_path, "-b", branch_name], cwd=BASE_DIR, check=True)

        # Copy gitignored local CONFIG.json into the worktree (nested joshua_os/.aim_core + flat .aim_core fallback)
        nested_src = os.path.join(PROJECT_ROOT, "joshua_os", ".aim_core", "CONFIG.json")
        flat_src = os.path.join(PROJECT_ROOT, ".aim_core", "CONFIG.json")
        if os.path.isfile(nested_src):
            dest_dir = os.path.join(worktree_path, "joshua_os", ".aim_core")
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(nested_src, os.path.join(dest_dir, "CONFIG.json"))
        if os.path.isfile(flat_src):
            dest_dir = os.path.join(worktree_path, ".aim_core")
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(flat_src, os.path.join(dest_dir, "CONFIG.json"))

        print(f"[SUCCESS] Worktree created at {worktree_path} on branch {branch_name}")
        print(f"[ACTION] To start working, run: cd workspace/issue-{issue_id}")
        print(f"[ACTION] When ready to merge, commit all worktree changes and run: {CLI_NAME} promote")
    except Exception as e:
        print(f"[ERROR] Failed to create worktree: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_prune_remote(args):
    """Prunes remote tracking branches like archive-fix/* and fix/issue-* that have no open PRs."""
    print("--- A.I.M. REMOTE BRANCH PRUNE ---")
    try:
        result = subprocess.run(["git", "branch", "-r"], cwd=BASE_DIR, capture_output=True, text=True, check=True)
        branches = [b.strip() for b in result.stdout.split("\n") if b.strip()]

        open_prs = set()
        pr_result = subprocess.run(
            ["gh", "pr", "list", "--state", "open", "--json", "headRefName"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )
        if pr_result.returncode == 0:
            try:
                pr_data = json.loads(pr_result.stdout)
                open_prs = {pr["headRefName"] for pr in pr_data}
            except Exception:
                pass
        else:
            if getattr(args, "confirm", False):
                print("[ERROR] Could not fetch open PRs from GitHub. Aborting unsafe remote prune.", file=sys.stderr)
                sys.exit(1)
            else:
                print("[WARNING] Could not fetch open PRs from GitHub. Proceeding with dry-run listing.")

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

        if not getattr(args, "confirm", False):
            print("\n[DRY RUN] Run with --confirm to delete these branches from origin.")
            return

        print("\n[ACTION] Deleting branches from origin...")
        failed = 0
        for branch in to_delete:
            try:
                subprocess.run(
                    ["git", "push", "origin", "--delete", branch],
                    cwd=BASE_DIR,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                print(f"  [DELETED] {branch}")
            except subprocess.CalledProcessError as e:
                failed += 1
                print(f"  [ERROR] Failed to delete {branch}: {e.stderr.strip()}", file=sys.stderr)

        if failed:
            sys.exit(1)
        print("\n[SUCCESS] Remote cleanup complete.")
    except SystemExit:
        raise
    except Exception as e:
        print(f"\n[ERROR] Failed to prune remote branches: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_promote(args):
    """Safely archives default branch, merges current dev worktree branch, and cleans up the worktree."""
    print("--- A.I.M. PHASE PROMOTION ---")
    try:
        current_dir = os.getcwd()
        in_worktree = "workspace/issue-" in current_dir.replace("\\", "/")

        common_dir = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=current_dir,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        repo_root = os.path.dirname(os.path.abspath(os.path.join(current_dir, common_dir)))

        if not os.path.isdir(os.path.join(repo_root, ".git")):
            print(
                f"[ERROR] Computed repo_root '{repo_root}' does not contain a .git directory. Aborting promote.",
                file=sys.stderr,
            )
            sys.exit(1)

        branches = subprocess.run(
            ["git", "branch", "--list"], cwd=repo_root, capture_output=True, text=True, check=True
        ).stdout
        default_branch = "master" if "master" in branches and "main" not in branches else "main"

        result = subprocess.run(
            ["git", "branch", "--show-current"], cwd=current_dir, capture_output=True, text=True, check=True
        )
        current_branch = result.stdout.strip()

        if not current_branch or current_branch == default_branch:
            print(
                f"[ERROR] You are on '{current_branch or 'DETACHED HEAD'}'. Run '{CLI_NAME} promote' from a feature/fix worktree branch.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Safety Gate 1: Refuse to promote or --force-remove a dirty worktree (#135)
        wt_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=current_dir,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if wt_status:
            print(
                f"[ERROR] Worktree '{current_dir}' has uncommitted or untracked changes:\n{wt_status}\n"
                "Commit, stash, or clean all worktree files before running promote.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Safety Gate 2: Refuse if root repository has staged or modified tracked files (untracked scaffold/user files allowed)
        root_status_raw = subprocess.run(
            ["git", "status", "--porcelain", "-uno"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        root_dirty = [ln for ln in root_status_raw.splitlines() if ln.strip()]
        if root_dirty:
            print(
                f"[ERROR] Root repository '{repo_root}' has uncommitted changes:\n"
                + "\n".join(root_dirty)
                + "\nClean or stash root repository changes before running promote.",
                file=sys.stderr,
            )
            sys.exit(1)

        print(f"[1/5] Preparing to promote '{current_branch}' to {default_branch}...")

        if not getattr(args, "yes", False):
            print("\n[CRITICAL INTERVENTION REQUIRED]")
            try:
                confirm = input(f"\nMerge branch '{current_branch}' to {default_branch}? (yes/no): ").strip().lower()
            except EOFError:
                print("[ERROR] Non-interactive promote requires --yes (-y) or 'yes' on stdin.", file=sys.stderr)
                sys.exit(1)
            if confirm not in ("yes", "y"):
                print("\n[ABORTED] Promotion cancelled. Branch remains isolated.")
                return

        has_origin = (
            subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=repo_root,
                capture_output=True,
                text=True,
            ).returncode
            == 0
        )

        date_str = datetime.now().strftime("%Y%m%d-%H%M")
        archive_branch = f"archive-{current_branch}-{date_str}"

        if has_origin:
            subprocess.run(["git", "fetch", "origin"], cwd=repo_root, check=True, capture_output=True, text=True)
            subprocess.run(["git", "checkout", default_branch], cwd=repo_root, check=True, capture_output=True, text=True)
            remote_ref = f"origin/{default_branch}"
            if (
                subprocess.run(
                    ["git", "rev-parse", "--verify", remote_ref],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                ).returncode
                == 0
            ):
                subprocess.run(
                    ["git", "merge", "--ff-only", remote_ref],
                    cwd=repo_root,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            print(f"[2/5] Backing up current '{default_branch}' to '{archive_branch}'...")
            subprocess.run(
                ["git", "checkout", "-b", archive_branch], cwd=repo_root, check=True, capture_output=True, text=True
            )
            subprocess.run(
                ["git", "push", "-u", "origin", archive_branch],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            )

            print(f"[3/5] Merging '{current_branch}' into {default_branch}...")
            subprocess.run(["git", "checkout", default_branch], cwd=repo_root, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "merge", current_branch, "--no-edit"], cwd=repo_root, check=True, capture_output=True, text=True
            )

            print("[4/5] Deploying new baseline to origin...")
            subprocess.run(
                ["git", "push", "origin", default_branch], cwd=repo_root, check=True, capture_output=True, text=True
            )
        else:
            print(f"[2/5] Local-only repository (no 'origin' remote): backing up '{default_branch}' to '{archive_branch}'...")
            subprocess.run(["git", "checkout", default_branch], cwd=repo_root, check=True, capture_output=True, text=True)
            subprocess.run(["git", "branch", archive_branch], cwd=repo_root, check=True, capture_output=True, text=True)

            print(f"[3/5] Merging '{current_branch}' into {default_branch}...")
            subprocess.run(
                ["git", "merge", current_branch, "--no-edit"], cwd=repo_root, check=True, capture_output=True, text=True
            )
            print("[4/5] Skipping remote push (no 'origin' remote configured).")

        print("[5/5] Cleaning up local worktree...")
        if in_worktree:
            os.chdir(repo_root)
            # Safe because wt_status verified 0 modified/untracked files; --force only clears gitignored CONFIG.json/__pycache__
            rm_res = subprocess.run(
                ["git", "worktree", "remove", current_dir, "--force"],
                cwd=repo_root,
                capture_output=True,
                text=True,
            )
            if rm_res.returncode != 0:
                if os.name == "nt":
                    # On Windows, a parent shell (cmd/pwsh) invoked from inside current_dir holds an open handle
                    # preventing final rmdir; clean contents and prune git worktree metadata cleanly.
                    shutil.rmtree(current_dir, ignore_errors=True)
                    wt_admin = os.path.join(repo_root, ".git", "worktrees", os.path.basename(current_dir))
                    if os.path.isdir(wt_admin):
                        shutil.rmtree(wt_admin, ignore_errors=True)
                    subprocess.run(
                        ["git", "worktree", "prune"],
                        cwd=repo_root,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                else:
                    raise subprocess.CalledProcessError(
                        rm_res.returncode, rm_res.args, output=rm_res.stdout, stderr=rm_res.stderr
                    )
        subprocess.run(["git", "branch", "-D", current_branch], cwd=repo_root, check=True, capture_output=True, text=True)

        print(f"\n[SUCCESS] Promotion complete. You are now on a clean '{default_branch}' branch in the root repository.")
    except SystemExit:
        raise
    except subprocess.CalledProcessError as e:
        print("\n[ERROR] Git operation failed. Promotion aborted.", file=sys.stderr)
        print(f"Command: {e.cmd}", file=sys.stderr)
        if e.stdout:
            print(f"Output: {e.stdout}", file=sys.stderr)
        if e.stderr:
            print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        traceback.print_exc()
        print(f"\n[ERROR] Failed to promote: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_merge_batch(args):
    """Executes aim_batch_merge.py to merge open fix/issue-* branches."""
    if not getattr(args, "yes", False):
        print("\n[CRITICAL INTERVENTION REQUIRED]")
        try:
            confirm = input("\nExecute batch merge to main? (yes/no): ").strip().lower()
        except EOFError:
            print("[ERROR] Non-interactive merge-batch requires --yes (-y).", file=sys.stderr)
            sys.exit(1)
        if confirm not in ("yes", "y"):
            print("\n[ABORTED] Batch merge cancelled. Main remains isolated.")
            return

    merge_args = []
    if args.push:
        merge_args.append("--push")
    run_script(os.path.join(AIM_CORE_DIR, "aim_batch_merge.py"), merge_args)


def is_upstream_engine_repo(project_root):
    """Returns True if project_root is the upstream aim-joshua engine repository itself."""
    if os.path.basename(os.path.abspath(project_root)) == "aim-joshua":
        return True
    try:
        res = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if res.returncode == 0 and "aim-joshua" in res.stdout.strip():
            return True
    except Exception:
        pass
    return False


def git_push_changes(msg, cwd=None, include_untracked=False):
    """Cross-platform pure-Python Git commit & push helper with untracked file detection."""
    work_dir = cwd or os.getcwd()
    version_str = "v1.0.0"
    version_path = os.path.join(work_dir, "VERSION")
    if not os.path.isfile(version_path):
        version_path = os.path.join(BASE_DIR, "VERSION")
    if os.path.isfile(version_path):
        with open(version_path, "r", encoding="utf-8") as vf:
            version_str = vf.read().strip() or "v1.0.0"

    for rel_file in ("VERSION", "CHANGELOG.md"):
        if os.path.isfile(os.path.join(work_dir, rel_file)):
            subprocess.run(["git", "add", rel_file], cwd=work_dir, check=False, capture_output=True)
    if is_upstream_engine_repo(work_dir) and os.path.isfile(os.path.join(work_dir, "joshua_os", "VERSION")):
        subprocess.run(
            ["git", "add", os.path.join("joshua_os", "VERSION")],
            cwd=work_dir,
            check=False,
            capture_output=True,
        )

    if include_untracked:
        subprocess.run(["git", "add", "-A"], cwd=work_dir, check=True)
    else:
        subprocess.run(["git", "add", "-u"], cwd=work_dir, check=True)
        untracked_res = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        untracked = [line.strip() for line in (untracked_res.stdout or "").splitlines() if line.strip()]
        if untracked:
            print(
                f"[NOTICE] Untracked files not staged (use 'git add <file>' or '{CLI_NAME} push --include-untracked'): "
                + ", ".join(untracked),
                file=sys.stderr,
            )

    subprocess.run(["git", "commit", "-m", msg, "-m", f"Version: {version_str}"], cwd=work_dir, check=True)
    branch_res = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=work_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    current_branch = branch_res.stdout.strip()
    subprocess.run(["git", "push", "origin", current_branch], cwd=work_dir, check=True)
    print(f"Successfully pushed A.I.M. version: {version_str}")


def cmd_push(args):
    """Pure-Python Semantic Release and Git push pipeline."""
    msg = args.message

    print("--- A.I.M. SEMANTIC RELEASE ---")
    version_file = os.path.join(BASE_DIR, "VERSION")
    changelog_file = os.path.join(BASE_DIR, "CHANGELOG.md")

    try:
        current_version = "v1.0.0"
        if os.path.exists(version_file):
            with open(version_file, "r", encoding="utf-8") as f:
                current_version = f.read().strip()

        if len(current_version.split(".")) != 3 or "202" in current_version:
            current_version = "v1.0.0"

        major, minor, patch = map(int, current_version.lstrip("v").split("."))

        bump_type = "none"
        if msg.startswith("BREAKING CHANGE:"):
            bump_type = "major"
        elif msg.startswith("Feature:") or msg.startswith("feat:"):
            bump_type = "minor"
        elif msg.startswith("Fix:") or msg.startswith("fix:"):
            bump_type = "patch"

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1

        new_version = f"v{major}.{minor}.{patch}"

        if bump_type != "none":
            print(f"[1/2] Bumping version: {current_version} -> {new_version}")
            with open(version_file, "w", encoding="utf-8") as f:
                f.write(f"{new_version}\n")
            os_version_file = os.path.join(OS_DIR, "VERSION")
            if os.path.isdir(OS_DIR):
                with open(os_version_file, "w", encoding="utf-8") as of:
                    of.write(f"{new_version}\n")

            date_str = datetime.now().strftime("%Y-%m-%d")
            log_entry = f"## [{new_version}] - {date_str}\n- {msg}\n\n"

            if not os.path.exists(changelog_file):
                with open(changelog_file, "w", encoding="utf-8") as f:
                    f.write(f"# Changelog\n\n{log_entry}")
            else:
                with open(changelog_file, "r", encoding="utf-8") as f:
                    content = f.read()
                content = content.replace("# Changelog\n", f"# Changelog\n\n{log_entry}", 1)
                with open(changelog_file, "w", encoding="utf-8") as f:
                    f.write(content)
        else:
            print(f"[1/2] No semantic prefix found (Feature/Fix/BREAKING CHANGE). Version remains {new_version}.")
    except Exception as e:
        traceback.print_exc()
        print(f"[WARNING] Semantic Release version bump skipped: {e}", file=sys.stderr)

    print("[2/2] Deploying to GitHub...")
    try:
        git_push_changes(msg, include_untracked=getattr(args, "include_untracked", False))
    except subprocess.CalledProcessError as e:
        print(f"Error: Git push failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)


def cmd_delegate(args):
    """Dispatches to aim_delegate.py to spawn parallel sub-agents."""
    delegate_args = [args.instruction, "--files"] + args.files
    run_script(os.path.join(AIM_CORE_DIR, "aim_delegate.py"), delegate_args)


def cmd_handoff(args):
    """Dispatches to handoff_pulse_generator.py to generate a session flight record pulse."""
    pulse_args = []
    if getattr(args, "session_id", None):
        pulse_args += ["--session-id", args.session_id]
    run_script(os.path.join(AIM_CORE_DIR, "handoff_pulse_generator.py"), pulse_args)


def cmd_init(args):
    """Dispatches to aim_init.py (New User Setup)."""
    init_args = []
    if args.reinstall:
        init_args.append("--reinstall")
    if args.uninstall:
        init_args.append("--uninstall")
    if args.light:
        init_args.append("--light")
    if getattr(args, "headless", False):
        init_args.append("--headless")
    if getattr(args, "persona", None):
        init_args.extend(["--persona", args.persona])
    if getattr(args, "clean", False):
        init_args.append("--clean")
    try:
        subprocess.run([VENV_PYTHON, os.path.join(AIM_CORE_DIR, "aim_init.py")] + init_args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 'aim init' failed: {e}", file=sys.stderr)
        sys.exit(e.returncode or 1)


def cmd_config(args):
    """Dispatches to aim_config.py (TUI Cockpit)."""
    try:
        subprocess.run([VENV_PYTHON, os.path.join(AIM_CORE_DIR, "aim_config.py")], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 'aim config' failed: {e}", file=sys.stderr)
        sys.exit(e.returncode or 1)


from cli_vault import (
    cmd_agy_blackbox,
    cmd_codex_blackbox,
    cmd_grok_blackbox,
    cmd_handoff_vnext,
    cmd_opencode_blackbox,
    cmd_vault,
)
from cli_memory import (
    cmd_audit,
    cmd_bake,
    cmd_clean,
    cmd_exchange,
    cmd_jack_in,
    cmd_purge,
    cmd_recall,
    cmd_search_sessions,
    cmd_sessions,
    cmd_uninstall,
    cmd_unplug,
)


def ensure_consumer_gitignore(project_root):
    """Ensures consumer projects ignore joshua_os/, aim, aim.ps1, aim.cmd, workspace/, and archive/."""
    if is_upstream_engine_repo(project_root):
        return False
    gitignore_path = os.path.join(project_root, ".gitignore")
    existing_lines = []
    if os.path.isfile(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
            existing_lines = f.read().splitlines()

    normalized = {line.strip() for line in existing_lines if line.strip() and not line.strip().startswith("#")}
    required = [
        ("joshua_os/", {"joshua_os", "joshua_os/", "joshua_os/*", "/joshua_os", "/joshua_os/"}),
        ("aim", {"aim", "/aim", "./aim"}),
        ("aim.ps1", {"aim.ps1", "/aim.ps1", "./aim.ps1"}),
        ("aim.cmd", {"aim.cmd", "/aim.cmd", "./aim.cmd"}),
        ("workspace/", {"workspace", "workspace/", "workspace/*", "/workspace", "/workspace/"}),
        ("archive/", {"archive", "archive/", "archive/*", "/archive", "/archive/"}),
    ]
    missing = [canonical for canonical, aliases in required if not (normalized & aliases)]
    if not missing:
        return False

    with open(gitignore_path, "a", encoding="utf-8") as f:
        if existing_lines and existing_lines[-1].strip() != "":
            f.write("\n")
        f.write("# --- J.O.S.H.U.A. OS Exoskeleton ---\n")
        for item in missing:
            f.write(f"{item}\n")
    return True


def safe_extract_zip(zf: zipfile.ZipFile, dest_dir: str) -> None:
    """Validate every ZipInfo entry against Zip-Slip path traversal and symlinks before extraction."""
    real_dest = os.path.realpath(dest_dir)
    for info in zf.infolist():
        member_name = info.filename
        if not member_name:
            continue
        norm_parts = member_name.replace("\\", "/").split("/")
        if (
            member_name.startswith(("/", "\\"))
            or re.match(r"^[A-Za-z]:", member_name)
            or ".." in norm_parts
        ):
            raise ValueError(f"Unsafe zip member path rejected: {member_name!r}")
        mode = (info.external_attr >> 16) & 0o170000
        if mode == 0o120000:
            raise ValueError(f"Unsafe zip symlink entry rejected: {member_name!r}")
        target_path = os.path.realpath(os.path.join(real_dest, *norm_parts))
        if os.path.commonpath([real_dest, target_path]) != real_dest:
            raise ValueError(f"Zip-Slip path traversal rejected: {member_name!r}")

    for info in zf.infolist():
        if not info.filename:
            continue
        zf.extract(info, path=real_dest)


def _resolve_remote_update_zip_url(explicit_ref: str | None = None) -> tuple[str, str]:
    """Return (zip_url, resolved_ref_label) preferring the latest GitHub release tag unless --ref is given."""
    if explicit_ref:
        clean_ref = explicit_ref.strip()
        quoted = urllib.parse.quote(clean_ref, safe="")
        return f"https://github.com/BrianV1981/aim-joshua/archive/{quoted}.zip", clean_ref

    try:
        api_req = urllib.request.Request(
            "https://api.github.com/repos/BrianV1981/aim-joshua/releases/latest",
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "aim-joshua-updater",
            },
        )
        with urllib.request.urlopen(api_req, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            tag_name = (payload.get("tag_name") or "").strip()
            if tag_name:
                quoted_tag = urllib.parse.quote(tag_name, safe="")
                return (
                    f"https://github.com/BrianV1981/aim-joshua/archive/refs/tags/{quoted_tag}.zip",
                    tag_name,
                )
    except Exception:
        pass

    return "https://github.com/BrianV1981/aim-joshua/archive/refs/heads/main.zip", "main"


def cmd_update(args):
    """Safely updates the local J.O.S.H.U.A. engine while preserving tenant state and CONFIG.json."""
    print("--- A.I.M. SOVEREIGN ENGINE UPDATE ---")
    source_arg = getattr(args, "source", None)
    explicit_ref = getattr(args, "ref", None)
    skip_deps = getattr(args, "skip_deps", False)
    temp_dir = None

    if source_arg:
        source_root = os.path.abspath(source_arg)
        candidate_os = (
            os.path.join(source_root, "joshua_os")
            if os.path.isdir(os.path.join(source_root, "joshua_os"))
            else source_root
        )
        if not os.path.isdir(os.path.join(candidate_os, ".aim_core")):
            print(f"[ERROR] Invalid local update source '{source_arg}': missing .aim_core directory.", file=sys.stderr)
            sys.exit(1)
        source_os_dir = candidate_os
        print(f"[*] Using local engine source: {source_os_dir}")
    else:
        zip_url, ref_label = _resolve_remote_update_zip_url(explicit_ref)
        print(f"[*] Fetching upstream J.O.S.H.U.A. release ({ref_label})...")
        temp_dir = os.path.join(OS_DIR, ".aim_temp_update")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        try:
            req = urllib.request.Request(zip_url, headers={"User-Agent": "aim-joshua-updater"})
            with urllib.request.urlopen(req, timeout=30) as response:
                with zipfile.ZipFile(io.BytesIO(response.read())) as z:
                    safe_extract_zip(z, temp_dir)
            print(f"    [SUCCESS] Remote payload ({ref_label}) verified and extracted.")
        except Exception as e:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"[ERROR] Engine update failed: {e}", file=sys.stderr)
            sys.exit(1)

        extracted_dirs = [
            os.path.join(temp_dir, d)
            for d in os.listdir(temp_dir)
            if os.path.isdir(os.path.join(temp_dir, d))
        ]
        extracted_root = (
            extracted_dirs[0] if len(extracted_dirs) == 1 else os.path.join(temp_dir, "aim-joshua-main")
        )
        source_os_dir = os.path.join(extracted_root, "joshua_os")
        if not os.path.isdir(os.path.join(source_os_dir, ".aim_core")):
            shutil.rmtree(temp_dir, ignore_errors=True)
            print("[ERROR] Downloaded archive does not contain a valid joshua_os/.aim_core directory.", file=sys.stderr)
            sys.exit(1)

    local_core = os.path.join(OS_DIR, ".aim_core")
    config_path = os.path.join(local_core, "CONFIG.json")
    preserved_config = None
    if os.path.isfile(config_path):
        with open(config_path, "rb") as cf:
            preserved_config = cf.read()

    print("[*] Hot-swapping local execution engine...")
    for subdir in (".aim_core", "joshua_os_docs", "handoff", "scripts", "hooks", "foundry"):
        src_sub = os.path.join(source_os_dir, subdir)
        dst_sub = os.path.join(OS_DIR, subdir)
        if os.path.isdir(src_sub):
            if os.path.exists(dst_sub):
                shutil.rmtree(dst_sub)
            shutil.copytree(src_sub, dst_sub)

    src_default_lance = os.path.join(source_os_dir, "assets", "default_lance")
    dst_default_lance = os.path.join(OS_DIR, "assets", "default_lance")
    if os.path.isdir(src_default_lance):
        os.makedirs(os.path.dirname(dst_default_lance), exist_ok=True)
        if os.path.exists(dst_default_lance):
            shutil.rmtree(dst_default_lance)
        shutil.copytree(src_default_lance, dst_default_lance)

    if preserved_config is not None:
        os.makedirs(local_core, exist_ok=True)
        with open(config_path, "wb") as cf:
            cf.write(preserved_config)

    for fname in (
        "setup.sh",
        "requirements.txt",
        "link_cli_alias.sh",
        "BOOTSTRAP.md",
        "VERSION",
        "install.sh",
        "install-clean.sh",
        "install-agent.sh",
        "install-core.sh",
        "install.ps1",
        "install-agent.ps1",
        "install-core.ps1",
    ):
        src_file = os.path.join(source_os_dir, fname)
        if os.path.isfile(src_file):
            shutil.copy2(src_file, os.path.join(OS_DIR, fname))

    source_parent = os.path.dirname(source_os_dir)
    root_version_src = os.path.join(source_parent, "VERSION")
    if os.path.isfile(root_version_src):
        shutil.copy2(root_version_src, os.path.join(OS_DIR, "VERSION"))
    for wrapper_name in ("aim", "aim.ps1", "aim.cmd"):
        src_wrapper = os.path.join(source_parent, wrapper_name)
        dst_wrapper = os.path.join(BASE_DIR, wrapper_name)
        if os.path.isfile(src_wrapper) and os.path.abspath(src_wrapper) != os.path.abspath(dst_wrapper):
            tmp_wrapper = dst_wrapper + ".tmp"
            shutil.copy2(src_wrapper, tmp_wrapper)
            if wrapper_name == "aim" and os.name != "nt":
                os.chmod(tmp_wrapper, 0o755)
            os.replace(tmp_wrapper, dst_wrapper)

    ensure_consumer_gitignore(BASE_DIR)

    # Prune retired legacy artifacts on consumer upgrade
    for stale_rel in (
        os.path.join("memory-wiki", "AGENTS.md"),
        os.path.join("memory-wiki", "_ingest"),
        os.path.join("core", "DAEMON_PULSE.md"),
        "planning-artifacts",
        os.path.join("assets", "default_engrams"),
    ):
        stale_path = os.path.join(OS_DIR, stale_rel)
        if os.path.isdir(stale_path):
            shutil.rmtree(stale_path, ignore_errors=True)
        elif os.path.isfile(stale_path):
            try:
                os.remove(stale_path)
            except OSError:
                pass

    if not skip_deps:
        print("[*] Rebuilding dependencies...")
        from bootstrap_install import build_engine_venv

        build_engine_venv(OS_DIR)

    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
    print("\n[SUCCESS] Sovereign Engine Update Complete. You are running the latest A.I.M. OS.")


def ensure_hooks_mapped():
    """Self-heals stale hook paths in global Antigravity settings when a workspace is moved."""
    from config_utils import get_agy_settings_paths

    settings_paths = get_agy_settings_paths(existing_only=True)
    if not settings_paths:
        return
    try:
        needs_update = False
        for settings_path in settings_paths:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            after_hooks = settings.get("hooks", {}).get("AfterTool", [])
            for entry in after_hooks:
                for hook in entry.get("hooks", []):
                    if hook.get("name") == "cognitive-mantra":
                        if "aim_router.py" not in hook.get("command", ""):
                            needs_update = True
                            break
            if needs_update:
                break

        if needs_update:
            try:
                if AIM_CORE_DIR not in sys.path:
                    sys.path.insert(0, AIM_CORE_DIR)
                import aim_init

                aim_init.register_hooks()
            except Exception:
                pass
    except Exception:
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="J.O.S.H.U.A. / A.I.M. Operating System CLI")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Initialize or configure J.O.S.H.U.A. workspace")
    init_parser.add_argument("--reinstall", action="store_true", help="Perform a reinstall with backup")
    init_parser.add_argument("--uninstall", action="store_true", help="Show uninstallation instructions")
    init_parser.add_argument("--light", action="store_true", help="Install Lightweight AOS Mode (continuity only)")
    init_parser.add_argument("--headless", action="store_true", help="Run non-interactively without prompts")
    init_parser.add_argument("--persona", type=str, help="Persona blueprint name for co-agent deployment")
    init_parser.add_argument("--clean", action="store_true", help="Reset docs and seed default LanceDB brain")

    subparsers.add_parser("status", help="Show latest session continuity pulse")
    subparsers.add_parser("config", aliases=["tui"], help="Open the interactive configuration menu")
    subparsers.add_parser("core-memory", help="Open CORE_MEMORY.md in $EDITOR")

    update_parser = subparsers.add_parser("update", help="Update the local J.O.S.H.U.A. engine")
    update_parser.add_argument("--source", type=str, default=None, help="Optional local path to aim-joshua checkout")
    update_parser.add_argument("--ref", type=str, default=None, help="Optional Git tag or branch ref (defaults to latest release)")
    update_parser.add_argument("--skip-deps", action="store_true", help="Skip Python venv dependency sync")

    subparsers.add_parser("doctor", help="Validate Python runtime and core package dependencies")
    subparsers.add_parser("health", help="Check LanceDB, session history DB, and Memory Wiki health")

    prune_remote_parser = subparsers.add_parser(
        "prune-remote", help="Garbage collect stale remote branches (fix/issue-* and archive-fix/*)"
    )
    prune_remote_parser.add_argument("--confirm", action="store_true", help="Delete matching branches on origin")

    purge_parser = subparsers.add_parser("purge", help="Reset J.O.S.H.U.A. memory/archive state inside joshua_os/")
    purge_parser.add_argument("--yes", "-y", action="store_true", help="Confirm non-interactively")

    uninstall_parser = subparsers.add_parser("uninstall", help="Safely remove J.O.S.H.U.A. from this repository")
    uninstall_parser.add_argument("--yes", "-y", action="store_true", help="Confirm non-interactively")
    uninstall_parser.add_argument(
        "--purge-memory",
        action="store_true",
        help="Also remove J.O.S.H.U.A.-managed memory-wiki/, HANDOFF.md, AGENTS.md, TOOLS.md, and blackbox",
    )
    uninstall_parser.add_argument(
        "--force-upstream", action="store_true", help=argparse.SUPPRESS
    )

    index_parser = subparsers.add_parser("index", help="Index AGENTS.md, memory-wiki/, and docs into LanceDB")
    index_parser.add_argument("--dir", type=str, help="Additional custom directory to ingest")

    handoff_parser = subparsers.add_parser("handoff", aliases=["pulse"], help="Generate session flight record pulse")
    handoff_parser.add_argument("--session-id", default=None, help="Explicit AGY conversation UUID")

    vault_parser = subparsers.add_parser(
        "vault",
        help="Encrypted session Blackbox Vault (audit / verify / seal / doctor)",
    )
    vault_sub = vault_parser.add_subparsers(dest="vault_command")
    vault_audit = vault_sub.add_parser("audit", help="Decrypt sealed session to stdout")
    vault_audit.add_argument("session_id")
    vault_audit.add_argument("--vessel", default=None, help="Vessel root (default: cwd)")
    vault_verify = vault_sub.add_parser("verify", help="Compare sealed sha256 against live transcript or blob")
    vault_verify.add_argument("session_id")
    vault_verify.add_argument("--vessel", default=None)
    vault_verify.add_argument("--live", default=None, help="Path to live transcript")
    vault_seal = vault_sub.add_parser("seal", help="Seal a session transcript into the Blackbox Vault")
    vault_seal.add_argument("--session-id", default=None)
    vault_seal.add_argument("--path", default=None, help="Explicit raw transcript path")
    vault_seal.add_argument("--vessel", default=None)
    vault_seal.add_argument("--force", action="store_true", help="Allow overwriting a larger previously sealed blob")
    vault_sub.add_parser("doctor", help="Run vault keyring and fallback key diagnostics")

    for bb_cmd, bb_help in (
        ("agy-blackbox", "Seal Antigravity session transcript to Blackbox Vault"),
        ("grok-blackbox", "Seal Grok CLI session transcript to Blackbox Vault"),
        ("codex-blackbox", "Seal Codex CLI rollout transcript to Blackbox Vault"),
        ("opencode-blackbox", "Seal OpenCode SQLite session transcript to Blackbox Vault"),
    ):
        bb_p = subparsers.add_parser(bb_cmd, help=bb_help)
        bb_p.add_argument("--session-id", required=True)
        bb_p.add_argument("--vessel-root", "--vessel", dest="vessel_root", default=None, help="Target project/vessel root")
        bb_p.add_argument("--force", action="store_true", help="Allow overwriting a larger previously sealed blob")

    hv_parser = subparsers.add_parser(
        "handoff-vnext",
        help="Handoff vNext pipelines: handoff | blackbox-cron | e2e-staged",
    )
    hv_parser.add_argument(
        "vnext_command",
        choices=["handoff", "blackbox-cron", "e2e-staged"],
    )
    hv_parser.add_argument("--session-id", default=None)
    hv_parser.add_argument("--adapter", default="agy", help="agy|grok|fixture")
    hv_parser.add_argument("--fixture-root", default=None)
    hv_parser.add_argument("--vessel-root", default=None)
    hv_parser.add_argument("--project-root", default=None)
    hv_parser.add_argument("--marker", default=None)
    hv_parser.add_argument("--limit", type=int, default=50)
    hv_parser.add_argument("--json", action="store_true")

    delegate_parser = subparsers.add_parser(
        "delegate", help="Analyze multiple files in parallel via configured LLM reasoning endpoint"
    )
    delegate_parser.add_argument("instruction", help="Prompt/instruction for each file worker")
    delegate_parser.add_argument("--files", nargs="+", required=True, help="Target files to analyze")

    clean_parser = subparsers.add_parser(
        "clean", help="Run rolling archive retention cleanup and safe LanceDB compaction"
    )
    clean_parser.add_argument(
        "days",
        nargs="?",
        type=int,
        default=None,
        help="Optional rolling archive retention window in days",
    )
    clean_parser.add_argument(
        "--immediate",
        action="store_true",
        help="Compact LanceDB immediately with zero-second retention window",
    )

    exchange_parser = subparsers.add_parser("exchange", help="Mount, unmount, or list Parquet ROM cartridges")
    exchange_parser.add_argument("exchange_args", nargs=argparse.REMAINDER, help="{import <file> | unplug <kw> | list}")

    bake_parser = subparsers.add_parser("bake", help="Compile a documentation folder into a .parquet ROM cartridge")
    bake_parser.add_argument("directory", help="Source documentation directory to vectorize")
    bake_parser.add_argument("output", help="Output .parquet cartridge filename")
    bake_parser.add_argument("--author", help="Cartridge author metadata", default="Unknown")
    bake_parser.add_argument("--version", help="Cartridge version (e.g., 1.0.0)", default="1.0.0")
    bake_parser.add_argument("--description", help="Cartridge description", default="No description provided.")

    jackin_parser = subparsers.add_parser("jack-in", help="Mount a local .parquet cartridge into archive/cartridges/")
    jackin_parser.add_argument("file", help="Path to local .parquet cartridge")

    unplug_parser = subparsers.add_parser("unplug", help="Unmount a mounted .parquet cartridge by keyword/name")
    unplug_parser.add_argument("keyword", help="Cartridge name or prefix to unmount")

    subparsers.add_parser("map", help="Print the LanceDB Index of Keys (Knowledge Map)")

    audit_parser = subparsers.add_parser("audit", help="Synthesize a strategic report from recent archived sessions")
    audit_parser.add_argument("-n", type=int, default=5, help="Number of recent sessions to include")

    recall_parser = subparsers.add_parser("recall", help="Synthesize an answer from archived session transcripts")
    recall_parser.add_argument("query", nargs="+", help="Recall query")

    subparsers.add_parser("sessions", help="List archived sessions for this project")
    search_sessions_parser = subparsers.add_parser(
        "search-sessions", help="Full-text search across archived project sessions"
    )
    search_sessions_parser.add_argument("query", nargs="+", help="Search query")

    bug_parser = subparsers.add_parser("bug", help="Create a structured GitHub Issue via gh CLI (strict mode)")
    bug_parser.add_argument("title", help="Issue title")
    bug_parser.add_argument("--context", help="Architectural context", default="")
    bug_parser.add_argument("--failure", help="Observed failure or goal", default="")
    bug_parser.add_argument("--intent", help="Actionable implementation steps", default="")

    bug_operator_parser = subparsers.add_parser(
        "bug-operator", help="Create a structured GitHub Issue via gh CLI (interactive mode)"
    )
    bug_operator_parser.add_argument("title", help="Issue title")
    bug_operator_parser.add_argument("--context", help="Architectural context", default="")
    bug_operator_parser.add_argument("--failure", help="Observed failure or goal", default="")
    bug_operator_parser.add_argument("--intent", help="Actionable implementation steps", default="")

    fix_parser = subparsers.add_parser("fix", help="Spawn an isolated git worktree under workspace/issue-<id>")
    fix_parser.add_argument("id", help="Issue or task ID")

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
        help="owner/repo for auto-adding issues (e.g. my-org/my-repo)",
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

    promote_parser = subparsers.add_parser(
        "promote", help="Archive default branch, merge current worktree branch, and remove clean worktree"
    )
    promote_parser.add_argument("--yes", "-y", action="store_true", help="Confirm merge non-interactively")

    merge_batch_parser = subparsers.add_parser(
        "merge-batch", help="Merge all open remote fix/issue-* branches into default branch"
    )
    merge_batch_parser.add_argument("--push", action="store_true", help="Push merged default branch to origin")
    merge_batch_parser.add_argument("--yes", "-y", action="store_true", help="Confirm batch merge non-interactively")

    search_parser = subparsers.add_parser("search", help="Hybrid vector + BM25 search over LanceDB")
    search_parser.add_argument("query", nargs="+")
    search_parser.add_argument("--top-k", type=int)
    search_parser.add_argument("--full", action="store_true")
    search_parser.add_argument("--session", type=str)
    search_parser.add_argument("--json", action="store_true")

    push_parser = subparsers.add_parser("push", help="Semantic version bump, commit tracked changes, and push")
    push_parser.add_argument("message")
    push_parser.add_argument(
        "--include-untracked",
        "-a",
        action="store_true",
        help="Stage all untracked (non-gitignored) files before committing",
    )

    return parser


COMMAND_HANDLERS = {
    "init": cmd_init,
    "status": cmd_status,
    "core-memory": cmd_core_memory,
    "search": cmd_search,
    "map": cmd_map,
    "update": cmd_update,
    "config": cmd_config,
    "tui": cmd_config,
    "index": cmd_index,
    "handoff": cmd_handoff,
    "pulse": cmd_handoff,
    "push": cmd_push,
    "handoff-vnext": cmd_handoff_vnext,
    "delegate": cmd_delegate,
    "vault": cmd_vault,
    "clean": cmd_clean,
    "bake": cmd_bake,
    "exchange": cmd_exchange,
    "jack-in": cmd_jack_in,
    "unplug": cmd_unplug,
    "agy-blackbox": cmd_agy_blackbox,
    "grok-blackbox": cmd_grok_blackbox,
    "codex-blackbox": cmd_codex_blackbox,
    "opencode-blackbox": cmd_opencode_blackbox,
    "audit": cmd_audit,
    "recall": cmd_recall,
    "sessions": cmd_sessions,
    "search-sessions": cmd_search_sessions,
    "doctor": cmd_doctor,
    "health": cmd_health,
    "bug": cmd_bug,
    "bug-operator": cmd_bug_operator,
    "projects": cmd_projects,
    "project": cmd_projects,
    "fix": cmd_fix,
    "promote": cmd_promote,
    "merge-batch": cmd_merge_batch,
    "purge": cmd_purge,
    "prune-remote": cmd_prune_remote,
    "uninstall": cmd_uninstall,
}


def main():
    ensure_hooks_mapped()
    parser = build_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    handler = COMMAND_HANDLERS.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(2)
    handler(args)


if __name__ == "__main__":
    main()
