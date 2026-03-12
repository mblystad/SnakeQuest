from __future__ import annotations

import os
from pathlib import Path
import time


def _should_run_android_app() -> bool:
    if os.environ.get("SNAKEQUEST_ANDROID") == "1":
        return True
    if os.environ.get("ANDROID_ARGUMENT"):
        return True
    try:
        from kivy.utils import platform as kivy_platform
    except ImportError:
        return False
    return kivy_platform == "android"


def _run_desktop() -> None:
    import pygame

    try:
        import audioop
    except ImportError:
        audioop = None

    from config import ASSET_DIR, FALLBACK_ASSET_DIR, SCREEN_HEIGHT, SCREEN_WIDTH
    from game import Game

    SPLASH_LOGO_FILE = "IDMGlogo.png"
    SPLASH_SOUND_FILE = "jump.mp3"
    SPLASH_SOUND_SPEED = 0.8
    SPLASH_FADE_MS = 2000
    SPLASH_HOLD_MS = 2000
    SPLASH_SOUND_PLAY_MS = 1000
    SPLASH_FADE_OUT_MS = 1000
    SPLASH_FPS = 60
    SPLASH_ENABLED = os.environ.get("SNAKEQUEST_SKIP_SPLASH", "0") != "1"

    def find_asset_path(filename: str) -> Path | None:
        for base_dir in (ASSET_DIR, FALLBACK_ASSET_DIR):
            path = base_dir / filename
            if path.exists():
                return path
        return None

    def load_splash_logo() -> pygame.Surface | None:
        path = find_asset_path(SPLASH_LOGO_FILE)
        if path is None:
            return None
        try:
            return pygame.image.load(path).convert_alpha()
        except (FileNotFoundError, pygame.error):
            return None

    def load_splash_sound() -> pygame.mixer.Sound | None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            try:
                pygame.mixer.set_num_channels(32)
            except pygame.error:
                pass
        except pygame.error:
            return None

        path = find_asset_path(SPLASH_SOUND_FILE)
        if path is None:
            return None

        try:
            base = pygame.mixer.Sound(path)
            init = pygame.mixer.get_init()
            if not init:
                return base
            freq, size, channels = init
            width = max(1, abs(size) // 8)
            raw = base.get_raw()

            if abs(SPLASH_SOUND_SPEED - 1.0) < 0.01 or audioop is None:
                converted = raw
            else:
                target_rate = int(freq / max(0.01, SPLASH_SOUND_SPEED))
                converted, _ = audioop.ratecv(raw, width, channels, freq, target_rate, None)

            bytes_per_frame = width * channels
            frames_wanted = int(freq * (SPLASH_SOUND_PLAY_MS / 1000.0))
            bytes_wanted = frames_wanted * bytes_per_frame
            if bytes_wanted > 0 and len(converted) > bytes_wanted:
                converted = converted[:bytes_wanted]

            return pygame.mixer.Sound(buffer=converted)
        except (pygame.error, OSError, ValueError):
            return None

    def run_splash_screen(
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        logo: pygame.Surface | None,
        sound: pygame.mixer.Sound | None,
    ) -> None:
        if not SPLASH_ENABLED or logo is None:
            return

        channel = None
        sound_started = False

        width, height = logo.get_size()
        max_w = int(SCREEN_WIDTH)
        max_h = int(SCREEN_HEIGHT)
        scale = max(max_w / max(1, width), max_h / max(1, height))
        if scale <= 0:
            return
        if abs(scale - 1.0) > 0.01:
            logo = pygame.transform.smoothscale(logo, (int(width * scale), int(height * scale)))

        logo_x, logo_y = logo.get_size()
        pos_x = (SCREEN_WIDTH - logo_x) // 2
        pos_y = (SCREEN_HEIGHT - logo_y) // 2

        start_ms = pygame.time.get_ticks()
        start_time = time.perf_counter()
        skip_requested = False
        sound_delay_ms = max(0, int(SPLASH_FADE_MS - SPLASH_SOUND_PLAY_MS))
        total_ms = max(
            0,
            int(SPLASH_FADE_MS + max(0, SPLASH_HOLD_MS) + max(0, SPLASH_FADE_OUT_MS)),
        )

        while True:
            elapsed = pygame.time.get_ticks() - start_ms
            elapsed_wall_ms = int((time.perf_counter() - start_time) * 1000)
            elapsed = max(elapsed, elapsed_wall_ms)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    skip_requested = True

            if (not sound_started) and (sound is not None) and elapsed >= sound_delay_ms:
                try:
                    channel = sound.play(loops=0)
                except pygame.error:
                    channel = None
                sound_started = True

            screen.fill((0, 0, 0))
            if elapsed <= SPLASH_FADE_MS:
                alpha = 255 if SPLASH_FADE_MS <= 0 else int(
                    255 * min(1.0, max(0.0, elapsed / SPLASH_FADE_MS))
                )
            elif elapsed <= (SPLASH_FADE_MS + SPLASH_HOLD_MS):
                alpha = 255
            else:
                out_elapsed = elapsed - SPLASH_FADE_MS - SPLASH_HOLD_MS
                alpha = 0 if SPLASH_FADE_OUT_MS <= 0 else int(
                    255 * max(0.0, 1.0 - (out_elapsed / SPLASH_FADE_OUT_MS))
                )
            logo.set_alpha(alpha)
            screen.blit(logo, (pos_x, pos_y))
            pygame.display.flip()
            clock.tick(SPLASH_FPS)

            if skip_requested or elapsed >= total_ms:
                break

        if channel is not None:
            try:
                channel.stop()
            except pygame.error:
                pass

        pygame.event.clear()

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    splash_logo = load_splash_logo()
    splash_sound = load_splash_sound()
    run_splash_screen(screen, clock, splash_logo, splash_sound)

    game = Game()
    game.run()
def main() -> None:
    try:
        if _should_run_android_app():
            from android_app import run_android_app

            run_android_app()
            return
        _run_desktop()
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
