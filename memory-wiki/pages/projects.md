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

Configuration relies on setting `AIM_PROJECTS_OWNER` and `AIM_PROJECTS_NUMBER` (and optionally `AIM_PROJECTS_REPO`) via environment variables or inside `CONFIG.json`.
