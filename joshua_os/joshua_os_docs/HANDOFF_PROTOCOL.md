# A.I.M. Handoff & Retrieval Protocols

This document formalizes the exact sequence of events that occur during an A.I.M. Handoff (formerly known as Reincarnation). This protocol exists to prevent context window bloat (the "Amnesia Problem") while preserving absolute epistemic continuity across agent lifetimes.

---

## The 3-Step Handoff Pipeline

When an agent's context window fills up, or a specific vessel is needed, the agent must undergo an **Agent Handoff**.

### 1. The Blackbox Vault Sealing
Before exiting the current session, the agent MUST seal the session into the immutable blackbox vault. This extracts raw session history (SQLite/JSONL) natively.
- **Action:** Execute the vessel-specific blackbox command (e.g., `aim agy-blackbox --session-id <uuid>`, `aim grok-blackbox`, etc.).

### 2. The `aim-handoff` Skill
The agent invokes the `aim-handoff` skill to write a highly structured `HANDOFF.md`.
- **Prerequisite:** Before initiating the handoff, the agent or operator MUST ensure the `memory-wiki/` is up to date by synchronously running the `aim-memory-wiki` skill. *The legacy `_ingest/` asynchronous background daemons have been abolished in favor of this JIT synchronous synthesis.*
- **Format:** The `HANDOFF.md` contains the tactical state, local constraints, and immediate next commands for the incoming agent.

### 3. The Baton Pass
The agent uses Tmux to spawn the next agent vessel and injects the handoff document directly into its prompt.
- **Execution:** The current agent creates a detached `tmux` session, loads the `HANDOFF.md` into the buffer, pastes it, and submits it to the new agent.

---

## LanceDB Retrieval
A.I.M. uses LanceDB for semantic hybrid retrieval (RAG 5.21). When an agent needs to retrieve factual knowledge, it must natively act as a retrieval agent. 
- Agents must execute the raw Python CLI script explicitly rather than relying on bash aliases: 
  `python3 joshua_os/.aim_core/aim_cli.py search "<query>"`
- The LanceDB memory pool is dynamically routed; it uses `memory_lance/` at the OS root, or `./memory_lance` if operating inside a sandbox directory.
