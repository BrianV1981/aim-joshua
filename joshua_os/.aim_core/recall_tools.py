import os
import sys

_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from blackbox_vault import connect_history_db, sync_vault_to_history
from cli_memory import _sanitize_fts5_query
from config_utils import OS_ROOT, PROJECT_ROOT
from reasoning_utils import generate_reasoning


def run_recall(query, limit=5):
    """
    Queries joshua_os/archive/history.db using FTS5 and synthesizes matching
    session contexts to answer the user's question directly.
    """
    db_path = os.path.join(OS_ROOT, "archive", "history.db")
    if not os.path.exists(db_path):
        try:
            sync_vault_to_history(PROJECT_ROOT)
        except Exception:
            pass

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}", file=sys.stderr)
        return None

    fts_query = _sanitize_fts5_query(query)
    if not fts_query:
        print(f"No historical context found for '{query}'.")
        return None

    conn = None
    try:
        conn = connect_history_db(db_path)
        c = conn.cursor()
        c.execute(
            """
            SELECT session_id, timestamp, content
            FROM history_fts
            WHERE history_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (fts_query, limit),
        )
        rows = c.fetchall()
    except Exception as e:
        print(f"Error reading database: {e}", file=sys.stderr)
        return None
    finally:
        if conn is not None:
            conn.close()

    if not rows:
        print(f"No historical context found for '{query}'.")
        return None

    context = ""
    for session_id, timestamp, content in rows:
        context += f"--- Session: {session_id} | Date: {timestamp} ---\n{content}\n\n"

    print(f"Recalling memory from {len(rows)} historical session(s)...")

    prompt = (
        "You are tasked with answering a user's question using ONLY the provided historical session transcripts.\n"
        f'Question/Query: "{query}"\n\n'
        "Synthesize the findings and output a precise memory recall of the exact conversation context.\n"
        "Do not hallucinate external knowledge. If the answer is not in the context, state that you cannot recall.\n\n"
        f"HISTORICAL CONTEXT:\n{context}"
    )

    system_instruction = (
        "You are the A.I.M. Panopticon Protocol. You provide exact, synthesized memory recall "
        "based only on the provided session transcripts."
    )

    synthesis = generate_reasoning(prompt, system_instruction=system_instruction)

    print("\n--- 🧠 MEMORY RECALL ---\n")
    print(synthesis)
    print("\n------------------------")

    return synthesis
