import pygame
from pathlib import Path

# Grid
TILE_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 20

SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE

FPS = 10

# Colors
COLOR_BG = (10, 10, 10)
COLOR_GRID = (40, 40, 40)
COLOR_SNAKE = (0, 200, 0)
COLOR_FOOD = (200, 30, 30)

pygame.font.init()
DEFAULT_FONT = pygame.font.SysFont("consolas", 20)

# Assets
ASSET_DIR = Path(__file__).parent / "assets"


def load_scaled_image(filename: str, size: tuple[int, int]):
    """Load a PNG from the assets folder and scale it to the given size.

    Returns ``None`` when the file is missing or invalid so callers can
    gracefully fall back to procedural placeholders.
    """

    path = ASSET_DIR / filename
    try:
        image = pygame.image.load(path).convert_alpha()
    except (FileNotFoundError, pygame.error):
        return None

    return pygame.transform.smoothscale(image, size)
