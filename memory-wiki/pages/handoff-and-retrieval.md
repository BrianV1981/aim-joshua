# Handoff & Retrieval Protocols

## The Handoff Pipeline
When an agent's context window fills up, or a specific vessel is needed, the agent must undergo an **Agent Handoff** (previously referred to as "Reincarnation").
1. **Memory Synthesis (`aim-memory-wiki`):** Before sealing the vault, the agent MUST run the `aim-memory-wiki` skill to synchronously extract and document recent architectural context into the memory wiki.
2. **Blackbox Vault (Forensic Archive):** Before exiting the current session, the agent MUST seal the session into the immutable, Operator-locked blackbox vault by executing a vessel-specific blackbox command (e.g., `aim agy-blackbox --session-id <uuid>`, `aim grok-blackbox`, etc.). This extracts raw session history natively to prevent agent tampering. Operators can diagnose missing keys or the fallback file-key (`~/.aim/blackbox.key`) by running `aim vault doctor`.
3. **`aim-handoff`:** The agent invokes the `aim-handoff` skill to write a highly structured `HANDOFF.md`.
4. **Baton Pass:** The agent uses Tmux to spawn the next agent vessel and injects the handoff document directly into its prompt.

## LanceDB Retrieval (Two-Tier Protocol)
A.I.M. uses LanceDB for semantic hybrid retrieval (RAG 5.21). When an agent needs to retrieve factual knowledge, it must natively act as a retrieval agent using the Two-Tier Protocol:
1. **Primary (Native MCP — Pure Automatic Mode):** Agents use the `search_lancedb(query, top_k=10)` internal tool exposed via the `mcp_lancedb.py` MCP server with **zero path or scope parameters** required from the LLM:
   - **Local-First:** If the active workspace root (`params.workspaceFolders[0].uri` or `os.getcwd()`) contains `joshua_os/memory_lance`, it queries that project's isolated cartridge directly.
   - **Umbrella Subfolder Fallback:** If the agent is opened in a parent/umbrella directory (e.g., `/home/kingb/aim-agents`) that has no root `joshua_os/memory_lance`, `mcp_lancedb.py` automatically discovers all immediate child subdirectories (`*/joshua_os/memory_lance`), queries each child cartridge, merges and ranks results by hybrid score, and prefixes every hit with `[Source: <subproject_name>]`.
2. **Fallback (CLI-Agnostic):** If an agent is spawned in a vessel that does not support MCP (e.g. legacy CLIs or bare LLM loops), they must degrade to executing the raw Python CLI script explicitly: `python3 joshua_os/.aim_core/aim_cli.py search "<query>"`
