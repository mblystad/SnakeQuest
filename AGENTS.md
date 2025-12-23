# agents.md — SnakeQuest (pygame-ce)

This repository is a small, single-folder pygame-ce project: a Snake clone with **menus**, **settings (speed + sound)**, **HUD**, and a **gates & keys** level progression mechanic. It also supports **optional assets** (images/fonts/audio) that must never be required to run.

This file is instructions for coding agents (Copilot, Claude Code, Cursor, etc.). If you are an agent, follow these rules before editing anything.

---

## Non‑negotiables (must always hold)

- **Runs with only `pygame-ce` installed** (`python main.py`).
- **Missing assets never crash the game** — fall back to primitive drawing + default fonts.
- **Grid movement remains discrete** (one cell per tick), with **no instant 180° reversal**.
- **Transitions remain reachable**:
  - Menu → settings → start game
  - Level loading animation → playing
  - Level clear pause → next level
  - Game over → return to menu
- **No new runtime dependencies** unless explicitly requested.

Repo overview (current files in the root):
- `main.py` (entry point)
- `game.py`, `snake.py`, `food.py`, `grid.py`, `config.py` (core logic)
- Optional assets present in repo: `menubg.png`, `banner.png`, `head.png`, `segment.png`, `tail.png`, `throat.png`, `theme.wav`, `Vipnagorgialla_Bd.otf` citeturn1view0

---

## How to work on this repo (agent workflow)

1. **Read first**: skim `README.md`, then open `main.py` → `game.py` to find the active loop and state flow.
2. **Make small, safe changes**:
   - One feature / bug fix per PR.
   - Prefer local refactors over “rewrite everything”.
3. **Manual smoke test after each change**:
   - Start game, move, eat food
   - Change speed in settings and verify tick rate changes
   - Toggle sound and verify silence / music behavior
   - Trigger level progression (gate/key)
   - Trigger game over and return to menu

---

## Project mental model

Even if internal names differ, treat the code as layered:

### 1) App / Scene orchestration (`main.py`)
Owns:
- pygame init + display
- main loop, event pump
- scene/state switching (menu/settings/game)

Rules:
- Call `pygame.event.get()` **once per frame** at the top level, then dispatch to current scene.
- Keep quitting behavior consistent (`Esc` or window close).

### 2) Run gameplay loop (`game.py`)
Owns:
- playing vs loading vs level_clear vs game_over
- score/level/time HUD updates
- gate/key thresholds and transitions

Rules:
- Gameplay updates should be **tick-based** (fixed step), not per-frame pixel movement.
- Level transitions should be **explicit** and easy to reason about (avoid “boolean soup”).

### 3) Entities (`snake.py`, `food.py`)
Own:
- grid positions, collision checks, respawn rules
- drawing (sprite if loaded, else shapes)

Rules:
- Use **grid coordinates** `(x, y)` as the source of truth; convert to pixel Rects only in render.
- Spawns must avoid occupied tiles (snake body, walls, gates).

### 4) Grid helpers (`grid.py`) + constants (`config.py`)
Own:
- board size, cell size
- colors and asset filenames
- any helper for safe asset loading (recommended)

---

## Timing & determinism (recommended pattern)

Snake games are easiest to keep stable with a **fixed-step accumulator**:

- `frame_ms = clock.tick(fps_cap)`
- `accumulator += frame_ms`
- while `accumulator >= tick_ms`:
  - update snake + collisions + pickups
  - `accumulator -= tick_ms`
- render every frame

Why:
- Avoids machine-dependent speed variance
- Keeps collisions consistent
- Makes “speed settings” a single knob: `tick_ms` (or moves/sec)

Avoid mixing dt-based interpolation with grid steps.

---

## Assets policy (must be robust)

The repo includes some assets, but the game must remain playable without any of them. citeturn1view0

### Safe-load rules
- Every load must be wrapped:
  - `try/except (FileNotFoundError, pygame.error)`
- Images:
  - call `convert()`/`convert_alpha()` after display init
  - scale once and cache (never scale every frame)
- Fonts:
  - if custom font file missing, use `pygame.font.Font(None, size)`
- Audio:
  - if mixer init fails, force sound off and continue silently

### Rendering fallback
When sprite missing:
- Snake segments: colored rects
- Food/key: circles or rects
- Gate: line/rect with distinct color

---

## Input rules (avoid subtle bugs)

- Use `KEYDOWN` events for menu navigation and direction changes.
- Prevent instant reversal:
  - If moving left, ignore right, etc.
- Allow only one direction change per tick (or per frame) to prevent “double-turn” glitches.

---

## Gates & keys mechanic (guard rails)

Because this is the unique twist, do not “simplify away” these behaviors:

- There is a **collection requirement** (food count and/or key pickup).
- There is a **gate** whose state changes (locked → open).
- **Level transition** occurs only when conditions are met and the snake reaches the gate.
- Level clear and loading animation states should not be skipped unintentionally.

If you refactor this logic:
- Centralize it in one place (e.g., `GameState.update_progression()`).
- Add a small pure function for the rule:
  - `can_open_gate(collected_food, has_key, required_food) -> bool`

---

## Code style conventions for this repo

- Python 3.10+
- Keep code readable over clever:
  - clear names, minimal nesting, short helper functions
- Prefer pure functions for logic that can be unit-tested.
- Type hints are welcome where they clarify interfaces (grid coords, settings, state transitions).

---

## Testing (optional, lightweight)

No external frameworks required.

If adding tests:
- Use `unittest`
- Keep tests display-free (no pygame window needed)
- Focus on logic:
  - spawn validity
  - reversal prevention
  - progression rules (gate/key)
  - collision detection

---

## Common pitfalls (don’t introduce)

- **Spawn-on-snake** bugs (always compute occupied cells)
- **Per-frame scaling** (cache scaled surfaces)
- **Soft-lock transitions** (make every state exit path explicit)
- **Audio crash** on machines without mixer device
- **Multiple event pumps** in nested modules

---

## Safe “modernizations” you may implement (if asked)

These are good improvements that keep the game simple:

1. **Explicit state machine**
   - `MENU`, `SETTINGS`, `LOADING`, `PLAYING`, `LEVEL_CLEAR`, `GAME_OVER`
   - each has `handle_event / update / render`

2. **Settings dataclass**
   - `Settings(speed: int, sound: bool)`
   - passed into `Game` rather than global mutation

3. **Centralized asset registry**
   - `Assets` loads once, provides `get_image('head')` etc.
   - always returns `None` if missing, never raises

4. **Seedable RNG (optional)**
   - CLI `--seed` for reproducible spawns
   - defaults to random

---

## Definition of done

A change is “done” when:
- `python main.py` runs on a clean machine with only `pygame-ce`
- menus/settings work
- movement is stable and grid-based
- levels progress correctly via gate/key rules
- missing assets do not crash and have visible fallbacks
