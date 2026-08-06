import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from config import GRID_HEIGHT, GRID_WIDTH
from game import Game, can_open_gate
from food import Food
from snake import Snake


class CoreLogicTests(unittest.TestCase):
    def test_can_open_gate_requires_food_and_button(self):
        self.assertFalse(can_open_gate(1, True, 2))
        self.assertFalse(can_open_gate(2, False, 2))
        self.assertTrue(can_open_gate(2, True, 2))

    def test_snake_rejects_instant_reverse(self):
        snake = Snake()
        snake.direction = (1, 0)
        snake.pending_direction = (1, 0)

        snake.set_direction((-1, 0))

        self.assertEqual(snake.pending_direction, (1, 0))

    def test_game_queues_one_extra_turn(self):
        game = Game()
        game.snake = Snake()

        game.queue_direction((0, -1))
        game.queue_direction((-1, 0))

        self.assertEqual(game.snake.pending_direction, (0, -1))
        self.assertEqual(game.queued_direction, (-1, 0))

    def test_fire_key_is_f_not_s(self):
        game = Game()

        self.assertTrue(game._is_fire_key(pygame.K_f))
        self.assertFalse(game._is_fire_key(pygame.K_s))

    def test_victory_flyout_waits_for_snake_to_leave_screen(self):
        game = Game()
        game.snake = Snake()
        game.snake.segments = [(5, 5), (4, 5), (3, 5)]
        game.side_scroller_camera_x = 0.0

        self.assertFalse(game._victory_snake_has_left_screen())

        game.snake.segments = [(42, 5), (41, 5), (40, 5)]

        self.assertTrue(game._victory_snake_has_left_screen())

    def test_victory_sequence_fades_then_shakes_before_explosion(self):
        game = Game()
        game.snake = Snake()
        game.snake.segments = [(20, 5), (19, 5), (18, 5)]
        game.boss_pos = (28.0, 10.0)

        game._start_victory_sequence()

        self.assertEqual(game.victory_phase, "fadeout")
        self.assertEqual(game.victory_particles, [])
        self.assertEqual(game._victory_scene_fade(), 0.0)

        game._update_victory(game.victory_fade_duration_ms)

        self.assertEqual(game.victory_phase, "shake")
        self.assertEqual(game.victory_particles, [])
        self.assertEqual(game._victory_scene_fade(), 1.0)

        game._update_victory(game.victory_shake_duration_ms)

        self.assertEqual(game.victory_phase, "explode")
        self.assertTrue(game.victory_particles)

    def test_skip_escape_level_does_not_show_final_story(self):
        game = Game()
        game.game_started = True
        game.level = game.escape_level
        game.snake = Snake()
        game.food = Food()

        game.skip_level()

        self.assertFalse(game.story_active)
        self.assertNotEqual(game.story_next_action, "end_to_menu")
        self.assertTrue(game.side_scroller_active)

    def test_escape_level_clear_continuation_does_not_show_final_story(self):
        game = Game()
        game.game_started = True
        game.level = game.escape_level
        game.level_clear = True
        game.snake = Snake()
        game.food = Food()

        game.skip_level()

        self.assertFalse(game.story_active)
        self.assertNotEqual(game.story_next_action, "end_to_menu")
        self.assertFalse(game.level_clear)
        self.assertTrue(game.side_scroller_active)

    def test_side_scroller_vertical_wrap_translates_whole_snake(self):
        game = Game()
        game.snake = Snake()
        game.snake.segments = [(5, -1), (5, 0), (5, 1)]

        game._apply_side_scroller_bounds()

        self.assertEqual(game.snake.segments, [(5, GRID_HEIGHT - 1), (5, GRID_HEIGHT), (5, GRID_HEIGHT + 1)])

    def test_side_scroller_right_exit_kills_snake(self):
        game = Game()
        game.game_started = True
        game.side_scroller_active = True
        game.snake = Snake()
        game.snake.segments = [(GRID_WIDTH, 5), (GRID_WIDTH - 1, 5)]

        game._apply_side_scroller_bounds()

        self.assertTrue(game.game_over)
        self.assertFalse(game.game_started)

    def test_food_never_spawns_on_blocked_cells(self):
        game = Game()
        game.snake = Snake()
        game.food = Food()
        game.wall_positions = {(10, 10), (11, 10)}
        game.button_pos = (12, 10)
        game.key_pos = (13, 10)

        game.spawn_food()

        blocked = set(game.wall_positions)
        blocked.update(game.snake.segments)
        blocked.add(game.button_pos)
        blocked.add(game.key_pos)
        self.assertNotIn(game.food.position, blocked)

    def test_food_draw_applies_camera_offset(self):
        food = Food((3, 4))
        food.image = None
        surface = pygame.Surface((120, 120), pygame.SRCALPHA)

        food.draw(surface, offset_y=10, offset_x_px=-20)

        self.assertNotEqual(surface.get_at((41, 91)).a, 0)
        self.assertEqual(surface.get_at((61, 91)).a, 0)

    def test_faded_snake_draw_does_not_mutate_sprite_alpha(self):
        snake = Snake()
        snake.segments = [(2, 1), (1, 1)]
        snake.prev_segments = [(1, 1), (0, 1)]
        snake.interp_ready = True
        snake.fading_segments = [{"index_from_tail": 0, "alpha": 80}]
        image = snake.tail_image
        original_alpha = image.get_alpha()
        surface = pygame.Surface((120, 80), pygame.SRCALPHA)

        snake.draw(surface, alpha=1.0)

        self.assertEqual(image.get_alpha(), original_alpha)


if __name__ == "__main__":
    unittest.main()
