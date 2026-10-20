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
    """Handoff vNext three pipelines (docs/HANDOFF_VNEXT_E2E.md / issue #32)."""
    os_root = os.path.dirname(_CORE_DIR)  # joshua_os
    vessel = os.path.dirname(os_root)
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
        vessel,
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
    if sub == "audit":
        audit_vault(args.session_id, vessel_root=vessel)
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
            )
        else:
            ok = seal_for_reincarnate(
                vessel, session_id=getattr(args, "session_id", None)
            )
        sys.exit(0 if ok else 1)
    elif sub == "doctor":
        from aim_vault import vault_doctor
        vault_doctor()
        sys.exit(0)
    else:
        print("Usage: aim vault {audit|verify|seal|doctor} ...")
        sys.exit(2)


def cmd_agy_blackbox(args):
    from pathlib import Path
    from blackbox_vault import vault_session

    sid = args.session_id
    agy_log = (
        Path.home()
        / ".gemini"
        / "antigravity-cli"
        / "brain"
        / sid
        / ".system_generated"
        / "logs"
        / "transcript.jsonl"
    )
    if agy_log.is_file():
        if vault_session(str(agy_log), session_id=sid, vessel_root=os.getcwd(), reason="reincarnate"):
            print(f"Sealed AGY session {sid} into blackbox.")
        else:
            print(f"WARN: Failed to seal AGY session {sid}.")
    else:
        print(f"ERROR: AGY transcript not found for {sid} at {agy_log}")


def cmd_grok_blackbox(args):
    from blackbox_vault import seal_for_reincarnate

    sid = args.session_id
    if seal_for_reincarnate(os.getcwd(), session_id=sid):
        print(f"Sealed Grok session {sid} into blackbox.")
    else:
        print(f"WARN: Failed to seal Grok session {sid}.")


def cmd_codex_blackbox(args):
    from blackbox_vault import seal_for_reincarnate

    sid = args.session_id
    if seal_for_reincarnate(os.getcwd(), session_id=sid):
        print(f"Sealed Codex session {sid} into blackbox.")
    else:
        print(f"WARN: Failed to seal Codex session {sid}.")


def cmd_opencode_blackbox(args):
    from blackbox_vault import vault_session

    sid = args.session_id
    db_path = os.path.join(os.getcwd(), "opencode_data", "opencode.db")
    if not os.path.exists(db_path):
        print(f"ERROR: opencode.db not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = """
        SELECT m.data as m_data, p.data as p_data, m.time_created
        FROM message m
        JOIN part p ON m.id = p.message_id
        ORDER BY m.time_created ASC, p.time_created ASC
        """
        rows = cursor.execute(query).fetchall()

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl", encoding="utf-8") as tmp:
            for r in rows:
                obj = {
                    "message": json.loads(r["m_data"]),
                    "part": json.loads(r["p_data"]),
                    "time_created": r["time_created"],
                }
                tmp.write(json.dumps(obj) + "\n")
            tmp_path = tmp.name
        conn.close()

        if vault_session(tmp_path, session_id=sid, vessel_root=os.getcwd(), reason="reincarnate"):
            print(f"Sealed OpenCode session {sid} into blackbox.")
        else:
            print(f"WARN: Failed to seal OpenCode session {sid}.")
    except Exception as e:
        print(f"ERROR extracting opencode session: {e}")
    finally:
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
