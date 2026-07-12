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
            
        subprocess.run(pulse_args, cwd=workspace, check=True, timeout=120)
        
        print("      Triggering Subconscious Scribe (Session Summarizer)...")
        subprocess.Popen(
            [venv_python, os.path.join(aim_root, "hooks", "session_summarizer.py"), "--reincarnate", "--bg"],
            cwd=workspace,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
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
        print(f"[ERROR] Failed to generate handoff: {e}")
        sys.exit(1)
