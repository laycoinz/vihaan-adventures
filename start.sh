#!/usr/bin/env sh
# Launcher for macOS / Linux. Creates the virtual environment if needed,
# installs the dependencies, then starts the game.
set -e
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
    echo "Virtual environment not found. Setting it up now..."
    python3 -m venv .venv
    .venv/bin/python -m pip install --upgrade pip
    .venv/bin/python -m pip install -r requirements.txt
fi

.venv/bin/python game.py "$@"
