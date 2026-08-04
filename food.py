import pygame
from config import TILE_SIZE, COLOR_FOOD, load_scaled_image

class Food:
    def __init__(self, grid_pos=(10, 10)):
        self.position = grid_pos
        self.image = (
            load_scaled_image("f1.png", (TILE_SIZE, TILE_SIZE), smooth=False)
            or load_scaled_image("food.png", (TILE_SIZE, TILE_SIZE), smooth=False)
        )

    def draw(self, surface: pygame.Surface, offset_y: int = 0, offset_x_px: int = 0):
        x, y = self.position
        dest = (x * TILE_SIZE + offset_x_px, y * TILE_SIZE + offset_y)

        if self.image:
            surface.blit(self.image, dest)
            return

        rect = pygame.Rect(*dest, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, COLOR_FOOD, rect)
