@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Setting it up now...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create the virtual environment. Is Python installed?
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
