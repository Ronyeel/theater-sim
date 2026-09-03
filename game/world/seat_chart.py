from typing import Optional, Tuple

from game.settings import SEAT_ROWS

CHART_ROWS = 5
CHART_COLS = 10
LEFT_BLOCK = (2, 3, 4, 5, 6)
RIGHT_BLOCK = (13, 14, 15, 16, 17)


def tile_to_chart(col: int, row: int) -> Optional[Tuple[int, int]]:
    if row not in SEAT_ROWS:
        return None
    chart_row = SEAT_ROWS.index(row) + 1
    if col in LEFT_BLOCK:
        return chart_row, LEFT_BLOCK.index(col) + 1
    if col in RIGHT_BLOCK:
        return chart_row, 6 + RIGHT_BLOCK.index(col)
    return None


def chart_to_tile(chart_row: int, chart_col: int) -> Tuple[int, int]:
    map_row = SEAT_ROWS[chart_row - 1]
    if chart_col <= 5:
        return LEFT_BLOCK[chart_col - 1], map_row
    return RIGHT_BLOCK[chart_col - 6], map_row
