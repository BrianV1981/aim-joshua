# A.I.M. Agents Amendment Protocol

The `AGENTS.md` file is the absolute core system prompt and foundational operating structure for the A.I.M. ecosystem. 

## The Re-bake Mandate
If you are tasked with amending, adding, or modifying any rule inside the global `AGENTS.md` file, you **MUST** ensure that the newly modified rules are permanently embedded into the memory pool.

If you fail to do this, newly spawned agents will operate with an outdated understanding of the system, and will hallucinate rules that no longer exist.

## The Protocol
Whenever `AGENTS.md` (or `memory-wiki/` / `joshua_os_docs/`) is updated, you must execute the following command to re-embed and rebuild the `memory_lance` vector and FTS index:

```bash
./aim index
```

This ensures the new constraints and amendments inside `AGENTS.md` and `memory-wiki/` are immediately vectorized, chunked, and indexed via Tantivy FTS for the Hybrid Search Engine (`search_lancedb` MCP and `./aim search`).
