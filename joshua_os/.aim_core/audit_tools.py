import os
import sys

_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from blackbox_vault import connect_history_db, sync_vault_to_history
from config_utils import OS_ROOT, PROJECT_ROOT
from reasoning_utils import generate_reasoning


def run_audit(n_sessions=5):
    """
    Pulls the last N sessions from joshua_os/archive/history.db and generates
    a WEEKLY_SITREP.md report for the human operator.
    """
    db_path = os.path.join(OS_ROOT, "archive", "history.db")
    if not os.path.exists(db_path):
        try:
            sync_vault_to_history(PROJECT_ROOT)
        except Exception:
            pass

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}", file=sys.stderr)
        return

    conn = None
    try:
        conn = connect_history_db(db_path)
        c = conn.cursor()
        c.execute(
            "SELECT session_id, timestamp, content FROM history ORDER BY timestamp DESC LIMIT ?",
            (n_sessions,),
        )
        rows = c.fetchall()
    except Exception as e:
        print(f"Error reading database: {e}", file=sys.stderr)
        return
    finally:
        if conn is not None:
            conn.close()

    if not rows:
        print("No historical sessions found to audit.")
        return

    context = ""
    for session_id, timestamp, content in reversed(rows):
        context += f"--- Session: {session_id} | Date: {timestamp} ---\n{content}\n\n"

    print(f"Auditing last {len(rows)} sessions. Generating Strategic Synthesis...")

    prompt = (
        f"Analyze the following {len(rows)} recent A.I.M. sessions and generate a comprehensive strategic synthesis.\n\n"
        "Output a WEEKLY_SITREP.md formatted report containing:\n"
        "1. Executive Summary\n2. Key Achievements & Completed Tasks\n"
        "3. Outstanding Issues & Blockers\n4. Recommended Next Steps (Roadmap Proposal)\n\n"
        "Do not include any introductory conversation. Output pure markdown.\n\n"
        f"SESSIONS CONTEXT:\n{context}"
    )

    system_instruction = (
        "You are A.I.M. (Actual Intelligent Memory), a senior technical lead. "
        "Your job is to analyze historical terminal sessions and synthesize a high-level strategic report."
    )

    report_content = generate_reasoning(prompt, system_instruction=system_instruction)

    report_path = os.path.join(OS_ROOT, "WEEKLY_SITREP.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\n[SUCCESS] Strategic Synthesis complete! Report generated at: {report_path}")
    print("Please review the WEEKLY_SITREP.md file and create new `aim bug` tickets based on the insights.")
