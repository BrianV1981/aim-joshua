#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from datetime import datetime

def find_aim_root():
    current = os.path.abspath(os.getcwd())
    while current != '/':
        if os.path.exists(os.path.join(current, ".aim_core/CONFIG.json")) or os.path.exists(os.path.join(current, "setup.sh")): return current
        if os.path.exists(os.path.join(current, "setup.sh")): return current
        current = os.path.dirname(current)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AIM_ROOT = find_aim_root()

def fetch_issues(state="open", limit=100):
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--state", state, "--limit", str(limit), "--json", "number,title,labels,createdAt"],
            capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to fetch {state} issues from GitHub: {e.stderr}")
        return []
    except json.JSONDecodeError:
        print(f"[ERROR] Failed to parse GitHub CLI output.")
        return []

def generate_markdown(open_issues):
    now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    md = f"# A.I.M. Issue Ledger\n\n"
    md += f"*Last Synchronized: {now}*\n"
    md += f"*This file serves as the local, zero-latency index of all active project tasks.*\n\n"
    
    md += "## 🟢 OPEN ISSUES (Actionable)\n\n"
    if not open_issues:
        md += "*No open issues found.*\n\n"
    else:
        for issue in open_issues:
            labels = ", ".join([label['name'] for label in issue.get('labels', [])])
            label_str = f" [{labels}]" if labels else ""
            date_str = issue.get('createdAt', '')[:10]
            md += f"* **#{issue['number']}** - {issue['title']}{label_str} *(Created: {date_str})*\n"
            
    return md

def main():
    print("--- A.I.M. ISSUE SYNCHRONIZER ---")
    
    print("[1/2] Fetching OPEN issues from GitHub...")
    open_issues = fetch_issues(state="open")
    
    print("[2/2] Generating local ledger...")
    markdown_content = generate_markdown(open_issues)
    
    print(markdown_content)
        
    print("\n[SUCCESS] Local Issue Ledger fetched.")

if __name__ == "__main__":
    main()