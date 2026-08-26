try:
    from importlib import import_module

    simpy = import_module("simpy")
except ModuleNotFoundError as exc:
    if exc.name == "simpy":
        raise ModuleNotFoundError(
            "The 'simpy' package is required. Install it with: python -m pip install simpy"
        ) from exc
    raise
from src.theater import MovieTheater
from src.simulation import generate_moviegoers
from src.stats import average_wait, format_minutes_seconds

def run_simulation(num_cashiers, num_ushers, num_servers,
                    arrival_interval=0.2, food_probability=0.5, runtime=90):
    wait_times = []
    env = simpy.Environment()
    theater = MovieTheater(env, num_cashiers, num_ushers, num_servers)
    env.process(generate_moviegoers(env, theater, wait_times, arrival_interval, food_probability))
    env.run(until=runtime)
    return wait_times


def get_user_input():
    num_cashiers = input("Input # of cashiers working: ")
    num_ushers = input("Input # of ushers working: ")
    num_servers = input("Input # of servers working: ")

    values = [num_cashiers, num_ushers, num_servers]
    if all(v.isdigit() for v in values):
        return [int(v) for v in values]
    else:
        print("Invalid input. Using default: 1 cashier, 1 usher, 1 server.")
        return [1, 1, 1]


def main():
    num_cashiers, num_ushers, num_servers = get_user_input()
    wait_times = run_simulation(num_cashiers, num_ushers, num_servers)

    if not wait_times:
        print("No moviegoers completed the process in this runtime.")
        return

    minutes, seconds = format_minutes_seconds(average_wait(wait_times))
    print(f"\nSimulated {len(wait_times)} moviegoers.")
    print(f"The average wait time is {minutes} minutes and {seconds} seconds.")


if __name__ == "__main__":
    main()