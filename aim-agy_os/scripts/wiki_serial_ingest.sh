#!/usr/bin/env bash
# Serial memory-wiki Stage 0 multi-page ingest (one archive at a time).
# Fleet lockstep: shared script under aim-agy_os/scripts/
#
# Usage:
#   ./aim-agy_os/scripts/wiki_serial_ingest.sh --archive path/to.md [--source-id ID]
#   ./aim-agy_os/scripts/wiki_serial_ingest.sh --queue memory-wiki/_queue/pending.txt
#   ./aim-agy_os/scripts/wiki_serial_ingest.sh --list-archives
#   ./aim-agy_os/scripts/wiki_serial_ingest.sh --dry-run --archive ...
#
# Queue file: one path per line (optional second field = source_id). # comments ok.
# Does NOT run LLM agent mode (Stage 1). Deterministic multi-page only.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ ! -f "$OS_DIR/.aim_core/wiki_compiler.py" ]]; then
  echo "Cannot find wiki_compiler under $OS_DIR" >&2
  exit 1
fi
VESSEL_ROOT="$(cd "$OS_DIR/.." && pwd)"

PY="${OS_DIR}/venv/bin/python3"
[[ -x "$PY" ]] || PY=python3
export PYTHONPATH="${OS_DIR}/.aim_core${PYTHONPATH:+:$PYTHONPATH}"

ARCHIVE=""
SOURCE_ID=""
QUEUE=""
LIST=0
STOP_AFTER=0
DRY=0

usage() {
  sed -n '2,14p' "$0"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive) ARCHIVE="$2"; shift 2 ;;
    --source-id) SOURCE_ID="$2"; shift 2 ;;
    --queue) QUEUE="$2"; shift 2 ;;
    --list-archives) LIST=1; shift ;;
    --stop-after) STOP_AFTER="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1"; usage ;;
  esac
done

cd "$VESSEL_ROOT"

if [[ "$LIST" -eq 1 ]]; then
  ls -1t "${OS_DIR}/archive/history/"*.md 2>/dev/null || echo "(no archives)"
  exit 0
fi

run_one() {
  local path="$1"
  local sid="${2:-}"
  if [[ ! -f "$path" ]]; then
    if [[ -f "${OS_DIR}/archive/history/$path" ]]; then
      path="${OS_DIR}/archive/history/$path"
    else
      echo "[ERROR] missing archive: $path" >&2
      return 1
    fi
  fi
  echo "=== Stage 0 multi-page: $path (source_id=${sid:-auto}) ==="
  if [[ "$DRY" -eq 1 ]]; then
    echo "[dry-run] would integrate $path"
    return 0
  fi
  "$PY" - "$path" "$sid" <<'PY'
import sys
from pathlib import Path
from wiki_compiler import stage0_multi_page_integrate
path = Path(sys.argv[1])
sid = sys.argv[2] or None
if sid == "":
    sid = None
for line in stage0_multi_page_integrate(path, source_id=sid):
    print(" ", line)
print("[OK] done")
PY
}

if [[ -n "$ARCHIVE" ]]; then
  run_one "$ARCHIVE" "$SOURCE_ID"
  exit 0
fi

if [[ -n "$QUEUE" ]]; then
  [[ -f "$QUEUE" ]] || { echo "queue not found: $QUEUE" >&2; exit 1; }
  n=0
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    [[ -z "${line// /}" || "$line" =~ ^[[:space:]]*# ]] && continue
    path=$(echo "$line" | awk '{print $1}')
    sid=$(echo "$line" | awk '{print $2}')
    run_one "$path" "${sid:-}"
    n=$((n + 1))
    if [[ "$STOP_AFTER" -gt 0 && "$n" -ge "$STOP_AFTER" ]]; then
      echo "[STOP] stop-after=$STOP_AFTER"
      break
    fi
  done < "$QUEUE"
  exit 0
fi

usage
