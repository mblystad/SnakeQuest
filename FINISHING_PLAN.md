# SnakeQuest Finishing Plan

## Current Shape
- The active game is a desktop `pygame-ce` project launched with `python main.py`.
- The Android/Kivy experiment has been removed from the active runtime so the repo has one source of truth.
- Existing level groups are normal gate levels, Tetris-shaped arenas, sacrifice levels, the escape transition, and final boss/victory flow.

## Finish Criteria
- A full run can be completed from the main menu without using debug skips.
- Every level has readable spawn positions, reachable food, reachable button/key, and clear wall/gate visuals.
- Speed settings feel meaningfully different without making transitions or collision checks unstable.
- Sound can be toggled on/off and missing audio devices or missing files never crash startup.
- Game over, replay, leaderboard save, and return-to-menu all work from keyboard controls.

## Tuning Pass
1. Play normal levels 1-5 and adjust `required_food_for_level()` or gate spacing if a level drags.
2. Play Tetris levels and verify each shape has enough room to recover from turns.
3. Play sacrifice levels and tune ammo cost, wall break timing, and right-side key placement.
4. Play escape/final boss and tune boss health, shot limit, bullet speed, and victory timing.
5. Remove or gate debug shortcuts (`N` skip level and `Q` final boss jump) before release builds.

## Cleanup Backlog
- Split `game.py` into scene/state, level layout, audio, leaderboard, and rendering modules once behavior is stable.
- Move root assets into an `assets/` directory after confirming all load paths still use `ASSET_SEARCH_DIRS`.
- Add display-free unit tests for pure layout/progression rules as they are extracted.
- Add a short manual QA checklist for release playthroughs.
