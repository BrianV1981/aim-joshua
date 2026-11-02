#!/usr/bin/env python3
import os
import glob
import time
import shutil
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="A.I.M. Benchmark JSON Recovery Protocol")
    parser.add_argument("--dest", type=str, default="docs/benchmarks/raw_logs", help="Destination folder for recovered logs")
    parser.add_argument("--hours", type=int, default=24, help="How many hours back to search")
    parser.add_argument("--auto-copy", action="store_true", help="Automatically copy found files without prompting")
    args = parser.parse_args()

    from config_utils import get_agy_roots

    agy_roots = get_agy_roots()
    brain_dirs = [os.path.join(r, "brain") for r in agy_roots if os.path.isdir(os.path.join(r, "brain"))]
    dest_dir = Path(args.dest)
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"--- A.I.M. BENCHMARK RECOVERY PROTOCOL ---")
    print(f"Searching hidden Antigravity temporary environment caches...")
    if not brain_dirs:
        print(f"Error: Could not find any global Antigravity brain directory under {[os.path.join(r, 'brain') for r in agy_roots]}")
        return

    # Load workspace mapping from history
    import json
    workspace_map = {}
    for agy_root in agy_roots:
        history_file = os.path.join(agy_root, "history.jsonl")
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        data = json.loads(line)
                        cid = data.get("conversationId")
                        ws = data.get("workspace")
                        if cid and ws:
                            workspace_map[cid] = os.path.basename(ws)
            except Exception:
                pass

    # Find all jsonl files in the brain subdirectories
    files = []
    for tmp_dir in brain_dirs:
        print(f"Path: {tmp_dir}/*/.system_generated/logs/*.jsonl")
        files.extend(glob.glob(os.path.join(tmp_dir, "*", ".system_generated", "logs", "*.jsonl")))
    print("")

    # Filter by time
    current_time = time.time()
    cutoff_time = current_time - (args.hours * 3600)
    recent_files = [f for f in files if os.path.getmtime(f) > cutoff_time]
    
    # Sort by newest first
    recent_files.sort(key=os.path.getmtime, reverse=True)

    if not recent_files:
        print(f"No benchmark logs found from the last {args.hours} hours.")
        return

    print(f"Found {len(recent_files)} recent session logs across all isolated environments:")
    for i, f in enumerate(recent_files):
        mod_time = time.ctime(os.path.getmtime(f))
        size_kb = os.path.getsize(f) / 1024
        # Extract the environment name from history map
        session_id = Path(f).parts[-4]
        env_name = workspace_map.get(session_id, "unknown_env")
        print(f" [{i+1}] {env_name} | {mod_time} | {size_kb:.1f} KB")
        print(f"     Path: {f}")

    print("\n-------------------------------------------")
    if args.auto_copy:
        for f in recent_files:
            session_id = Path(f).parts[-4]
            env_name = workspace_map.get(session_id, "unknown_env")
            new_name = f"{env_name}_{session_id}.jsonl"
            dest_path = dest_dir / new_name
            shutil.copy2(f, dest_path)
            print(f"Copied to: {dest_path}")
    else:
        choice = input(f"\nDo you want to copy these {len(recent_files)} files to '{args.dest}/'? (y/n): ")
        if choice.lower() == 'y':
            for f in recent_files:
                session_id = Path(f).parts[-4]
                env_name = workspace_map.get(session_id, "unknown_env")
                new_name = f"{env_name}_{session_id}.jsonl"
                dest_path = dest_dir / new_name
                shutil.copy2(f, dest_path)
                print(f"Copied to: {dest_path}")
        else:
            print("Recovery aborted. The files remain safe in the hidden cache.")

if __name__ == "__main__":
    main()
