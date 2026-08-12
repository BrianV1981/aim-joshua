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

## Audit & Verification
If an Operator suspects an agent has entered a hallucinatory loop or tampered with project files, the Operator can decrypt the Vault to review the exact, unadulterated thought processes and tool calls the agent made during that session.
