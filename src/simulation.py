"""
Simulation Processes and Generators
Simulates moviegoer arrivals and their progression through ticketing, usher check,
optional concessions, and seating in the auditorium.
"""

from typing import Generator, List, Callable, Optional, Any
import random
import simpy
from src.theater import MovieTheater


def moviegoer_journey(
    env: simpy.Environment,
    moviegoer_id: int,
    theater: MovieTheater,
    wait_times: List[float],
    food_probability: float = 0.5,
) -> Generator[Any, None, None]:
    """Simulate a single guest's journey through the movie theater.

    Steps:
    1. Wait in line and purchase ticket from cashier (if available).
    2. Wait in line and have ticket verified by usher (if available).
    3. With probability `food_probability`, wait and purchase snacks from concession server.
    4. Record total time elapsed from arrival to seating.

    Args:
        env: SimPy simulation environment.
        moviegoer_id: Unique integer identifier for the guest.
        theater: MovieTheater instance containing resource pools.
        wait_times: Output list where total journey durations (in minutes) are appended.
        food_probability: Probability (0.0 to 1.0) that this guest visits concession stand.
    """
    arrival_time = env.now

    # 1. Box Office Ticketing
    if not theater.cashier_available:
        yield env.event()
        return
    with theater.cashier.request() as request:
        yield request
        yield env.process(theater.purchase_ticket(moviegoer_id))

    # 2. Usher Checkpoint
    if not theater.usher_available:
        yield env.event()
        return
    with theater.usher.request() as request:
        yield request
        yield env.process(theater.check_ticket(moviegoer_id))

    # 3. Concession Stand (Optional)
    if random.random() < food_probability:
        if not theater.server_available:
            yield env.event()
            return
        with theater.server.request() as request:
            yield request
            yield env.process(theater.buy_food(moviegoer_id))

    # 4. Completed Journey
    wait_times.append(env.now - arrival_time)


def generate_moviegoers(
    env: simpy.Environment,
    theater: MovieTheater,
    wait_times: List[float],
    arrival_interval: float = 0.20,
    food_probability: float = 0.50,
    on_arrival: Optional[Callable[[int], None]] = None,
) -> Generator[Any, None, None]:
    """Seed initial queue and periodically generate new arriving moviegoers.

    According to the problem specification:
    - 3 moviegoers start already waiting in line at t = 0.
    - Subsequent guests arrive at intervals of `arrival_interval` minutes.

    Args:
        env: SimPy simulation environment.
        theater: MovieTheater instance.
        wait_times: Output list for completed wait times.
        arrival_interval: Time (minutes) between subsequent arrivals.
        food_probability: Probability of purchasing concessions.
        on_arrival: Optional callback invoked when a guest arrives (useful for GUI bridge).
    """
    # Initial 3 guests already in line at opening
    for moviegoer_id in range(3):
        if on_arrival:
            on_arrival(moviegoer_id)
        env.process(
            moviegoer_journey(
                env, moviegoer_id, theater, wait_times, food_probability
            )
        )

    # Continuous arrival stream
    moviegoer_id = 3
    while True:
        yield env.timeout(arrival_interval)
        if on_arrival:
            on_arrival(moviegoer_id)
        env.process(
            moviegoer_journey(
                env, moviegoer_id, theater, wait_times, food_probability
            )
        )
        moviegoer_id += 1
