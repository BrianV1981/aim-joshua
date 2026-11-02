# The Blackbox Vault (Encrypted At-Rest Session Archival)

## Purpose & Threat Model
The Blackbox Vault (`<project_root>/archive/.raw_jsonl_blackbox/`) provides portable, encrypted-at-rest archival and cryptographic SHA-256 manifest verification for raw coding-agent session transcripts across harnesses (`agy`, `grok`, `opencode`, `codex`).

- **Cipher & Key Management:** Raw transcript payloads are encrypted with `cryptography.fernet.Fernet` (**`AES-128-CBC + HMAC-SHA256`** authenticated encryption). Keys are stored in the host OS keyring (`aim-system:blackbox-key`) with fallback to a `0600` host file (`~/.aim/blackbox.key`, or `settings.blackbox_key_path` in `CONFIG.json`).
- **Honest Same-UID Threat Model:** Encryption protects archived `.enc` blobs at rest (for example when backing up `archive/.raw_jsonl_blackbox/` to cloud storage, NAS, or Git) and detects accidental truncation or post-hoc file edits via `manifest.jsonl` SHA-256 digests. Because local CLI agents execute under the Operator's OS user account (UID), the Blackbox Vault is **not** a kernel-enforced privilege boundary against a rogue same-UID local process — and sealing also indexes noise-reduced Markdown summaries into local gitignored `joshua_os/archive/history/` and SQLite WAL `joshua_os/archive/history.db` so `./aim sessions` and `./aim search-sessions` work instantaneously.
- **Shrink-Overwrite Protection:** If `<session_id>.enc` already exists in the vault and a subsequent seal attempt supplies fewer plaintext bytes than previously recorded in `manifest.jsonl`, `vault_session()` refuses to overwrite the larger archive unless `--force` is explicitly passed. When a session grows (e.g., re-sealed later in the same conversation), the previous `.enc` snapshot is preserved under `archive/.raw_jsonl_blackbox/snapshots/` before atomically replacing `<session_id>.enc`.

## Sealing Commands
Before closing out a session during `/aim-handoff`, seal the active session transcript:
```bash
./aim agy-blackbox --session-id <uuid>
./aim grok-blackbox --session-id <id>
./aim opencode-blackbox --session-id <id>
./aim codex-blackbox --session-id <id>
# Or seal any raw JSONL transcript path directly:
./aim vault seal --path /path/to/transcript.jsonl --session-id <id>
```
Temporary staging files created during sealing or history indexing use `0600` `tempfile.mkstemp` handles and are unlinked unconditionally inside `finally:` blocks.

## Operator Audit & Verification
```bash
./aim vault verify <session_id>    # Verify SHA-256 digest against live file or decrypted blob
./aim vault audit <session_id>     # Decrypt session plaintext to stdout
./aim vault doctor                 # Inspect OS keyring and ~/.aim/blackbox.key permissions
```
