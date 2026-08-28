"""
Statistical Analysis and Metrics Formatting
Calculates mean wait times, percentiles, and normalized time formats for the theater simulation.
"""

from typing import List, Tuple
import statistics


def average_wait(wait_times: List[float]) -> float:
    """Calculate the mean completed wait time in minutes.

    Args:
        wait_times: List of journey durations (in minutes).

    Returns:
        float: Mean wait time in minutes, or 0.0 if no guests completed their journey.
    """
    return statistics.mean(wait_times) if wait_times else 0.0


def get_average_wait_time(wait_times: List[float]) -> float:
    """Alias for `average_wait` to maintain compatibility with original activity guidelines."""
    return average_wait(wait_times)


def format_minutes_seconds(total_minutes: float) -> Tuple[int, int]:
    """Convert a duration in fractional minutes to an integer (minutes, seconds) pair.

    Args:
        total_minutes: Duration in minutes.

    Returns:
        Tuple[int, int]: (minutes, seconds) where 0 <= seconds < 60.
    """
    total_seconds = max(0, round(float(total_minutes) * 60.0))
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return minutes, seconds


def calculate_wait_time(wait_times: List[float]) -> Tuple[int, int]:
    """Calculate average wait time and return formatted as (minutes, seconds)."""
    return format_minutes_seconds(average_wait(wait_times))
