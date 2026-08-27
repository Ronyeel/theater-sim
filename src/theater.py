import simpy
import random

class MovieTheater:
    """SimPy resources and service times from the theater-management brief.

    Simulation time is measured in minutes.
    """
    def __init__(self, env, num_cashiers, num_servers, num_ushers):
        self.env = env
        self.cashier = simpy.Resource(env, num_cashiers)
        self.server = simpy.Resource(env, num_servers)
        self.usher = simpy.Resource(env, num_ushers)

    def purchase_ticket(self, moviegoer):
        # Box-office transaction: 1–3 minutes.
        yield self.env.timeout(random.randint(1, 3))

    def check_ticket(self, moviegoer):
        # Usher scan: 3 seconds, expressed as a fraction of a minute.
        yield self.env.timeout(3 / 60)

    def buy_food(self, moviegoer):
        # Concession transaction: 1–5 minutes.
        yield self.env.timeout(random.randint(1, 5))
