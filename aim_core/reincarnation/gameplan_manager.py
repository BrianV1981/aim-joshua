import os
import sys
import time

def load_and_validate_gameplan(aim_root):
    print("Assuming the live agent has already written REINCARNATION_GAMEPLAN.md to .aim_core/temp...")
    
    temp_dir = os.path.join(aim_root, ".aim_core", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    gameplan_path = os.path.join(temp_dir, "REINCARNATION_GAMEPLAN.md")
    
    if not os.path.exists(gameplan_path):
        print(f"\n[FATAL] Missing {gameplan_path}!")
        print("You MUST write a Reincarnation Gameplan before triggering a handoff.")
        sys.exit(1)
        
    mtime = os.path.getmtime(gameplan_path)
    if time.time() - mtime > 300: # 5 minutes
        print(f"\n[FATAL] The REINCARNATION_GAMEPLAN.md is stale (last updated over 5 minutes ago)!")
        print("You MUST update the Gameplan to reflect the current state before triggering a handoff.")
        sys.exit(1)

    with open(gameplan_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print("Verified live agent has recently updated REINCARNATION_GAMEPLAN.md...")
    return content

def cleanup_gameplan(aim_root):
    gameplan_path = os.path.join(aim_root, ".aim_core", "temp", "REINCARNATION_GAMEPLAN.md")
    try:
        os.remove(gameplan_path)
    except FileNotFoundError:
        pass
