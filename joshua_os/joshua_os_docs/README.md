# J.O.S.H.U.A. Operating System Protocols (`joshua_os/joshua_os_docs/`)

This directory contains the canonical operational manuals defining the J.O.S.H.U.A. (`v1.1.2`) architecture and behavioral guardrails.

## 🛑 MANDATORY RE-INDEXING RULE
These files serve as the foundational handbook ingested into `joshua_os/memory_lance` (and pre-baked into `joshua_os/assets/default_lance` for fresh consumer installations).

Whenever you modify, add, or delete a file in `joshua_os/joshua_os_docs/` or `AGENTS.md`:
1. Re-index the local project database:
   ```bash
   ./aim index          # Windows PowerShell: .\aim.ps1 index
   ```
2. If contributing to the upstream `aim-joshua` repository itself, also re-bake the seed LanceDB directory shipped to new consumers:
   ```bash
   ./joshua_os/venv/bin/python3 joshua_os/.aim_core/bootstrap_brain.py --seed-default-lance
   ```

---

## Index of Protocol Manuals

* **`AGENTS_AMENDMENT_PROTOCOL.md`**: Re-indexing rules whenever `AGENTS.md` or `memory-wiki/` changes.
* **`AIM_CLI_TOOLS.md`**: Reference for core CLI commands (`fix`, `promote`, `push`, `projects`, `search`, `index`, `*-blackbox`, `update`).
* **`BLACKBOX_VAULT.md`**: Fernet (`AES-128-CBC + HMAC-SHA256`) at-rest session archival (`archive/.raw_jsonl_blackbox/`), threat model, shrink-overwrite protection, and SQLite WAL `history.db` indexing.
* **`COGNITIVE_ARCHITECTURE.md`**: End-to-end map of `HANDOFF.md`, `memory-wiki/`, Two-Tier LanceDB RAM + Parquet ROM, and the SQLite FTS5 session notebook.
* **`DATAJACK_SWARM.md`**: Local Parquet ROM cartridge compilation (`aim bake`), zero-copy mounting (`aim jack-in`), and unmounting (`aim unplug`).
* **`FLEET_ORCHESTRATION.md`**: Parallel execution across isolated Git worktrees (`aim fix`, `aim promote`, `aim merge-batch`) and optional Linux `bwrap` sandboxing.
* **`GAMEPLAN_SOP.md`**: Mandatory `0–9` numbered template and Auto-Wiki Delta Check for `HANDOFF.md`.
* **`GITOPS_DEPLOYMENT.md`**: Worktree isolation rules, clean-worktree `promote` gate, local-only vs GitHub-backed mode, and the Direct-to-`main` Agent Memory Exemption.
* **`HANDOFF_PROTOCOL.md`**: Session closeout workflow (`*-blackbox` + `/aim-handoff` + cross-platform LanceDB retrieval).
* **`HEADLESS_BOOTSTRAP_PROTOCOL.md`**: Non-interactive provisioning via `bootstrap_install.py` (`clean`, `agent`, `core` modes) across Linux, macOS, WSL, and Windows.
* **`HYBRID_SEARCH.md`**: Tantivy BM25 query engineering, 768-dim vector search, `EntityIntersectionReranker` RRF, N-1/N+1 context expansion, and `mcp_lancedb.py`.
* **`LANCEDB_INGESTION_PROTOCOL.md`**: Length-Constrained Accumulator chunking, SHA-256 cached incremental vector preservation, cross-platform write locking, and safe version compaction.
* **`PERSISTENT_WIKI.md`**: Synchronous active-agent maintenance of `memory-wiki/` via `/aim-memory-wiki` and the Direct-to-`main` GitOps Exemption.
* **`PROJECTS_KANBAN.md`**: GitHub Projects Kanban coordination via `aim projects`.
* **`SCRIPT_MAP.md`**: Directory map of every active module in `joshua_os/.aim_core/`, `joshua_os/handoff/`, and `joshua_os/hooks/`.
* **`TESTING_AND_VALIDATION.md`**: Test-Driven Development mandate, `-W error::DeprecationWarning` pytest gate, and `/aim-handoff` context hygiene.
