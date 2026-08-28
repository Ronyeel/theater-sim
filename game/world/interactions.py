
from typing import List, Optional, Tuple
import math
import pygame
from game.settings import (
    TILE_SIZE, INTERACT_RADIUS, C_NEON_GOLD, C_NEON_PINK, C_NEON_CYAN, C_NEON_RED,
    C_SECURITY, C_WALL_TRIM, CASHIER_DESK_COLS, USHER_DESK_COLS,
    SNACK_DESK_COLS, SEAT_ROWS, SEAT_COLS, TILE_SEAT,
    CASHIER_QUEUE_ROW, USHER_DESK_ROW, SNACK_DESK_ROW,
    SECURITY_COL, SECURITY_ROW, BOARD_COL, BOARD_ROW, EXIT_DOOR_COLS, EXIT_DOOR_ROW,
)
from game.core.tilemap import tile_at


class Zone:

    def __init__(
        self,
        name: str,
        wx: float,
        wy: float,
        color: Tuple[int, int, int] = C_NEON_GOLD,
        label: str = "",
    ) -> None:
        self.name = name
        self.x = wx
        self.y = wy
        self.color = color
        self.label = label
        self._glow_t = 0.0

    def is_near(self, px: float, py: float) -> bool:
        return math.hypot(px - self.x, py - self.y) <= INTERACT_RADIUS

    def update(self, dt: float) -> None:
        self._glow_t += dt

    def draw_glow(self, surface: pygame.Surface, camera) -> None:
        pass


def _tc(col: int, row: int) -> Tuple[float, float]:
    return float(col * TILE_SIZE + TILE_SIZE // 2), float(row * TILE_SIZE + TILE_SIZE // 2)


def build_zones(num_cashiers: int, num_ushers: int, num_servers: int) -> List[Zone]:
    zones: List[Zone] = []

    x, y = _tc(SECURITY_COL, SECURITY_ROW)
    zones.append(Zone("security", x, y, C_SECURITY, "[E] Security Check"))

    x, y = _tc(BOARD_COL, BOARD_ROW)
    zones.append(Zone("board", x, y, C_WALL_TRIM, "[E] Check Schedule"))

    x, y = _tc(3, 8)
    zones.append(Zone("poster", x, y, C_WALL_TRIM, "[E] View Poster"))
    x, y = _tc(16, 8)
    zones.append(Zone("poster", x, y, C_WALL_TRIM, "[E] View Poster"))
    x, y = _tc(16, 21)
    zones.append(Zone("poster", x, y, C_WALL_TRIM, "[E] View Poster"))

    for i in range(min(num_cashiers, len(CASHIER_DESK_COLS))):
        col = CASHIER_DESK_COLS[i]
        x, y = _tc(col, CASHIER_QUEUE_ROW)
        zones.append(Zone("cashier", x, y, C_NEON_GOLD, "[E] Buy Ticket"))

    for i in range(min(num_ushers, len(USHER_DESK_COLS))):
        col = USHER_DESK_COLS[i]
        x, y = _tc(col, USHER_DESK_ROW + 1)
        zones.append(Zone("usher", x, y, C_NEON_PINK, "[E] Show Ticket"))

    for i in range(min(num_servers, len(SNACK_DESK_COLS))):
        col = SNACK_DESK_COLS[i]
        x, y = _tc(col, SNACK_DESK_ROW - 1)
        zones.append(Zone("snack", x, y, C_NEON_CYAN, "[E] Buy Snacks"))

    for row in SEAT_ROWS:
        for col in range(SEAT_COLS[0], SEAT_COLS[-1], 2):
            if tile_at(col, row) == TILE_SEAT:
                x, y = _tc(col, row)
                zones.append(Zone("seat", x, y, C_NEON_GOLD, "[E] Take Seat"))

    exit_col = sum(EXIT_DOOR_COLS) // len(EXIT_DOOR_COLS)
    x, y = _tc(exit_col, EXIT_DOOR_ROW)
    zones.append(Zone("exit", x, y, C_NEON_RED, "[E] Exit Theater"))

    return zones


def find_nearest_zone(
    zones: List[Zone],
    px: float,
    py: float,
    filter_name: Optional[str] = None,
) -> Optional[Zone]:
    best: Optional[Zone] = None
    best_d = float("inf")
    for z in zones:
        if filter_name and z.name != filter_name:
            continue
        d = math.hypot(px - z.x, py - z.y)
        if d < INTERACT_RADIUS and d < best_d:
            best = z
            best_d = d
    return best
