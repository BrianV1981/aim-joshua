# J.O.S.H.U.A.
**Joint Operational Systems for Heuristic User Automation**

J.O.S.H.U.A. is an open-source, CLI-agnostic Operating System designed to serve as the foundational brain, memory, and infrastructure for autonomous AI coding agents. External LanceDB (RAG) memory, GitOps guardrails, encrypted Blackbox session continuity, and Parquet "Datajack" knowledge cartridges. v1.1.2 — Production-tested, trenches-first.

## 🚀 Quickstart & Installation

J.O.S.H.U.A. runs natively on **Linux**, **WSL (Ubuntu)**, **macOS**, and **Windows 10/11**, requiring Python 3.10+, Git, and your preferred underlying LLM harness (Antigravity IDE/CLI, Grok CLI, OpenCode, Codex, Claude Code, Cursor, etc.).

- **Local-Only Mode (Zero GitHub Setup):** Works immediately out of the box after `git init` — includes LanceDB RAG (`search_lancedb` MCP + `./aim search`), `memory-wiki/`, `HANDOFF.md`, encrypted Blackbox Vault, and local Git worktrees (`./aim fix <id>` → `./aim promote` merges locally when no `origin` remote is configured).
- **GitHub-Backed GitOps & Kanban Mode (Optional):** Commands that create/query GitHub Issues, PRs, or Project boards (`./aim bug`, `./aim projects`, `./aim prune-remote --confirm`, and remote pushes during `./aim push` / `./aim promote`) require a configured Git `origin` remote and an authenticated GitHub CLI (`gh auth login`, plus `gh auth refresh -s project,read:project` for Kanban boards).

> **⚠️ IMPORTANT (Target Directory Rule):** All installers scaffold J.O.S.H.U.A. **directly into your current working directory (`pwd`)** and register a CLI alias matching the folder name. Always create and `cd` into your target project directory **before** running the installer.

| Option | Installer Script | Windows PowerShell | Best For | `AGENTS.md` Installed | Upstream `.git` / `tests/` |
|--------|------------------|--------------------|----------|-----------------------|----------------------------|
| **Option A (Default)** | `joshua_os/install.sh` | `joshua_os/install.ps1` | New or existing software projects | Full 10-section J.O.S.H.U.A. `AGENTS.md` (`cp -n`, never overwrites existing) | Stripped (clean project root) |
| **Option B (Co-Agent)** | `joshua_os/install-agent.sh [persona]` | `joshua_os/install-agent.ps1 [persona]` | Specialist peer nodes under `~/aim-agents/<name>` | Specialist blueprint from `aim-coagents` if `[persona]` is passed; otherwise full 10-section `AGENTS.md` | Stripped (isolated node) |
| **Option C (Contributor)** | `joshua_os/install-core.sh` | `joshua_os/install-core.ps1` | Developing the J.O.S.H.U.A. OS engine itself | Upstream `aim-joshua/AGENTS.md` | Preserved (`tests/`, `memory-wiki/`, `.git`) |

### Option A: Clean Project Installation (Default — New or Existing Projects)
Installs the `joshua_os/` engine, local `./aim` / `aim.ps1` / `aim.cmd` launchers, project-specific `memory_lance/` database, multi-harness `search_lancedb` MCP server (auto-registered for Antigravity, Grok, Codex, OpenCode, and existing Cursor/Claude configs), and default `AGENTS.md` / `TOOLS.md` blueprints into your project directory without `aim-joshua` contributor history.

**Linux / macOS / WSL (Bash / Zsh):**
```bash
# 1. Create and enter your project directory (the folder name becomes your CLI alias)
mkdir -p ~/my-project && cd ~/my-project

# 2. Run the clean installer
curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install.sh | bash

# 3. Reload shell (~/.bashrc on Linux/WSL or ~/.zshrc on macOS) and verify installation
source ~/.bashrc
./aim doctor
```

**Windows 10/11 (PowerShell):**
```powershell
# 1. Create and enter your project directory
mkdir my-project; cd my-project

# 2. Run the native PowerShell installer
irm https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install.ps1 | iex

# 3. Verify installation
.\aim.ps1 doctor
```

### Option B: Headless Co-Agent (Sovereign Node)
Deploys a stripped-down, headless Sovereign Co-Agent node (ideal for specialist peers under `~/aim-agents/<node-name>` paired with a blueprint from `aim-coagents`). Pass an optional persona name (`python-developer`, `aim-auditor`, `lead-analyst`, etc.) to pull that specialist `AGENTS.md` blueprint automatically, or omit it to use the default 10-section J.O.S.H.U.A. `AGENTS.md`.

```bash
# Linux / macOS / WSL
mkdir -p ~/aim-agents/my-agent && cd ~/aim-agents/my-agent
curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install-agent.sh | bash -s python-developer
source ~/.bashrc
./aim doctor
```

```powershell
# Windows 10/11 (PowerShell)
mkdir C:\aim-agents\my-agent; cd C:\aim-agents\my-agent
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install-agent.ps1))) python-developer
.\aim.ps1 doctor
```

### Option C: Core Contributor Installation
Installs the universal engine while preserving the `aim-joshua` `.git` history, test suites (`tests/`), and `memory-wiki/` for developing J.O.S.H.U.A. itself.

```bash
# Linux / macOS / WSL
mkdir -p ~/aim-joshua-dev && cd ~/aim-joshua-dev
curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install-core.sh | bash
```

```powershell
# Windows 10/11 (PowerShell)
mkdir aim-joshua-dev; cd aim-joshua-dev
irm https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install-core.ps1 | iex
```

### Customizing J.O.S.H.U.A. for Your New Project
Once installed in your project directory:
1. **Personalize Identity & Rules (`AGENTS.md`):**
   - **Automatic Turn-1 Prompt or Direct Edit:** The default `AGENTS.md` includes `- **Operator Name:** [ASK OPERATOR FOR THEIR NAME AND FILL IT IN HERE USING FILE EDIT TOOLS]`, instructing your agent on Turn 1 to ask your name and update `AGENTS.md` surgically in place. You can also edit `AGENTS.md` (and `TOOLS.md`) directly to define your project's domain architecture, tech stack, and specific rules, or copy a specialist blueprint from [`aim-coagents`](https://github.com/BrianV1981/aim-coagents).
   - **Interactive Onboarding Interview (`./aim init`):** Alternatively, run `./aim init` (on POSIX systems with `tmux`) to launch the interactive Onboarding Architect (`joshua_os/BOOTSTRAP.md`) in a `tmux` session, or run `.\aim.ps1 init --headless` on Windows and paste `joshua_os/BOOTSTRAP.md` into your IDE/CLI chat to customize `AGENTS.md` (`## 1` and `## 11`) while preserving all 10 core OS sections.
2. **Initialize Project Knowledge (`memory-wiki/` & LanceDB):** Add project documentation in `memory-wiki/` (or any docs folder) and vectorize it into your project's isolated LanceDB database:
   ```bash
   ./aim index          # Windows PowerShell: .\aim.ps1 index
   # Or ingest a custom documentation directory:
   ./aim index --dir ./docs
   ```
3. **Keep the Engine Updated:** At any time, pull the latest pinned J.O.S.H.U.A. release into your project without overwriting your custom `AGENTS.md`, `TOOLS.md`, `memory-wiki/`, or `CONFIG.json`:
   ```bash
   ./aim update         # Windows PowerShell: .\aim.ps1 update (supports --ref <tag> or --source <dir>)
   ```

### Universal Skill Injection (Required Once Per Supported Host CLI)
Because J.O.S.H.U.A. is CLI-agnostic, skills are decoupled from the OS engine. Clone [`aim-skill-library`](https://github.com/BrianV1981/aim-skill-library) once and install the skill pack for **`agy`**, **`grok`**, **`opencode`**, or **`codex`** (Claude Code and Cursor use `AGENTS.md` + auto-registered `search_lancedb` MCP + `./aim` CLI directly):

```bash
# Linux / macOS / WSL (Antigravity 2.0 global skills; legacy standalone agy 1.x CLI uses ~/.gemini/antigravity-cli/skills)
git clone https://github.com/BrianV1981/aim-skill-library.git ~/aim-skill-library
cd ~/aim-skill-library
./scripts/install.sh --vessel agy --dest ~/.gemini/config/skills --mode symlink
```

```powershell
# Windows 10/11 (PowerShell — Antigravity 2.0 global skills; defaults to copy mode without requiring Developer Mode symlinks)
git clone https://github.com/BrianV1981/aim-skill-library.git "$HOME\aim-skill-library"
cd "$HOME\aim-skill-library"
.\scripts\install.ps1 -Vessel agy -Dest "$HOME\.gemini\config\skills"
```

---

## 🧭 Platform & Harness Capability Matrix

J.O.S.H.U.A. separates its cross-platform **Universal Core** from optional **POSIX Swarm** add-ons, with transparent per-harness integration tiers:

| Tier / Harness Group | Platforms & Harnesses | Included Capabilities |
|----------------------|-----------------------|-----------------------|
| **Tier 1A: Full Harness Pack** | **Windows 10/11, macOS, Linux, WSL** · Antigravity (`agy`), Grok CLI (`grok`), OpenCode (`opencode`), Codex CLI (`codex`) | `AGENTS.md` constitution, `search_lancedb` MCP auto-registration, `aim-skill-library` slash skills (`/aim-memory-wiki`, `/aim-handoff`, etc.), dedicated session sealers (`agy-blackbox`, `grok-blackbox`, `opencode-blackbox`, `codex-blackbox`), FTS5 session notebook (`./aim sessions`), and GitOps worktrees. |
| **Tier 1B: Universal MCP + CLI** | **Windows 10/11, macOS, Linux, WSL** · Claude Code, Cursor, or any MCP/CLI agent | `AGENTS.md` constitution, automatic `search_lancedb` MCP registration (when `~/.claude.json` or `~/.cursor` exists), `./aim` / `.\aim.ps1` CLI retrieval & GitOps worktrees, and manual transcript sealing via `./aim vault seal --path <transcript>`. |
| **Tier 2: POSIX Swarm** | **Linux, WSL, macOS** (`tmux`; `bwrap` on Linux) | Detached `tmux` execution, `aim-communicate` live multi-agent pane messaging, `/aim-handoff` automated `tmux` baton pass, and Linux `bwrap` sandbox isolation (`aim-bwrap-forge`). |

---

## 🔥 Core Capabilities

*   **Universal OS Framework:** Runs natively across Linux, macOS, WSL, and Windows 10/11 as the external memory and workflow exoskeleton for coding agents.
*   **Headless Deployment:** Co-agents can be deployed into dedicated repositories via `install-agent.sh` / `install-agent.ps1`.
*   **Embedded Local Memory:** Two-Tier Hybrid RAG (LanceDB vectors + Tantivy BM25 FTS + RRF reranking) with zero-copy Parquet ROM cartridge mounting (`./aim bake`, `./aim jack-in`, `./aim unplug`).
*   **GitOps Enforcement (with Memory-State Exemption):** Application code and configuration changes run inside isolated `workspace/issue-<id>` worktrees (`./aim fix` → TDD → `./aim promote`), while living Agent Memory (`memory-wiki/**` and `HANDOFF.md`) commits and pushes directly to `origin/main` with zero prompts.
*   **Autonomous Memory Wiki & One-Command Handoffs:** `/aim-memory-wiki` runs as a fast mid-session "Save Game" checkpoint directly to `main`, and `/aim-handoff` automatically checks `memory-wiki/log.md` for unlogged session deltas, surgically updates `HANDOFF.md` (`0–9` template), and pushes both to `origin/main`.
*   **Encrypted Blackbox Vault & Session Notebook:** Fernet (`AES-128-CBC + HMAC-SHA256`) at-rest encrypted session archival (`archive/.raw_jsonl_blackbox/`, keyed via OS keyring or `0600` `~/.aim/blackbox.key` for safe Git/cloud backup) paired with a local SQLite WAL/FTS5 project session notebook (`./aim sessions`, `./aim search-sessions`).
*   **Anti-Drift Shield (Antigravity Hook):** When registered in Antigravity, `cognitive_mantra.py` (`AfterTool` via `aim_router.py`) periodically reinforces `AGENTS.md` mandates during long tool-call chains.

---

## 📖 Documentation & Contributing

- **[Engine Architecture Manuals (`joshua_os/joshua_os_docs/`)](./joshua_os/joshua_os_docs/README.md)**: Canonical specifications for Hybrid RAG, GitOps worktrees, Blackbox Vault at-rest encryption, DataJack Parquet cartridges, and Handoff protocols.
- **[Contributing Guide (`CONTRIBUTING.md`)](./CONTRIBUTING.md)**: Setup (`install-core.sh` / `install-core.ps1`), worktree workflow, and `pytest` verification gates.

---

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
☕ **Support the project:** [Buy Me a Coffee](https://buymeacoffee.com/brianv1981)

---

<!-- AIM_ECOSYSTEM_START -->
### 🧬 The A.I.M. Ecosystem

J.O.S.H.U.A. (AIM-Joshua) is the foundational operating system in the larger A.I.M. (Actual Intelligent Memory) architecture.

To see how the sovereign OS, AI agents, MCP servers, and terminal multiplexers all connect, please visit the central ecosystem repository:

👉 **[The A.I.M. Ecosystem Directory](https://github.com/BrianV1981/aim-ecosystem)**
<!-- AIM_ECOSYSTEM_END -->
