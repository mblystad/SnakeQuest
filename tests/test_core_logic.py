import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

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
