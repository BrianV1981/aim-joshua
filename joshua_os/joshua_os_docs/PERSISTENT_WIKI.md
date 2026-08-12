# The Persistent LLM Wiki (Long-Term Memory)

This document outlines the mechanics of the A.I.M. Persistent Wiki. To prevent "Context Collapse" and token burn, A.I.M. physically separates reference data (RAG Cartridges) from synthesized logic (The Wiki) and offloads wiki maintenance to an event-driven background daemon.

## 1. The Hybrid Search Architecture
The Wiki operates on a Hybrid Search engine to maximize speed and semantic understanding:
*   **Hybrid Semantic Search (`aim search`):** To ensure the Conscious Agent can "feel" the architectural decisions via vector embeddings and exact keywords, the synthesized `memory-wiki/*.md` files are ingested natively into the `memory_lance` LanceDB vector store alongside raw session flight recorders.
*   **Obsidian Native Sync:** The entire `memory-wiki/` directory is purely native Markdown. It can be opened directly as an Obsidian Vault, providing a real-time graphical representation of the project's subconscious memory.

## 2. The Golden Rule of Epistemic Certainty
A "Conscious Agent" (the agent the operator is actively using) is responsible for maintaining the wiki through the `aim-memory-wiki` skill. Forcing the primary agent to manually figure out markdown structures without guidance creates severe latency and token burn.
*   **To Read:** Agents query the `memory-wiki/` folder natively or use `aim search`.
*   **To Write:** Agents must invoke the `aim-memory-wiki` skill. The legacy `_ingest/` Drop Zone and background daemons have been abolished in favor of Just-In-Time (JIT) active-agent synthesis.

## 3. Just-In-Time (JIT) Memory Synthesis
Wiki maintenance is now handled synchronously by the active agent using the `aim-memory-wiki` skill.
1.  **The Trigger:** The user invokes the `aim-memory-wiki` skill directly, or the agent determines a critical architectural milestone has been reached.
2.  **Synthesis:** The agent synthesizes recent context, extracting tactical takeaways and architectural changes without copying raw transcripts.
3.  **Surgical Edits:** The agent natively edits `memory-wiki/index.md`, appends an entry to `memory-wiki/log.md`, and surgically modifies or creates markdown files in `memory-wiki/pages/` using standard file edit tools.
4.  **Vector Ingestion:** The updated wiki is continuously and natively re-embedded into the `memory_lance` RAM pool during the standard bootstrapping process, ensuring the database always reflects the live markdown files.
