"""
Unit tests for the SimPy MovieTheater resource model in src/theater.py.
"""

import unittest
import simpy
from src.theater import MovieTheater


class TestTheater(unittest.TestCase):
    """Tests for MovieTheater SimPy resource management."""

    def setUp(self) -> None:
        self.env = simpy.Environment()

    def test_resource_initialization(self) -> None:
        theater = MovieTheater(self.env, num_cashiers=3, num_servers=2, num_ushers=1)
        self.assertEqual(theater.num_cashiers, 3)
        self.assertEqual(theater.num_servers, 2)
        self.assertEqual(theater.num_ushers, 1)
        self.assertEqual(theater.cashier.capacity, 3)
        self.assertEqual(theater.server.capacity, 2)
        self.assertEqual(theater.usher.capacity, 1)

    def test_availability_flags(self) -> None:
        theater = MovieTheater(self.env, num_cashiers=2, num_servers=0, num_ushers=1)
        self.assertTrue(theater.cashier_available)
        self.assertFalse(theater.server_available)
        self.assertTrue(theater.usher_available)

    def test_negative_capacity_clamped(self) -> None:
        theater = MovieTheater(self.env, num_cashiers=-1, num_servers=-5, num_ushers=0)
        self.assertEqual(theater.num_cashiers, 0)
        self.assertEqual(theater.num_servers, 0)
        self.assertEqual(theater.num_ushers, 0)
        # Internal SimPy resources must have at least 1 capacity
        self.assertEqual(theater.cashier.capacity, 1)
        self.assertFalse(theater.cashier_available)

    def test_service_delay_execution(self) -> None:
        theater = MovieTheater(self.env, num_cashiers=1, num_servers=1, num_ushers=1)

        def runner():
            start = self.env.now
            yield self.env.process(theater.check_ticket(1))
            self.assertAlmostEqual(round(self.env.now - start, 5), 0.05)

            start = self.env.now
            yield self.env.process(theater.purchase_ticket(1))
            duration = round(self.env.now - start, 5)
            self.assertTrue(1.0 <= duration <= 3.0)

            start = self.env.now
            yield self.env.process(theater.buy_food(1))
            duration = round(self.env.now - start, 5)
            self.assertTrue(1.0 <= duration <= 5.0)

        self.env.process(runner())
        self.env.run()


if __name__ == "__main__":
    unittest.main()
