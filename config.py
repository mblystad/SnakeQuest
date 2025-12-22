import pygame
from pathlib import Path

# Grid
TILE_SIZE = 20
GRID_WIDTH = 36
GRID_HEIGHT = 24

SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE
PLAYFIELD_HEIGHT = GRID_HEIGHT * TILE_SIZE
HUD_HEIGHT = 70
SCREEN_HEIGHT = PLAYFIELD_HEIGHT + HUD_HEIGHT

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

# Assets
ASSET_DIR = Path(__file__).parent / "assets"
FALLBACK_ASSET_DIR = Path(__file__).parent

PIXEL_FONT_FILES = (
    "PressStart2P-Regular.ttf",
    "pressstart2p.ttf",
    "8bit.ttf",
    "pixel.ttf",
)
PIXEL_FONT_NAMES = (
    "Press Start 2P",
    "PressStart2P",
    "Pixel Emulator",
    "VT323",
    "Pixel Operator",
    "Pixeled",
)


def load_pixel_font(size: int) -> pygame.font.Font:
    """Load an 8-bit style font with graceful fallbacks."""
    search_dirs = (ASSET_DIR, FALLBACK_ASSET_DIR)
    for base_dir in search_dirs:
        for filename in PIXEL_FONT_FILES:
            path = base_dir / filename
            if not path.exists():
                continue
            try:
                return pygame.font.Font(path, size)
            except (FileNotFoundError, pygame.error):
                continue

    for name in PIXEL_FONT_NAMES:
        font = pygame.font.SysFont(name, size)
        if font:
            return font

    return pygame.font.SysFont("consolas", size)


DEFAULT_FONT = load_pixel_font(24)


def load_scaled_image(filename: str, size: tuple[int, int]):
    """Load a PNG from the assets folder and scale it to the given size.

    Returns ``None`` when the file is missing or invalid so callers can
    gracefully fall back to procedural placeholders.
    """

    search_dirs = (ASSET_DIR, FALLBACK_ASSET_DIR)
    image = None
    for base_dir in search_dirs:
        path = base_dir / filename
        if not path.exists():
            continue
        try:
            image = pygame.image.load(path).convert_alpha()
        except (FileNotFoundError, pygame.error):
            image = None
        if image is not None:
            break

    if image is None:
        return None

    return pygame.transform.smoothscale(image, size)
