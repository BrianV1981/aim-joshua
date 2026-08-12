# A.I.M. Native CLI Tools & Commands

This document maps the core command-line tools available to Conscious Agents operating within the A.I.M. exoskeleton. Agents must utilize these commands rather than attempting raw git/system commands.

## 1. GitOps & Deployment (Atomic Operations)
A.I.M. strictly forbids raw `git commit` and `git push` commands. 

*   **`aim bug "<Description>"`**
    *   *Usage:* Creates a formal GitHub issue. Returns an Issue ID.
    *   *Rule:* Execute this before starting any coding task to get an issue number.
*   **`aim fix <Issue_ID>`**
    *   *Usage:* Checks out an isolated Git worktree (e.g., `workspace/issue-42`).
    *   *Rule:* You must `cd` into this isolated workspace to do your development.
*   **`aim promote`**
    *   *Usage:* Automates the Phase Protocol from inside a worktree. Archives main, merges the worktree branch, pushes to GitHub, and cleans up the worktree.
    *   *Rule:* Use this to deploy your work atomically once TDD validation passes on your isolated branch.

*   **`aim projects <command>`**
    *   *Usage:* Natively interact with the GitHub Projects Kanban board (`aim projects board`, `in-progress`, `done`, `blocked`).
    *   *Rule:* Agents must claim work and mark issues as done on the shared board to prevent parallel agent collisions.

## 2. RAG Memory & Knowledge Retrieval
A.I.M. uses LanceDB for semantic hybrid retrieval (RAG 5.21).

*   **`aim search "<Query>"`**
    *   *Usage:* Executes a Hybrid Search (Tantivy FTS + Vector Embeddings) across the LanceDB memory pool to answer deep architectural questions.
    *   *Rule:* Use this instead of reading massive codebases.
*   **`aim map`**
    *   *Usage:* Prints an index map of available knowledge within the database.

## 3. Cognitive Teleportation & Checkpoints
Long-running sessions experience context collapse (hallucinations) past 30% utilization.

*   **`aim <vessel>-blackbox --session-id <uuid>`** (e.g., `aim agy-blackbox`)
    *   *Usage:* Extracts raw flight records and seals the session into the immutable Blackbox Vault.
    *   *Rule:* Must be executed before terminating a vessel to prevent amnesia.
*   **`aim-handoff` (Skill)**
    *   *Usage:* Teleports your active context, current intent, and task list to a fresh, unburdened agent session via a Tmux baton pass.
    *   *Rule:* Execute this command the moment you feel lost, have completed a major task, or start thrashing. Do not overstay your welcome in a single terminal session.

## 4. The DataJack Swarm (Skill Injection)
DataJack allows the instant injection of massive frameworks and cross-project knowledge via native Apache Arrow Parquet cartridges.

*   **`aim jack-in <file.parquet>`**
    *   *Usage:* Mounts a `.parquet` ROM cartridge into your Subconscious (Zero-Copy) allowing you to use `aim search` on that knowledge instantly.
*   **`aim bake <directory_path> <output_name.parquet>`**
    *   *Usage:* Compiles raw markdown or text documentation into a highly compressed Parquet skill cartridge.

## 5. System Management
*   **`aim update engine`**: Safely pulls the latest A.I.M. OS updates from GitHub without wiping your local LanceDB memory.
*   **`aim audit`**: Audits recent history to generate a Weekly Sitrep.
