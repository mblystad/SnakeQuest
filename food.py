import pygame
from config import TILE_SIZE, COLOR_FOOD, load_scaled_image

class Food:
    def __init__(self, grid_pos=(10, 10)):
        self.position = grid_pos
        self.image = load_scaled_image("food.png", (TILE_SIZE, TILE_SIZE))

    def draw(self, surface: pygame.Surface):
        x, y = self.position
        dest = (x * TILE_SIZE, y * TILE_SIZE)

        if self.image:
            surface.blit(self.image, dest)
            return

        rect = pygame.Rect(*dest, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, COLOR_FOOD, rect)
