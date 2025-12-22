import random
from pathlib import Path
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    GRID_WIDTH, GRID_HEIGHT, TILE_SIZE,
    HUD_HEIGHT, PLAYFIELD_HEIGHT,
    COLOR_BUTTON, COLOR_KEY, COLOR_HUD, COLOR_WALL, COLOR_SNAKE,
    MENU_FONT_FILE, UI_FONT_FILE, load_custom_font,
)
from grid import draw_grid, build_background
from snake import Snake
from food import Food
from config import load_scaled_image


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snake Quest - Gates & Keys")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.level = 1
        self.points = 0
        self.background = build_background(PLAYFIELD_HEIGHT)
        self.menu_background = build_background(SCREEN_HEIGHT)

        self.music_enabled = False
        self.music_loaded = False
        self._init_audio()

        self.snake: Snake | None = None
        self.food: Food | None = None
        self.button_pos: tuple[int, int] | None = None
        self.key_pos: tuple[int, int] | None = None
        self.wall_positions: set[tuple[int, int]] = set()
        self.key_image = load_scaled_image("key.png", (TILE_SIZE, TILE_SIZE))
        self.start_bg = load_scaled_image("menubg.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.banner_image = load_scaled_image("banner.png", (SCREEN_WIDTH, HUD_HEIGHT))

        self.game_started = False
        self.game_over = False
        self.start_time_ms: int | None = None
        self.level_food_eaten = 0
        self.playable_cells: set[tuple[int, int]] | None = None
        self.loading_active = False
        self.loading_start_ms: int | None = None
        self.loading_duration_ms = 2000
        self.loading_tiles: list[tuple[int, int]] = []
        self.loading_reveal_count = 0
        self.layout_ready = False
        self.level_clear = False
        self.speed_options = [("Slow", 0.5), ("Normal", 1.0), ("Fast", 1.5)]
        self.speed_index = 1
        self.speed_multiplier = self.speed_options[self.speed_index][1]
        self.last_frame_ms: int | None = None
        self.move_accumulator_ms = 0.0
        self.menu_page = "main"
        self.menu_options = ["Start Game", "Settings", "Quit"]
        self.menu_index = 0
        self.input_locked = False
        self.sound_on = True
        self.settings_index = 0

        self.menu_title_font = load_custom_font(MENU_FONT_FILE, 54)
        self.menu_option_font = load_custom_font(MENU_FONT_FILE, 30)
        self.menu_prompt_font = load_custom_font(MENU_FONT_FILE, 16)
        self.game_title_font = load_custom_font(MENU_FONT_FILE, 36)
        self.game_font = load_custom_font(MENU_FONT_FILE, 20)
        self.ui_title_font = load_custom_font(UI_FONT_FILE, 34)
        self.ui_font = load_custom_font(UI_FONT_FILE, 24)

    def start_level(self):
        """Set up a fresh level layout with increasing gate spacing."""
        self.snake = Snake(grid_pos=(5, 5))
        self.food = Food()
        if not self.layout_ready:
            self.build_walls()
        self.layout_ready = False
        if self.playable_cells and self.snake.head not in self.playable_cells:
            self.snake.segments[0] = random.choice(list(self.playable_cells))
        self.place_gate_elements()
        self.spawn_food()
        self.level_food_eaten = 0
        self.loading_active = False
        self.loading_start_ms = None
        self.loading_tiles = []
        self.loading_reveal_count = 0
        self.last_frame_ms = None
        self.move_accumulator_ms = 0.0
        self.level_clear = False
        self.input_locked = False

    def start_game(self):
        """Begin a new run from the start screen."""
        self.level = 1
        self.points = 0
        self.game_started = True
        self.game_over = False
        self.start_time_ms = pygame.time.get_ticks()
        self.last_frame_ms = None
        self.move_accumulator_ms = 0.0
        self.input_locked = False
        self.level_clear = False
        self.start_music()
        self.begin_loading()

    def build_walls(self):
        """Create a neon wall outline that also serves as collision."""

        self.wall_positions = set()
        if self.level >= 4:
            self.playable_cells = self._build_tetris_arena()
            for x in range(GRID_WIDTH):
                for y in range(GRID_HEIGHT):
                    if (x, y) not in self.playable_cells:
                        self.wall_positions.add((x, y))
        else:
            self.playable_cells = None
            for x in range(GRID_WIDTH):
                self.wall_positions.add((x, 0))
                self.wall_positions.add((x, GRID_HEIGHT - 1))
            for y in range(GRID_HEIGHT):
                self.wall_positions.add((0, y))
                self.wall_positions.add((GRID_WIDTH - 1, y))

    def _init_audio(self):
        """Load background music if theme.wav exists, otherwise stay silent."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            return

        music_path = Path(__file__).parent / "theme.wav"
        if not music_path.exists():
            return

        try:
            pygame.mixer.music.load(music_path)
            self.music_enabled = True
            self.music_loaded = True
        except pygame.error:
            return

    def start_music(self):
        if not self.music_loaded:
            return
        if not self.sound_on:
            return
        if pygame.mixer.music.get_busy():
            return
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1, fade_ms=1000)

    def stop_music(self, fade_ms: int = 1000):
        if not self.music_loaded:
            return
        if not pygame.mixer.music.get_busy():
            return
        pygame.mixer.music.fadeout(fade_ms)

    def place_gate_elements(self):
        """Place the button and key with increasing separation per level."""
        if self.playable_cells:
            candidates = list(self.playable_cells)
            random.shuffle(candidates)
            min_gap = 6 + self._shape_level_offset() * 2
            button = None
            key = None
            for candidate in candidates:
                if candidate == self.snake.head or candidate in self.wall_positions:
                    continue
                button = candidate
                break
            if button is None:
                button = self.snake.head
            for candidate in candidates:
                if candidate == button or candidate == self.snake.head:
                    continue
                if abs(candidate[0] - button[0]) + abs(candidate[1] - button[1]) < min_gap:
                    continue
                key = candidate
                break
            if key is None:
                key = button
            self.button_pos = button
            self.key_pos = key
            return

        min_gap = min(max(GRID_WIDTH, GRID_HEIGHT) - 2, 4 + self.level)
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

        # Ensure the snake does not spawn on the gate elements
        if button == self.snake.head or button in self.wall_positions:
            button = (button[0], max(0, button[1] - 1))
        if key == self.snake.head or key in self.wall_positions:
            key = (key[0], min(GRID_HEIGHT - 1, key[1] + 1))

        self.button_pos = button
        self.key_pos = key

    def spawn_food(self):
        assert self.food is not None and self.snake is not None
        if self.playable_cells:
            candidates = list(self.playable_cells)
            random.shuffle(candidates)
            for candidate in candidates:
                if candidate in self.snake.segments:
                    continue
                if candidate == self.button_pos or candidate == self.key_pos:
                    continue
                if candidate in self.wall_positions:
                    continue
                self.food.position = candidate
                return
            return

        while True:
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
            break

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_SPACE:
                        self.game_over = False
                        self.game_started = False
                        self.menu_page = "main"
                        self.stop_music()
                    elif event.key == pygame.K_ESCAPE:
                        self.stop_music()
                        self.running = False
                    continue

                if not self.game_started:
                    if self.menu_page == "main":
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.menu_index = (self.menu_index - 1) % len(self.menu_options)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.menu_index = (self.menu_index + 1) % len(self.menu_options)
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            selected = self.menu_options[self.menu_index]
                            if selected == "Start Game":
                                self.start_game()
                            elif selected == "Settings":
                                self.menu_page = "settings"
                            elif selected == "Quit":
                                self.stop_music()
                                self.running = False
                    elif self.menu_page == "settings":
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.settings_index = (self.settings_index - 1) % 2
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.settings_index = (self.settings_index + 1) % 2
                        elif event.key in (pygame.K_LEFT, pygame.K_a):
                            if self.settings_index == 0:
                                self.speed_index = (self.speed_index - 1) % len(self.speed_options)
                                self.speed_multiplier = self.speed_options[self.speed_index][1]
                            else:
                                self.sound_on = not self.sound_on
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            if self.settings_index == 0:
                                self.speed_index = (self.speed_index + 1) % len(self.speed_options)
                                self.speed_multiplier = self.speed_options[self.speed_index][1]
                            else:
                                self.sound_on = not self.sound_on
                        elif event.key in (pygame.K_1, pygame.K_KP1):
                            self.speed_index = 0
                            self.speed_multiplier = self.speed_options[self.speed_index][1]
                        elif event.key in (pygame.K_2, pygame.K_KP2):
                            self.speed_index = 1
                            self.speed_multiplier = self.speed_options[self.speed_index][1]
                        elif event.key in (pygame.K_3, pygame.K_KP3):
                            self.speed_index = 2
                            self.speed_multiplier = self.speed_options[self.speed_index][1]
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            if self.settings_index == 1:
                                self.sound_on = not self.sound_on
                        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                            self.menu_page = "main"
                            continue
                elif self.game_started:
                    if self.level_clear:
                        if event.key == pygame.K_SPACE:
                            self.level += 1
                            self.level_clear = False
                            self.begin_loading()
                        elif event.key == pygame.K_ESCAPE:
                            self.stop_music()
                            self.running = False
                        continue
                    if not self.loading_active:
                        if event.key == pygame.K_n:
                            self.complete_level()
                            continue
                        if event.key in (pygame.K_UP, pygame.K_w):
                            if not self.input_locked:
                                self.snake.set_direction((0, -1))
                                self.input_locked = True
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            if not self.input_locked:
                                self.snake.set_direction((0, 1))
                                self.input_locked = True
                        elif event.key in (pygame.K_LEFT, pygame.K_a):
                            if not self.input_locked:
                                self.snake.set_direction((-1, 0))
                                self.input_locked = True
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            if not self.input_locked:
                                self.snake.set_direction((1, 0))
                                self.input_locked = True
                    if event.key == pygame.K_ESCAPE:
                        self.stop_music()
                        self.running = False
                if not self.game_started and self.menu_page == "main" and event.key == pygame.K_ESCAPE:
                    self.stop_music()
                    self.running = False

    def update(self):
        if not self.game_started or self.game_over or self.level_clear:
            return

        now_ms = pygame.time.get_ticks()
        if self.last_frame_ms is None:
            self.last_frame_ms = now_ms
        dt_ms = now_ms - self.last_frame_ms
        self.last_frame_ms = now_ms
        dt_ms = min(dt_ms, 200)

        if self.loading_active:
            self.update_loading()
            return

        move_interval_ms = 1000 / max(1e-6, FPS * self.speed_multiplier)
        self.move_accumulator_ms += dt_ms
        while self.move_accumulator_ms >= move_interval_ms and not self.game_over:
            self.move_accumulator_ms -= move_interval_ms
            self.snake.update()
            self.input_locked = False
            self.check_collisions()
            self.check_food_eaten()
            self.check_key_reached()

    def check_collisions(self):
        head_x, head_y = self.snake.head

        # Wall collision ends game
        if head_x < 0 or head_x >= GRID_WIDTH or head_y < 0 or head_y >= GRID_HEIGHT:
            self.play_sound("death")
            self.game_over = True
            self.game_started = False
            self.stop_music()
            return

        if (head_x, head_y) in self.wall_positions:
            self.play_sound("death")
            self.game_over = True
            self.game_started = False
            self.stop_music()
            return

        # TODO: self-collision later

    def check_food_eaten(self):
        if self.snake.head == self.food.position:
            self.snake.grow(1)
            self.points += 1
            self.level_food_eaten += 1
            self.spawn_food()

    def check_key_reached(self):
        if self.key_pos is None or self.button_pos is None:
            return

        if self.level_food_eaten < self.required_food_for_level():
            return

        button_active = any(seg == self.button_pos for seg in self.snake.segments[1:])
        if self.snake.head == self.key_pos and button_active:
            self.complete_level()

    def complete_level(self):
        self.level_clear = True

    def draw(self):
        if self.game_over:
            self.draw_game_over()
        elif not self.game_started:
            if self.menu_page == "settings":
                self.draw_settings_screen()
            else:
                self.draw_start_screen()
        elif self.level_clear:
            self.draw_level_clear()
        elif self.loading_active:
            self.draw_loading_screen()
        else:
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.background, (0, HUD_HEIGHT))
            draw_grid(self.screen, offset_y=HUD_HEIGHT)
            self.draw_walls()

            self.food.draw(self.screen, HUD_HEIGHT)
            self.draw_button()
            self.draw_key()
            move_interval_ms = 1000 / max(1e-6, FPS * self.speed_multiplier)
            alpha = 0.0
            if move_interval_ms > 0:
                alpha = min(1.0, self.move_accumulator_ms / move_interval_ms)
            self.snake.draw(self.screen, HUD_HEIGHT, alpha=alpha)

            self.draw_hud_band()
            self.draw_hud()
            pygame.display.flip()

    def draw_button(self):
        if not self.button_pos:
            return
        x, y = self.button_pos
        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE + HUD_HEIGHT, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(self.screen, COLOR_BUTTON, rect)

    def draw_key(self):
        if not self.key_pos:
            return
        x, y = self.key_pos
        dest = (x * TILE_SIZE, y * TILE_SIZE + HUD_HEIGHT)
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
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE + HUD_HEIGHT, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, COLOR_WALL, rect, width=2, border_radius=4)

    def draw_hud_band(self):
        if self.banner_image:
            self.screen.blit(self.banner_image, (0, 0))
        else:
            pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, SCREEN_WIDTH, HUD_HEIGHT))

    def draw_hud(self):
        score_text = self.game_font.render(f"Score: {self.points}", True, COLOR_HUD)
        level_text = self.game_font.render(f"Level: {self.level}", True, COLOR_HUD)
        time_text = self.game_font.render(f"Time: {self.format_elapsed_time()}", True, COLOR_HUD)

        padding = 12
        score_rect = score_text.get_rect(midleft=(padding, HUD_HEIGHT // 2))
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, HUD_HEIGHT // 2))
        time_rect = time_text.get_rect(midright=(SCREEN_WIDTH - padding, HUD_HEIGHT // 2))

        shadow_color = (0, 0, 0)
        shadow_offset = (2, 2)

        score_shadow = self.game_font.render(f"Score: {self.points}", True, shadow_color)
        level_shadow = self.game_font.render(f"Level: {self.level}", True, shadow_color)
        time_shadow = self.game_font.render(f"Time: {self.format_elapsed_time()}", True, shadow_color)
        self.screen.blit(score_shadow, score_rect.move(*shadow_offset))
        self.screen.blit(level_shadow, level_rect.move(*shadow_offset))
        self.screen.blit(time_shadow, time_rect.move(*shadow_offset))
        self.screen.blit(score_text, score_rect)
        self.screen.blit(level_text, level_rect)
        self.screen.blit(time_text, time_rect)

    def play_sound(self, name: str):
        """Safe sound hook (no-op if audio assets are missing)."""
        return

    def required_food_for_level(self) -> int:
        if self.level == 1:
            return 2
        if self.level == 2:
            return 3
        return 5

    def _build_tetris_arena(self) -> set[tuple[int, int]]:
        """Create a full-arena Tetris-shaped playfield."""
        shapes = [
            ("I", [(0, 0), (1, 0), (2, 0), (3, 0)]),
            ("O", [(0, 0), (1, 0), (0, 1), (1, 1)]),
            ("T", [(0, 0), (1, 0), (2, 0), (1, 1)]),
            ("S", [(1, 0), (2, 0), (0, 1), (1, 1)]),
            ("Z", [(0, 0), (1, 0), (1, 1), (2, 1)]),
            ("L", [(0, 0), (0, 1), (0, 2), (1, 2)]),
            ("J", [(1, 0), (1, 1), (1, 2), (0, 2)]),
        ]
        shape_index = ((self.level - 4) // 3) % len(shapes)
        _, base_shape = shapes[shape_index]

        max_x = max(p[0] for p in base_shape)
        max_y = max(p[1] for p in base_shape)
        max_scale_x = max(1, (GRID_WIDTH - 4) // (max_x + 1))
        max_scale_y = max(1, (GRID_HEIGHT - 4) // (max_y + 1))
        max_scale = min(max_scale_x, max_scale_y)
        if self.level <= 6:
            scale = max(3, max_scale - 1)
        else:
            scale = max(3, max_scale - 2)
        width = (max_x + 1) * scale
        height = (max_y + 1) * scale
        origin_x = max(1, (GRID_WIDTH - width) // 2)
        origin_y = max(1, (GRID_HEIGHT - height) // 2)

        cells = set()
        for bx, by in base_shape:
            start_x = origin_x + bx * scale
            start_y = origin_y + by * scale
            for dx in range(scale):
                for dy in range(scale):
                    cells.add((start_x + dx, start_y + dy))

        return cells

    def _shape_level_offset(self) -> int:
        """0, 1, 2 within the current 3-level shape group."""
        if self.level < 4:
            return 0
        return (self.level - 4) % 3

    def begin_loading(self):
        """Show a 2s loading build for the next level before gameplay starts."""
        self.build_walls()
        self.layout_ready = True
        self.loading_tiles = self._build_loading_tiles()
        self.loading_reveal_count = 0
        self.loading_active = True
        self.loading_start_ms = pygame.time.get_ticks()

    def _build_loading_tiles(self) -> list[tuple[int, int]]:
        if not self.wall_positions:
            return []

        if self.level < 4:
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

        return sorted(self.wall_positions, key=lambda p: (p[1], p[0]))

    def update_loading(self):
        if self.loading_start_ms is None:
            self.loading_start_ms = pygame.time.get_ticks()
        elapsed = pygame.time.get_ticks() - self.loading_start_ms
        duration = max(1, self.loading_duration_ms)
        progress = min(1.0, elapsed / duration)
        target_count = int(progress * len(self.loading_tiles))
        self.loading_reveal_count = max(self.loading_reveal_count, target_count)

        if elapsed >= duration:
            self.loading_active = False
            self.start_level()

    def draw_loading_screen(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.background, (0, HUD_HEIGHT))
        draw_grid(self.screen, offset_y=HUD_HEIGHT)

        if self.loading_tiles:
            for (x, y) in self.loading_tiles[: self.loading_reveal_count]:
                rect = pygame.Rect(
                    x * TILE_SIZE,
                    y * TILE_SIZE + HUD_HEIGHT,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                pygame.draw.rect(self.screen, COLOR_WALL, rect, width=2, border_radius=4)

        self.draw_hud_band()
        self.draw_hud()
        pygame.display.flip()

    def draw_level_clear(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.background, (0, HUD_HEIGHT))
        draw_grid(self.screen, offset_y=HUD_HEIGHT)
        self.draw_walls()

        if self.food:
            self.food.draw(self.screen, HUD_HEIGHT)
        if self.button_pos:
            self.draw_button()
        if self.key_pos:
            self.draw_key()
        if self.snake:
            self.snake.draw(self.screen, HUD_HEIGHT, alpha=0.0)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        title_text = self.game_title_font.render("Level Clear", True, COLOR_HUD)
        prompt_text = self.game_font.render("Press SPACE to continue", True, COLOR_HUD)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 12))
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(title_text, title_rect)
        self.screen.blit(prompt_text, prompt_rect)
        pygame.display.flip()

    def draw_menu_background(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.menu_background, (0, 0))
        draw_grid(self.screen, offset_y=0)
        self.draw_menu_border()

    def draw_menu_border(self):
        tiles_x = SCREEN_WIDTH // TILE_SIZE
        tiles_y = SCREEN_HEIGHT // TILE_SIZE
        for x in range(tiles_x):
            for y in (0, tiles_y - 1):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, COLOR_WALL, rect, width=2, border_radius=4)
        for y in range(1, tiles_y - 1):
            for x in (0, tiles_x - 1):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, COLOR_WALL, rect, width=2, border_radius=4)

    def draw_start_screen(self):
        if self.start_bg:
            self.screen.blit(self.start_bg, (0, 0))
        else:
            self.screen.blit(self.menu_background, (0, 0))

        base_y = int(SCREEN_HEIGHT * 0.66) + 52
        line_gap = 40
        for idx, label in enumerate(self.menu_options):
            color = COLOR_SNAKE if idx == self.menu_index else COLOR_HUD
            option_text = self.menu_option_font.render(label, True, color)
            option_rect = option_text.get_rect(center=(SCREEN_WIDTH // 2, base_y + idx * line_gap))
            self.screen.blit(option_text, option_rect)

        prompt_text = self.menu_prompt_font.render("Press ENTER or SPACE", True, COLOR_HUD)
        prompt_rect = prompt_text.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 18))
        self.screen.blit(prompt_text, prompt_rect)
        pygame.display.flip()

    def draw_settings_screen(self):
        self.draw_menu_background()

        title_text = self.menu_title_font.render("Settings", True, COLOR_HUD)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
        self.screen.blit(title_text, title_rect)

        speed_label = f"Speed: {self.speed_options[self.speed_index][0]}"
        sound_label = f"Sound: {'On' if self.sound_on else 'Off'}"
        settings_labels = [speed_label, sound_label]
        base_y = SCREEN_HEIGHT // 2 - 20
        line_gap = 40
        for idx, label in enumerate(settings_labels):
            color = COLOR_SNAKE if idx == self.settings_index else COLOR_HUD
            option_text = self.menu_option_font.render(label, True, color)
            option_rect = option_text.get_rect(center=(SCREEN_WIDTH // 2, base_y + idx * line_gap))
            self.screen.blit(option_text, option_rect)

        prompt_text = self.menu_prompt_font.render("Press ESC to return", True, COLOR_HUD)
        prompt_rect = prompt_text.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 28))
        self.screen.blit(prompt_text, prompt_rect)
        pygame.display.flip()

    def draw_game_over(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.background, (0, HUD_HEIGHT))
        draw_grid(self.screen, offset_y=HUD_HEIGHT)
        self.draw_walls()

        if self.food:
            self.food.draw(self.screen, HUD_HEIGHT)
        if self.button_pos:
            self.draw_button()
        if self.key_pos:
            self.draw_key()
        if self.snake:
            self.snake.draw(self.screen, HUD_HEIGHT, alpha=0.0)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        title_text = self.game_title_font.render("Game Over", True, COLOR_HUD)
        prompt_text = self.game_font.render(
            "Press SPACE for main menu or ESC to exit",
            True,
            COLOR_HUD,
        )

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
            self.clock.tick(60)
            self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
