# Testing, Validation & The TDD Reflex

This document defines the mandatory verification standards for all J.O.S.H.U.A. engine, CLI, and project code changes.

## 1. Zero Blind Output ("No Vibe Coding")
Generating code that "looks plausible" without executing real tests is strictly prohibited. Every bug fix, CLI route, path resolver, or RAG behavior change must be proven empirically before promotion to `main`.

## 2. The TDD Workflow
1. **Reproduce First:** Write or extend an automated `pytest` test case under `tests/` that reproduces the bug or specifies the new contract.
2. **Implement Cleanly:** Apply surgical changes inside your isolated `workspace/issue-<id>` worktree.
3. **Run the Full Warning-Clean Test Gate:**
   ```bash
   # Linux / macOS / WSL
   ./joshua_os/venv/bin/python3 -m pytest tests/ -W error::DeprecationWarning

   # Windows 10/11 (PowerShell)
   .\joshua_os\venv\Scripts\python.exe -m pytest tests\ -W error::DeprecationWarning
   ```
4. **Cross-Platform CI Parity:** GitHub Actions (`.github/workflows/smoke-test.yml`) runs both `ubuntu-latest` and `windows-latest` matrix legs on pushes and pull requests. Never introduce POSIX-only path assumptions (`while current != '/':`, unguarded `fcntl`, GNU-only `sed -i`, or bare `python3` subprocesses on Windows).

## 3. Context Hygiene & Sprint Handoffs
Long-horizon agent sessions lose precision as context windows saturate. Treat complex multi-phase sprints as clean relays: checkpoint durable discoveries mid-session with `/aim-memory-wiki`, and when context pressure builds, seal the session (`./aim <vessel>-blackbox --session-id <id>`) and execute `/aim-handoff` to pass a verified `HANDOFF.md` to a fresh agent session.
