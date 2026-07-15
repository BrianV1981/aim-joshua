#!/bin/bash
# A.I.M. Core Contributor Installer
# curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-agy/main/aim-agy_os/install-core.sh | bash

set -e
echo "--- A.I.M. CORE CONTRIBUTOR INSTALLER ---"

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

shopt -s dotglob
cp -a * ../
cd ..
rm -rf .aim_temp_clone
shopt -u dotglob

# Base OS Provisioning (Moving the pre-baked DB to the active layer)
mkdir -p aim-agy_os/memory_lance
cp -r aim-agy_os/assets/default_lance/* aim-agy_os/memory_lance/

echo "    [*] Linking Local Alias ($CLI_NAME)..."
bash ./aim-agy_os/link_cli_alias.sh "$CURRENT_DIR" "$CLI_NAME"

echo ""
echo "--- INSTALLATION COMPLETE ---"
echo "You are a Core Contributor. The .git history and developer folders (tests/, benchmarks/) have been preserved."
echo "To set up your identity, run:"
echo "  $CLI_NAME init"
echo ""
echo ""