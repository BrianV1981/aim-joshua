# J.O.S.H.U.A. Modular Tool Registry

This document serves as the external registry for the CLI tools available to the Operator and autonomous agents via `./aim` (Linux/macOS/WSL) or `.\aim.ps1` / `aim.cmd` (Windows 10/11).

## 1. GitOps & Lifecycle Tools
* **`aim bug <title> --context ... --failure ... --intent ...`**: Opens a structured GitHub issue via `gh issue create` (or use `aim bug-operator <title>` for interactive prompts).
* **`aim fix <id>`**: Spawns an isolated Git worktree (`workspace/issue-<id>`) on branch `fix/issue-<id>`.
* **`aim push "<message>" [--include-untracked]`**: Bumps `VERSION`/`CHANGELOG.md` on semantic prefixes (`Fix:`, `Feature:`, `BREAKING CHANGE:`), commits tracked changes, and pushes the current branch to `origin`.
* **`aim promote [--yes]`**: Verifies `git status --porcelain` is clean, archives `main`, merges the active worktree branch (locally or pushing to `origin` when configured), and removes the clean worktree.
* **`aim merge-batch [--push] [--yes]`**: Sequentially merges open `origin/fix/issue-*` branches into the default branch.
* **`aim prune-remote [--confirm]`**: Lists stale `origin/archive-fix/*` and `origin/fix/issue-*` branches (protecting open PR heads); pass `--confirm` to delete them on `origin`.

## 1b. GitHub Projects (Kanban Board SoT)
Shared board for multi-agent orchestration. Requires `gh` with **project** scope (`gh auth refresh -s project,read:project`).

Config (env or `joshua_os/.aim_core/CONFIG.json` → `settings.github_projects`):
* `AIM_PROJECTS_OWNER` (auto-detected from `git remote.origin.url`, falling back to `@me`)
* `AIM_PROJECTS_NUMBER` (e.g. `1` — required per project)
* `AIM_PROJECTS_STATUS_FIELD` (default `Status`)
* `AIM_PROJECTS_REPO` (e.g. `my-org/my-repo` — optional, used to auto-add issues onto the board)

Commands:
* **`aim projects doctor`**: Validate `gh` auth/scopes and project config.
* **`aim projects list`** / **`fields`**: List Projects or Status column options.
* **`aim projects board [--status "In Progress"] [--json]`**: Print kanban snapshot grouped by Status.
* **`aim projects in-progress <n>`** / **`ready`** / **`todo`** / **`blocked`** / **`done <n>`**: Move issue Status.
* **`aim projects set <n> "<Status>"`** / **`aim projects view <n>`**: Set custom Status or inspect board + issue detail.

## 2. Memory, Hybrid RAG & Cartridge Exchange
* **`aim search "<query>" [--top-k N] [--full] [--session ID] [--json]`**: Executes Two-Tier LanceDB Hybrid Search (Vectors + Tantivy BM25 + RRF) over `memory_lance` and mounted `.parquet` cartridges.
* **`aim index [--dir <path>]`**: Indexes `AGENTS.md`, `joshua_os_docs/`, and `memory-wiki/` (or `--dir <path>`) into `joshua_os/memory_lance`.
* **`aim map`**: Prints the Knowledge Map of indexed sources and mounted Parquet cartridges.
* **`aim bake <dir> <output.parquet>`**: Compiles supported docs/code files into a portable `.parquet` ROM cartridge (requires local Ollama embeddings).
* **`aim jack-in <file.parquet>`** / **`aim unplug <keyword>`** / **`aim exchange list`**: Mount, unmount, or list `.parquet` cartridges in `joshua_os/archive/cartridges/`.

## 3. Session Continuity, Vault & Diagnostics
* **`aim doctor`** / **`aim health`**: Validate Python/package dependencies and check LanceDB, `history.db`, and `memory-wiki/` health.
* **`aim update [--ref <tag|branch>] [--source <dir>] [--skip-deps]`**: Updates `joshua_os/` from the latest pinned GitHub release (with Zip-Slip validation) while preserving `AGENTS.md`, `TOOLS.md`, `memory-wiki/`, and `CONFIG.json`.
* **`aim agy-blackbox`** / **`grok-blackbox`** / **`opencode-blackbox`** / **`codex-blackbox --session-id <id>`**: Seal a session transcript into the Fernet-encrypted Blackbox Vault (`archive/.raw_jsonl_blackbox/`).
* **`aim vault {audit|verify|seal|doctor}`**: Decrypt, verify SHA-256 manifest integrity, manually seal a transcript, or inspect keyring/keyfile health.
* **`aim sessions`** / **`aim search-sessions "<query>"`**: Browse or FTS5-search archived project sessions in `joshua_os/archive/history.db`.
* **`aim audit [-n 5]`** / **`aim recall "<query>"`** / **`aim delegate "<instruction>" --files ...`**: LLM-assisted synthesis and parallel multi-file analysis via `reasoning_utils.py`.
* **`aim clean`** / **`aim purge [--yes]`** / **`aim uninstall [--yes] [--purge-memory]`**: Rolling archive maintenance, `joshua_os/` memory reset, or safe J.O.S.H.U.A.-only uninstallation (preserving host repo files).
