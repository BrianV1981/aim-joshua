@echo off
setlocal
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
if not defined NODE_OPTIONS set "NODE_OPTIONS=--max-old-space-size=8192"

set "VENV_PY=%ROOT%\joshua_os\venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    if exist "%ROOT%\..\..\joshua_os\venv\Scripts\python.exe" (
        set "VENV_PY=%ROOT%\..\..\joshua_os\venv\Scripts\python.exe"
    ) else (
        set "VENV_PY=python"
    )
)

(goto) 2>nul & "%VENV_PY%" "%ROOT%\joshua_os\.aim_core\aim_cli.py" %*
