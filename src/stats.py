import statistics

def average_wait(wait_times):
    """Return the mean completed journey time, or zero before anyone finishes."""
    return statistics.mean(wait_times) if wait_times else 0.0


def get_average_wait_time(wait_times):
    """Activity-compatible name for calculating average completed wait time."""
    return average_wait(wait_times)

def format_minutes_seconds(total_minutes):
    """Format simulated minutes as a normalized ``(minutes, seconds)`` pair."""
    total_seconds = max(0, round(float(total_minutes) * 60))
    return total_seconds // 60, total_seconds % 60


def calculate_wait_time(wait_times):
    """Return the activity report format for a list of journey durations."""
    return format_minutes_seconds(average_wait(wait_times))
