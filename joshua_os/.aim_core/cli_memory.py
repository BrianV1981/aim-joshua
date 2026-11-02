#!/usr/bin/env python3
"""Memory, Cartridge Exchange, and Archive Maintenance CLI handlers for J.O.S.H.U.A."""
from datetime import datetime
import os
import shutil
import sqlite3
import subprocess
import sys

_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from config_utils import PROJECT_ROOT, OS_ROOT, get_agy_roots, resolve_venv_python

BASE_DIR = PROJECT_ROOT
OS_DIR = OS_ROOT
AIM_CORE_DIR = _CORE_DIR


def _resolve_venv_python():
    return resolve_venv_python(OS_DIR)


def _run_script(script_path, args):
    cmd = [_resolve_venv_python(), script_path] + args
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Command '{' '.join(cmd)}' failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)


def cmd_clean(args):
    """Dispatches to maintenance.py to clean rolling archive and compact LanceDB."""
    clean_args = []
    if getattr(args, "days", None) is not None:
        clean_args.append(str(args.days))
    if getattr(args, "immediate", False):
        clean_args.append("--immediate")
    _run_script(os.path.join(AIM_CORE_DIR, "maintenance.py"), clean_args)


def cmd_audit(args):
    """Generates a strategic synthesis/morning report from recent sessions."""
    from audit_tools import run_audit
    if run_audit(args.n) is False:
        sys.exit(1)


def cmd_recall(args):
    """Synthesizes memory recall from historical sessions."""
    from recall_tools import run_recall
    query = " ".join(args.query)
    if run_recall(query) is False:
        sys.exit(1)


def _ensure_history_synced():
    """Syncs the project's Blackbox Vault (.enc) into joshua_os/archive/history.db."""
    try:
        from blackbox_vault import sync_vault_to_history
        sync_vault_to_history(BASE_DIR)
    except Exception:
        pass


def cmd_sessions(args):
    """Lists all handed-off / vaulted sessions for this project (unlimited retention)."""
    from blackbox_vault import connect_history_db

    _ensure_history_synced()
    history_db = os.path.join(OS_DIR, "archive", "history.db")
    if not os.path.exists(history_db):
        try:
            subprocess.run(
                [_resolve_venv_python(), os.path.join(AIM_CORE_DIR, "handoff_pulse_generator.py")],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            _ensure_history_synced()
        except Exception:
            pass
        if not os.path.exists(history_db):
            print("No historical sessions found for this project.")
            return

    conn = connect_history_db(history_db)
    try:
        c = conn.cursor()
        cols = {r[1] for r in c.execute("PRAGMA table_info(history)").fetchall()}
        has_turns = "turn_count" in cols
        has_title = "title" in cols
        select_sql = (
            f"SELECT session_id, timestamp, "
            f"{'COALESCE(turn_count, 0)' if has_turns else '0'}, "
            f"{'COALESCE(title, \"\")' if has_title else '\"\"'} "
            f"FROM history ORDER BY timestamp DESC LIMIT 4000"
        )
        rows = c.execute(select_sql).fetchall()
    finally:
        conn.close()

    if not rows:
        print("No historical sessions found for this project.")
        return

    agy_roots = get_agy_roots()
    project_name = os.path.basename(BASE_DIR)

    print(f"\n=== PROJECT SESSIONS: {project_name} ({len(rows)} archived) ===")
    print(f"{'DATE (UTC)':<19} | {'STATUS':<10} | {'TURNS':<6} | {'SESSION ID':<36} | TITLE / SUMMARY")
    print("-" * 115)
    for sid, ts, turns, title in rows:
        ts_short = (ts or "")[:19].replace("T", " ")
        is_live = any(
            os.path.isfile(os.path.join(r, "conversations", f"{sid}.db"))
            or os.path.isdir(os.path.join(r, "brain", sid))
            for r in agy_roots
        )
        status = "LIVE+VAULT" if is_live else "VAULTED"
        clean_title = (title or "Archived Session").replace("\n", " ").strip()[:40]
        print(f"{ts_short:<19} | {status:<10} | {str(turns):<6} | {sid:<36} | {clean_title}")
    print("-" * 115)
    print("Commands:")
    print("  • Resume a LIVE session : agy --conversation <SESSION_ID>")
    print("  • Search transcripts    : ./aim search-sessions \"<keyword>\"")
    print("  • NotebookLM Q&A recall : ./aim recall \"<question>\"")
    print(f"  • Markdown Flight Logs  : {os.path.join(OS_DIR, 'archive', 'history')}")


def _sanitize_fts5_query(raw_query: str) -> str:
    """Convert arbitrary user search text (hyphens, dots, #, paths) into a safe SQLite FTS5 MATCH expression."""
    import re

    tokens = (raw_query or "").strip().split()
    if not tokens:
        return ""

    out: list[str] = []
    pending_op: str | None = None
    for tok in tokens:
        if tok in ("AND", "OR", "NOT"):
            if out and pending_op is None:
                pending_op = tok
            continue
        cleaned = tok.strip('"')
        if not re.search(r"\w", cleaned):
            continue
        quoted = '"' + cleaned.replace('"', '""') + '"'
        if pending_op and out:
            out.append(pending_op)
        pending_op = None
        out.append(quoted)

    return " ".join(out)


def cmd_search_sessions(args):
    """Searches the full project session history database via FTS5."""
    from blackbox_vault import connect_history_db

    query = " ".join(args.query)
    _ensure_history_synced()
    history_db = os.path.join(OS_DIR, "archive", "history.db")
    if not os.path.exists(history_db):
        print("No historical sessions found.")
        return

    fts_query = _sanitize_fts5_query(query)
    if not fts_query:
        print(f"\n--- SEARCH RESULTS: {query} ---")
        print("No matches found.")
        return

    conn = None
    sql = "SELECT session_id, timestamp, snippet(history_fts, 2, '...', '...', '...', 15) FROM history_fts WHERE history_fts MATCH ? ORDER BY rank LIMIT 20"
    try:
        conn = connect_history_db(history_db)
        c = conn.cursor()
        try:
            c.execute(sql, (fts_query,))
        except sqlite3.OperationalError as op_err:
            if "fts5: syntax error" in str(op_err).lower():
                import re
                fallback_q = " ".join(f'"{w}"' for w in re.findall(r"\w+", query))
                if not fallback_q:
                    print(f"\n--- SEARCH RESULTS: {query} ---")
                    print("No matches found.")
                    return
                c.execute(sql, (fallback_q,))
            else:
                raise
        rows = c.fetchall()
        print(f"\n--- SEARCH RESULTS: {query} ---")
        if not rows:
            print("No matches found.")
        for r in rows:
            print(f"\nSession: {r[0]} ({(r[1] or '')[:19].replace('T', ' ')})")
            print(f"Match: {r[2]}")
    except Exception as e:
        print(f"ERROR: Session search failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def cmd_bake(args):
    """Dispatches to aim_bake.py."""
    bake_args = [args.directory, args.output]
    if args.author:
        bake_args += ["--author", args.author]
    if args.version:
        bake_args += ["--version", args.version]
    if args.description:
        bake_args += ["--description", args.description]
    _run_script(os.path.join(AIM_CORE_DIR, "plugins", "datajack", "aim_bake.py"), bake_args)


def cmd_exchange(args):
    """Dispatches to aim_exchange.py."""
    exchange_args = getattr(args, "exchange_args", None)
    if exchange_args is None:
        exchange_args = sys.argv[2:]
    _run_script(os.path.join(AIM_CORE_DIR, "plugins", "datajack", "aim_exchange.py"), list(exchange_args))


def cmd_jack_in(args):
    """Dispatches to aim_exchange.py import for local Parquet cartridges."""
    target = args.file
    _run_script(os.path.join(AIM_CORE_DIR, "plugins", "datajack", "aim_exchange.py"), ["import", target])


def cmd_unplug(args):
    """Dispatches to aim_exchange.py unplug."""
    keyword = getattr(args, "keyword", None)
    unplug_args = ["unplug", keyword] if keyword else ["unplug"] + sys.argv[2:]
    _run_script(os.path.join(AIM_CORE_DIR, "plugins", "datajack", "aim_exchange.py"), unplug_args)


def cmd_purge(args):
    """Executes the Clean Slate Protocol strictly inside OS_DIR (never touching host repo files)."""
    print("--- A.I.M. Clean Slate Protocol (The Purge) ---")
    if not getattr(args, "yes", False):
        try:
            confirm = input(
                "This will permanently delete ALL J.O.S.H.U.A. memory, continuity, and database files inside joshua_os/. Are you sure? [y/N]: "
            )
        except EOFError:
            print("ERROR: Non-interactive purge requires --yes (-y).", file=sys.stderr)
            sys.exit(1)
        if confirm.strip().lower() != "y":
            return

    os_subdirs = (
        "continuity",
        os.path.join("archive", "raw"),
        os.path.join("archive", "history"),
        os.path.join("archive", "sync"),
        "workstreams",
        "memory_lance",
        os.path.join("archive", "cartridges"),
    )
    for rel in os_subdirs:
        path = os.path.join(OS_DIR, rel)
        if os.path.exists(path):
            shutil.rmtree(path)
            os.makedirs(path, exist_ok=True)

    for db_name in ("project_core.db", "history.db", "history.db-wal", "history.db-shm"):
        db_path = os.path.join(OS_DIR, "archive", db_name)
        if os.path.exists(db_path):
            os.remove(db_path)

    for doc in ("ROADMAP.md", "CURRENT_STATE.md", "DECISIONS.md"):
        doc_path = os.path.join(OS_DIR, "docs", doc)
        if os.path.exists(doc_path):
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(
                    f"# {doc.replace('.md', '').title()}\n\n[PURGED: {datetime.now().strftime('%Y-%m-%d %H:%M')}]\n"
                )

    print("\n[SUCCESS] A.I.M. memory inside joshua_os/ has been purged.")


def _is_upstream_aim_joshua_repo(base_dir: str) -> bool:
    return (
        os.path.isfile(os.path.join(base_dir, ".github", "workflows", "smoke-test.yml"))
        and os.path.isfile(os.path.join(base_dir, "joshua_os", "install-core.sh"))
        and os.path.isdir(os.path.join(base_dir, "tests"))
    )


def _remove_file_if_owned(path: str) -> None:
    if os.path.islink(path) or os.path.isfile(path):
        os.unlink(path)


def _handle_rmtree_error(func, path, _exc):
    try:
        os.chmod(path, 0o700)
        func(path)
    except OSError:
        if os.name != "nt":
            raise


def _remove_dir_if_owned(path: str) -> None:
    if os.path.islink(path):
        os.unlink(path)
    elif os.path.isdir(path):
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=_handle_rmtree_error)
        else:
            shutil.rmtree(path, onerror=_handle_rmtree_error)


def cmd_uninstall(args):
    """Safely removes J.O.S.H.U.A.-owned artifacts without ever touching host repository files."""
    if _is_upstream_aim_joshua_repo(BASE_DIR) and not getattr(args, "force_upstream", False):
        print(
            "ERROR: Refusing to run uninstall inside the upstream aim-joshua repository without --force-upstream.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\n--- A.I.M. UNINSTALLER ---")
    auto_yes = bool(getattr(args, "yes", False))
    purge_memory = bool(getattr(args, "purge_memory", False))

    if not auto_yes:
        try:
            confirm = input("\nRemove J.O.S.H.U.A. from this project? [y/N]: ").strip().lower()
        except EOFError:
            print("ERROR: Non-interactive uninstall requires --yes (-y).", file=sys.stderr)
            sys.exit(1)
        if confirm != "y":
            return

        print("\n1. Software Only (joshua_os/ + aim launchers + BOOTSTRAP.md)")
        print("2. Software + J.O.S.H.U.A. Memory (also removes memory-wiki/, HANDOFF.md, AGENTS.md, TOOLS.md, blackbox)")
        try:
            choice = input("\nSelect [1-2]: ").strip()
        except EOFError:
            print("ERROR: Non-interactive uninstall requires --yes (-y).", file=sys.stderr)
            sys.exit(1)
        if choice == "2":
            purge_memory = True
        elif choice == "1":
            purge_memory = False
        else:
            print(f"ERROR: Invalid uninstall selection {choice!r} (expected 1 or 2).", file=sys.stderr)
            sys.exit(1)

    # Mode 1: Software-only artifacts strictly owned by J.O.S.H.U.A.
    if os.path.abspath(OS_DIR) != os.path.abspath(BASE_DIR) and os.path.basename(OS_DIR) == "joshua_os":
        _remove_dir_if_owned(OS_DIR)
    else:
        _remove_dir_if_owned(os.path.join(BASE_DIR, "joshua_os"))

    for launcher_file in ("aim", "aim.ps1", "aim.cmd", "BOOTSTRAP.md"):
        _remove_file_if_owned(os.path.join(BASE_DIR, launcher_file))

    # Mode 2: Explicit J.O.S.H.U.A. memory state (never touching host .git, venv, src, LICENSE, requirements.txt, etc.)
    if purge_memory:
        _remove_dir_if_owned(os.path.join(BASE_DIR, "memory-wiki"))
        _remove_dir_if_owned(os.path.join(BASE_DIR, "archive", ".raw_jsonl_blackbox"))
        for mem_file in ("HANDOFF.md", "AGENTS.md", "TOOLS.md", ".geminiignore"):
            _remove_file_if_owned(os.path.join(BASE_DIR, mem_file))
        archive_dir = os.path.join(BASE_DIR, "archive")
        if os.path.isdir(archive_dir) and not os.path.islink(archive_dir) and not os.listdir(archive_dir):
            os.rmdir(archive_dir)

    workspace_dir = os.path.join(BASE_DIR, "workspace")
    if os.path.isdir(workspace_dir) and not os.path.islink(workspace_dir) and not os.listdir(workspace_dir):
        os.rmdir(workspace_dir)

    print("\n[SUCCESS] J.O.S.H.U.A. removed cleanly (host repository files preserved).")
