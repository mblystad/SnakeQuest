import random
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, FPS,
    DEFAULT_FONT, GRID_WIDTH, GRID_HEIGHT
)
from grid import draw_grid
from snake import Snake
from food import Food


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Modular Snake - Chew + Growth Fade")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.snake = Snake(grid_pos=(5, 5))
        self.food = Food()
        self.spawn_food()

    def spawn_food(self):
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in self.snake.segments:
                self.food.position = (x, y)
                break

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
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
        self.snake.update()
        self.check_collisions()
        self.check_food_eaten()

    def check_collisions(self):
        head_x, head_y = self.snake.head

        # Wall collision ends game
        if head_x < 0 or head_x >= GRID_WIDTH or head_y < 0 or head_y >= GRID_HEIGHT:
            self.running = False

        # TODO: self-collision later

    def check_food_eaten(self):
        if self.snake.head == self.food.position:
            self.snake.grow(1)
            self.spawn_food()

    def draw(self):
        self.screen.fill(COLOR_BG)
        draw_grid(self.screen)

        self.food.draw(self.screen)
        self.snake.draw(self.screen)

        text = DEFAULT_FONT.render(
            "Chew animation + fade-in growth", True, (200, 200, 200)
        )
        self.screen.blit(text, (10, 10))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
