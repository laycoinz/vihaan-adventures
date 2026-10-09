@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Setting it up now...
    set "PYCMD=python"
    where python >nul 2>nul || set "PYCMD=py -3"
    %PYCMD% -m venv .venv
    if errorlevel 1 (
        echo Failed to create the virtual environment. Is Python installed and on PATH?
        echo Try installing Python 3.11+ from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

".venv\Scripts\python.exe" game.py %*
if errorlevel 1 (
    echo.
    echo The game exited with an error.
    pause
)
endlocal
