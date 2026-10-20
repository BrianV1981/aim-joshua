#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $env:NODE_OPTIONS) {
    $env:NODE_OPTIONS = "--max-old-space-size=8192"
}

$Candidates = @(
    (Join-Path $ROOT "joshua_os\venv\Scripts\python.exe"),
    (Join-Path $ROOT "..\..\joshua_os\venv\Scripts\python.exe"),
    (Join-Path $ROOT "joshua_os/venv/bin/python3"),
    (Join-Path $ROOT "../../joshua_os/venv/bin/python3")
)

$VENV_PY = $null
foreach ($cand in $Candidates) {
    if (Test-Path -LiteralPath $cand) {
        $VENV_PY = (Resolve-Path -LiteralPath $cand).Path
        break
    }
}
if (-not $VENV_PY) {
    $VENV_PY = "python"
}

$CLI_SCRIPT = Join-Path $ROOT "joshua_os\.aim_core\aim_cli.py"
& $VENV_PY $CLI_SCRIPT @args
$EXIT_CODE = $LASTEXITCODE

if (($PWD.Path -ne $ROOT) -and (Test-Path -LiteralPath ".git")) {
    Write-Host "[*] Session complete. Committing state to local ledger..."
    git add memory_lance/ 2>$null
    git add AGENTS.md 2>$null
    git commit -m "Auto-commit: Agent session complete" *>$null
}

exit $EXIT_CODE
