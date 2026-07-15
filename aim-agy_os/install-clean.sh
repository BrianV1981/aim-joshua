#!/bin/bash
# A.I.M. Exoskeleton Installer (Clean Project Wrapper)
# curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-agy/main/aim-agy_os/install-clean.sh | bash

set -e
echo "--- A.I.M. CLEAN INSTALLER ---"

CURRENT_DIR=$(pwd)
CLI_NAME=$(basename "$CURRENT_DIR")

echo "[*] Step 1: Provisioning Local Operating System..."

# Clone the engine directly into a temporary hidden folder to avoid empty directory conflicts
# Hardcoded to fix/issue-52 for testing. Will revert to main later.
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

# Generate Ghost Folder Explainers
mkdir -p aim-agy_os/foundry aim-agy_os/planning-artifacts aim-agy_os/workspace
echo "# A.I.M. Foundry
Drop external raw PDFs, documents, or foreign repositories here before compiling them into \`.parquet\` cartridges via the \`aim bake\` command." > aim-agy_os/foundry/README.md

echo "# A.I.M. Planning Artifacts
Use this directory as a scratchpad for agents to generate architectural roadmaps, design documents, or task breakdowns before committing to code." > aim-agy_os/planning-artifacts/README.md

echo "# A.I.M. Workspace
This directory contains isolated Git Worktrees. When you type \`aim fix <id>\`, A.I.M. checks out a clean sandbox here to prevent you from working directly on the \`main\` branch." > aim-agy_os/workspace/README.md

echo "    [*] Linking Local Alias ($CLI_NAME)..."
bash ./aim-agy_os/link_cli_alias.sh "$CURRENT_DIR" "$CLI_NAME"

echo ""
echo "--- INSTALLATION COMPLETE ---"
echo "A.I.M. is installed with default settings. To customize your agent's personality and project goals, run:"
echo "  $CLI_NAME init"
echo ""
