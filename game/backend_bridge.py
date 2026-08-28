"""Run the activity's SimPy theater model alongside the Pygame world.

The bridge deliberately contains no drawing code.  It keeps the GUI free to
render the existing map and NPCs while using the same resources, timings,
arrival process, and wait-time calculations as the command-line simulation.
"""
import random
import simpy

from src.theater import MovieTheater
from src.simulation import generate_moviegoers
from src.stats import average_wait, format_minutes_seconds


class SimulationStats:
    """Read-only-style snapshot consumed by gameplay systems or HUDs."""

    def __init__(self):
        self.sim_time = 0.0
        self.total_arrived = 0
        self.total_seated = 0
        self.avg_wait = 0.0
        self.cashier_queue = 0
        self.usher_queue = 0
        self.snack_queue = 0
        self.active_guests = 0
        self.goal_met = True
        self.goal_completion_rate = 0.0
        self.cashiers_busy = 0
        self.ushers_busy = 0
        self.servers_busy = 0


class TheaterSimulationBridge:
    """Embed the specification's SimPy process in the running game."""

    def __init__(self, num_cashiers, num_servers, num_ushers,
                 arrival_interval=0.20, food_probability=0.5,
                 runtime=90, speed=1, seed=42, on_arrival=None):
        self.num_cashiers = num_cashiers
        self.num_servers = num_servers
        self.num_ushers = num_ushers
        self.arrival_interval = arrival_interval
        self.food_prob = food_probability
        self.runtime = runtime
        self.speed = speed
        self.seed = seed
        self._on_arrival = on_arrival
        self.stats = SimulationStats()
        self.is_running = False
        self.reset()

    def reset(self):
        """Start a fresh seeded SimPy environment for a new game session."""
        random.seed(self.seed)
        self.env = simpy.Environment()
        self.wait_times = []
        self.theater = MovieTheater(
            self.env, self.num_cashiers, self.num_servers, self.num_ushers
        )
        self._arrival_count = [0]
        self.env.process(generate_moviegoers(
            self.env, self.theater, self.wait_times,
            self.arrival_interval, self.food_prob,
            on_arrival=self._handle_arrival,
        ))
        self.stats = SimulationStats()
        self.is_running = True

    def _handle_arrival(self, moviegoer_id):
        self._arrival_count[0] += 1
        if self._on_arrival:
            self._on_arrival(moviegoer_id)

    def update(self, real_seconds):
        """Advance simulated minutes according to the game's speed setting."""
        if not self.is_running or real_seconds <= 0:
            return
        target = min(self.runtime, self.env.now + real_seconds * self.speed)
        if target > self.env.now:
            self.env.run(until=target)
        self.stats.sim_time = self.env.now
        self.stats.total_arrived = self._arrival_count[0]
        self.stats.total_seated = len(self.wait_times)
        self.stats.avg_wait = average_wait(self.wait_times)
        self.stats.cashier_queue = (self.stats.active_guests
                                    if not self.theater.cashier_available
                                    else len(self.theater.cashier.queue))
        self.stats.usher_queue = (self.stats.active_guests
                                  if self.theater.cashier_available and not self.theater.usher_available
                                  else len(self.theater.usher.queue))
        self.stats.snack_queue = (self.stats.active_guests
                                  if self.theater.cashier_available and self.theater.usher_available
                                  and not self.theater.server_available
                                  else len(self.theater.server.queue))
        self.stats.active_guests = max(0, self.stats.total_arrived - self.stats.total_seated)
        self.stats.goal_met = self.stats.avg_wait <= 10.0
        if self.wait_times:
            self.stats.goal_completion_rate = sum(wait <= 10.0 for wait in self.wait_times) / len(self.wait_times)
        self.stats.cashiers_busy = self.theater.cashier.count
        self.stats.ushers_busy = self.theater.usher.count
        self.stats.servers_busy = self.theater.server.count
        if self.env.now >= self.runtime:
            self.is_running = False
