
from typing import List, Optional, Callable
import random
import simpy

from src.theater import Theater
from src.simulation import generate_moviegoers
from src.stats import average_wait
from src.seating import TheaterSeating


class SimulationStats:

    def __init__(self) -> None:
        self.sim_time: float = 0.0
        self.total_arrived: int = 0
        self.total_seated: int = 0
        self.avg_wait: float = 0.0
        self.cashier_queue: int = 0
        self.usher_queue: int = 0
        self.snack_queue: int = 0
        self.active_guests: int = 0
        self.goal_met: bool = True
        self.goal_completion_rate: float = 0.0
        self.cashiers_busy: int = 0
        self.ushers_busy: int = 0
        self.seats_reserved: int = 0
        self.seats_available: int = 0


class TheaterSimulationBridge:

    def __init__(
        self,
        num_cashiers: int,
        num_servers: int,
        num_ushers: int,
        arrival_interval: float = 0.20,
        food_probability: float = 0.50,
        runtime: float = 90.0,
        speed: int = 1,
        seed: Optional[int] = None,
        on_arrival: Optional[Callable[[int], None]] = None,
    ) -> None:
        self.num_cashiers = int(num_cashiers)
        self.num_servers = int(num_servers)
        self.num_ushers = int(num_ushers)
        self.arrival_interval = float(arrival_interval)
        self.food_prob = float(food_probability)
        self.runtime = float(runtime)
        self.speed = int(speed)
        self.seed = int(seed) if seed is not None else None
        self._on_arrival = on_arrival

        self.stats = SimulationStats()
        self.is_running: bool = False
        self.is_paused: bool = False
        self.wait_times: List[float] = []
        self._arrival_count = [0]
        self.env: simpy.Environment = simpy.Environment()
        self.theater: Theater = Theater(self.env, self.num_cashiers, self.num_servers, self.num_ushers)
        self.seating = TheaterSeating(5, 10)
        self.final_chart = self.seating.snapshot()

        self.reset()

    def reset(self) -> None:
        if self.seed is not None:
            random.seed(self.seed)
        else:
            random.seed()
        self.env = simpy.Environment()
        self.wait_times = []
        self.theater = Theater(
            self.env, self.num_cashiers, self.num_servers, self.num_ushers
        )
        self._arrival_count = [0]
        self.env.process(
            generate_moviegoers(
                self.env,
                self.theater,
                self.wait_times,
                self.arrival_interval,
                self.food_prob,
                on_arrival=self._handle_arrival,
            )
        )
        self.stats = SimulationStats()
        self.is_running = True
        self.is_paused = False
        self.seating.reset()
        self.final_chart = self.seating.snapshot()

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        self.is_paused = False

    def toggle_pause(self) -> bool:
        self.is_paused = not self.is_paused
        return self.is_paused

    def _handle_arrival(self, moviegoer_id: int) -> None:
        self._arrival_count[0] += 1
        if self._on_arrival:
            self._on_arrival(moviegoer_id)

    def update(self, real_seconds: float) -> None:
        if not self.is_running or self.is_paused or real_seconds <= 0:
            return

        target = min(self.runtime, self.env.now + real_seconds * self.speed)
        if target > self.env.now:
            self.env.run(until=target)

        self.stats.sim_time = self.env.now
        self.stats.total_arrived = self._arrival_count[0]
        self.stats.total_seated = len(self.wait_times)
        self.stats.avg_wait = average_wait(self.wait_times)

        if not self.theater.cashier_available:
            self.stats.cashier_queue = self.stats.active_guests
        else:
            self.stats.cashier_queue = len(self.theater.cashier.queue)

        if self.theater.cashier_available and not self.theater.usher_available:
            self.stats.usher_queue = self.stats.active_guests
        else:
            self.stats.usher_queue = len(self.theater.usher.queue)

        if (
            self.theater.cashier_available
            and self.theater.usher_available
            and not self.theater.server_available
        ):
            self.stats.snack_queue = self.stats.active_guests
        else:
            self.stats.snack_queue = len(self.theater.server.queue)

        self.stats.active_guests = max(0, self.stats.total_arrived - self.stats.total_seated)
        self.stats.goal_met = self.stats.avg_wait <= 10.0

        if self.wait_times:
            self.stats.goal_completion_rate = sum(
                w <= 10.0 for w in self.wait_times
            ) / len(self.wait_times)
        else:
            self.stats.goal_completion_rate = 1.0

        self.stats.cashiers_busy = self.theater.cashier.count
        self.stats.ushers_busy = self.theater.usher.count
        self.stats.servers_busy = self.theater.server.count
        self.stats.seats_reserved = self.seating.reserved_seats
        self.stats.seats_available = self.seating.available_seats

        if self.env.now >= self.runtime:
            if self.is_running:
                self.final_chart = self.seating.snapshot()
            self.is_running = False
