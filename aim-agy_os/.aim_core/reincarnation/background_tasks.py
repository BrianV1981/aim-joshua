import os
import sys
import subprocess

def trigger_background_pipelines(aim_root, workspace, session_id=None):
    print("[1/4] Mechanically extracting session signal & routing to pipelines...")
    
    venv_python = os.path.join(aim_root, "venv", "bin", "python3")
    if not os.path.exists(venv_python):
        venv_python = sys.executable

    try:
        pulse_args = [venv_python, os.path.join(aim_root, ".aim_core", "handoff_pulse_generator.py")]
        if session_id:
            pulse_args.extend(["--session-id", session_id])
            
        # Pulse owns wiki daemon spawn (archive path + daemon.log). Do NOT
        # re-Popen session_summarizer here — a second --bg with no path races
        # _ingest/, double-processes the newest archive, and swallows logs (DEVNULL).
        subprocess.run(pulse_args, cwd=workspace, check=True, timeout=120)
        print(
            "      Pulse complete (wiki daemon triggered by handoff when monolithic; "
            "see memory-wiki/daemon.log)."
        )

        print("      Syncing remote issues and harvesting closed bugs...")
        # Harvest recently completed bugs into foundry/scraped_docs
        subprocess.run(
            [venv_python, os.path.join(aim_root, ".aim_core", "aim_scraper.py"), "--source", "github", "--query", "is:closed", "--limit", "5"],
            cwd=workspace, check=False, timeout=30
        )
        
    except subprocess.TimeoutExpired as e:
        print(f"\n[WARNING] A reincarnation subprocess timed out: {e}\nContinuing reincarnation protocol anyway to preserve context...")
    except subprocess.CalledProcessError as e:
        # Pulse/scribe failure must not block vessel spawn — handoff is best-effort.
        print(f"[WARNING] Handoff pipeline error (continuing reincarnation): {e}")
