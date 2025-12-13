import random
from pathlib import Path
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    DEFAULT_FONT, GRID_WIDTH, GRID_HEIGHT, TILE_SIZE,
    COLOR_BUTTON, COLOR_KEY, COLOR_HUD, COLOR_WALL, ASSET_DIR,
)
from grid import draw_grid, build_background
from snake import Snake
from food import Food
from config import load_scaled_image, load_sound

TETRIS_SHAPES = {
    "I": [(0, 0), (1, 0), (2, 0), (3, 0)],
    "O": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "T": [(0, 0), (1, 0), (2, 0), (1, 1)],
    "S": [(1, 0), (2, 0), (0, 1), (1, 1)],
    "Z": [(0, 0), (1, 0), (1, 1), (2, 1)],
    "J": [(0, 0), (0, 1), (1, 1), (2, 1)],
    "L": [(2, 0), (0, 1), (1, 1), (2, 1)],
}


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snake Quest - Gates & Keys")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.level = 1
        self.points = 0
        self.transition_timer = 0
        self.transition_text = ""
        self.background = build_background()

        self.snake: Snake | None = None
        self.food: Food | None = None
        self.button_pos: tuple[int, int] | None = None
        self.key_pos: tuple[int, int] | None = None
        self.wall_positions: set[tuple[int, int]] = set()
        self.key_image = load_scaled_image("key.png", (TILE_SIZE, TILE_SIZE))
        self.start_bg = load_scaled_image("bg.png", (SCREEN_WIDTH, SCREEN_HEIGHT))

        # Audio
        self.audio_enabled = self.init_audio()
        self.start_music_path: Path | None = None
        self.level_music_paths: list[Path] = []
        self.current_music_path: Path | None = None
        self.sounds: dict[str, pygame.mixer.Sound | None] = {}
        self.load_audio_assets()
        self.play_start_music()

        self.game_started = False
        self.start_time_ms: int | None = None

    # -- Audio helpers ---------------------------------------------------
    def init_audio(self) -> bool:
        try:
            pygame.mixer.init()
        except pygame.error:
            return False
        return True

    def load_audio_assets(self):
        if not self.audio_enabled:
            return

        # Music
        self.start_music_path = self._music_path("start.ogg")
        for name in ("level1.ogg", "level2.ogg", "level3.ogg"):
            path = self._music_path(name)
            if path:
                self.level_music_paths.append(path)

        # Sound effects
        self.sounds = {
            "eat": load_sound("eat.wav", volume=0.6),
            "key": load_sound("key.wav", volume=0.8),
            "start": load_sound("start.wav", volume=0.8),
            "death": load_sound("snakesplosion.wav", volume=0.9),
        }

    def _music_path(self, filename: str) -> Path | None:
        path = ASSET_DIR / filename
        return path if path.exists() else None

    def play_music(self, path: Path | None, *, loop: bool = True):
        if not self.audio_enabled or path is None:
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1 if loop else 0)
            self.current_music_path = path
        except pygame.error:
            pass

    def stop_music(self):
        if not self.audio_enabled:
            return
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass

    def play_start_music(self):
        if self.current_music_path == self.start_music_path:
            return
        self.play_music(self.start_music_path, loop=True)

    def set_music_for_level(self):
        if not self.level_music_paths:
            return
        index = ((self.level - 1) // 5) % len(self.level_music_paths)
        target = self.level_music_paths[index]
        if self.current_music_path != target:
            self.play_music(target, loop=True)

    def play_sound(self, key: str):
        if not self.audio_enabled:
            return
        sound = self.sounds.get(key)
        if sound:
            try:
                sound.play()
            except pygame.error:
                pass

    def start_level(self):
        """Set up a fresh level layout with increasing gate spacing."""
        spawn = self.find_spawn_point()
        self.snake = Snake(grid_pos=spawn)
        self.food = Food()
        self.build_walls()
        self.place_gate_elements()
        self.spawn_food()
        self.transition_timer = 0
        self.transition_text = ""
        self.set_music_for_level()

    def start_game(self):
        """Begin a new run from the start screen."""
        self.level = 1
        self.points = 0
        self.game_started = True
        self.start_time_ms = pygame.time.get_ticks()
        self.stop_music()
        self.play_sound("start")
        self.start_level()

    def build_walls(self):
        """Create the border walls and interior Tetris-inspired obstacles."""

        self.wall_positions = set()
        for x in range(GRID_WIDTH):
            self.wall_positions.add((x, 0))
            self.wall_positions.add((x, GRID_HEIGHT - 1))
        for y in range(GRID_HEIGHT):
            self.wall_positions.add((0, y))
            self.wall_positions.add((GRID_WIDTH - 1, y))

        self.wall_positions |= self.generate_tetris_obstacles()

    def generate_tetris_obstacles(self) -> set[tuple[int, int]]:
        """Build progressively denser obstacle layouts using Tetris shapes."""

        rng = random.Random(self.level * 1337)
        shape_order = list(TETRIS_SHAPES.keys())
        shape_count = min(1 + (self.level - 1) // 2, 6)
        scale = 1 + (self.level - 1) // 6
        margin = 3

        occupied: set[tuple[int, int]] = set()
        # Reserve a breathing space around the starting area
        spawn_x, spawn_y = GRID_WIDTH // 2, GRID_HEIGHT // 2
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                occupied.add((spawn_x + dx, spawn_y + dy))

        for i in range(shape_count):
            shape_name = shape_order[(self.level - 1 + i) % len(shape_order)]
            shape_cells = TETRIS_SHAPES[shape_name]
            rotation = rng.randrange(4)
            shape_cells = self.rotate_shape(shape_cells, rotation)

            bounds = self.shape_bounds(shape_cells, scale)
            attempts = 50
            placed_cells: set[tuple[int, int]] | None = None
            while attempts > 0 and placed_cells is None:
                attempts -= 1
                anchor_x = rng.randint(margin, GRID_WIDTH - bounds[0] - margin)
                anchor_y = rng.randint(margin, GRID_HEIGHT - bounds[1] - margin)
                candidate = self.place_shape(shape_cells, anchor_x, anchor_y, scale)

                if candidate & occupied:
                    continue
                placed_cells = candidate

            if placed_cells:
                occupied |= placed_cells

        return occupied

    def shape_bounds(self, cells: list[tuple[int, int]], scale: int) -> tuple[int, int]:
        max_x = max(x for x, _ in cells)
        max_y = max(y for _, y in cells)
        min_x = min(x for x, _ in cells)
        min_y = min(y for _, y in cells)
        width = (max_x - min_x + 1) * scale
        height = (max_y - min_y + 1) * scale
        return width, height

    def rotate_shape(self, cells: list[tuple[int, int]], turns: int) -> list[tuple[int, int]]:
        rotated = cells
        for _ in range(turns % 4):
            rotated = [(-y, x) for x, y in rotated]
            min_x = min(x for x, _ in rotated)
            min_y = min(y for _, y in rotated)
            rotated = [(x - min_x, y - min_y) for x, y in rotated]
        return rotated

    def place_shape(
        self, cells: list[tuple[int, int]], anchor_x: int, anchor_y: int, scale: int
    ) -> set[tuple[int, int]]:
        placed = set()
        for x, y in cells:
            for dx in range(scale):
                for dy in range(scale):
                    px = anchor_x + x * scale + dx
                    py = anchor_y + y * scale + dy
                    if 0 <= px < GRID_WIDTH and 0 <= py < GRID_HEIGHT:
                        placed.add((px, py))
        return placed

    def find_spawn_point(self) -> tuple[int, int]:
        """Find a spawn location away from walls for the snake's head."""

        center = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
        self.build_walls()
        if center not in self.wall_positions:
            return center

        # Spiral search outward from center
        for radius in range(1, max(GRID_WIDTH, GRID_HEIGHT)):
            for dx in range(-radius, radius + 1):
                for dy in (-radius, radius):
                    candidate = (center[0] + dx, center[1] + dy)
                    if candidate not in self.wall_positions:
                        return candidate
            for dy in range(-radius + 1, radius):
                for dx in (-radius, radius):
                    candidate = (center[0] + dx, center[1] + dy)
                    if candidate not in self.wall_positions:
                        return candidate

        return (1, 1)

    def place_gate_elements(self):
        """Place the button and key with increasing separation per level."""
        min_gap = min(max(GRID_WIDTH, GRID_HEIGHT) - 2, 4 + self.level)
        attempts = 80

        while attempts > 0:
            attempts -= 1
            oriented_horizontal = random.choice([True, False])

            if oriented_horizontal:
                y = random.randint(2, GRID_HEIGHT - 3)
                start_x = random.randint(1, max(1, GRID_WIDTH - min_gap - 2))
                button = (start_x, y)
                key = (min(start_x + min_gap, GRID_WIDTH - 2), y)
            else:
                x = random.randint(2, GRID_WIDTH - 3)
                start_y = random.randint(1, max(1, GRID_HEIGHT - min_gap - 2))
                button = (x, start_y)
                key = (x, min(start_y + min_gap, GRID_HEIGHT - 2))

            if (
                button in self.wall_positions
                or key in self.wall_positions
                or button == self.snake.head
                or key == self.snake.head
            ):
                continue

            self.button_pos = button
            self.key_pos = key
            return

        # Fallback placement near center if all else fails
        center = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
        self.button_pos = (center[0], max(1, center[1] - 2))
        self.key_pos = (center[0], min(GRID_HEIGHT - 2, center[1] + 2))

    def spawn_food(self):
        assert self.food is not None and self.snake is not None
        attempts = 200
        while attempts > 0:
            attempts -= 1
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            candidate = (x, y)
            if candidate in self.snake.segments:
                continue
            if candidate == self.button_pos or candidate == self.key_pos:
                continue
            if candidate in self.wall_positions:
                continue
            self.food.position = candidate
            return

        # Fallback: place at first open tile
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                candidate = (x, y)
                if (
                    candidate not in self.snake.segments
                    and candidate not in self.wall_positions
                    and candidate not in (self.button_pos, self.key_pos)
                ):
                    self.food.position = candidate
                    return

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if not self.game_started and event.key == pygame.K_SPACE:
                    self.start_game()
                elif self.game_started:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.snake.set_direction((0, -1))
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.snake.set_direction((0, 1))
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self.snake.set_direction((-1, 0))
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.snake.set_direction((1, 0))

                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self):
        if not self.game_started:
            return

        if self.transition_timer > 0:
            self.transition_timer -= 1
            if self.transition_timer == 0:
                self.start_level()
            return

        self.snake.update()
        self.check_collisions()
        self.check_food_eaten()
        self.check_key_reached()

    def check_collisions(self):
        head_x, head_y = self.snake.head

        # Wall collision ends game
        if head_x < 0 or head_x >= GRID_WIDTH or head_y < 0 or head_y >= GRID_HEIGHT:
            self.play_sound("death")
            self.running = False
            return

        if (head_x, head_y) in self.wall_positions:
            self.play_sound("death")
            self.running = False

        # TODO: self-collision later

    def check_food_eaten(self):
        if self.snake.head == self.food.position:
            self.snake.grow(1)
            self.points += 1
            self.play_sound("eat")
            self.spawn_food()

    def check_key_reached(self):
        if self.key_pos is None or self.button_pos is None:
            return

        button_active = any(seg == self.button_pos for seg in self.snake.segments[1:])
        if self.snake.head == self.key_pos and button_active:
            self.complete_level()

    def complete_level(self):
        self.transition_text = f"Level {self.level} complete!"
        self.level += 1
        self.transition_timer = FPS // 2
        self.play_sound("key")

    def draw(self):
        if not self.game_started:
            self.draw_start_screen()
        else:
            self.screen.blit(self.background, (0, 0))
            draw_grid(self.screen)
            self.draw_walls()

            self.food.draw(self.screen)
            self.draw_button()
            self.draw_key()
            self.snake.draw(self.screen)

            self.draw_hud()
            if self.transition_timer > 0:
                self.draw_transition()

            pygame.display.flip()

    def draw_button(self):
        if not self.button_pos:
            return
        x, y = self.button_pos
        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(self.screen, COLOR_BUTTON, rect)

    def draw_key(self):
        if not self.key_pos:
            return
        x, y = self.key_pos
        dest = (x * TILE_SIZE, y * TILE_SIZE)
        if self.key_image:
            self.screen.blit(self.key_image, dest)
        else:
            rect = pygame.Rect(*dest, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, COLOR_KEY, rect)

        # Overlay lock indicator if button is not pressed yet
        if not any(seg == self.button_pos for seg in self.snake.segments[1:]):
            lock_overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            lock_overlay.fill((0, 0, 0, 120))
            self.screen.blit(lock_overlay, dest)

    def draw_walls(self):
        if not self.wall_positions:
            return

        for (x, y) in self.wall_positions:
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, COLOR_WALL, rect, border_radius=4)

    def draw_hud(self):
        time_text = DEFAULT_FONT.render(f"Time: {self.format_elapsed_time()}", True, COLOR_HUD)
        score_text = DEFAULT_FONT.render(f"Score: {self.points}", True, COLOR_HUD)
        level_text = DEFAULT_FONT.render(f"Level: {self.level}", True, COLOR_HUD)

        self.screen.blit(time_text, (10, 10))
        self.screen.blit(score_text, (10, 35))
        self.screen.blit(level_text, (10, 60))

    def draw_transition(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        if self.transition_text:
            text_surf = DEFAULT_FONT.render(self.transition_text, True, COLOR_HUD)
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text_surf, text_rect)

    def draw_start_screen(self):
        self.play_start_music()
        if self.start_bg:
            self.screen.blit(self.start_bg, (0, 0))
        else:
            self.screen.blit(self.background, (0, 0))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        title_text = DEFAULT_FONT.render("Snake Quest", True, COLOR_HUD)
        prompt_text = DEFAULT_FONT.render("Press SPACE to start", True, COLOR_HUD)

        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))

        self.screen.blit(title_text, title_rect)
        self.screen.blit(prompt_text, prompt_rect)
        pygame.display.flip()

    def format_elapsed_time(self) -> str:
        if not self.start_time_ms:
            return "00:00"

        elapsed_ms = pygame.time.get_ticks() - self.start_time_ms
        total_seconds = max(0, elapsed_ms // 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02}:{seconds:02}"

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
