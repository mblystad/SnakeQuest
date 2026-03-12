from __future__ import annotations

from dataclasses import dataclass, field
import random

GRID_WIDTH = 36
GRID_HEIGHT = 24
BASE_TICKS_PER_SECOND = 10
LOADING_DURATION_MS = 1400

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)


def can_open_gate(collected_food: int, button_active: bool, required_food: int) -> bool:
    return collected_food >= required_food and button_active


def direction_is_valid(new_dir: tuple[int, int], current_dir: tuple[int, int]) -> bool:
    cur_dx, cur_dy = current_dir
    new_dx, new_dy = new_dir
    if (cur_dx == -new_dx and cur_dx != 0) or (cur_dy == -new_dy and cur_dy != 0):
        return False
    return True


@dataclass(slots=True)
class MobileSettings:
    speed_index: int = 1
    sound_on: bool = True
    speed_options: tuple[tuple[str, float], ...] = (
        ("Slow", 0.5),
        ("Normal", 1.0),
        ("Fast", 1.5),
    )

    @property
    def speed_name(self) -> str:
        return self.speed_options[self.speed_index][0]

    @property
    def speed_multiplier(self) -> float:
        return self.speed_options[self.speed_index][1]

    @property
    def tick_interval_ms(self) -> float:
        return 1000.0 / max(1e-6, BASE_TICKS_PER_SECOND * self.speed_multiplier)

    def cycle_speed(self) -> None:
        self.speed_index = (self.speed_index + 1) % len(self.speed_options)


@dataclass(slots=True)
class MobileSnake:
    segments: list[tuple[int, int]]
    direction: tuple[int, int] = RIGHT
    pending_direction: tuple[int, int] = RIGHT
    grow_pending: int = 0

    @property
    def head(self) -> tuple[int, int]:
        return self.segments[0]

    def set_direction(self, new_dir: tuple[int, int]) -> bool:
        if not direction_is_valid(new_dir, self.pending_direction):
            return False
        self.pending_direction = new_dir
        return True

    def grow(self, amount: int = 1) -> None:
        self.grow_pending += amount

    def step(self) -> None:
        self.direction = self.pending_direction
        head_x, head_y = self.head
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        self.segments.insert(0, new_head)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.segments.pop()


@dataclass(slots=True)
class MobileGameSession:
    settings: MobileSettings = field(default_factory=MobileSettings)
    random_seed: int | None = None
    rng: random.Random = field(init=False)
    state: str = field(init=False, default="menu")
    level: int = field(init=False, default=1)
    score: int = field(init=False, default=0)
    elapsed_time_ms: float = field(init=False, default=0.0)
    level_food_eaten: int = field(init=False, default=0)
    accumulator_ms: float = field(init=False, default=0.0)
    loading_elapsed_ms: float = field(init=False, default=0.0)
    loading_tiles: list[tuple[int, int]] = field(init=False, default_factory=list)
    loading_reveal_count: int = field(init=False, default=0)
    walls: set[tuple[int, int]] = field(init=False, default_factory=set)
    snake: MobileSnake | None = field(init=False, default=None)
    food_pos: tuple[int, int] | None = field(init=False, default=None)
    button_pos: tuple[int, int] | None = field(init=False, default=None)
    key_pos: tuple[int, int] | None = field(init=False, default=None)
    input_locked: bool = field(init=False, default=False)
    queued_direction: tuple[int, int] | None = field(init=False, default=None)
    level_start_score: int = field(init=False, default=0)
    level_start_time_ms: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.random_seed)

    def start_new_run(self) -> None:
        self.level = 1
        self.score = 0
        self.elapsed_time_ms = 0.0
        self.level_start_score = 0
        self.level_start_time_ms = 0.0
        self.begin_loading()

    def replay_level(self) -> None:
        self.score = self.level_start_score
        self.elapsed_time_ms = self.level_start_time_ms
        self.begin_loading()

    def advance_level(self) -> None:
        if self.state != "level_clear":
            return
        self.level += 1
        self.begin_loading()

    def begin_loading(self) -> None:
        self._build_border_walls()
        self.loading_tiles = self._build_loading_tiles()
        self.loading_reveal_count = 0
        self.loading_elapsed_ms = 0.0
        self.level_food_eaten = 0
        self.accumulator_ms = 0.0
        self.input_locked = False
        self.queued_direction = None
        self.state = "loading"

    def start_level(self) -> None:
        self.level_start_score = self.score
        self.level_start_time_ms = self.elapsed_time_ms
        self.level_food_eaten = 0
        self.accumulator_ms = 0.0
        self.input_locked = False
        self.queued_direction = None
        self.snake = MobileSnake(segments=[(5, 5), (4, 5)])
        self._place_gate_elements()
        self._spawn_food()
        self.state = "playing"

    def queue_direction(self, new_dir: tuple[int, int]) -> None:
        if self.state != "playing" or self.snake is None:
            return
        if new_dir == self.snake.pending_direction:
            return
        if not self.input_locked:
            if self.snake.set_direction(new_dir):
                self.input_locked = True
                self.queued_direction = None
            return
        if direction_is_valid(new_dir, self.snake.pending_direction):
            self.queued_direction = new_dir

    def toggle_pause(self) -> None:
        if self.state == "playing":
            self.state = "paused"
        elif self.state == "paused":
            self.state = "playing"

    def update(self, dt_ms: float) -> None:
        dt_ms = min(200.0, max(0.0, dt_ms))
        if self.state == "loading":
            self._update_loading(dt_ms)
            return
        if self.state != "playing" or self.snake is None:
            return

        move_interval_ms = self.settings.tick_interval_ms
        self.accumulator_ms += dt_ms
        updates = 0
        max_updates = 5
        while self.accumulator_ms >= move_interval_ms and self.state == "playing":
            self.accumulator_ms -= move_interval_ms
            self._step_once(move_interval_ms)
            updates += 1
            if updates >= max_updates:
                self.accumulator_ms = 0.0
                break

    def gate_button_active(self) -> bool:
        if self.snake is None or self.button_pos is None:
            return False
        return self.button_pos in self.snake.segments[1:]

    def gate_open(self) -> bool:
        return can_open_gate(
            self.level_food_eaten,
            self.gate_button_active(),
            self.required_food_for_level(),
        )

    def required_food_for_level(self) -> int:
        if self.level == 1:
            return 2
        if self.level == 2:
            return 3
        return 5

    def progress_ratio(self) -> float:
        required_food = self.required_food_for_level()
        if required_food <= 0:
            return 1.0
        return min(1.0, self.level_food_eaten / required_food)

    def format_elapsed_time(self) -> str:
        total_seconds = max(0, int(self.elapsed_time_ms) // 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02}:{seconds:02}"

    def status_text(self) -> str:
        if self.state == "loading":
            return f"Loading level {self.level}"
        if self.state == "paused":
            return "Paused"
        if self.state == "level_clear":
            return "Gate reached. Tap Next."
        if self.state == "game_over":
            return "Game over. Replay or return to menu."
        if self.gate_open():
            return "Gate open. Reach the key."
        return (
            f"Collect {self.required_food_for_level()} food and hold the button to open the gate."
        )

    def _update_loading(self, dt_ms: float) -> None:
        self.loading_elapsed_ms += dt_ms
        progress = min(1.0, self.loading_elapsed_ms / LOADING_DURATION_MS)
        self.loading_reveal_count = int(progress * len(self.loading_tiles))
        if self.loading_elapsed_ms >= LOADING_DURATION_MS:
            self.start_level()

    def _step_once(self, move_interval_ms: float) -> None:
        if self.snake is None:
            return
        self.snake.step()
        self.elapsed_time_ms += move_interval_ms
        self.input_locked = False
        if self.queued_direction is not None:
            if direction_is_valid(self.queued_direction, self.snake.direction):
                self.snake.set_direction(self.queued_direction)
            self.queued_direction = None

        head = self.snake.head
        if head in self.walls or self._snake_hit_self():
            self.state = "game_over"
            return

        if self.food_pos is not None and head == self.food_pos:
            self.snake.grow(1)
            self.score += 1
            self.level_food_eaten += 1
            self._spawn_food()

        if self.key_pos is not None and head == self.key_pos and self.gate_open():
            self.state = "level_clear"

    def _snake_hit_self(self) -> bool:
        if self.snake is None or len(self.snake.segments) < 4:
            return False
        return self.snake.head in self.snake.segments[1:]

    def _build_border_walls(self) -> None:
        self.walls = set()
        for x in range(GRID_WIDTH):
            self.walls.add((x, 0))
            self.walls.add((x, GRID_HEIGHT - 1))
        for y in range(GRID_HEIGHT):
            self.walls.add((0, y))
            self.walls.add((GRID_WIDTH - 1, y))

    def _build_loading_tiles(self) -> list[tuple[int, int]]:
        tiles: list[tuple[int, int]] = []
        top = 0
        bottom = GRID_HEIGHT - 1
        left = 0
        right = GRID_WIDTH - 1
        for x in range(left, right + 1):
            tiles.append((x, top))
        for y in range(top + 1, bottom + 1):
            tiles.append((right, y))
        for x in range(right - 1, left - 1, -1):
            tiles.append((x, bottom))
        for y in range(bottom - 1, top, -1):
            tiles.append((left, y))
        return tiles

    def _place_gate_elements(self) -> None:
        if self.snake is None:
            self.button_pos = None
            self.key_pos = None
            return

        candidates = [
            (x, y)
            for x in range(1, GRID_WIDTH - 1)
            for y in range(1, GRID_HEIGHT - 1)
            if (x, y) not in self.snake.segments
        ]
        head = self.snake.head
        candidates.sort(key=lambda pos: self._distance(pos, head), reverse=True)
        self.button_pos = candidates[0]

        key_candidates = [pos for pos in candidates if pos != self.button_pos]
        key_candidates.sort(
            key=lambda pos: (self._distance(pos, self.button_pos), self._distance(pos, head)),
            reverse=True,
        )
        self.key_pos = key_candidates[0]

    def _spawn_food(self) -> None:
        occupied = set(self.walls)
        if self.snake is not None:
            occupied.update(self.snake.segments)
        if self.button_pos is not None:
            occupied.add(self.button_pos)
        if self.key_pos is not None:
            occupied.add(self.key_pos)

        candidates = [
            (x, y)
            for x in range(1, GRID_WIDTH - 1)
            for y in range(1, GRID_HEIGHT - 1)
            if (x, y) not in occupied
        ]
        self.food_pos = self.rng.choice(candidates) if candidates else None

    @staticmethod
    def _distance(a: tuple[int, int], b: tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
