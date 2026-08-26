import simpy
import random

class MovieTheater:
    def __init__(self, env, num_cashiers, num_ushers, num_servers):
        self.env = env
        self.cashier = simpy.Resource(env, num_cashiers)
        self.usher = simpy.Resource(env, num_ushers)
        self.server = simpy.Resource(env, num_servers)

    def purchase_ticket(self, moviegoer):
        yield self.env.timeout(random.uniform(1, 3))

    def check_ticket(self, moviegoer):
        yield self.env.timeout(5 / 60)

    def buy_food(self, moviegoer):
        yield self.env.timeout(random.uniform(1, 4))