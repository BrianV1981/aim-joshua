# A.I.M. Handoff & Retrieval Protocols

This document formalizes the exact sequence of events that occur during an A.I.M. Handoff (formerly known as Reincarnation). This protocol exists to prevent context window bloat (the "Amnesia Problem") while preserving absolute epistemic continuity across agent lifetimes.

---

## The 3-Step Handoff Pipeline

When an agent's context window fills up, or a specific vessel is needed, the agent must undergo an **Agent Handoff**.

### 1. The Blackbox Vault Sealing (Forensic Archive)
Before exiting the current session, the agent MUST seal the session into the immutable, Operator-locked blackbox vault. This extracts raw session history natively to prevent agents from tampering with or covering up their own mistakes.
- **Action:** Execute the vessel-specific blackbox command (e.g., `aim agy-blackbox --session-id <uuid>`, `aim grok-blackbox`, etc.).

### 2. The `aim-handoff` Skill (One-Command Closeout with Auto-Wiki Delta)
The agent invokes the `aim-handoff` skill to close out the session in a single turn:
- **Step 1 — Idempotent Auto-Wiki Delta Check:** Before updating `HANDOFF.md`, the agent inspects `memory-wiki/log.md`. If work or architectural decisions occurred since the last `/aim-memory-wiki` checkpoint (or if `/aim-memory-wiki` was not run during the session), `aim-handoff` automatically synthesizes those updates into `memory-wiki/` first. If `memory-wiki/` is already current for the session, it skips straight to `HANDOFF.md`.
- **Step 2 — Surgical `HANDOFF.md` Update:** The agent appends completed session work to `§0` and updates `§2` / `§9` for the incoming session using surgical edits (`0–9` gold-standard template).
- **Step 3 — Single Atomic Push to `main` (Zero Prompts):** Both `memory-wiki/**` and `HANDOFF.md` are living OS memory state exempt from GitHub Issues and worktrees. The agent runs:
  ```bash
  git add memory-wiki/ HANDOFF.md
  git diff --cached --quiet || git commit -m "docs(handoff): update memory-wiki and HANDOFF.md for session closeout"
  git pull --rebase --autostash origin main
  git push origin main
  ```
  *(Strictly forbidding `git add .` or `git commit -a`, and executing with zero Operator confirmation prompts).*

### 3. The Baton Pass
The agent uses Tmux to spawn the next agent vessel and injects the handoff document directly into its prompt.
- **Execution:** The current agent creates a detached `tmux` session, loads the `HANDOFF.md` into the buffer, pastes it, and submits it to the new agent.

---

## LanceDB Retrieval
A.I.M. uses LanceDB for semantic hybrid retrieval (RAG 5.21). When an agent needs to retrieve factual knowledge, it must natively act as a retrieval agent. 
- Agents must execute the raw Python CLI script explicitly rather than relying on bash aliases: 
  `python3 joshua_os/.aim_core/aim_cli.py search "<query>"`
- The LanceDB memory pool is dynamically routed; it uses `memory_lance/` at the OS root, or `./memory_lance` if operating inside a sandbox directory.
