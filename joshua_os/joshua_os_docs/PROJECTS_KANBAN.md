# Project Management (GitHub Projects Kanban)

## The `aim projects` Integration
J.O.S.H.U.A. includes a native GitHub Projects v2 Kanban integration (`joshua_os/.aim_core/aim_projects.py`, invoked via `./aim projects` on POSIX or `.\aim.ps1 projects` on Windows) so multiple agents can coordinate issue status from the terminal.

## Agent Board Protocol
1. **Read the board:** `aim projects board` (or `aim projects board --status "In Progress"` / `--json`)
2. **Claim work:** `aim projects in-progress <issue_id>`
3. **Execute in isolation:** `aim fix <issue_id>` (work inside `workspace/issue-<issue_id>`)
4. **Ship:** After promoting to `main` via `aim promote`, mark complete with `aim projects done <issue_id>`
5. **Blocked:** `aim projects blocked <issue_id>` when waiting on Operator input or external dependencies.

## Prerequisites & Configuration
Requires an authenticated GitHub CLI (`gh auth status`) with `project` scopes:
```bash
gh auth refresh -h github.com -s project,read:project
```

Configure per repository via environment variables or `joshua_os/.aim_core/CONFIG.json` (`settings.github_projects`):
- `AIM_PROJECTS_NUMBER` (required — your GitHub Project number, e.g. `1`)
- `AIM_PROJECTS_OWNER` (optional — auto-detected from `git remote.origin.url`, falling back to `@me`)
- `AIM_PROJECTS_STATUS_FIELD` (optional — defaults to `Status`)
- `AIM_PROJECTS_REPO` (optional — `owner/repo` for auto-adding issues onto the board)
