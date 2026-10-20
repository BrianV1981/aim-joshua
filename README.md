# J.O.S.H.U.A.
**Joint Operational Systems for Heuristic User Automation**

J.O.S.H.U.A. is an open-source, CLI-agnostic Operating System designed to serve as the foundational brain, memory, and infrastructure for autonomous AI coding agents. External LanceDB (RAG) memory, GitOps guardrails, Parquet "Datajack" knowledge cartridges. Alpha, trenches-first.

## 🚀 Quickstart & Installation

J.O.S.H.U.A. requires **Linux** or **WSL (Ubuntu)**, Node.js v20+, and your preferred underlying LLM CLI.

J.O.S.H.U.A. can be installed as a native, globally accessible operating framework, or deployed as a headless Sovereign Co-Agent within individual project directories for multi-tenant isolation.

### Option A: Clean Installation (Default)
Installs the universal engine natively with a completely fresh footprint (purges Git history and developer files). This is the recommended approach for standard users and daily driver use.

```bash
curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install.sh | bash
```

### Option B: Core Contributor Installation
Installs the universal engine but preserves the `.git` directory, test suites, and benchmarks for those looking to develop or contribute to J.O.S.H.U.A.

```bash
curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install-core.sh | bash
```

### Option C: Headless Co-Agent (Sovereign Node)
Sets up a stripped-down, headless environment for autonomous co-agents. Ideal for deploying J.O.S.H.U.A. directly into individual project repositories without global OS footprint overhead.

```bash
curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install-agent.sh | bash
```

### Universal Skill Injection (Required)
Because J.O.S.H.U.A. is CLI-agnostic, skills are not hardcoded into the OS. You must clone the central skill library and inject them universally into your preferred CLI vessel:

```bash
git clone https://github.com/BrianV1981/aim-skill-library.git
cd aim-skill-library

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
*   **GitOps Enforcement:** Agents must create issues, branch out, and deploy atomically.
*   **Ephemeral Context Handoffs:** When the context window fills up, the `aim-handoff` skill automatically captures tactical state and teleports the context to a fresh vessel via `tmux`.
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

