# SnakeQuest Local IDE Quickstart

A short, copy/paste-friendly guide to run SnakeQuest in common local IDEs or straight from the terminal.

## 1) Prerequisites
- **Python**: 3.10+ recommended.
- **Dependencies**: `pygame` (game loop & rendering).
- **Optional assets**: Add your own `bg.png`, `key.png`, snake sprites (`head.png`, `segment.png`, `tail.png`), and audio (`start.ogg`, `level1.ogg`-`level3.ogg`, `eat.wav`, `key.wav`, `start.wav`, `snakesplosion.wav`) into `assets/` to override the procedural fallback art and sound.

## 2) Clone and prepare an environment
```bash
# Clone and enter the project
git clone <your-fork-url> SnakeQuest
cd SnakeQuest

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# Install requirements
python -m pip install --upgrade pip
pip install pygame
```

## 3) Run from the terminal
```bash
python main.py
```
Controls: press **Space** on the start screen, then use **Arrow keys** or **WASD** to steer. The HUD shows score, level, timer, and points carried across levels. The playfield is a roomy 36x24 grid to fit the new Tetris-inspired wall layouts that ramp up in complexity as you advance through levels.

## 4) VS Code setup
1. **Open folder**: File → Open Folder… and choose the repo.
2. **Interpreter**: Command Palette → "Python: Select Interpreter" → pick `.venv` (or create it via the steps above).
3. **Debug config**: Run and Debug → "create a launch.json" → Python → replace the generated entry with:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "SnakeQuest",
         "type": "python",
         "request": "launch",
         "program": "${workspaceFolder}/main.py",
         "console": "integratedTerminal",
         "cwd": "${workspaceFolder}"
       }
     ]
   }
   ```
4. **Start**: press **F5**. The game launches in the integrated terminal with live stdout/stderr.

## 5) PyCharm setup
1. **Open project**: Open the repo directory.
2. **Interpreter**: When prompted, create/attach a virtualenv (File → Settings → Project → Python Interpreter). Install `pygame` if PyCharm offers to auto-install requirements.
3. **Run configuration**: Run → Edit Configurations… → **+** → Python, then set:
   - **Script path**: `<project-root>/main.py`
   - **Working directory**: `<project-root>`
   - **Interpreter**: the venv from step 2
4. **Run/Debug**: click the green Run or Debug arrow to start the game.

## 6) Troubleshooting
- If you see `ModuleNotFoundError: pygame`, confirm the virtual environment is active and rerun `pip install pygame`.
- If the window opens off-screen or is too large, lower `SCREEN_WIDTH`/`SCREEN_HEIGHT` in `config.py` (defaults are 720x480 for the expanded Tetris puzzle arenas).
- Missing art files are fine—the game falls back to neon placeholders. Drop custom PNGs into `assets/` to customize visuals.
- Missing audio is also fine. Add the optional files listed above to hear music on the start screen, rotating in-level tracks every 5 levels, and sound effects for eating, level gates, starting, and the snakesplosion on death.
- On macOS, allow the Python app to accept keyboard input if macOS prompts for accessibility permissions.

Enjoy hacking on SnakeQuest!
