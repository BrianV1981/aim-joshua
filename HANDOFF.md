# J.O.S.H.U.A. — Engineering Handoff

> **Updated:** 2026-11-28T06:00:00Z
> **Updated by:** OpenCode (deepseek-flash, session `ses_dedc690adffetv1kmeP4M0FvVV`)
> **Priority Mission:** Epic `#142` P0s — `#156` (zero-vector guard) + `#173` (doctor embedding probe) SHIPPED on `main` (`2aac1673`, `99/99`, Ubuntu+Windows CI green). Epic `#181` scoped migrations all CLOSED; auditor E2E report sent (`thr_8833d4ec85eb`); private/live-vertical tickets filed as board Backlog (`#182`, `aim-youtube#23`, `aim-gbp#1`). Next: `#150` atomic engine rollback, `#154` incremental upsert, `#159` packaging (`#143` still approval-gated).
> **Operator:** Brian Vasquez (`@BrianV1981` / `brianv1981@gmail.com`)

---

## 0. COMPLETED WORK (DO NOT REVISIT)
| Session | Work | Status |
|---------|------|--------|
| 2026-11-28 P0s | Epic `#142`: `#156` zero-vector guard (offline `aim index` refuses `[0.0]*768`, exits `1`, new `--allow-lexical-only` opt-in) + `#173` doctor embedding probe (`probe_embedding_provider`, `--fix` shebang/mailbox repair, `--strict` exit codes); `2aac1673`, dual-OS smoke + gitleaks green, `99/99` pytest; board Done. | ✅ SHIPPED |
| 2026-11-28 E2E | #181 scoped migrations completed: `aim-connect#319` CLOSED (`d84638e`, WS submit via `amail --driver tmux` Enter-only/zero Escape + `/api/swarm/activity` reads Maildir, `160/160`), `aim-office#33` CLOSED (`3b2e7d1`, UI relabel, `22/22` Vitest + `3/3` pytest), `aim-google#21` CLOSED (PR `#22`, README footer → `aim-mailbox`, all CI green, WIP `docs/ecosystem-aim-codex` untouched); shared engine synced `v1.2.1`; auditor new-thread E2E report sent (`thr_8833d4ec85eb`), original dispatch ACKed. | ✅ SHIPPED (awaiting auditor E2E) |
| ca771035→e0dc4bff | #181 (kernel + fleet sweep, `v1.2.1`, `90/90`, Ubuntu+Windows CI green): A-Mail (`amail` / `aim-mail`, `aim-mailbox` `v0.3.0`) is the sole transport; `AGENTS.md` + `default_AGENTS.md` §8c, `FLEET_ORCHESTRATION.md` §4, README, non-blocking `aim doctor` checks, `tests/test_issue_181_amail.py`. `aim-mailbox#19` (`8f78f91`), `aim-skill-library#35` (`043d462`, PR `#36`), `aim-coagents#20` (`ed5a892`, §6/§7 DNA preserved); public docs in `aim-ecosystem` / `aim-browser` / `aim-flight-recorder` / `aim-calc-skill` / `aim-cron-dashboard` / `aim-memory` / `aim-calendar` / `aim-office`; 6 specialist desks registered in both mailboxes; auditor status reply delivered. Open migrations: `aim-connect#319`, `aim-office#33`, `aim-google#21`; private/live verticals deferred. | 🚧 IN PROGRESS (E2E) |
| 4a9a6f6a | #141 (`b9ea4f70` / `84d65321` / `4a9a6f6a`, GHA Ubuntu + Windows smoke & Gitleaks `success`, `85/85` dual-OS pytest, `0` warnings): Replaced last-writer-wins per-project MCP registration with one shared versioned engine at `~/.aim/engine` (`aim_engine.py`; dedicated venv, `VERSION`, `engine.json`, downgrade guard, `CONFIG.json` exclusion, requirements-hash venv reuse) registered across AGY/Grok/Codex/OpenCode/Claude with `registration.json` provenance. `mcp_lancedb.py` now resolves `<workspace>/joshua_os/memory_lance` strictly and fails closed with `[NO PROJECT MEMORY DB]` (removed #118 Rule 3 fallback), adds `AIM_MEMORY_DB` / `AIM_UMBRELLA_SCAN=1` escape hatches and `DB: <path>` provenance. Wired installers, `./aim update`, `./aim doctor`, TUI, and new `./aim engine status|sync`; added `tests/test_shared_engine.py`, `tests/conftest.py` engine isolation, and Windows-safe test fixes. Engine installed locally and all harnesses re-registered. | ✅ SHIPPED |
| ad4cc84c | #140 (`b05512dc` / `e2633067`, GHA `45117722225` Ubuntu + Windows `success`, `74/74` dual-OS pytest, `0` warnings): Fixed multi-repo issue-number collisions in `aim_projects.py` (`_repos_match()` exact segment equality, `content.url` & `remote.origin.url` repo resolution, `limit=500` board scans, `shutil.which("gh")` Windows `PATHEXT` resolution, and `_ensure_utf8_stdio()` `cp1252` UTF-8 safety), added unit + unmocked CLI subprocess E2E tests (`tests/test_issue_140_projects_multirepo.py`), shipped paired satellite upgrades (`BrianV1981/aim-browser#14` & `#15`, `45/45` Jest, GHA `45284432934` `success`) while keeping `aim-joshua/memory-wiki/` pure OS-kernel (`e37f3a2d`), and sealed session `ad4cc84c` | ✅ SHIPPED |
| afc18927 | #137, #138, #139 (`v1.1.4`, `441a840e`, GHA `44977104811` Ubuntu + Windows & `44977104321` Gitleaks `success`, GitHub Release `v1.1.4` published): Removed hardcoded `agy-3.1-flash-lite-preview` override in `reasoning_utils.py`, added `agy-*` -> `gemini-*` REST model mapping + `"openai-api-key"` alignment + `rc=1` synthesis error exits (`audit`/`recall`), wired `output_dimensionality=768` / `dimensions=768` in `forensic_utils.py` + UTC/relpath `aim_bake.py` + alphanumeric/sentence-case Tantivy BM25 in `lance_backend.py`, added `repair_venv_shebangs()` (`32` host venv scripts repaired) + `archive-*` / `--include-local` `prune-remote` + dynamic `VERSION` in `aim_init.py` (`71/71` dual-OS pytest, `0` warnings), published Nov 2026 ecosystem audit to `aim-knowledge` (`e6abdb7`), and sealed session `afc18927` | ✅ SHIPPED |
| ffa01d2f | #136 (`badcb829`, GHA `44696621963` `success`): Vaulted verbatim pre-compaction `HANDOFF.md` (`21,692` bytes, `SHA-256: 8d5e209c...`) in Issue `#136`, executed surgical rolling-window compaction (`21.7 KB -> 14.1 KB`, `143 -> 116` lines, `10/10` `§5` traps preserved), aligned `aim-skill-library` (`aim-communicate` `v2.0`, `#19`/`#24`) + `aim-mailbox` (`v0.1.1`) + `aim-ecosystem`, and sealed session `ffa01d2f` to Blackbox Vault | ✅ RESOLVED |
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

## 2. YOUR MISSION: ACT ON AUDITOR E2E, THEN EPIC #142
Epic `#181` scoped migrations are **complete** (`aim-connect#319`, `aim-office#33`, `aim-google#21` all CLOSED); the E2E completion report is with `aim-auditor` (thread `thr_8833d4ec85eb`). Do **not** start `#143` without explicit Operator approval and a `git bundle` backup.

### Execution Queue (in order)
1. **Await/act on auditor E2E:** check `aim-mail inbox aim-joshua` for findings; fix in the owning repo via worktree, then re-report. Keep `#181` open until the auditor certifies.
2. **Private/live follow-ups (board Backlog):** `#182` (local specialist desks AGENTS/TOOLS/cron), `aim-youtube#23` (README/template), `aim-gbp#1` (AGENTS.md). Never wake the DND-protected live vertical or edit `aim-auditor`.
3. **Remaining Epic `#142` P0s:** `#150` atomic engine rollback, `#154` incremental upsert, `#159` packaging (`#156`/`#173` are shipped; `#143` still approval-gated).
---

## 3. DETAILED ANALYSIS / BREAKDOWN
- **Two-Tier Retrieval Protocol:** The retrieval architecture has fundamentally shifted. If you are operating in a modern CLI/IDE harness (like AGY), you will natively possess the `search_lancedb` internal tool. This MCP server dynamically locates the vector database using Local-First, Umbrella Subfolder Fallback, or Desktop `_os_root` Fallback (`#118`), passing explicit `db_path=` into `retriever.py` (`get_active_aim_root(db_path=...)`) without mutating global module state (`#130`) so supplemental `archive/cartridges` resolve inside the target project. If you are operating in a CLI that lacks MCP, gracefully degrade to `./aim search` (POSIX) or `.\aim.ps1 search` / `.\aim.cmd search` (Windows) — never bare `python3` on Windows (`rc=9009` Microsoft Store stub). Do not assume tools exist if they are not in your prompt.
- **Cross-Platform Installers, Launchers & Multi-Harness MCP (Linux/macOS/WSL & Windows 10/11):** Onboarding scripts (`install*.sh` and `install*.ps1` delegating to `bootstrap_install.py`), root entrypoints `./aim` (Bash), `aim.ps1` (PowerShell), and `aim.cmd` (CMD), `resolve_venv_python()`, `git_push_changes()`, and `register_mcp.py` (`agy`, `grok`, `codex`, `opencode`, `cursor`, `claude`) allow Tier 1 J.O.S.H.U.A. features to run natively across Linux, macOS, WSL, and Windows 10/11 without requiring Bash, while keeping Tier 2 (`tmux` and `bwrap`) cleanly POSIX-scoped.
- **GitOps Enforcement:** Never code on `main`. Always `aim fix <id>` to branch into a worktree sandbox.
- **Vector Ingestion & 768-Dim Provider Parity (Index):** Ingestion (`bootstrap_brain.py` + `VectorBackend.upsert_fragments()` + `forensic_utils.get_embedding()`) is idempotent across re-runs using collision-free repo-relative `session_id` keys, `768`-dim output config across Ollama/Google/OpenAI, alphanumeric Tantivy `FTS(with_position=True)` queries, and `table.optimize` compaction. Custom directories can be ingested via `aim index --dir <path>`.
- **Testing Framework (`90/90` Dual-OS Pytest):** Core Python modules (`mcp_lancedb.py`, `bootstrap_brain.py`, `reasoning_utils.py`, `aim_projects.py`) and all advertised CLI/GitOps/Vault entrypoints (`tests/test_v1_1_2_remediation.py`, `tests/test_v1_1_3_remediation.py`, `tests/test_v1_1_4_remediation.py`, `tests/test_issue_140_projects_multirepo.py`) enforce both unit tests and real unmocked subprocess CLI E2E coverage across `ubuntu-latest` and `windows-latest` under `-W error::DeprecationWarning`.
- **DHH Agentic Philosophy:** The OS now runs on outcome-oriented directives. The Operator supplies the "what/why" (the fuzzy problem), and agents determine the "how" (architecture, routing). The agent acts as an automated gatekeeper during `aim promote`, ensuring TDD and architectural rules are strictly followed before hitting main.
- **Plain-Text Ascendancy:** J.O.S.H.U.A. relies on the Unix Philosophy. All configs, wikis, and tasks must be CLI-accessible flat files (Markdown, JSON) avoiding opaque GUIs.

- **A-Mail Fleet Rollout (`#181`, scoped migrations complete):** Kernel + `aim-mailbox#19` + `aim-skill-library#35` + `aim-coagents#20` + public docs landed; `aim-connect#319` (`d84638e`, amail `--driver tmux` Enter-only + Maildir activity feed), `aim-office#33` (`3b2e7d1`, UI relabel), and `aim-google#21` (PR `#22`, README footer) CLOSED. Only private/live-vertical follow-ups remain — file as tickets, never mid-batch.
- **OpenCode Skill UX (discovery):** Skills are **not** slash commands. `opencode debug skill` lists IDs; invoke via `@<id>` as plain text, natural language ("use the `aim-handoff` skill"), or a custom `commands/*.md` wrapper. The library's `Slash: /aim-*` text is aspirational; no command files are installed. `handoff_pulse_generator.py` is the `./aim handoff` pulse CLI, **not** the `aim-handoff` skill.
- **Shared Engine (in sync):** The shared MCP engine is now `v1.2.1`, matching this project; re-run `./aim engine sync` after any version bump. The MCP DB contract is unchanged.


---

## 4. IMPLEMENTATION STRATEGY
Follow strict GitOps workflow for any future tasks:
1. `./aim bug "Title" --context "..." --failure "..." --intent "..."` to create a structured issue.
2. `./aim projects in-progress <id>` (Board is `#7` via local `CONFIG.json`)
3. `./aim fix <id>`
4. Work in the `workspace/issue-<id>` worktree.
5. `./aim push "Fix: ..."` (Ensure `git add` is used for untracked files).
6. `../../aim promote` (from inside clean `workspace/issue-<id>`) followed by `./aim prune-remote --confirm --include-local` after CI is green.
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
- **Live MCP Reader-Safe Indexing & Unmocked CLI Gate:** Never run `./aim clean --immediate` on live consumer workspaces while sibling agent sessions hold open `mcp_lancedb.py` stdio readers (use `./aim index`, which retains 5 minutes of manifests safely). All new CLI entrypoints must include real unmocked subprocess Pytest tests (mocking `subprocess.run` previously masked `health`/`clean` defects in Pass 13). **Current fleet inventory (2026-11-26):** `42` project roots carry `joshua_os/.aim_core` — `22` on `v1.1.3`, `14` on `v0.8.2` (mostly `aim-connect/agent_workspaces/*` session nodes), `1` on `v1.2.1` (this repo) and `2` on `v1.1.4`, `2` on `v1.0.7`, and `1` on `v1.0.8` (plus inactive `aim-cron-dashboard.bak`). The shared MCP engine (`~/.aim/engine`, `v1.1.4`) serves every project's own DB regardless of that project's engine version; per-project `./aim update` is still required for CLI/GitOps parity. Separately, `build_engine_venv()` (`repair_venv_shebangs()`) automatically heals stale POSIX `venv/bin` shebangs after directory moves. **Shared MCP engine (`#141`):** the server code lives once at `~/.aim/engine` (override `AIM_ENGINE_ROOT`); never register a project-local `mcp_lancedb.py` path or reintroduce an engine/other-project DB fallback. `./aim engine status|sync` manages it, `AIM_MEMORY_DB` is the only explicit DB override, and `AIM_UMBRELLA_SCAN=1` is the only cross-project read (opt-in, read-only).

- **OpenCode Skills ≠ Slash Commands:** The TUI `/` menu lists commands, not skills. Use `opencode debug skill` to list IDs, then `@<id>` (plain text, do not pick a `.py`/`.md` file from the picker) or ask by name. `handoff_pulse_generator.py` is the `./aim handoff` pulse generator, not the `aim-handoff` skill. Slash wrappers are a pending UX fix.
- **A-Mail E2E Pending Auditor Sign-off:** Scoped code migrations are CLOSED and green, but `#181` stays open until `aim-auditor` certifies the E2E pass. Do not close the epic on the strength of the self-report alone.
- **Shared Engine Sync:** `~/.aim/engine` is now `v1.2.1` (matches repo); re-run `./aim engine sync` after any version bump. Do not register project-local `mcp_lancedb.py` paths.
- **Offline Index Is Fail-Closed Now (`#156`):** `./aim index` refuses to write zero-vector fragments when embeddings are offline and exits `1`; pass `--allow-lexical-only` only when FTS-only retrieval is acceptable. Do not "fix" the new error by disabling the guard. Re-index online (or with the opt-in) to heal the pre-existing ~19 zero-norm fragments.

---

## 6. KEY PATHS
- `~/aim-joshua/joshua_os/` (`install*.sh`, `install*.ps1`)
- `~/aim-joshua/aim`, `~/aim-joshua/aim.ps1`, `~/aim-joshua/aim.cmd` (Cross-Platform Launchers)
- `~/aim-joshua/memory-wiki/`
- `~/aim-joshua/joshua_os/.aim_core/bootstrap_install.py` & `register_mcp.py`
- `~/aim-joshua/joshua_os/.aim_core/mcp_lancedb.py`
- `~/aim-joshua/joshua_os/.aim_core/retriever.py` & `reasoning_utils.py`
- `~/aim-joshua/artifacts/AUDIT_ROADMAP_2026-11-26.md` (Epic `#142` audit packet: 37 tickets, evidence, sequencing, auditor prompt)
- `~/aim-joshua/tests/` (`90/90` Pytest Coverage on Linux + Windows, `0` Warnings)
- `~/aim-joshua/joshua_os/.aim_core/aim_cli.py` & `aim_projects.py` (CLI Router & Multi-Repo Kanban GitOps)
- `~/.config/opencode/skills/` (global skill symlinks) + `~/aim-skill-library/vessels/opencode/manifest.txt`
- `~/.aim/engine/` (shared MCP engine) + `$AIM_MAILBOX_DIR` (A-Mail Maildir; WSL default `/mnt/c/Users/<user>/.aim/mailbox`)

---

## 7. THE FULL PICTURE / WHAT COMES AFTER
Upstream `aim-joshua` is clean on `main` (`v1.2.1`, `99/99` dual-OS pytest) and the shared MCP engine is synced to `v1.2.1`. A-Mail (`amail` / `aim-mail`, `aim-mailbox` `v0.3.0`) is the sole transport (`AGENTS.md` §8c); **all scoped migrations are CLOSED** (`aim-connect#319`, `aim-office#33`, `aim-google#21`), leaving only board-Backlog private/live-vertical follow-ups. `aim-auditor` holds the E2E pass on thread `thr_8833d4ec85eb`. Epic `#142` P0s `#156`/`#173` shipped, so offline indexing is now fail-closed and `aim doctor` probes the embedding provider; remaining P0s are `#150`, `#154`, `#159` (`#143` approval-gated).

---

## 8. OPERATOR PREFERENCES
- **Worktree Discipline:** Explicit adherence to `git worktree` isolation is non-negotiable (`aim fix`).
- **Kanban Discipline:** All tasks must be claimed natively via `aim projects in-progress`.
- **CLI-Agnosticism:** Ensure all features gracefully degrade so headless, non-MCP agents can still operate the OS.
- **Elevated Operator Role:** When interacting with the Operator, NEVER ask for syntax or mechanical help. Only ping the Operator for high-level "taste", design, or business logic decisions.
- **Outcome-Oriented Directives:** Do not demand prescriptive step-by-step paths from the Operator. Solve the fuzzy problem autonomously.

---

## 9. IMMEDIATE NEXT STEPS
1. Run `./aim doctor && ./aim engine status && ./aim health && ./aim projects board`; the shared engine is already synced to `v1.2.1` (re-sync only after a version bump). `./aim doctor` now probes embeddings; use `--strict` for CI-grade gating and `--fix` for shebang/mailbox repair.
2. Check A-Mail (`aim-mail inbox aim-joshua --state active`) for `aim-auditor` E2E findings on thread `thr_8833d4ec85eb`; fix any finding in the owning repo via worktree and re-report.
3. Work the private/live follow-ups from the board Backlog (`#182`, `aim-youtube#23`, `aim-gbp#1`) without waking the DND vertical.
4. Close `#181` only after `aim-auditor` certifies the E2E pass.
5. Continue Epic `#142` P0s: `#150` atomic engine rollback, `#154` incremental upsert, `#159` packaging (`#143` approval-gated).
