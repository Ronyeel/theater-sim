"""
Movie Theater Resource Model
Defines SimPy resources and service delays for box-office cashiers, ushers, and concession servers.
"""

from typing import Generator, Any
import random
import simpy


class MovieTheater:
    """SimPy resource and service manager for the movie theater.

    Attributes:
        env (simpy.Environment): The SimPy simulation environment.
        num_cashiers (int): Number of active box-office cashiers.
        num_servers (int): Number of active concession stand servers.
        num_ushers (int): Number of active ticket-checking ushers.
        cashier (simpy.Resource): SimPy resource pool for box-office ticketing.
        server (simpy.Resource): SimPy resource pool for concessions.
        usher (simpy.Resource): SimPy resource pool for usher checkpoint.
    """

    def __init__(
        self,
        env: simpy.Environment,
        num_cashiers: int,
        num_servers: int,
        num_ushers: int,
    ) -> None:
        self.env = env
        self.num_cashiers = max(0, int(num_cashiers))
        self.num_servers = max(0, int(num_servers))
        self.num_ushers = max(0, int(num_ushers))

        # SimPy resources require capacity >= 1. Availability flags retain
        # zero-capacity configurations as closed service points.
        self.cashier = simpy.Resource(env, capacity=max(1, self.num_cashiers))
        self.server = simpy.Resource(env, capacity=max(1, self.num_servers))
        self.usher = simpy.Resource(env, capacity=max(1, self.num_ushers))

    @property
    def cashier_available(self) -> bool:
        """Return True if at least one cashier is staffed."""
        return self.num_cashiers > 0

    @property
    def server_available(self) -> bool:
        """Return True if at least one concession server is staffed."""
        return self.num_servers > 0

    @property
    def usher_available(self) -> bool:
        """Return True if at least one usher is staffed."""
        return self.num_ushers > 0

    def purchase_ticket(self, moviegoer: int) -> Generator[Any, None, None]:
        """Simulate box-office transaction delay (1 to 3 minutes)."""
        yield self.env.timeout(random.randint(1, 3))

    def check_ticket(self, moviegoer: int) -> Generator[Any, None, None]:
        """Simulate usher scanning ticket (3 seconds = 3/60 of a minute)."""
        yield self.env.timeout(3.0 / 60.0)

    def buy_food(self, moviegoer: int) -> Generator[Any, None, None]:
        """Simulate concession stand transaction delay (1 to 5 minutes)."""
        yield self.env.timeout(random.randint(1, 5))
