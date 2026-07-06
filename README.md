# A.I.M. (Actual Intelligent Memory) — aim-opencode

A.I.M. is an open-source engineering exoskeleton designed to solve context amnesia, token bloat, state loss, and drift in long-running autonomous AI coding sessions.

**This repository** is the [OpenCode CLI](https://github.com/opencode-ai/opencode) adaptation of A.I.M. For the primary "Soul" of the project (built for Antigravity CLI), see [aim-agy](https://github.com/BrianV1981/aim-agy).

## 🚀 Quickstart & Installation

A.I.M. requires **Linux** or **WSL (Ubuntu)**, Node.js v20+, and [OpenCode CLI](https://github.com/opencode-ai/opencode).

```bash
git clone https://github.com/BrianV1981/aim-opencode.git
cd aim-opencode
./setup.sh
source ~/.bashrc
```

### Initialize a Project
```bash
mkdir ~/my-new-project && cd ~/my-new-project
aim-opencode init
```
*(During `aim-opencode init`, select 'y' to perform a Clean Sweep to sever git history and wipe internal docs).*

### Configure Your AI Providers
Launch the interactive dashboard to set your API keys, local Ollama models, and configure the background Wiki daemon.
```bash
aim-opencode tui
```

---

## 🔥 Core Capabilities

A.I.M. provides a massive suite of tools to control, manage, and scale your AI agents:

*   **Embedded LanceDB Memory (RAG 5.21):** Replaces standard sliding-window context with a high-fidelity, columnar vector database featuring Native Hybrid Search (Ollama semantics + Tantivy FTS) and an Entity Intersection Reranker.
*   **Background Markdown Generation:** A deterministic Python script strips terminal noise, reducing context weight by 85%. A background daemon then weaves this into a human-readable Markdown wiki (`memory-wiki/`).
*   **GitOps Enforcement:** AI agents are forbidden from coding on `main`. They must create GitHub issues (`aim-opencode bug`), branch out into isolated worktrees (`aim-opencode fix`), use TDD, and deploy atomically (`aim-opencode push`).
*   **Interactive TUI Cockpit:** A visual terminal interface (`aim-opencode tui`) to configure LLM routing, guardrails, and context limits without editing JSON files.
*   **Cognitive Routing:** Route expensive coding tasks to flagship models (e.g., DeepSeek) in your terminal, while offloading repetitive background tasks (like memory indexing) to free, local models (e.g., Ollama) on your GPU.
*   **P2P Knowledge Cartridges:** Package thousands of pages of documentation into pre-vectorized native Apache Arrow `.parquet` files. Share and download them peer-to-peer via BitTorrent (`aim-opencode export` / `aim-opencode jack-in`) to give agents instant recall of entire frameworks without burning API tokens.
*   **Universal IDE Support (MCP):** A built-in FastMCP server exposes the memory databases to any connected IDE (Cursor, VS Code, Claude Desktop) without requiring platform-specific adapters.
*   **Crash Recovery & Handoffs:** When the context window fills up, run `aim-opencode reincarnate` to extract active context and spawn a fresh terminal session. If the CLI crashes, run `aim-opencode crash` to salvage the interrupted session.
*   **Anti-Drift Shield:** A background hook continuously tracks autonomous tool calls. Every 50 actions, it forcefully halts execution and requires the agent to recite its GitOps rules, preventing "Lost in the Middle" context degradation.
*   **Peer-to-Peer Wiki Sync (Syncthing):** Offload heavy memory compilation to a secondary server by syncing the `memory-wiki/` folder natively via Syncthing.

---

## 📖 Documentation & Philosophy

A.I.M. separates fast onboarding documentation from deep philosophical essays and architectural diagrams.

- **[The Official A.I.M. Wiki](https://github.com/BrianV1981/aim/wiki)**: The primary onboarding ramp. Includes step-by-step user guides, configuration variables, and tutorials.
- **[The A.I.M. Knowledge Base (Public Obsidian Vault)](https://github.com/BrianV1981/aim-wiki)**: A massive, decentralized digital garden containing raw benchmark JSON logs, architectural design history, and the complete "vibe coding" origin story.

---

### 🧬 The A.I.M. Ecosystem

> ⚠️ **ARCHITECTURAL SHIFT NOTICE**
> Google has sunset the original `gemini-cli` for standard subscribers, restricting it to Enterprise environments. As a result, **[aim-agy](https://github.com/BrianV1981/aim-agy) is now the primary "Soul" of the project.** The core architectural decisions, the memory logic, and the central integrations happen there first before being ported to the external adaptations.

| Repo | CLI Target | Status |
|------|-----------|--------|
| [aim-agy](https://github.com/BrianV1981/aim-agy) | Antigravity (`agy`) | **Primary Soul** — active development |
| **aim-opencode** (this repo) | [OpenCode](https://github.com/opencode-ai/opencode) | Active — maintained adaptation |
| [aim](https://github.com/BrianV1981/aim) | Gemini CLI (original) | Sunset — enterprise only |

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
☕ **Support the project:** [Buy Me a Coffee](https://buymeacoffee.com/brianv1981)
