#!/bin/bash
# A.I.M. Clean OS Installer (Default)
# curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install.sh | bash

set -euo pipefail
echo "--- J.O.S.H.U.A. CLEAN INSTALLER ---"

CURRENT_DIR=$(pwd)
if [ "$CURRENT_DIR" = "$HOME" ] || [ "$CURRENT_DIR" = "/" ]; then
    echo "[ERROR] Refusing to install directly in $CURRENT_DIR." >&2
    echo "Please create and cd into a dedicated project directory first:" >&2
    echo "  mkdir -p ~/my-project && cd ~/my-project" >&2
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 (3.10+) is required on PATH." >&2
    exit 1
fi

TEMP_CLONE=""
cleanup() {
    local rc=$?
    if [ -n "$TEMP_CLONE" ] && [ -d "$TEMP_CLONE" ]; then
        rm -rf "$TEMP_CLONE"
    fi
    exit "$rc"
}
trap cleanup EXIT

if [ -n "${AIM_INSTALL_SOURCE:-}" ] && [ -f "$AIM_INSTALL_SOURCE/joshua_os/.aim_core/bootstrap_install.py" ]; then
    SOURCE_ROOT="$AIM_INSTALL_SOURCE"
else
    TEMP_CLONE="$CURRENT_DIR/.aim_temp_clone"
    rm -rf "$TEMP_CLONE"
    echo "[*] Step 1: Cloning J.O.S.H.U.A. Operating System..."
    git clone --depth 1 https://github.com/BrianV1981/aim-joshua.git "$TEMP_CLONE"
    SOURCE_ROOT="$TEMP_CLONE"
fi

EXTRA_ARGS=()
[ "${AIM_SKIP_DEPS:-0}" = "1" ] && EXTRA_ARGS+=("--skip-deps")
[ -n "${AIM_HOME_OVERRIDE:-}" ] && EXTRA_ARGS+=("--home" "$AIM_HOME_OVERRIDE")
[ "${AIM_SKIP_SHELL_RC:-0}" = "1" ] && EXTRA_ARGS+=("--skip-shell-rc")

python3 "$SOURCE_ROOT/joshua_os/.aim_core/bootstrap_install.py" \
    --mode clean --source "$SOURCE_ROOT" --target "$CURRENT_DIR" "${EXTRA_ARGS[@]}"
