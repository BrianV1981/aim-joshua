# J.O.S.H.U.A. Headless Bootstrap Protocol

This document outlines the standard procedure for provisioning a fresh, isolated J.O.S.H.U.A. workspace non-interactively across Linux, macOS, WSL, and Windows 10/11.

## Prerequisites
- Python 3.10+ (`python3` on POSIX; `py -3` or `python` on Windows 10/11)
- Git (`git`)

## 1. Automated Cross-Platform Installer (`bootstrap_install.py`)
The recommended zero-touch entry point for both autonomous agents and CI pipelines is `joshua_os/.aim_core/bootstrap_install.py`:

```bash
# Linux / macOS / WSL — Clean Consumer Project
mkdir -p ~/my-project && cd ~/my-project
curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install.sh | bash

# Or from an existing local aim-joshua checkout (zero network clone):
python3 /path/to/aim-joshua/joshua_os/.aim_core/bootstrap_install.py \
  --mode clean \
  --target /path/to/my-project \
  --source /path/to/aim-joshua
```

```powershell
# Windows 10/11 (PowerShell)
mkdir C:\Projects\my-project; cd C:\Projects\my-project
irm https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install.ps1 | iex
```

For Sovereign Co-Agent nodes, use `--mode agent [--persona <blueprint-name>]` (or `install-agent.sh` / `install-agent.ps1`). `bootstrap_install.py` checks `sudo -n true` non-interactively on Linux so headless agents never block on `sudo` password prompts.

## 2. Re-Initializing an Installed Workspace (`aim init --headless`)
Inside an already-scaffolded project directory, run headless initialization via the engine virtual environment:

```bash
# Linux / macOS / WSL
./aim init --headless
# (Direct venv equivalent: ./joshua_os/venv/bin/python3 joshua_os/.aim_core/aim_init.py --headless)

# Windows 10/11 (PowerShell)
.\aim.ps1 init --headless
```

## 3. Verification
Verify the provisioned workspace artifacts and dependencies:
- `joshua_os/.aim_core/CONFIG.json` (portable engine configuration)
- `joshua_os/memory_lance/` (seeded LanceDB Hybrid RAG table)
- `memory-wiki/` (`index.md`, `log.md`, `pages/`)
- `./aim doctor` (or `.\aim.ps1 doctor` on Windows) exits `0`
