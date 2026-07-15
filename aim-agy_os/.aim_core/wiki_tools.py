import os
import glob
import sqlite3
import time

try:
    from aim_core.reasoning_utils import generate_reasoning
except ImportError:
    try:
        from reasoning_utils import generate_reasoning
    except ImportError:
        generate_reasoning = None  # type: ignore


def get_base_dir():
    """Prefer nested aim-agy_os; fall back to vessel root with core/CONFIG or setup.sh."""
    current = os.path.abspath(os.getcwd())
    while current != "/":
        nested = os.path.join(current, "aim-agy_os")
        if os.path.exists(os.path.join(nested, "setup.sh")):
            return nested
        if os.path.exists(os.path.join(current, "setup.sh")):
            return current
        if os.path.exists(os.path.join(current, "core", "CONFIG.json")):
            # flat vessel: wiki often at vessel_root/memory-wiki
            return current
        current = os.path.dirname(current)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _wiki_dir(base_dir):
    # nested OS: base is aim-agy_os → memory-wiki under it OR vessel parent
    candidates = [
        os.path.join(base_dir, "memory-wiki"),
        os.path.join(os.path.dirname(base_dir), "memory-wiki"),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    return os.path.join(base_dir, "memory-wiki")


def search_wiki(query):
    base_dir = get_base_dir()
    wiki_dir = _wiki_dir(base_dir)
    if not os.path.exists(wiki_dir):
        print("Error: memory-wiki/ directory not found. Please initialize the wiki first.")
        return
    conn = sqlite3.connect(":memory:")
    c = conn.cursor()
    c.execute("""CREATE VIRTUAL TABLE wiki_fts USING fts5(filepath, content)""")
    md_files = glob.glob(os.path.join(wiki_dir, "**", "*.md"), recursive=True)
    for file_path in md_files:
        if os.path.basename(file_path) in ("GEMINI.md",):
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                c.execute(
                    "INSERT INTO wiki_fts (filepath, content) VALUES (?, ?)",
                    (os.path.relpath(file_path, wiki_dir), content),
                )
        except Exception as e:
            import sys
            print(f"[WARN] Failed to read {file_path}: {e}", file=sys.stderr)
    try:
        c.execute(
            "SELECT filepath, snippet(wiki_fts, 1, '>>', '<<', '...', 64) "
            "FROM wiki_fts WHERE wiki_fts MATCH ? ORDER BY rank LIMIT 5",
            (query,),
        )
        results = c.fetchall()
    except sqlite3.OperationalError:
        c.execute(
            "SELECT filepath, substr(content, 1, 200) FROM wiki_fts WHERE content LIKE ? LIMIT 5",
            (f"%{query}%",),
        )
        results = c.fetchall()
    conn.close()
    if not results:
        print(f"No results found in Wiki for '{query}'.")
        return
    print(f"\n--- 🔍 WIKI SEARCH RESULTS: '{query}' ---")
    for filepath, snippet in results:
        print(f"\n📄 {filepath}:\n{snippet}\n")
    print("-----------------------------------")


def process_wiki_agent():
    import subprocess
    base_dir = get_base_dir()
    wiki_dir = _wiki_dir(base_dir)
    ingest_dir = os.path.join(wiki_dir, "_ingest")
    if not os.path.exists(ingest_dir):
        print("Error: memory-wiki/_ingest/ directory not found.")
        return
    files = [
        f for f in glob.glob(os.path.join(ingest_dir, "*.*"))
        if os.path.basename(f) not in (".gitkeep", ".keep")
    ]
    if not files:
        print("No files found in memory-wiki/_ingest/ to process.")
        return
    try:
        from session_naming import build_agent_session_name
        session_name = build_agent_session_name("wiki", base_dir)
    except Exception:
        session_name = f"wiki_agent_{os.path.basename(base_dir)}_{int(time.time())}"
    check_cmd = subprocess.run(["tmux", "has-session", "-t", session_name], capture_output=True)
    if check_cmd.returncode == 0:
        print(f"[{session_name}] is already active. Skipping new spawn.")
        return
    print(f"Starting fresh '{session_name}' tmux session (opencode)...")
    subprocess.run([
        "tmux", "new-session", "-d", "-s", session_name, "-c", wiki_dir,
        "opencode", "--dangerously-skip-permissions",
    ])
    time.sleep(4)
    prompt = (
        "Read AGENTS.md (schema) and index.md first. "
        "Process exactly ONE file in `_ingest/` per the schema: integrate into "
        "index.md, log.md, and pages/; delete that file; stop. "
        f"When empty: type /exit or `tmux kill-session -t {session_name}`."
    )
    try:
        subprocess.run(["tmux", "set-buffer", prompt], check=True)
        subprocess.run(["tmux", "paste-buffer", "-p", "-t", session_name], check=True)
        time.sleep(1)
        subprocess.run(["tmux", "send-keys", "-t", session_name, "Enter"], check=True)
        print(f"[SUCCESS] Directives dispatched to {session_name}.")
    except Exception as e:
        print(f"[ERROR] Failed to hand off to {session_name}: {e}")


def process_wiki_deterministic():
    print("--- WIKI PROCESS (deterministic) ---")
    # Prefer nested compiler; set cwd context
    try:
        from wiki_compiler import process_raw_logs_to_ingest, process_ingest, ensure_wiki_scaffold, wiki_paths
    except ImportError:
        print("[ERROR] wiki_compiler.py missing — cannot run deterministic wiki.")
        return []
    ensure_wiki_scaffold(wiki_paths())
    for line in process_raw_logs_to_ingest():
        print(" ", line)
    results = process_ingest()
    for line in results:
        print(" ", line)
    return results


def process_wiki():
    """
    Default: deterministic (fleet lockstep B).
    AIM_WIKI_MODE=agent → opencode tmux maintainer.
    """
    mode = os.environ.get("AIM_WIKI_MODE", "deterministic").lower()
    if mode in ("agent", "llm", "opencode"):
        return process_wiki_agent()
    return process_wiki_deterministic()
