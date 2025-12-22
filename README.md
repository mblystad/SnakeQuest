# SnakeQuest

SnakeQuest is a pygame-based snake game with a gates-and-keys twist, level transitions, and optional audio/visual assets.

## Features
- Classic snake movement with speed selection before each run.
- Gates & keys mechanic to advance levels after collecting enough food.
- Animated level-loading sequence and HUD for score/level/time.
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
- **Start / Menu**: `Space` to start, `Up/Down` (or `W/S`) to change speed, `1/2/3` to pick speed directly, `Enter` to start.
- **In-game**: Arrow keys or `W/A/S/D` to move, `Esc` to quit.
- **Game Over**: `Space` returns to the speed menu, `Esc` exits.

## Assets (optional)
The game will load these files if they exist in the project root:
- `menubg.png` (menu background)
- `banner.png` (HUD banner)
- `key.png` (key sprite)
- `head.png`, `segment.png`, `tail.png`, `throat.png` (snake parts)
- `bg.mp3` (music)

Missing assets fall back to simple shapes/colors.

## Project layout
- `main.py` entry point.
- `game.py`, `snake.py`, `food.py`, `grid.py`, `config.py` core logic and rendering.
