# Project Management (Kanban)

## The `aim projects` Wrapper
J.O.S.H.U.A. includes a built-in wrapper for the GitHub CLI (`gh project`) to manage multi-agent work streams directly via terminal commands. This allows agents to natively interface with Kanban boards without breaking workflow.
- Located in `joshua_os/.aim_core/aim_projects.py` and accessed via `aim projects` (or optionally linked globally as `aim-projects`).

## Agent Board Protocol
As defined in `AGENTS.md` (§8b), agents must adhere to the following protocol to prevent collisions:
1. **Read the board**: `aim projects board`
2. **Claim work**: `aim projects in-progress <issue_id>`
3. **Execute**: `aim fix <issue_id>`
4. **Ship**: `aim projects done <issue_id>`

## Operator Prerequisites
The active GitHub CLI account (`gh auth status`) MUST have the specific project OAuth scopes to modify the board. If `aim projects doctor` reveals missing scopes, the Operator must run:
```bash
gh auth refresh -h github.com -s project,read:project
```

Configuration defaults to `owner: ""` (auto-detected dynamically from `git config --get remote.origin.url` in `aim_projects.py`, `#129`), `repo` auto-detected locally from `remote.origin.url` before falling back to `gh repo view` (`#140`), `number: 7`, and `status_field: "Status"` in `config_utils.py` (`settings.github_projects`), and can be overridden via environment variables (`AIM_PROJECTS_OWNER`, `AIM_PROJECTS_NUMBER`, and optionally `AIM_PROJECTS_REPO`) or inside `CONFIG.json`.

## Multi-Repository Board Safety & Windows UTF-8 Hardening (`#140`)
When multiple repositories share one GitHub Projects v2 board (e.g., Project `#7`):
- **Exact Repo Isolation (`_repos_match` & `find_item_by_issue`):** `aim_projects.py` compares full `owner/name` or exact repo-slug segments (`continue` on mismatch, rejecting prefix collisions like `aim-site` vs. `aim-site-content` and extracting `owner/repo` fallback from `content.url`) with `limit=500` board scans so `aim projects set <N>` never mutates a sibling repository's issue `#<N>`.
- **Windows `PATHEXT` & `cp1252` Safety (`_run_gh` & `_ensure_utf8_stdio`):** Resolves `gh` via `shutil.which("gh")` (honoring `.cmd`/`.bat` shims on Windows `PATH`) and reconfigures `stdout`/`stderr` + subprocess streams to `utf-8` (`errors="replace"`) so Unicode status arrows (`→`) and emoji issue titles never raise `UnicodeEncodeError` on piped Windows `cp1252` streams.
