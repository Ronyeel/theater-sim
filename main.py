import simpy
import random
from src.theater import MovieTheater
from src.simulation import generate_moviegoers
from src.stats import average_wait, format_minutes_seconds
from game.settings import RANDOM_SEED

def run_simulation(num_cashiers, num_servers, num_ushers,
                    arrival_interval=0.2, food_probability=0.5, runtime=90,
                    seed=RANDOM_SEED):
    """Run one reproducible theater scenario and return completed wait times."""
    if min(num_cashiers, num_ushers, num_servers) < 1:
        raise ValueError("Cashiers, ushers, and servers must each be at least 1")
    if arrival_interval <= 0 or runtime <= 0:
        raise ValueError("Arrival interval and runtime must be positive")
    if not 0 <= food_probability <= 1:
        raise ValueError("Food probability must be between 0 and 1")
    random.seed(seed)
    wait_times = []
    env = simpy.Environment()
    theater = MovieTheater(env, num_cashiers, num_servers, num_ushers)
    env.process(generate_moviegoers(env, theater, wait_times, arrival_interval, food_probability))
    env.run(until=runtime)
    return wait_times


def get_user_input():
    num_cashiers = input("Input # of cashiers working: ")
    num_servers = input("Input # of servers working: ")
    num_ushers = input("Input # of ushers working: ")

    values = [num_cashiers, num_ushers, num_servers]
    if all(v.isdigit() and int(v) > 0 for v in values):
        return [int(num_cashiers), int(num_servers), int(num_ushers)]
    else:
        print("Invalid input. Using default: 1 cashier, 1 usher, 1 server.")
        return [1, 1, 1]


def main():
    random.seed(RANDOM_SEED)
    num_cashiers, num_servers, num_ushers = get_user_input()
    wait_times = run_simulation(num_cashiers, num_servers, num_ushers)

    if not wait_times:
        print("No moviegoers completed the process in this runtime.")
        return

    minutes, seconds = format_minutes_seconds(average_wait(wait_times))
    print("Running simulation...")
    print(f"Simulated {len(wait_times)} completed moviegoers.")
    print(f"The average wait time is {minutes} minutes and {seconds} seconds.")


if __name__ == "__main__":
    main()
