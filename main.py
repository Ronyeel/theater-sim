import os
import sys
import subprocess
import random
from typing import List, Optional
import simpy

def _ensure_environment() -> None:
    try:
        import simpy
        import pygame
    except ImportError:
        project_dir = os.path.dirname(os.path.abspath(__file__))
        venv_candidates = [
            os.path.join(project_dir, ".venv", "Scripts", "python.exe"),
            os.path.join(project_dir, ".venv", "bin", "python"),
            os.path.join(project_dir, "venv", "Scripts", "python.exe"),
            os.path.join(project_dir, "venv", "bin", "python"),
        ]
        for venv_python in venv_candidates:
            if os.path.exists(venv_python) and os.path.abspath(sys.executable) != os.path.abspath(venv_python):
                try:
                    result = subprocess.run([venv_python] + sys.argv, check=False)
                    sys.exit(result.returncode)
                except Exception:
                    pass

        print("\n" + "=" * 60)
        print(" [!] Missing Required Dependencies for Theater Simulation")
        print("=" * 60)
        print(" Pygame or SimPy is not installed in the active Python environment.")
        print(f" Current Python interpreter: {sys.executable}")
        print("\n Please activate your virtual environment:")
        print("   On Windows PowerShell: .venv\\Scripts\\Activate.ps1")
        print("   On Windows Command:    .venv\\Scripts\\activate.bat")
        print("   On macOS / Linux:      source .venv/bin/activate")
        print("\n Or install dependencies directly:")
        print("   pip install -r requirements.txt")
        print("=" * 60 + "\n")
        sys.exit(1)


_ensure_environment()

from src.theater import MovieTheater
from src.simulation import generate_moviegoers
from src.stats import average_wait, format_minutes_seconds
from game.settings import (
    RANDOM_SEED, DEFAULT_CASHIERS, DEFAULT_USHERS,
    DEFAULT_SERVERS, DEFAULT_RUNTIME, DEFAULT_ARRIVAL_INTERVAL,
    DEFAULT_FOOD_PROB,
)


def run_simulation(
    num_cashiers: int,
    num_servers: int,
    num_ushers: int,
    arrival_interval: float = DEFAULT_ARRIVAL_INTERVAL,
    food_probability: float = DEFAULT_FOOD_PROB,
    runtime: float = DEFAULT_RUNTIME,
    seed: Optional[int] = RANDOM_SEED,
) -> List[float]:
    if min(num_cashiers, num_ushers, num_servers) < 1:
        raise ValueError("Cashiers, ushers, and servers must each be at least 1")
    if arrival_interval <= 0 or runtime <= 0:
        raise ValueError("Arrival interval and runtime must be positive")
    if not 0.0 <= food_probability <= 1.0:
        raise ValueError("Food probability must be between 0.0 and 1.0")

    if seed is not None:
        random.seed(seed)
    else:
        random.seed()
    env = simpy.Environment()
    theater = MovieTheater(env, num_cashiers, num_servers, num_ushers)
    wait_times: List[float] = []

    env.process(
        generate_moviegoers(
            env,
            theater,
            wait_times,
            arrival_interval=arrival_interval,
            food_probability=food_probability,
        )
    )
    env.run(until=runtime)
    return wait_times


def main() -> None:
    if any(arg in sys.argv for arg in ("--seats", "-s", "--cli", "--book")):
        from src.seating import run_seating_cli
        run_seating_cli()
        return

    from game.__main__ import main as run_game
    run_game()


if __name__ == "__main__":
    main()
