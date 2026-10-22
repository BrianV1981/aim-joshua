# J.O.S.H.U.A. — Engineering Handoff

> **Updated:** 2026-10-21T20:14:00-04:00
> **Updated by:** Antigravity (Session ID: 3078de63-43ae-427e-8e31-f5698043c30a)
> **Priority Mission:** STANDBY / Awaiting Directives (`AUDIT_AIM_JOSHUA.md` Grade **A+**, `v0.8.3` Direct-to-`main` Memory State, Onboarding Blueprint Guard & Cross-Platform Engine, `34/34` Pytest, Backlog Clear)
> **Operator:** Brian Vasquez (`@BrianV1981`)

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
| 513519c1 | Fleet Rollout: Provisioned `aim-skorbane` and upgraded all 16 active `aim-*` & `aim-agents/*` repos to `v0.7.3+` (`./aim doctor` 100% green) | ✅ RESOLVED |
| 6c0e4f7b | #98: Added Windows 10/11 launchers (`aim.ps1`, `aim.cmd`), `resolve_venv_python()`, Windows root-drive guard, and pure-Python `git_push_changes()` with untracked warning & `--include-untracked` (`-a`) (`v0.8.0`, `67d5fb36`) | ✅ RESOLVED |
| 6c0e4f7b | #99: Added dynamic `get_active_aim_root()` in `retriever.py` so `archive/cartridges` & `flashrank_cache` follow `lance_backend.LANCE_DB_PATH` during MCP queries (`32/32` pytest passing) | ✅ RESOLVED |
| 6c0e4f7b | #100: Ingested `v0.8.0` cross-platform launchers, pure-Python push, MCP cartridge root, and default Project `#7` config into `memory-wiki/` (`3d715061`) | ✅ RESOLVED |
| 6c0e4f7b | Lore Sync (`aim-knowledge`): Published *The Great Convergence* & *J.O.S.H.U.A. vs. Open-Source Harness Era* essays + updated `AIM_ECOSYSTEM_HISTORY.md` (`c6b4d63`) | ✅ RESOLVED |
| 3078de63 | #101: Decoupled `memory-wiki/**` & `HANDOFF.md` from worktree GitOps (`AGENTS.md`, `aim-skill-library` `08511ae`), added Auto-Wiki Delta Check to `/aim-handoff`, and fixed `bootstrap_brain.py` root `memory-wiki/` indexing (`v0.8.1`, `b8f0b88a`, `33/33` pytest) | ✅ RESOLVED |
| 3078de63 | #102: Aligned `COGNITIVE_ARCHITECTURE.md`, `GAMEPLAN_SOP.md`, `GITOPS_DEPLOYMENT.md`, `AIM_CLI_TOOLS.md`, `AGENTS_AMENDMENT_PROTOCOL.md`, `README.md`, `CONTRIBUTING.md`, and `memory-wiki/pages/` with direct-to-`main` memory state (`v0.8.2`, `cc9d13c0`) | ✅ RESOLVED |
| 3078de63 | Fleet `AGENTS.md` Rollout: Upgraded 22 `AGENTS.md` files across all active `aim-*`, `aim-coagents`, and `aim-agents/*` repos to `v0.8.2` (`git commit --only`, preserving 100% of project domain rules) + deleted stray `/home/kingb/AGENTS.md` | ✅ RESOLVED |
| 3078de63 | #103: Fixed `aim_init.py` 7-line `AGENTS.md` stub overwrite (`provision_agents_md` + `templates/default_AGENTS.md`), aligned `BOOTSTRAP.md`, added `$1` persona blueprint fetch to `install-agent.sh`, and standardized all 4 `install*.sh` scripts (`v0.8.3`, `4f950fbd`, `34/34` pytest) | ✅ RESOLVED |

*(Keep clean and consolidated. Point to wiki/issues for deep history — do not re-audit.)*

---

## 1. PROJECT IDENTITY
J.O.S.H.U.A. is the CLI-agnostic OS brain for A.I.M. agents: nested `joshua_os/`, GitOps worktrees, LanceDB hybrid memory, blackbox vault, GitHub Projects CLI.

### Your Knowledge Base
- `/home/kingb/aim-joshua/memory-wiki/index.md` (The active LLM Wiki Index)
- `/home/kingb/aim-joshua/AGENTS.md` (The sovereign agent blueprint and OS rules)
- `/home/kingb/aim-joshua/memory-wiki/pages/handoff-and-retrieval.md` (Retrieval mechanics)
- `/home/kingb/aim-joshua/memory-wiki/pages/architecture.md` (Two-Tier MCP Protocol)
- `/home/kingb/aim-joshua/memory-wiki/pages/dhh-agentic-philosophy.md` (Core Agentic Directives)

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
- **Legacy `aim-agy_os/` Migration Sequence:** When migrating legacy `aim-agy_os/` repos to `joshua_os/`, copy the updated `joshua_os/.aim_core/config_utils.py` *before* running `./aim update` so `find_project_root()` does not walk up to `~/aim-agy_os`.

---

## 6. KEY PATHS
- `/home/kingb/aim-joshua/joshua_os/`
- `/home/kingb/aim-joshua/aim`, `/home/kingb/aim-joshua/aim.ps1`, `/home/kingb/aim-joshua/aim.cmd` (Cross-Platform Launchers)
- `/home/kingb/aim-joshua/memory-wiki/`
- `/home/kingb/aim-joshua/joshua_os/.aim_core/mcp_lancedb.py`
- `/home/kingb/aim-joshua/joshua_os/.aim_core/retriever.py`
- `/home/kingb/aim-joshua/tests/` (`33/33` Pytest Coverage)
- `/home/kingb/aim-joshua/joshua_os/.aim_core/aim_cli.py` (CLI Router)

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
