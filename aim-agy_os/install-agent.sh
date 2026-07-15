#!/bin/bash
# A.I.M. Sovereign Co-Agent Installer
# curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-agy/main/aim-agy_os/install-agent.sh | bash -s python-developer

set -e
echo "--- A.I.M. SOVEREIGN CO-AGENT INSTALLER ---"

PERSONA="${1:-generic-node}"
echo "[*] Target Persona Blueprint: $PERSONA"

CURRENT_DIR=$(pwd)
CLI_NAME=$(basename "$CURRENT_DIR")

echo "[*] Step 1: Provisioning Local Operating System..."

# Clone the engine directly into a temporary hidden folder to avoid empty directory conflicts
git clone --depth 1 https://github.com/BrianV1981/aim-agy.git .aim_temp_clone
cd .aim_temp_clone

echo "    [*] Building Engine Virtual Environment..."
./aim-agy_os/setup.sh

# Safely merge the Engine components into the host project
echo "[*] Step 2: Scaffolding Sovereign Environment..."

# Clean Sweep (Severing identity and cleaning out developer artifacts BEFORE moving)
rm -rf .git/ .github/ .vscode/
rm -rf aim-agy_os/tests/ aim-agy_os/benchmarks/ aim-agy_os/docs/ aim-agy_os/scripts/ aim-agy_os/skills/

cp -a aim-agy_os ../
cp -a aim-agy_os_docs ../ 2>/dev/null || true

cp -n AGENTS.md ../ 2>/dev/null || true
cp -n TOOLS.md ../ 2>/dev/null || true

cd ..
rm -rf .aim_temp_clone

if [ ! -d ".git" ]; then
    git init
fi

[ ! -f README.md ] && touch README.md
[ ! -f CHANGELOG.md ] && touch CHANGELOG.md
[ ! -f VERSION ] && touch VERSION
[ ! -f CONTRIBUTING.md ] && touch CONTRIBUTING.md

# Base OS Provisioning (Moving the pre-baked DB to the active layer)
mkdir -p aim-agy_os/memory_lance
cp -r aim-agy_os/assets/default_lance/* aim-agy_os/memory_lance/

echo "    [*] Initializing Headless OS..."
./aim-agy_os/venv/bin/python3 ./aim-agy_os/.aim_core/aim_cli.py init --headless --persona "$PERSONA"

echo ""
echo "--- CO-AGENT DEPLOYMENT COMPLETE ---"
echo "Your Sovereign Node ($PERSONA) is installed."
