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

---

## Summary Cheat Sheet

*   `aim-connect` = The Python WebSockets backend, `tmux` manager, and terminal router.
*   `api.leaddeeds.com` = The `aim-connect` frontend React app (Admin Panel, 3FA, raw shell access).
*   `www.leaddeeds.com/dashboard/analyst` = JOSHUA (The LeadDeeds frontend, JWT auth, Sandboxed PTY).
*   **Harness** = The actual CLI binary spawned inside the `tmux` session (`aim-opencode` for BYOK users, `aim-agy` for Admin).
*   **BYOK** = Injecting standard API keys via UI to bypass AGY's enterprise OAuth constraints, utilizing free-tier AI Studio models.
