# A.I.M. Modular Tool Registry

This document serves as the external registry for the mechanical tools available to the Operator and Agents via the `aim` (Antigravity) CLI.

## 1. GitOps & Lifecycle Tools
* **`aim bug <title>`**: Opens a GitHub issue to track a bug. Use `--context`, `--failure`, and `--intent` for headless agent submissions.
* **`aim fix <id>`**: Checks out a dedicated Git worktree branch (`fix/issue-<id>`) to surgically fix an issue without polluting the main directory.
* **`aim push <message>`**: Pushes your current isolated branch to the remote repository and generates a Pull Request.
* **`aim promote`**: Archives the current `main` branch, safely merges the active dev branch, and prunes the local workspace.
* **`aim prune-remote`**: Garbage collects stale `archive-fix/*` and `fix/issue-*` remote branches.

## 1b. GitHub Projects (Kanban board SoT)
Shared board for multi-agent orchestration. Requires `gh` with **project** scope (`gh auth refresh -s project,read:project`).

Config (env or `CONFIG.json` → `settings.github_projects`):
* `AIM_PROJECTS_OWNER` (default `@me`)
* `AIM_PROJECTS_NUMBER` (e.g. `5`)
* `AIM_PROJECTS_STATUS_FIELD` (default `Status`)
* `AIM_PROJECTS_REPO` (e.g. `BrianV1981/aim-ld` — used to auto-add issues onto the board)

Commands:
* **`aim projects doctor`**: Validate gh auth/scopes and project config.
* **`aim projects list`**: List Projects for the owner.
* **`aim projects fields`**: Show Status field options (exact column names).
* **`aim projects board`**: Print kanban snapshot grouped by Status.
* **`aim projects board --status "In Progress"`**: Filter one column.
* **`aim projects board --json`**: Machine-readable for agents.
* **`aim projects in-progress <n>`** / **`ready`** / **`todo`** / **`blocked`** / **`done <n>`**: Move issue Status (aliases map to board options).
* **`aim projects set <n> "In Progress"`**: Set exact/alias Status.
* **`aim projects view <n>`**: Board row + `gh issue view`.

Agent protocol: read board → claim with `in-progress` → work via `aim fix` → `done` when PR ships.

## 2. Memory & Intelligence (Hybrid RAG)
* **`aim search "<query>"`**: Executes a LanceDB Hybrid Search (BM25 + Semantic) against the Engram DB and local markdown wikis.
* **`aim map`**: Prints a lightweight "Knowledge Map" of all currently loaded documentation titles.
* **`aim audit`**: Synthesizes a strategic overarching summary from the noise-reduced session history databases.

## 3. Operations & Sandboxing
* **`aim doctor`**: Validates the host environment, checking for correct Python versions and LanceDB dependencies.
* **`aim reincarnate`**: Triggers the Reincarnation Protocol to handoff context securely to a new agent session.
* **`aim delegate`**: Spawns parallel sub-agents (the RLM pattern) to execute multi-file analysis simultaneously.
