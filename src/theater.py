
from typing import Generator, Any
import random
import simpy


class Theater:

    def __init__(
        self,
        env: simpy.Environment,
        num_cashiers: int,
        num_servers: int,
        num_ushers: int,
    ) -> None:
        self.env = env
        self.num_cashiers = max(0, int(num_cashiers))
        self.num_servers  = max(0, int(num_servers))
        self.num_ushers   = max(0, int(num_ushers))

        self.cashier = simpy.Resource(env, capacity=max(1, self.num_cashiers))
        self.server  = simpy.Resource(env, capacity=max(1, self.num_servers))
        self.usher   = simpy.Resource(env, capacity=max(1, self.num_ushers))


    @property
    def cashier_available(self) -> bool:
        return self.num_cashiers > 0

    @property
    def server_available(self) -> bool:
        return self.num_servers > 0

    @property
    def usher_available(self) -> bool:
        return self.num_ushers > 0


    def purchase_ticket(self, moviegoer: int) -> Generator[Any, None, None]:
        yield self.env.timeout(random.randint(1, 3))

    def check_ticket(self, moviegoer: int) -> Generator[Any, None, None]:
        yield self.env.timeout(3 / 60)

    def sell_food(self, moviegoer: int) -> Generator[Any, None, None]:
        yield self.env.timeout(random.randint(1, 5))

    buy_food = sell_food

MovieTheater = Theater
