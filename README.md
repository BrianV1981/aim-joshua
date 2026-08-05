# J.O.S.H.U.A. (Universal Agentic OS)

J.O.S.H.U.A. is an open-source, CLI-agnostic Operating System designed to serve as the foundational brain, memory, and infrastructure for autonomous AI coding agents. 

It solves context amnesia, token bloat, state loss, and drift in long-running sessions by providing a persistent, isolated, and highly-structured environment that **any agent** can plug into.

**This repository represents the culmination of the A.I.M. ecosystem.** 
It officially deprecates and consolidates the previous fragmented architecture (`aim-agy`, `aim-opencode`, `aim-grok`, and `aim-codex`) into a single, unified, universal foundation.

> **The Vision:** "One OS, Any Harness." Install J.O.S.H.U.A. into a project directory. You can boot up OpenCode, switch to Antigravity 20 minutes later, and finish your session in Grok. They all share the same memory, the same rules, the same Git ledger, and the same toolset natively.

## 🚀 Quickstart & Installation

J.O.S.H.U.A. requires **Linux** or **WSL (Ubuntu)** and Python 3.10+.

### Spawn a Universal Sandbox
The safest way to spawn a fresh, isolated project from the OS blueprint is to use the clean installer. This pulls the immutable `joshua_os` engine and configures a pristine, CLI-agnostic workspace without polluting your global git history.

```bash
mkdir my-new-idea && cd my-new-idea
curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install-clean.sh | bash
source ~/.bashrc
```

### Interact with the OS
Once installed, your directory becomes a JOSHUA node. You can interact with the OS layer directly via the injected alias:
```bash
aim-my-new-idea status
aim-my-new-idea doctor
aim-my-new-idea tui
```

### Plug in Your Agent
Simply navigate into your JOSHUA-powered folder and launch your favorite CLI harness (Antigravity, OpenCode, Grok, etc.). The agent will natively read the universal `AGENTS.md` and immediately inherit the project's LanceDB memory, GitOps rules, and customized toolkit.

---

## 🔥 Core Capabilities

J.O.S.H.U.A. provides an enterprise-grade suite of tools to control, manage, and scale your AI agents regardless of the CLI they use:

*   **Universal Sandbox Protocol:** Every session gets its own local `.git` ledger. When the agent completes a task, the OS automatically fires a teardown hook that commits the vector memory state to the local git ledger, creating an immutable time-machine of the agent's brain.
*   **Opt-In Bubblewrap (bwrap) Jails:** Hardened enterprise isolation for SaaS integration (e.g., LeadDeeds). Agents can be spawned inside an impenetrable read-only jail, completely protecting the host PC while retaining access to their specific sandbox.
*   **Embedded LanceDB Memory (RAG 5.21):** Replaces standard sliding-window context with a high-fidelity, columnar vector database strictly localized to the tenant's sandbox. Features Native Hybrid Search (Ollama semantics + Tantivy FTS).
*   **Decentralized Git-Less Updates:** Independent nodes can pull core OS engine updates directly via ZIP extraction, bypassing Git entirely so it never conflicts with the tenant's local ledgers.
*   **GitOps Enforcement:** AI agents are forbidden from coding on `main`. They must create GitHub issues (`aim bug`), branch out into isolated worktrees (`aim fix`), use TDD, and deploy atomically (`aim push`).
*   **Interactive TUI Cockpit:** A visual terminal interface (`aim tui`) to configure guardrails and project context without editing JSON files.
*   **Background Markdown Generation:** A deterministic Python script strips terminal noise, reducing context weight by 85%. A background daemon then weaves this into a human-readable Markdown wiki (`memory-wiki/`).
*   **P2P Knowledge Cartridges:** Package thousands of pages of documentation into pre-vectorized native Apache Arrow `.parquet` files. Share and download them peer-to-peer to give agents instant recall of entire frameworks without burning API tokens.
*   **Universal IDE Support (MCP):** A built-in FastMCP server exposes the memory databases to any connected IDE (Cursor, VS Code, Claude Desktop) without requiring platform-specific adapters.

---

## 📖 The Great Consolidation

In mid-2026, the A.I.M. ecosystem suffered from severe repository bloat. Every time a new CLI was released, a new OS repository was forked (`aim-agy`, `aim-opencode`, `aim-grok`, `aim-codex`), creating massive technical debt and conflicting tool configurations.

J.O.S.H.U.A. represents the "Great Consolidation." 
By abstracting the OS layer completely away from the CLI layer, we achieved a true Universal OS. All legacy vessel repositories are now deprecated.

**The Current Architecture:**
* **`aim-joshua`**: The single, flagship repository. It contains the universal `joshua_os` engine.
* **`aim-skills`**: The modular library where CLI-specific syntaxes, custom tools, and agent behaviors can be optionally injected into JOSHUA via the `AGENTS.md` blueprint.
* **`aim-connect`**: The Web UI and WebSocket gateway for managing remote JOSHUA sandboxes.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
☕ **Support the project:** [Buy Me a Coffee](https://buymeacoffee.com/brianv1981)
