

from typing import Generator, List, Callable, Optional, Any
import random
import simpy

from src.theater import Theater






def go_to_movies(
    env: simpy.Environment,
    moviegoer: int,
    theater: Theater,
    wait_times: List[float],
    food_probability: float = 0.5,
) -> Generator[Any, None, None]:
   
    arrival_time = env.now


    while not theater.cashier_available:
        yield env.timeout(0.1)
    with theater.cashier.request() as request:
        yield request
        while not theater.cashier_available:
            yield env.timeout(0.1)
        yield env.process(theater.purchase_ticket(moviegoer))


    while not theater.usher_available:
        yield env.timeout(0.1)
    with theater.usher.request() as request:
        yield request
        while not theater.usher_available:
            yield env.timeout(0.1)
        yield env.process(theater.check_ticket(moviegoer))


    if random.random() < food_probability:
        while not theater.server_available:
            yield env.timeout(0.1)
        with theater.server.request() as request:
            yield request
            while not theater.server_available:
                yield env.timeout(0.1)
            yield env.process(theater.sell_food(moviegoer))


    wait_times.append(env.now - arrival_time)


def run_theater(
    env: simpy.Environment,
    theater: Theater,
    wait_times: List[float],
    arrival_interval: float = 0.20,
    food_probability: float = 0.50,
    on_arrival: Optional[Callable[[int], None]] = None,
) -> Generator[Any, None, None]:
   

    # The activity specification begins with three guests already in line.
    for moviegoer in range(3):
        if on_arrival:
            on_arrival(moviegoer)
        env.process(
            go_to_movies(env, moviegoer, theater, wait_times, food_probability)
        )

    moviegoer = 3
    while True:
        yield env.timeout(arrival_interval)
        if on_arrival:
            on_arrival(moviegoer)
        env.process(
            go_to_movies(env, moviegoer, theater, wait_times, food_probability)
        )
        moviegoer += 1



moviegoer_journey  = go_to_movies
generate_moviegoers = run_theater
