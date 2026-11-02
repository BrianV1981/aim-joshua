# A.I.M. Sovereign Co-Agent Installer for Windows 10/11 (PowerShell)
# Usage:
#   mkdir C:\aim-agents\my-agent; cd C:\aim-agents\my-agent
#   & ([scriptblock]::Create((irm https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install-agent.ps1))) python-developer

param(
    [Parameter(Position = 0)]
    [string]$PersonaName = ""
)

$ErrorActionPreference = "Stop"
Write-Host "--- J.O.S.H.U.A. SOVEREIGN CO-AGENT INSTALLER (WINDOWS) ---"

$CurrentDir = (Get-Location).Path
$HomePath = [Environment]::GetFolderPath("UserProfile")
$DriveRoot = [System.IO.Path]::GetPathRoot($CurrentDir)

if (($CurrentDir.TrimEnd('\') -ieq $HomePath.TrimEnd('\')) -or ($CurrentDir.TrimEnd('\') -ieq $DriveRoot.TrimEnd('\'))) {
    Write-Error "[ERROR] Refusing to install directly in $CurrentDir. Create and cd into a dedicated co-agent directory first."
    exit 1
}

function Resolve-JoshuaPython {
    $probe = "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
    if (Get-Command "py" -ErrorAction SilentlyContinue) {
        $null | & py -3 -c $probe 2>$null
        if ($LASTEXITCODE -eq 0) {
            return "py-3"
        }
    }
    foreach ($exe in @("python", "python3")) {
        if (Get-Command $exe -ErrorAction SilentlyContinue) {
            $null | & $exe -c $probe 2>$null
            if ($LASTEXITCODE -eq 0) {
                return $exe
            }
        }
    }
    throw "[ERROR] Python 3.10+ is required on PATH."
}

$PySpec = Resolve-JoshuaPython
$TempClone = Join-Path $CurrentDir ".aim_temp_clone"
try {
    if ($env:AIM_INSTALL_SOURCE -and (Test-Path (Join-Path $env:AIM_INSTALL_SOURCE "joshua_os\.aim_core\bootstrap_install.py"))) {
        $SourceRoot = $env:AIM_INSTALL_SOURCE
    } else {
        if (Test-Path $TempClone) { Remove-Item -Recurse -Force $TempClone }
        git clone --depth 1 https://github.com/BrianV1981/aim-joshua.git $TempClone
        if ($LASTEXITCODE -ne 0) { throw "git clone failed." }
        $SourceRoot = $TempClone
    }
    $BootstrapScript = Join-Path $SourceRoot "joshua_os\.aim_core\bootstrap_install.py"
    if ($PersonaName) {
        if ($PySpec -eq "py-3") {
            & py -3 $BootstrapScript --mode agent --source $SourceRoot --target $CurrentDir --persona $PersonaName
        } else {
            & $PySpec $BootstrapScript --mode agent --source $SourceRoot --target $CurrentDir --persona $PersonaName
        }
    } else {
        if ($PySpec -eq "py-3") {
            & py -3 $BootstrapScript --mode agent --source $SourceRoot --target $CurrentDir
        } else {
            & $PySpec $BootstrapScript --mode agent --source $SourceRoot --target $CurrentDir
        }
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    if (Test-Path $TempClone) { Remove-Item -Recurse -Force $TempClone -ErrorAction SilentlyContinue }
}
