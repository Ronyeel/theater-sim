
from typing import List, Tuple
import statistics


def get_average_wait_time(wait_times: List[float]) -> float:
    return statistics.mean(wait_times) if wait_times else 0.0


def calculate_wait_time(wait_times: List[float]) -> Tuple[int, int]:
    return format_minutes_seconds(get_average_wait_time(wait_times))


def average_wait(wait_times: List[float]) -> float:
    return statistics.mean(wait_times) if wait_times else 0.0


def format_minutes_seconds(total_minutes: float) -> Tuple[int, int]:
    total_seconds = max(0, round(float(total_minutes) * 60.0))
    return total_seconds // 60, total_seconds % 60
