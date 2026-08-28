"""
CinePlex Dreams — Theater Simulation Launcher
Unified entry point supporting both graphical 2D visualization (Pygame)
and discrete-event queuing simulation (SimPy CLI).

Usage:
  python main.py               # Launch GUI Interactive Game
  python main.py --gui         # Explicitly launch GUI mode
  python main.py --cli         # Run CLI Discrete-Event Simulation
  python main.py --cli -c 3 -u 2 -s 2 --runtime 90
  python main.py --cli --interactive
"""

import os
import sys
import subprocess


def _ensure_environment() -> None:
    """Ensure required packages exist, or automatically re-execute using local .venv."""
    needs_pygame = "--cli" not in sys.argv
    try:
        import simpy  # noqa: F401
        if needs_pygame:
            import pygame  # noqa: F401
    except ImportError:
        # Search for project virtual environment
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

        # If venv not found or failed, print clean diagnostic guidance
        print("\n" + "=" * 60)
        print(" [!] Missing Required Dependencies for CinePlex Dreams")
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

import argparse
import random
from typing import List, Tuple, Optional
import simpy

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
    seed: int = RANDOM_SEED,
) -> List[float]:
    """Execute a single deterministic SimPy simulation run and return completed wait times.

    Args:
        num_cashiers: Number of box-office cashiers (>= 1).
        num_servers: Number of concession servers (>= 1).
        num_ushers: Number of ticket-checking ushers (>= 1).
        arrival_interval: Minutes between guest arrivals (> 0).
        food_probability: Probability that a guest visits concession stand (0.0 to 1.0).
        runtime: Total simulation time in minutes (> 0).
        seed: Random generator seed for reproducibility.

    Returns:
        List[float]: List of journey durations (in minutes) for completed moviegoers.
    """
    if min(num_cashiers, num_ushers, num_servers) < 1:
        raise ValueError("Cashiers, ushers, and servers must each be at least 1")
    if arrival_interval <= 0 or runtime <= 0:
        raise ValueError("Arrival interval and runtime must be positive")
    if not 0.0 <= food_probability <= 1.0:
        raise ValueError("Food probability must be between 0.0 and 1.0")

    random.seed(seed)
    wait_times: List[float] = []
    env = simpy.Environment()
    theater = MovieTheater(env, num_cashiers, num_servers, num_ushers)
    env.process(
        generate_moviegoers(
            env, theater, wait_times, arrival_interval, food_probability
        )
    )
    env.run(until=runtime)
    return wait_times


def get_interactive_user_input() -> Tuple[int, int, int]:
    """Prompt user in console for cashier, server, and usher staffing counts."""
    print("\n--- Movie Theater Simulation Setup ---")
    c_str = input("Input # of cashiers working [default: 1]: ").strip()
    s_str = input("Input # of servers working  [default: 1]: ").strip()
    u_str = input("Input # of ushers working   [default: 1]: ").strip()

    num_cashiers = int(c_str) if c_str.isdigit() and int(c_str) > 0 else 1
    num_servers = int(s_str) if s_str.isdigit() and int(s_str) > 0 else 1
    num_ushers = int(u_str) if u_str.isdigit() and int(u_str) > 0 else 1

    print(f"Configured: {num_cashiers} cashier(s), {num_servers} server(s), {num_ushers} usher(s).\n")
    return num_cashiers, num_servers, num_ushers


def execute_cli_mode(args: argparse.Namespace) -> None:
    """Run discrete-event simulation in console mode and print performance report."""
    if args.interactive:
        num_cashiers, num_servers, num_ushers = get_interactive_user_input()
    else:
        num_cashiers = args.cashiers
        num_servers = args.servers
        num_ushers = args.ushers

    print("=" * 60)
    print("      CINEPLEX DREAMS :: DISCRETE-EVENT SIMULATION")
    print("=" * 60)
    print(f"  Cashiers (Box Office)  : {num_cashiers}")
    print(f"  Servers (Concession)   : {num_servers}")
    print(f"  Ushers (Checkpoint)    : {num_ushers}")
    print(f"  Arrival Gap            : {args.arrival_interval * 60:.1f} sec ({args.arrival_interval} min)")
    print(f"  Concession Probability : {args.food_prob * 100:.0f}%")
    print(f"  Simulation Runtime     : {args.runtime} minutes")
    print(f"  Random Seed            : {args.seed}")
    print("-" * 60)
    print("Running simulation...")

    wait_times = run_simulation(
        num_cashiers=num_cashiers,
        num_servers=num_servers,
        num_ushers=num_ushers,
        arrival_interval=args.arrival_interval,
        food_probability=args.food_prob,
        runtime=args.runtime,
        seed=args.seed,
    )

    if not wait_times:
        print("\nNo moviegoers completed the process within the configured runtime.")
        print("=" * 60)
        return

    avg_wait = average_wait(wait_times)
    minutes, seconds = format_minutes_seconds(avg_wait)
    target_met = avg_wait <= 10.0
    status_str = "PASSED (<= 10 min)" if target_met else "FAILED (> 10 min)"

    print(f"Completed Moviegoers   : {len(wait_times)}")
    print(f"Average Wait Time      : {minutes} minutes and {seconds:02d} seconds ({avg_wait:.2f} min)")
    print(f"10-Minute Target       : {status_str}")
    print("=" * 60)


def execute_gui_mode() -> None:
    """Launch the Pygame graphical simulation."""
    from game.__main__ import main as run_game
    run_game()


def main() -> None:
    """Main CLI argument parser and mode dispatcher."""
    parser = argparse.ArgumentParser(
        description="CinePlex Dreams: Movie Theater Queuing Simulation (SimPy + Pygame)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                  # Launch GUI Game
  python main.py --cli            # Run SimPy simulation in CLI
  python main.py --cli -c 3 -u 2 -s 2 --runtime 120
  python main.py --cli --interactive
        """,
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--cli", action="store_true", help="Run in Command-Line Interface (CLI) simulation mode"
    )
    mode_group.add_argument(
        "--gui", action="store_true", help="Run in Graphical User Interface (GUI) mode (default)"
    )

    # Simulation parameters
    parser.add_argument(
        "-c", "--cashiers", type=int, default=1, help="Number of box-office cashiers (default: 1)"
    )
    parser.add_argument(
        "-s", "--servers", type=int, default=1, help="Number of concession servers (default: 1)"
    )
    parser.add_argument(
        "-u", "--ushers", type=int, default=1, help="Number of ticket-checking ushers (default: 1)"
    )
    parser.add_argument(
        "-r", "--runtime", type=float, default=90.0, help="Simulation runtime in minutes (default: 90.0)"
    )
    parser.add_argument(
        "-a", "--arrival-interval", type=float, default=0.20, help="Minutes between arrivals (default: 0.20)"
    )
    parser.add_argument(
        "-f", "--food-prob", type=float, default=0.50, help="Probability of buying food (default: 0.50)"
    )
    parser.add_argument(
        "--seed", type=int, default=RANDOM_SEED, help=f"Random seed (default: {RANDOM_SEED})"
    )
    parser.add_argument(
        "-i", "--interactive", action="store_true", help="Prompt for staff counts interactively in console"
    )

    args = parser.parse_args()

    if args.cli:
        execute_cli_mode(args)
    else:
        execute_gui_mode()


if __name__ == "__main__":
    main()
