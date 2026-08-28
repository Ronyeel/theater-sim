"""
Unit tests for TheaterSimulationBridge in game/backend_bridge.py.
"""

import unittest
from game.backend_bridge import TheaterSimulationBridge


class TestBridge(unittest.TestCase):
    """Tests for Pygame-SimPy synchronization bridge."""

    def test_bridge_initialization_and_reset(self) -> None:
        bridge = TheaterSimulationBridge(
            num_cashiers=2,
            num_servers=2,
            num_ushers=1,
            arrival_interval=0.2,
            food_probability=0.5,
            runtime=60,
            speed=1,
            seed=42,
        )
        self.assertTrue(bridge.is_running)
        self.assertFalse(bridge.is_paused)
        self.assertEqual(bridge.stats.sim_time, 0.0)

        # Advance bridge by 10 real seconds (10 sim minutes at 1x speed)
        bridge.update(10.0)
        self.assertAlmostEqual(bridge.stats.sim_time, 10.0)
        self.assertGreater(bridge.stats.total_arrived, 0)

        # Reset should restore clean initial state
        bridge.reset()
        self.assertEqual(bridge.stats.sim_time, 0.0)
        self.assertEqual(bridge.stats.total_seated, 0)

    def test_bridge_pause_and_resume(self) -> None:
        bridge = TheaterSimulationBridge(2, 2, 2, runtime=60, speed=1, seed=42)
        bridge.update(5.0)
        current_time = bridge.stats.sim_time

        bridge.pause()
        self.assertTrue(bridge.is_paused)
        bridge.update(5.0)
        self.assertEqual(bridge.stats.sim_time, current_time)

        bridge.resume()
        self.assertFalse(bridge.is_paused)
        bridge.update(5.0)
        self.assertGreater(bridge.stats.sim_time, current_time)

    def test_bridge_speed_multiplier(self) -> None:
        bridge = TheaterSimulationBridge(2, 2, 2, runtime=60, speed=5, seed=42)
        bridge.update(2.0)  # 2.0 real seconds * 5 speed = 10.0 sim minutes
        self.assertAlmostEqual(bridge.stats.sim_time, 10.0)

    def test_bridge_runtime_termination(self) -> None:
        bridge = TheaterSimulationBridge(2, 2, 2, runtime=10, speed=1, seed=42)
        bridge.update(15.0)
        self.assertEqual(bridge.stats.sim_time, 10.0)
        self.assertFalse(bridge.is_running)


if __name__ == "__main__":
    unittest.main()
