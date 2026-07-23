#!/usr/bin/env bash
# aim-opencode handoff vNext cron wrapper — vessel-isolated
set -euo pipefail
cd /home/kingb/aim-opencode
export PYTHONPATH='aim-agy_os:aim-agy_os/.aim_core'
LOG_DIR="$HOME/.aim/cron/logs/aim-opencode"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/handoff_$(date +%Y%m%d).log"
exec python3 aim-agy_os/handoff/cli.py "$@" --vessel-root /home/kingb/aim-opencode --adapter opencode >> "$LOG" 2>&1
