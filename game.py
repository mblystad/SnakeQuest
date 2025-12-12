import random
from pathlib import Path
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    DEFAULT_FONT, GRID_WIDTH, GRID_HEIGHT, TILE_SIZE,
    COLOR_BUTTON, COLOR_KEY, COLOR_HUD, COLOR_WALL
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

        self.game_started = False
        self.start_time_ms: int | None = None

    def start_level(self):
        """Set up a fresh level layout with increasing gate spacing."""
        self.snake = Snake(grid_pos=(5, 5))
        self.food = Food()
        self.build_walls()
        self.place_gate_elements()
        self.spawn_food()
        self.transition_timer = 0
        self.transition_text = ""

    def start_game(self):
        """Begin a new run from the start screen."""
        self.level = 1
        self.points = 0
        self.game_started = True
        self.start_time_ms = pygame.time.get_ticks()
        self.start_level()

    def build_walls(self):
        """Create a neon wall outline that also serves as collision."""

        self.wall_positions = set()
        for x in range(GRID_WIDTH):
            self.wall_positions.add((x, 0))
            self.wall_positions.add((x, GRID_HEIGHT - 1))
        for y in range(GRID_HEIGHT):
            self.wall_positions.add((0, y))
            self.wall_positions.add((GRID_WIDTH - 1, y))

    def place_gate_elements(self):
        """Place the button and key with increasing separation per level."""
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
            return

        if (head_x, head_y) in self.wall_positions:
            self.running = False

        # TODO: self-collision later

    def check_food_eaten(self):
        if self.snake.head == self.food.position:
            self.snake.grow(1)
            self.points += 1
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
            pygame.draw.rect(self.screen, COLOR_WALL, rect, width=2, border_radius=4)

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
