# A.I.M. Clean OS Installer for Windows 10/11 (PowerShell)
# Usage:
#   mkdir my-project; cd my-project
#   irm https://raw.githubusercontent.com/BrianV1981/aim-joshua/main/joshua_os/install.ps1 | iex

$ErrorActionPreference = "Stop"
Write-Host "--- J.O.S.H.U.A. CLEAN INSTALLER (WINDOWS) ---"

$CurrentDir = (Get-Location).Path
$HomePath = [Environment]::GetFolderPath("UserProfile")
$DriveRoot = [System.IO.Path]::GetPathRoot($CurrentDir)

if (($CurrentDir.TrimEnd('\') -ieq $HomePath.TrimEnd('\')) -or ($CurrentDir.TrimEnd('\') -ieq $DriveRoot.TrimEnd('\'))) {
    Write-Error "[ERROR] Refusing to install directly in $CurrentDir. Create and cd into a dedicated project directory first."
    exit 1
}

function Resolve-JoshuaPython {
    foreach ($candidate in @(@("py", "-3"), @("python"), @("python3"))) {
        $exe = $candidate[0]
        $prefixArgs = if ($candidate.Length -gt 1) { $candidate[1..($candidate.Length - 1)] } else { @() }
        if (Get-Command $exe -ErrorAction SilentlyContinue) {
            & $exe @prefixArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                return ,$candidate
            }
        }
    }
    throw "[ERROR] Python 3.10+ is required on PATH. Install Python 3.10+ from python.org and retry."
}

$PyCmd = Resolve-JoshuaPython
$PyExe = $PyCmd[0]
$PyArgs = if ($PyCmd.Length -gt 1) { $PyCmd[1..($PyCmd.Length - 1)] } else { @() }

$TempClone = Join-Path $CurrentDir ".aim_temp_clone"
try {
    if (Test-Path $TempClone) { Remove-Item -Recurse -Force $TempClone }
    git clone --depth 1 https://github.com/BrianV1981/aim-joshua.git $TempClone
    if ($LASTEXITCODE -ne 0) { throw "git clone failed." }
    & $PyExe @PyArgs (Join-Path $TempClone "joshua_os\.aim_core\bootstrap_install.py") --mode clean --source $TempClone --target $CurrentDir
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    if (Test-Path $TempClone) { Remove-Item -Recurse -Force $TempClone -ErrorAction SilentlyContinue }
}
