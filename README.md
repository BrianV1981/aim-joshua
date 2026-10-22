# J.O.S.H.U.A.
**Joint Operational Systems for Heuristic User Automation**

J.O.S.H.U.A. is an open-source, CLI-agnostic Operating System designed to serve as the foundational brain, memory, and infrastructure for autonomous AI coding agents. External LanceDB (RAG) memory, GitOps guardrails, Parquet "Datajack" knowledge cartridges. Alpha, trenches-first.

## 🚀 Quickstart & Installation

J.O.S.H.U.A. requires **Linux** or **WSL (Ubuntu)**, Python 3.10+, Node.js v20+, and your preferred underlying LLM CLI (Antigravity, Grok, OpenCode, Codex, etc.).

> **⚠️ IMPORTANT (Target Directory Rule):** All installers scaffold J.O.S.H.U.A. **directly into your current working directory (`pwd`)** and register a bash CLI alias matching the folder name (`basename $(pwd)`). Always create and `cd` into your target project directory **before** running the installer.

| Option | Installer Script | Best For | `AGENTS.md` Installed | Upstream `.git` / `tests/` |
|--------|------------------|----------|-----------------------|----------------------------|
| **Option A (Default)** | `joshua_os/install.sh` | New or existing software projects | Full 10-section J.O.S.H.U.A. `AGENTS.md` (`cp -n`, never overwrites existing) | Stripped (clean project root) |
| **Option B (Co-Agent)** | `joshua_os/install-agent.sh [persona]` | Specialist peer nodes under `~/aim-agents/<name>` | Specialist blueprint from `aim-coagents` if `[persona]` is passed; otherwise full 10-section `AGENTS.md` | Stripped (isolated node) |
| **Option C (Contributor)** | `joshua_os/install-core.sh` | Developing the J.O.S.H.U.A. OS engine itself | Upstream `aim-joshua/AGENTS.md` | Preserved (`tests/`, `memory-wiki/`, `.git`) |

### Option A: Clean Project Installation (Default — New or Existing Projects)
Installs the `joshua_os/` engine, local `./aim` wrapper, project-specific `memory_lance/` database, `search_lancedb` MCP server, and default `AGENTS.md` / `TOOLS.md` blueprints into your project directory without `aim-joshua` contributor history.

```bash
# 1. Create and enter your project directory (the folder name becomes your CLI alias)
mkdir -p ~/my-project && cd ~/my-project

# 2. Run the clean installer
curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install.sh | bash

# 3. Reload shell and verify installation
source ~/.bashrc
my-project doctor
```

### Option B: Headless Co-Agent (Sovereign Node)
Deploys a stripped-down, headless Sovereign Co-Agent node (ideal for specialist peers under `~/aim-agents/<node-name>` paired with a blueprint from `aim-coagents`). Pass an optional persona name (`python-developer`, `aim-auditor`, `lead-analyst`, etc.) to pull that specialist `AGENTS.md` blueprint automatically, or omit it to use the default 10-section J.O.S.H.U.A. `AGENTS.md`.

```bash
mkdir -p ~/aim-agents/my-agent && cd ~/aim-agents/my-agent
curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install-agent.sh | bash -s python-developer
source ~/.bashrc
my-agent doctor
```

### Option C: Core Contributor Installation
Installs the universal engine while preserving the `aim-joshua` `.git` history, test suites (`tests/`), and `memory-wiki/` for developing J.O.S.H.U.A. itself.

```bash
mkdir -p ~/aim-joshua-dev && cd ~/aim-joshua-dev
curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install-core.sh | bash
```

### Customizing J.O.S.H.U.A. for Your New Project
Once installed in your project directory:
1. **Personalize Identity & Rules (`AGENTS.md`):**
   - **Automatic Turn-1 Prompt or Direct Edit:** The default `AGENTS.md` includes `- **Operator Name:** [ASK OPERATOR FOR THEIR NAME AND FILL IT IN HERE USING FILE EDIT TOOLS]`, instructing your agent on Turn 1 to ask your name and update `AGENTS.md` in place. You can also edit `AGENTS.md` (and `TOOLS.md`) directly to define your project's domain architecture, tech stack, and specific rules, or copy a specialist blueprint from [`aim-coagents`](https://github.com/BrianV1981/aim-coagents).
   - **Interactive Onboarding Interview (`./aim init`):** Alternatively, run `./aim init` to launch the interactive Onboarding Architect (`joshua_os/BOOTSTRAP.md`) in a `tmux` session, which interviews you for your Operator Name, tech stack, and mission and updates `AGENTS.md` (`## 1` and `## 11`) while preserving all 10 core OS sections.
2. **Initialize Project Knowledge (`memory-wiki/` & LanceDB):** Add project documentation in `memory-wiki/` (or any docs folder) and vectorize it into your project's isolated LanceDB database:
   ```bash
   ./aim index
   # Or ingest a custom documentation directory:
   ./aim index --dir ./docs
   ```
3. **Keep the Engine Updated:** At any time, pull the latest J.O.S.H.U.A. engine into your project without overwriting your custom `AGENTS.md`, `TOOLS.md`, `memory-wiki/`, or `CONFIG.json`:
   ```bash
   ./aim update
   ```

### Universal Skill Injection (Required Once Per Host CLI)
Because J.O.S.H.U.A. is CLI-agnostic, skills are not hardcoded into the OS. Clone the central skill library once and link the skills into your preferred CLI vessel:

```bash
git clone https://github.com/BrianV1981/aim-skill-library.git ~/aim-skill-library
cd ~/aim-skill-library

# Example: Install globally for the 'agy' vessel
./scripts/install.sh --vessel agy --dest ~/.gemini/antigravity-cli/builtin/skills --mode symlink
```

---

## 🔥 Core Capabilities

J.O.S.H.U.A. provides a massive suite of tools to control, manage, and scale your AI agents:

*   **Universal OS Framework:** J.O.S.H.U.A. runs natively as the foundational brain for autonomous coding agents.
*   **Headless Deployment:** Co-agents can be deployed securely into localized project repositories via the `install-agent.sh` Sovereign Node installer.
*   **Embedded Local Memory:** The RAG database (LanceDB) is stored locally. In sandboxed mode, memory is strictly tenant-specific.
*   **CLI-Agnostic Skill Injection:** Decoupled from any specific CLI. Tool parsing is modularized via the `aim-skill-library`.
*   **GitOps Enforcement (with Memory-State Exemption):** Application code and configuration changes strictly require GitHub Issues and isolated `workspace/issue-<id>` worktrees (`./aim fix` → TDD → `./aim promote`), while living Agent Memory (`memory-wiki/**` and `HANDOFF.md`) commits and pushes directly to `origin/main` with zero prompts.
*   **Autonomous Memory Wiki & One-Command Handoffs:** `/aim-memory-wiki` runs as a ~15-second mid-session "Save Game" checkpoint directly to `main`, and `/aim-handoff` automatically checks `memory-wiki/log.md` for unlogged session deltas, surgically updates `HANDOFF.md` (`0–9` template), pushes both to `origin/main` in a single atomic commit, and optionally passes the baton to a fresh vessel via `tmux`.
*   **Anti-Drift Shield:** A background hook continuously tracks autonomous tool calls.

---

## 📖 Documentation & Philosophy

- **[The Official J.O.S.H.U.A. Wiki](https://github.com/BrianV1981/aim-joshua/wiki)**: The primary onboarding ramp. Includes step-by-step user guides, configuration variables, and tutorials.

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

