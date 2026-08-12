# Project Management (Kanban)

## The `aim projects` Wrapper
J.O.S.H.U.A. includes a built-in wrapper for the GitHub CLI (`gh project`) to manage multi-agent work streams directly via terminal commands. This allows agents to natively interface with Kanban boards without breaking workflow.
- Located in `joshua_os/.aim_core/aim_projects.py` and accessed via `aim projects` (or optionally linked globally as `aim-projects`).

## Agent Board Protocol
Agents must adhere to the following strict GitOps protocol to prevent collisions across parallel environments:

1. **Read the board**: `aim projects board`
   *Query the active project board to find available tasks or see active work.*
2. **Claim work**: `aim projects in-progress <issue_id>`
   *Move the task to the "In Progress" column on the Kanban board so other agents know it is actively being worked on.*
3. **Execute**: `aim fix <issue_id>`
   *Spawn a highly isolated Git worktree for the task to avoid colliding with `main`.*
4. **Ship**: `aim projects done <issue_id>`
   *Once the task is promoted to `main` via `aim promote`, officially close it on the Kanban board.*
5. **Blocked**: `aim projects blocked <issue_id>`
   *If waiting on Operator input, DNS, or external dependencies.*

## Operator Prerequisites
The active GitHub CLI account (`gh auth status`) MUST have the specific project OAuth scopes to modify the board. If `aim projects doctor` reveals missing scopes, the Operator must run:
```bash
gh auth refresh -h github.com -s project,read:project
```

Configuration relies on setting `AIM_PROJECTS_OWNER` and `AIM_PROJECTS_NUMBER` (and optionally `AIM_PROJECTS_REPO`) via environment variables or inside `CONFIG.json`.
