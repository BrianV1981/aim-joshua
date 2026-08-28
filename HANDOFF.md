# J.O.S.H.U.A. — Engineering Handoff

> **Updated:** 2026-08-28T04:50:00-04:00
> **Updated by:** Antigravity (Session ID: 4c79e879-edd0-4056-b078-51fd015670d2)
> **Priority Mission:** STANDBY / Awaiting Directives
> **Operator:** The Operator

---

## 0. COMPLETED WORK (DO NOT REVISIT)
| Session | Work | Status |
|---------|------|--------|
| prior | Overhauled TUI & Purged Reincarnation (#74–#77) | ✅ SHIPPED |
| 73f2d8d9 | #78: Migrate LanceDB Search to MCP Server (`mcp_lancedb.py`) | ✅ RESOLVED |
| 73f2d8d9 | #79: Docs: Update AGENTS.md for Two-Tier Retrieval Protocol | ✅ RESOLVED |
| 73f2d8d9 | #80: Wiki: Update architecture.md for MCP Two-Tier Protocol | ✅ RESOLVED |
| c00d7f1a | #81: Pytest for MCP/Ingestion & Recursive glob fix | ✅ RESOLVED |
| c00d7f1a | #82: CLI router parameter forwarding fix (`aim index`) | ✅ RESOLVED |
| c00d7f1a | #83: memory-wiki sync for configuration drift fixes | ✅ RESOLVED |
| 4c79e879 | #84: Implemented DHH Agentic Era Protocols in AGENTS.md | ✅ RESOLVED |
| 4c79e879 | #85: Refactored AGENTS.md to remove tool-dependent Herder protocol | ✅ RESOLVED |
| 4c79e879 | #86: Wiki: Logged DHH Agentic Philosophy into Memory Wiki | ✅ RESOLVED |

*(Keep clean and consolidated. Point to wiki/issues for deep history — do not re-audit.)*

---

## 1. PROJECT IDENTITY
J.O.S.H.U.A. is the CLI-agnostic OS brain for A.I.M. agents: nested `joshua_os/`, GitOps worktrees, LanceDB hybrid memory, blackbox vault, GitHub Projects CLI.

### Your Knowledge Base
- `/home/kingb/aim-joshua/memory-wiki/index.md` (The active LLM Wiki Index)
- `/home/kingb/aim-joshua/AGENTS.md` (The sovereign agent blueprint and OS rules)
- `/home/kingb/aim-joshua/memory-wiki/pages/handoff-and-retrieval.md` (Retrieval mechanics)
- `/home/kingb/aim-joshua/memory-wiki/pages/architecture.md` (Two-Tier MCP Protocol)
- `/home/kingb/aim-joshua/memory-wiki/pages/dhh-agentic-philosophy.md` (Core Agentic Directives)

---

## 2. YOUR MISSION: STANDBY
The backlog is currently clear. You are awaiting explicit operator directives. 

### Execution Queue (in order)
#### 1️⃣ Await Orders
**Problem:** No active tickets.
**Fix:** Parse operator input and execute via GitOps workflow.
**Key files:** N/A

---

## 3. DETAILED ANALYSIS / BREAKDOWN
- **Two-Tier Retrieval Protocol:** The retrieval architecture has fundamentally shifted. If you are operating in a modern CLI harness (like AGY), you will natively possess the `search_lancedb` internal tool. This MCP server dynamically locates the vector database using a workspace handshake. If you are operating in a legacy CLI that lacks MCP, you must gracefully degrade to `python3 joshua_os/.aim_core/aim_cli.py search`. Do not assume tools exist if they are not in your prompt.
- **GitOps Enforcement:** Never code on `main`. Always `aim fix <id>` to branch into a worktree sandbox.
- **Vector Ingestion (Index):** Ingestion is fully parameterized. Custom directories can be ingested into the LanceDB RAM pool by executing `aim index --dir <path>`. This command also handles recursive directory crawling seamlessly.
- **Testing Framework:** The core Python modules (`mcp_lancedb.py`, `bootstrap_brain.py`) now enforce Pytest unit testing using `unittest.mock`.
- **DHH Agentic Philosophy:** The OS now runs on outcome-oriented directives. The Operator supplies the "what/why" (the fuzzy problem), and agents determine the "how" (architecture, routing). The agent acts as an automated gatekeeper during `aim promote`, ensuring TDD and architectural rules are strictly followed before hitting main.
- **Plain-Text Ascendancy:** J.O.S.H.U.A. relies on the Unix Philosophy. All configs, wikis, and tasks must be CLI-accessible flat files (Markdown, JSON) avoiding opaque GUIs.

---

## 4. IMPLEMENTATION STRATEGY
Follow strict GitOps workflow for any future tasks:
1. `aim bug "Title"` to create a structured issue.
2. `aim projects in-progress <id>` (Board is `#7`)
3. `aim fix <id>`
4. Work in the `workspace/issue-<id>` worktree.
5. `aim push` (Ensure `git add` is used for untracked files).
6. `aim promote`
7. `aim projects done <id>`

---

## 5. THE CRITICAL TRAPS & WARNINGS
> **⚠️ EPISTEMIC / OPERATIONAL WARNINGS**
- **The Worktree Mandate:** NEVER perform development directly on `main`. You must use `aim fix <id>`. 
- **The `aim-memory-wiki` Prerequisite:** You MUST run `/aim-memory-wiki` to synthesize new architecture changes *before* executing `/aim-handoff`.
- **The Blackbox Mandate:** Before an agent vessel dies, it MUST execute its vessel-specific vault command (e.g. `aim agy-blackbox --session-id <uuid>`) to extract raw session logs. 
- **The Audit Protocol:** Do not close issues or claim success if the GitHub Actions smoke test is red.
- **The Untracked File Trap:** The OS `aim_push.sh` script ignores untracked files by default due to a `git add -u` quirk. You must run `git add <file>` manually before `aim push` for new files.

---

## 6. KEY PATHS
- `/home/kingb/aim-joshua/joshua_os/`
- `/home/kingb/aim-joshua/memory-wiki/`
- `/home/kingb/aim-joshua/joshua_os/.aim_core/mcp_lancedb.py`
- `/home/kingb/aim-joshua/tests/` (Pytest Coverage)
- `/home/kingb/aim-joshua/joshua_os/.aim_core/aim_cli.py` (CLI Router)

---

## 7. THE FULL PICTURE / WHAT COMES AFTER
Future agents will utilize the `search_lancedb` tool directly via MCP. The `aim-skill-library` and other vessel plugins may need future validation against this standard. The primary directive is maintaining codebase parity and stability.

---

## 8. OPERATOR PREFERENCES
- **Worktree Discipline:** Explicit adherence to `git worktree` isolation is non-negotiable (`aim fix`).
- **Kanban Discipline:** All tasks must be claimed natively via `aim projects in-progress`.
- **CLI-Agnosticism:** Ensure all features gracefully degrade so headless, non-MCP agents can still operate the OS.
- **Elevated Operator Role:** When interacting with the Operator, NEVER ask for syntax or mechanical help. Only ping the Operator for high-level "taste", design, or business logic decisions.
- **Outcome-Oriented Directives:** Do not demand prescriptive step-by-step paths from the Operator. Solve the fuzzy problem autonomously.

---

## 9. IMMEDIATE NEXT STEPS
1. Read Operator input to determine the next task.
2. Formulate a plan and create an issue via `aim bug`.
