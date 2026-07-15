#!/bin/bash
# A.I.M. Sovereign Co-Agent Installer (headless)
# curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-agy/main/aim-agy_os/install-agent.sh | bash -s python-developer

set -e
echo "--- A.I.M. SOVEREIGN CO-AGENT INSTALLER ---"

PERSONA="${1:-generic-node}"
echo "[*] Target Persona Blueprint: $PERSONA"

CURRENT_DIR=$(pwd)
CLI_NAME=$(basename "$CURRENT_DIR")

echo "[*] Step 1: Provisioning Local Operating System..."

git clone --depth 1 https://github.com/BrianV1981/aim-agy.git .aim_temp_clone
cd .aim_temp_clone

echo "    [*] Building Engine Virtual Environment..."
./aim-agy_os/setup.sh

echo "[*] Step 2: Scaffolding Sovereign Environment..."

# Clean Sweep (sever OS identity / product dirt before merge)
rm -rf .git/ .github/ .vscode/
rm -rf aim-agy_os/tests/ aim-agy_os/benchmarks/ aim-agy_os/docs/ aim-agy_os/scripts/ aim-agy_os/skills/
# Keep aim-agy_os/link_cli_alias.sh (not under stripped dirs)

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

mkdir -p aim-agy_os/memory_lance
cp -r aim-agy_os/assets/default_lance/* aim-agy_os/memory_lance/

echo "    [*] Initializing Headless OS..."
./aim-agy_os/venv/bin/python3 ./aim-agy_os/.aim_core/aim_cli.py init --headless --persona "$PERSONA"

echo "    [*] Linking Local Alias ($CLI_NAME)..."
bash ./aim-agy_os/link_cli_alias.sh "$CURRENT_DIR" "$CLI_NAME"

echo ""
echo "--- CO-AGENT DEPLOYMENT COMPLETE ---"
echo "Your Sovereign Node ($PERSONA) is installed."
echo "CRITICAL: source your shell RC (see above), then run: $CLI_NAME doctor"
echo ""
