from __future__ import annotations

from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.resources import resource_find
from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.widget import Widget

from mobile_core import (
    DOWN,
    GRID_HEIGHT,
    GRID_WIDTH,
    LEFT,
    RIGHT,
    UP,
    MobileGameSession,
    MobileSettings,
)

TITLE_COLOR = (0.95, 0.89, 1.0, 1.0)
TEXT_COLOR = (0.9, 0.86, 1.0, 1.0)
ACCENT_COLOR = (0.25, 0.92, 0.86, 1.0)
WALL_COLOR = (1.0, 0.35, 0.75, 1.0)
GRID_COLOR = (0.35, 0.1, 0.56, 0.7)
FOOD_COLOR = (1.0, 0.76, 0.35, 1.0)
BUTTON_COLOR = (0.33, 0.56, 1.0, 1.0)
KEY_CLOSED_COLOR = (1.0, 0.46, 0.8, 1.0)
KEY_OPEN_COLOR = (0.37, 1.0, 0.55, 1.0)
SNAKE_HEAD_COLOR = (0.55, 1.0, 0.95, 1.0)
SNAKE_BODY_COLOR = (0.22, 0.84, 0.8, 1.0)
BG_COLOR = (0.07, 0.04, 0.17, 1.0)
PANEL_COLOR = (0.1, 0.07, 0.24, 0.95)
OVERLAY_COLOR = (0.0, 0.0, 0.0, 0.45)


class NeonButton(Button):
    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(48))
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("color", TITLE_COLOR)
        kwargs.setdefault("font_size", sp(18))
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw, state=self._redraw)
        self._redraw()

    def _redraw(self, *_args):
        active = self.state == "down" or not self.disabled
        fill = (0.12, 0.1, 0.28, 0.96) if active else (0.08, 0.07, 0.14, 0.6)
        border = ACCENT_COLOR if active else (0.4, 0.35, 0.5, 0.7)
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*fill)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)] * 4)
            Color(*border)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(16)), width=1.4)


class PlayfieldWidget(Widget):
    def __init__(self, session: MobileGameSession, direction_callback, **kwargs):
        super().__init__(**kwargs)
        self.session = session
        self.direction_callback = direction_callback
        self._touch_start: tuple[float, float] | None = None
        self.bind(pos=self.redraw, size=self.redraw)

    def redraw(self, *_args):
        cell = min(self.width / max(1, GRID_WIDTH), self.height / max(1, GRID_HEIGHT))
        board_width = cell * GRID_WIDTH
        board_height = cell * GRID_HEIGHT
        origin_x = self.x + (self.width - board_width) / 2.0
        origin_y = self.y + (self.height - board_height) / 2.0
        radius = max(3.0, cell * 0.18)
        inset = max(1.0, cell * 0.08)

        self.canvas.clear()
        with self.canvas:
            Color(*BG_COLOR)
            RoundedRectangle(pos=(origin_x, origin_y), size=(board_width, board_height), radius=[dp(20)] * 4)
            Color(0.18, 0.1, 0.32, 0.22)
            for row in range(10):
                band_height = board_height / 10.0
                RoundedRectangle(
                    pos=(origin_x, origin_y + row * band_height),
                    size=(board_width, band_height),
                    radius=[0, 0, 0, 0],
                )

            Color(*GRID_COLOR)
            for index in range(GRID_WIDTH + 1):
                x = origin_x + index * cell
                Line(points=[x, origin_y, x, origin_y + board_height], width=1)
            for index in range(GRID_HEIGHT + 1):
                y = origin_y + index * cell
                Line(points=[origin_x, y, origin_x + board_width, y], width=1)

            walls = self.session.walls
            if self.session.state == "loading" and self.session.loading_tiles:
                walls = set(self.session.loading_tiles[: self.session.loading_reveal_count])
            Color(*WALL_COLOR)
            for cell_pos in walls:
                x, y = self._cell_rect(origin_x, origin_y, cell, cell_pos)
                Line(
                    rounded_rectangle=(x + inset, y + inset, cell - inset * 2, cell - inset * 2, radius),
                    width=max(1.0, cell * 0.08),
                )

            if self.session.button_pos is not None:
                Color(*BUTTON_COLOR)
                x, y = self._cell_rect(origin_x, origin_y, cell, self.session.button_pos)
                RoundedRectangle(
                    pos=(x + inset, y + inset),
                    size=(cell - inset * 2, cell - inset * 2),
                    radius=[radius] * 4,
                )

            if self.session.key_pos is not None:
                Color(*(KEY_OPEN_COLOR if self.session.gate_open() else KEY_CLOSED_COLOR))
                x, y = self._cell_rect(origin_x, origin_y, cell, self.session.key_pos)
                RoundedRectangle(
                    pos=(x + cell * 0.18, y + cell * 0.12),
                    size=(cell * 0.64, cell * 0.76),
                    radius=[radius] * 4,
                )
                Color(0.07, 0.04, 0.17, 0.9)
                Line(circle=(x + cell * 0.5, y + cell * 0.62, cell * 0.13), width=max(1.0, cell * 0.08))

            if self.session.food_pos is not None:
                Color(*FOOD_COLOR)
                x, y = self._cell_rect(origin_x, origin_y, cell, self.session.food_pos)
                RoundedRectangle(
                    pos=(x + cell * 0.15, y + cell * 0.15),
                    size=(cell * 0.7, cell * 0.7),
                    radius=[radius] * 4,
                )

            if self.session.snake is not None:
                for index, segment in enumerate(reversed(self.session.snake.segments)):
                    x, y = self._cell_rect(origin_x, origin_y, cell, segment)
                    Color(*(SNAKE_HEAD_COLOR if index == len(self.session.snake.segments) - 1 else SNAKE_BODY_COLOR))
                    RoundedRectangle(
                        pos=(x + inset, y + inset),
                        size=(cell - inset * 2, cell - inset * 2),
                        radius=[radius] * 4,
                    )

            if self.session.state != "playing":
                Color(*OVERLAY_COLOR)
                RoundedRectangle(pos=(origin_x, origin_y), size=(board_width, board_height), radius=[dp(20)] * 4)

    def _cell_rect(
        self,
        origin_x: float,
        origin_y: float,
        cell: float,
        grid_pos: tuple[int, int],
    ) -> tuple[float, float]:
        grid_x, grid_y = grid_pos
        screen_y = GRID_HEIGHT - 1 - grid_y
        return origin_x + grid_x * cell, origin_y + screen_y * cell

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        self._touch_start = touch.pos
        return True

    def on_touch_up(self, touch):
        if self._touch_start is None or not self.collide_point(*touch.pos):
            return super().on_touch_up(touch)
        start_x, start_y = self._touch_start
        delta_x = touch.x - start_x
        delta_y = touch.y - start_y
        threshold = dp(20)
        if abs(delta_x) > abs(delta_y) and abs(delta_x) >= threshold:
            self.direction_callback(RIGHT if delta_x > 0 else LEFT)
        elif abs(delta_y) >= threshold:
            self.direction_callback(UP if delta_y > 0 else DOWN)
        self._touch_start = None
        return True


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.best_label = Label(color=TEXT_COLOR, font_size=sp(18), size_hint_y=None, height=dp(30))
        layout = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(16))
        title = Label(
            text="SnakeQuest Android",
            color=TITLE_COLOR,
            font_size=sp(34),
            bold=True,
            size_hint_y=None,
            height=dp(90),
        )
        subtitle = Label(
            text="Touch-first port with the original gate-and-key loop.",
            color=TEXT_COLOR,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(30),
        )
        start_button = NeonButton(text="Start Run")
        start_button.bind(on_release=lambda *_: App.get_running_app().start_run())
        settings_button = NeonButton(text="Settings")
        settings_button.bind(on_release=lambda *_: setattr(self.manager, "current", "settings"))
        exit_button = NeonButton(text="Exit")
        exit_button.bind(on_release=lambda *_: App.get_running_app().stop())
        hint = Label(
            text="Swipe on the board or use the D-pad buttons.",
            color=TEXT_COLOR,
            font_size=sp(15),
            size_hint_y=None,
            height=dp(28),
        )
        layout.add_widget(title)
        layout.add_widget(subtitle)
        layout.add_widget(self.best_label)
        layout.add_widget(hint)
        layout.add_widget(Widget())
        layout.add_widget(start_button)
        layout.add_widget(settings_button)
        layout.add_widget(exit_button)
        self.add_widget(layout)
        self.bind(size=self._redraw, pos=self._redraw)

    def on_pre_enter(self, *_args):
        app = App.get_running_app()
        self.best_label.text = f"Best score: {app.best_score}"

    def _redraw(self, *_args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*PANEL_COLOR)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[0, 0, 0, 0])
            Color(0.18, 0.08, 0.32, 0.6)
            for stripe in range(6):
                stripe_height = self.height / 6.0
                RoundedRectangle(
                    pos=(self.x, self.y + stripe * stripe_height),
                    size=(self.width, stripe_height),
                    radius=[0, 0, 0, 0],
                )


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.speed_label = Label(color=TEXT_COLOR, font_size=sp(20), size_hint_y=None, height=dp(36))
        self.sound_label = Label(color=TEXT_COLOR, font_size=sp(20), size_hint_y=None, height=dp(36))
        layout = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(16))
        title = Label(
            text="Settings",
            color=TITLE_COLOR,
            font_size=sp(30),
            bold=True,
            size_hint_y=None,
            height=dp(70),
        )
        speed_button = NeonButton(text="Cycle Speed")
        speed_button.bind(on_release=lambda *_: App.get_running_app().cycle_speed())
        sound_button = NeonButton(text="Toggle Sound")
        sound_button.bind(on_release=lambda *_: App.get_running_app().toggle_sound())
        back_button = NeonButton(text="Back")
        back_button.bind(on_release=lambda *_: setattr(self.manager, "current", "menu"))
        layout.add_widget(title)
        layout.add_widget(self.speed_label)
        layout.add_widget(self.sound_label)
        layout.add_widget(speed_button)
        layout.add_widget(sound_button)
        layout.add_widget(Widget())
        layout.add_widget(back_button)
        self.add_widget(layout)
        self.bind(size=self._redraw, pos=self._redraw)

    def on_pre_enter(self, *_args):
        self.refresh_labels()

    def refresh_labels(self):
        app = App.get_running_app()
        self.speed_label.text = f"Speed: {app.session.settings.speed_name}"
        self.sound_label.text = f"Sound: {'On' if app.session.settings.sound_on else 'Off'}"

    def _redraw(self, *_args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*PANEL_COLOR)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[0, 0, 0, 0])


class GameScreen(Screen):
    def __init__(self, session: MobileGameSession, **kwargs):
        super().__init__(**kwargs)
        self.session = session
        self.event = None
        self.score_label = Label(color=TITLE_COLOR, font_size=sp(18), halign="left")
        self.level_label = Label(color=TITLE_COLOR, font_size=sp(18))
        self.time_label = Label(color=TITLE_COLOR, font_size=sp(18), halign="right")
        self.status_label = Label(
            color=TEXT_COLOR,
            font_size=sp(15),
            size_hint_y=None,
            height=dp(48),
            valign="middle",
        )
        self.board = PlayfieldWidget(session, self.session.queue_direction)
        self.pause_button = NeonButton(text="Pause")
        self.pause_button.bind(on_release=lambda *_: self._toggle_pause())
        self.next_button = NeonButton(text="Next")
        self.next_button.bind(on_release=lambda *_: self._next_level())
        self.replay_button = NeonButton(text="Replay")
        self.replay_button.bind(on_release=lambda *_: self._replay())
        self.menu_button = NeonButton(text="Menu")
        self.menu_button.bind(on_release=lambda *_: self._menu())

        layout = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        hud = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32))
        hud.add_widget(self.score_label)
        hud.add_widget(self.level_label)
        hud.add_widget(self.time_label)
        layout.add_widget(hud)
        layout.add_widget(self.status_label)
        layout.add_widget(self.board)

        action_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48), spacing=dp(8))
        action_row.add_widget(self.pause_button)
        action_row.add_widget(self.next_button)
        action_row.add_widget(self.replay_button)
        action_row.add_widget(self.menu_button)
        layout.add_widget(action_row)

        dpad = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(144), spacing=dp(8))
        top_row = BoxLayout(orientation="horizontal", spacing=dp(8))
        top_row.add_widget(Widget())
        up_button = NeonButton(text="Up")
        up_button.bind(on_release=lambda *_: self.session.queue_direction(UP))
        top_row.add_widget(up_button)
        top_row.add_widget(Widget())

        bottom_row = BoxLayout(orientation="horizontal", spacing=dp(8))
        left_button = NeonButton(text="Left")
        left_button.bind(on_release=lambda *_: self.session.queue_direction(LEFT))
        down_button = NeonButton(text="Down")
        down_button.bind(on_release=lambda *_: self.session.queue_direction(DOWN))
        right_button = NeonButton(text="Right")
        right_button.bind(on_release=lambda *_: self.session.queue_direction(RIGHT))
        bottom_row.add_widget(left_button)
        bottom_row.add_widget(down_button)
        bottom_row.add_widget(right_button)

        dpad.add_widget(top_row)
        dpad.add_widget(bottom_row)
        layout.add_widget(dpad)

        self.add_widget(layout)
        self.bind(size=self._redraw, pos=self._redraw)

    def on_pre_enter(self, *_args):
        if self.event is None:
            self.event = Clock.schedule_interval(self._update_frame, 1.0 / 60.0)
        self.refresh()

    def on_leave(self, *_args):
        if self.event is not None:
            self.event.cancel()
            self.event = None

    def refresh(self):
        self.score_label.text = f"Score: {self.session.score}"
        self.level_label.text = f"Level: {self.session.level}"
        self.time_label.text = self.session.format_elapsed_time()
        self.status_label.text = self.session.status_text()
        self.next_button.disabled = self.session.state != "level_clear"
        self.replay_button.disabled = self.session.state != "game_over"
        self.pause_button.disabled = self.session.state not in ("playing", "paused")
        self.pause_button.text = "Resume" if self.session.state == "paused" else "Pause"
        self.board.redraw()

    def _update_frame(self, dt: float):
        previous_state = self.session.state
        self.session.update(dt * 1000.0)
        if self.session.state == "game_over" and previous_state != "game_over":
            App.get_running_app().register_score(self.session.score)
        self.refresh()

    def _toggle_pause(self):
        self.session.toggle_pause()
        self.refresh()

    def _next_level(self):
        self.session.advance_level()
        self.refresh()

    def _replay(self):
        self.session.replay_level()
        self.refresh()

    def _menu(self):
        self.manager.current = "menu"

    def _redraw(self, *_args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*PANEL_COLOR)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[0, 0, 0, 0])


class SnakeQuestAndroidApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = MobileGameSession(settings=MobileSettings())
        self.best_score = 0
        self.music = None
        self.store: JsonStore | None = None

    def build(self):
        self.title = "SnakeQuest Android"
        self._load_store()
        self._load_audio()
        manager = ScreenManager(transition=FadeTransition(duration=0.18))
        manager.add_widget(MenuScreen(name="menu"))
        manager.add_widget(SettingsScreen(name="settings"))
        manager.add_widget(GameScreen(self.session, name="game"))
        self._refresh_music()
        return manager

    def start_run(self):
        self.session.start_new_run()
        self.root.current = "game"
        self._refresh_music()

    def cycle_speed(self):
        self.session.settings.cycle_speed()
        self._save_settings()
        settings_screen = self.root.get_screen("settings")
        settings_screen.refresh_labels()

    def toggle_sound(self):
        self.session.settings.sound_on = not self.session.settings.sound_on
        self._save_settings()
        self._refresh_music()
        settings_screen = self.root.get_screen("settings")
        settings_screen.refresh_labels()

    def register_score(self, score: int):
        if score <= self.best_score:
            return
        self.best_score = score
        if self.store is not None:
            self.store.put("scores", best_score=int(score))

    def _load_store(self):
        store_path = Path(self.user_data_dir) / "snakequest_mobile.json"
        self.store = JsonStore(str(store_path))
        if self.store.exists("settings"):
            payload = self.store.get("settings")
            speed_index = int(payload.get("speed_index", self.session.settings.speed_index))
            sound_on = bool(payload.get("sound_on", self.session.settings.sound_on))
            max_index = len(self.session.settings.speed_options) - 1
            self.session.settings.speed_index = max(0, min(max_index, speed_index))
            self.session.settings.sound_on = sound_on
        if self.store.exists("scores"):
            self.best_score = int(self.store.get("scores").get("best_score", 0))

    def _save_settings(self):
        if self.store is None:
            return
        self.store.put(
            "settings",
            speed_index=int(self.session.settings.speed_index),
            sound_on=bool(self.session.settings.sound_on),
        )

    def _load_audio(self):
        asset_path = resource_find("theme.wav")
        if asset_path is None:
            fallback = Path(__file__).with_name("theme.wav")
            asset_path = str(fallback) if fallback.exists() else None
        if asset_path is None:
            return
        self.music = SoundLoader.load(asset_path)
        if self.music is None:
            return
        try:
            self.music.loop = True
        except AttributeError:
            pass
        self.music.volume = 0.4

    def _refresh_music(self):
        if self.music is None:
            return
        if self.session.settings.sound_on:
            if self.music.state != "play":
                self.music.play()
        elif self.music.state == "play":
            self.music.stop()


def run_android_app() -> None:
    SnakeQuestAndroidApp().run()


if __name__ == "__main__":
    run_android_app()
