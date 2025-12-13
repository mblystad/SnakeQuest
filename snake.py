import pygame
from config import TILE_SIZE, COLOR_SNAKE, load_scaled_image


class Snake:
    def __init__(self, grid_pos=(5, 5)):
        # Snake is a list of (x, y) grid positions, head is index 0
        self.segments = [grid_pos]

        # Movement
        self.direction = (1, 0)          # (dx, dy)
        self.pending_direction = self.direction

        # Growth
        self.grow_pending = 0

        # Placeholder PNG-style sprites (fallback when assets are missing)
        self.head_frames = self._load_head_frames() or self._create_head_frames()
        self.anim_index = 0

        # Body and tail images (fallback to simple colored blocks)
        self.body_image = self._load_body_image()
        self.tail_image = self._load_tail_image()

        # Fade-in animation for growing segments
        # Each entry: {"pos": (x, y), "alpha": int}
        self.fading_segments = []
        self.fade_speed = 40  # Alpha increase per update

    def _create_head_frames(self):
        """Create simple placeholder frames for a chew animation."""
        frames = []
        for i in range(3):
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(surf, COLOR_SNAKE, surf.get_rect())

            # Simple mouth animation on bottom
            mouth_height = 4 + i * 2
            mouth_rect = pygame.Rect(4, TILE_SIZE - mouth_height - 2,
                                     TILE_SIZE - 8, mouth_height)
            pygame.draw.rect(surf, (0, 0, 0), mouth_rect)

            frames.append(surf)
        return frames

    def _load_head_frames(self):
        """Try loading a single head PNG and return as frames list."""

        image = load_scaled_image("head.png", (TILE_SIZE, TILE_SIZE))
        return [image] if image is not None else []

    def _load_body_image(self) -> pygame.Surface:
        """Load a body PNG or build a simple colored block fallback."""

        image = load_scaled_image("segment.png", (TILE_SIZE, TILE_SIZE))
        if image is not None:
            return image

        placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        placeholder.fill(COLOR_SNAKE)
        return placeholder

    def _load_tail_image(self) -> pygame.Surface:
        """Load a tail PNG or reuse the body placeholder."""

        image = load_scaled_image("tail.png", (TILE_SIZE, TILE_SIZE))
        if image is not None:
            return image

        placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        placeholder.fill(COLOR_SNAKE)
        return placeholder

    @property
    def head(self):
        return self.segments[0]

    def set_direction(self, new_dir):
        """Set new direction if it's not directly opposite to current."""
        cur_dx, cur_dy = self.direction
        new_dx, new_dy = new_dir

        # Prevent reversing
        if (cur_dx == -new_dx and cur_dx != 0) or (cur_dy == -new_dy and cur_dy != 0):
            return

        self.pending_direction = new_dir

    def grow(self, amount: int = 1):
        """Schedule growth and prepare fade-in animation."""
        self.grow_pending += amount

        if self.segments:
            tail_pos = self.segments[-1]
            self.fading_segments.append({"pos": tail_pos, "alpha": 0})

    def update(self):
        """Move the snake and update animations."""
        # Advance chew animation
        self.anim_index = (self.anim_index + 1) % len(self.head_frames)

        # Apply movement
        self.direction = self.pending_direction
        head_x, head_y = self.head
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        self.segments.insert(0, new_head)

        # Handle growth
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.segments.pop()

        # Update fade-in animations
        for seg in self.fading_segments:
            seg["alpha"] = min(255, seg["alpha"] + self.fade_speed)

        # Remove finished fades
        self.fading_segments = [
            seg for seg in self.fading_segments
            if seg["alpha"] < 255
        ]

    def draw(self, surface: pygame.Surface):
        for index, (x, y) in enumerate(self.segments):
            dest = (x * TILE_SIZE, y * TILE_SIZE)

            # Determine fade overlay
            fade_entry = next(
                (seg for seg in self.fading_segments if seg["pos"] == (x, y)),
                None,
            )

            if index == 0:
                # Head with chew animation and rotation
                frame = self.head_frames[self.anim_index]
                angle = self._direction_to_angle(self.direction)
                oriented = pygame.transform.rotate(frame, angle) if frame else frame
                self._blit_with_fade(surface, oriented, dest, fade_entry)
            elif index == len(self.segments) - 1:
                # Tail pointing toward previous segment
                prev_x, prev_y = self.segments[index - 1]
                dx, dy = x - prev_x, y - prev_y
                angle = self._direction_to_angle((dx, dy))
                oriented = pygame.transform.rotate(self.tail_image, angle)
                self._blit_with_fade(surface, oriented, dest, fade_entry)
            else:
                oriented = self.body_image
                self._blit_with_fade(surface, oriented, dest, fade_entry)

    def _blit_with_fade(self, surface: pygame.Surface, image: pygame.Surface, dest, fade_entry):
        if fade_entry:
            image.set_alpha(fade_entry["alpha"])
            surface.blit(image, dest)
            image.set_alpha(255)
        else:
            surface.blit(image, dest)

    @staticmethod
    def _direction_to_angle(direction: tuple[int, int]) -> int:
        dx, dy = direction
        if dx == 1 and dy == 0:
            return 0
        if dx == -1 and dy == 0:
            return 180
        if dx == 0 and dy == -1:
            return 90
        if dx == 0 and dy == 1:
            return -90
        return 0
