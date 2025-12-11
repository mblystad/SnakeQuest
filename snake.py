import pygame
from config import TILE_SIZE, COLOR_SNAKE


class Snake:
    def __init__(self, grid_pos=(5, 5)):
        # Snake is a list of (x, y) grid positions, head is index 0
        self.segments = [grid_pos]

        # Movement
        self.direction = (1, 0)          # (dx, dy)
        self.pending_direction = self.direction

        # Growth
        self.grow_pending = 0

        # Placeholder PNG-style sprites
        self.head_frames = self._create_head_frames()
        self.anim_index = 0

        # Body image placeholder (acts like a PNG segment)
        self.body_image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.body_image.fill(COLOR_SNAKE)

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

            if index == 0:
                # Head with chew animation
                frame = self.head_frames[self.anim_index]
                surface.blit(frame, dest)
            else:
                # Fade-in body segments
                fade_entry = next(
                    (seg for seg in self.fading_segments if seg["pos"] == (x, y)),
                    None
                )

                if fade_entry:
                    self.body_image.set_alpha(fade_entry["alpha"])
                    surface.blit(self.body_image, dest)
                    self.body_image.set_alpha(255)
                else:
                    surface.blit(self.body_image, dest)
