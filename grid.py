import pygame
from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TILE_SIZE,
    COLOR_GRID,
    COLOR_BG_TOP,
    COLOR_BG_BOTTOM,
)


def build_background() -> pygame.Surface:
    """Pre-render a synthwave gradient background with a subtle grid overlay."""

    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Vertical gradient sky
    for y in range(SCREEN_HEIGHT):
        t = y / SCREEN_HEIGHT
        r = int(COLOR_BG_TOP[0] + (COLOR_BG_BOTTOM[0] - COLOR_BG_TOP[0]) * t)
        g = int(COLOR_BG_TOP[1] + (COLOR_BG_BOTTOM[1] - COLOR_BG_TOP[1]) * t)
        b = int(COLOR_BG_TOP[2] + (COLOR_BG_BOTTOM[2] - COLOR_BG_TOP[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    # Neon grid overlay
    grid_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    line_color = (*COLOR_GRID, 90)
    for x in range(0, SCREEN_WIDTH, TILE_SIZE):
        pygame.draw.line(grid_overlay, line_color, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, TILE_SIZE):
        pygame.draw.line(grid_overlay, line_color, (0, y), (SCREEN_WIDTH, y))

    surface.blit(grid_overlay, (0, 0))
    return surface


def draw_grid(surface: pygame.Surface):
    """Draw a light neon grid overlay on top of the background."""

    line_color = (*COLOR_GRID, 120)
    for x in range(0, SCREEN_WIDTH, TILE_SIZE):
        pygame.draw.line(surface, line_color, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, TILE_SIZE):
        pygame.draw.line(surface, line_color, (0, y), (SCREEN_WIDTH, y))
