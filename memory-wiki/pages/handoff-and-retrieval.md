# Handoff & Retrieval Protocols

## The Handoff Pipeline
When an agent's context window fills up, or a specific vessel is needed, the agent must undergo an **Agent Handoff** (previously referred to as "Reincarnation").
1. **Blackbox Vault:** Before exiting the current session, the agent MUST seal the session into the immutable blackbox vault by executing a vessel-specific blackbox command (e.g., `aim agy-blackbox --session-id <uuid>`, `aim grok-blackbox`, etc.). This extracts raw session history (SQLite/JSONL) natively.
2. **`aim-handoff`:** The agent invokes the `aim-handoff` skill to write a highly structured `HANDOFF.md`.
3. **Baton Pass:** The agent uses Tmux to spawn the next agent vessel and injects the handoff document directly into its prompt.

## LanceDB Retrieval
A.I.M. uses LanceDB for semantic hybrid retrieval (RAG 5.21). When an agent needs to retrieve factual knowledge, it must natively act as a retrieval agent. 
- Agents must execute the raw Python CLI script explicitly rather than relying on bash aliases: 
  `python3 joshua_os/.aim_core/aim_cli.py search "<query>"`
- The LanceDB memory pool is dynamically routed; it uses `memory_lance/` at the OS root, or `./memory_lance` if operating inside a sandbox directory.
