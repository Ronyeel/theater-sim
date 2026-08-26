import random

def moviegoer_journey(env, moviegoer_id, theater, wait_times, food_probability):
    arrival_time = env.now

    with theater.cashier.request() as request:
        yield request
        yield env.process(theater.purchase_ticket(moviegoer_id))

    with theater.usher.request() as request:
        yield request
        yield env.process(theater.check_ticket(moviegoer_id))

    if random.random() < food_probability:
        with theater.server.request() as request:
            yield request
            yield env.process(theater.buy_food(moviegoer_id))

    wait_times.append(env.now - arrival_time)


def generate_moviegoers(env, theater, wait_times, arrival_interval, food_probability):
    moviegoer_id = 0
    while True:
        env.process(moviegoer_journey(env, moviegoer_id, theater, wait_times, food_probability))
        yield env.timeout(arrival_interval)
        moviegoer_id += 1