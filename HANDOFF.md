# J.O.S.H.U.A. — Engineering Handoff

> **Updated:** 2026-10-30T20:06:00-04:00
> **Updated by:** Antigravity (Session ID: 2e735b20-372f-4d65-b5b7-a2904d9c2e9f)
> **Priority Mission:** STANDBY — `v1.0.0` GENERAL AVAILABILITY SHIPPED (`AUDIT_AIM_JOSHUA.md` Grade **A+**, `v1.0.0` GitHub Release Live, `0` Open Issues, `41/41` Pytest w/ `0` Warnings, `26.03 GiB` Legacy Bloat Reclaimed)
> **Operator:** Brian Vasquez (`@BrianV1981` / `brianv1981@gmail.com`)

---

## 0. COMPLETED WORK (DO NOT REVISIT)
| Session | Work | Status |
|---------|------|--------|
| prior | Overhauled TUI & Purged Reincarnation (#74–#77) | ✅ SHIPPED |
| 73f2d8d9 | #78–#80: Migrate LanceDB Search to MCP Server (`mcp_lancedb.py`) & Two-Tier Docs | ✅ RESOLVED |
| c00d7f1a | #81–#83: Pytest for MCP/Ingestion, recursive glob fix, & `aim index --dir` forwarding | ✅ RESOLVED |
| 4c79e879 | #84–#86: DHH Agentic Era & Direct Execution Protocols in `AGENTS.md` and `memory-wiki/` | ✅ RESOLVED |
| 513519c1 | #87–#88: Reconciled local Git/worktree drift & pruned 95 remote + 72 local stale branches | ✅ RESOLVED |
| 513519c1 | #89–#90: Removed deprecated `swarm` CLI routes & standardized `README.md` `AIM_ECOSYSTEM` block | ✅ RESOLVED |
| 513519c1 | #92: Hardened `cmd_update` (`--source`, `--skip-deps`, `CONFIG.json` & Co-Agent blueprint preservation) | ✅ RESOLVED |
| 513519c1 | #93: Modularized `aim_cli.py` (`cli_vault.py`, `cli_memory.py`), fixed relative imports, expanded pytest suite | ✅ RESOLVED |
| 513519c1 | #91: Pass 9 Delta Audit by `aim-auditor` (`e37ea954`) — **Overall Grade: A+** (`0` open findings) | ✅ RESOLVED |
| 513519c1 | #94: Implemented Local-First + Umbrella Subfolder Fallback in `mcp_lancedb.py` | ✅ RESOLVED |
| 513519c1 | #95: Hardened `install.sh`/`install-agent.sh` (`$HOME` guard, clean project scaffolding) & clarified `README.md` onboarding (`28/28` pytest passing) | ✅ RESOLVED |
| 513519c1 | #96: Auto-populate consumer `.gitignore` (`joshua_os/`, `aim`, `workspace/`, `archive/`), atomic `os.replace` on `./aim` in `cmd_update` (`29/29` pytest passing) | ✅ RESOLVED |
| 513519c1 | #97: Ingested `.gitignore` safeguards, atomic `./aim` updates, and 16-repo fleet upgrade into `memory-wiki/` (`v0.7.4`, `6d7a383b`) | ✅ RESOLVED |
| 513519c1 | Fleet Rollout: Upgraded all 16 active `~/aim-*` & `~/aim-agents/*` repos to `v0.7.3+` (`./aim doctor` 100% green) | ✅ RESOLVED |
| 6c0e4f7b | #98: Added Windows 10/11 launchers (`aim.ps1`, `aim.cmd`), `resolve_venv_python()`, Windows root-drive guard, and pure-Python `git_push_changes()` with untracked warning & `--include-untracked` (`-a`) (`v0.8.0`, `67d5fb36`) | ✅ RESOLVED |
| 6c0e4f7b | #99: Added dynamic `get_active_aim_root()` in `retriever.py` so `archive/cartridges` & `flashrank_cache` follow `lance_backend.LANCE_DB_PATH` during MCP queries (`32/32` pytest passing) | ✅ RESOLVED |
| 6c0e4f7b | #100: Ingested `v0.8.0` cross-platform launchers, pure-Python push, MCP cartridge root, and default Project `#7` config into `memory-wiki/` (`3d715061`) | ✅ RESOLVED |
| 6c0e4f7b | Lore Sync (`aim-knowledge`): Published *The Great Convergence* & *J.O.S.H.U.A. vs. Open-Source Harness Era* essays + updated `AIM_ECOSYSTEM_HISTORY.md` (`c6b4d63`) | ✅ RESOLVED |
| 3078de63 | #101: Decoupled `memory-wiki/**` & `HANDOFF.md` from worktree GitOps (`AGENTS.md`, `aim-skill-library` `08511ae`), added Auto-Wiki Delta Check to `/aim-handoff`, and fixed `bootstrap_brain.py` root `memory-wiki/` indexing (`v0.8.1`, `b8f0b88a`, `33/33` pytest) | ✅ RESOLVED |
| 3078de63 | #102: Aligned `COGNITIVE_ARCHITECTURE.md`, `GAMEPLAN_SOP.md`, `GITOPS_DEPLOYMENT.md`, `AIM_CLI_TOOLS.md`, `AGENTS_AMENDMENT_PROTOCOL.md`, `README.md`, `CONTRIBUTING.md`, and `memory-wiki/pages/` with direct-to-`main` memory state (`v0.8.2`, `cc9d13c0`) | ✅ RESOLVED |
| 3078de63 | Fleet `AGENTS.md` Rollout: Upgraded 22 `AGENTS.md` files across all active `~/aim-*`, `aim-coagents`, and `~/aim-agents/*` repos to `v0.8.2` (`git commit --only`, preserving 100% of project domain rules) + deleted stray `~/AGENTS.md` | ✅ RESOLVED |
| 3078de63 | #103: Fixed `aim_init.py` 7-line `AGENTS.md` stub overwrite (`provision_agents_md` + `templates/default_AGENTS.md`), aligned `BOOTSTRAP.md`, added `$1` persona blueprint fetch to `install-agent.sh`, and standardized all 4 `install*.sh` scripts (`v0.8.3`, `4f950fbd`, `34/34` pytest) | ✅ RESOLVED |
| 3078de63 | #104: Added `README.md` 3-option comparison table & `./aim init` guide, refreshed `default_lance` (`364 KB`, `58` `v0.8.4` fragments), fixed dynamic `LANCE_DB_PATH` binding in `VectorBackend()`, deduplicated `install-clean.sh`, and updated `aim-coagents` installer URLs (`v0.8.4`, `9a5b5cef` / `d5f52a6`) | ✅ RESOLVED |
| 3078de63 | #105: Set `timeout=(0.5, 15)` on local Ollama (`127.0.0.1:11434`) in `forensic_utils.py`, added `artifacts/AUDIT_*.md` to `bootstrap_brain.py`, added 4-point Live Production & Deploy Parity lens to `aim-coagents/personas/aim-auditor/PERSONA.md` (`a644fce`), and upgraded/indexed `aim-tester` (`6525cc1`), `aim-enricher` (`f5822d6`), and `aim-permits` (`75064cc`) (`4c39858c`, `35/35` pytest in `14.87s`) | ✅ RESOLVED |
| 3078de63 | Content Co-Agents & `aim-youtube` Hub-and-Spoke Protocol: Codified `blueprints/content-node` and `blueprints/content-wordpress` in `aim-coagents` (`3af01d6`); synced canonical Linux Tmux `aim-communicate` to `vessels/agy/skills/aim-communicate/`, standardized Operator emails (`83c5a9e`), and codified `aim-youtube` Hub-and-Spoke delegation in `aim-skill-library` (`30db021`) | ✅ RESOLVED |
| 0eca3c90 | #106: Codified Google Oct 1st People-First Content & First-Party Effort Doctrine (`RankEmbed BERT` 4 Rater Pillars, First-Party Non-Training Data, Interactive Main Content Micro-Tools, Zero Scaled Templates, Anti-LLM Prose Filter, Full Human Bylines, `HTTP 200` + `<title>`/`<meta>`/`<img alt>` Fact-Checking) across `aim-skill-library` (`2e3edeb`), `aim-coagents` (`9ff5782`), and `aim-joshua/memory-wiki/` (`01ae4d1b`) | ✅ RESOLVED |
| 02feb6e8 | #107: Fixed `aim_init.py` `f.read().splitlines()` on pre-existing `.gitignore` files and added regression test (`v0.8.5`, `2c5d4bc4`, `36/36` pytest) | ✅ RESOLVED |
| 02feb6e8 | #108: Removed hardcoded host path comments in `agy_workspace_trust.py` and `spawn_sandbox.py`, added `test_no_hardcoded_host_paths_in_engine_code` (`v0.8.6`, `71a0b086`, `37/37` pytest), sanitized `HANDOFF.md` & `memory-wiki/`, and pruned stale remote branches on `origin` | ✅ RESOLVED |
| 02feb6e8 | `aim-connect` `#209`–`#212`: Shipped Fleet Panes Telemetry (`/api/fleet/panes`), Swarm Activity (`/api/swarm/activity`), Session Forensics (`/api/forensics/{session}`), and Workspace Context (`/api/workspace/context`) endpoints on Project `#6` | ✅ RESOLVED |
| 02feb6e8 | `aim-office` `#1`–`#10`: Provisioned `~/aim-office` (`BrianV1981/aim-office`, Project `#14` `10/10` `Done`, `d1e17b4`, live on `http://localhost:5175`), sliced all 20 Sovereign Character `2x2` sprite sheets (`80` directional PNGs), built 3-theme pack engine (`sovereign-war-room`, `cutaway-agency`, `classic-command`) with `v4` bottom-anchor-compensated pod coordinates, floating draggable 2-column Agent Cockpit (`AgentInspectorDrawer.tsx`), and live per-agent Kanban switching (`SESSION_PROJECT_MAP` + `parseHandoffKanbanForSession` + 60s cache in `officeBridge.ts`, `13/13` Vitest + `2/2` Pytest) | ✅ RESOLVED |
| 2e735b20 | #110: Fixed multi-key `audit_vault()` decrypt (`get_candidate_keys()`), added `index_session_to_history()` & `sync_vault_to_history()` auto-populating `joshua_os/archive/history.db` (FTS5), upgraded `./aim sessions` & `./aim search-sessions`, created `/aim-sessions` skill & enforced `agy-blackbox` in `aim-handoff` (`aim-skill-library` `e5fb9fe`), orchestrated `aim-ld` `#469` (`759fdcf` / `904a397`) to stop `parse_news_llm.py` & `run_enricher.py` session spam (purging `2,785` 2-step rows & `351` `.db`/`brain` dirs), and upgraded/backfilled all 22 active `joshua_os` repos to `v0.8.7` (`2da8423a`, `39/39` pytest) | ✅ RESOLVED |
| 2e735b20 | #111–#112: Codified and expanded the multi-paragraph `Spoken Summary (🔊)` mandate in `AGENTS.md`, `joshua_os/.aim_core/templates/default_AGENTS.md`, and `joshua_os/assets/default_lance` (`v0.8.8`–`v0.8.9`, `23e4f752`, `39/39` pytest); updated all 6 `aim-coagents` blueprints (`955f467`); and rolled out `v0.8.9` + surgical `Spoken Summary (🔊)` `AGENTS.md` updates across all 22 active `joshua_os` repositories for `aim-connect` start-to-prompt Neural TTS (`#222`–`#224`) | ✅ RESOLVED |
| 2e735b20 | #113–#114: Added forward-compatible `list_lance_tables(db)` across `lance_backend.py`, `retriever.py`, and `embed_store.py` (`v0.8.10`, `b3bddb0b`, `40/40` pytest w/ `0` warnings); pruned all stale remote/local archive branches; verified cold-vault `.git.bundle` + dirty worktree snapshots (`~/aim_legacy_archive/cold_vault_20261030/`), symlink-deduped `longmemeval_s.engram`, and dehydrated `203` retired `venv`/`node_modules` dirs reclaiming **`26.03 GiB`** (`385G` → `410G` free) | ✅ RESOLVED |
| 2e735b20 | #115: Graduated `README.md` to `v1.0 — Production-tested, trenches-first.`, bumped `VERSION` to `v1.0.0`, updated `CHANGELOG.md`, added `test_semver_ga_posture()` (`480511b0`, `41/41` pytest w/ `0` warnings), and published the inaugural official `v1.0.0` GitHub Release on `BrianV1981/aim-joshua` | ✅ SHIPPED |

*(Keep clean and consolidated. Point to wiki/issues for deep history — do not re-audit.)*

---

## 1. PROJECT IDENTITY
J.O.S.H.U.A. is the CLI-agnostic OS brain for A.I.M. agents: nested `joshua_os/`, GitOps worktrees, LanceDB hybrid memory, blackbox vault, GitHub Projects CLI.

### Your Knowledge Base
- `~/aim-joshua/memory-wiki/index.md` (The active LLM Wiki Index)
- `~/aim-joshua/AGENTS.md` (The sovereign agent blueprint and OS rules)
- `~/aim-joshua/memory-wiki/pages/handoff-and-retrieval.md` (Retrieval mechanics)
- `~/aim-joshua/memory-wiki/pages/architecture.md` (Two-Tier MCP Protocol)
- `~/aim-joshua/memory-wiki/pages/dhh-agentic-philosophy.md` (Core Agentic Directives)
- `~/aim-joshua/memory-wiki/pages/google-oct1-people-first-content.md` (Google Oct 1st Main Content & First-Party Effort Doctrine)
- `~/aim-joshua/memory-wiki/pages/aim-office-cockpit.md` (AIM-Office 2.5D Isometric Multi-Vessel Fleet Cockpit & Telemetry Bridge)

---

## 2. YOUR MISSION: STANDBY
The backlog is currently clear. You are awaiting explicit operator directives. 

### Execution Queue (in order)
#### 1️⃣ Await Orders
**Problem:** No active tickets.
**Fix:** Parse operator input and execute via GitOps workflow.
**Key files:** N/A

---

## 3. DETAILED ANALYSIS / BREAKDOWN
- **Two-Tier Retrieval Protocol:** The retrieval architecture has fundamentally shifted. If you are operating in a modern CLI/IDE harness (like AGY), you will natively possess the `search_lancedb` internal tool. This MCP server dynamically locates the vector database using Local-First or Umbrella Subfolder Fallback, and `retriever.py` (`get_active_aim_root()`) dynamically tracks `lance_backend.LANCE_DB_PATH` so supplemental `archive/cartridges` and `archive/flashrank_cache` resolve inside the target project. If you are operating in a legacy CLI that lacks MCP, you must gracefully degrade to `python3 joshua_os/.aim_core/aim_cli.py search`. Do not assume tools exist if they are not in your prompt.
- **Cross-Platform Launchers (Linux/macOS & Windows 10/11):** Root entrypoints `./aim` (Bash), `aim.ps1` (PowerShell), and `aim.cmd` (CMD) alongside `resolve_venv_python()` (`Scripts/python.exe` and `bin/python3`) and `git_push_changes()` (pure-Python `cmd_push`) allow J.O.S.H.U.A. to run natively on Linux, macOS, and Windows 10/11 IDEs without requiring a Bash subshell.
- **GitOps Enforcement:** Never code on `main`. Always `aim fix <id>` to branch into a worktree sandbox.
- **Vector Ingestion (Index):** Ingestion is fully parameterized. Custom directories can be ingested into the LanceDB RAM pool by executing `aim index --dir <path>`. This command also handles recursive directory crawling seamlessly.
- **Testing Framework:** The core Python modules (`mcp_lancedb.py`, `bootstrap_brain.py`) now enforce Pytest unit testing using `unittest.mock`.
- **DHH Agentic Philosophy:** The OS now runs on outcome-oriented directives. The Operator supplies the "what/why" (the fuzzy problem), and agents determine the "how" (architecture, routing). The agent acts as an automated gatekeeper during `aim promote`, ensuring TDD and architectural rules are strictly followed before hitting main.
- **Plain-Text Ascendancy:** J.O.S.H.U.A. relies on the Unix Philosophy. All configs, wikis, and tasks must be CLI-accessible flat files (Markdown, JSON) avoiding opaque GUIs.

---

## 4. IMPLEMENTATION STRATEGY
Follow strict GitOps workflow for any future tasks:
1. `aim bug "Title"` to create a structured issue.
2. `aim projects in-progress <id>` (Board is `#7`)
3. `aim fix <id>`
4. Work in the `workspace/issue-<id>` worktree.
5. `aim push` (Ensure `git add` is used for untracked files).
6. `aim promote`
7. `aim projects done <id>`

---

## 5. THE CRITICAL TRAPS & WARNINGS
> **⚠️ EPISTEMIC / OPERATIONAL WARNINGS**
- **The Worktree Mandate (with Agent Memory Exemption):** NEVER perform application code/config development directly on `main` — always use `aim fix <id>`. Conversely, living Agent Memory (`memory-wiki/**` and `HANDOFF.md`) is explicitly exempt from GitHub Issues and worktrees: stage only `git add memory-wiki/` and/or `git add HANDOFF.md` (never `git add .` or `git commit -a`), commit, run `git pull --rebase --autostash origin main`, and push directly to `origin/main` with zero prompts.
- **Mid-Session `/aim-memory-wiki` & Closeout `/aim-handoff`:** `/aim-memory-wiki` runs as a fast (~15s) mid-session checkpoint directly on `main`. At session closeout, `/aim-handoff` automatically inspects `memory-wiki/log.md` first (Step 1 Idempotent Auto-Wiki Delta Check), updates `memory-wiki/` if needed, surgically updates `HANDOFF.md`, and pushes both to `origin/main` in a single atomic commit.
- **The Blackbox Mandate:** Before an agent vessel dies, it MUST execute its vessel-specific vault command (e.g. `aim agy-blackbox --session-id <uuid>`) to extract raw session logs. 
- **The Audit Protocol:** Do not close issues or claim success if the GitHub Actions smoke test is red.
- **The Untracked File Safeguard:** `cmd_push` (`git_push_changes()` in `aim_cli.py`) runs `git add -u` by default for surgical safety, emits a `[NOTICE]` warning on `stderr` if untracked files exist, and supports `aim push --include-untracked "msg"` (or `-a`) or manual `git add <file>` before `aim push`.
- **Consumer `.gitignore` & Atomic Launcher Replacement:** Downstream consumer projects must never track `joshua_os/` or root launchers (`aim`, `aim.ps1`, `aim.cmd`) in Git (`ensure_consumer_gitignore` in `aim_cli.py` and `install.sh` enforce this automatically). When updating launchers inside `cmd_update`, always use atomic `os.replace(tmp_file, dst_file)` rather than `shutil.copy2` so running `/bin/bash ./aim update` processes do not suffer inode byte-offset shifts.
- **Onboarding `AGENTS.md` Protection (`#103`–`#104`):** `aim_init.provision_agents_md()` (`joshua_os/.aim_core/aim_init.py`) and `joshua_os/.aim_core/templates/default_AGENTS.md` must stay in lockstep with the root `AGENTS.md` (`test_aim_init_never_truncates_agents_md_to_stub` in `tests/test_cli.py` enforces exact equality). Never allow any onboarding or init script to overwrite `AGENTS.md` with a stub.
- **Legacy `aim-agy_os/` Migration Sequence:** When migrating legacy `aim-agy_os/` repos to `joshua_os/`, copy the updated `joshua_os/.aim_core/config_utils.py` *before* running `./aim update` so `find_project_root()` does not walk up to `~/aim-agy_os`.

---

## 6. KEY PATHS
- `~/aim-joshua/joshua_os/`
- `~/aim-joshua/aim`, `~/aim-joshua/aim.ps1`, `~/aim-joshua/aim.cmd` (Cross-Platform Launchers)
- `~/aim-joshua/memory-wiki/`
- `~/aim-joshua/joshua_os/.aim_core/mcp_lancedb.py`
- `~/aim-joshua/joshua_os/.aim_core/retriever.py`
- `~/aim-joshua/tests/` (`41/41` Pytest Coverage, `0` Warnings)
- `~/aim-joshua/joshua_os/.aim_core/aim_cli.py` (CLI Router)
- `~/aim-office/` (2.5D Isometric Multi-Vessel Fleet Cockpit, live in `tmux` window `aim-office:server` on `http://localhost:5175`)

---

## 7. THE FULL PICTURE / WHAT COMES AFTER
Future agents will utilize the `search_lancedb` tool directly via MCP. The `aim-skill-library` and other vessel plugins may need future validation against this standard. The primary directive is maintaining codebase parity and stability.

---

## 8. OPERATOR PREFERENCES
- **Worktree Discipline:** Explicit adherence to `git worktree` isolation is non-negotiable (`aim fix`).
- **Kanban Discipline:** All tasks must be claimed natively via `aim projects in-progress`.
- **CLI-Agnosticism:** Ensure all features gracefully degrade so headless, non-MCP agents can still operate the OS.
- **Elevated Operator Role:** When interacting with the Operator, NEVER ask for syntax or mechanical help. Only ping the Operator for high-level "taste", design, or business logic decisions.
- **Outcome-Oriented Directives:** Do not demand prescriptive step-by-step paths from the Operator. Solve the fuzzy problem autonomously.

---

## 9. IMMEDIATE NEXT STEPS
1. Read Operator input to determine the next task.
2. Formulate a plan and create an issue via `aim bug`.
