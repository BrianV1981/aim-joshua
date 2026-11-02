# The Persistent LLM Wiki (Long-Term Memory)

This document outlines the mechanics of the J.O.S.H.U.A. Persistent Wiki (`memory-wiki/` at the project root). To prevent context collapse and institutional amnesia, J.O.S.H.U.A. pairs structured Markdown synthesis (`memory-wiki/`) with Two-Tier Hybrid RAG (`joshua_os/memory_lance`).

## 1. Hybrid Search + Plain-Text Markdown
* **Hybrid Semantic & Keyword Search (`search_lancedb` MCP / `./aim search`):** Synthesized `memory-wiki/**/*.md` pages are indexed directly into `joshua_os/memory_lance` alongside `AGENTS.md` and `joshua_os/joshua_os_docs/` whenever `./aim index` (or `.\aim.ps1 index` on Windows) runs.
* **Obsidian-Compatible Markdown:** `memory-wiki/` (`index.md`, `log.md`, and `pages/*.md`) uses plain Git-tracked Markdown at the repository root so both humans and agents can inspect architectural history directly.

## 2. Active-Agent Ownership
The active Conscious Agent maintains `memory-wiki/` synchronously via the `aim-memory-wiki` skill:
* **To Read:** Query via `search_lancedb` MCP (`./aim search` fallback) or read `memory-wiki/index.md` and `memory-wiki/pages/*.md` directly.
* **To Write:** Invoke `/aim-memory-wiki` (or let `/aim-handoff` run its Step 1 Auto-Wiki Delta Check). Legacy `_ingest/` drop zones and background summarizer daemons have been retired in favor of deterministic active-agent synthesis.

## 3. Just-In-Time (JIT) Memory Synthesis (Direct-to-`main` "Save Game")
1. **Trigger:** Invoke `/aim-memory-wiki` mid-session, or run `/aim-handoff` at session closeout (which inspects `memory-wiki/log.md` for unlogged session work).
2. **Synthesis:** Distill architectural decisions, root causes, and verified outcomes without dumping raw session transcripts.
3. **Surgical Edits:** Update `memory-wiki/index.md`, append a chronological entry to `memory-wiki/log.md`, and create or update topic pages under `memory-wiki/pages/`.
4. **Vector Ingestion:** Run `./aim index` (POSIX) or `.\aim.ps1 index` (Windows) so `joshua_os/memory_lance` reflects the updated wiki pages immediately.
5. **Direct-to-`main` Auto-Push (GitOps Exemption):** Because `memory-wiki/**` and `HANDOFF.md` represent living OS memory state rather than application code, wiki updates **never** open a GitHub Issue or spawn a `workspace/issue-*` worktree. Stage only `git add memory-wiki/` (never `git add .` or `git commit -a`), commit (`docs(wiki): ingest <summary>`), run `git pull --rebase --autostash origin main`, and push directly to `origin/main` with zero Operator confirmation prompts.
