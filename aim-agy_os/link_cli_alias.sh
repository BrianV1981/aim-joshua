#!/usr/bin/env bash
# Shared by install-clean / install-agent / install-core (and retrofit for existing projects).
# Links a host-project shell alias → nested aim-agy_os CLI + optional ./aim wrapper.
#
# Usage:
#   bash aim-agy_os/link_cli_alias.sh [PROJECT_ROOT] [CLI_NAME]
# Defaults: PROJECT_ROOT=cwd, CLI_NAME=basename(PROJECT_ROOT)

set -euo pipefail

PROJECT_ROOT="${1:-$(pwd)}"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
CLI_NAME="${2:-$(basename "$PROJECT_ROOT")}"

VENV_PY="$PROJECT_ROOT/aim-agy_os/venv/bin/python3"
CLI_PY="$PROJECT_ROOT/aim-agy_os/.aim_core/aim_cli.py"

if [[ ! -f "$CLI_PY" ]]; then
  echo "[ERROR] link_cli_alias: aim_cli.py not found at $CLI_PY" >&2
  exit 1
fi
if [[ ! -f "$VENV_PY" ]]; then
  echo "[WARN] link_cli_alias: venv python not found at $VENV_PY (alias still written)"
fi

RC_FILE="$HOME/.bashrc"
if [[ -f "$HOME/.zshrc" ]]; then
  RC_FILE="$HOME/.zshrc"
fi

SED_ALIAS="alias ${CLI_NAME}='NODE_OPTIONS=\"--max-old-space-size=8192\" ${VENV_PY} ${CLI_PY}'"

if [[ ! -f "$RC_FILE" ]]; then
  touch "$RC_FILE"
fi

if ! grep -q "alias ${CLI_NAME}=" "$RC_FILE" 2>/dev/null; then
  {
    echo ""
    echo "# A.I.M. CLI — ${CLI_NAME} (project: ${PROJECT_ROOT})"
    echo "$SED_ALIAS"
  } >> "$RC_FILE"
  echo "    [SUCCESS] Alias '${CLI_NAME}' added to $RC_FILE"
else
  sed -i "s|alias ${CLI_NAME}=.*|${SED_ALIAS}|g" "$RC_FILE"
  echo "    [OK] Alias '${CLI_NAME}' already exists (updated path in $RC_FILE)."
fi

WRAPPER="$PROJECT_ROOT/aim"
if [[ ! -f "$WRAPPER" ]]; then
  cat > "$WRAPPER" << 'WRAP'
#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")" && pwd)"
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=8192}"
exec "$ROOT/aim-agy_os/venv/bin/python3" "$ROOT/aim-agy_os/.aim_core/aim_cli.py" "$@"
WRAP
  chmod +x "$WRAPPER"
  echo "    [SUCCESS] Local ./aim wrapper written"
fi

echo "    [ACTION] Load the alias:  source $RC_FILE"
echo "    [ACTION] Then run:        ${CLI_NAME} doctor"
