# Handoff & Retrieval Protocols

## The Handoff Pipeline
When an agent's context window fills up, or a specific vessel is needed, the agent must undergo an **Agent Handoff** (previously referred to as "Reincarnation").
1. **Memory Synthesis (`aim-memory-wiki`):** Before sealing the vault, the agent MUST run the `aim-memory-wiki` skill to synchronously extract and document recent architectural context into the memory wiki.
2. **Blackbox Vault (Forensic Archive):** Before exiting the current session, the agent MUST seal the session into the immutable, Operator-locked blackbox vault by executing a vessel-specific blackbox command (e.g., `aim agy-blackbox --session-id <uuid>`, `aim grok-blackbox`, etc.). This extracts raw session history natively to prevent agent tampering. Operators can diagnose missing keys or the fallback file-key (`~/.aim/blackbox.key`) by running `aim vault doctor`.
3. **`aim-handoff`:** The agent invokes the `aim-handoff` skill to write a highly structured `HANDOFF.md`.
4. **Baton Pass:** The agent uses Tmux to spawn the next agent vessel and injects the handoff document directly into its prompt.

## LanceDB Retrieval (MCP)
A.I.M. uses LanceDB for semantic hybrid retrieval (RAG 5.21). When an agent needs to retrieve factual knowledge, it must natively act as a retrieval agent. 
- Agents can natively use the `search_lancedb` internal tool exposed via the `mcp_lancedb.py` MCP server.
- The MCP server dynamically extracts the active workspace URI during the initialization handshake, removing the need for hardcoded root paths.
- The LanceDB memory pool is dynamically routed to the active `memory_lance/` folder using the workspace handshake.
