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
    """Vessel root (parent of aim-agy_os when nested)."""
    current = Path(start or os.getcwd()).resolve()
    for _ in range(12):
        if (current / "aim-agy_os" / "setup.sh").is_file():
            return current
        if (current / "setup.sh").is_file() and (current / ".aim_core").is_dir():
            # flat engine at vessel root
            return current
        if current.parent == current:
            break
        current = current.parent
    # fallback: engine dir's parent if we're under aim-agy_os/.aim_core
    here = Path(__file__).resolve()
    if here.parent.name == ".aim_core":
        engine = here.parent.parent
        if engine.name == "aim-agy_os":
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
        vessel_root / "aim-agy_os" / ".aim_core" / "CONFIG.json",
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
        if reason != "reincarnate":
            _log(f"[VAULT] skip reason={reason!r} (reincarnate-only policy)")
            return False

        root = Path(vessel_root) if vessel_root else find_vessel_root()
        settings = _load_settings(root)
        if settings.get("blackbox_enabled") is False:
            _log("[VAULT] skip blackbox_enabled=false")
            return False
        if settings.get("blackbox_on_reincarnate_only", True) and reason != "reincarnate":
            _log("[VAULT] skip not reincarnate")
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
    """Operator decrypt. Returns plaintext bytes or None."""
    try:
        root = Path(vessel_root) if vessel_root else find_vessel_root()
        box = blackbox_dir(str(root))
        vault_path = box / f"{session_id}.enc"
        if not vault_path.is_file():
            _log(f"[VAULT] ERROR session {session_id} not in black box ({box})")
            return None
        key, _ = get_or_create_key(root)
        plain = Fernet(key).decrypt(vault_path.read_bytes())
        if to_stdout:
            sys.stdout.buffer.write(plain)
            if not plain.endswith(b"\n"):
                sys.stdout.buffer.write(b"\n")
        return plain
    except Exception as e:
        _log(f"[VAULT] ERROR decrypt failed: {e}")
        return None


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
        from vessel_paths import find_session_transcripts, session_id_from_transcript_path

        paths = find_session_transcripts(
            workspace,
            explicit_session_id=session_id,
            prefer="auto",
            prefer_durable=True,
        )
        if not paths:
            _log("[VAULT] WARN no transcript to seal for reincarnate")
            return False
        src = paths[0]
        sid = session_id or session_id_from_transcript_path(src)
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
