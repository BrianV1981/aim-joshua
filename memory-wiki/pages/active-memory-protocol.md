# Active Memory Protocol

## Context
Previously, the A.I.M. system used a complex set of detached crons and background daemons (`wiki_batch`, `wiki_compiler`, `session_summarizer`) to "vacuum" up previous sessions from the transcript and write them into the memory wiki. This resulted in the wiki becoming polluted with Pytest fixture artifacts, E2E test runs, and general scratchpad noise, because the background agent lacked the live context to differentiate a test from a real operational breakthrough.

## The Pivot
On July 26, 2026, the architecture was drastically simplified:
- The entire background vacuum system was deprecated (PR #122).
- Replaced by the `aim-memory-wiki` skill.
- The wiki is now explicitly "opt-in" and strictly maintained by the **active agent** while the session context is still fresh in its context window.

This returns agency to the operator and drastically increases the signal-to-noise ratio in the persistent long-term memory.

## Direct-to-`main` Memory State Exemption (#101)
`memory-wiki/**` and `HANDOFF.md` are living OS memory state, **not** application code, and are explicitly exempt from GitHub Issues and `workspace/issue-*` worktrees:
1. **Mid-Session Checkpoint (`/aim-memory-wiki`):** Runs as a fast (~15s), autonomous "Save Game" checkpoint directly in the root repository — updating `memory-wiki/index.md`, `memory-wiki/log.md`, and `memory-wiki/pages/*.md`, running `./aim index` if LanceDB is active, and pushing directly to `origin/main` (`git add memory-wiki/` + `git pull --rebase --autostash origin main` + `git push origin main`) with zero issues, zero worktrees, and zero confirmation prompts.
2. **End-of-Session Closeout (`/aim-handoff`):** Performs an **Idempotent Auto-Wiki Delta Check** first (inspecting `memory-wiki/log.md` and automatically updating `memory-wiki/` if unlogged session work occurred), surgically updates `HANDOFF.md` (`0–9` template), and pushes both `memory-wiki/` and `HANDOFF.md` directly to `origin/main` in a single atomic commit (`git add memory-wiki/ HANDOFF.md`) with zero prompts.
3. **Surgical Path-Scoped Staging Only:** Agents must never run `git add .` or `git commit -a` when committing memory state — only `git add memory-wiki/` and/or `git add HANDOFF.md`.
