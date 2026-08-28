import random

def moviegoer_journey(env, moviegoer_id, theater, wait_times, food_probability):
    """Run one guest through ticketing, usher check, optional food, and seating."""
    arrival_time = env.now

    if not theater.cashier_available:
        yield env.event()
        return
    with theater.cashier.request() as request:
        yield request
        yield env.process(theater.purchase_ticket(moviegoer_id))

    if not theater.usher_available:
        yield env.event()
        return
    with theater.usher.request() as request:
        yield request
        yield env.process(theater.check_ticket(moviegoer_id))

    if random.random() < food_probability:
        if not theater.server_available:
            yield env.event()
            return
        with theater.server.request() as request:
            yield request
            yield env.process(theater.buy_food(moviegoer_id))

    wait_times.append(env.now - arrival_time)


def generate_moviegoers(env, theater, wait_times, arrival_interval,
                        food_probability, on_arrival=None):
    """Seed the opening ticket line, then add guests at the configured interval."""
    # The activity specification begins with three guests already in line.
    for moviegoer_id in range(3):
        if on_arrival:
            on_arrival(moviegoer_id)
        env.process(moviegoer_journey(
            env, moviegoer_id, theater, wait_times, food_probability
        ))

    moviegoer_id = 3
    while True:
        yield env.timeout(arrival_interval)
        if on_arrival:
            on_arrival(moviegoer_id)
        env.process(moviegoer_journey(
            env, moviegoer_id, theater, wait_times, food_probability
        ))
        moviegoer_id += 1
