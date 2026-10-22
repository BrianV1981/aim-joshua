#!/bin/bash
# A.I.M. Exoskeleton Installer (Clean Project Wrapper)
# curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install-clean.sh | bash

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

# Clean Sweep (Severing identity and cleaning out developer artifacts BEFORE moving)
rm -rf .git/ .github/ .vscode/
rm -rf joshua_os/tests/ joshua_os/benchmarks/ joshua_os/docs/ joshua_os/scripts/ joshua_os/skills/ joshua_os/memory-wiki/

cp -a joshua_os ../

cp -n AGENTS.md ../ 2>/dev/null || true
cp -n TOOLS.md ../ 2>/dev/null || true
cp -n aim.ps1 ../ 2>/dev/null || true
cp -n aim.cmd ../ 2>/dev/null || true

cd ..
rm -rf .aim_temp_clone

if [ ! -d ".git" ]; then
    git init
fi

touch .gitignore
for entry in "joshua_os/" "aim" "aim.ps1" "aim.cmd" "workspace/" "archive/"; do
    base="${entry%/}"
    if ! grep -qxE "/?${base}(/|/\*)?" .gitignore 2>/dev/null; then
        echo "$entry" >> .gitignore
    fi
done

mkdir -p memory-wiki/pages
[ ! -f memory-wiki/index.md ] && printf "# %s — Memory Wiki Index\n\n## Core Pages\n" "$CLI_NAME" > memory-wiki/index.md
[ ! -f memory-wiki/log.md ] && printf "# %s — Memory Wiki Log\n" "$CLI_NAME" > memory-wiki/log.md

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
echo "J.O.S.H.U.A. is installed and ready. A default AGENTS.md blueprint has been provided."
echo ""
