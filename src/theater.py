import simpy
import random

class MovieTheater:
    """SimPy resources and service times from the theater-management brief.

    Simulation time is measured in minutes.
    """
    def __init__(self, env, num_cashiers, num_servers, num_ushers):
        self.env = env
        self.num_cashiers = max(0, int(num_cashiers))
        self.num_servers = max(0, int(num_servers))
        self.num_ushers = max(0, int(num_ushers))
        # SimPy resources require positive capacity. Availability flags retain
        # a user-entered zero as a genuinely closed service point.
        self.cashier = simpy.Resource(env, max(1, self.num_cashiers))
        self.server = simpy.Resource(env, max(1, self.num_servers))
        self.usher = simpy.Resource(env, max(1, self.num_ushers))

    @property
    def cashier_available(self): return self.num_cashiers > 0

    @property
    def server_available(self): return self.num_servers > 0

    @property
    def usher_available(self): return self.num_ushers > 0

    def purchase_ticket(self, moviegoer):
        # Box-office transaction: 1–3 minutes.
        yield self.env.timeout(random.randint(1, 3))

    def check_ticket(self, moviegoer):
        # Usher scan: 3 seconds, expressed as a fraction of a minute.
        yield self.env.timeout(3 / 60)

    def buy_food(self, moviegoer):
        # Concession transaction: 1–5 minutes.
        yield self.env.timeout(random.randint(1, 5))
