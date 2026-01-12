import json
import random
from collections import deque
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
    TETRIS_SHAPES = [
        ("I", [(0, 0), (1, 0), (2, 0), (3, 0)]),
        ("O", [(0, 0), (1, 0), (0, 1), (1, 1)]),
        ("T", [(0, 0), (1, 0), (2, 0), (1, 1)]),
        ("S", [(1, 0), (2, 0), (0, 1), (1, 1)]),
        ("Z", [(0, 0), (1, 0), (1, 1), (2, 1)]),
        ("L", [(0, 0), (0, 1), (0, 2), (1, 2)]),
        ("J", [(1, 0), (1, 1), (1, 2), (0, 2)]),
    ]

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snake Quest - Gates & Keys")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.level = 1
        self.points = 0
        self.elapsed_time_ms = 0
        self.level_start_points = 0
        self.level_start_time_ms = 0
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
        self.start_bg_alt = load_scaled_image("menubg2.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.banner_image = load_scaled_image("banner.png", (SCREEN_WIDTH, HUD_HEIGHT))
        self.sacrifice_shot_size = max(4, int(TILE_SIZE * 0.7))
        self.sacrifice_shot_corner = max(2, int(self.sacrifice_shot_size * 0.3))
        self.sacrifice_shot_images = self._build_sacrifice_shot_images()

        self.game_started = False
        self.game_over = False
        self.level_food_eaten = 0
        self.sacrifice_ammo = 0
        self.playable_cells: set[tuple[int, int]] | None = None
        self.sacrifice_playable_cells: set[tuple[int, int]] | None = None
        self.sacrifice_left_cells: set[tuple[int, int]] | None = None
        self.sacrifice_right_cells: set[tuple[int, int]] | None = None
        self.sacrifice_wall_open = False
        self.sacrifice_shot_active = False
        self.sacrifice_shot_pos = (0.0, 0.0)
        self.sacrifice_shot_dir = (0, 0)
        self.sacrifice_shot_target = (0.0, 0.0)
        self.sacrifice_shot_target_cell = (0, 0)
        self.sacrifice_shot_speed = 18.0
        self.sacrifice_shot_radius = max(2, int(TILE_SIZE * 0.35))
        self.sacrifice_shot_hit_radius = 0.2
        self.sacrifice_explosions: list[dict] = []
        self.loading_active = False
        self.loading_start_ms: int | None = None
        self.loading_duration_ms = 2000
        self.loading_tiles: list[tuple[int, int]] = []
        self.loading_reveal_count = 0
        self.layout_ready = False
        self.level_clear = False
        self.game_paused = False
        self.speed_options = [("Slow", 0.5), ("Normal", 1.0), ("Fast", 1.5)]
        self.speed_index = 1
        self.speed_multiplier = self.speed_options[self.speed_index][1]
        self.last_frame_ms: int | None = None
        self.move_accumulator_ms = 0.0
        self.menu_page = "main"
        self.menu_options = ["Start Game", "Settings", "Quit"]
        self.menu_index = 0
        self.input_locked = False
        self.queued_direction: tuple[int, int] | None = None
        self.sound_on = True
        self.settings_index = 0
        self.score_recorded = False
        self.name_input = ""
        self.name_max_length = 10
        self.leaderboard_path = Path(__file__).with_name("leaderboard.json")
        self.leaderboard_entries: list[dict] = []
        self._load_leaderboard()

        self.menu_title_font = load_custom_font(MENU_FONT_FILE, 54)
        self.menu_option_font = load_custom_font(MENU_FONT_FILE, 30)
        self.menu_prompt_font = load_custom_font(MENU_FONT_FILE, 16)
        self.game_title_font = load_custom_font(MENU_FONT_FILE, 36)
        self.game_font = load_custom_font(MENU_FONT_FILE, 20)
        self.ui_title_font = load_custom_font(UI_FONT_FILE, 34)
        self.ui_font = load_custom_font(UI_FONT_FILE, 24)

        self.first_tetris_level = 6
        self.last_normal_level = self.first_tetris_level - 1
        self.last_tetris_level = self.first_tetris_level + len(self.TETRIS_SHAPES) - 1
        self.first_sacrifice_level = self.last_tetris_level + 1
        self.sacrifice_level_count = 5
        self.last_sacrifice_level = self.first_sacrifice_level + self.sacrifice_level_count - 1
        self.escape_level = self.last_sacrifice_level + 1
        self.breakable_wall_positions: set[tuple[int, int]] = set()
        self.escape_wall_open = False
        self.side_scroller_active = False
        self.side_scroller_left_lock = 2
        self.starfield: list[dict] = []
        self.star_count = 90
        self.star_speed_range = (40.0, 140.0)
        self.side_scroller_food_eaten = 0
        self.side_scroller_food_needed = 5
        self.side_scroller_trigger_x = GRID_WIDTH - 8
        self.space_fade = 0.0
        self.space_fade_time_ms = 0.0
        self.space_fade_duration_ms = 5000.0
        self.space_fade_active = False
        self.player_shots: list[dict] = []
        self.player_shot_speed = 16.0
        self.player_shot_radius = max(2, int(TILE_SIZE * 0.25))
        self.player_shot_limit = 3
        self.boss_active = False
        self.boss_hp = 0
        self.boss_pos = (0.0, 0.0)
        self.boss_dir = 1
        self.boss_speed = 3.8
        self.boss_approach_speed = 6.0
        self.boss_width = 3
        self.boss_height = 4
        self.boss_target_x = GRID_WIDTH - self.boss_width - 2
        self.boss_fire_interval_ms = 1200
        self.boss_fire_timer_ms = 0.0
        self.boss_bullets: list[dict] = []
        self.boss_bullet_speed = 9.5
        self.boss_bullet_radius = max(2, int(TILE_SIZE * 0.25))
        self.boss_state = "hidden"
        self.boss_sprite = self._build_boss_sprite()
        self.story_active = False
        self.story_text = ""
        self.story_next_action = ""
        self.story_last_frame_ms: int | None = None
        self.story_move_accumulator_ms = 0.0
        self.story_move_interval_ms = 140
        self.story_path = self._build_story_path()
        self.story_path_index = 0
        self.story_snake_length = 10
        self.story_snake: Snake | None = None
        self.story_intro_text = "Placeholder intro"
        self.story_mid_text = "Placeholder level 5-6"
        self.story_end_text = "Placeholder sacrifice intro"
        self.story_final_text = "Placeholder finale"
        self.intro_active = True
        self.intro_done = False
        self.intro_phase = "veil"
        self.intro_snake_length = 10
        self.intro_veil_snakes: list[Snake] = []
        self.intro_veil_steps = 0
        self.intro_veil_total_steps = 0
        self.intro_hero_target_x = 0
        self.intro_hero_row = 0
        self.intro_hero_done = False
        self.intro_snake: Snake | None = None
        self.intro_last_frame_ms: int | None = None
        self.intro_move_accumulator_ms = 0.0
        self.intro_move_interval_ms = 62
        self._reset_intro_sequence()

    def start_level(self):
        """Set up a fresh level layout with increasing gate spacing."""
        self.level_start_points = self.points
        self.level_start_time_ms = self.elapsed_time_ms
        self.snake = Snake(grid_pos=(5, 5))
        self.food = Food()
        if not self.layout_ready:
            self.build_walls()
        self.layout_ready = False
        self._place_snake_for_level()
        self.place_gate_elements()
        self.spawn_food()
        self.level_food_eaten = 0
        self.sacrifice_ammo = 0
        self.loading_active = False
        self.loading_start_ms = None
        self.loading_tiles = []
        self.loading_reveal_count = 0
        self.last_frame_ms = None
        self.move_accumulator_ms = 0.0
        self.sacrifice_shot_active = False
        self.sacrifice_explosions.clear()
        self.level_clear = False
        self.game_paused = False
        self.story_active = False
        self.input_locked = False
        self.queued_direction = None
        self.side_scroller_active = False
        self.escape_wall_open = False
        self.starfield = []
        self.side_scroller_food_eaten = 0
        self.space_fade = 0.0
        self.space_fade_time_ms = 0.0
        self.space_fade_active = False
        self.player_shots.clear()
        self.boss_bullets.clear()
        self.boss_active = False
        self.boss_hp = 0
        self.boss_state = "hidden"
        self.boss_fire_timer_ms = 0.0

    def _place_snake_for_level(self):
        if not self.snake:
            return

        if self._in_sacrifice_levels():
            self._place_snake_in_sacrifice_start()
            return

        if self.playable_cells:
            candidates = [pos for pos in self.playable_cells if pos not in self.wall_positions]
        else:
            candidates = [
                (x, y)
                for x in range(GRID_WIDTH)
                for y in range(GRID_HEIGHT)
                if (x, y) not in self.wall_positions
            ]

        if not candidates:
            return

        spawn = self._choose_spawn_position(candidates, min_wall_gap=8)
        self.snake.segments = [spawn]
        self.snake.reset_interpolation()

    def _choose_spawn_position(
        self,
        candidates: list[tuple[int, int]],
        min_wall_gap: int,
    ) -> tuple[int, int]:
        safe_cells: list[tuple[int, int]] = []
        best_cell = candidates[0]
        best_distance = -1
        for cell in candidates:
            distance = self._distance_to_nearest_wall(cell)
            if distance >= min_wall_gap:
                safe_cells.append(cell)
            if distance > best_distance:
                best_distance = distance
                best_cell = cell

        if safe_cells:
            return random.choice(safe_cells)

        return best_cell

    def _distance_to_nearest_wall(self, cell: tuple[int, int]) -> int:
        if not self.wall_positions:
            x, y = cell
            return min(x, y, GRID_WIDTH - 1 - x, GRID_HEIGHT - 1 - y)

        return min(
            abs(cell[0] - wall[0]) + abs(cell[1] - wall[1])
            for wall in self.wall_positions
        )


    def start_game(self):
        """Begin a new run from the start screen."""
        self.level = 1
        self.points = 0
        self.game_started = True
        self.game_over = False
        self.elapsed_time_ms = 0
        self.name_input = ""
        self.score_recorded = False
        self.sacrifice_ammo = 0
        self.sacrifice_wall_open = False
        self.last_frame_ms = None
        self.move_accumulator_ms = 0.0
        self.input_locked = False
        self.queued_direction = None
        self.level_clear = False
        self.game_paused = False
        self.sacrifice_shot_active = False
        self.sacrifice_explosions.clear()
        self.side_scroller_active = False
        self.starfield = []
        self.side_scroller_food_eaten = 0
        self.space_fade = 0.0
        self.space_fade_time_ms = 0.0
        self.space_fade_active = False
        self.player_shots.clear()
        self.boss_bullets.clear()
        self.boss_active = False
        self.boss_hp = 0
        self.boss_state = "hidden"
        self.start_music()
        self.start_story(self.story_intro_text, "begin_loading")

    def replay_level(self):
        """Restart the current level from its checkpoint."""
        self.game_started = True
        self.game_over = False
        self.level_clear = False
        self.game_paused = False
        self.loading_active = False
        self.story_active = False
        self.story_text = ""
        self.story_next_action = ""
        self.name_input = ""
        self.score_recorded = False
        self.last_frame_ms = None
        self.move_accumulator_ms = 0.0
        self.input_locked = False
        self.queued_direction = None
        self.sacrifice_shot_active = False
        self.sacrifice_explosions.clear()
        self.side_scroller_active = False
        self.starfield = []
        self.player_shots.clear()
        self.boss_bullets.clear()
        self.boss_active = False
        self.boss_hp = 0
        self.points = self.level_start_points
        self.elapsed_time_ms = self.level_start_time_ms
        self.start_music()
        self.begin_loading()

    def start_story(self, text: str, next_action: str):
        self.story_active = True
        self.story_text = text
        self.story_next_action = next_action
        self.story_last_frame_ms = None
        self.story_move_accumulator_ms = 0.0
        self.last_frame_ms = None
        self._reset_story_snake()

    def complete_story(self):
        action = self.story_next_action
        self.story_active = False
        self.story_text = ""
        self.story_next_action = ""
        self.story_last_frame_ms = None
        self.story_move_accumulator_ms = 0.0
        if action == "begin_loading":
            self.begin_loading()
        elif action == "end_to_menu":
            self.exit_to_menu()

    def build_walls(self):
        """Create a neon wall outline that also serves as collision."""

        self.wall_positions = set()
        self.breakable_wall_positions = set()
        self.playable_cells = None
        self.sacrifice_playable_cells = None
        self.sacrifice_left_cells = None
        self.sacrifice_right_cells = None
        self.sacrifice_wall_open = False
        self.escape_wall_open = False

        if self._in_escape_level():
            self._build_escape_arena()
            return

        if self._in_sacrifice_levels():
            self._build_sacrifice_arena()
            return

        if self._in_tetris_levels():
            self.playable_cells = self._build_tetris_arena()
            for x in range(GRID_WIDTH):
                for y in range(GRID_HEIGHT):
                    if (x, y) not in self.playable_cells:
                        self.wall_positions.add((x, y))
            return

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
        if self._in_escape_level():
            self.button_pos = None
            self.key_pos = None
            return
        if self._in_sacrifice_levels():
            self._place_sacrifice_gate()
            return

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
        if self._in_sacrifice_levels() and self.sacrifice_playable_cells:
            candidates_set = self._sacrifice_spawn_candidates()
            candidates = list(candidates_set or self.sacrifice_playable_cells)
            random.shuffle(candidates)
            for candidate in candidates:
                if candidate in self.snake.segments:
                    continue
                if candidate == self.button_pos or candidate == self.key_pos:
                    continue
                if self._position_in_boss_area(candidate):
                    continue
                self.food.position = candidate
                return
            return

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
                if self._position_in_boss_area(candidate):
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
            if self._position_in_boss_area(candidate):
                continue
            self.food.position = candidate
            break

    def _sacrifice_spawn_candidates(self) -> set[tuple[int, int]] | None:
        if not self.sacrifice_playable_cells:
            return None
        if self.sacrifice_wall_open:
            return self.sacrifice_playable_cells
        if self.snake and self.snake.head in self.sacrifice_playable_cells:
            reachable = self._flood_fill_sacrifice(self.snake.head)
            if reachable:
                return reachable
        return self.sacrifice_left_cells or self.sacrifice_playable_cells

    def _flood_fill_sacrifice(self, start: tuple[int, int]) -> set[tuple[int, int]]:
        visited: set[tuple[int, int]] = set()
        if not self.sacrifice_playable_cells:
            return visited
        if start not in self.sacrifice_playable_cells:
            return visited
        queue: deque[tuple[int, int]] = deque([start])
        visited.add(start)
        while queue:
            x, y = queue.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                pos = (nx, ny)
                if pos in visited:
                    continue
                if pos not in self.sacrifice_playable_cells:
                    continue
                if pos in self.wall_positions:
                    continue
                visited.add(pos)
                queue.append(pos)
        return visited

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if self.game_over:
                    if not self.score_recorded:
                        if event.key == pygame.K_RETURN:
                            self.record_score()
                        elif event.key == pygame.K_SPACE:
                            self.record_score()
                            self.replay_level()
                        elif event.key == pygame.K_BACKSPACE:
                            self.name_input = self.name_input[:-1]
                        elif event.key == pygame.K_ESCAPE:
                            self.stop_music()
                            self.running = False
                        else:
                            if event.unicode and event.unicode.isalnum():
                                if len(self.name_input) < self.name_max_length:
                                    self.name_input += event.unicode
                    else:
                        if event.key == pygame.K_SPACE:
                            self.replay_level()
                        elif event.key == pygame.K_ESCAPE:
                            self.stop_music()
                            self.running = False
                    continue

                if event.key == pygame.K_q:
                    self.jump_to_final_boss()
                    continue

                if not self.game_started and self.menu_page == "main" and self.intro_active:
                    self.intro_active = False
                    self.intro_done = True
                    self._place_intro_hero()
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
                            self.settings_index = (self.settings_index - 1) % 3
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.settings_index = (self.settings_index + 1) % 3
                        elif event.key in (pygame.K_LEFT, pygame.K_a):
                            if self.settings_index == 0:
                                self.speed_index = (self.speed_index - 1) % len(self.speed_options)
                                self.speed_multiplier = self.speed_options[self.speed_index][1]
                            elif self.settings_index == 1:
                                self.sound_on = not self.sound_on
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            if self.settings_index == 0:
                                self.speed_index = (self.speed_index + 1) % len(self.speed_options)
                                self.speed_multiplier = self.speed_options[self.speed_index][1]
                            elif self.settings_index == 1:
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
                            elif self.settings_index == 2:
                                self.menu_page = "leaderboard"
                        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                            self.menu_page = "main"
                            continue
                    elif self.menu_page == "leaderboard":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_SPACE):
                            self.menu_page = "settings"
                elif self.game_started:
                    if event.key == pygame.K_n:
                        self.skip_level()
                        continue
                    if self.story_active:
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.complete_story()
                        elif event.key == pygame.K_ESCAPE:
                            self.exit_to_menu()
                        continue
                    if self.level_clear:
                        if event.key == pygame.K_SPACE:
                            if self.level == self.last_normal_level:
                                self.level += 1
                                self.level_clear = False
                                self.start_story(self.story_mid_text, "begin_loading")
                            elif self.level == self.last_tetris_level:
                                self.level = self.first_sacrifice_level
                                self.level_clear = False
                                self.start_story(self.story_end_text, "begin_loading")
                            elif self.level == self.last_sacrifice_level:
                                self.level += 1
                                self.level_clear = False
                                self.begin_loading()
                            elif self.level == self.escape_level:
                                self.level_clear = False
                                self.start_story(self.story_final_text, "end_to_menu")
                            else:
                                self.level += 1
                                self.level_clear = False
                                self.begin_loading()
                        elif event.key == pygame.K_ESCAPE:
                            self.stop_music()
                            self.running = False
                        continue
                    if self.game_paused:
                        if event.key == pygame.K_RETURN:
                            self.game_paused = False
                            self.last_frame_ms = pygame.time.get_ticks()
                        elif event.key == pygame.K_ESCAPE:
                            self.exit_to_menu()
                        continue
                    if not self.loading_active:
                        if event.key == pygame.K_RETURN:
                            self.game_paused = True
                            self.last_frame_ms = pygame.time.get_ticks()
                            continue
                        if event.key == pygame.K_s and self._can_shoot():
                            self.shoot_sacrifice()
                            continue
                        if event.key == pygame.K_n:
                            self.complete_level()
                            continue
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.queue_direction((0, -1))
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.queue_direction((0, 1))
                        elif event.key in (pygame.K_LEFT, pygame.K_a):
                            self.queue_direction((-1, 0))
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.queue_direction((1, 0))
                    if event.key == pygame.K_ESCAPE:
                        self.stop_music()
                        self.running = False
                if not self.game_started and self.menu_page == "main" and event.key == pygame.K_ESCAPE:
                    self.stop_music()
                    self.running = False

    def update(self):
        if not self.game_started:
            if self.intro_active:
                self.update_intro()
            return
        if self.game_over or self.level_clear:
            return
        if self.story_active:
            self.update_story()
            return
        if self.game_paused:
            self.last_frame_ms = pygame.time.get_ticks()
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

        if self.side_scroller_active:
            self.update_side_scroller(dt_ms)
            return

        move_interval_ms = 1000 / max(1e-6, FPS * self.speed_multiplier)
        self.move_accumulator_ms += dt_ms
        self._update_sacrifice_shot(dt_ms)
        updates = 0
        max_updates = 5
        while self.move_accumulator_ms >= move_interval_ms and not self.game_over:
            self.move_accumulator_ms -= move_interval_ms
            self.snake.update()
            self.elapsed_time_ms += move_interval_ms
            self.input_locked = False
            if self.queued_direction:
                if self._direction_valid(self.queued_direction, self.snake.direction):
                    self.snake.set_direction(self.queued_direction)
                self.queued_direction = None
            self.check_collisions()
            self.check_food_eaten()
            self.check_key_reached()
            self._check_escape_transition()
            updates += 1
            if updates >= max_updates:
                self.move_accumulator_ms = 0.0
                break

    def update_story(self):
        now_ms = pygame.time.get_ticks()
        if self.story_last_frame_ms is None:
            self.story_last_frame_ms = now_ms
        dt_ms = now_ms - self.story_last_frame_ms
        self.story_last_frame_ms = now_ms
        dt_ms = min(dt_ms, 200)
        dt_ms = min(dt_ms, self.story_move_interval_ms)

        self.story_move_accumulator_ms += dt_ms
        updates = 0
        max_updates = 4
        while self.story_move_accumulator_ms >= self.story_move_interval_ms:
            self.story_move_accumulator_ms -= self.story_move_interval_ms
            self._advance_story_snake()
            updates += 1
            if updates >= max_updates:
                self.story_move_accumulator_ms = 0.0
                break

    def update_intro(self):
        now_ms = pygame.time.get_ticks()
        if self.intro_last_frame_ms is None:
            self.intro_last_frame_ms = now_ms
        dt_ms = now_ms - self.intro_last_frame_ms
        self.intro_last_frame_ms = now_ms
        dt_ms = min(dt_ms, 200)
        dt_ms = min(dt_ms, self.intro_move_interval_ms)

        self.intro_move_accumulator_ms += dt_ms
        updates = 0
        max_updates = 4
        while self.intro_move_accumulator_ms >= self.intro_move_interval_ms:
            self.intro_move_accumulator_ms -= self.intro_move_interval_ms
            if self.intro_phase == "veil":
                self._advance_intro_veil()
            else:
                self._advance_intro_hero()
            updates += 1
            if updates >= max_updates:
                self.intro_move_accumulator_ms = 0.0
                break

    def update_side_scroller(self, dt_ms: float):
        if not self.snake:
            return

        self._update_starfield(dt_ms)
        self._update_space_fade(dt_ms)
        self._update_boss(dt_ms)
        self._update_player_shots(dt_ms)
        if not self.side_scroller_active:
            return
        self._update_boss_bullets(dt_ms)

        move_interval_ms = 1000 / max(1e-6, FPS * self.speed_multiplier)
        self.move_accumulator_ms += dt_ms
        updates = 0
        max_updates = 5
        while self.move_accumulator_ms >= move_interval_ms and not self.game_over:
            self.move_accumulator_ms -= move_interval_ms
            self.elapsed_time_ms += move_interval_ms
            self.input_locked = False
            if self.queued_direction:
                if self._direction_valid(self.queued_direction, self.snake.direction):
                    self.snake.set_direction(self.queued_direction)
                self.queued_direction = None

            head_x, _ = self.snake.head
            if self.snake.pending_direction == (-1, 0) and head_x <= self.side_scroller_left_lock:
                updates += 1
                if updates >= max_updates:
                    self.move_accumulator_ms = 0.0
                continue

            self.snake.update()
            self._apply_side_scroller_bounds()
            self.check_food_eaten()
            updates += 1
            if updates >= max_updates:
                self.move_accumulator_ms = 0.0
                break

        self._check_side_scroller_collisions()

    def _apply_side_scroller_bounds(self):
        if not self.snake:
            return
        head_x, head_y = self.snake.head
        original = (head_x, head_y)
        if head_y < 0:
            head_y = GRID_HEIGHT - 1
        elif head_y >= GRID_HEIGHT:
            head_y = 0
        if head_x < self.side_scroller_left_lock:
            head_x = self.side_scroller_left_lock
        if head_x >= GRID_WIDTH:
            head_x = GRID_WIDTH - 1
        if (head_x, head_y) != original:
            self.snake.segments[0] = (head_x, head_y)
            self.snake.reset_interpolation()

    def _check_escape_transition(self):
        if not self._in_escape_level() or self.side_scroller_active:
            return
        if not self.snake:
            return
        head_x, head_y = self.snake.head
        if head_x == GRID_WIDTH - 1 and (head_x, head_y) not in self.wall_positions:
            self.enter_side_scroller(head_y)

    def enter_side_scroller(self, entry_row: int | None = None):
        if not self.snake:
            return
        self.side_scroller_active = True
        self.wall_positions.clear()
        self.breakable_wall_positions.clear()
        self.button_pos = None
        self.key_pos = None
        self.playable_cells = None
        self.sacrifice_shot_active = False
        self.sacrifice_explosions.clear()
        self.player_shots.clear()
        self.boss_bullets.clear()
        self.side_scroller_food_eaten = 0
        self.space_fade = 0.0
        self.space_fade_time_ms = 0.0
        self.space_fade_active = False
        self._reset_starfield()
        self._init_boss()

        length = max(1, len(self.snake.segments))
        y = entry_row if entry_row is not None else self.snake.head[1]
        y = max(0, min(GRID_HEIGHT - 1, y))
        head_x = min(GRID_WIDTH - 2, self.side_scroller_left_lock + max(0, length - 1))
        positions = [(head_x - i, y) for i in range(length)]
        self.snake.segments = positions
        self.snake.direction = (1, 0)
        self.snake.pending_direction = (1, 0)
        self.snake.reset_interpolation()
        self.spawn_food()
        self.last_frame_ms = pygame.time.get_ticks()
        self.move_accumulator_ms = 0.0
        self.input_locked = False
        self.queued_direction = None

    def _reset_starfield(self):
        self.starfield = []
        for _ in range(self.star_count):
            self.starfield.append(
                {
                    "x": random.uniform(0, SCREEN_WIDTH),
                    "y": random.uniform(HUD_HEIGHT, SCREEN_HEIGHT),
                    "speed": random.uniform(*self.star_speed_range),
                    "size": random.randint(1, 3),
                    "glow": random.randint(160, 255),
                }
            )

    def _update_starfield(self, dt_ms: float):
        if not self.starfield:
            return
        dt_sec = max(0.0, dt_ms / 1000.0)
        for star in self.starfield:
            star["x"] -= star["speed"] * dt_sec
            if star["x"] < -4:
                star["x"] = SCREEN_WIDTH + random.uniform(0, SCREEN_WIDTH * 0.2)
                star["y"] = random.uniform(HUD_HEIGHT, SCREEN_HEIGHT)
                star["speed"] = random.uniform(*self.star_speed_range)
                star["size"] = random.randint(1, 3)
                star["glow"] = random.randint(160, 255)
            elif random.random() < 0.02:
                star["glow"] = random.randint(160, 255)

    def _update_space_fade(self, dt_ms: float):
        if not self.snake:
            return
        if self.boss_state == "hidden" and not self.space_fade_active:
            head_x, _ = self.snake.head
            if (
                self.side_scroller_food_eaten >= self.side_scroller_food_needed
                and head_x >= self.side_scroller_trigger_x
            ):
                self.space_fade_active = True

        if not self.space_fade_active:
            return

        self.space_fade_time_ms += dt_ms
        self.space_fade = min(1.0, self.space_fade_time_ms / max(1.0, self.space_fade_duration_ms))
        if self.space_fade >= 1.0 and self.boss_state == "hidden":
            self._start_boss_approach()

    def _init_boss(self):
        boss_y = max(1, (GRID_HEIGHT - self.boss_height) // 2)
        self.boss_pos = (GRID_WIDTH + 2, float(boss_y))
        self.boss_dir = 1
        self.boss_fire_timer_ms = 0.0
        self.boss_target_x = GRID_WIDTH - self.boss_width - 2
        self.boss_hp = 10
        self.boss_active = False
        self.boss_state = "hidden"

    def _start_boss_approach(self):
        boss_y = max(1, (GRID_HEIGHT - self.boss_height) // 2)
        self.boss_pos = (GRID_WIDTH + 2, float(boss_y))
        self.boss_dir = 1
        self.boss_fire_timer_ms = 0.0
        self.boss_hp = 10
        self.boss_active = True
        self.boss_state = "approach"

    def _update_boss(self, dt_ms: float):
        if self.boss_state == "hidden":
            return
        dt_sec = max(0.0, dt_ms / 1000.0)
        boss_x, boss_y = self.boss_pos
        if self.boss_state == "approach":
            boss_x -= self.boss_approach_speed * dt_sec
            if boss_x <= self.boss_target_x:
                boss_x = self.boss_target_x
                self.boss_state = "active"
            self.boss_pos = (boss_x, boss_y)
            return

        if self.boss_state != "active":
            return

        boss_y += self.boss_dir * self.boss_speed * dt_sec
        min_y = 1
        max_y = GRID_HEIGHT - self.boss_height - 1
        if boss_y <= min_y:
            boss_y = min_y
            self.boss_dir = 1
        elif boss_y >= max_y:
            boss_y = max_y
            self.boss_dir = -1
        self.boss_pos = (boss_x, boss_y)

        self.boss_fire_timer_ms += dt_ms
        if self.boss_fire_timer_ms >= self.boss_fire_interval_ms:
            self.boss_fire_timer_ms = 0.0
            self._fire_boss_bullet()

    def _fire_boss_bullet(self):
        if not self.boss_active:
            return
        boss_x, boss_y = self.boss_pos
        center_x = boss_x + self.boss_width * 0.5
        center_y = boss_y + self.boss_height * 0.5
        self.boss_bullets.append(
            {
                "x": center_x,
                "y": center_y,
                "vx": -1.0,
                "vy": 0.0,
            }
        )

    def _update_player_shots(self, dt_ms: float):
        if not self.player_shots:
            return
        dt_sec = max(0.0, dt_ms / 1000.0)
        remaining: list[dict] = []
        for shot in self.player_shots:
            shot["x"] += shot["vx"] * self.player_shot_speed * dt_sec
            shot["y"] += shot["vy"] * self.player_shot_speed * dt_sec
            if shot["x"] > GRID_WIDTH + 1 or shot["x"] < -2:
                continue
            if shot["y"] > GRID_HEIGHT + 1 or shot["y"] < -2:
                continue
            if self.boss_active and self._shot_hits_boss(shot["x"], shot["y"]):
                self.boss_hp -= 1
                if self.boss_hp <= 0:
                    self._finish_boss()
                    return
                continue
            remaining.append(shot)
        self.player_shots = remaining

    def _update_boss_bullets(self, dt_ms: float):
        if self.boss_state != "active":
            return
        if not self.boss_bullets:
            return
        dt_sec = max(0.0, dt_ms / 1000.0)
        remaining: list[dict] = []
        for bullet in self.boss_bullets:
            bullet["x"] += bullet["vx"] * self.boss_bullet_speed * dt_sec
            bullet["y"] += bullet["vy"] * self.boss_bullet_speed * dt_sec
            if bullet["x"] < -2 or bullet["x"] > GRID_WIDTH + 2:
                continue
            if bullet["y"] < -2 or bullet["y"] > GRID_HEIGHT + 2:
                continue
            remaining.append(bullet)
        self.boss_bullets = remaining

    def _shot_hits_boss(self, shot_x: float, shot_y: float) -> bool:
        bx, by, bw, bh = self._boss_rect_cells()
        return bx <= shot_x < bx + bw and by <= shot_y < by + bh

    def _boss_rect_cells(self) -> tuple[int, int, int, int]:
        boss_x, boss_y = self.boss_pos
        return int(boss_x), int(boss_y), self.boss_width, self.boss_height

    def _boss_contact_hitbox_cells(self) -> tuple[float, float, float, float]:
        boss_x, boss_y = self.boss_pos
        inset = 0.2
        width = max(0.1, self.boss_width - inset * 2)
        height = max(0.1, self.boss_height - inset * 2)
        return boss_x + inset, boss_y + inset, width, height

    def _check_side_scroller_collisions(self):
        if not self.snake:
            return
        head_x, head_y = self.snake.head
        if self.boss_active:
            bx, by, bw, bh = self._boss_contact_hitbox_cells()
            if bx <= head_x < bx + bw and by <= head_y < by + bh:
                self.play_sound("death")
                self.game_over = True
                self.game_started = False
                self.game_paused = False
                self.stop_music()
                return

        if not self.boss_bullets:
            return
        for bullet in self.boss_bullets:
            for seg in self.snake.segments:
                if abs((seg[0] + 0.5) - bullet["x"]) <= 0.4 and abs((seg[1] + 0.5) - bullet["y"]) <= 0.4:
                    self.play_sound("death")
                    self.game_over = True
                    self.game_started = False
                    self.game_paused = False
                    self.stop_music()
                    return

    def _finish_boss(self):
        self.boss_active = False
        self.boss_state = "defeated"
        self.side_scroller_active = False
        self.player_shots.clear()
        self.boss_bullets.clear()
        self.start_story(self.story_final_text, "end_to_menu")

    def _position_in_boss_area(self, pos: tuple[int, int]) -> bool:
        if not self.boss_active:
            return False
        x, y = pos
        bx, by, bw, bh = self._boss_rect_cells()
        return bx <= x < bx + bw and by <= y < by + bh

    def check_collisions(self):
        head_x, head_y = self.snake.head

        if self.side_scroller_active:
            self._check_side_scroller_collisions()
            return

        if self._in_sacrifice_levels():
            if not self.sacrifice_playable_cells or (head_x, head_y) not in self.sacrifice_playable_cells:
                self.play_sound("death")
                self.game_over = True
                self.game_started = False
                self.game_paused = False
                self.stop_music()
            return

        # Wall collision ends game
        if head_x < 0 or head_x >= GRID_WIDTH or head_y < 0 or head_y >= GRID_HEIGHT:
            self.play_sound("death")
            self.game_over = True
            self.game_started = False
            self.game_paused = False
            self.stop_music()
            return

        if (head_x, head_y) in self.wall_positions:
            self.play_sound("death")
            self.game_over = True
            self.game_started = False
            self.game_paused = False
            self.stop_music()
            return

        # TODO: self-collision later

    def check_food_eaten(self):
        if self.snake.head == self.food.position:
            self.snake.grow(1)
            self.points += 1
            self.level_food_eaten += 1
            self.sacrifice_ammo += 1
            if self.side_scroller_active:
                self.side_scroller_food_eaten += 1
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

    def skip_level(self):
        if self.game_over:
            return
        if self.story_active:
            self.complete_story()
            return
        if self.level_clear:
            if self.level == self.last_normal_level:
                self.level += 1
                self.level_clear = False
                self.start_story(self.story_mid_text, "begin_loading")
            elif self.level == self.last_tetris_level:
                self.level = self.first_sacrifice_level
                self.level_clear = False
                self.start_story(self.story_end_text, "begin_loading")
            elif self.level == self.last_sacrifice_level:
                self.level += 1
                self.level_clear = False
                self.begin_loading()
            elif self.level == self.escape_level:
                self.level_clear = False
                self.start_story(self.story_final_text, "end_to_menu")
            else:
                self.level += 1
                self.level_clear = False
                self.begin_loading()
            return
        if self.loading_active:
            self.loading_active = False
            self.start_level()
            return
        if self.game_paused:
            self.game_paused = False
        if self.game_started:
            self.complete_level()

    def jump_to_final_boss(self):
        """Debug helper: jump straight to the final boss fight."""
        self.game_started = True
        self.game_over = False
        self.level_clear = False
        self.loading_active = False
        self.story_active = False
        self.story_text = ""
        self.story_next_action = ""
        self.game_paused = False
        self.menu_page = "main"
        self.intro_active = False
        self.intro_done = True
        self.input_locked = False
        self.queued_direction = None
        self.sacrifice_shot_active = False
        self.sacrifice_explosions.clear()
        self.side_scroller_active = False
        self.player_shots.clear()
        self.boss_bullets.clear()
        self.boss_active = False
        self.boss_hp = 0
        self.boss_state = "hidden"
        self.space_fade = 0.0
        self.space_fade_time_ms = 0.0
        self.space_fade_active = False
        self.starfield = []

        self.start_music()
        self.level = self.escape_level
        self.level_start_points = self.points
        self.level_start_time_ms = self.elapsed_time_ms
        self.layout_ready = False
        self.start_level()
        self.enter_side_scroller()
        self.sacrifice_ammo = max(self.sacrifice_ammo, 10)
        self.space_fade = 1.0
        self._start_boss_approach()
        self.spawn_food()

    def draw(self):
        if self.game_over:
            self.draw_game_over()
        elif not self.game_started:
            if self.menu_page == "settings":
                self.draw_settings_screen()
            elif self.menu_page == "leaderboard":
                self.draw_leaderboard_screen()
            else:
                self.draw_start_screen()
        elif self.story_active:
            self.draw_story_screen()
        elif self.level_clear:
            self.draw_level_clear()
        elif self.loading_active:
            self.draw_loading_screen()
        elif self.game_paused:
            self.draw_pause_screen()
        elif self.side_scroller_active:
            self.draw_side_scroller()
        else:
            self.draw_playfield()
            pygame.display.flip()

    def draw_playfield(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.background, (0, HUD_HEIGHT))
        draw_grid(self.screen, offset_y=HUD_HEIGHT)
        self.draw_walls()
        self.draw_sacrifice_effects()

        if self.food:
            self.food.draw(self.screen, HUD_HEIGHT)
        self.draw_button()
        self.draw_key()
        move_interval_ms = 1000 / max(1e-6, FPS * self.speed_multiplier)
        alpha = 0.0
        if move_interval_ms > 0:
            alpha = min(1.0, max(0.0, self.move_accumulator_ms / move_interval_ms))
        if self.snake:
            self.snake.draw(self.screen, HUD_HEIGHT, alpha=alpha)

        self.draw_hud_band()
        self.draw_hud()

    def draw_side_scroller(self, flip: bool = True):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.background, (0, HUD_HEIGHT))
        if self.space_fade > 0.0:
            overlay = pygame.Surface((SCREEN_WIDTH, PLAYFIELD_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(255 * min(1.0, self.space_fade))))
            self.screen.blit(overlay, (0, HUD_HEIGHT))
        self._draw_starfield()

        if self.food:
            self.food.draw(self.screen, HUD_HEIGHT)
        self._draw_boss()
        move_interval_ms = 1000 / max(1e-6, FPS * self.speed_multiplier)
        alpha = 0.0
        if move_interval_ms > 0:
            alpha = min(1.0, max(0.0, self.move_accumulator_ms / move_interval_ms))
        if self.snake:
            self.snake.draw(self.screen, HUD_HEIGHT, alpha=alpha)
        self._draw_player_shots()
        self._draw_boss_bullets()

        self.draw_hud_band()
        self.draw_hud()
        if flip:
            pygame.display.flip()

    def _build_boss_sprite(self) -> pygame.Surface | None:
        size = (self.boss_width * TILE_SIZE, self.boss_height * TILE_SIZE)
        image = load_scaled_image("head.png", size)
        if image is None:
            return None
        mask = pygame.Surface(size, pygame.SRCALPHA)
        radius = max(6, int(min(size) * 0.22))
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
        rounded = image.copy()
        rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return pygame.transform.flip(rounded, True, False)

    def draw_pause_screen(self):
        if self.side_scroller_active:
            self.draw_side_scroller(flip=False)
        else:
            self.draw_playfield()

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        title_text = self.game_font.render("Game Paused", True, COLOR_HUD)
        prompt_text = self.game_font.render("Press ENTER to begin", True, COLOR_HUD)
        esc_text = self.game_font.render("ESC to go to main screen", True, COLOR_HUD)

        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 18))
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        esc_rect = esc_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 36))
        self.screen.blit(title_text, title_rect)
        self.screen.blit(prompt_text, prompt_rect)
        self.screen.blit(esc_text, esc_rect)
        pygame.display.flip()

    def _draw_starfield(self):
        if not self.starfield:
            return
        for star in self.starfield:
            glow = int(star["glow"])
            color = (glow, glow, min(255, glow + 40))
            pygame.draw.circle(
                self.screen,
                color,
                (int(star["x"]), int(star["y"])),
                int(star["size"]),
            )

    def _draw_player_shots(self):
        if not self.player_shots:
            return
        for shot in self.player_shots:
            center = (
                int(shot["x"] * TILE_SIZE),
                int(shot["y"] * TILE_SIZE + HUD_HEIGHT),
            )
            pygame.draw.circle(self.screen, COLOR_SNAKE, center, self.player_shot_radius)

    def _draw_boss_bullets(self):
        if not self.boss_bullets:
            return
        for bullet in self.boss_bullets:
            center = (
                int(bullet["x"] * TILE_SIZE),
                int(bullet["y"] * TILE_SIZE + HUD_HEIGHT),
            )
            pygame.draw.circle(self.screen, (240, 80, 80), center, self.boss_bullet_radius)

    def _draw_boss(self):
        if not self.boss_active:
            return
        rect = self._boss_rect_pixels()
        if self.boss_sprite:
            self.screen.blit(self.boss_sprite, rect.topleft)
        else:
            pygame.draw.rect(self.screen, (220, 70, 90), rect, border_radius=8)

        if self.boss_hp > 0:
            hp_ratio = max(0.0, min(1.0, self.boss_hp / 10))
            bar_height = max(4, TILE_SIZE // 5)
            bar_rect = pygame.Rect(rect.left, rect.top - bar_height - 4, rect.width, bar_height)
            pygame.draw.rect(self.screen, (40, 20, 30), bar_rect, border_radius=4)
            fill_rect = pygame.Rect(bar_rect.left, bar_rect.top, int(bar_rect.width * hp_ratio), bar_rect.height)
            pygame.draw.rect(self.screen, (255, 120, 120), fill_rect, border_radius=4)

    def _boss_rect_pixels(self) -> pygame.Rect:
        boss_x, boss_y = self.boss_pos
        return pygame.Rect(
            int(boss_x * TILE_SIZE),
            int(boss_y * TILE_SIZE + HUD_HEIGHT),
            self.boss_width * TILE_SIZE,
            self.boss_height * TILE_SIZE,
        )

    def draw_story_screen(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.background, (0, HUD_HEIGHT))
        draw_grid(self.screen, offset_y=HUD_HEIGHT)

        if self.story_snake:
            alpha = self._movement_alpha(
                self.story_move_accumulator_ms,
                self.story_move_interval_ms,
            )
            self.story_snake.draw(self.screen, HUD_HEIGHT, alpha=alpha)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        box_width = int(SCREEN_WIDTH * 0.7)
        box_height = 120
        box_rect = pygame.Rect(0, 0, box_width, box_height)
        box_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10)
        pygame.draw.rect(self.screen, (0, 0, 0), box_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_WALL, box_rect, width=2, border_radius=8)

        title_text = self.game_title_font.render(self.story_text, True, COLOR_HUD)
        title_rect = title_text.get_rect(center=box_rect.center)
        self.screen.blit(title_text, title_rect)

        prompt_text = self.game_font.render("Press ENTER or SPACE to continue", True, COLOR_HUD)
        esc_text = self.game_font.render("ESC to go to main menu", True, COLOR_HUD)
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, box_rect.bottom + 24))
        esc_rect = esc_text.get_rect(center=(SCREEN_WIDTH // 2, box_rect.bottom + 48))
        self.screen.blit(prompt_text, prompt_rect)
        self.screen.blit(esc_text, esc_rect)
        pygame.display.flip()

    def draw_intro_screen(self):
        if self.start_bg:
            self.screen.blit(self.start_bg, (0, 0))
        else:
            self.screen.blit(self.menu_background, (0, 0))

        fade = self._intro_fade_progress()
        if self.start_bg_alt and fade > 0.0:
            alpha = int(255 * fade)
            self.start_bg_alt.set_alpha(alpha)
            self.screen.blit(self.start_bg_alt, (0, 0))
            self.start_bg_alt.set_alpha(255)

        intro_alpha = self._movement_alpha(
            self.intro_move_accumulator_ms,
            self.intro_move_interval_ms,
        )
        if self.intro_phase == "veil":
            for snake in self.intro_veil_snakes:
                snake.draw(self.screen, 0, alpha=intro_alpha)
        else:
            if self.intro_hero_done:
                intro_alpha = 0.0
            if self.intro_snake:
                self.intro_snake.draw(self.screen, 0, alpha=intro_alpha)

        prompt_text = self.menu_prompt_font.render("Press any key to skip", True, COLOR_HUD)
        prompt_rect = prompt_text.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 18))
        self.screen.blit(prompt_text, prompt_rect)
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
            if (x, y) in self.breakable_wall_positions:
                pygame.draw.rect(self.screen, COLOR_WALL, rect)
            else:
                pygame.draw.rect(self.screen, COLOR_WALL, rect, width=2, border_radius=4)

    def _build_sacrifice_shot_images(self) -> dict[tuple[int, int], pygame.Surface]:
        size = self.sacrifice_shot_size
        corner = self.sacrifice_shot_corner
        base = load_scaled_image("segment.png", (size, size))
        if base is None:
            base = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(base, COLOR_SNAKE, base.get_rect(), border_radius=corner)
            return {
                (1, 0): base,
                (-1, 0): base,
                (0, -1): base,
                (0, 1): base,
            }

        rounded = base.copy()
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=corner)
        rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        images: dict[tuple[int, int], pygame.Surface] = {}
        for direction in ((1, 0), (-1, 0), (0, -1), (0, 1)):
            angle = self._direction_to_angle(direction)
            images[direction] = pygame.transform.rotate(rounded, angle) if angle else rounded
        return images

    def draw_sacrifice_effects(self):
        if not self._in_sacrifice_levels() and not self._in_escape_level():
            return

        if self.sacrifice_shot_active:
            x, y = self.sacrifice_shot_pos
            center_x = int(round(x * TILE_SIZE))
            center_y = int(round(y * TILE_SIZE + HUD_HEIGHT))
            dx, dy = self.sacrifice_shot_dir
            lead = int(TILE_SIZE * 0.35)
            center = (center_x + dx * lead, center_y + dy * lead)
            image = self.sacrifice_shot_images.get((dx, dy)) if self.sacrifice_shot_images else None
            if image:
                rect = image.get_rect(center=center)
                self.screen.blit(image, rect)
            else:
                pygame.draw.circle(self.screen, COLOR_SNAKE, center, self.sacrifice_shot_radius)

        if not self.sacrifice_explosions:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for explosion in self.sacrifice_explosions:
            elapsed = explosion["elapsed"]
            duration = max(1.0, explosion["duration"])
            progress = min(1.0, max(0.0, elapsed / duration))
            grid_x, grid_y = explosion["pos"]
            center = (
                grid_x * TILE_SIZE + TILE_SIZE // 2,
                grid_y * TILE_SIZE + HUD_HEIGHT + TILE_SIZE // 2,
            )
            radius = int(TILE_SIZE * (0.2 + 0.9 * progress))
            alpha = int(220 * (1.0 - progress))
            color = (255, 210, 120, alpha)
            pygame.draw.circle(overlay, color, center, radius, width=2)
            flash_radius = max(1, int(TILE_SIZE * 0.12 * (1.0 - progress)))
            if flash_radius > 0:
                pygame.draw.circle(overlay, (255, 255, 255, alpha), center, flash_radius)

        self.screen.blit(overlay, (0, 0))

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

    @staticmethod
    def _direction_to_angle(direction: tuple[int, int]) -> int:
        dx, dy = direction
        if dx == 1 and dy == 0:
            return 0
        if dx == -1 and dy == 0:
            return 180
        if dx == 0 and dy == -1:
            return 90
        if dx == 0 and dy == 1:
            return -90
        return 0

    @staticmethod
    def _ease_out_alpha(alpha: float) -> float:
        alpha = max(0.0, min(1.0, alpha))
        return 1.0 - (1.0 - alpha) * (1.0 - alpha)

    def _movement_alpha(self, accumulator_ms: float, interval_ms: float) -> float:
        if interval_ms <= 0:
            return 1.0
        raw = min(1.0, max(0.0, accumulator_ms / interval_ms))
        return raw

    def _direction_valid(self, new_dir: tuple[int, int], current_dir: tuple[int, int]) -> bool:
        cur_dx, cur_dy = current_dir
        new_dx, new_dy = new_dir
        if (cur_dx == -new_dx and cur_dx != 0) or (cur_dy == -new_dy and cur_dy != 0):
            return False
        return True

    def queue_direction(self, new_dir: tuple[int, int]):
        if not self.snake:
            return

        if not self.input_locked:
            if self._direction_valid(new_dir, self.snake.direction):
                self.snake.set_direction(new_dir)
                self.input_locked = True
                self.queued_direction = None
            return

        if self._direction_valid(new_dir, self.snake.pending_direction):
            self.queued_direction = new_dir

    def _can_shoot(self) -> bool:
        return self._in_sacrifice_levels() or self._in_escape_level() or self.side_scroller_active

    def required_food_for_level(self) -> int:
        if self.level == 1:
            return 2
        if self.level == 2:
            return 3
        return 5

    def _in_tetris_levels(self) -> bool:
        return self.first_tetris_level <= self.level <= self.last_tetris_level

    def _in_sacrifice_levels(self) -> bool:
        return self.first_sacrifice_level <= self.level <= self.last_sacrifice_level

    def _in_escape_level(self) -> bool:
        return self.level == self.escape_level

    def _build_escape_arena(self):
        self.playable_cells = None
        right_x = GRID_WIDTH - 1
        for x in range(GRID_WIDTH):
            self.wall_positions.add((x, 0))
            self.wall_positions.add((x, GRID_HEIGHT - 1))
        for y in range(GRID_HEIGHT):
            self.wall_positions.add((0, y))
            self.wall_positions.add((right_x, y))
            self.breakable_wall_positions.add((right_x, y))

    def _build_sacrifice_arena(self):
        level_index = max(0, self.level - self.first_sacrifice_level)
        base_width = max(12, (GRID_WIDTH - 3) // 2)
        base_height = max(12, GRID_HEIGHT - 4)
        box_width = max(8, base_width - level_index)
        box_height = max(8, base_height - level_index * 2)

        total_width = box_width * 2 - 1
        if total_width > GRID_WIDTH - 2:
            box_width = max(8, (GRID_WIDTH - 1) // 2)
            total_width = box_width * 2 - 1

        left_x = max(1, (GRID_WIDTH - total_width) // 2)
        top_y = max(1, (GRID_HEIGHT - box_height) // 2)
        right_x = left_x + box_width - 1

        self.sacrifice_left_cells = set()
        self.sacrifice_right_cells = set()

        for x in range(left_x + 1, left_x + box_width - 1):
            for y in range(top_y + 1, top_y + box_height - 1):
                self.sacrifice_left_cells.add((x, y))
        for x in range(right_x + 1, right_x + box_width - 1):
            for y in range(top_y + 1, top_y + box_height - 1):
                self.sacrifice_right_cells.add((x, y))

        self.sacrifice_playable_cells = set()
        self.sacrifice_playable_cells.update(self.sacrifice_left_cells)
        self.sacrifice_playable_cells.update(self.sacrifice_right_cells)

        # Left box perimeter
        for x in range(left_x, left_x + box_width):
            self.wall_positions.add((x, top_y))
            self.wall_positions.add((x, top_y + box_height - 1))
        for y in range(top_y, top_y + box_height):
            self.wall_positions.add((left_x, y))
            self.wall_positions.add((left_x + box_width - 1, y))

        # Right box perimeter (shares the middle wall)
        for x in range(right_x, right_x + box_width):
            self.wall_positions.add((x, top_y))
            self.wall_positions.add((x, top_y + box_height - 1))
        for y in range(top_y, top_y + box_height):
            self.wall_positions.add((right_x, y))
            self.wall_positions.add((right_x + box_width - 1, y))

        separator_x = right_x
        for y in range(top_y, top_y + box_height):
            pos = (separator_x, y)
            self.wall_positions.add(pos)
            self.breakable_wall_positions.add(pos)

    def _place_sacrifice_gate(self):
        if not self.sacrifice_right_cells:
            self.button_pos = None
            self.key_pos = None
            return

        candidates = list(self.sacrifice_right_cells)
        random.shuffle(candidates)
        button = None
        key = None
        for candidate in candidates:
            if candidate == self.snake.head:
                continue
            button = candidate
            break
        if button is None:
            button = self.snake.head
        for candidate in candidates:
            if candidate == button or candidate == self.snake.head:
                continue
            key = candidate
            break
        if key is None:
            key = button
        self.button_pos = button
        self.key_pos = key

    def _place_snake_in_sacrifice_start(self):
        if not self.sacrifice_left_cells or not self.snake:
            return
        candidates = [pos for pos in self.sacrifice_left_cells if pos not in self.wall_positions]
        if not candidates:
            candidates = list(self.sacrifice_left_cells)
        start_pos = self._choose_spawn_position(candidates, min_wall_gap=8)
        self.snake.segments = [start_pos]
        self.snake.direction = (1, 0)
        self.snake.pending_direction = (1, 0)
        self.snake.reset_interpolation()

    def shoot_sacrifice(self):
        if not self._can_shoot():
            return
        if self.sacrifice_ammo <= 0:
            return
        if not self.snake:
            return
        if len(self.snake.segments) <= 1:
            return

        if self.side_scroller_active:
            if self._fire_player_shot():
                self._consume_shot_ammo()
            return

        if self.sacrifice_shot_active:
            return

        dx, dy = self.snake.pending_direction
        if (dx, dy) == (0, 0):
            return

        head_x, head_y = self.snake.head
        x = head_x + dx
        y = head_y + dy
        hit_pos = None
        while 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            if (x, y) in self.wall_positions:
                hit_pos = (x, y)
                break
            x += dx
            y += dy

        if hit_pos is None:
            return

        self._start_sacrifice_shot(hit_pos, (dx, dy))
        self._consume_shot_ammo()

    def _consume_shot_ammo(self):
        if self.sacrifice_ammo <= 0 or not self.snake:
            return
        self.sacrifice_ammo -= 1
        if self.snake.grow_pending > 0:
            self.snake.grow_pending -= 1
        elif len(self.snake.segments) > 1:
            self.snake.segments.pop()

    def _fire_player_shot(self) -> bool:
        if not self.snake:
            return False
        if len(self.player_shots) >= self.player_shot_limit:
            return False
        head_x, head_y = self.snake.head
        dx, dy = self.snake.pending_direction
        if (dx, dy) == (0, 0):
            dx, dy = self.snake.direction
        if (dx, dy) == (0, 0):
            return False
        offset = 0.55
        self.player_shots.append(
            {
                "x": head_x + 0.5 + dx * offset,
                "y": head_y + 0.5 + dy * offset,
                "vx": float(dx),
                "vy": float(dy),
            }
        )
        return True

    def _start_sacrifice_shot(self, hit_pos: tuple[int, int], direction: tuple[int, int]):
        if not self.snake:
            return

        head_x, head_y = self.snake.head
        self.sacrifice_shot_active = True
        self.sacrifice_shot_dir = direction
        self.sacrifice_shot_pos = (head_x + 0.5, head_y + 0.5)
        self.sacrifice_shot_target_cell = hit_pos
        self.sacrifice_shot_target = (hit_pos[0] + 0.5, hit_pos[1] + 0.5)

    def _update_sacrifice_shot(self, dt_ms: float):
        if not self.sacrifice_shot_active and not self.sacrifice_explosions:
            return

        dt_sec = max(0.0, dt_ms / 1000.0)

        if self.sacrifice_shot_active:
            x, y = self.sacrifice_shot_pos
            dx, dy = self.sacrifice_shot_dir
            step = self.sacrifice_shot_speed * dt_sec
            prev_x, prev_y = x, y
            x += dx * step
            y += dy * step

            target_x, target_y = self.sacrifice_shot_target
            hit_radius = self.sacrifice_shot_hit_radius
            hit = False
            if dx != 0:
                hit_line = target_x - dx * hit_radius
                crossed = (dx > 0 and prev_x <= hit_line <= x) or (dx < 0 and prev_x >= hit_line >= x)
                if crossed and abs(y - target_y) <= hit_radius + 1e-6:
                    x = hit_line
                    hit = True
            elif dy != 0:
                hit_line = target_y - dy * hit_radius
                crossed = (dy > 0 and prev_y <= hit_line <= y) or (dy < 0 and prev_y >= hit_line >= y)
                if crossed and abs(x - target_x) <= hit_radius + 1e-6:
                    y = hit_line
                    hit = True

            if hit:
                self.sacrifice_shot_active = False
                self.sacrifice_explosions.append(
                    {"pos": self.sacrifice_shot_target_cell, "elapsed": 0.0, "duration": 260.0}
                )
                self._resolve_sacrifice_shot_hit()

            self.sacrifice_shot_pos = (x, y)

        if self.sacrifice_explosions:
            updated: list[dict] = []
            for explosion in self.sacrifice_explosions:
                explosion["elapsed"] += dt_ms
                if explosion["elapsed"] < explosion["duration"]:
                    updated.append(explosion)
            self.sacrifice_explosions = updated

    def _resolve_sacrifice_shot_hit(self):
        hit_pos = self.sacrifice_shot_target_cell
        if hit_pos in self.breakable_wall_positions:
            self.breakable_wall_positions.discard(hit_pos)
            self.wall_positions.discard(hit_pos)
            if self.sacrifice_playable_cells is not None:
                self.sacrifice_playable_cells.add(hit_pos)
            if self._in_sacrifice_levels():
                self.sacrifice_wall_open = True
            if self._in_escape_level():
                self.escape_wall_open = True

    def _build_story_path(self) -> list[tuple[int, int]]:
        margin = 2
        left = margin
        right = GRID_WIDTH - margin - 1
        top = margin
        bottom = GRID_HEIGHT - margin - 1
        if right <= left or bottom <= top:
            left = 1
            right = GRID_WIDTH - 2
            top = 1
            bottom = GRID_HEIGHT - 2

        path: list[tuple[int, int]] = []
        for x in range(left, right + 1):
            path.append((x, top))
        for y in range(top + 1, bottom + 1):
            path.append((right, y))
        for x in range(right - 1, left - 1, -1):
            path.append((x, bottom))
        for y in range(bottom - 1, top, -1):
            path.append((left, y))
        return path

    def _reset_story_snake(self):
        if not self.story_path:
            self.story_snake = Snake(grid_pos=(GRID_WIDTH // 2, GRID_HEIGHT // 2))
            self.story_snake_length = max(3, self.story_snake_length)
            if self.story_snake:
                self.story_snake.reset_interpolation()
            return

        self.story_path_index = 0
        positions: list[tuple[int, int]] = []
        for i in range(self.story_snake_length):
            idx = (self.story_path_index - i) % len(self.story_path)
            positions.append(self.story_path[idx])

        self.story_snake = Snake(grid_pos=positions[0])
        self.story_snake.segments = positions
        if len(positions) > 1:
            head_x, head_y = positions[0]
            next_x, next_y = positions[1]
            dx, dy = head_x - next_x, head_y - next_y
            self.story_snake.direction = (dx, dy)
            self.story_snake.pending_direction = (dx, dy)
        if self.story_snake:
            self.story_snake.reset_interpolation()

    def _advance_story_snake(self):
        if not self.story_snake or not self.story_path:
            return

        self.story_snake.prev_segments = list(self.story_snake.segments)
        self.story_snake.prev_direction = self.story_snake.direction

        self.story_path_index = (self.story_path_index + 1) % len(self.story_path)
        new_head = self.story_path[self.story_path_index]
        old_head = self.story_snake.segments[0]
        dx, dy = new_head[0] - old_head[0], new_head[1] - old_head[1]
        if (dx, dy) != (0, 0):
            self.story_snake.direction = (dx, dy)
            self.story_snake.pending_direction = (dx, dy)

        self.story_snake.segments.insert(0, new_head)
        if len(self.story_snake.segments) > self.story_snake_length:
            self.story_snake.segments.pop()

        if self.story_snake.head_frames:
            self.story_snake.anim_index = (self.story_snake.anim_index + 1) % len(
                self.story_snake.head_frames
            )
        self.story_snake.interp_ready = True

    def _reset_intro_sequence(self):
        self.intro_phase = "veil"
        self.intro_done = False
        self.intro_active = True
        self.intro_last_frame_ms = None
        self.intro_move_accumulator_ms = 0.0
        self.intro_veil_snakes = self._build_intro_veil()
        self.intro_veil_steps = 0
        self.intro_hero_done = False
        self.intro_snake = None

    def _intro_grid(self) -> tuple[int, int]:
        cols = max(1, SCREEN_WIDTH // TILE_SIZE)
        rows = max(1, SCREEN_HEIGHT // TILE_SIZE)
        return cols, rows

    def _build_intro_veil(self) -> list[Snake]:
        cols, rows = self._intro_grid()
        snakes: list[Snake] = []
        max_offset = 0
        max_length = 0
        for row in range(1, rows - 1, 2):
            length = 6 + (row % 5)
            offset = (row * 3) % 10
            start_x = -length - offset
            positions = [(start_x - i, row) for i in range(length)]
            snake = Snake(grid_pos=positions[0])
            snake.segments = positions
            snake.direction = (1, 0)
            snake.pending_direction = (1, 0)
            snake.reset_interpolation()
            snakes.append(snake)
            max_offset = max(max_offset, offset)
            max_length = max(max_length, length)

        extra_snakes = 40
        if rows > 2:
            for _ in range(extra_snakes):
                row = random.randint(1, rows - 2)
                length = random.randint(6, 10)
                offset = random.randint(0, 10)
                start_x = -length - offset
                positions = [(start_x - i, row) for i in range(length)]
                snake = Snake(grid_pos=positions[0])
                snake.segments = positions
                snake.direction = (1, 0)
                snake.pending_direction = (1, 0)
                snake.reset_interpolation()
                snakes.append(snake)
                max_offset = max(max_offset, offset)
                max_length = max(max_length, length)

        self.intro_veil_total_steps = cols + max_offset + max_length + 2
        return snakes

    def _advance_intro_veil(self):
        if not self.intro_veil_snakes:
            self._start_intro_hero()
            return

        self.intro_veil_steps += 1
        for snake in self.intro_veil_snakes:
            snake.update()

        if self.intro_veil_steps >= self.intro_veil_total_steps:
            self._start_intro_hero()

    def _start_intro_hero(self):
        self.intro_phase = "hero"
        cols, rows = self._intro_grid()
        base_row = min(rows - 3, max(2, int(rows * 0.62)))
        self.intro_hero_row = min(rows - 3, base_row + 1)
        length = max(6, self.intro_snake_length)
        target_x = max(3, int(cols * 0.5))
        target_x = min(target_x, max(3, cols - length - 2))
        target_x = max(3, target_x - length)
        self.intro_hero_target_x = target_x
        start_x = cols + length + 2
        positions = [(start_x - i, self.intro_hero_row) for i in range(length)]
        self.intro_snake = Snake(grid_pos=positions[0])
        self.intro_snake.segments = positions
        self.intro_snake.direction = (-1, 0)
        self.intro_snake.pending_direction = (-1, 0)
        self.intro_snake.reset_interpolation()
        self.intro_hero_done = False

    def _advance_intro_hero(self):
        if not self.intro_snake:
            return

        if self.intro_hero_done:
            if self.intro_snake.head_frames:
                self.intro_snake.anim_index = (self.intro_snake.anim_index + 1) % len(
                    self.intro_snake.head_frames
                )
            return

        head_x, _ = self.intro_snake.head
        if head_x <= self.intro_hero_target_x:
            self.intro_hero_done = True
            self.intro_snake.reset_interpolation()
            self.intro_active = False
            self.intro_done = True
            return

        self.intro_snake.pending_direction = (-1, 0)
        self.intro_snake.update()

    def _place_intro_hero(self):
        self.intro_phase = "hero"
        cols, rows = self._intro_grid()
        base_row = min(rows - 3, max(2, int(rows * 0.62)))
        self.intro_hero_row = min(rows - 3, base_row + 1)
        length = max(6, self.intro_snake_length)
        target_x = max(3, int(cols * 0.5))
        target_x = min(target_x, max(3, cols - length - 2))
        target_x = max(3, target_x - length)
        self.intro_hero_target_x = target_x
        positions = [(target_x + i, self.intro_hero_row) for i in range(length)]
        self.intro_snake = Snake(grid_pos=positions[0])
        self.intro_snake.segments = positions
        self.intro_snake.direction = (-1, 0)
        self.intro_snake.pending_direction = (-1, 0)
        self.intro_snake.reset_interpolation()
        self.intro_hero_done = True

    def _intro_fade_progress(self) -> float:
        if self.intro_phase == "veil" and self.intro_veil_total_steps > 0:
            progress = self.intro_veil_steps / max(1, self.intro_veil_total_steps)
            if progress <= 1.0 / 4.0:
                return 0.0
            return min(1.0, (progress - 1.0 / 4.0) / (3.0 / 4.0))
        return 1.0

    def _build_tetris_arena(self) -> set[tuple[int, int]]:
        """Create a full-arena Tetris-shaped playfield."""
        shape_index = (self.level - self.first_tetris_level) % len(self.TETRIS_SHAPES)
        _, base_shape = self.TETRIS_SHAPES[shape_index]

        max_x = max(p[0] for p in base_shape)
        max_y = max(p[1] for p in base_shape)
        max_scale_x = max(1, (GRID_WIDTH - 4) // (max_x + 1))
        max_scale_y = max(1, (GRID_HEIGHT - 4) // (max_y + 1))
        max_scale = min(max_scale_x, max_scale_y)
        if shape_index < 3:
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
        if not self._in_tetris_levels():
            return 0
        return (self.level - self.first_tetris_level) % 3

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

        if self.level <= self.last_normal_level:
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
        if self.intro_active:
            self.draw_intro_screen()
            return

        if self.intro_done and self.start_bg_alt:
            self.screen.blit(self.start_bg_alt, (0, 0))
        elif self.start_bg:
            self.screen.blit(self.start_bg, (0, 0))
        else:
            self.screen.blit(self.menu_background, (0, 0))

        if self.intro_done and self.intro_snake:
            self.intro_snake.draw(self.screen, 0, alpha=0.0)

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
        leaderboard_label = "Leaderboard"
        settings_labels = [speed_label, sound_label, leaderboard_label]
        base_y = SCREEN_HEIGHT // 2 - 20
        line_gap = 40
        for idx, label in enumerate(settings_labels):
            color = COLOR_SNAKE if idx == self.settings_index else COLOR_HUD
            option_text = self.menu_option_font.render(label, True, color)
            option_rect = option_text.get_rect(center=(SCREEN_WIDTH // 2, base_y + idx * line_gap))
            self.screen.blit(option_text, option_rect)

        prompt_text = self.menu_prompt_font.render("Press ENTER to open, ESC to return", True, COLOR_HUD)
        prompt_rect = prompt_text.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 28))
        self.screen.blit(prompt_text, prompt_rect)
        pygame.display.flip()

    def draw_leaderboard_screen(self):
        self.draw_menu_background()

        title_text = self.menu_title_font.render("Leaderboard", True, COLOR_HUD)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 140))
        self.screen.blit(title_text, title_rect)

        base_y = SCREEN_HEIGHT // 2 - 60
        line_gap = 34
        if self.leaderboard_entries:
            for idx, entry in enumerate(self.leaderboard_entries, start=1):
                name = entry.get("name", "Anon")
                score = entry.get("score", 0)
                label = f"{idx}. {name} - {score}"
                entry_text = self.menu_option_font.render(label, True, COLOR_HUD)
                entry_rect = entry_text.get_rect(center=(SCREEN_WIDTH // 2, base_y + (idx - 1) * line_gap))
                self.screen.blit(entry_text, entry_rect)
        else:
            empty_text = self.menu_option_font.render("No scores yet", True, COLOR_HUD)
            empty_rect = empty_text.get_rect(center=(SCREEN_WIDTH // 2, base_y))
            self.screen.blit(empty_text, empty_rect)

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
        if not self.score_recorded:
            prompt_label = "Replay level? SPACE | ENTER to save | ESC to exit"
        else:
            prompt_label = "Replay level? SPACE | ESC to exit"
        prompt_text = self.game_font.render(prompt_label, True, COLOR_HUD)

        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(title_text, title_rect)
        self.screen.blit(prompt_text, prompt_rect)

        if not self.score_recorded:
            name_display = self.name_input if self.name_input else "_"
            name_text = self.menu_option_font.render(f"Name: {name_display}", True, COLOR_HUD)
            name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
            self.screen.blit(name_text, name_rect)

            hint_text = self.menu_prompt_font.render(
                "Type your name, ENTER to save, SPACE to replay level",
                True,
                COLOR_HUD,
            )
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 92))
            self.screen.blit(hint_text, hint_rect)
        pygame.display.flip()

    def exit_to_menu(self):
        self.game_paused = False
        self.game_started = False
        self.game_over = False
        self.level_clear = False
        self.loading_active = False
        self.story_active = False
        self.side_scroller_active = False
        self.starfield = []
        self.side_scroller_food_eaten = 0
        self.space_fade = 0.0
        self.space_fade_time_ms = 0.0
        self.space_fade_active = False
        self.player_shots.clear()
        self.boss_bullets.clear()
        self.boss_active = False
        self.boss_hp = 0
        self.boss_state = "hidden"
        self.story_text = ""
        self.story_next_action = ""
        self.menu_page = "main"
        self.stop_music()

    def format_elapsed_time(self) -> str:
        total_seconds = max(0, int(self.elapsed_time_ms) // 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02}:{seconds:02}"

    def _load_leaderboard(self):
        try:
            if not self.leaderboard_path.exists():
                self.leaderboard_entries = []
                return
            payload = json.loads(self.leaderboard_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.leaderboard_entries = []
            return

        entries = None
        if isinstance(payload, dict):
            entries = payload.get("entries")
            if entries is None:
                entries = payload.get("scores")

        if not isinstance(entries, list):
            self.leaderboard_entries = []
            return

        self.leaderboard_entries = self._normalize_leaderboard(entries)

    def _save_leaderboard(self):
        payload = {"entries": self.leaderboard_entries}
        try:
            self.leaderboard_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            return

    def _normalize_leaderboard(self, entries: list) -> list[dict]:
        cleaned: list[dict] = []
        for entry in entries:
            if isinstance(entry, dict):
                name = entry.get("name", "Anon")
                score = entry.get("score", 0)
            else:
                name = "Anon"
                score = entry
            try:
                score_value = int(score)
            except (TypeError, ValueError):
                continue
            name_value = str(name).strip() if name else "Anon"
            if not name_value:
                name_value = "Anon"
            cleaned.append({"name": name_value, "score": score_value})
        cleaned.sort(key=lambda item: item["score"], reverse=True)
        return cleaned[:5]

    def record_score(self):
        if self.score_recorded:
            return

        self.score_recorded = True
        raw_name = self.name_input or ""
        cleaned_name = "".join(ch for ch in raw_name if ch.isalnum())
        name = cleaned_name.strip()
        if not name:
            name = f"Snake{random.randint(1000, 9999)}"
        self.leaderboard_entries.append({"name": name, "score": int(self.points)})
        self.leaderboard_entries = self._normalize_leaderboard(self.leaderboard_entries)
        self._save_leaderboard()

    def run(self):
        while self.running:
            self.clock.tick(60)
            self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
