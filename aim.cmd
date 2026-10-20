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

"%VENV_PY%" "%ROOT%\joshua_os\.aim_core\aim_cli.py" %*
set "EXIT_CODE=%ERRORLEVEL%"

if /I not "%CD%"=="%ROOT%" (
    if exist ".git" (
        echo [*] Session complete. Committing state to local ledger...
        git add memory_lance/ 2>nul
        git add AGENTS.md 2>nul
        git commit -m "Auto-commit: Agent session complete" >nul 2>&1
    )
)

exit /b %EXIT_CODE%
