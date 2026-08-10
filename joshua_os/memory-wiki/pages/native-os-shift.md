# Native OS Shift & GitOps Worktree Enforcement

J.O.S.H.U.A. has shifted from a mandatory "bubblewrapped" sandbox architecture to a native, universally accessible OS framework.

## Key Changes
- **Optional Sandboxing:** `bwrap` is now strictly an optional security feature for multi-tenant isolation, rather than the default development environment.
- **GitOps Worktree Protocol:** The official method for workspace isolation and parallel agent execution is now `git worktree`.
  - `aim fix <issue_id>` spawns an isolated physical worktree.
  - `aim promote` archives `main`, merges the dev branch, and cleanly tears down the worktree.
- **Dynamic Teardown Hook:** The `aim` entrypoint script no longer hardcodes the string `sandboxes` for the automatic memory teardown commit. It dynamically evaluates `if [ "$PWD" != "$ROOT" ] && [ -d ".git" ]; then`, allowing agents to automatically commit their state if operating inside any independent local `.git` repository (such as an active worktree).
- **Public Scaffold Readiness:** The default `AGENTS.md` OS blueprint now interactively prompts the user for their Operator Name upon initial deployment to ensure universal usability across all forks.
