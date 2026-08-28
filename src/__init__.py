"""
Theater Simulation Backend
Pure discrete-event simulation package powered by SimPy.
"""

from src.theater import MovieTheater
from src.simulation import moviegoer_journey, generate_moviegoers
from src.stats import average_wait, get_average_wait_time, format_minutes_seconds, calculate_wait_time

__all__ = [
    "MovieTheater",
    "moviegoer_journey",
    "generate_moviegoers",
    "average_wait",
    "get_average_wait_time",
    "format_minutes_seconds",
    "calculate_wait_time",
]
