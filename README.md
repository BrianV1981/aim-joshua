# J.O.S.H.U.A.
**Joint Operational Systems for Heuristic User Automation**

J.O.S.H.U.A. is an open-source, CLI-agnostic Operating System designed to serve as the foundational brain, memory, and infrastructure for autonomous AI coding agents. External LanceDB (RAG) memory, GitOps guardrails, Parquet "Datajack" knowledge cartridges. Alpha, trenches-first.

## 🚀 Quickstart & Installation

J.O.S.H.U.A. requires **Linux** or **WSL (Ubuntu)**, Node.js v20+, and your preferred underlying LLM CLI.

### Option A: The Universal Sandbox (Recommended)
Installs the universal engine, sets up the Git sandbox, and provides the AI with a clean, lightweight shell.

```bash
curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/setup.sh | bash
```

### Option B: The Core Contributor
Preserves the GitHub connection and all internal testing folders for developing the OS itself.

```bash
curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/setup-core.sh | bash
```

---

## 🔥 Core Capabilities

J.O.S.H.U.A. provides a massive suite of tools to control, manage, and scale your AI agents:

*   **Universal Sandbox Protocol:** Every agent gets a localized, bubble-wrapped environment. 
*   **Decentralized Updates:** Independent nodes can pull core OS updates without conflicting with their local `.git` histories.
*   **Embedded Local Memory:** Tenant data remains strictly localized. The RAG database is instantiated inside the sandbox, not the global OS root.
*   **CLI-Agnostic Skill Injection:** Decoupled from any specific CLI. Tool parsing is modularized via the `aim-skill-library`.
*   **GitOps Enforcement:** Agents must create issues, branch out, and deploy atomically.
*   **Ephemeral Context Handoffs:** When the context window fills up, the `aim-handoff` skill automatically captures tactical state and teleports the context to a fresh vessel via `tmux`.
*   **Anti-Drift Shield:** A background hook continuously tracks autonomous tool calls.

---

## 🧬 The A.I.M. Ecosystem (The Daily Driver Stack)

Modular A.I.M. (Actual Intelligent Memory) repositories. While the original architecture relied on separate CLI harnesses, **J.O.S.H.U.A.** is the convergence point that unifies the active vessels under a single, agnostic operating system.

**Active vessels (CLI hosts):**
- **[aim-joshua](https://github.com/BrianV1981/aim-joshua)** — The Universal Operating System convergence point.

**Tools & workspaces:**
- **[aim-dash](https://github.com/BrianV1981/aim-tmux-dashboard)** — Terminal multi-session monitor and daily cockpit.
- **[aim-connect](https://github.com/BrianV1981/aim-connect)** — Self-hosted remote workspace web UI.
- **[aim-skill-library](https://github.com/BrianV1981/aim-skill-library)** — Skills index / multi-CLI install registry. Home of the sleeper powerhouse: **`aim-communicate`**.
- **[aim-browser](https://github.com/BrianV1981/aim-browser)** — Headed Chromium CDP engine + browser skill suite.
- **[aim-google](https://github.com/BrianV1981/aim-google)** — Google Workspace CLI (Gmail, Drive, Calendar, …).
- **[aim-flight-recorder](https://github.com/BrianV1981/aim-flight-recorder)** — Forensic Markdown session extractor.
- **[aim-boardroom](https://github.com/BrianV1981/aim-boardroom)** — Multi-agent orchestration room (OS multiplexing + artifacts).

**DNA, comms & lore:**
- **[aim-coagents](https://github.com/BrianV1981/aim-coagents)** — DNA bank for sovereign co-agent blueprints.
- **[aim-knowledge](https://github.com/BrianV1981/aim-knowledge)** — Public Obsidian vault / deep-lore archive.
- **[aim-chalkboard](https://github.com/BrianV1981/aim-chalkboard)** — Optional cross-host async git mailbox (PoC; default same-host comms = aim-communicate skill).

**Deprecated / not maintained:**
- **aim-agy** — Legacy Core engine (Antigravity CLI). Deprecated in favor of aim-joshua.
- **aim-grok** — Legacy Grok CLI vessel. Deprecated in favor of aim-joshua.
- **aim-opencode** — Legacy OpenCode CLI vessel. Deprecated in favor of aim-joshua.
- **aim-codex** — Legacy OpenAI Codex CLI vessel. Deprecated in favor of aim-joshua.
- **aim-claude / Anthropic-line vessels** — Done. Operator does not develop against Anthropic. Deprecated in favor of aim-joshua.
- **aim-skills** — Deprecated private repository. Replaced by `aim-skill-library`.
- **aim** — Original Gemini CLI framework. Deprecated after loss of practical subscription access.
- **aim-swarm** — Legacy Python swarm factory.

---

## 📖 Documentation & Philosophy

- **[The Official J.O.S.H.U.A. Wiki](https://github.com/BrianV1981/aim-joshua/wiki)**: The primary onboarding ramp. Includes step-by-step user guides, configuration variables, and tutorials.

---

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
☕ **Support the project:** [Buy Me a Coffee](https://buymeacoffee.com/brianv1981)
