# Operations

## Parallel Execution & GitOps
J.O.S.H.U.A. enforces a highly parallel GitOps execution model, heavily formalized in `CONTRIBUTING.md`:
- Agents must NOT develop application code on the `main` branch. They use `aim fix <issue_id>` to spawn physically isolated `git worktree` sandboxes.
- **Agent Memory Exemption (#101):** Living OS memory state (`memory-wiki/**` and `HANDOFF.md`) is explicitly exempt from GitHub Issues and worktrees. Both `/aim-memory-wiki` (mid-session checkpoint) and `/aim-handoff` (end-of-session closeout with Auto-Wiki Delta Check) stage only the explicit memory paths (`git add memory-wiki/` and/or `git add HANDOFF.md`), commit, run `git pull --rebase --autostash origin main`, and push directly to `origin/main` with zero Operator confirmation prompts.
- The agent workspace loop uses `aim push "<msg>"` (implemented in pure Python via `git_push_changes` in `aim_cli.py`) to commit and push changes within the worktree. By default, `aim push` stages tracked changes (`git add -u`) and emits a `[NOTICE]` on `stderr` if untracked files are detected; pass `--include-untracked` (`-a`) or run `git add <file>` to stage new files.
- Native cross-platform entrypoints (`./aim` for Bash, `aim.ps1` for PowerShell, and `aim.cmd` for Windows CMD) resolve both Unix (`venv/bin/python3`) and Windows (`venv\Scripts\python.exe`) virtual environments.
- The atomic release process utilizes `aim promote` to safely archive `main`, merge the active worktree branch, deploy the final baseline to GitHub, and destroy the local workspace sandbox.
- System-level isolation can be optionally added using `bwrap` if network or filesystem restrictions are required.

## Installation Pathways
- **Option A — Clean Project Installation (Default)**: Uses `install.sh` to install the engine into a new or existing software project while purging upstream Git history, tests, and benchmarks. Enforces a `$HOME`/`/` safety guard, copies `joshua_os/`, `AGENTS.md` (`cp -n`), `TOOLS.md` (`cp -n`), `aim.ps1` (`cp -n`), and `aim.cmd` (`cp -n`), scaffolds root `memory-wiki/pages/`, initializes `.git` if missing, registers `search_lancedb` MCP and AGY folder-trust (`agy_workspace_trust.py`), and automatically populates `.gitignore` with `joshua_os/`, `aim`, `aim.ps1`, `aim.cmd`, `workspace/`, and `archive/`.
- **Option B — Headless Co-Agent / Sovereign Node**: Uses `install-agent.sh [persona_name]` for specialist Co-Agent deployments (`aim-agents/*`). If `<persona_name>` is passed (e.g., `python-developer`, `aim-auditor`, `content-node`, `content-wordpress`), resolves `blueprints/<persona_name>/AGENTS.md` from local `~/aim-coagents` or GitHub `BrianV1981/aim-coagents`; otherwise installs the full 10-section J.O.S.H.U.A. `AGENTS.md` blueprint.
  - **Two Content Co-Agent Blueprints (`content-node` vs. `content-wordpress`)**:
    1. **`content-node` (`aim-ld-content`)**: Built for Node.js / Next.js applications (`leaddeeds.com`). Outputs Markdown with YAML frontmatter (`src/content/resources/<slug>.md`), 3 dark-mode `.jpg` graphics (`public/<slug>_*.jpg`), React-Markdown YouTube thumbnail embeds, and gates delivery on `npm run build`.
    2. **`content-wordpress` (`aim-tbsoftwash-content`)**: Built for custom WordPress PHP themes (`tbsoftwash.com` + `academy.tbsoftwash.com`). Outputs PHP templates (`blog-<slug>.php` / `page-<slug>-guide.php`) with centralized Router SEO (`tbsoftwash_get_current_route_seo()`), zero inline `<style>` tags, `<lite-youtube>` embeds, local `1200px` quality-`80` `.webp` graphics, `component-meet-the-experts.php` automatic `BlogPosting` JSON-LD, and gates delivery on `python3 tools/test_guardrails.py`.
- **Option C — Core Contributor Installation**: Uses `install-core.sh` to install the engine while preserving developer histories, `tests/`, `benchmarks/`, and `.git` artifacts (with `$HOME`/`/` safety guard and MCP registration).
- **Post-Install CLI Onboarding (`./aim init` / `aim_init.py` & `BOOTSTRAP.md`)**: `aim_init.provision_agents_md()` guarantees `AGENTS.md` always contains the full 10-section J.O.S.H.U.A. template (`joshua_os/.aim_core/templates/default_AGENTS.md`) or a resolved `aim-coagents` blueprint, never overwriting `AGENTS.md` with a truncated stub (#103).

## Co-Agent Engine Updates (`aim update`) & Fleet Migrations
`cmd_update` (`aim update [--source <local_dir>] [--skip-deps]`) upgrades `joshua_os/` across deployed projects and Co-Agent nodes while strictly preserving tenant state:
- Preserves `.aim_core/CONFIG.json` across `.aim_core` directory replacement.
- Never overwrites tenant root files (`AGENTS.md`, `TOOLS.md`, `manifest.json`, `memory-wiki/`, `artifacts/`, or `joshua_os/memory_lance/`).
- Guards optional subdirectories (such as `scripts/`) with existence checks prior to `shutil.copytree`.
- **Consumer `.gitignore` Safeguard (`ensure_consumer_gitignore`)**: Automatically ensures `joshua_os/`, `aim`, `workspace/`, and `archive/` are ignored in downstream consumer projects' `.gitignore` files while skipping the upstream `aim-joshua` repository (`is_upstream_engine_repo`).
- **Atomic `./aim` Wrapper Refresh**: Uses `os.replace(tmp_aim, dst_aim)` rather than in-place `shutil.copy2` when refreshing the root `./aim` bash wrapper so that an actively executing `/bin/bash ./aim update` process continues reading its original inode without a byte-offset shift.
- **Legacy `aim-agy_os/` → `joshua_os/` Migration Pitfall**: When migrating legacy `aim-agy_os/` repositories to `joshua_os/`, copy the new `.aim_core/config_utils.py` *before* running `./aim update`; otherwise, the legacy `find_project_root()` walks up to `$HOME` if `~/aim-agy_os` exists and misroutes `PROJECT_ROOT`.

