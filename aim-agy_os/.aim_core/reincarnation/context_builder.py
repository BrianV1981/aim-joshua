import os
import sys

def fetch_issue_context(aim_root):
    issues_content = ""
    try:
        sys.path.append(os.path.join(aim_root, ".aim_core"))
        import sync_issue_tracker
        open_issues = sync_issue_tracker.fetch_issues(state="open")
        issues_content = sync_issue_tracker.generate_markdown(open_issues)
    except Exception as e:
        print(f"      [WARNING] Could not fetch live issues: {e}")
        issues_content = "*Error fetching live issues from GitHub.*\n"
    return issues_content

def build_wakeup_prompt(gameplan_content, issues_content):
    return (
        "Wake up. MANDATE: Read AGENTS.md and acknowledge your core constraints. "
        "Review your injected Gameplan and Issue Tracker below before taking any action.\n\n"
        "--- REINCARNATION GAMEPLAN ---\n"
        f"{gameplan_content}\n\n"
        "--- LIVE ISSUE TRACKER ---\n"
        f"{issues_content}"
    )
