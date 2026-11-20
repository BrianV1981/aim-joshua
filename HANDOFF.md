# J.O.S.H.U.A. — Engineering Handoff

> **Updated:** 2026-11-20T02:38:00-05:00
> **Updated by:** Antigravity (Session ID: ffa01d2f-b8f0-4264-8973-7f9c1df9a2b9)
> **Priority Mission:** STANDBY — `v1.1.3` SHIPPED, PASS 14 `A+` CERTIFIED & ROLLED OUT ACROSS `21/21` CONSUMER WORKSPACES (`0` Open Issues, `66/66` Pytest w/ `0` Warnings, `HANDOFF.md` Compacted via `#136`)
> **Operator:** Brian Vasquez (`@BrianV1981` / `brianv1981@gmail.com`)

---

## 0. COMPLETED WORK (DO NOT REVISIT)
| Session | Work | Status |
|---------|------|--------|
| ffa01d2f | #136: Vaulted verbatim pre-compaction `HANDOFF.md` (`21,692` bytes, `SHA-256: 8d5e209c...`) in Issue `#136` and executed surgical rolling-window compaction (`~21.7 KB -> ~9.8 KB`, `10/10` `§5` traps preserved) + aligned `aim-skill-library` (`aim-communicate` `v2.0`) | ✅ RESOLVED |
| c0ebd30d | Pass 14 `A+` Certification & `21/21` `v1.1.3` Fleet Rollout: Upgraded all `21` active downstream consumer workspaces (`10` Co-Agent desks + `11` product/tooling workspaces) from `v0.8.2` to `v1.1.3` via two-pass `./aim update --source ~/aim-joshua --skip-deps` + reader-safe `./aim index`, certified `IN_SYNC` by `aim-auditor` (`5,549` clean LanceDB fragments, `14` live MCP servers), consolidated `memory-wiki/` (`90356519`), and sealed session `c0ebd30d` | ✅ SHIPPED |
| c0ebd30d | #132, #134, #135 (`v1.1.3`, `55982475`): Fixed `VectorBackend(path=lance_dir)` in `heartbeat.py` (`./aim health` `rc=0`), `VectorBackend.compact()` + `--immediate`/`[days]` (`./aim clean` `rc=0`), `rc=1` on missing/corrupt `history.db` (`audit`/`recall`), Day-0 baseline commit in `bootstrap_install.py`, unborn-`HEAD` guard in `cmd_fix`, `-uno` root-dirty gate in `cmd_promote`, `(goto) 2>nul` batch unwinding in `aim.cmd`, `--vessel-root` across all 4 `*-blackbox` commands, and unmocked subprocess CLI E2E suite (`66/66` dual-OS pytest, `0` warnings) | ✅ SHIPPED |
| c0ebd30d | #127–#135 (`v1.1.2`, `f26e4e3c`): Remediated all 9 Pass 12 EGM Cold-Reader tickets — host-safe `cmd_uninstall`/`cmd_purge`, `windows-latest` CI leg, unified `AIM_ROOT = OS_ROOT`, `.lance.lock` + `sql_quote()` + explicit `db_path` isolation + cached offline 768-dim vectors, session-scoped `opencode-blackbox` + WAL `history.db` + shrink-overwrite guard, 28-file zombie purge + `COMMAND_HANDLERS` parity, clean-worktree/local-only `promote`, and release-pinned `safe_extract_zip()` `update` | ✅ SHIPPED |
| b1b9864e–c0ebd30d | #116–#126 (`v1.1.0`–`v1.1.1`, `2207caf4` / `84949726`): Shipped pure-Python `bootstrap_install.py` + `install*.ps1`/`install*.sh` shims, 6-harness `register_mcp.py`, dual AGY 2.0 (`~/.gemini/antigravity`) + CLI resolvers, single-batch `upsert_fragments` + `FTS(with_position=True)`, sanitized FTS5 `search-sessions`, and archived `BrianV1981/agy-joshua` | ✅ SHIPPED |
| 2e735b20 | #115 (`v1.0.0`, `480511b0` / `9ecaf496`): Inaugural SemVer GA release, `test_semver_ga_posture()`, strict OS-kernel `memory-wiki/` scope, and single standardized `aim-ecosystem` hub link | ✅ SHIPPED |
| `v0.8.x` Era | #98–#114 (`v0.8.0`–`v0.8.10` — see `CHANGELOG.md`, `memory-wiki/index.md`, & verbatim archive in `#136`): Windows `aim.ps1`/`aim.cmd` launchers, direct-to-`main` `memory-wiki/` & `HANDOFF.md` exemption (`#101`), `AGENTS.md` == `default_AGENTS.md` lockstep (`#103`), host-path hygiene gate (`#108`), FTS5 `history.db` (`#110`), `Spoken Summary (🔊)` (`#111`–`#112`), `list_lance_tables()` (`#114`), and `27.15 GiB` cold-vault dehydration (`#113`) | 📚 ARCHIVED (`#136`) |
| `v0.7.x` Era | #74–#97 (`v0.7.x` — see `memory-wiki/pages/architecture.md` & `#136`): Two-Tier `mcp_lancedb.py` + Umbrella fallback (`#78`, `#94`), DHH Agentic Era protocols (`#84`), modular CLI (`cli_vault.py`, `cli_memory.py`, `#93`), consumer `.gitignore` + atomic `os.replace` (`#96`). **Tombstones (Never Revive):** legacy `reincarnation` module (`#74`) and `swarm` CLI routes (`#89`) are permanently purged | 📚 ARCHIVED (`#136`) |

*(Rolling-window hygiene `< 12 KB` per `#136`: keep active releases + era pointers here; full verbatim pre-`v1.1` rows vaulted in Issue `#136`, `CHANGELOG.md`, and `memory-wiki/`.)*

---

## 1. PROJECT IDENTITY
J.O.S.H.U.A. is the CLI-agnostic OS brain for A.I.M. agents: nested `joshua_os/`, GitOps worktrees, LanceDB hybrid memory, blackbox vault, GitHub Projects CLI.

### Your Knowledge Base
- `~/aim-joshua/memory-wiki/index.md` (The active LLM Wiki Index)
- `~/aim-joshua/AGENTS.md` (The sovereign agent blueprint and OS rules)
- `~/aim-joshua/memory-wiki/pages/handoff-and-retrieval.md` (Retrieval mechanics)
- `~/aim-joshua/memory-wiki/pages/architecture.md` (Two-Tier MCP Protocol)
- `~/aim-joshua/memory-wiki/pages/dhh-agentic-philosophy.md` (Core Agentic Directives)
- `~/aim-joshua/memory-wiki/pages/operations.md` (GitOps, Installers, Fleet Rollout & SemVer Release SOP)

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
- **Two-Tier Retrieval Protocol:** The retrieval architecture has fundamentally shifted. If you are operating in a modern CLI/IDE harness (like AGY), you will natively possess the `search_lancedb` internal tool. This MCP server dynamically locates the vector database using Local-First, Umbrella Subfolder Fallback, or Desktop `_os_root` Fallback (`#118`), passing explicit `db_path=` into `retriever.py` (`get_active_aim_root(db_path=...)`) without mutating global module state (`#130`) so supplemental `archive/cartridges` resolve inside the target project. If you are operating in a CLI that lacks MCP, gracefully degrade to `./aim search` (POSIX) or `.\aim.ps1 search` / `.\aim.cmd search` (Windows) — never bare `python3` on Windows (`rc=9009` Microsoft Store stub). Do not assume tools exist if they are not in your prompt.
- **Cross-Platform Installers, Launchers & Multi-Harness MCP (Linux/macOS/WSL & Windows 10/11):** Onboarding scripts (`install*.sh` and `install*.ps1` delegating to `bootstrap_install.py`), root entrypoints `./aim` (Bash), `aim.ps1` (PowerShell), and `aim.cmd` (CMD), `resolve_venv_python()`, `git_push_changes()`, and `register_mcp.py` (`agy`, `grok`, `codex`, `opencode`, `cursor`, `claude`) allow Tier 1 J.O.S.H.U.A. features to run natively across Linux, macOS, WSL, and Windows 10/11 without requiring Bash, while keeping Tier 2 (`tmux` and `bwrap`) cleanly POSIX-scoped.
- **GitOps Enforcement:** Never code on `main`. Always `aim fix <id>` to branch into a worktree sandbox.
- **Vector Ingestion (Index):** Ingestion (`bootstrap_brain.py` + `VectorBackend.upsert_fragments()`) is idempotent across re-runs using collision-free repo-relative `session_id` keys, single-pass `FTS(with_position=True)` rebuilds, and `table.optimize` compaction. Custom directories can be ingested via `aim index --dir <path>`.
- **Testing Framework (`66/66` Dual-OS Pytest):** Core Python modules (`mcp_lancedb.py`, `bootstrap_brain.py`) and all advertised CLI/GitOps/Vault entrypoints (`tests/test_v1_1_2_remediation.py`, `tests/test_v1_1_3_remediation.py`) enforce both unit tests and real unmocked subprocess CLI E2E coverage across `ubuntu-latest` and `windows-latest` under `-W error::DeprecationWarning`.
- **DHH Agentic Philosophy:** The OS now runs on outcome-oriented directives. The Operator supplies the "what/why" (the fuzzy problem), and agents determine the "how" (architecture, routing). The agent acts as an automated gatekeeper during `aim promote`, ensuring TDD and architectural rules are strictly followed before hitting main.
- **Plain-Text Ascendancy:** J.O.S.H.U.A. relies on the Unix Philosophy. All configs, wikis, and tasks must be CLI-accessible flat files (Markdown, JSON) avoiding opaque GUIs.

---

## 4. IMPLEMENTATION STRATEGY
Follow strict GitOps workflow for any future tasks:
1. `./aim bug "Title" --context "..." --failure "..." --intent "..."` to create a structured issue.
2. `./aim projects in-progress <id>` (Board is `#7` via local `CONFIG.json`)
3. `./aim fix <id>`
4. Work in the `workspace/issue-<id>` worktree.
5. `./aim push "Fix: ..."` (Ensure `git add` is used for untracked files).
6. `../../aim promote` (from inside clean `workspace/issue-<id>`)
7. `./aim projects done <id>`

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
- **Strict OS Kernel Scope & Single `aim-ecosystem` Pointer:** Keep `aim-joshua/memory-wiki/` and `HANDOFF.md` strictly scoped to the J.O.S.H.U.A. OS kernel — never ingest sibling or client repository domain lore here (each sibling repo maintains its own `memory-wiki/`). In `README.md` and release notes, point external readers to the single standardized `aim-ecosystem` hub rather than hardcoding evolving sibling repository lists.
- **Live MCP Reader-Safe Indexing & Unmocked CLI Gate:** Never run `./aim clean --immediate` on live consumer workspaces while sibling agent sessions hold open `mcp_lancedb.py` stdio readers (use `./aim index`, which retains 5 minutes of manifests safely). All new CLI entrypoints must include real unmocked subprocess Pytest tests (mocking `subprocess.run` previously masked `health`/`clean` defects in Pass 13). All `21` active consumer workspaces are now converged on `v1.1.3` (so future `v1.1.3 -> v1.1.4+` consumer upgrades only require a single `./aim update` pass).

---

## 6. KEY PATHS
- `~/aim-joshua/joshua_os/` (`install*.sh`, `install*.ps1`)
- `~/aim-joshua/aim`, `~/aim-joshua/aim.ps1`, `~/aim-joshua/aim.cmd` (Cross-Platform Launchers)
- `~/aim-joshua/memory-wiki/`
- `~/aim-joshua/joshua_os/.aim_core/bootstrap_install.py` & `register_mcp.py`
- `~/aim-joshua/joshua_os/.aim_core/mcp_lancedb.py`
- `~/aim-joshua/joshua_os/.aim_core/retriever.py`
- `~/aim-joshua/tests/` (`66/66` Pytest Coverage on Linux + Windows, `0` Warnings)
- `~/aim-joshua/joshua_os/.aim_core/aim_cli.py` (CLI Router)

---

## 7. THE FULL PICTURE / WHAT COMES AFTER
All `21` active consumer workspaces are converged on `v1.1.3`, and cross-OS inter-agent messaging in `aim-skill-library` (`aim-communicate` `v2.0`) is aligned with `aim-mailbox`. Primary ongoing directive is maintaining codebase parity, dual-OS CI stability, and strict OS-kernel hygiene.

---

## 8. OPERATOR PREFERENCES
- **Worktree Discipline:** Explicit adherence to `git worktree` isolation is non-negotiable (`aim fix`).
- **Kanban Discipline:** All tasks must be claimed natively via `aim projects in-progress`.
- **CLI-Agnosticism:** Ensure all features gracefully degrade so headless, non-MCP agents can still operate the OS.
- **Elevated Operator Role:** When interacting with the Operator, NEVER ask for syntax or mechanical help. Only ping the Operator for high-level "taste", design, or business logic decisions.
- **Outcome-Oriented Directives:** Do not demand prescriptive step-by-step paths from the Operator. Solve the fuzzy problem autonomously.

---

## 9. IMMEDIATE NEXT STEPS
1. Run `./aim doctor && ./aim health && ./aim projects board` to verify baseline health and inspect Project `#7` (`0` open issues at closeout).
2. Read `memory-wiki/index.md` and await the Operator's next outcome-oriented directive, then claim and isolate work via `./aim bug` -> `./aim projects in-progress <id>` -> `./aim fix <id>`.
