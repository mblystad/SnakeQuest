# SnakeQuest

SnakeQuest is a pygame-based snake game with a gates-and-keys twist, level transitions, and optional audio/visual assets.

## Features
- Main menu with settings (speed + sound toggle) before starting a run.
- Persistent leaderboard (top 5 scores) with name entry.
- Gates & keys mechanic to advance levels after collecting enough food.
- Animated level-loading sequence plus a Level Clear pause between stages.
- HUD for score/level/time with custom font support.
- Optional art and music assets if files are present in the project root.

## Requirements
- Python 3.10+
- pygame-ce (drop-in replacement for pygame)

## Install
```bash
python -m pip install --upgrade pip
python -m pip install pygame-ce
```

## Run
```bash
python main.py
```

## Android Port
- `android_app.py` contains a touch-first Kivy port of the core SnakeQuest loop: menu, settings, HUD, loading animation, replay, and gate/key progression.
- `main.py` now detects Android packaging and starts the Kivy app there, while desktop still runs the existing `pygame-ce` version.
- `buildozer.spec` is included for APK builds.

### Desktop preview of the Android port
```bash
python -m pip install kivy
python android_app.py
```

### Build the APK
As of March 12, 2026, the current Buildozer and Kivy docs still recommend building on Linux/macOS, or on Windows through WSL. Build inside the Linux filesystem, not directly from `/mnt/c/...`.

Official references:
- Buildozer installation: https://buildozer.readthedocs.io/en/latest/installation/
- Buildozer quickstart: https://buildozer.readthedocs.io/en/1.5.0/quickstart.html
- Kivy Android packaging guide: https://kivy.org/doc/stable-2.1.0/guide/packaging-android.html

Typical WSL flow:
```bash
python3 -m pip install --user --upgrade buildozer
buildozer -v android debug
```

The generated APK will be written under `bin/`.

## Controls
- **Main Menu**: `Up/Down` (or `W/S`) to select, `Enter`/`Space` to confirm.
- **Settings**: `Up/Down` to select, `Left/Right` to adjust, `1/2/3` set speed, `Enter` to open leaderboard, `Esc` to return.
- **In-game**: Arrow keys or `W/A/S/D` to move, `Enter` to pause/resume, `Esc` to quit, `N` to skip a level.
- **Sacrifice levels**: `S` to shoot a segment (consumes ammo), use arrow keys to move down while shooting is enabled.
- **Paused**: `Enter` to resume, `Esc` returns to main menu.
- **Level Clear**: `Space` to continue, `Esc` exits.
- **Game Over**: type name (letters/numbers only, max 10 chars) + `Enter` to save score, `Space` plays again, `Esc` exits.

## Leaderboard
- Stored in `leaderboard.json` (auto-created on the first game over).
- If you skip name entry, the game saves `Snake####` automatically.

## Assets (optional)
The game will load these files if they exist in the project root:
- `menubg.png` (menu background)
- `banner.png` (HUD banner)
- `key.png` (key sprite)
- `head.png`, `segment.png`, `tail.png`, `throat.png` (snake parts)
- `theme.wav` (music)
- `Vipnagorgialla_Bd.otf`, `Vipnagorgialla_Rg.otf` (menu/game fonts)

Missing assets fall back to simple shapes/colors.

## Project layout
- `main.py` entry point.
- `game.py`, `snake.py`, `food.py`, `grid.py`, `config.py` core logic and rendering.
