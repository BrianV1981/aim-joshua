#!/usr/bin/env bash
# Ensure nested OS venv exists (lockstep)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
OS="$ROOT/aim-agy_os"
cd "$OS"
if [[ ! -d venv ]]; then
  bash setup.sh
else
  echo "[setup_nested] aim-agy_os/venv already present"
fi
# symlink root venv → nested for old scripts if root venv missing
if [[ ! -e "$ROOT/venv" ]]; then
  ln -s aim-agy_os/venv "$ROOT/venv" || true
fi
echo "[setup_nested] done"
