# J.O.S.H.U.A. — Roadmap Audit Packet (Epic #142)

> **Status:** DRAFT FOR EXTERNAL AUDIT — not yet acted on.
> **Created:** 2026-11-26 (UTC)
> **Prepared by:** OpenCode (deepseek-flash) at the Operator's request
> **Scope:** The 37 recommendations opened as Epic [#142](https://github.com/BrianV1981/aim-joshua/issues/142) + child issues #143–#179, derived from a repository review on 2026-11-26.
> **Repository:** `BrianV1981/aim-joshua` @ `main` (`v1.1.4`, commit `378640d9` at time of writing; `#141` shipped)
> **Audience:** An independent reviewing agent. Everything needed to challenge the findings is in this file; no prior context should be assumed.

---

## 0. How to use this document

1. Read §1–§6 for context, method, and the claims most likely to be wrong.
2. Audit the 37 tickets in §9. Each has **Problem / Evidence / Acceptance / Dependencies / Risk if skipped / Auditor question**.
3. Use §10 to challenge sequencing, §11 to challenge risk ranking, and §13 to reproduce the measurements on your own machine.
4. Return: per-ticket verdict (`accept` / `revise` / `reject` / `defer`), corrections with evidence, and any missing recommendations.
5. Do **not** execute destructive steps (especially `#143`). This packet authorizes review only.

A copy-paste auditor prompt is in §15.

---

## 1. Executive summary

J.O.S.H.U.A. is a **harness-agnostic OS layer** for AI coding agents: per-project memory (LanceDB hybrid search), GitOps worktree enforcement, encrypted session forensics, and GitHub Projects plumbing. It is not an agent and deliberately has no reasoning loop or sandbox.

**Current posture (verified 2026-11-26):**

| Item | Value |
|---|---|
| Version | `v1.1.4` (MIT, created 2026-07-24) |
| Engine size | ~11,967 Python LOC across 32 modules, 30 CLI commands |
| Tests | 85 collected / ~3,487 test LOC, Ubuntu + Windows CI, 0 warnings |
| Shared MCP engine | `~/.aim/engine` `v1.1.4`, 5 harnesses registered (`agy`, `grok`, `codex`, `opencode`, `claude`); Cursor absent |
| Local project installs | 42 roots (mixed versions: 22× `v1.1.3`, 14× `v0.8.2`, 3× `v1.1.4`, 2× `v1.0.7`, 1× `v1.0.8`) |
| Adoption | ~3 GitHub stars, 0 forks, effectively 1 human maintainer |
| Repository pack | ~314 MiB (history contains legacy large blobs) |
| Distribution | No `pyproject.toml`, no PyPI, no Docker; `curl \| bash` + zip updater |
| Retrieval evidence | Local LoCoMo V2 run: 178/199 (89.4%) raw, 191/199 (96.0%) adjusted — **older RAG 5.0 pipeline, not the current engine** |

**Three findings that outrank the rest:**

1. **Trust debt:** `main`'s git history still contains large legacy memory/transcript/benchmark blobs (~24 MB DB, 2× ~21 MB JSONL, 15 MB + 13 MB session JSON). The working tree is clean, but every clone downloads them and the data remains recoverable. `#143`.
2. **New single point of failure:** the shared MCP engine (shipped in `#141`) updates by deleting the old code before copying the new. An interrupted update breaks search for every project at once. `#150`.
3. **Scaling ceiling:** every index run loads the entire vector table into Python and rewrites it. Fine at 155 chunks, untenable at 10k+. `#154`.

**The macro judgment:** code quality is better than adoption suggests; the ceiling is discoverability (no package/demo/benchmark) plus operational sharp edges (silent failures, timeouts, unpinned updater).

**Confidence:** high on measured code/history facts; medium on effort estimates; low on community/market claims (no telemetry, 3 stars).

---

## 2. What the product is (for an auditor with no context)

- **No agent loop.** It never calls an LLM to act. It supplies memory, Git hygiene, and forensics to whatever harness the Operator uses (Antigravity, Grok, Codex, OpenCode, Claude Code, Cursor).
- **Two-tier retrieval.** Preference order: native MCP tool `search_lancedb` → CLI fallback `./aim search` → project venv Python. If no MCP, agents must still work.
- **Per-project memory, one engine.** Since `#141`, one versioned engine at `~/.aim/engine` serves all projects; the database is always `<workspace>/joshua_os/memory_lance` and the server **fails closed** when absent (no borrowing another project's DB).
- **GitOps.** Application changes happen in `workspace/issue-<id>` worktrees (`./aim fix`), then `./aim promote`. Memory-state files (`memory-wiki/**`, `HANDOFF.md`) are deliberately exempt and push directly to `main`.
- **Forensics.** Per-harness session sealers write Fernet-encrypted transcripts to a vault; a SQLite FTS5 notebook indexes session text.
- **Deterministic memory writes.** Ingestion is Python-only (SHA-256 chunk identity, `(session_id, sha256)` vector cache). No LLM sorts or rewrites the vector DB. This is a deliberate safety property; the audit should flag any recommendation that violates it.

---

## 3. Scope and non-goals

**In scope:** the 37 tickets in §9, their evidence, priority, size, sequencing, and acceptance criteria.

**Out of scope (deliberate):**
- Building an agent loop, hosted SaaS, or multi-tenant auth.
- LLM-based memory extraction, entity graphs, or temporal/bi-temporal graphs. These require an LLM to decide what to store; the Operator rejected that risk model. `git` + curated wiki + session search already provide temporal provenance.
- Rewriting the CI, test framework, or storage engine from scratch.
- The history rewrite in `#143` — it is documented, not authorized.

---

## 4. Method and evidence provenance

All findings were derived from the local checkout on 2026-11-26 using read-only inspection:

| Method | Used for |
|---|---|
| `git` plumbing (`rev-list`, `cat-file`, `count-objects`, `log`) | History blobs, reachability, pack size, leak guards |
| Python AST over `joshua_os/` | `except` handlers, silent swallows, `subprocess.run` without `timeout` |
| Direct source reads | Memory engine, MCP server, registration, updater, CLI |
| GitHub REST/GraphQL (`gh`) | Stars, versions, open issues, project board |
| Local execution | `./aim doctor`, `./aim health`, `./aim engine status`, MCP resolution, fail-closed checks |
| SQLite queries | Session DB (138 sessions, 47,903 parts, 7,838 tool calls) for MCP usage |
| LanceDB reads | Fragment counts, zero-vector detection, per-project DB resolution |
| Local benchmark artifacts | LoCoMo results (held outside the repo) |

**Environment:** Linux, Python 3.12.3, `gh` authenticated. CI matrix is `ubuntu-latest` + `windows-latest` on Python 3.12 only.

**Confidence labels used below:**
- **High** — directly measured in this checkout or in current CI.
- **Medium** — derived from code reading or a single sample; may vary per machine.
- **Low** — inference, external comparison, or market judgment.

---

## 5. Claims to stress-test first

These are the load-bearing claims. If one is wrong, several tickets change priority.

| # | Claim | How measured | Caveat / why challenge it | Confidence |
|---|---|---|---|---|
| C1 | Legacy memory/transcript/benchmark blobs are reachable from `main` | `git rev-list --objects main` + `git cat-file --batch-check` | Paths are historical; the working tree is clean. Verify whether your threat model treats public history as exposure. | High |
| C2 | Repository pack is ~314 MiB | `git count-objects -vH` | Includes all refs; after clone, size may differ if the server repacks. | High |
| C3 | 61 `except: pass` and 93 `subprocess.run` calls without timeout | AST script in §13 | Counting heuristic; some are intentional best-effort paths. Judge by blast radius, not raw count. | High |
| C4 | Every index rewrites the full table | Code read `lance_backend.py` `upsert_fragments()` | Correct for current code; confirm on your LanceDB version whether delete+add is safe under the existing file lock. | High |
| C5 | 19/155 fragments in this repo have zero vectors | NumPy norm over the local DB | Repo-specific. Other installs may differ; the mechanism (offline embeddings) is what matters. | High |
| C6 | 0 MCP `search_lancedb` calls in 138 recorded sessions | OpenCode SQLite `part` table scan | Only covers one harness's local history; other harnesses are not equally greppable. Absence of evidence, not proof of no use anywhere. | Medium |
| C7 | 42 local project roots | `find` for `joshua_os/.aim_core` | Includes 14 ephemeral `aim-connect` workspace nodes; the count may fluctuate. | High |
| C8 | LoCoMo 89.4% raw / 96.0% adjusted | Local benchmark report | Produced on an older RAG 5.0 pipeline in May 2026, **not** the current `v1.1.4` engine. Directional only; re-run before publishing. | Medium |
| C9 | No packaging / no coverage / no lint/type gates | Direct inspection + import checks | Trivially verifiable; challenge whether it matters for this audience. | High |
| C10 | Updater can fall back to `main.zip` | Source read `aim_cli.py` `_resolve_remote_update_zip_url()` | Fallback occurs only when the release API fails; still a moving target. | High |

---

## 6. Deliberately rejected recommendations

Documented so the auditor does not re-propose them without addressing the reason:

1. **Temporal knowledge graphs** (Graphiti/Zep-style) — requires LLM entity extraction and contradiction resolution; violates the "no LLM writes memory" property. `git` + curated wiki + transcript search already answer "what was true when".
2. **LLM-based memory extraction/dedup** — same risk. Dedup stays deterministic (hash, and optionally cosine threshold in Python).
3. **A `./aim fleet` CLI** — previously evaluated and rejected as parser-fragile; heterogeneous repos are handled by an orchestrating agent + per-repo `./aim update`.
4. **Replacing the harness** — the project's value is being harness-agnostic; do not compete with the 100k-star agents.
5. **Mandatory sandboxing by default** — proposed as opt-in (`#178`); forcing Docker would break the zero-dependency local mode.

---

## 7. Scoring rubric

| Priority | Meaning |
|---|---|
| **P0** | Trust, data loss, global outage, or blocks adoption. Do before feature work. |
| **P1** | Material improvement to reliability, correctness, or discoverability. |
| **P2** | Valuable but deferrable; unlocks scale or polish. |
| **P3** | Cleanup / hygiene. |

| Size | Rough effort |
|---|---|
| **S** | ≤ 1 focused session (hours), small diff, low coordination |
| **M** | 1–3 sessions, multi-file, needs tests |
| **L** | Multi-session, cross-cutting, migration or destructive component |

---

## 8. Epic and board state

- **Epic:** [#142 — v1.2 hardening](https://github.com/BrianV1981/aim-joshua/issues/142)
- **Children:** #143–#179 (37 issues, all open).
- **Board:** Project `#7` (`@BrianV1981`), all 38 items added; most sit in **Backlog**, `#143`/`#144` in **Todo**. GitHub GraphQL rate limits blocked promoting the remaining P0s at creation time; this is bookkeeping only.
- **Labels created:** `epic`, `security`, `reliability`, `performance`, `memory`, `packaging`, `ci`, `tests`, `ux`, `observability`, `docs` (plus existing `enhancement`, `documentation`).
- **Source of truth for acceptance:** each GitHub issue body. If this packet and an issue disagree, the issue wins; flag the discrepancy.

---

## 9. Ticket catalog

Legend: **P/S** = priority/size. Links point to GitHub. "Auditor question" is the specific thing to challenge.

### 9.1 Security & supply chain (#143–#147)

#### #143 · security(history): purge private session data from git history
- **P/S/L:** P0 · L · `security`
- **Problem:** The working tree is clean, but `main`'s history still carries legacy memory/transcript/benchmark blobs. Every clone downloads them; deleted data remains recoverable from history.
- **Evidence (High):** `git rev-list --objects main` shows a ~24 MB memory DB, 2× ~21 MB transcript JSONL, 15 MB + 13 MB raw session JSON, plus benchmark logs. Pack ≈ 314 MiB. Prior commits are named as leak purges, but history was not rewritten.
- **Acceptance:** full `git bundle` backup verified; rewrite with `git filter-repo` removing legacy archive/session/benchmark paths and `*.engram` blobs; force-push; re-clone and verify no private blobs; target pack < 50 MiB; document the procedure; rotate anything that may have leaked.
- **Dependencies:** Operator approval + backup **before** execution. Coordinate with any forks (currently 0).
- **Risk if skipped:** permanent public exposure of session data, slow clones, distrust from enterprise users.
- **Auditor question:** Is history exposure actually in scope for this Operator, and is `filter-repo` safe given the 42 downstream installs that may have copied the repo?

#### #144 · security(update): fail closed instead of falling back to main.zip
- **P/S/L:** P0 · S · `security`
- **Problem:** If the release API lookup fails, `aim update` silently falls back to a moving `refs/heads/main.zip`.
- **Evidence (High):** `aim_cli.py` `_resolve_remote_update_zip_url()` returns `refs/heads/main.zip` after a bare `except Exception: pass`.
- **Acceptance:** non-zero exit when no tag resolves; explicit `--allow-main` escape hatch; verify a per-release SHA-256 manifest when present; unit test simulating API failure.
- **Dependencies:** none.
- **Risk if skipped:** a transient API error becomes an unpinned code update across trust boundaries.
- **Auditor question:** Is there a reason the fallback exists (e.g., pre-release users), and would failing closed break a documented workflow?

#### #145 · docs(security): add SECURITY.md threat model
- **P/S/L:** P1 · S · `security`, `docs`
- **Problem:** Vault, key precedence, MCP trust boundary, and update chain are security-relevant but undocumented.
- **Evidence (High):** no `SECURITY.md`; vault details live only in engine manuals.
- **Acceptance:** assets/boundaries; Fernet at-rest model; keyring vs `0600` key precedence + backup/rotation; MCP trust model + fail-closed rule; supported versions and private reporting.
- **Dependencies:** best after `#143` so the doc reflects reality.
- **Risk if skipped:** auditors and enterprise users cannot evaluate risk.
- **Auditor question:** Does documenting key precedence weaken security by revealing the fallback path?

#### #146 · ci(security): full-history gitleaks + pip-audit
- **P/S/L:** P1 · S · `security`, `ci`
- **Problem:** Secret scanning covers pushes/diffs, not older history; dependencies are not audited.
- **Evidence (High):** `.github/workflows/gitleaks.yml`; no pip-audit job; 12 of 13 requirements use `>=`.
- **Acceptance:** scheduled + manual full-history secret scan; `pip-audit` against the lockfile; fail on findings; upload reports.
- **Dependencies:** `#147` for a lockfile.
- **Risk if skipped:** regressions in history or dependencies go unnoticed.
- **Auditor question:** Will full-history scanning produce false positives that block CI, and should it be advisory first?

#### #147 · chore(deps): requirements.lock + Dependabot
- **P/S/L:** P2 · S · `security`
- **Problem:** Range-pinned dependencies are not reproducible.
- **Evidence (High):** `joshua_os/requirements.txt`: 12 `>=`, 1 `==`.
- **Acceptance:** locked file per release; CI and `build_engine_venv()` install from it; Dependabot for pip + Actions.
- **Dependencies:** feeds `#146` and `#159`.
- **Risk if skipped:** silent breakage; non-reproducible installs.
- **Auditor question:** Does a lockfile conflict with the cross-platform/venv model, and which lock tool fits (pip-tools vs uv)?

### 9.2 Reliability & failure handling (#148–#153)

#### #148 · reliability(logging): replace 61 silent `except: pass` sites
- **P/S/L:** P1 · M · `reliability`, `observability`
- **Problem:** Silent failures hid degraded search and registration problems.
- **Evidence (High):** AST audit: 223 broad handlers, 61 are `except Exception: pass`.
- **Acceptance:** logging helper → `~/.aim/logs/aim.log` with rotation; `AIM_DEBUG=1`; convert critical paths first (MCP, index, update, engine, registration).
- **Dependencies:** none.
- **Risk if skipped:** operators cannot diagnose failures; trust erodes.
- **Auditor question:** Which swallows are legitimately best-effort, and would logging every one create noise/secret leakage?

#### #149 · reliability(subprocess): add timeouts to 93 calls
- **P/S/L:** P1 · M · `reliability`
- **Problem:** A hung `git`/`gh`/`pip` freezes an agent session.
- **Evidence (High):** AST audit: 93 `subprocess.run` calls without `timeout=`.
- **Acceptance:** shared `run_cmd()` with defaults (git 120s, gh 60s, pip 900s); kill + report; tests; migrate highest-risk sites.
- **Dependencies:** interacts with `#148`.
- **Risk if skipped:** indefinite hangs in unattended use.
- **Auditor question:** Are any long-running calls legitimately unbounded (interactive editors, streaming), and would a default timeout break them?

#### #150 · fix(engine): atomic shared-engine update + rollback
- **P/S/L:** P0 · M · `reliability`
- **Problem:** The shared engine serves every project; a crash/disk-full during sync breaks MCP globally.
- **Evidence (High):** `aim_engine.py` does `shutil.rmtree(dest_core)` then `copytree(...)` in place.
- **Acceptance:** stage to temp + `os.replace`; keep `engine.prev`; `aim engine rollback`; verify imports before success; interrupted-sync test.
- **Dependencies:** extends `#141`.
- **Risk if skipped:** one failed update becomes a fleet-wide outage.
- **Auditor question:** Is `os.replace` atomic across the relevant filesystems (Windows?), and should rollback be automatic on failed health checks?

#### #151 · fix(mcp): merge registration entries
- **P/S/L:** P1 · S · `reliability`
- **Problem:** Forced registration replaces the whole server entry, dropping user `env`/`timeout`/`disabled`.
- **Evidence (High):** `register_mcp.py` upsert functions replace the entry.
- **Acceptance:** update only `command`/`args`, preserve unknown keys; tests for JSON/OpenCode/Claude/TOML.
- **Dependencies:** none.
- **Risk if skipped:** silent loss of user configuration on every sync.
- **Auditor question:** Should the tool own the whole entry (simpler) or preserve user fields (safer)? Any conflicting keys?

#### #152 · chore: replace `os.system('clear')`
- **P/S/L:** P3 · S · `reliability`
- **Problem:** Unnecessary shell-out in the TUI.
- **Evidence (High):** `aim_config.py` uses `os.system('cls' if os.name == 'nt' else 'clear')`.
- **Acceptance:** ANSI or guarded subprocess; no-op when not a TTY.
- **Dependencies:** none.
- **Risk if skipped:** trivial.
- **Auditor question:** Any terminal where ANSI is worse than the current behavior?

#### #153 · fix(push): Conventional Commits scopes
- **P/S/L:** P1 · S · `reliability`, `ux`
- **Problem:** `feat(scope):` does not bump `VERSION`; the `#141` feature shipped without a bump.
- **Evidence (High):** `aim_cli.py` only checks `startswith('feat:')`/`startswith('fix:')`.
- **Acceptance:** parse scopes, `!:` breaking, and `BREAKING CHANGE:` anywhere; table-driven tests.
- **Dependencies:** none.
- **Risk if skipped:** releases silently skip version bumps.
- **Auditor question:** Does the project want full Conventional Commits, or only the minimum scope handling?

### 9.3 Memory engine (#154–#158)

#### #154 · perf(memory): incremental upsert
- **P/S/L:** P0 · M · `performance`, `memory`
- **Problem:** Every index loads the whole table into Python and rewrites it; cost grows linearly.
- **Evidence (High):** `lance_backend.py` `upsert_fragments()`: `to_arrow().to_pylist()` then `create_table(..., mode='overwrite')`.
- **Acceptance:** delete incoming `session_id`s + append; stable fragment IDs; `optimize()` out of the hot path; 1k/10k/50k benchmark.
- **Dependencies:** must respect the existing `.lance.lock` and 5-minute reader window.
- **Risk if skipped:** large repos become unusable; RAM spikes during index.
- **Auditor question:** Is delete+add safe for concurrent MCP readers under the current lock, or is a staging table required?

#### #155 · perf(memory): cache cartridge tables
- **P/S/L:** P2 · S · `performance`, `memory`
- **Problem:** Each search reconnects `memory://` and rebuilds FTS per cartridge.
- **Evidence (High):** `lance_backend.py` search() loops per query.
- **Acceptance:** cache by `(path, mtime)`; invalidate on jack-in/unplug; latency test.
- **Dependencies:** none.
- **Risk if skipped:** every ROM query is slower than necessary.
- **Auditor question:** Is per-process caching safe when cartridges change on disk during a session?

#### #156 · fix(memory): zero-vector guard
- **P/S/L:** P0 · S · `memory`
- **Problem:** Offline embeddings write `[0.0]*768`, making chunks semantically invisible while reporting success.
- **Evidence (High):** 19/155 fragments here are zero-norm; cache preserves only non-zero vectors.
- **Acceptance:** refuse zero writes or mark `vector_status=missing`; warning + non-zero exit unless `--allow-lexical-only`; later online index heals.
- **Dependencies:** relates to `#173` (embedding probe).
- **Risk if skipped:** silent recall loss; agents see low-quality results and abandon RAG.
- **Auditor question:** Is failing the index the right UX for offline-first users, or should it warn and continue?

#### #157 · feat(memory): embedding model/dim metadata
- **P/S/L:** P1 · M · `memory`
- **Problem:** Schema is hard-locked to 768 but does not record the model, so a model switch can mix incompatible vectors.
- **Evidence (High):** fixed `list_(float32, 768)` schema; no table metadata.
- **Acceptance:** store `embedding_model`/`dim`/`built_at`; refuse incompatible model unless `--rebuild`; document re-index.
- **Dependencies:** `#154` (schema touch).
- **Risk if skipped:** silent quality collapse after a model change.
- **Auditor question:** Where should metadata live (table metadata vs a sidecar manifest) for LanceDB portability?

#### #158 · chore(memory): dead `semantic_pruning_threshold`
- **P/S/L:** P3 · S · `memory`
- **Problem:** A config key no code reads is misleading in a deterministic-dedup system.
- **Evidence (High):** only appears in config defaults; no consumer.
- **Acceptance:** implement deterministic cosine pruning with tests, or delete from config/templates/docs.
- **Dependencies:** decision needed.
- **Risk if skipped:** operator assumes semantic dedup exists.
- **Auditor question:** Is similarity pruning worth building, or does it violate determinism/reproducibility?

### 9.4 Packaging & release (#159–#162)

#### #159 · feat(packaging): pyproject + pip/uvx
- **P/S/L:** P0 · M · `packaging`
- **Problem:** No installable package; every trial starts with `curl | bash`; no PyPI/uvx discovery.
- **Evidence (High):** no `pyproject.toml`/`setup.py`.
- **Acceptance:** `pyproject.toml` with `aim` and `aim-joshua-mcp`; exclude venv/assets (<5 MB wheel); verify clean-venv install + `uvx`; publish on tag.
- **Dependencies:** `#147` lockfile; `#162` release workflow.
- **Risk if skipped:** adoption stays near zero; enterprise installs are blocked.
- **Auditor question:** How do you package an app that scaffolds into a target directory without conflicting with pip's site-packages model?

#### #160 · feat(packaging): Docker/devcontainer/Action
- **P/S/L:** P1 · M · `packaging`, `ci`
- **Problem:** Teams want container/CI-native trials.
- **Evidence (High):** no Dockerfile/devcontainer/action.
- **Acceptance:** slim image (no Ollama) with mounted workspace; devcontainer; composite action.
- **Dependencies:** `#159`.
- **Risk if skipped:** slower enterprise evaluation.
- **Auditor question:** Does the MCP server's per-workspace DB model map cleanly onto container mounts?

#### #161 · feat(packaging): registries + package managers
- **P/S/L:** P2 · M · `packaging`
- **Problem:** Discovery is the ceiling; registry listings put the server where agents look.
- **Evidence (High):** absent from MCP registry, Homebrew, winget, Scoop.
- **Acceptance:** MCP registry metadata + community directories; Homebrew tap + winget/Scoop with checksums; versioned listings.
- **Dependencies:** `#159`, `#162`.
- **Risk if skipped:** continued invisibility.
- **Auditor question:** Which registries actually drive installs for this audience, and what is the maintenance cost?

#### #162 · ci(release): tag-driven release + `default_lance` asset
- **P/S/L:** P1 · M · `packaging`, `ci`
- **Problem:** Releases are manual; the seed DB bloats git history.
- **Evidence (High):** no release workflow; `default_lance` committed.
- **Acceptance:** on tag build sdist/wheel + changelog + Release; attach `default_lance` with SHA-256; updater/installer verify it.
- **Dependencies:** `#143` (history cleanup) for best effect.
- **Risk if skipped:** inconsistent releases; continued repo bloat.
- **Auditor question:** Is a release asset acceptable for offline installs, or does it add a network dependency to bootstrap?

### 9.5 CI & tests (#163–#167)

#### #163 · ci: Python 3.10/3.13 + macOS
- **P/S/L:** P1 · S · `ci`
- **Problem:** README claims 3.10+ and macOS; CI runs 3.12 on Ubuntu/Windows only.
- **Evidence (High):** `.github/workflows/smoke-test.yml`.
- **Acceptance:** 3.10 + 3.13 (Ubuntu), one macOS job, pip caching.
- **Dependencies:** none.
- **Risk if skipped:** claimed platform support is unverified.
- **Auditor question:** Is macOS support real enough to gate, or should the claim be narrowed instead?

#### #164 · ci(quality): ruff + coverage gate
- **P/S/L:** P1 · M · `ci`, `tests`
- **Problem:** No lint/coverage, so "production-tested" is unquantified.
- **Evidence (High):** ruff/black/mypy/pytest-cov not installed.
- **Acceptance:** ruff (conservative), coverage baseline then ratchet, both in CI.
- **Dependencies:** none.
- **Risk if skipped:** regressions and style drift.
- **Auditor question:** What coverage number is meaningful here, given many tests are mocked subprocess E2E?

#### #165 · test(installer): E2E onboarding
- **P/S/L:** P1 · M · `tests`, `ci`
- **Problem:** CI tests the repo, not the onboarding path users run.
- **Evidence (High):** smoke test never runs `install.sh`/`install.ps1`/`uninstall`.
- **Acceptance:** temp project → installer → `doctor`; `fix`→commit→`promote`; `uninstall` preserves host files.
- **Dependencies:** `#163` maybe.
- **Risk if skipped:** installer regressions reach users.
- **Auditor question:** Can installer E2E run hermetically (no network, no global harness config writes) in CI?

#### #166 · test(mcp): real stdio integration
- **P/S/L:** P1 · M · `tests`
- **Problem:** All MCP tests mock `retriever.perform_search`; the real handshake/DB resolution is untested.
- **Evidence (High):** `tests/test_mcp_lancedb.py` patches throughout.
- **Acceptance:** spawn server over stdio with fastmcp client; temp DB; assert `DB:` line; fail-closed from `$HOME`; umbrella opt-in.
- **Dependencies:** none.
- **Risk if skipped:** protocol-level breakage ships undetected.
- **Auditor question:** Is fastmcp's client stable enough for CI, or should this be a subprocess JSON-RPC test?

#### #167 · test(docs): documented commands exist
- **P/S/L:** P2 · S · `tests`, `docs`
- **Problem:** Docs drift from the CLI.
- **Evidence (High):** many `./aim ...` references with no binding.
- **Acceptance:** parse README/engine docs; assert parser knows each command; report file/line.
- **Dependencies:** none.
- **Risk if skipped:** users copy broken commands.
- **Auditor question:** How to handle aliases and intentionally historical docs?

### 9.6 Proof & positioning (#168–#172)

#### #168 · docs(bench): publish LoCoMo harness/results
- **P/S/L:** P0 · M · `memory`, `docs`
- **Problem:** The strongest result (89.4% raw / 96.0% adjusted) is unverifiable and not in the repo.
- **Evidence (Medium):** local benchmark reports; older RAG 5.0 pipeline, May 2026.
- **Acceptance:** `benchmarks/locomo/` fetch+ingest+run+judge; sanitize data; publish methodology/results; `make bench`.
- **Dependencies:** re-run under current engine first.
- **Risk if skipped:** the key claim stays hearsay.
- **Auditor question:** Is LoCoMo a credible benchmark for this product, and is the judge reproducible?

#### #169 · docs(bench): code retrieval vs grep/Serena
- **P/S/L:** P1 · M · `memory`, `docs`
- **Problem:** The specialist comparison (semantic code retrieval) has no evidence.
- **Evidence (High):** no eval harness.
- **Acceptance:** 50-query corpus; recall@10 + MRR for `aim search`/grep/Serena; methodology + failure cases.
- **Dependencies:** `#168` for harness patterns.
- **Risk if skipped:** can't defend a core claim.
- **Auditor question:** Is a hand-built 50-query set large enough to be credible, and who labels ground truth?

#### #170 · feat(cli): `aim demo`
- **P/S/L:** P0 · S · `ux`, `packaging`
- **Problem:** The "wow" is invisible without a harness; 60-second trial is impossible.
- **Evidence (High):** quickstart requires an external CLI.
- **Acceptance:** temp project → seed → index → query → print `DB:`; offline lexical fallback; CI smoke; GIF.
- **Dependencies:** none.
- **Risk if skipped:** discovery stays flat.
- **Auditor question:** Does a synthetic demo prove anything, or does it need a real repository sample?

#### #171 · docs: WHY.md positioning
- **P/S/L:** P1 · S · `docs`
- **Problem:** Without a wedge it reads as "another AGENTS.md framework".
- **Evidence (Medium):** README lists capabilities, not category placement.
- **Acceptance:** category statement, comparison table, when-not-to-use.
- **Dependencies:** `#169` for evidence.
- **Risk if skipped:** wrong comparisons, wrong expectations.
- **Auditor question:** Is the comparison set (mem0, Letta, basic-memory, Serena, spec-kit) the right one?

#### #172 · docs: versioned docs site + link check
- **P/S/L:** P2 · M · `docs`
- **Problem:** 17 manuals + 11 wiki pages, no search/versioning; dead links unnoticed.
- **Evidence (High):** no site build or link test.
- **Acceptance:** MkDocs (or equivalent), Pages deploy, link check in CI.
- **Dependencies:** none.
- **Risk if skipped:** onboarding friction.
- **Auditor question:** Is a docs site worth the maintenance for a 3-star project, or should README + docs stay canonical?

### 9.7 Agent UX & observability (#173–#177)

#### #173 · feat(doctor): `--fix` + embedding probe
- **P/S/L:** P0 · S · `ux`, `observability`
- **Problem:** `doctor`/`health` miss an unreachable embedding provider, the most common silent degradation.
- **Evidence (High):** Ollama offline still reports PASS.
- **Acceptance:** probe endpoint (latency/model/dim); `--fix` for venv shebangs/engine/missing dirs; `--strict` exit codes.
- **Dependencies:** pairs with `#156`.
- **Risk if skipped:** silent lexical-only operation (already observed).
- **Auditor question:** Should `doctor` mutate state (`--fix`), or stay read-only with a separate repair command?

#### #174 · feat(cli): consistent `--json`
- **P/S/L:** P2 · M · `ux`
- **Problem:** Agents scrape text; only `search` has `--json`.
- **Evidence (High):** map/health/doctor/projects are text/partial.
- **Acceptance:** one envelope (ok, command, data, warnings, db_path); implement + golden tests.
- **Dependencies:** none.
- **Risk if skipped:** brittle agent integrations.
- **Auditor question:** Is a single envelope flexible enough for heterogeneous commands?

#### #175 · feat(gitops): local-only issue ledger
- **P/S/L:** P2 · M · `ux`
- **Problem:** README advertises Local-Only Mode, but `bug`/`projects` require GitHub.
- **Evidence (High):** `cmd_bug` strict mode requires `gh` + origin.
- **Acceptance:** local `issues/NNN-slug.md`; local board file; tests + docs.
- **Dependencies:** none.
- **Risk if skipped:** advertised local mode is incomplete.
- **Auditor question:** Does a local ledger undermine the "GitHub is the source of truth" model?

#### #176 · feat(engine): engine doctor + config provenance
- **P/S/L:** P1 · S · `reliability`, `ux`
- **Problem:** Engine can be "healthy" but venv imports broken; `AIM_MEMORY_DB` from `$HOME` uses engine-default embeddings instead of the project's.
- **Evidence (High):** `doctor` reports version only; config resolves from cwd, not the DB's project.
- **Acceptance:** `aim engine doctor` imports/timing probe; load `<project>/.aim_core/CONFIG.json` when `AIM_MEMORY_DB` is set; tests.
- **Dependencies:** `#150` (engine lifecycle).
- **Risk if skipped:** wrong embedding config in explicit-DB mode.
- **Auditor question:** Should an explicit DB override also override config, or is cwd-based config correct?

#### #177 · feat(observability): MCP telemetry + `aim stats`
- **P/S/L:** P1 · S · `observability`, `ux`
- **Problem:** No way to know whether agents use the RAG.
- **Evidence (Medium):** 0 MCP calls found across 138 recorded sessions; no server logging.
- **Acceptance:** JSONL per call (query hash, hits, latency, db_path, client); `aim stats` aggregates; `AIM_NO_TELEMETRY=1`; no raw query text by default.
- **Dependencies:** none.
- **Risk if skipped:** you cannot measure adoption or regressions.
- **Auditor question:** Is telemetry acceptable in a privacy-first local tool, and where should it live?

### 9.8 Sandbox & integrations (#178–#179)

#### #178 · feat(sandbox): optional Docker/bwrap execution
- **P/S/L:** P1 · L · `enhancement`, `reliability`
- **Problem:** `promote` enforces cleanliness but never executes tests in isolation; this is the biggest gap vs full agent platforms.
- **Evidence (High):** no sandbox in core; `bwrap` is a Tier-2 skill only.
- **Acceptance:** `aim promote --sandbox docker|bwrap` with a configurable test command; fail closed when unavailable; opt-in; threat model.
- **Dependencies:** none.
- **Risk if skipped:** GitOps can merge untested code; enterprise gap remains.
- **Auditor question:** Does sandboxing belong in the OS layer or in the harness, and is `bwrap` portable enough?

#### #179 · docs(integration): per-harness recipes
- **P/S/L:** P1 · S · `docs`, `ux`
- **Problem:** No copy-paste onboarding per harness.
- **Evidence (High):** README lists harnesses without walkthroughs.
- **Acceptance:** recipe per harness (config, expected `DB:` output, troubleshooting), MCP + CLI fallback, linked from README/docs.
- **Dependencies:** `#159` (install) and `#166` (tested behavior).
- **Risk if skipped:** users fail at setup and leave.
- **Auditor question:** Which harnesses deserve first-class recipes, and are any configs project-scoped vs global?

---

## 10. Sequenced waves (challenge this)

| Wave | Tickets | Rationale |
|---|---|---|
| **0 — decision** | `#143` | Destructive; needs approval + backup; everything else can proceed without it. |
| **1 — stop the bleeding** | `#144`, `#150`, `#151`, `#173`, `#156` | Trust, global outage, silent degradation. Low effort except `#150`. |
| **2 — scale & visibility** | `#154`, `#148`, `#149`, `#157`, `#176`, `#177` | Makes the engine scale and failures observable. |
| **3 — adoption** | `#159`, `#170`, `#168`, `#171`, `#179`, `#163`, `#164` | Package, demo, prove, onboard. |
| **4 — depth** | `#160`, `#162`, `#165`, `#166`, `#167`, `#169`, `#172`, `#174`, `#175`, `#178`, `#161`, `#147`, `#146`, `#145`, `#152`, `#153`, `#155`, `#158` | Remaining hardening and polish. |

**Open sequencing questions:** Should packaging (`#159`) outrank engine safety (`#150`) because adoption is the real ceiling? Should `#168` wait for a clean current-engine re-run? Is `#178` worth building before sandbox demand exists?

---

## 11. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Private data in public history | Already true | High | `#143` (approval-gated) + `#146` |
| Fleet-wide MCP outage from interrupted engine sync | Medium | High | `#150` |
| Silent lexical-only degradation | Already observed | High | `#156`, `#173`, `#177` |
| Index stalls / RAM spikes at scale | Medium (as repos grow) | High | `#154` |
| Unpinned updater executes moving target | Low/Medium | High | `#144` |
| Bus factor 1 | High | High | Packaging + docs + CI gates (`#159`, `#163`, `#164`) |
| No measurable proof of value | High | Medium | `#168`, `#169`, `#177` |
| Over-trusting mocked tests | Medium | Medium | `#165`, `#166` |

---

## 12. Questions for the external auditor

1. Are C1–C10 in §5 reproducible, and do any change the priority order?
2. Is the 42-install count meaningful, or inflated by ephemeral workspaces? Should it appear in docs at all?
3. Is the history-purge risk real given the repo is public and already scanned, or is it an acceptable legacy cost?
4. Is LanceDB delete+add safe under the current file lock, or does `#154` need a staging table?
5. Is packaging (`#159`) correctly ranked below runtime safety, given adoption is the stated ceiling?
6. Are any tickets over-scoped (e.g., `#178`) or under-scoped (e.g., `#165`)?
7. What recommendation is missing entirely?
8. Are the acceptance criteria testable as written? Rewrite any that are not.
9. Does any ticket violate the "no LLM writes memory" principle or the local-first/zero-daemon posture?
10. Which tickets should be closed as `wontfix`, and why?

---

## 13. Verification appendix (read-only)

Run these on a clean checkout. Expected results are from 2026-11-26; your numbers may differ slightly.

```bash
# 1. Size and history
git count-objects -vH                      # expect ~314 MiB pack
git rev-list --objects main \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1=="blob"{print $3, $4}' | sort -rn | head -8

# 2. Code size and tests
find joshua_os -name '*.py' -not -path '*/venv/*' | xargs wc -l | tail -1   # ~11,967
find tests -name '*.py' | xargs wc -l | tail -1                              # ~3,487
python -m pytest --collect-only -q | tail -2                                # 85 collected

# 3. Silent failures / missing timeouts (AST)
python - <<'PY'
import ast, pathlib
sw=[]; nt=[]
for p in pathlib.Path("joshua_os").rglob("*.py"):
    if "venv" in p.parts: continue
    t=ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
    for n in ast.walk(t):
        if isinstance(n, ast.ExceptHandler) and len(n.body)==1 and isinstance(n.body[0], ast.Pass):
            sw.append((str(p), n.lineno))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr=="run" \
           and getattr(n.func.value,"id","")=="subprocess" \
           and not any(k.arg=="timeout" for k in n.keywords):
            nt.append((str(p), n.lineno))
print("except:pass", len(sw)); print("subprocess-no-timeout", len(nt))
PY

# 4. Dependencies and packaging
grep -c '>=' joshua_os/requirements.txt      # 12
grep -c '==' joshua_os/requirements.txt      # 1
ls pyproject.toml setup.py 2>&1              # both missing

# 5. CI scope
grep -n "python-version\|os:" .github/workflows/smoke-test.yml

# 6. MCP usage (OpenCode local DB only)
python - <<'PY'
import sqlite3, json, collections
p=__import__("os").path.expanduser("~/.local/share/opencode/opencode.db")
c=sqlite3.connect(f"file:{p}?mode=ro", uri=True)
tools=collections.Counter()
for (data,) in c.execute("select data from part"):
    try: d=json.loads(data)
    except Exception: continue
    if d.get("type")=="tool":
        tools[d.get("tool") or d.get("name")]+=1
print("sessions:", c.execute("select count(*) from session").fetchone()[0])
print("search_lancedb calls:", tools.get("search_lancedb", 0))
PY

# 7. Zero vectors in this workspace's DB
python - <<'PY'
import lancedb, numpy as np
t=lancedb.connect("joshua_os/memory_lance").open_table("fragments")
rows=t.to_arrow().to_pylist()
print(len(rows), sum(float(np.linalg.norm(np.array(r["vector"],dtype=np.float32)))==0 for r in rows))
PY

# 8. Live project checks
./aim doctor
./aim engine status
./aim health
./aim projects board
```

**Caveats:** the history blobs are reachable from `main` but absent from the working tree; the MCP usage scan covers OpenCode sessions only; the zero-vector count is repo-specific; the LoCoMo numbers come from an older pipeline and must be re-run before publication.

---

## 14. Source-of-truth links

- Epic: https://github.com/BrianV1981/aim-joshua/issues/142
- Children: https://github.com/BrianV1981/aim-joshua/issues/143 … /179
- Board: GitHub Project `#7` (`@BrianV1981`)
- Engine docs: `joshua_os/joshua_os_docs/` (Hybrid Search, GitOps, Vault, Handoff)
- Memory wiki: `memory-wiki/index.md`, `pages/architecture.md`, `pages/operations.md`
- Handoff: `HANDOFF.md`

---

## 15. Copy-paste auditor prompt

```text
You are auditing a roadmap for the J.O.S.H.U.A. repository (BrianV1981/aim-joshua).
Read artifacts/AUDIT_ROADMAP_2026-11-26.md in full, then:
1. Reproduce the measurements in §13 that are cheap and read-only.
2. Validate each ticket in §9 against the code and issue bodies. Mark accept/revise/reject/defer.
3. Challenge the priority order, size estimates, dependencies, and sequencing in §10.
4. Flag any claim in §5 that is overstated, unreproducible, or missing a caveat.
5. Identify missing recommendations, over-scoped tickets, and any that violate the documented
   non-goals (no LLM memory writes, no agent loop, local-first, zero-daemon).
6. Output a table: ticket | verdict | correction | evidence (file:line or command) | confidence.
7. Finish with: the 3 changes to the roadmap you would make first, and what you would delete.
Do not execute #143 (history rewrite) or any destructive command. Review only.
```

---

*End of packet. If this file and the GitHub issues diverge, the issues are authoritative; report the mismatch.*
