import pygame
from pathlib import Path

# Grid
TILE_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 20

SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE

FPS = 10

# Colors — synthwave palette
COLOR_BG_TOP = (14, 8, 38)
COLOR_BG_BOTTOM = (88, 15, 94)
COLOR_GRID = (64, 10, 140)
COLOR_WALL = (255, 72, 184)
COLOR_SNAKE = (64, 235, 220)
COLOR_FOOD = (255, 190, 92)
COLOR_BUTTON = (80, 150, 255)
COLOR_KEY = (255, 119, 208)
COLOR_HUD = (240, 225, 255)

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


def load_sound(filename: str, volume: float | None = None):
    """Load a sound effect from assets, returning ``None`` if missing.

    The helper quietly ignores missing files or mixer errors so the game can
    run without audio assets present. An optional ``volume`` value between
    ``0.0`` and ``1.0`` is applied when the sound loads successfully.
    """

    path = ASSET_DIR / filename
    try:
        sound = pygame.mixer.Sound(path)
    except (FileNotFoundError, pygame.error):
        return None

    if volume is not None:
        sound.set_volume(max(0.0, min(1.0, volume)))

    return sound
