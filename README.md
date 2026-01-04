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
