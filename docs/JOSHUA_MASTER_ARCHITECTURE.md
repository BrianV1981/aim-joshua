# JOSHUA & A.I.M. Connect: Master Architecture Document

**Date:** 2026-07-29
**System:** LeadDeeds Sovereign Intelligence Network

---

## 1. The High-Level Topology: Two Frontends, One Brain

The most frequent point of confusion when developing the LeadDeeds infrastructure is understanding the relationship between **JOSHUA** and **aim-connect**. 

To simplify: There is only **one backend**, but it serves **two completely different frontends**.

### The Backend: `aim-connect` (The Multiplexer)
At its core, `aim-connect` (running on FastAPI and Python) is a secure WebSockets router and `tmux` session multiplexer. It lives on your sovereign server and its primary job is managing isolated terminal sessions, routing PTY input/output streams over WebSockets, and enforcing cryptographic security. 

### Frontend 1: The Operator Admin Panel (`api.leaddeeds.com`)
*   **What it is:** This is the native frontend that ships inside the `aim-connect` repository. 
*   **Purpose:** Your remote server "God Mode" admin panel. 
*   **Access:** It is locked down behind a strict **3-Factor Authentication** wall (Stealth Passphrase + Password + TOTP). 
*   **Capabilities:** Full root-level terminal execution. From here, you can see every running `tmux` session, use the Web IDE, execute voice macros, and manage the entire LeadDeeds infrastructure.

### Frontend 2: JOSHUA (`www.leaddeeds.com/dashboard/analyst`)
*   **What it is:** The public-facing React chat interface (`AgentTerminal.tsx`) built into the LeadDeeds dashboard.
*   **Purpose:** A secure, interactive A.I. analyst for your LeadDeeds subscribers.
*   **Access:** Instead of 3FA, it connects to the `aim-connect` backend via the **Sovereign Agent Gateway**. It uses a "Magic Link" JWT token (signed with `LEADDEED_DOWNLOAD_SIGNING_SECRET`).
*   **Capabilities:** When `aim-connect` receives this token via WebSocket, it completely strips the user of root privileges. Instead, it spins up a sandboxed, isolated `tmux` session specifically for that user (e.g., `agent-client@email.com`) running an AI CLI (the "Harness").

---

## 2. JOSHUA: The Sandboxed Chatbot 

When a subscriber logs into LeadDeeds and clicks "Launch A.I. Analyst", they are transported to JOSHUA. 

Behind the glass, JOSHUA isn't a traditional web server API calling an LLM. It is actually a raw **terminal process** streaming securely to their browser via WebSockets. The user thinks they are in a chatbot, but they are actually typing into a sandboxed `stdin` and reading a formatted `stdout`.

### The Harness Fork: How the AI is booted
When JOSHUA initializes the WebSocket connection to `aim-connect`, the backend must spawn an AI agent in the terminal. The exact CLI binary it spawns is called the **Harness**.

Because LeadDeeds supports both free public users and you (the sovereign operator), the backend dynamically forks between two different Harnesses based on the user's tier and API key strategy:

#### A. OpenCode (`aim-opencode`) - The Public "BYOK" Route
*   **The Problem:** Google's free-tier developer APIs (like `gemini-3.5-flash-lite`) use standard API Keys (`GEMINI_API_KEY`). The flagship A.I.M. CLI (`agy`) rejects standard API keys and free-tier model strings, enforcing an enterprise OAuth flow instead.
*   **The Solution:** The **Bring Your Own Key (BYOK)** UI modal. JOSHUA prompts the user for their Google AI Studio API key. 
*   **The Wiring:** The React UI sends this key over the WebSocket during authentication. `aim-connect` reads it, and instead of spawning `agy`, it spawns `opencode run --pure -m google/gemini-3.5-flash-lite` inside the sandbox, passing the API key as an environment variable. 
*   **Result:** Public customers get 100% free, multi-provider AI chat without eating your corporate bandwidth.

#### B. Antigravity (`aim-agy`) - The Operator God-Mode Route
*   **The Problem:** As the admin, you want to use your premium effort-tier models (like `gemini-3.1-pro`) powered by your master OAuth subscription, without typing in a raw API key every time.
*   **The Solution:** The `admin-cli` harness option in the BYOK modal.
*   **The Wiring:** When you select this, `aim-connect` bypasses OpenCode entirely and spawns the flagship `/home/kingb/.local/bin/agy` binary, linking it directly to your server's master OAuth token file.
*   **Result:** You get unbridled access to the most powerful models natively within the chat UI.

---

## 3. The "Fleet" Architecture

JOSHUA features a **Fleet Orchestration** sidebar. This is a manifestation of `aim-connect`'s ability to run multiple simultaneous `tmux` sessions.

1.  **Primary Node:** The main conversational context.
2.  **Isolated Sub-Agents (Fleet):** If a user needs an agent to perform a long-running background task (like parsing 1,000 deeds), they can click "New Fleet Agent". 
3.  **Under the Hood:** The React frontend tells `aim-connect` to spawn a *new* `tmux` session with a randomly generated sub-session ID (e.g., `agent-client@email.com-chat-x7f9a`). The user can toggle between these instances in the UI, and the backend simply switches which `tmux` socket it is tailing and piping over the WebSocket.

---

## 4. End-to-End Encryption (E2EE) & Security

Because JOSHUA is routing real terminal input/output over the web, security is paramount.

1.  **Transport Layer:** Standard `wss://` over Cloudflare/NGINX.
2.  **Application Layer:** JOSHUA implements `E2EESocketWrapper.ts`. Even before the chat text hits the WebSocket, it is AES-GCM encrypted using a shared secret. `aim-connect` decrypts it on the server. If a middlebox or proxy intercepts the packets, they only see scrambled byte arrays.
3.  **File Interception:** When the agent generates a file (like a CSV of leads) and prints a local path (e.g., `file:///path/to/leads.csv`), the React frontend hijacks the Markdown renderer. It converts that path into a secure download link hitting `aim-connect`'s `/download` endpoint, appending the user's JWT token to prove they have the rights to download that specific artifact from the server.

## 5. Fleet Agents & OS Sandboxing (`bwrap`)

JOSHUA enforces strict boundary constraints via OS-level sandboxing:
- **Primary Node:** Has broader access (`harness-opencode`).
- **Fleet Agents:** Restricted sub-sessions. They operate strictly within `fleet_workspaces/<sub_id>`.
- The `bwrap` container mounts the host filesystem as read-only (`--ro-bind / /`), meaning any attempt by a sandboxed agent to modify files outside its explicitly bound workspace directory (`--bind`) will physically fail at the OS level with a `Read-only file system` error.

## 6. Interactive Permission Bypassing (`--auto`)

Because OpenCode is an interactive CLI tool, it natively pauses execution to present permission modals (e.g., `△ Permission required: Access external directory`) when an agent attempts to violate its directory constraints. 
- In a headless setup running over `tmux`, these UI modals block execution indefinitely and cause the backend WebSocket bridging to hit inactivity timeouts (120 seconds).
- **The Solution:** The OpenCode process is launched with the `--auto` flag. This automatically approves permissions, bypassing the modal. Because the agent is encased in `bwrap`, it does not grant actual file access; instead, the action hits the OS wall and immediately fails, allowing the agent to see the failure and continue chatting without hanging the connection.

## 7. Real-Time SQLite WAL Polling

The JOSHUA backend natively intercepts the conversation history in real-time by polling the active SQLite database (`opencode.db`) produced by the sandboxed OpenCode process.
- **The Challenge:** OpenCode uses SQLite in Write-Ahead Log (WAL) mode. When the Python backend queries the database, standard connections can inadvertently unlink or delete the `-wal` and `-shm` files upon closure (`conn.close()`), destroying the open file descriptors of the sandboxed OpenCode process and crashing it ("Connection closed by remote node").
- **The Solution:** The backend MUST connect to the SQLite database strictly using URI parameters `?mode=ro`. A read-only SQLite connection (`mode=ro`) correctly bypasses acquiring disruptive locks and inherently avoids checkpointing or deleting the `-wal` file when the connection is closed.
- **Warning:** Do *not* use `nolock=1` in the connection string. While it prevents lock collisions, `nolock=1` entirely disables SQLite's ability to read `-wal` files. This causes complex `JOIN` queries against the live database to fail with an `unable to open database file` error.

---

## Summary Cheat Sheet

*   `aim-connect` = The Python WebSockets backend, `tmux` manager, and terminal router.
*   `api.leaddeeds.com` = The `aim-connect` frontend React app (Admin Panel, 3FA, raw shell access).
*   `www.leaddeeds.com/dashboard/analyst` = JOSHUA (The LeadDeeds frontend, JWT auth, Sandboxed PTY).
*   **Harness** = The actual CLI binary spawned inside the `tmux` session (`aim-opencode` for BYOK users, `aim-agy` for Admin).
*   **BYOK** = Injecting standard API keys via UI to bypass AGY's enterprise OAuth constraints, utilizing free-tier AI Studio models.
