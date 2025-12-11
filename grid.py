import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, COLOR_GRID

def draw_grid(surface: pygame.Surface):
    for x in range(0, SCREEN_WIDTH, TILE_SIZE):
        pygame.draw.line(surface, COLOR_GRID, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, TILE_SIZE):
        pygame.draw.line(surface, COLOR_GRID, (0, y), (SCREEN_WIDTH, y))
