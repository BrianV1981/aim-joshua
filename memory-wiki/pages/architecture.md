# Architecture

## The OS Framework
J.O.S.H.U.A. is a CLI-agnostic operating system designed to serve as the foundational brain for autonomous AI agents. The framework has entirely decoupled from legacy "CLI vessels" (e.g., aim-grok, aim-opencode). 

## Memory Synthesis
The system utilizes a Just-In-Time (JIT) memory synthesis approach. 
- The legacy `_ingest/` drop zone and background `session_summarizer.py` daemons have been abolished. 
- Instead, Conscious Agents invoke the `aim-memory-wiki` skill synchronously to synthesize recent architectural changes and natively edit this persistent markdown wiki.
- During system boot, the wiki is embedded directly into the `memory_lance` LanceDB RAM pool.

## The Skill Library Architecture
The `aim-skill-library` utilizes a **Base + Override** architecture. All universal tool skills reside in the global `skills/` directory. However, when a specific vessel requires unique mechanics (e.g., `aim-handoff` triggering distinct `agy-blackbox` or `grok-blackbox` commands), the vessel-specific override is stored in `vessels/<cli>/skills/`. The installation script seamlessly detects and links the override, falling back to the global base if none exists.

## TUI Cockpit (aim_config.py)
The TUI has been strictly scoped down to OS-level environment management. It no longer contains logic for modifying agent personas, modifying markdown files via regex, or toggling legacy background daemons. Its mandate is limited to:
- Secret Vault & API Key Management
- LLM Cognitive Tier Routing (RAG Model Matrix)
- MCP Server Configuration
- Archive Retention settings

## Handoff vs Reincarnation
The original `reincarnation` sub-package (which automatically spawned new terminals via background hooks) has been completely purged from the codebase. It has been 100% superseded by the `aim-handoff` skill, placing the responsibility of context teleportation back into the hands of the conscious agent rather than unpredictable background daemons.

## Tool Injection (MCP)
J.O.S.H.U.A. operates with a strict "Two-Tier Protocol" for extending capabilities (such as the LanceDB memory pool).
- **Primary (Native MCP):** Modern CLI harnesses automatically ingest the local MCP server (`mcp_lancedb.py`), natively granting the active agent the `search_lancedb` internal tool. The MCP server dynamically binds to the active workspace to prevent cross-contamination.
- **Fallback (CLI-Agnostic):** To ensure 100% interoperability with legacy or custom CLI loops, agents gracefully degrade to direct python subprocess shell commands (e.g., `aim_cli.py search`) if an MCP tool is not present in their prompt. This guarantees no agent is ever completely blind.
