import pygame
from config import TILE_SIZE, COLOR_FOOD

class Food:
    def __init__(self, grid_pos=(10, 10)):
        self.position = grid_pos

    def draw(self, surface: pygame.Surface):
        x, y = self.position
        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, COLOR_FOOD, rect)
