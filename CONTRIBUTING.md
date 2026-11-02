# Contributing to J.O.S.H.U.A.

Welcome to the J.O.S.H.U.A. repository! All engine code, CLI, and documentation changes follow an isolated Git worktree + TDD workflow so `main` stays green and reproducible across Linux, macOS, WSL, and Windows 10/11.

## Prerequisites & Contributor Setup

1. **Runtime:** Python 3.10+ and Git (plus authenticated `gh` CLI if opening issues/PRs from the terminal).
2. **Clone & Build Engine Venv (Option C — Core Contributor):**
   ```bash
   # Linux / macOS / WSL
   git clone https://github.com/BrianV1981/aim-joshua.git
   cd aim-joshua
   bash joshua_os/setup.sh
   ./aim doctor
   ```
   ```powershell
   # Windows 10/11 (PowerShell)
   git clone https://github.com/BrianV1981/aim-joshua.git
   cd aim-joshua
   py -3 joshua_os\.aim_core\bootstrap_install.py --mode core --target .
   .\aim.ps1 doctor
   ```

## The GitOps Worktree Pipeline

**Do not develop application or engine code directly on `main`** *(Note: Agent Memory state in `memory-wiki/**` and `HANDOFF.md` is explicitly exempt and is committed/pushed directly to `origin/main` via `/aim-memory-wiki` and `/aim-handoff`)*.

### 1. Open or Claim an Issue (`aim bug` / GitHub Issues)
Create a structured GitHub issue (passing Commander's Intent flags `--context`, `--failure`, and `--intent`), or open an issue via the GitHub web UI:
```bash
./aim bug "Fix: short summary of the bug or feature" \
  --context "Affected module and architectural background" \
  --failure "Exact error, regression, or capability gap" \
  --intent "Step-by-step fix and pytest coverage plan"
```
*(Maintainers with Kanban access can claim an existing issue via `./aim projects in-progress <issue_id>`).*

### 2. Spawn an Isolated Worktree (`aim fix`)
Create an isolated `git worktree` under `workspace/issue-<issue_id>` on branch `fix/issue-<issue_id>`:
```bash
./aim fix <issue_id>
cd workspace/issue-<issue_id>
```
Write or update tests alongside your changes and run the full test suite with deprecation warnings treated as errors:
```bash
# Linux / macOS / WSL (from inside workspace/issue-<issue_id>)
../../joshua_os/venv/bin/python3 -m pytest tests/ -W error::DeprecationWarning

# Windows 10/11 (PowerShell, from inside workspace\issue-<issue_id>)
..\..\joshua_os\venv\Scripts\python.exe -m pytest tests\ -W error::DeprecationWarning
```
Stage specific files surgically (`git add <files>`) and commit (`git commit -m "..."`) — or push your worktree branch to `origin` via `../../aim push "Fix: ..."`.

### 3. Merge or Open a Pull Request
- **External Contributors (Forks):** Push your `fix/issue-<issue_id>` branch to your fork (`git push -u origin fix/issue-<issue_id>`) and open a Pull Request against `BrianV1981/aim-joshua` `main`. Both `ubuntu-latest` and `windows-latest` CI legs must pass.
- **Maintainers (Direct Worktree Promotion):** From inside your clean `workspace/issue-<issue_id>` directory (two levels below the repo root), run:
  ```bash
  ../../aim promote
  # Windows PowerShell: ..\..\aim.ps1 promote
  ```
  `promote` verifies the worktree has zero uncommitted/untracked changes, backs up `main`, merges `fix/issue-<issue_id>`, pushes to `origin` (when configured), and removes the clean worktree.

Finally, if tracking on GitHub Projects, mark the issue done from the repository root:
```bash
./aim projects done <issue_id>
```
