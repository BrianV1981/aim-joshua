#!/usr/bin/env python3
"""Vault and Blackbox CLI command handlers for J.O.S.H.U.A."""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)


def cmd_handoff_vnext(args):
    """Handoff vNext pipelines (handoff / blackbox-cron / e2e-staged)."""
    os_root = os.path.dirname(_CORE_DIR)  # joshua_os
    default_vessel = os.path.dirname(os_root)
    vessel = os.path.abspath(getattr(args, "vessel_root", None) or default_vessel)
    proj = os.path.abspath(getattr(args, "project_root", None) or vessel)
    env = os.environ.copy()
    env["PYTHONPATH"] = os_root + os.pathsep + _CORE_DIR + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    env.setdefault("AIM_BLACKBOX_ALLOW_CRON", "1")
    cmd = [
        sys.executable,
        "-m",
        "handoff.cli",
        args.vnext_command,
        "--adapter",
        getattr(args, "adapter", None) or "agy",
        "--vessel-root",
        vessel,
        "--project-root",
        proj,
        "--limit",
        str(getattr(args, "limit", 50) or 50),
    ]
    if getattr(args, "session_id", None):
        cmd += ["--session-id", args.session_id]
    if getattr(args, "fixture_root", None):
        cmd += ["--fixture-root", args.fixture_root]
    if getattr(args, "marker", None):
        cmd += ["--marker", args.marker]
    if getattr(args, "json", False):
        cmd.append("--json")
    raise SystemExit(subprocess.call(cmd, env=env, cwd=vessel))


def cmd_vault(args):
    """Operator forensic black box (audit/verify/seal). Non-agent critical path."""
    from blackbox_vault import (
        audit_vault,
        verify_manifest,
        vault_session,
        seal_for_reincarnate,
    )

    vessel = getattr(args, "vessel", None) or os.getcwd()
    sub = getattr(args, "vault_command", None)
    force = bool(getattr(args, "force", False))
    if sub == "audit":
        plain = audit_vault(args.session_id, vessel_root=vessel)
        sys.exit(0 if plain is not None else 1)
    elif sub == "verify":
        ok = verify_manifest(
            args.session_id, vessel_root=vessel, live_path=getattr(args, "live", None)
        )
        sys.exit(0 if ok else 1)
    elif sub == "seal":
        if getattr(args, "path", None):
            ok = vault_session(
                args.path,
                session_id=getattr(args, "session_id", None),
                vessel_root=vessel,
                reason="reincarnate",
                force=force,
            )
        else:
            ok = seal_for_reincarnate(
                vessel, session_id=getattr(args, "session_id", None), force=force
            )
        sys.exit(0 if ok else 1)
    elif sub == "doctor":
        from aim_vault import vault_doctor
        vault_doctor()
        sys.exit(0)
    else:
        print("Usage: aim vault {audit|verify|seal|doctor} ...", file=sys.stderr)
        sys.exit(2)


def cmd_agy_blackbox(args):
    from blackbox_vault import vault_session
    from config_utils import find_agy_transcript

    sid = args.session_id
    force = bool(getattr(args, "force", False))
    agy_log, probed_paths = find_agy_transcript(sid)
    if not agy_log:
        print(
            f"ERROR: AGY transcript not found for {sid} (searched: {', '.join(probed_paths)})",
            file=sys.stderr,
        )
        sys.exit(1)

    if vault_session(
        agy_log, session_id=sid, vessel_root=os.getcwd(), reason="reincarnate", force=force
    ):
        print(f"Sealed AGY session {sid} into blackbox.")
    else:
        print(f"ERROR: Failed to seal AGY session {sid}.", file=sys.stderr)
        sys.exit(1)


def cmd_grok_blackbox(args):
    from blackbox_vault import seal_for_reincarnate

    sid = args.session_id
    force = bool(getattr(args, "force", False))
    if seal_for_reincarnate(os.getcwd(), session_id=sid, force=force):
        print(f"Sealed Grok session {sid} into blackbox.")
    else:
        print(f"ERROR: Failed to seal Grok session {sid}.", file=sys.stderr)
        sys.exit(1)


def cmd_codex_blackbox(args):
    from blackbox_vault import seal_for_reincarnate

    sid = args.session_id
    force = bool(getattr(args, "force", False))
    if seal_for_reincarnate(os.getcwd(), session_id=sid, force=force):
        print(f"Sealed Codex session {sid} into blackbox.")
    else:
        print(f"ERROR: Failed to seal Codex session {sid}.", file=sys.stderr)
        sys.exit(1)


def _resolve_opencode_db() -> tuple[str | None, list[str]]:
    probed: list[str] = []
    env_db = os.environ.get("AIM_OPENCODE_DB", "").strip()
    candidates = []
    if env_db:
        candidates.append(os.path.expanduser(env_db))
    candidates.append(os.path.join(os.getcwd(), "opencode_data", "opencode.db"))
    candidates.append(os.path.expanduser("~/.local/share/opencode/opencode.db"))
    for c in candidates:
        probed.append(c)
        if os.path.isfile(c):
            return c, probed
    return None, probed


def cmd_opencode_blackbox(args):
    from blackbox_vault import vault_session

    sid = args.session_id
    force = bool(getattr(args, "force", False))
    db_path, probed = _resolve_opencode_db()
    if not db_path:
        print(
            f"ERROR: opencode.db not found (searched: {', '.join(probed)})",
            file=sys.stderr,
        )
        sys.exit(1)

    conn = None
    tmp_path = None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        tables = {
            r[0]
            for r in cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        msg_cols = {
            r[1] for r in cursor.execute("PRAGMA table_info(message)").fetchall()
        }

        if "part" in tables and "data" in msg_cols:
            if "session_id" in msg_cols:
                query = """
                SELECT m.data as m_data, p.data as p_data, m.time_created
                FROM message m
                LEFT JOIN part p ON m.id = p.message_id
                WHERE m.session_id = ?
                ORDER BY m.time_created ASC, p.time_created ASC
                """
            else:
                query = """
                SELECT m.data as m_data, p.data as p_data, m.time_created
                FROM message m
                LEFT JOIN part p ON m.id = p.message_id
                WHERE json_extract(m.data, '$.sessionID') = ?
                ORDER BY m.time_created ASC, p.time_created ASC
                """
            rows = cursor.execute(query, (sid,)).fetchall()
            records = [
                {
                    "session_id": sid,
                    "message": json.loads(r["m_data"]) if r["m_data"] else {},
                    "part": json.loads(r["p_data"]) if r["p_data"] else {},
                    "time_created": r["time_created"],
                }
                for r in rows
            ]
        elif "session_id" in msg_cols:
            select_cols = [c for c in ("role", "content", "data", "time_created") if c in msg_cols]
            query = (
                f"SELECT {', '.join(select_cols)} FROM message "
                f"WHERE session_id = ? ORDER BY time_created ASC"
            )
            rows = cursor.execute(query, (sid,)).fetchall()
            records = [{col: r[col] for col in select_cols} | {"session_id": sid} for r in rows]
        else:
            print(
                f"ERROR: Unsupported OpenCode message schema in {db_path}",
                file=sys.stderr,
            )
            sys.exit(1)

        if not records:
            print(
                f"ERROR: No messages found for OpenCode session '{sid}' in {db_path}",
                file=sys.stderr,
            )
            sys.exit(1)

        fd, tmp_path = tempfile.mkstemp(prefix="aim_oc_", suffix="_transcript.jsonl")
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_f:
            for obj in records:
                tmp_f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        try:
            os.chmod(tmp_path, 0o600)
        except OSError:
            pass

        if vault_session(
            tmp_path, session_id=sid, vessel_root=os.getcwd(), reason="reincarnate", force=force
        ):
            print(f"Sealed OpenCode session {sid} into blackbox.")
        else:
            print(f"ERROR: Failed to seal OpenCode session {sid}.", file=sys.stderr)
            sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR extracting opencode session: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
