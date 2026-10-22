#!/bin/bash
# A.I.M. Sovereign Co-Agent Installer (headless)
# curl -fsSL https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install-agent.sh | bash -s python-developer

set -e
echo "--- J.O.S.H.U.A. SOVEREIGN CO-AGENT INSTALLER ---"

CURRENT_DIR=$(pwd)
CLI_NAME=$(basename "$CURRENT_DIR")
PERSONA_NAME="${1:-}"

if [ "$CURRENT_DIR" = "$HOME" ] || [ "$CURRENT_DIR" = "/" ]; then
    echo "[ERROR] Refusing to install directly in $CURRENT_DIR."
    echo "Please create and cd into a dedicated project or co-agent directory first:"
    echo "  mkdir -p ~/aim-agents/my-agent && cd ~/aim-agents/my-agent"
    exit 1
fi

echo "[*] Step 1: Provisioning Local Operating System..."

git clone --depth 1 https://github.com/BrianV1981/aim-joshua.git .aim_temp_clone
cd .aim_temp_clone

echo "    [*] Building Engine Virtual Environment..."
./joshua_os/setup.sh

echo "[*] Step 2: Scaffolding Sovereign Environment..."

# Clean Sweep (sever OS identity / product dirt before merge)
rm -rf .git/ .github/ .vscode/ memory-wiki/ joshua_os/memory-wiki/ workspace/
rm -f HANDOFF.md
rm -rf joshua_os/tests/ joshua_os/benchmarks/ joshua_os/docs/ joshua_os/skills/
# Keep scripts/ for agy trust wrapper installer; strip bulk only if present
# (link_cli_alias + install_agy_trust_wrapper are required for folder-trust)

cp -a joshua_os ../

if [ -n "$PERSONA_NAME" ]; then
    echo "    [*] Resolving Co-Agent Persona Blueprint: $PERSONA_NAME..."
    if [ -f "$HOME/aim-coagents/blueprints/$PERSONA_NAME/AGENTS.md" ]; then
        cp -n "$HOME/aim-coagents/blueprints/$PERSONA_NAME/AGENTS.md" ../AGENTS.md 2>/dev/null || true
        [ -f "$HOME/aim-coagents/blueprints/$PERSONA_NAME/TOOLS.md" ] && cp -n "$HOME/aim-coagents/blueprints/$PERSONA_NAME/TOOLS.md" ../TOOLS.md 2>/dev/null || true
    elif curl -fsSL "https://raw.githubusercontent.com/BrianV1981/aim-coagents/main/blueprints/$PERSONA_NAME/AGENTS.md" -o .persona_AGENTS.md 2>/dev/null && [ "$(wc -l < .persona_AGENTS.md)" -ge 15 ]; then
        cp -n .persona_AGENTS.md ../AGENTS.md 2>/dev/null || true
        curl -fsSL "https://raw.githubusercontent.com/BrianV1981/aim-coagents/main/blueprints/$PERSONA_NAME/TOOLS.md" -o .persona_TOOLS.md 2>/dev/null && cp -n .persona_TOOLS.md ../TOOLS.md 2>/dev/null || true
    else
        echo "    [!] Persona '$PERSONA_NAME' not found in aim-coagents; falling back to default J.O.S.H.U.A. AGENTS.md blueprint."
    fi
fi

cp -n AGENTS.md ../ 2>/dev/null || true
cp -n TOOLS.md ../ 2>/dev/null || true
cp -n aim.ps1 ../ 2>/dev/null || true
cp -n aim.cmd ../ 2>/dev/null || true

cd ..
rm -rf .aim_temp_clone

if [ ! -d ".git" ]; then
    git init
fi

# Ensure J.O.S.H.U.A. OS exoskeleton is gitignored in consumer projects
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

[ ! -f README.md ] && echo "# My JOSHUA Project" > README.md

mkdir -p joshua_os/memory_lance
cp -r joshua_os/assets/default_lance/* joshua_os/memory_lance/

echo "    [*] Registering MCP Server..."
python3 ./joshua_os/.aim_core/register_mcp.py

echo "    [*] Linking Local Alias ($CLI_NAME)..."
bash ./joshua_os/link_cli_alias.sh "$CURRENT_DIR" "$CLI_NAME"

echo "    [*] AGY folder-trust (exact cwd registration for all future spawns)..."
# Preserve trust helper even if scripts/ was stripped earlier in this installer
if [[ -f ./joshua_os/.aim_core/agy_workspace_trust.py ]]; then
  mkdir -p "$HOME/.local/share/aim-joshua"
  cp -a ./joshua_os/.aim_core/agy_workspace_trust.py \
    "$HOME/.local/share/aim-joshua/agy_workspace_trust.py"
  # Prefer full wrapper installer if scripts survived; else minimal trust of project root
  if [[ -f ./joshua_os/scripts/install_agy_trust_wrapper.sh ]]; then
    bash ./joshua_os/scripts/install_agy_trust_wrapper.sh || true
  fi
  PYTHONPATH="./joshua_os/.aim_core${PYTHONPATH:+:$PYTHONPATH}" \
    python3 ./joshua_os/.aim_core/agy_workspace_trust.py "$CURRENT_DIR" || true
fi

echo ""
echo "--- CO-AGENT DEPLOYMENT COMPLETE ---"
echo "Your Sovereign Node is installed with the default AGENTS.md blueprint."
echo "CRITICAL: source your shell RC (see above), then run: $CLI_NAME doctor"
echo "NOTE: New folders still need exact trust — host 'agy' wrapper pre-trusts pwd on each launch."
echo ""
