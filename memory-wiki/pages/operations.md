# Operations

## Parallel Execution & GitOps
J.O.S.H.U.A. enforces a highly parallel GitOps execution model:
- Agents must NOT code on the `main` branch. They use `aim fix <issue_id>` to spawn physically isolated `git worktree` sandboxes.
- The atomic release process utilizes `aim promote` (replacing the legacy `aim push`) to safely archive `main`, merge the active worktree branch, deploy to GitHub, and destroy the sandbox.
- System-level isolation can be optionally added using `bwrap` if network or filesystem restrictions are required.

## Installation Pathways
- **Clean Installation (Default)**: Uses `install.sh` to install the engine natively while completely purging Git history, tests, and benchmarks.
- **Core Contributor Installation**: Uses `install-core.sh` to install the engine while preserving developer histories and `.git` artifacts.
- **Isolated Sandbox**: Uses `install-agent.sh` for `bwrap` sandboxed installations.
