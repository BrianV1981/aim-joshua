# J.O.S.H.U.A. — Engineering Handoff

> **Updated:** 2026-08-12T21:15:00-04:00
> **Updated by:** Antigravity (Session ID: 20ea24cb-e71f-419b-a8b7-0b256c75850c)
> **Priority Mission:** Address Backlog Issue #57 (aim_batch_merge hardcoded branch)
> **Operator:** Brian

---

## 0. COMPLETED WORK (DO NOT REVISIT)
| Session | Work | Status |
|---------|------|--------|
| [3c7e001f] | Audit #3 Resolution Sprint: Fixed `aim promote`, added CI, wiped `wiki_tools.py` (Issues #36-45) | ✅ RESOLVED |
| [20ea24cb] | Audit #3 Polish Sprint: Resolved SOURCE.md, doc sync, LanceDB seed, search output, CI tests (Issues #46-51) | ✅ RESOLVED |
| [20ea24cb] | Audit #3 Polish Sprint (Cont'd): Vault Keyring Fallback, CLI Parser strictness, CONTRIBUTING.md (Issues #52-54) | ✅ RESOLVED |
| [20ea24cb] | `memory-wiki` ingestion and update for Audit #3 Polish Sprint (Issue #58) | ✅ RESOLVED |

*(Keep clean and consolidated. Point to wiki/issues for deep history — do not re-audit.)*

---

## 1. PROJECT IDENTITY
J.O.S.H.U.A. is the foundational, CLI-agnostic Operating System brain for autonomous AI coding agents. It has successfully decoupled from its legacy origins and rigid sandboxing mandates, now relying natively on `git worktree` for isolated agent execution, LanceDB for RAM, and GitHub Projects for Kanban orchestration.

### Your Knowledge Base
- `/home/kingb/aim-joshua/AGENTS.md` (The sovereign agent blueprint and OS rules)
- `/home/kingb/aim-joshua/memory-wiki/index.md` (The active LLM Wiki Index)
- `/home/kingb/aim-joshua/CONTRIBUTING.md` (The mandatory 3-step GitOps workflow)

---

## 2. YOUR MISSION: Fix Hardcoded 'main' branch in aim_batch_merge.py
There is only 1 open backlog issue left before the system is completely clean. The `cmd_promote` flow was successfully patched to use dynamic branch resolution (`main` vs `master`), but the `aim_batch_merge.py` script was missed.

### Execution Queue (in order)
#### 1️⃣ Fix Issue #57 (`aim_batch_merge.py`)
**Problem:** `aim_batch_merge.py` still has the string `"main"` hardcoded in its checkout and push operations. This breaks on repositories that use `master`.
**Fix:** Implement dynamic default branch resolution in `joshua_os/.aim_core/aim_batch_merge.py`.
**Key files:** `/home/kingb/aim-joshua/joshua_os/.aim_core/aim_batch_merge.py`

---

## 3. DETAILED ANALYSIS / BREAKDOWN
- During the previous sprint, `aim_cli.py` was updated in `cmd_promote` to resolve the default branch automatically (lines 374-376). 
- `aim_batch_merge.py` currently contains hardcoded `subprocess.run(["git", "checkout", "main"], ...)` at lines 25, 26, and 62.
- The script needs to use the same `git branch --list` parsing trick as `cmd_promote` to dynamically identify whether the default branch is `main` or `master`.

---

## 4. IMPLEMENTATION STRATEGY
Maintain extreme GitOps discipline for any new tasks. Do not act on `main`. Follow the exact lifecycle:
1. `aim projects board`
2. `aim projects in-progress 57`
3. `aim fix 57`
4. *Code & Test* (Update `aim_batch_merge.py` to use dynamic branching)
5. `aim promote`
6. `aim projects done 57`

---

## 5. THE CRITICAL TRAPS & WARNINGS
> **⚠️ EPISTEMIC / OPERATIONAL WARNINGS**
- **The Worktree Mandate:** NEVER perform development directly on `main`. You must use `aim fix <id>`. 
- **The `aim-memory-wiki` Prerequisite:** You MUST run `/aim-memory-wiki` to synthesize new architecture changes *before* executing `/aim-handoff`.
- **The Blackbox Mandate:** Before an agent vessel dies, it MUST execute its vessel-specific vault command (e.g. `aim agy-blackbox --session-id <uuid>`) to extract raw session logs. 

---

## 6. KEY PATHS
- `/home/kingb/aim-joshua/joshua_os/.aim_core/aim_batch_merge.py`
- `/home/kingb/aim-joshua/joshua_os/.aim_core/aim_cli.py` (For reference on how `cmd_promote` did dynamic branching)

---

## 7. THE FULL PICTURE / WHAT COMES AFTER
Once Issue 57 is resolved, J.O.S.H.U.A. will be entirely devoid of legacy hardcoded branches, allowing clean, framework-agnostic deployments on any repository (whether they use `main` or `master`).

---

## 8. OPERATOR PREFERENCES
- **Worktree Discipline:** Explicit adherence to `git worktree` isolation is non-negotiable (`aim fix`).
- **Kanban Discipline:** All tasks must be claimed natively via `aim projects in-progress`.

---

## 9. IMMEDIATE NEXT STEPS
1. Claim Issue 57: `export AIM_PROJECTS_OWNER=BrianV1981; export AIM_PROJECTS_NUMBER=7; ./aim projects in-progress 57`
2. Spawn your isolated workspace using `./aim fix 57`
3. Enter the workspace and patch `joshua_os/.aim_core/aim_batch_merge.py`.
