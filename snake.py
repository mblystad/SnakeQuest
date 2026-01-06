import pygame
from config import TILE_SIZE, COLOR_SNAKE, load_scaled_image


class Snake:
    def __init__(self, grid_pos=(5, 5)):
        # Snake is a list of (x, y) grid positions, head is index 0
        self.segments = [grid_pos]
        self.prev_segments = list(self.segments)
        self.interp_ready = False

        # Movement
        self.direction = (1, 0)          # (dx, dy)
        self.pending_direction = self.direction
        self.prev_direction = self.direction

        # Growth
        self.grow_pending = 0

        # Placeholder PNG-style sprites (fallback when assets are missing)
        self.head_frames = self._load_head_frames() or self._create_head_frames()
        self.anim_index = 0

        # Body and tail images (fallback to solid blocks when assets are missing)
        self.body_image = self._load_body_image()
        self.throat_image = self._load_throat_image()
        self.tail_image = self._load_tail_image()
        self._rotation_cache = self._build_rotation_cache()
        self.connector_thickness = max(4, int(TILE_SIZE * 0.6))
        self.connector_radius = max(2, int(self.connector_thickness * 0.5))

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
        """Try loading head animation frames from disk.

        Returns an empty list when the PNGs are not available so callers can
        gracefully fall back to generated placeholders.
        """

        frames = []
        for i in range(3):
            image = load_scaled_image(f"snake_head_{i}.png", (TILE_SIZE, TILE_SIZE))
            if image is None:
                frames = []
                break
            frames.append(image)
        if frames:
            return frames

        single = load_scaled_image("head.png", (TILE_SIZE, TILE_SIZE))
        if single is not None:
            return [single]

        return []

    def _load_body_image(self) -> pygame.Surface:
        """Load a body PNG or build a simple colored block fallback."""

        for filename in ("segment.png", "snake_body.png"):
            image = load_scaled_image(filename, (TILE_SIZE, TILE_SIZE))
            if image is not None:
                return image

        placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        placeholder.fill(COLOR_SNAKE)
        return placeholder

    def _load_throat_image(self) -> pygame.Surface:
        """Load the throat/neck PNG or fall back to the body image."""

        image = load_scaled_image("throat.png", (TILE_SIZE, TILE_SIZE))
        if image is not None:
            return image

        return self.body_image

    def _load_tail_image(self) -> pygame.Surface:
        """Load a tail PNG or build a simple colored block fallback."""

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
        self.prev_segments = list(self.segments)
        self.prev_direction = self.direction

        # Advance chew animation
        if self.head_frames:
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
        self.interp_ready = True

    def reset_interpolation(self):
        self.prev_segments = list(self.segments)
        self.prev_direction = self.direction
        self.interp_ready = False

    def draw(self, surface: pygame.Surface, offset_y: int = 0, alpha: float = 0.0):
        if not self.interp_ready:
            alpha = 0.0
        else:
            alpha = max(0.0, min(1.0, alpha))
        positions = (
            self._interpolated_positions(alpha)
            if self.interp_ready
            else list(self.segments)
        )
        positions = positions[: len(self.segments)]
        if len(positions) > 1:
            self._draw_connectors(surface, positions, offset_y)
        for index, (x, y) in enumerate(positions):
            dest = (int(x * TILE_SIZE), int(y * TILE_SIZE + offset_y))

            # Determine fade overlay
            fade_entry = next(
                (seg for seg in self.fading_segments if seg["pos"] == (int(x), int(y))),
                None,
            )

            if index == 0:
                # Head with chew animation and rotation
                frame = self._get_rotated_head_frame()
                angle = self._direction_to_angle(self._head_direction())
                oriented = self._rotated_head(angle, frame)
                self._blit_with_fade(surface, oriented, dest, fade_entry)
            elif index == len(self.segments) - 1:
                # Tail pointing toward previous segment
                cur_x, cur_y = positions[index]
                prev_x, prev_y = positions[index - 1]
                dx, dy = cur_x - prev_x, cur_y - prev_y
                angle = self._direction_to_angle(self._axis_direction(dx, dy))
                oriented = self._rotated_body("tail", angle)
                self._blit_with_fade(surface, oriented, dest, fade_entry)
            else:
                angle = self._body_angle_from_positions(positions, index)
                cache_key = "throat" if index == 1 else "body"
                oriented = self._rotated_body(cache_key, angle)
                self._blit_with_fade(surface, oriented, dest, fade_entry)

    def _interpolated_positions(self, alpha: float) -> list[tuple[float, float]]:
        current = list(self.segments)
        previous = list(self.prev_segments) if self.prev_segments else current

        if len(previous) > len(current):
            current.extend([current[-1]] * (len(previous) - len(current)))
        elif len(previous) < len(current):
            previous.extend([previous[-1]] * (len(current) - len(previous)))

        interpolated = []
        for (x1, y1), (x2, y2) in zip(previous, current):
            ix = x1 + (x2 - x1) * alpha
            iy = y1 + (y2 - y1) * alpha
            interpolated.append((ix, iy))
        return interpolated

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

    def _body_angle(self, index: int) -> int:
        """Rotate a body segment to match its neighboring segments."""
        prev_x, prev_y = self.segments[index - 1]
        next_x, next_y = self.segments[index + 1]
        x, y = self.segments[index]

        dx1, dy1 = prev_x - x, prev_y - y
        dx2, dy2 = next_x - x, next_y - y

        # Straight segment: align with its axis based on the previous segment.
        if dx1 == dx2 and dx1 == 0:
            return self._direction_to_angle((0, dy1))
        if dy1 == dy2 and dy1 == 0:
            return self._direction_to_angle((dx1, 0))

        # Corner segment: fall back to the previous direction.
        return self._direction_to_angle((dx1, dy1))

    def _build_rotation_cache(self) -> dict[str, dict[int, pygame.Surface] | dict[int, list[pygame.Surface]]]:
        angles = (0, 90, 180, 270)
        head_cache = {}
        for angle in angles:
            head_cache[angle] = [
                pygame.transform.rotate(frame, angle) if angle else frame
                for frame in self.head_frames
            ]
        body_cache = {
            angle: pygame.transform.rotate(self.body_image, angle) if angle else self.body_image
            for angle in angles
        }
        throat_cache = {
            angle: pygame.transform.rotate(self.throat_image, angle) if angle else self.throat_image
            for angle in angles
        }
        tail_cache = {
            angle: pygame.transform.rotate(self.tail_image, angle) if angle else self.tail_image
            for angle in angles
        }
        return {
            "head": head_cache,
            "body": body_cache,
            "throat": throat_cache,
            "tail": tail_cache,
        }

    def _normalized_angle(self, angle: int) -> int:
        return angle % 360

    def _rotated_head(self, angle: int, fallback: pygame.Surface) -> pygame.Surface:
        normalized = self._normalized_angle(angle)
        frames = self._rotation_cache.get("head", {})
        cached_frames = frames.get(normalized)
        if cached_frames:
            return cached_frames[self.anim_index % len(cached_frames)]
        return fallback

    def _rotated_body(self, key: str, angle: int) -> pygame.Surface:
        normalized = self._normalized_angle(angle)
        cache = self._rotation_cache.get(key, {})
        return cache.get(normalized, self.body_image)

    def _get_rotated_head_frame(self) -> pygame.Surface:
        if not self.head_frames:
            return self.body_image
        return self.head_frames[self.anim_index % len(self.head_frames)]

    def _head_direction(self) -> tuple[int, int]:
        if self.prev_segments and self.segments:
            prev_head = self.prev_segments[0]
            head = self.segments[0]
            dx = head[0] - prev_head[0]
            dy = head[1] - prev_head[1]
            if (dx, dy) != (0, 0):
                return self._axis_direction(dx, dy)
        return self.pending_direction

    def _body_angle_from_positions(self, positions: list[tuple[float, float]], index: int) -> int:
        if index <= 0 or index >= len(positions) - 1:
            return self._body_angle(index)

        prev_x, prev_y = positions[index - 1]
        next_x, next_y = positions[index + 1]
        x, y = positions[index]

        dx1, dy1 = prev_x - x, prev_y - y
        dx2, dy2 = next_x - x, next_y - y
        dir1 = self._axis_direction(dx1, dy1)
        dir2 = self._axis_direction(dx2, dy2)

        if dir1 == (0, 0):
            return self._body_angle(index)

        if (dir1[0] != 0 and dir2[0] != 0) or (dir1[1] != 0 and dir2[1] != 0):
            return self._direction_to_angle(dir1)

        return self._direction_to_angle(dir1)

    def _axis_direction(self, dx: float, dy: float) -> tuple[int, int]:
        if abs(dx) >= abs(dy):
            return (self._sign(dx), 0) if abs(dx) > 1e-3 else (0, self._sign(dy))
        return (0, self._sign(dy))

    @staticmethod
    def _sign(value: float) -> int:
        if value > 0:
            return 1
        if value < 0:
            return -1
        return 0

    def _draw_connectors(self, surface: pygame.Surface, positions: list[tuple[float, float]], offset_y: int):
        half = TILE_SIZE / 2
        thickness = self.connector_thickness
        radius = self.connector_radius
        for index in range(1, len(positions)):
            x1, y1 = positions[index - 1]
            x2, y2 = positions[index]
            cx1 = x1 * TILE_SIZE + half
            cy1 = y1 * TILE_SIZE + offset_y + half
            cx2 = x2 * TILE_SIZE + half
            cy2 = y2 * TILE_SIZE + offset_y + half
            dx = cx2 - cx1
            dy = cy2 - cy1
            overlap = thickness
            if index == 1:
                overlap = max(2, int(thickness * 0.25))
            if abs(dx) >= abs(dy):
                width = abs(dx) + overlap
                height = thickness
            else:
                width = thickness
                height = abs(dy) + overlap

            rect = pygame.Rect(0, 0, int(round(width)), int(round(height)))
            rect.center = (int(round((cx1 + cx2) / 2)), int(round((cy1 + cy2) / 2)))
            pygame.draw.rect(surface, COLOR_SNAKE, rect, border_radius=radius)
