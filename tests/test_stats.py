"""
Unit tests for statistical calculation and formatting functions in src/stats.py.
"""

import unittest
from src.stats import average_wait, get_average_wait_time, format_minutes_seconds, calculate_wait_time


class TestStats(unittest.TestCase):
    """Tests for wait time metrics and formatting."""

    def test_average_wait_normal(self) -> None:
        durations = [2.0, 4.0, 6.0, 8.0]
        self.assertAlmostEqual(average_wait(durations), 5.0)
        self.assertAlmostEqual(get_average_wait_time(durations), 5.0)

    def test_average_wait_single(self) -> None:
        self.assertAlmostEqual(average_wait([7.5]), 7.5)

    def test_average_wait_empty(self) -> None:
        self.assertEqual(average_wait([]), 0.0)
        self.assertEqual(get_average_wait_time([]), 0.0)

    def test_format_minutes_seconds_exact_minutes(self) -> None:
        self.assertEqual(format_minutes_seconds(5.0), (5, 0))
        self.assertEqual(format_minutes_seconds(0.0), (0, 0))

    def test_format_minutes_seconds_fractional(self) -> None:
        self.assertEqual(format_minutes_seconds(1.5), (1, 30))
        self.assertEqual(format_minutes_seconds(0.5), (0, 30))
        self.assertEqual(format_minutes_seconds(10.25), (10, 15))
        self.assertEqual(format_minutes_seconds(0.05), (0, 3))

    def test_format_minutes_seconds_negative_clamp(self) -> None:
        self.assertEqual(format_minutes_seconds(-2.0), (0, 0))

    def test_calculate_wait_time_integration(self) -> None:
        self.assertEqual(calculate_wait_time([1.5, 2.5]), (2, 0))
        self.assertEqual(calculate_wait_time([]), (0, 0))


if __name__ == "__main__":
    unittest.main()
