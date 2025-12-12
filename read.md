# SnakeQuest IDE Setup Guide

This guide covers running the game locally in common IDEs (PyCharm, VS Code) and from the command line.

## Requirements
- Python 3.10+ (recommended).
- `pygame` installed in your environment:
  ```bash
  python -m pip install --upgrade pip
  pip install pygame
  ```
- Optional assets in `assets/` for richer visuals (e.g., `bg.png`, `key.png`); the game will fall back to procedural graphics when files are missing.

## Project layout
- `main.py` — entry point that launches the `Game` loop.
- `game.py`, `snake.py`, `food.py`, `grid.py`, `config.py` — game logic, rendering, and configuration.
- `assets/` — optional art used when present.

## Running from the command line
```bash
python main.py
```
Press **Space** on the start screen to begin. Use **Arrow keys** or **WASD** to move. The HUD shows score, level, and elapsed time.

## VS Code setup
1. Open the folder in VS Code.
2. Create or select a Python interpreter (Command Palette → "Python: Select Interpreter"). A venv in `.venv/` keeps dependencies isolated:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   pip install pygame
   ```
3. Add a minimal debug configuration (Run and Debug → "create a launch.json" → Python) similar to:
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
4. Start debugging with **F5**; VS Code will launch `main.py` in the integrated terminal.

## PyCharm setup
1. Open the project directory in PyCharm.
2. When prompted, create a new virtual environment for the project and install dependencies:
   ```bash
   pip install pygame
   ```
3. Create a Run/Debug Configuration:
   - Script path: `<project root>/main.py`
   - Working directory: `<project root>`
   - Python interpreter: the venv created in step 2
4. Click **Run** or **Debug** to start the game. PyCharm will display stdout/stderr in its Run tool window.

## Tips
- If the window opens off-screen or at an unexpected size, adjust `SCREEN_WIDTH`/`SCREEN_HEIGHT` in `config.py`.
- When adding new art, keep file names consistent; missing files automatically fall back to procedural sprites.
- Use the built-in timer and score display to verify timing and level progression during testing.
