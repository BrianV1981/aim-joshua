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
    throw "[ERROR] Python 3.10+ is required on PATH. Install Python 3.10+ from python.org and retry."
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
    if ($PySpec -eq "py-3") {
        & py -3 $BootstrapScript --mode clean --source $SourceRoot --target $CurrentDir
    } else {
        & $PySpec $BootstrapScript --mode clean --source $SourceRoot --target $CurrentDir
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    if (Test-Path $TempClone) { Remove-Item -Recurse -Force $TempClone -ErrorAction SilentlyContinue }
}
