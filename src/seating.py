from typing import List, Tuple, Optional


# =====================================================================
# Step 1: Define the Theater Layout
# • 2D list representing the seating chart (5 rows by 10 seats).
# • 'A' = available, 'X' = taken.
# =====================================================================
seats = [['A' for _ in range(10)] for _ in range(5)]


def create_seating_chart(rows: int = 5, cols: int = 10, default_state: str = 'A') -> List[List[str]]:
    return [[default_state for _ in range(cols)] for _ in range(rows)]


def copy_chart(chart: List[List[str]]) -> List[List[str]]:
    return [row[:] for row in chart]


def price_for_row(row: int, total_rows: int = 5) -> float:
    """Front rows (closest to the screen) cost more than back rows."""
    if row <= max(1, total_rows // 3):
        return 250.0
    if row >= total_rows:
        return 120.0
    return 180.0


# =====================================================================
# Step 2: Display the Seating Chart
# • Prints column headers (1..10) and rows formatted as "Row N: ...".
# =====================================================================
def display_seats(seats: List[List[str]]) -> None:
    if not seats or not seats[0]:
        print("Empty seating chart.")
        return
    print("   " + " ".join(f"{i+1:>2}" for i in range(len(seats[0]))))
    for i, row in enumerate(seats):
        print(f"Row {i+1:<2}: " + "  ".join(row))


# Alias for backwards compatibility across existing modules
display_seating_chart = display_seats


def is_valid_seat(chart: List[List[str]], row: int, col: int) -> bool:
    if not chart:
        return False
    return 1 <= row <= len(chart) and 1 <= col <= len(chart[0])


def is_seat_available(chart: List[List[str]], row: int, col: int) -> bool:
    if not is_valid_seat(chart, row, col):
        return False
    return chart[row - 1][col - 1] == 'A'


def reserve_seat_pos(chart: List[List[str]], row: int, col: int) -> Tuple[bool, str]:
    """Internal programmatic seat reservation by 1-indexed row and col."""
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


# =====================================================================
# Step 3: Seat Reservation Function
# • Interactive loop prompting user for row & seat numbers.
# • Also supports programmatic calls: reserve_seat(seats, row, col).
# =====================================================================
def reserve_seat(seats: List[List[str]], row: Optional[int] = None, col: Optional[int] = None):
    if row is not None and col is not None:
        return reserve_seat_pos(seats, row, col)

    num_rows = len(seats)
    num_cols = len(seats[0]) if num_rows > 0 else 0
    while True:
        try:
            row_in = int(input(f"Enter row (1-{num_rows}): ")) - 1
            col_in = int(input(f"Enter seat (1-{num_cols}): ")) - 1
            if row_in < 0 or col_in < 0:
                raise IndexError
            if seats[row_in][col_in] == 'A':
                seats[row_in][col_in] = 'X'
                print("Seat reserved successfully!")
                break
            else:
                print("Sorry, that seat is already taken.")
        except (IndexError, ValueError):
            print("Invalid input. Try again.")


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


# =====================================================================
# Step 4: Loop the Booking System
# • Allows multiple seat bookings using a menu loop.
# =====================================================================
def book_seats(seats_chart: Optional[List[List[str]]] = None) -> None:
    global seats
    target = seats if seats_chart is None else seats_chart
    while True:
        display_seats(target)
        reserve_seat(target)
        cont = input("Reserve another seat? (y/n): ").lower()
        if cont != 'y':
            break


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
        display_seats(self.chart)

    def available_positions(self) -> List[Tuple[int, int]]:
        seats_avail: List[Tuple[int, int]] = []
        for row_idx, row in enumerate(self.chart, start=1):
            for col_idx, seat in enumerate(row, start=1):
                if seat == 'A':
                    seats_avail.append((row_idx, col_idx))
        return seats_avail

    def snapshot(self) -> List[List[str]]:
        return copy_chart(self.chart)

    def reserve(self, row: int, col: int, customer_name: str = "Guest", price: Optional[float] = None) -> Tuple[bool, str]:
        success, msg = reserve_seat_pos(self.chart, row, col)
        if success:
            charged = price if price is not None else price_for_row(row, self.rows)
            self.seat_data[(row, col)] = {
                "customer_name": customer_name,
                "price": charged,
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


def _read_int(prompt: str) -> Optional[int]:
    raw = input(prompt).strip()
    try:
        return int(raw)
    except ValueError:
        return None


def run_seating_cli(seating_obj: Optional[TheaterSeating] = None) -> None:
    target_chart = seating_obj.chart if seating_obj is not None else seats
    print("\n" + "=" * 55)
    print(" CAMARINES NORTE STATE COLLEGE - THEATER SEAT BOOKING")
    print("=" * 55)
    book_seats(target_chart)
    print("\nFinal Seating Chart:")
    display_seats(target_chart)


if __name__ == "__main__":
    book_seats(seats)
