# Vihaan Adventures

A Mario-style 2D platformer built with **Python** and **pygame**. Play as **Vihaan**
across **11 levels** - the six stages of World 1 and the five cloud-themed stages of
World 2. Stomp enemies, grab coins, store power-ups, parry the bosses, and reach the end
of each stage.

Everything in the game - character art, bosses, sound effects and music - is drawn or
synthesized in code. No external asset packs, and nothing copyrighted.

---

## Requirements

- **Python 3.11 or newer** (developed and tested on Python 3.14) - <https://www.python.org/downloads/>
- **pip** (comes with Python)
- A desktop environment with a display (the game opens a window)

The project's dependencies are pinned in `requirements.txt`:

```
pygame-ce==2.5.8
numpy==2.5.3
```

> These are installed **inside the project's own `.venv`** so nothing is added to your
> global Python. The `.venv` folder is **not** committed to git (see `.gitignore`) - it is
> created for you automatically the first time you run the launcher, or you can make one
> yourself with the manual steps below.

---

## Quick start

### Windows

The easiest way is to **double-click `start.bat`**. The first time you run it, it creates
the `.venv` folder, installs the dependencies, and launches the game. Every run after that
just launches the game.

You can also run it from **PowerShell** or **Command Prompt** - open a terminal in this
folder and type:

```bat
start.bat
```

> If double-clicking does nothing (the window flashes and closes), open the folder in a
> terminal and run `start.bat` there so you can read the error message.

### macOS / Linux

```sh
./start.sh
```

(If it says permission denied, run `chmod +x start.sh` once first.) This does the same as
`start.bat`: it creates `.venv`, installs the dependencies, then launches the game.

---

## Manual setup

If you would rather set up the virtual environment yourself, follow the section for your
operating system.

### Windows

Open **PowerShell** or **Command Prompt** in the project folder and run:

```bat
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python game.py
```

If `python` isn't recognised, use the Windows Python launcher `py` instead:

```bat
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python game.py
```

Optional - **activate** the environment so plain `python` and `pip` use it:

- **PowerShell:**  `.venv\Scripts\Activate.ps1`
  (if it's blocked, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` once,
  then try again)
- **Command Prompt:**  `.venv\Scripts\activate.bat`

When it's active your prompt shows `(.venv)`, and you can just run `python game.py`. Type
`deactivate` to leave it.

### macOS / Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python game.py
```

To activate instead: `source .venv/bin/activate`, then run `python game.py`.

---

> On Windows always launch the game with the **`.venv` interpreter**
> (`.venv\Scripts\python game.py`); on macOS/Linux use `.venv/bin/python game.py`. Running
> plain `python game.py` with your global Python will only work if pygame and numpy happen
> to be installed globally - which is exactly what the venv exists to avoid.

---

## First run

The game synthesizes its music and sound effects the first time it starts (they are written
into the `assets/` folder). This can take a few seconds on the very first launch; after that
startup is instant. The `assets/` folder is intentionally not committed - it is rebuilt
automatically whenever it is missing.

---

## Controls

**Keyboard**

| Action | Keys |
| --- | --- |
| Move | Arrow keys or `A` / `D` |
| Jump | `Space` (also `W` / `Up` / `Z`) |
| Run / throw ramen | `Shift` (also `X`) |
| Recall stored mushroom | `E` |
| Pause | `P` (or `Esc` during a level) |
| Mute | `M` |
| Quit | `Esc` on the title screen, or close the window |

**Gamepad** (Xbox / PlayStation layout; the pad is detected automatically)

| Action | Button |
| --- | --- |
| Move | Left stick or D-pad |
| Jump | `A` (also `B`) |
| Run / throw ramen | `X` (also `LB`) |
| Recall stored mushroom | `RB` |
| Confirm / start | `Start` |
| Pause / back | `Back` / `Select` |
| Mute | `Y` |

A controller can be plugged in at any time - the game picks it up on the fly.

---

## Project structure

```
.
├── game.py             # The whole game (levels, entities, rendering, input)
├── generate_audio.py   # Synthesizes the music and sound effects into assets/
├── requirements.txt    # Pinned dependencies (pygame-ce, numpy)
├── start.bat           # Windows launcher (auto-creates .venv and runs)
├── start.sh            # macOS / Linux launcher (same, for POSIX shells)
├── .gitignore
├── assets/             # Generated .wav files (created on first run, not committed)
└── .venv/              # Your local virtual environment (not committed)
```

Handy extras:

- `generate_audio.py` can be run on its own to (re)generate the audio:
  `.venv\Scripts\python generate_audio.py`
- `game.py --selftest` runs a short headless simulation of every level - useful to check the
  install works without opening a window.

---

## Troubleshooting

**Windows: "python is not recognized as an internal or external command"**
Python isn't on your `PATH`. Either:

- Re-run the Python installer, choose **Modify**, and tick **"Add Python to PATH"**; or
- Use the Windows launcher `py` instead of `python` (e.g. `py -3 -m venv .venv`); or
- Check **Settings → Apps → Advanced app settings → App execution aliases** and make sure
  the `python.exe` / `python3.exe` aliases are turned on.

You can confirm what Windows sees with `where python` (or `py --version`).

**macOS / Linux: "command not found: python3"**
Install Python 3.11+ with your package manager (e.g. `brew install python` on macOS, or
`sudo apt install python3 python3-venv` on Debian/Ubuntu), then recreate the venv.

**`pip install` fails on an old Python**
The pinned `numpy` needs a recent Python. Install Python 3.11+ and recreate the venv
(delete the `.venv` folder, then run the launcher again).

**No sound / the game is silent**
That usually means no audio device is available. The game still runs - it just turns audio
off automatically. Check your system output device and that nothing else is using it
exclusively.

**The controller isn't detected**
Plug it in before or during play and press a button. If it still doesn't work, close and
reopen the game; some pads need a fresh start to be registered.

**The window doesn't open**
The game needs a graphical desktop session. It will not run over a plain SSH/headless shell
without a virtual display.

**Start over cleanly**
Delete the `.venv` folder and run `start.bat` / `start.sh` again - it will rebuild the
environment from scratch.

- **Windows (PowerShell):** `Remove-Item -Recurse -Force .venv`
- **Windows (cmd):** `rmdir /s /q .venv`
- **macOS / Linux:** `rm -rf .venv`

---

## Notes

- All artwork and audio are generated in code; there are no third-party or copyrighted assets.
- The `.venv/` folder and the generated `assets/` audio are excluded from git via `.gitignore`.
  Clone the repo, run the launcher, and everything you need is built for you.
