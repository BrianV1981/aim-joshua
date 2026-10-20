# Operations

## Parallel Execution & GitOps
J.O.S.H.U.A. enforces a highly parallel GitOps execution model, heavily formalized in `CONTRIBUTING.md`:
- Agents must NOT code on the `main` branch. They use `aim fix <issue_id>` to spawn physically isolated `git worktree` sandboxes.
- The agent workspace loop uses `aim push "<msg>"` to commit and push changes within the worktree. **Important:** `aim push` implicitly relies on `git add -u`, which will ignore newly created untracked files unless they are explicitly staged with `git add` first.
- The atomic release process utilizes `aim promote` to safely archive `main`, merge the active worktree branch, deploy the final baseline to GitHub, and destroy the local workspace sandbox.
- System-level isolation can be optionally added using `bwrap` if network or filesystem restrictions are required.

## Installation Pathways
- **Clean Installation (Default)**: Uses `install.sh` to install the engine natively while completely purging Git history, tests, and benchmarks.
- **Core Contributor Installation**: Uses `install-core.sh` to install the engine while preserving developer histories and `.git` artifacts.
- **Isolated Sandbox / Sovereign Co-Agent**: Uses `install-agent.sh` for headless Sovereign Co-Agent deployments (`aim-agents/*`).

## Co-Agent Engine Updates (`aim update`)
`cmd_update` (`aim update [--source <local_dir>] [--skip-deps]`) upgrades `joshua_os/` across deployed projects and Co-Agent nodes while strictly preserving tenant state:
- Preserves `.aim_core/CONFIG.json` across `.aim_core` directory replacement.
- Never overwrites tenant root files (`AGENTS.md`, `TOOLS.md`, `manifest.json`, `memory-wiki/`, `artifacts/`, or `joshua_os/memory_lance/`).
- Guards optional subdirectories (such as `scripts/`) with existence checks prior to `shutil.copytree`.

