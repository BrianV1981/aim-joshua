# A.I.M. Engineering Handoff SOP (`HANDOFF.md`)

This document defines the strict, high-fidelity structure required for the project root `HANDOFF.md` file maintained via the `/aim-handoff` skill (superseding the legacy `REINCARNATION_GAMEPLAN.md` and `/reincarnate` pipeline).

## 1. The Rule of Epistemic Certainty & Auto-Wiki Delta
The outgoing agent must act as a precise tactician. The incoming agent will wake up with a blank context window, and `HANDOFF.md` + `memory-wiki/` are its link to the mission state:
*   **Step 1 — Idempotent Auto-Wiki Delta Check:** Before editing `HANDOFF.md`, inspect `memory-wiki/log.md`. If work or architectural decisions occurred since the last `/aim-memory-wiki` checkpoint, update `memory-wiki/` (`index.md`, `log.md`, `pages/*.md`) first.
*   **Step 2 — Surgical Update Only:** Update `HANDOFF.md` in place using surgical edits (`0–9` numbered sections). Never delete or compress historical rows in `§0. COMPLETED WORK`.
*   **Step 3 — Direct-to-`main` Atomic Push (Zero Prompts):** Stage only `git add memory-wiki/ HANDOFF.md`, commit, run `git pull --rebase --autostash origin main`, and push directly to `origin/main` without opening a GitHub Issue or spawning a worktree.

## 2. Mandatory `0–9` Handoff Structure
Every `HANDOFF.md` MUST contain the following 10 numbered sections (`0–9`):
*   **`0. COMPLETED WORK (DO NOT REVISIT)`**: Append-only table of completed session work (`Session | Work | Status`).
*   **`1. PROJECT IDENTITY`**: 1–3 sentences on the system and absolute paths to `memory-wiki/index.md` and core docs.
*   **`2. YOUR MISSION`**: Overarching goal and ordered Execution Queue for the incoming session.
*   **`3. DETAILED ANALYSIS / BREAKDOWN`**: Module-by-module technical depth and architectural invariants.
*   **`4. IMPLEMENTATION STRATEGY`**: Ordered GitOps/TDD workflow steps.
*   **`5. THE CRITICAL TRAPS & WARNINGS`**: Epistemic and operational landmines.
*   **`6. KEY PATHS`**: Canonical absolute paths for the repository.
*   **`7. THE FULL PICTURE / WHAT COMES AFTER`**: Post-mission roadmap.
*   **`8. OPERATOR PREFERENCES`**: Boundaries, proof standards, and multi-agent coordination rules.
*   **`9. IMMEDIATE NEXT STEPS`**: Imperative, ordered first commands for the incoming agent.
