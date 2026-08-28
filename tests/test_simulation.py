"""
Unit tests for customer journey processes and simulation runner in src/simulation.py and main.py.
"""

import unittest
import simpy
from src.theater import MovieTheater
from src.simulation import moviegoer_journey, generate_moviegoers
from main import run_simulation


class TestSimulation(unittest.TestCase):
    """Tests for discrete-event simulation processes."""

    def test_run_simulation_deterministic(self) -> None:
        runs_1 = run_simulation(num_cashiers=2, num_servers=2, num_ushers=2, runtime=30, seed=42)
        runs_2 = run_simulation(num_cashiers=2, num_servers=2, num_ushers=2, runtime=30, seed=42)
        self.assertEqual(len(runs_1), len(runs_2))
        self.assertEqual(runs_1, runs_2)
        self.assertGreater(len(runs_1), 0)

    def test_run_simulation_validation_errors(self) -> None:
        with self.assertRaises(ValueError):
            run_simulation(num_cashiers=0, num_servers=1, num_ushers=1)
        with self.assertRaises(ValueError):
            run_simulation(num_cashiers=1, num_servers=1, num_ushers=1, arrival_interval=-0.1)
        with self.assertRaises(ValueError):
            run_simulation(num_cashiers=1, num_servers=1, num_ushers=1, runtime=0)
        with self.assertRaises(ValueError):
            run_simulation(num_cashiers=1, num_servers=1, num_ushers=1, food_probability=1.5)

    def test_arrival_callback_invocations(self) -> None:
        arrived_ids = []
        env = simpy.Environment()
        theater = MovieTheater(env, num_cashiers=2, num_servers=2, num_ushers=2)
        wait_times = []

        def on_arrive(m_id: int):
            arrived_ids.append(m_id)

        env.process(
            generate_moviegoers(
                env, theater, wait_times,
                arrival_interval=1.0,
                food_probability=0.5,
                on_arrival=on_arrive,
            )
        )
        env.run(until=5.5)

        # At t=0: 3 guests (0, 1, 2). Then at t=1(3), t=2(4), t=3(5), t=4(6), t=5(7). Total = 8.
        self.assertEqual(len(arrived_ids), 8)
        self.assertEqual(arrived_ids, list(range(8)))


if __name__ == "__main__":
    unittest.main()
