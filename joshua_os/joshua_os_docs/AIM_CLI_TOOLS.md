# J.O.S.H.U.A. Native CLI Tools & Commands

This document maps the core CLI commands available via `./aim` (Linux/macOS/WSL) and `.\aim.ps1` / `aim.cmd` (Windows 10/11).

## 1. GitOps & Worktree Lifecycle
* **`aim bug "<Title>" --context "..." --failure "..." --intent "..."`**
  * *Usage:* Creates a structured GitHub issue via `gh issue create` (use `aim bug-operator "<Title>"` for interactive prompts).
* **`aim fix <Issue_ID>`**
  * *Usage:* Spawns an isolated Git worktree at `workspace/issue-<Issue_ID>` on branch `fix/issue-<Issue_ID>` and copies local `CONFIG.json` into the worktree.
* **`aim push "<Message>" [--include-untracked]`**
  * *Usage:* Applies optional semantic version bumps (`Fix:`, `Feature:`, `BREAKING CHANGE:`), commits tracked changes, and pushes the current branch to `origin`.
* **`aim promote [--yes]`**
  * *Usage:* Run from inside `workspace/issue-<Issue_ID>` (`../../aim promote` on POSIX; `..\..\aim.ps1 promote` on Windows). Verifies `git status --porcelain` is clean, backs up `main`, merges the worktree branch (pushing to `origin` if configured, or merging locally in local-only repos), and removes the worktree.
* **`aim projects <subcommand>`**
  * *Usage:* GitHub Projects Kanban workflow (`board`, `in-progress <id>`, `done <id>`, `blocked <id>`, `doctor`).

## 2. Hybrid RAG Memory & Knowledge Retrieval
* **`aim search "<Query>" [--top-k N] [--full] [--session ID] [--json]`**
  * *Usage:* Executes Two-Tier Hybrid Search (LanceDB vectors + Tantivy BM25 FTS + RRF reranking) across `joshua_os/memory_lance` and mounted `.parquet` cartridges.
* **`aim map`**
  * *Usage:* Prints the Knowledge Map of indexed sources and mounted cartridges.
* **`aim index [--dir <path>]`**
  * *Usage:* Incrementally indexes `AGENTS.md`, `joshua_os/joshua_os_docs/`, and `memory-wiki/` (or `--dir <path>`) into `joshua_os/memory_lance`, preserving cached 768-dim vectors for unchanged chunks.

## 3. Checkpoints, Handoffs & Session Notebook
* **`aim-memory-wiki` (Skill — Mid-Session "Save Game")**
  * *Usage:* Synthesizes architectural takeaways into `memory-wiki/` (`index.md`, `log.md`, `pages/*.md`), runs `./aim index`, and pushes `memory-wiki/` directly to `origin/main` (`git add memory-wiki/` + `git pull --rebase --autostash origin main` + `git push origin main`).
* **`aim <vessel>-blackbox --session-id <id>`** (`agy-blackbox`, `grok-blackbox`, `opencode-blackbox`, `codex-blackbox`)
  * *Usage:* Seals the raw session transcript into `archive/.raw_jsonl_blackbox/` (Fernet `AES-128-CBC + HMAC-SHA256`) and indexes a noise-reduced Flight Record into `joshua_os/archive/history.db`.
* **`aim-handoff` (Skill — End-of-Session Closeout)**
  * *Usage:* Runs an **Idempotent Auto-Wiki Delta Check** on `memory-wiki/log.md`, surgically updates `HANDOFF.md` (`0–9` template), pushes `memory-wiki/` and `HANDOFF.md` directly to `origin/main`, and optionally passes the baton via `tmux` on POSIX hosts.
* **`aim sessions` / `aim search-sessions "<query>"`**
  * *Usage:* Lists and FTS5-searches all vaulted project sessions in `joshua_os/archive/history.db`.

## 4. DataJack Parquet Cartridges & Maintenance
* **`aim bake <directory_path> <output.parquet>`**: Compiles supported docs/code files into a `.parquet` ROM cartridge (requires local Ollama).
* **`aim jack-in <file.parquet>` / `aim unplug <keyword>` / `aim exchange list`**: Mounts, unmounts, or lists zero-copy `.parquet` cartridges in `joshua_os/archive/cartridges/`.
* **`aim update [--ref <tag|branch>] [--source <dir>] [--skip-deps]`**: Updates `joshua_os/` from the latest pinned GitHub release (with Zip-Slip path validation) while preserving `AGENTS.md`, `TOOLS.md`, `memory-wiki/`, and `CONFIG.json`.
* **`aim doctor` / `aim health` / `aim clean` / `aim purge [--yes]` / `aim uninstall [--yes] [--purge-memory]`**: Environment diagnostics, rolling archive + LanceDB compaction, `joshua_os/` memory reset, and host-safe uninstallation.
