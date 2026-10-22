#!/bin/bash
# A.I.M. Exoskeleton Installer (Clean Project Wrapper — Delegates to install.sh)
# curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install-clean.sh | bash

set -e

CURRENT_DIR=$(pwd)
if [ "$CURRENT_DIR" = "$HOME" ] || [ "$CURRENT_DIR" = "/" ]; then
    echo "[ERROR] Refusing to install directly in $CURRENT_DIR."
    echo "Please create and cd into a dedicated project directory first:"
    echo "  mkdir -p ~/my-project && cd ~/my-project"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/install.sh" ]; then
    exec bash "$SCRIPT_DIR/install.sh" "$@"
else
    curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install.sh | bash -s -- "$@"
fi
