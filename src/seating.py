
from typing import List, Tuple, Optional


def create_seating_chart(rows: int = 5, cols: int = 10, default_state: str = 'A') -> List[List[str]]:
    return [[default_state for _ in range(cols)] for _ in range(rows)]


def display_seating_chart(chart: List[List[str]]) -> None:
    if not chart or not chart[0]:
        print("Empty seating chart.")
        return

    num_rows = len(chart)
    num_cols = len(chart[0])

    col_header = "       " + " ".join(f"{col:1d}" if col < 10 else f"{col:2d}" for col in range(1, num_cols + 1))
    print("\n" + col_header)

    for r_idx, row in enumerate(chart, start=1):
        row_str = " ".join(f"{seat:1s}" for seat in row)
        print(f"Row {r_idx:<2d} {row_str}")
    print()


def is_valid_seat(chart: List[List[str]], row: int, col: int) -> bool:
    if not chart:
        return False
    return 1 <= row <= len(chart) and 1 <= col <= len(chart[0])


def is_seat_available(chart: List[List[str]], row: int, col: int) -> bool:
    if not is_valid_seat(chart, row, col):
        return False
    return chart[row - 1][col - 1] == 'A'


def reserve_seat(chart: List[List[str]], row: int, col: int) -> Tuple[bool, str]:
    if not is_valid_seat(chart, row, col):
        num_rows = len(chart)
        num_cols = len(chart[0]) if chart else 0
        return False, f"Invalid seat location! Rows are 1–{num_rows}, Seats are 1–{num_cols}."

    r_idx = row - 1
    c_idx = col - 1

    if chart[r_idx][c_idx] == 'X':
        return False, f"Seat (Row {row}, Seat {col}) is already taken! Please choose another seat."

    chart[r_idx][c_idx] = 'X'
    return True, f"Success! Seat (Row {row}, Seat {col}) has been reserved."


def cancel_reservation(chart: List[List[str]], row: int, col: int) -> Tuple[bool, str]:
    if not is_valid_seat(chart, row, col):
        return False, "Invalid seat location."
    if chart[row - 1][col - 1] == 'A':
        return False, f"Seat (Row {row}, Seat {col}) is not currently reserved."
    chart[row - 1][col - 1] = 'A'
    return True, f"Reservation for Seat (Row {row}, Seat {col}) cancelled."


def get_available_seats_count(chart: List[List[str]]) -> int:
    return sum(row.count('A') for row in chart)


def get_taken_seats_count(chart: List[List[str]]) -> int:
    return sum(row.count('X') for row in chart)


class TheaterSeating:

    def __init__(self, rows: int = 5, cols: int = 10, default_price: float = 150.0) -> None:
        self.rows = rows
        self.cols = cols
        self.default_price = default_price
        self.chart = create_seating_chart(rows, cols, 'A')
        self.seat_data: dict[Tuple[int, int], dict] = {}

    @property
    def total_seats(self) -> int:
        return self.rows * self.cols

    @property
    def available_seats(self) -> int:
        return get_available_seats_count(self.chart)

    @property
    def reserved_seats(self) -> int:
        return get_taken_seats_count(self.chart)

    @property
    def occupancy_rate(self) -> float:
        return (self.reserved_seats / self.total_seats) * 100.0 if self.total_seats > 0 else 0.0

    def display(self) -> None:
        display_seating_chart(self.chart)

    def reserve(self, row: int, col: int, customer_name: str = "Guest", price: Optional[float] = None) -> Tuple[bool, str]:
        success, msg = reserve_seat(self.chart, row, col)
        if success:
            self.seat_data[(row, col)] = {
                "customer_name": customer_name,
                "price": price if price is not None else self.default_price,
            }
        return success, msg

    def cancel(self, row: int, col: int) -> Tuple[bool, str]:
        success, msg = cancel_reservation(self.chart, row, col)
        if success:
            self.seat_data.pop((row, col), None)
        return success, msg

    def reset(self) -> None:
        self.chart = create_seating_chart(self.rows, self.cols, 'A')
        self.seat_data.clear()


def run_seating_cli() -> None:
    pass


