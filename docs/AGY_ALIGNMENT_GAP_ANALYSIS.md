# aim-agy ↔ aim-opencode Alignment Gap Analysis

*Generated: 2026-07-06*

This document tracks the structural, procedural, and feature gaps between
**aim-agy** (the primary "Soul" of A.I.M., built for Antigravity CLI) and
**aim-opencode** (our OpenCode CLI adaptation). Each gap is assessed for
whether it should be ported, kept divergent, or left alone.

---

## 1. Structural Gaps (Repository Layout)

| Area | aim-agy | aim-opencode | Action |
|------|---------|-------------|--------|
| Engine directory | `aim-agy_os/.aim_core/` (hidden, nested one level deep) | `aim_core/` (visible, at repo root) | **Keep ours** — different CLI, different layout. No benefit to mirroring. |
| `core/` directory | `aim-agy_os/core/` (contains only `DAEMON_PULSE.md`) | `core/` at repo root (contains `OPERATOR.md`, `CONFIG.json`, etc.) | **Keep ours** — already functional. |
| `continuity/` folder | **Abolished** (#56) — all context is ephemeral, injected into wake-up prompt | Still exists with `ISSUE_TRACKER.md`, `REINCARNATION_GAMEPLAN.md` | **PORT** — see Section 2 (Reincarnation). |
| Daemon process | **Deprecated** (#23) — replaced by native agy cronjobs | `daemon.py` still present | **Evaluate** — depends on whether OpenCode has an equivalent scheduling mechanism. |
| Crash recovery | **Deprecated** (#18, #20, #22) — removed `aim crash`, ghost session auditing | `aim crash` still present in AGENTS.md and code | **PORT** — dead path, never used in OpenCode. |
| Installer scripts | `install-clean.sh`, `install-core.sh`, `install-agent.sh` | `setup.sh` (single script) | **Evaluate** — aim-agy's 3-path installer is cleaner. |

---

## 2. AGENTS.md Gaps

### 2.1 Reincarnation Pipeline (Sections 7 + 10) — 🔴 HIGH PRIORITY

This is the biggest divergence and your stated pain point.

| Sub-area | aim-agy | aim-opencode | Gap |
|----------|---------|-------------|-----|
| Context handoff | **Ephemeral**: gameplan injected directly into wake-up prompt. No file I/O by the agent. | **Manual**: agent reads `continuity/ISSUE_TRACKER.md` and `continuity/REINCARNATION_GAMEPLAN.md` via `cat` | aim-agy is simpler — no files to read, no ordering rules, just "wake up and the plan is already there" |
| Pre-read protocol | None — nothing to read | CRITICAL PROTOCOL block: must read gameplan BEFORE other continuity files | Eliminated in aim-agy |
| Gameplan location | `.aim_core/temp/REINCARNATION_GAMEPLAN.md` (auto-deleted after injection) | `continuity/REINCARNATION_GAMEPLAN.md` (persists on disk) | aim-agy avoids "file permanence bias" |
| Reincarnation trigger | Agent writes gameplan → runs `aim_reincarnate.py` → system auto-injects into next agent → auto-deletes `.md` → self-terminates | Agent writes gameplan → runs `aim_reincarnate.py` → reads tmux link from stdout → displays to operator → exits | aim-agy is fully automated; ours requires manual relay |
| GAMEPLAN format | 5-section SOP from `aim-agy_os_docs/GAMEPLAN_SOP.md` | Freeform | aim-agy forces structured handoff |

**Verdict:** PORT the Ephemeral Context Injection pattern (#56). This gives you the "clean reset" reincarnation you're already comfortable with in aim-agy.

### 2.2 Issue Tracker Reference (Section 4)

| aim-agy | aim-opencode |
|---------|-------------|
| "Read the live Issue Tracker injected into your wake-up prompt, or manually query GitHub using `gh issue list`" | "Read `continuity/ISSUE_TRACKER.md` via `cat`" |

**Verdict:** PORT. No more manual `cat` of a gitignored file. OpenCode does inject the issue list via the `.opencode/plugins/aim-hooks.ts` plugin during compaction — we're already halfway there.

### 2.3 Catastrophic Memory Crashes Subsection (Section 6)

| aim-agy | aim-opencode |
|---------|-------------|
| Removed entirely | Still present: "execute `python3 aim_core/aim_cli.py crash`..." |

**Verdict:** PORT (remove). `aim crash` was deprecated in aim-agy (#18). OpenCode doesn't have a Gemini CLI crash recovery pathway. Dead instruction.

### 2.4 HALT AND CATCH FIRE Reference (Section 6)

| aim-agy | aim-opencode |
|---------|-------------|
| References `.gemini/settings.json` | References `opencode.json` |

**Verdict:** KEEP OURS. This is correct for OpenCode.

### 2.5 Workspace Isolation Ignore File (Section 8)

| aim-agy | aim-opencode |
|---------|-------------|
| `.geminiignore` | `.opencodeignore` |

**Verdict:** KEEP OURS. Correct for OpenCode.

### 2.6 "Gemini Added Memories" — tmux inter-agent chat

| aim-agy | aim-opencode |
|---------|-------------|
| Present: bracketed paste, Escape+Enter protocols for tmux messaging | Absent |

**Verdict:** SKIP. OpenCode doesn't use tmux-based agent chat. Not applicable.

### 2.7 Blast Radius Mandate

| aim-agy | aim-opencode |
|---------|-------------|
| ✅ Present | ✅ Present (backported 2026-07-06) |

**Verdict:** ALIGNED.

### 2.8 CLI_NAME → explicit path

| aim-agy | aim-opencode |
|---------|-------------|
| ✅ Explicit `python3 .aim_core/aim_cli.py` | ✅ Explicit `python3 aim_core/aim_cli.py` (backported 2026-07-06) |

**Verdict:** ALIGNED (dot difference is structural, not functional — see Section 1).

---

## 3. Feature Gaps (aim-agy closed issues worth porting)

| aim-agy # | Title | Worth porting? | Rationale |
|-----------|-------|----------------|-----------|
| **#56** | Ephemeral Context Injection (abolish continuity) | ✅ **Yes** | Simplifies reincarnation — your main pain point |
| **#53** | Operator UI Authorization Lock (prevent YOLO merges) | ✅ **Yes** | `aim_cli.py push` auto-merged to main today — this would have blocked it |
| **#44** | Universal Memory Salvage Engine | ⚠️ Maybe | Useful if sessions regularly crash/need recovery |
| **#33** | Pre-Commit Linter 'Shock Collar' | ⚠️ Maybe | Catches broken code before commit; nice-to-have |
| **#13** | Agent Amendment Protocol (how to safely edit AGENTS.md) | ✅ **Yes** | We edit AGENTS.md frequently with no formal protocol |
| **#14** | "Stop and Ask" mandate | ✅ **Yes** | Added safety: agents must ask before modifying AGENTS.md |
| **#40** | Tmux Knock Protocol (inter-agent chat) | ❌ Skip | Not applicable to OpenCode |
| **#34** | `install-agent.sh` (Sovereign Co-Agent installer) | ⚠️ Maybe | Only if we build co-agent swarm for OpenCode |
| **#5** | Fix: mkdir in installer scripts | ⚠️ Maybe | See Section 4 below |

---

## 4. aim-agy Issue #5 — Installer Script mkdir Bug

**Problem:** `install-clean.sh` crashes on line 43 when it tries to write placeholder `README.md` files into directories (`foundry/`, `planning-artifacts/`, `workspace/`, `memory/lance/`) that haven't been created yet.

This is a classic "directory restructuring casualty" — when aim-agy was reorganized into `aim-agy_os/` (#52), the `mkdir -p` calls that create these directories were lost from the installer script. The script tries to write files before ensuring the target directories exist.

**Fix:** Add `mkdir -p foundry planning-artifacts workspace memory/lance` before the file generation step in `install-clean.sh` (and verify `install-core.sh` doesn't have the same gap).

**Relevance to aim-opencode:** Our `setup.sh` is a single script, not the 3-path installer aim-agy uses. Our `aim_init.py` has its own `mkdir` logic (line 646-648). We should verify our setup doesn't have the same class of bug, but we're not directly affected by #5 since our installer architecture is different.

---

## 5. Recommended Action Sequence

### Phase 1 — Reincarnation Simplification (highest impact)
1. Port Ephemeral Context Injection pattern (#56) to AGENTS.md
2. Remove `continuity/` folder references from AGENTS.md
3. Remove CRITICAL PROTOCOL block
4. Update reincarnation trigger (Section 10) to match aim-agy's auto-inject + auto-delete pattern
5. Remove dead `aim crash` subsection
6. Update Section 4 issue tracker reference
7. Update `aim_init.py` T_SOUL template to match

### Phase 2 — Safety & Governance
1. Port Operator UI Authorization Lock (#53)
2. Port Agent Amendment Protocol (#13)
3. Add Stop and Ask mandate (#14)

### Phase 3 — Infrastructure Cleanup
1. Evaluate daemon deprecation
2. Evaluate installer improvements
3. New tickets for any remaining gaps

### Phase 4 — Future (low urgency)
- Universal Memory Salvage Engine (#44)
- Pre-Commit Linter (#33)
- Co-Agent Architecture if/when needed (#32, #34)

---

## 6. Current State

| Metric | Count |
|--------|-------|
| Open issues | 0 (all 6 migrated issues closed 2026-07-06) |
| Files aligned with aim-agy | README.md (ecosystem), AGENTS.md (Blast Radius, CLI_NAME) |
| Files needing alignment | AGENTS.md (reincarnation, issue tracker, crash), aim_init.py (T_SOUL template) |
| aim-agy features worth porting | 6 (in Phases 1-3 above) |
| aim-agy features to skip | 3 (Gemini-specific, not applicable to OpenCode) |
