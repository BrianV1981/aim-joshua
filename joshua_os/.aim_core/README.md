# A.I.M. Core Engine (`src/`)

This directory contains the internal Python engine that powers the A.I.M. exoskeleton. These files are typically NOT invoked directly by the Operator; they are called by the `aim_core/aim_cli.py` router, the background `daemon`, or the Antigravity CLI `hooks/`.

## Key Components
*   **`reasoning_utils.py`**: The API Bridge. Handles routing payloads to Google Antigravity, Anthropic, OpenRouter, Codex, or Local Ollama. It manages subprocess execution and parses stdout/stderr to protect the agent from brittle CLI outputs.
*   **`plugins/datajack/forensic_utils.py`**: Contains the RAG 5.21 Length-Constrained Accumulator chunking algorithm, embedding functions, and ingestion utilities.
*   **`mcp_server.py`**: The Universal IDE interface. Runs a FastMCP server that exposes the A.I.M. database and skills directly to Cursor, Claude Code, or VS Code.
*   **`retriever.py` & `lance_backend.py`**: The core Hybrid RAG memory engine powered by LanceDB.