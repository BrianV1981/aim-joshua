#!/bin/bash
# A.I.M. Clean OS Installer (Default)
# curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install.sh | bash

set -e
echo "--- J.O.S.H.U.A. CLEAN INSTALLER ---"

CURRENT_DIR=$(pwd)
CLI_NAME=$(basename "$CURRENT_DIR")

if [ "$CURRENT_DIR" = "$HOME" ] || [ "$CURRENT_DIR" = "/" ]; then
    echo "[ERROR] Refusing to install directly in $CURRENT_DIR."
    echo "Please create and cd into a dedicated project directory first:"
    echo "  mkdir -p ~/my-project && cd ~/my-project"
    exit 1
fi

echo "[*] Step 1: Provisioning Local Operating System..."

# Clone the engine directly into a temporary hidden folder to avoid empty directory conflicts
git clone --depth 1 https://github.com/BrianV1981/aim-joshua.git .aim_temp_clone
cd .aim_temp_clone

echo "    [*] Building Engine Virtual Environment..."
./joshua_os/setup.sh

# Safely merge the Engine components into the host project
echo "[*] Step 2: Scaffolding Sovereign Environment..."

rm -rf joshua_os/tests/ joshua_os/benchmarks/ joshua_os/memory-wiki/

cp -a joshua_os ../
cp -n AGENTS.md ../ 2>/dev/null || true
cp -n TOOLS.md ../ 2>/dev/null || true

cd ..
rm -rf .aim_temp_clone

if [ ! -d ".git" ]; then
    git init
fi

[ ! -f README.md ] && echo "# $CLI_NAME" > README.md

# Base OS Provisioning (Moving the pre-baked DB to the active layer)
mkdir -p joshua_os/memory_lance
cp -r joshua_os/assets/default_lance/* joshua_os/memory_lance/

echo "    [*] Registering MCP Server..."
python3 ./joshua_os/.aim_core/register_mcp.py

echo "    [*] Linking Local Alias ($CLI_NAME)..."
bash ./joshua_os/link_cli_alias.sh "$CURRENT_DIR" "$CLI_NAME"

if [[ -f ./joshua_os/.aim_core/agy_workspace_trust.py ]]; then
    PYTHONPATH="./joshua_os/.aim_core${PYTHONPATH:+:$PYTHONPATH}" \
        python3 ./joshua_os/.aim_core/agy_workspace_trust.py "$CURRENT_DIR" || true
fi

echo ""
echo "--- INSTALLATION COMPLETE ---"
echo "You have successfully installed the clean J.O.S.H.U.A. OS into $CURRENT_DIR."
echo "Next steps:"
echo "  1. source ~/.bashrc"
echo "  2. $CLI_NAME doctor"
echo "  3. Customize AGENTS.md for $CLI_NAME and run: ./aim index"
echo ""
