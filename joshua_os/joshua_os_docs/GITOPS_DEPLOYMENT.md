# J.O.S.H.U.A. GitOps Deployment Rules (Worktree Architecture)

This document defines the version-control guardrails enforced by J.O.S.H.U.A. across both GitHub-backed repositories and local-only Git repositories.

## 1. The Prime Directive & Agent Memory Exemption
* **Application Code, Configs & Scripts:** Agents must never develop code directly on `main`. Every bug fix, feature, or engine documentation update is developed inside an isolated Git worktree (`aim fix <id>` → TDD → `aim promote`).
* **Agent Memory Exemption (`memory-wiki/**` & `HANDOFF.md`):** Living OS memory state (`memory-wiki/**` and `HANDOFF.md`) is explicitly exempt from GitHub Issues and worktrees. When running `/aim-memory-wiki` or `/aim-handoff`, agents stage **only** the explicit memory paths (`git add memory-wiki/` and/or `git add HANDOFF.md` — strictly forbidding `git add .` or `git commit -a`), commit, run `git pull --rebase --autostash origin main`, and push directly to `origin/main` with zero Operator confirmation prompts (or commit locally on `main` when no `origin` remote is configured).

## 2. The Worktree Pipeline

### Step 1: Track Work (`aim bug` — GitHub-Backed Repos)
When working against a GitHub repository with `gh` CLI authenticated, open or claim an issue before coding:
```bash
./aim bug "Fix: concise summary" \
  --context "Affected subsystem" \
  --failure "Observed error or gap" \
  --intent "Planned fix and tests"
```
*(In local-only repositories without GitHub or `gh`, skip `aim bug` and pass any local task identifier directly to `aim fix <task_id>`).*

### Step 2: Surgical Isolation (`aim fix`)
Spawn a dedicated Git worktree under `workspace/issue-<id>` on branch `fix/issue-<id>`:
```bash
./aim fix 42
cd workspace/issue-42
```
All code edits, tests, and surgical staging (`git add <specific-files>` + `git commit`) happen exclusively inside `workspace/issue-42`.

### Step 3: Safe Promotion (`aim promote`)
From inside `workspace/issue-<id>`, run `../../aim promote` (POSIX) or `..\..\aim.ps1 promote` (Windows):
1. **Clean-Worktree Gate:** `cmd_promote` checks `git status --porcelain` in both the worktree and root repository first, aborting with `rc=1` if any uncommitted or untracked files exist so `--force` worktree cleanup never destroys work.
2. **Archive & Merge:** When `origin` is configured, `promote` fetches `origin`, fast-forwards `main`, pushes backup branch `archive-fix/issue-<id>-<timestamp>`, merges `fix/issue-<id>` into `main`, and pushes `origin/main`. In local-only repositories without `origin`, `promote` creates the local archive branch and merges into `main` locally.
3. **Teardown:** Removes `workspace/issue-<id>` and deletes the merged local `fix/issue-<id>` branch.

## 3. Batch Merge (`aim merge-batch`)
When multiple `origin/fix/issue-*` branches are ready simultaneously, `./aim merge-batch [--push]` merges non-conflicting branches sequentially into the default branch.
