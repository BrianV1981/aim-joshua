#!/usr/bin/env python3
"""Memory, Cartridge Exchange, and Archive Maintenance CLI handlers for J.O.S.H.U.A."""
from datetime import datetime
import os
import shutil
import sqlite3
import subprocess
import sys
import traceback

_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from config_utils import PROJECT_ROOT, OS_ROOT, resolve_venv_python

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
    _run_script(os.path.join(AIM_CORE_DIR, "maintenance.py"), [])


def cmd_sync(args):
    """Bakes native LanceDB cartridges and runs Sovereign Sync."""
    print("--- A.I.M. SYNC ---")
    try:
        from sovereign_sync import export_to_parquet, import_from_parquet

        sync_dir = os.path.join(OS_DIR, "archive/sync")
        os.makedirs(sync_dir, exist_ok=True)

        export_to_parquet(OS_DIR, sync_dir)

        print("[2/3] Executing network sync...")
        _run_script(os.path.join(AIM_CORE_DIR, "back-populator.py"), [])

        imported = import_from_parquet(OS_DIR, sync_dir)
        print(f"      Imported {imported} new/updated cartridges.")
        print("[SUCCESS] Workspace synchronized.")
    except Exception as e:
        traceback.print_exc()
        print(f"[ERROR] Sync failed: {e}")


def cmd_audit(args):
    """Generates a strategic synthesis/morning report from recent sessions."""
    from audit_tools import run_audit
    run_audit(args.n)


def cmd_recall(args):
    """Synthesizes memory recall from historical sessions."""
    from recall_tools import run_recall
    query = " ".join(args.query)
    run_recall(query)


def cmd_mail(args):
    """Syncs the Unread Mail tracker from the Swarm Post Office."""
    _run_script(os.path.join(AIM_CORE_DIR, "sync_mail.py"), [])


def _ensure_history_synced():
    """Syncs the project's Blackbox Vault (.enc) into joshua_os/archive/history.db."""
    try:
        from blackbox_vault import sync_vault_to_history
        sync_vault_to_history(BASE_DIR)
    except Exception:
        pass


def cmd_sessions(args):
    """Lists all handed-off / vaulted sessions for this project (unlimited retention)."""
    _ensure_history_synced()
    history_db = os.path.join(OS_DIR, "archive/history.db")
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

    conn = sqlite3.connect(history_db)
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
    conn.close()

    if not rows:
        print("No historical sessions found for this project.")
        return

    agy_conv_dir = os.path.expanduser("~/.gemini/antigravity-cli/conversations")
    agy_brain_dir = os.path.expanduser("~/.gemini/antigravity-cli/brain")
    project_name = os.path.basename(BASE_DIR)

    print(f"\n=== PROJECT SESSIONS: {project_name} ({len(rows)} archived) ===")
    print(f"{'DATE (UTC)':<19} | {'STATUS':<10} | {'TURNS':<6} | {'SESSION ID':<36} | TITLE / SUMMARY")
    print("-" * 115)
    for sid, ts, turns, title in rows:
        ts_short = (ts or "")[:19].replace("T", " ")
        is_live = (
            os.path.isfile(os.path.join(agy_conv_dir, f"{sid}.db"))
            or os.path.isdir(os.path.join(agy_brain_dir, sid))
        )
        status = "LIVE+VAULT" if is_live else "VAULTED"
        clean_title = (title or "Archived Session").replace("\n", " ").strip()[:40]
        print(f"{ts_short:<19} | {status:<10} | {str(turns):<6} | {sid:<36} | {clean_title}")
    print("-" * 115)
    print("Commands:")
    print("  • Resume a LIVE session : agy --conversation <SESSION_ID>")
    print("  • Search transcripts    : ./aim search-sessions \"<keyword>\"")
    print("  • NotebookLM Q&A recall : ./aim recall \"<question>\"")
    print(f"  • Markdown Flight Logs  : {os.path.join(OS_DIR, 'archive/history/')}")


def cmd_search_sessions(args):
    """Searches the full project session history database via FTS5."""
    query = " ".join(args.query)
    _ensure_history_synced()
    history_db = os.path.join(OS_DIR, "archive/history.db")
    if not os.path.exists(history_db):
        print("No historical sessions found.")
        return

    conn = sqlite3.connect(history_db)
    c = conn.cursor()
    sql = "SELECT session_id, timestamp, snippet(history_fts, 2, '...', '...', '...', 15) FROM history_fts WHERE history_fts MATCH ? ORDER BY rank LIMIT 20"
    try:
        c.execute(sql, (query,))
        rows = c.fetchall()
        print(f"\n--- SEARCH RESULTS: {query} ---")
        if not rows:
            print("No matches found.")
        for r in rows:
            print(f"\nSession: {r[0]} ({r[1][:19].replace('T', ' ')})")
            print(f"Match: {r[2]}")
    except Exception as e:
        traceback.print_exc()
        print(f"Search failed: {e}")
    conn.close()


def cmd_scrape(args):
    """Scrapes forum threads or GitHub issues into Synapse Markdown docs."""
    scrape_args = []
    if args.source:
        scrape_args += ["--source", args.source]
    if args.repo:
        scrape_args += ["--repo", args.repo]
    if args.query:
        scrape_args += ["--query", args.query]
    if args.limit:
        scrape_args += ["--limit", str(args.limit)]
    if args.outdir:
        scrape_args += ["--outdir", args.outdir]
    _run_script(os.path.join(AIM_CORE_DIR, "aim_scraper.py"), scrape_args)


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


def cmd_export(args):
    """Exports and seeds an engram via BitTorrent Swarm."""
    target = args.file
    if not os.path.exists(target):
        print(f"[ERROR] File not found: {target}")
        sys.exit(1)

    print("\n[EXPORT] Preparing DataJack Swarm Seed...")
    torrent_handler = os.path.join(AIM_CORE_DIR, "aim_torrent.py")
    if not os.path.exists(torrent_handler):
        print("[ERROR] Torrent handler not found.")
        sys.exit(1)

    try:
        subprocess.run([_resolve_venv_python(), torrent_handler, "seed", target], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Seeding failed: {e}")
        sys.exit(e.returncode)


def cmd_exchange(args):
    """Dispatches to aim_exchange.py."""
    _run_script(os.path.join(AIM_CORE_DIR, "plugins", "datajack", "aim_exchange.py"), sys.argv[2:])


def cmd_jack_in(args):
    """Dispatches to aim_exchange.py import, with support for BitTorrent Magnet Links."""
    target = args.file

    if target.startswith("magnet:?"):
        print("\n[JACK-IN] Initiating DataJack Swarm Handshake...")
        print("  Target: Magnet Link Detected")

        temp_dir = os.path.join(OS_DIR, "archive/quarantine")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            torrent_handler = os.path.join(AIM_CORE_DIR, "aim_torrent.py")
            if not os.path.exists(torrent_handler):
                print("[ERROR] Torrent handler not found. Ensure Phase 38 is fully installed.")
                sys.exit(1)

            print("  Connecting to swarm. Please wait (this depends on seeder availability)...")
            result = subprocess.run(
                [_resolve_venv_python(), torrent_handler, "download", target, temp_dir],
                capture_output=True,
                text=True,
                check=True,
            )

            output_lines = result.stdout.strip().split("\n")
            downloaded_file = ""
            for line in reversed(output_lines):
                if line.startswith("SUCCESS_PATH:"):
                    downloaded_file = line.replace("SUCCESS_PATH:", "").strip()
                    break

            if not downloaded_file or not os.path.exists(downloaded_file):
                print("[ERROR] Swarm download failed or returned invalid file path.")
                print(f"  DEBUG:\n{result.stdout}\n{result.stderr}")
                sys.exit(1)

            print(f"[JACK-IN] Swarm payload isolated in Quarantine: {os.path.basename(downloaded_file)}")
            print("          The Quarantine Daemon will perform heuristic analysis before merging.")
            return
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] DataJack Swarm failure (Code {e.returncode}).")
            print(f"  DEBUG:\n{e.stdout}\n{e.stderr}")
            sys.exit(e.returncode)

    _run_script(os.path.join(AIM_CORE_DIR, "plugins", "datajack", "aim_exchange.py"), ["import", target])


def cmd_unplug(args):
    """Dispatches to aim_exchange.py unplug."""
    _run_script(os.path.join(AIM_CORE_DIR, "plugins", "datajack", "aim_exchange.py"), ["unplug"] + sys.argv[2:])


def cmd_purge(args):
    """Executes the Clean Slate Protocol --- (Safety Warning Required) ---"""
    print("--- A.I.M. Clean Slate Protocol (The Purge) ---")
    confirm = input("This will permanently delete ALL memory, continuity, and database files. Are you sure? [y/N]: ")
    if confirm.lower() != "y":
        return

    dirs = ["continuity/", "archive/raw/", "archive/history/", "archive/sync/", "workstreams/", "memory_lance/", "archive/cartridges/"]
    for d in dirs:
        path = os.path.join(BASE_DIR, d)
        if os.path.exists(path):
            shutil.rmtree(path)
            os.makedirs(path, exist_ok=True)

    db_paths = [os.path.join(OS_DIR, "archive/project_core.db"), os.path.join(OS_DIR, "archive/history.db")]
    for db_path in db_paths:
        if os.path.exists(db_path):
            os.remove(db_path)

    docs = ["ROADMAP.md", "CURRENT_STATE.md", "DECISIONS.md"]
    for doc in docs:
        doc_path = os.path.join(OS_DIR, "docs", doc)
        if os.path.exists(doc_path):
            with open(doc_path, "w") as f:
                f.write(f"# {doc.replace('.md', '').title()}\n\n[PURGED: {datetime.now().strftime('%Y-%m-%d %H:%M')}]\n")

    print("\n[SUCCESS] A.I.M. has been purged.")


def cmd_uninstall(args):
    """Interactive uninstaller."""
    print("\n--- A.I.M. UNINSTALLER ---")
    confirm = input("\nRemove A.I.M. from your system? [y/N]: ").lower()
    if confirm != "y":
        return

    print("\n1. Software Only\n2. Total Purge")
    choice = input("\nSelect [1-2]: ").strip()

    if choice == "2":
        for item in os.listdir(BASE_DIR):
            p = os.path.join(BASE_DIR, item)
            if os.path.isfile(p):
                os.unlink(p)
            elif os.path.isdir(p):
                shutil.rmtree(p)
    else:
        dirs = [".aim_core/", "hooks/", "venv/", "archive/experimental/"]
        for d in dirs:
            p = os.path.join(BASE_DIR, d)
            if os.path.exists(p):
                shutil.rmtree(p)
        for f in ["setup.sh", "requirements.txt", "LICENSE"]:
            p = os.path.join(BASE_DIR, f)
            if os.path.exists(p):
                os.remove(p)

    print("\n[SUCCESS] A.I.M. removed.")


def cmd_import(args):
    """Manually ingests raw JSONL, JSON, or MD files into the Subconscious Swarm."""
    filepath = getattr(args, "file", None)
    if not filepath:
        print("Usage: aim import <path/to/file.jsonl | file.md>")
        sys.exit(1)

    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        sys.exit(1)

    subprocess.run([sys.executable, os.path.join(OS_DIR, ".aim_core", "memory_salvage.py"), filepath], check=False)
