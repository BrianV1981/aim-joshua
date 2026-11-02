# J.O.S.H.U.A. Handoff & Retrieval Protocols

This document formalizes the session closeout ("Agent Handoff") and LanceDB retrieval protocols across Linux, macOS, WSL, and Windows 10/11.

---

## The 3-Step Handoff Pipeline

When an agent's context window approaches capacity or a task shifts to a fresh session, execute an **Agent Handoff**:

### 1. Seal the Session into the Blackbox Vault
Before exiting the session, archive the raw session transcript into `<project_root>/archive/.raw_jsonl_blackbox/` using the harness-specific sealer:
- **Linux / macOS / WSL:** `./aim agy-blackbox --session-id <uuid>` (or `grok-blackbox`, `opencode-blackbox`, `codex-blackbox`)
- **Windows 10/11:** `.\aim.ps1 agy-blackbox --session-id <uuid>`

*(Note: Antigravity transcripts are resolved automatically across both Antigravity 2.0 `~/.gemini/antigravity/brain/` and legacy `~/.gemini/antigravity-cli/brain/`).*

### 2. Invoke `aim-handoff` (Auto-Wiki Delta + `HANDOFF.md`)
Invoke the `aim-handoff` skill to close out memory state in a single turn:
- **Step 1 — Idempotent Auto-Wiki Delta Check:** Inspect `memory-wiki/log.md` first. If session work or architectural decisions occurred since the last `/aim-memory-wiki` checkpoint, synthesize those updates into `memory-wiki/` (`index.md`, `log.md`, `pages/*.md`) and run `./aim index` (POSIX) or `.\aim.ps1 index` (Windows).
- **Step 2 — Surgical `HANDOFF.md` Update:** Append completed work to `§0` and update active mission/next steps (`0–9` template).
- **Step 3 — Direct-to-`main` Atomic Push:** Stage only explicit memory state and push directly to `origin/main` (when `origin` is configured) with zero prompts:
  ```bash
  git add memory-wiki/ HANDOFF.md
  git diff --cached --quiet || git commit -m "docs(handoff): update memory-wiki and HANDOFF.md for session closeout"
  git pull --rebase --autostash origin main
  git push origin main
  ```

### 3. Baton Pass
- **POSIX (`tmux`):** Optionally spawn or target a `tmux` session, paste the handoff prompt via `tmux load-buffer` + `tmux paste-buffer -p`, and submit `Enter` in a separate command (never send `Escape` before `Enter` in Antigravity 1.4.4+ / 2.0).
- **Windows 10/11 / IDE:** Leave `HANDOFF.md` ready at the repository root for the next session.

---

## Cross-Platform LanceDB Retrieval
1. **Primary (Native MCP):** Call the `search_lancedb` MCP tool (`joshua_os/.aim_core/mcp_lancedb.py`).
2. **Fallback (CLI):** Use the project wrapper (`./aim search "<query>"` on POSIX; `.\aim.ps1 search "<query>"` or `aim.cmd search "<query>"` on Windows) or the engine venv Python (`./joshua_os/venv/bin/python3 joshua_os/.aim_core/aim_cli.py search "<query>"` on POSIX; `.\joshua_os\venv\Scripts\python.exe joshua_os\.aim_core\aim_cli.py search "<query>"` on Windows — never bare `python3` on Windows).
