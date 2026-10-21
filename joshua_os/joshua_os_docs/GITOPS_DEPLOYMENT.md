# A.I.M. GitOps Deployment Rules (The Atomic Architecture)

This document defines the strict version control protocols that all A.I.M. agents must follow. To prevent autonomous agents from destroying the `main` branch or generating complex merge conflicts, A.I.M. enforces an "Atomic Deployment" architecture via specialized CLI commands.

## 1. The Prime Directive & Agent Memory Exemption
*   **Application Code, Configs & Scripts:** AI agents must never develop code directly on `main`. Every bug fix, feature, or engine documentation update must be deployed through the isolated worktree pipeline (`aim bug` → `aim fix <id>` → `aim push` → `aim promote`).
*   **Agent Memory Exemption (`memory-wiki/**` & `HANDOFF.md`):** Living OS memory state (`memory-wiki/**` and `HANDOFF.md`) is explicitly exempt from GitHub Issues and worktrees. When running `/aim-memory-wiki` (mid-session checkpoint) or `/aim-handoff` (end-of-session closeout), agents stage **only** the explicit memory paths (`git add memory-wiki/` and/or `git add HANDOFF.md` — strictly forbidding `git add .` or `git commit -a`), commit, run `git pull --rebase --autostash origin main`, and push directly to `origin/main` with zero Operator confirmation prompts.

## 2. The Deployment Pipeline

### Step 1: Report & Track (`aim bug`)
Agents must never start coding without an explicit issue ticket.
*   **Command:** `aim bug "<Description of the issue>"` (or `aim bug-operator` for internal OS tasks).
*   **Action:** This interfaces with the GitHub CLI (`gh`) to create a structured issue ticket and returns an Issue ID.
*   **Rule:** The issue description must be concise but exhaustive, detailing the specific failure mode or requested enhancement.

### Step 2: Surgical Isolation (`aim fix`)
Agents must never code directly on the `main` branch.
*   **Command:** `aim fix <Issue_ID>`
*   **Action:** The CLI automatically checks out a clean Git worktree (e.g., `fix/issue-42`) inside the isolated `workspace/` directory.
*   **Rule:** The agent must immediately `cd` into the new isolated workspace folder before touching any code.

### Step 3: Atomic Release (`aim promote`)
Once the code has been written, validated via automated tests, and confirmed working, the agent must deploy it atomically.
*   **Command:** `aim promote`
*   **Action:** The CLI automates the Phase Protocol from inside a worktree. It automatically fetches the latest code, archives the `main` branch safely, merges the worktree's branch into `main`, pushes to GitHub, and cleanly deletes the isolated workspace directory.
*   **Rule:** You must execute `aim promote` from inside your worktree once your code is empirically proven to work.

## 3. The Batch Merge (`aim merge-batch`)
If multiple independent agents are working in parallel across different `workspace/` directories, the Operator or the Prime Agent can execute `aim merge-batch`. This command automatically evaluates all open `fix/*` branches, resolves non-conflicting merges into `main`, and safely deletes the isolated worktrees to maintain repository hygiene.
