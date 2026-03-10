import pygame
from config import (
    SCREEN_WIDTH,
    PLAYFIELD_HEIGHT,
    TILE_SIZE,
    COLOR_GRID,
    COLOR_BG_TOP,
    COLOR_BG_BOTTOM,
)

_GRID_OVERLAY_CACHE: dict[tuple[int, int], pygame.Surface] = {}


def _get_grid_overlay(height: int, alpha: int) -> pygame.Surface:
    key = (height, alpha)
    cached = _GRID_OVERLAY_CACHE.get(key)
    if cached is not None:
        return cached

    overlay = pygame.Surface((SCREEN_WIDTH, height), pygame.SRCALPHA)
    line_color = (*COLOR_GRID, alpha)
    for x in range(0, SCREEN_WIDTH, TILE_SIZE):
        pygame.draw.line(overlay, line_color, (x, 0), (x, height))
    for y in range(0, height, TILE_SIZE):
        pygame.draw.line(overlay, line_color, (0, y), (SCREEN_WIDTH, y))
    _GRID_OVERLAY_CACHE[key] = overlay
    return overlay


def build_background(height: int = PLAYFIELD_HEIGHT) -> pygame.Surface:
    """Pre-render a synthwave gradient background with a subtle grid overlay."""

    surface = pygame.Surface((SCREEN_WIDTH, height))

    # Vertical gradient sky
    for y in range(height):
        t = y / height
        r = int(COLOR_BG_TOP[0] + (COLOR_BG_BOTTOM[0] - COLOR_BG_TOP[0]) * t)
        g = int(COLOR_BG_TOP[1] + (COLOR_BG_BOTTOM[1] - COLOR_BG_TOP[1]) * t)
        b = int(COLOR_BG_TOP[2] + (COLOR_BG_BOTTOM[2] - COLOR_BG_TOP[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    # Neon grid overlay
    surface.blit(_get_grid_overlay(height, 90), (0, 0))
    return surface


def draw_grid(surface: pygame.Surface, offset_y: int = 0, height: int = PLAYFIELD_HEIGHT):
    """Draw a light neon grid overlay on top of the background."""
    surface.blit(_get_grid_overlay(height, 120), (0, offset_y))
