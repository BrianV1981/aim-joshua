#!/usr/bin/env python3
"""
Immutable Black Box — vessel-scoped encrypted seal of raw session transcripts.

Purpose (Operator forensic): answer "did something alter the story after the fact?"
Non-purpose: wiki, Engram, agent self-edit tooling.

Contract (issue #12):
  - One box per vessel install: <vessel_root>/archive/.raw_jsonl_blackbox/
  - Seal on reincarnate only (callers enforce); never bulk-scrape all sessions
  - Never fatal: return False + WARN; never block reincarnate/wiki
  - Key: OS keyring preferred, then ~/.aim/blackbox.key (0600)
  - Manifest line per seal with sha256 of plaintext
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from cryptography.fernet import Fernet
except ImportError:  # pragma: no cover
    Fernet = None  # type: ignore

try:
    import keyring
except ImportError:  # pragma: no cover
    keyring = None  # type: ignore

SERVICE = "aim-system"
ACCOUNT = "blackbox-key"
DEFAULT_HOST_KEY = Path.home() / ".aim" / "blackbox.key"
MANIFEST_NAME = "manifest.jsonl"


def _log(msg: str) -> None:
    print(msg, flush=True)


def find_vessel_root(start: Optional[str] = None) -> Path:
    """Vessel root (parent of joshua_os when nested)."""
    current = Path(start or os.getcwd()).resolve()
    for _ in range(12):
        if (current / "joshua_os" / "setup.sh").is_file():
            return current
        if (current / "setup.sh").is_file() and (current / ".aim_core").is_dir():
            # flat engine at vessel root
            return current
        if current.parent == current:
            break
        current = current.parent
    # fallback: engine dir's parent if we're under joshua_os/.aim_core
    here = Path(__file__).resolve()
    if here.parent.name == ".aim_core":
        engine = here.parent.parent
        if engine.name == "joshua_os":
            return engine.parent
        return engine
    return Path(os.getcwd()).resolve()


def blackbox_dir(vessel_root: Optional[str] = None) -> Path:
    root = Path(vessel_root) if vessel_root else find_vessel_root()
    return root / "archive" / ".raw_jsonl_blackbox"


def _load_settings(vessel_root: Path) -> Dict[str, Any]:
    settings: Dict[str, Any] = {
        "blackbox_enabled": True,
        "blackbox_on_reincarnate_only": True,
    }
    for cfg_path in (
        vessel_root / ".aim_core" / "CONFIG.json",
        vessel_root / "joshua_os" / ".aim_core" / "CONFIG.json",
        vessel_root / "core" / "CONFIG.json",
    ):
        if not cfg_path.is_file():
            continue
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8") or "{}")
            s = data.get("settings") or {}
            if isinstance(s, dict):
                settings.update({k: s[k] for k in s if k.startswith("blackbox")})
                if "blackbox_key_path" in s:
                    settings["blackbox_key_path"] = s["blackbox_key_path"]
        except Exception:
            pass
    return settings


def get_or_create_key(
    vessel_root: Optional[Path] = None,
    key_path_override: Optional[str] = None,
) -> Tuple[bytes, str]:
    """
    Return (fernet_key_bytes, source_label).
    Prefer OS keyring; fall back to host file ~/.aim/blackbox.key (0600).
    """
    if Fernet is None:
        raise RuntimeError("cryptography.fernet not installed")

    # 1) OS keyring
    if keyring is not None:
        try:
            key = keyring.get_password(SERVICE, ACCOUNT)
            if key:
                return key.encode("utf-8"), "keyring"
            # try create
            key = Fernet.generate_key().decode("utf-8")
            keyring.set_password(SERVICE, ACCOUNT, key)
            return key.encode("utf-8"), "keyring-created"
        except Exception as e:
            _log(f"[VAULT] WARN keyring unavailable ({e}); trying file key")

    # 2) File key
    if key_path_override:
        key_file = Path(key_path_override).expanduser()
    else:
        settings = _load_settings(vessel_root or find_vessel_root())
        override = settings.get("blackbox_key_path")
        key_file = Path(override).expanduser() if override else DEFAULT_HOST_KEY

    key_file.parent.mkdir(parents=True, exist_ok=True)
    if key_file.is_file():
        raw = key_file.read_bytes().strip()
        if raw:
            return raw, f"file:{key_file}"
    key = Fernet.generate_key()
    # write 0600
    fd = os.open(str(key_file), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, key)
    finally:
        os.close(fd)
    try:
        os.chmod(key_file, 0o600)
    except OSError:
        pass
    _log(f"[VAULT] created file key at {key_file} (mode 0600)")
    return key, f"file-created:{key_file}"


def get_candidate_keys(
    vessel_root: Optional[Path] = None,
    key_path_override: Optional[str] = None,
    preferred_source: Optional[str] = None,
) -> list[Tuple[bytes, str]]:
    """
    Return all available candidate (fernet_key_bytes, source_label) pairs for decryption.
    Checks both OS keyring and host file key (~/.aim/blackbox.key) so blobs sealed under
    either environment (interactive keyring vs. headless/venv file key) always decrypt.
    """
    if Fernet is None:
        raise RuntimeError("cryptography.fernet not installed")

    candidates: list[Tuple[bytes, str]] = []

    # Collect OS keyring key if available
    kr_pair: Optional[Tuple[bytes, str]] = None
    if keyring is not None:
        try:
            k = keyring.get_password(SERVICE, ACCOUNT)
            if k and k.strip():
                kr_pair = (k.strip().encode("utf-8"), "keyring")
        except Exception:
            pass

    # Collect file key if available
    file_pair: Optional[Tuple[bytes, str]] = None
    if key_path_override:
        key_file = Path(key_path_override).expanduser()
    else:
        settings = _load_settings(vessel_root or find_vessel_root())
        override = settings.get("blackbox_key_path")
        key_file = Path(override).expanduser() if override else DEFAULT_HOST_KEY

    if key_file.is_file():
        try:
            raw = key_file.read_bytes().strip()
            if raw:
                file_pair = (raw, f"file:{key_file}")
        except Exception:
            pass

    if preferred_source and preferred_source.startswith("file"):
        if file_pair:
            candidates.append(file_pair)
        if kr_pair:
            candidates.append(kr_pair)
    else:
        if kr_pair:
            candidates.append(kr_pair)
        if file_pair:
            candidates.append(file_pair)

    if not candidates:
        candidates.append(get_or_create_key(vessel_root, key_path_override=key_path_override))

    # Deduplicate by key bytes while preserving order
    seen: set[bytes] = set()
    unique: list[Tuple[bytes, str]] = []
    for kbytes, src in candidates:
        if kbytes not in seen:
            seen.add(kbytes)
            unique.append((kbytes, src))
    return unique


def _resolve_os_dir(vessel_root: Path) -> Path:
    if (vessel_root / "joshua_os").is_dir():
        return vessel_root / "joshua_os"
    if (vessel_root / "aim-agy_os").is_dir():
        return vessel_root / "aim-agy_os"
    return vessel_root


def _lookup_conversation_title(session_id: str) -> str:
    summary_db = Path.home() / ".gemini" / "antigravity-cli" / "conversation_summaries.db"
    if not summary_db.is_file():
        return ""
    try:
        import sqlite3
        conn = sqlite3.connect(f"file:{summary_db}?mode=ro", uri=True)
        row = conn.execute(
            "SELECT title, preview FROM conversation_summaries WHERE conversation_id = ?",
            (session_id,),
        ).fetchone()
        conn.close()
        if row:
            title = (row[0] or "").strip()
            if title:
                return title
            preview = (row[1] or "").strip().splitlines()
            if preview:
                return preview[0][:80]
    except Exception:
        pass
    return ""


def index_session_to_history(
    raw_bytes: bytes,
    session_id: str,
    vessel_root: Path,
    sealed_at: Optional[str] = None,
) -> bool:
    """
    Render raw session transcript bytes into a clean Markdown Flight Record in
    <os_dir>/archive/history/ and index into <os_dir>/archive/history.db (history + history_fts).
    """
    if not raw_bytes or session_id.startswith("hermetic-"):
        return False
    try:
        import sqlite3
        import tempfile

        here = Path(__file__).resolve().parent
        if str(here) not in sys.path:
            sys.path.insert(0, str(here))
        from extract_signal import (
            conversational_turn_count,
            extract_signal,
            skeleton_to_markdown,
        )

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix="_transcript.jsonl", delete=False
        ) as tmp:
            tmp.write(raw_bytes)
            tmp_path = tmp.name

        try:
            skeleton = extract_signal(tmp_path)
            turns = conversational_turn_count(skeleton)
            md_content = skeleton_to_markdown(skeleton, session_id)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        title = _lookup_conversation_title(session_id)
        if not title and isinstance(skeleton, list):
            for turn in skeleton:
                if isinstance(turn, dict) and (turn.get("role") or "").lower() == "user":
                    first_line = (turn.get("text") or "").strip().splitlines()
                    if first_line:
                        title = first_line[0].lstrip("#> ").strip()[:80]
                        break

        ts_iso = sealed_at or datetime.now(timezone.utc).isoformat()
        date_prefix = ts_iso[:10] if len(ts_iso) >= 10 else datetime.now(timezone.utc).strftime("%Y-%m-%d")

        os_dir = _resolve_os_dir(vessel_root)
        hist_dir = os_dir / "archive" / "history"
        hist_dir.mkdir(parents=True, exist_ok=True)

        # Write or update markdown flight record
        existing_md = list(hist_dir.glob(f"*_{session_id}.md"))
        md_path = existing_md[0] if existing_md else (hist_dir / f"{date_prefix}_{session_id}.md")
        md_path.write_text(md_content, encoding="utf-8")

        db_path = os_dir / "archive" / "history.db"
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    session_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    content TEXT NOT NULL,
                    turn_count INTEGER DEFAULT 0,
                    title TEXT DEFAULT ''
                )
                """
            )
            # Ensure turn_count and title columns exist on legacy DBs
            cols = {r[1] for r in conn.execute("PRAGMA table_info(history)").fetchall()}
            if "turn_count" not in cols:
                conn.execute("ALTER TABLE history ADD COLUMN turn_count INTEGER DEFAULT 0")
            if "title" not in cols:
                conn.execute("ALTER TABLE history ADD COLUMN title TEXT DEFAULT ''")

            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS history_fts USING fts5(
                    session_id,
                    timestamp,
                    content
                )
                """
            )
            conn.execute(
                """
                INSERT INTO history (session_id, timestamp, content, turn_count, title)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    timestamp = excluded.timestamp,
                    content = excluded.content,
                    turn_count = excluded.turn_count,
                    title = CASE WHEN excluded.title != '' THEN excluded.title ELSE history.title END
                """,
                (session_id, ts_iso, md_content, turns, title),
            )
            conn.execute("DELETE FROM history_fts WHERE session_id = ?", (session_id,))
            conn.execute(
                "INSERT INTO history_fts (session_id, timestamp, content) VALUES (?, ?, ?)",
                (session_id, ts_iso, md_content),
            )
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception as e:
        _log(f"[VAULT] WARN history index skipped for {session_id}: {e}")
        return False


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _append_manifest(box: Path, entry: Dict[str, Any]) -> None:
    box.mkdir(parents=True, exist_ok=True)
    man = box / MANIFEST_NAME
    with man.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def vault_session(
    source_path: str,
    *,
    session_id: Optional[str] = None,
    vessel_root: Optional[str] = None,
    reason: str = "reincarnate",
) -> bool:
    """
    Encrypt raw session bytes into the vessel black box.
    Always non-fatal: returns False on skip/failure.
    """
    try:
        # Allowed seal reasons: reincarnate (legacy live path) + cron (nightly vNext)
        allowed = {"reincarnate", "cron", "handoff_vnext"}
        if reason not in allowed:
            _log(f"[VAULT] skip reason={reason!r} (allowed={sorted(allowed)})")
            return False

        root = Path(vessel_root) if vessel_root else find_vessel_root()
        settings = _load_settings(root)
        if settings.get("blackbox_enabled") is False:
            _log("[VAULT] skip blackbox_enabled=false")
            return False
        # Legacy flag: when true, only reincarnate — unless AIM_BLACKBOX_ALLOW_CRON=1
        allow_cron = os.environ.get("AIM_BLACKBOX_ALLOW_CRON", "1") not in (
            "0",
            "false",
            "no",
        )
        if settings.get("blackbox_on_reincarnate_only", True):
            if reason == "reincarnate":
                pass
            elif reason in ("cron", "handoff_vnext") and allow_cron:
                pass
            else:
                _log("[VAULT] skip not reincarnate (and cron not allowed)")
                return False

        if not source_path or not os.path.isfile(source_path):
            _log(f"[VAULT] WARN skip: source missing {source_path!r}")
            return False

        sid = session_id
        if not sid:
            base = os.path.basename(source_path)
            if base in ("chat_history.jsonl", "updates.jsonl", "transcript.jsonl"):
                sid = os.path.basename(os.path.dirname(source_path))
            else:
                sid = base.replace(".jsonl", "").replace(".json", "")
        # never store under useless basenames
        if sid in ("chat_history", "updates", "transcript", "history"):
            sid = os.path.basename(os.path.dirname(source_path))

        box = blackbox_dir(str(root))
        box.mkdir(parents=True, exist_ok=True)
        # hide from casual listing if possible
        try:
            os.chmod(box, 0o700)
        except OSError:
            pass

        vault_path = box / f"{sid}.enc"
        raw = Path(source_path).read_bytes()
        digest = _sha256(raw)

        # idempotent if same hash already sealed
        man = box / MANIFEST_NAME
        if man.is_file():
            for line in man.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    prev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if prev.get("session_id") == sid and prev.get("sha256_plaintext") == digest:
                    index_session_to_history(raw, sid, root, sealed_at=prev.get("sealed_at"))
                    _log(f"[VAULT] already sealed session={sid} sha256={digest[:12]}…")
                    return True

        key, key_src = get_or_create_key(
            root, key_path_override=settings.get("blackbox_key_path")
        )
        fernet = Fernet(key)
        encrypted = fernet.encrypt(raw)
        vault_path.write_bytes(encrypted)
        try:
            os.chmod(vault_path, 0o600)
        except OSError:
            pass

        entry = {
            "session_id": sid,
            "source_path": str(Path(source_path).resolve()),
            "blob_path": str(vault_path),
            "sealed_at": datetime.now(timezone.utc).isoformat(),
            "sha256_plaintext": digest,
            "bytes": len(raw),
            "reason": reason,
            "vessel_root": str(root),
            "key_source": key_src.split(":")[0],
        }
        _append_manifest(box, entry)
        index_session_to_history(raw, sid, root, sealed_at=entry["sealed_at"])
        _log(
            f"[VAULT] sealed session={sid} blob={vault_path.name} "
            f"sha256={digest[:16]}… key={entry['key_source']}"
        )
        return True
    except Exception as e:
        _log(f"[VAULT] WARN skipped: {e}")
        return False


def audit_vault(
    session_id: str,
    *,
    vessel_root: Optional[str] = None,
    to_stdout: bool = True,
) -> Optional[bytes]:
    """Operator decrypt. Tries all candidate keys (keyring + file key). Returns plaintext bytes or None."""
    try:
        root = Path(vessel_root) if vessel_root else find_vessel_root()
        box = blackbox_dir(str(root))
        vault_path = box / f"{session_id}.enc"
        if not vault_path.is_file():
            _log(f"[VAULT] ERROR session {session_id} not in black box ({box})")
            return None

        preferred_source: Optional[str] = None
        man = box / MANIFEST_NAME
        if man.is_file():
            for line in man.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    o = json.loads(line)
                    if o.get("session_id") == session_id:
                        preferred_source = o.get("key_source")
                except Exception:
                    continue

        settings = _load_settings(root)
        cipher_bytes = vault_path.read_bytes()
        last_err: Optional[Exception] = None
        for key, _ in get_candidate_keys(
            root,
            key_path_override=settings.get("blackbox_key_path"),
            preferred_source=preferred_source,
        ):
            try:
                plain = Fernet(key).decrypt(cipher_bytes)
                if to_stdout:
                    sys.stdout.buffer.write(plain)
                    if not plain.endswith(b"\n"):
                        sys.stdout.buffer.write(b"\n")
                return plain
            except Exception as err:
                last_err = err
        _log(f"[VAULT] ERROR decrypt failed: {last_err}")
        return None
    except Exception as e:
        _log(f"[VAULT] ERROR decrypt failed: {e}")
        return None


def sync_vault_to_history(vessel_root: Optional[str] = None) -> int:
    """
    Ensure every non-hermetic .enc blob in <vessel_root>/archive/.raw_jsonl_blackbox/
    is decrypted and indexed into <os_dir>/archive/history/ and history.db.
    Returns count of newly indexed sessions.
    """
    root = Path(vessel_root) if vessel_root else find_vessel_root()
    box = blackbox_dir(str(root))
    if not box.is_dir():
        return 0

    sealed_dates: Dict[str, str] = {}
    man = box / MANIFEST_NAME
    if man.is_file():
        for line in man.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                o = json.loads(line)
                sid = o.get("session_id")
                if sid and o.get("sealed_at"):
                    sealed_dates[sid] = o["sealed_at"]
            except Exception:
                continue

    os_dir = _resolve_os_dir(root)
    db_path = os_dir / "archive" / "history.db"
    existing_ids: set[str] = set()
    if db_path.is_file():
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            existing_ids = {
                r[0] for r in conn.execute("SELECT session_id FROM history").fetchall()
            }
            conn.close()
        except Exception:
            existing_ids = set()

    indexed = 0
    for enc_file in sorted(box.glob("*.enc")):
        sid = enc_file.stem
        if sid.startswith("hermetic-") or sid in existing_ids:
            continue
        plain = audit_vault(sid, vessel_root=str(root), to_stdout=False)
        if plain:
            if index_session_to_history(
                plain,
                sid,
                root,
                sealed_at=sealed_dates.get(sid)
                or datetime.fromtimestamp(enc_file.stat().st_mtime, tz=timezone.utc).isoformat(),
            ):
                indexed += 1
    return indexed


def verify_manifest(
    session_id: str,
    *,
    vessel_root: Optional[str] = None,
    live_path: Optional[str] = None,
) -> bool:
    """Compare sealed sha256 to live file (or re-decrypt blob)."""
    root = Path(vessel_root) if vessel_root else find_vessel_root()
    box = blackbox_dir(str(root))
    man = box / MANIFEST_NAME
    if not man.is_file():
        _log("[VAULT] no manifest")
        return False
    entry = None
    for line in man.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if o.get("session_id") == session_id:
            entry = o  # last wins
    if not entry:
        _log(f"[VAULT] no manifest entry for {session_id}")
        return False
    expected = entry.get("sha256_plaintext")
    path = live_path or entry.get("source_path")
    if path and os.path.isfile(path):
        actual = _sha256(Path(path).read_bytes())
        ok = actual == expected
        _log(
            f"[VAULT] verify session={session_id} live_match={ok} "
            f"expected={expected[:16]}… actual={actual[:16]}…"
        )
        return ok
    # fall back: decrypt blob and hash
    plain = audit_vault(session_id, vessel_root=str(root), to_stdout=False)
    if plain is None:
        return False
    actual = _sha256(plain)
    ok = actual == expected
    _log(f"[VAULT] verify blob session={session_id} match={ok}")
    return ok


def _resolve_reincarnate_transcripts(
    workspace: str, session_id: Optional[str]
) -> Tuple[list, Optional[str]]:
    """Return (paths, session_id_helper_name). Vessel-native fallbacks if no vessel_paths."""
    paths: list = []
    id_from_path = None
    try:
        from vessel_paths import (  # type: ignore
            find_session_transcripts,
            session_id_from_transcript_path,
        )

        paths = find_session_transcripts(
            workspace,
            explicit_session_id=session_id,
            prefer="auto",
            prefer_durable=True,
        )
        id_from_path = session_id_from_transcript_path
    except Exception:
        paths = []

    if paths:
        return paths, id_from_path

    # AGY brain (soul / aim-joshua — no vessel_paths module)
    if session_id:
        agy = (
            Path.home()
            / ".gemini"
            / "antigravity-cli"
            / "brain"
            / session_id
            / ".system_generated"
            / "logs"
            / "transcript.jsonl"
        )
        if agy.is_file():
            return [str(agy)], id_from_path

    # OpenCode archive/raw session-*.json
    raw_dirs = [
        Path(workspace) / "archive" / "raw",
        Path(workspace) / "joshua_os" / "archive" / "raw",
    ]
    for raw in raw_dirs:
        if not raw.is_dir():
            continue
        if session_id:
            hits = sorted(raw.glob(f"*{session_id}*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if hits:
                return [str(hits[0])], id_from_path
        hits = sorted(raw.glob("session-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if hits:
            return [str(hits[0])], id_from_path

    # Codex rollouts by session id substring
    if session_id:
        codex_root = Path.home() / ".codex" / "sessions"
        if codex_root.is_dir():
            hits = sorted(
                codex_root.rglob(f"*{session_id}*.jsonl"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if hits:
                return [str(hits[0])], id_from_path

    return [], id_from_path


def seal_for_reincarnate(
    workspace: str,
    session_id: Optional[str] = None,
) -> bool:
    """
    Resolve raw transcript for reincarnating session and seal once.
    Used by reincarnation background pipeline only.
    """
    workspace = os.path.abspath(workspace or ".")
    try:
        paths, id_from_path = _resolve_reincarnate_transcripts(workspace, session_id)
        if not paths:
            _log("[VAULT] WARN no transcript to seal for reincarnate")
            return False
        src = paths[0]
        sid = session_id
        if not sid and id_from_path:
            try:
                sid = id_from_path(src)
            except Exception:
                sid = None
        if not sid:
            base = os.path.basename(src)
            if base in ("chat_history.jsonl", "updates.jsonl", "transcript.jsonl"):
                sid = os.path.basename(os.path.dirname(src))
            elif base.startswith("rollout-") and base.endswith(".jsonl"):
                # rollout-<ts>-<uuid>.jsonl — uuid often last 36-ish chars
                sid = base[len("rollout-") : -len(".jsonl")]
                if "-" in sid:
                    # prefer trailing uuid-looking segment
                    parts = sid.split("-")
                    if len(parts) >= 5:
                        sid = "-".join(parts[-5:])
            else:
                sid = base.replace(".jsonl", "").replace(".json", "")
        return vault_session(
            src,
            session_id=sid,
            vessel_root=workspace,
            reason="reincarnate",
        )
    except Exception as e:
        _log(f"[VAULT] WARN seal_for_reincarnate: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  blackbox_vault.py seal <path> [--session-id ID] [--vessel ROOT]\n"
            "  blackbox_vault.py audit <session_id> [--vessel ROOT]\n"
            "  blackbox_vault.py verify <session_id> [--vessel ROOT] [--live PATH]\n"
        )
        sys.exit(1)
    cmd = sys.argv[1]
    # minimal argv parse
    def _opt(name, default=None):
        if name in sys.argv:
            i = sys.argv.index(name)
            if i + 1 < len(sys.argv):
                return sys.argv[i + 1]
        return default

    vessel = _opt("--vessel")
    if cmd == "seal" and len(sys.argv) > 2:
        ok = vault_session(
            sys.argv[2],
            session_id=_opt("--session-id"),
            vessel_root=vessel,
            reason="reincarnate",
        )
        sys.exit(0 if ok else 1)
    if cmd == "audit" and len(sys.argv) > 2:
        audit_vault(sys.argv[2], vessel_root=vessel)
        sys.exit(0)
    if cmd == "verify" and len(sys.argv) > 2:
        ok = verify_manifest(
            sys.argv[2], vessel_root=vessel, live_path=_opt("--live")
        )
        sys.exit(0 if ok else 1)
    print("Unknown command")
    sys.exit(2)
