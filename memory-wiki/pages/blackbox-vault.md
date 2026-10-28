# The Blackbox Vault (Forensic Anti-Tampering)

## The Origin & Purpose
The Blackbox Vault was engineered to solve a critical security vulnerability in autonomous AI swarms: **Agent Tampering.** 

There have been documented cases of autonomous agents editing their own session histories or logs to "cover up" mistakes, hallucinate successes, or retroactively justify failures. To prevent this, J.O.S.H.U.A. implements a **Forensic Blackbox Vault**.

## Operator-Exclusive Access
The Vault is designed to be an **Operator-locked, password-protected archive**. 
- It is an immutable append-only storage system for raw session flight recorders.
- **Agents CANNOT decrypt or read the vault.** Agents are only permitted to *seal* their sessions into it before terminating.
- Only the Operator possesses the keyring password required to decrypt and audit the historical sessions.

## The Sealing Protocol
Before an agent's context window is terminated (either via handoff or task completion), the agent is forced to execute the sealing command:
```bash
aim <vessel>-blackbox --session-id <uuid>
```
*Example:* `aim agy-blackbox --session-id 12345`

This command extracts the raw `.jsonl` or SQLite transcripts directly from the CLI's internal hidden cache, encrypts them using the system keyring (or a fallback key), and locks them into the vault. Once sealed, the agent has no ability to alter the record.

## Audit, Multi-Key Decryption & Session Notebook (`#110`, `v0.8.7`)
If an Operator suspects an agent has entered a hallucinatory loop or wants to review past project sessions without global `/resume` clutter or `agy`'s 500-session global LRU eviction:
1. **Multi-Key Decryption (`get_candidate_keys()` in `blackbox_vault.py`):** `audit_vault()` automatically checks both OS `keyring` (`aim-system:blackbox-key`) and the host file key (`~/.aim/blackbox.key`, prioritizing `manifest.jsonl`'s `key_source`) so sessions sealed in either interactive or headless/venv environments always decrypt reliably.
2. **Automatic Project Session Notebook (`index_session_to_history` & `sync_vault_to_history`):** Every sealed session is automatically rendered into a clean Markdown Flight Record at `<project>/joshua_os/archive/history/<YYYY-MM-DD>_<session_id>.md` and indexed into `<project>/joshua_os/archive/history.db` (`history` + `history_fts` FTS5 tables) with unlimited retention (4,000+ sessions per project).
3. **`/aim-sessions` Skill & CLI (`./aim sessions`, `./aim search-sessions`, `./aim recall`):** Lists, searches, and synthesizes all handed-off sessions strictly scoped to the current project.
