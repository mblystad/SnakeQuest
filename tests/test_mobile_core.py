import unittest

from mobile_core import DOWN, LEFT, RIGHT, UP, MobileGameSession, can_open_gate


class MobileCoreTests(unittest.TestCase):
    def test_can_open_gate_requires_food_and_button(self):
        self.assertFalse(can_open_gate(1, True, 2))
        self.assertFalse(can_open_gate(2, False, 2))
        self.assertTrue(can_open_gate(2, True, 2))

    def test_reverse_direction_is_blocked(self):
        session = MobileGameSession()
        session.start_level()
        self.assertEqual(session.snake.pending_direction, RIGHT)
        session.queue_direction(LEFT)
        self.assertEqual(session.snake.pending_direction, RIGHT)

    def test_food_never_spawns_on_blocked_cells(self):
        session = MobileGameSession(random_seed=7)
        session.start_level()
        blocked = set(session.walls)
        blocked.update(session.snake.segments)
        blocked.add(session.button_pos)
        blocked.add(session.key_pos)
        self.assertNotIn(session.food_pos, blocked)

    def test_level_clears_when_open_gate_is_reached(self):
        session = MobileGameSession()
        session.start_level()
        session.snake.segments = [(5, 5), (4, 5), (3, 5)]
        session.snake.direction = RIGHT
        session.snake.pending_direction = RIGHT
        session.level_food_eaten = session.required_food_for_level()
        session.button_pos = (4, 5)
        session.key_pos = (6, 5)
        session.food_pos = None
        session._step_once(session.settings.tick_interval_ms)
        self.assertEqual(session.state, "level_clear")

    def test_queue_direction_applies_next_turn_after_lock(self):
        session = MobileGameSession()
        session.start_level()
        session.queue_direction(UP)
        session.queue_direction(LEFT)
        self.assertEqual(session.snake.pending_direction, UP)
        self.assertEqual(session.queued_direction, LEFT)
        session._step_once(session.settings.tick_interval_ms)
        self.assertEqual(session.snake.direction, UP)
        self.assertEqual(session.snake.pending_direction, LEFT)

    def test_replay_restores_level_checkpoint(self):
        session = MobileGameSession(random_seed=3)
        session.start_level()
        session.level_start_score = 4
        session.level_start_time_ms = 1200
        session.score = 9
        session.elapsed_time_ms = 3000
        session.replay_level()
        self.assertEqual(session.score, 4)
        self.assertEqual(session.elapsed_time_ms, 1200)
        self.assertEqual(session.state, "loading")


if __name__ == "__main__":
    unittest.main()
