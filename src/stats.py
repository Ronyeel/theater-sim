import statistics

def average_wait(wait_times):
    return statistics.mean(wait_times)

def format_minutes_seconds(total_minutes):
    minutes, fraction = divmod(total_minutes, 1)
    seconds = round(fraction * 60)
    return int(minutes), seconds