"""
CinePlex Dreams — Interaction Zones
Defines interaction areas in the theater world.  When the player enters
a zone and presses E, a callback fires to advance their journey stage.
"""
import pygame
import math
from game.settings import (
    TILE_SIZE, INTERACT_RADIUS, C_NEON_GOLD, C_NEON_PINK, C_NEON_CYAN,
    C_SECURITY, C_WALL_TRIM, CASHIER_DESK_COLS, USHER_DESK_COLS, 
    SNACK_DESK_COLS, SEAT_ROWS, SEAT_COLS,
    CASHIER_QUEUE_ROW, USHER_DESK_ROW, SNACK_DESK_ROW, 
    SECURITY_COL, SECURITY_ROW, BOARD_COL, BOARD_ROW
)


class Zone:
    def __init__(self, name: str, wx: float, wy: float,
                 color=C_NEON_GOLD, label: str = ""):
        self.name  = name
        self.x     = wx
        self.y     = wy
        self.color = color
        self.label = label
        self._glow_t = 0.0

    def is_near(self, px: float, py: float) -> bool:
        return math.hypot(px - self.x, py - self.y) <= INTERACT_RADIUS

    def update(self, dt):
        self._glow_t += dt

    def draw_glow(self, surface: pygame.Surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        pulse = 0.4 + 0.6 * abs(math.sin(self._glow_t * 2.5))
        r = int(INTERACT_RADIUS * 0.6)
        glow = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        a = int(35 * pulse)
        pygame.draw.circle(glow, (*self.color[:3], a), (r, r), r)
        pygame.draw.circle(glow, (*self.color[:3], int(a*1.5)), (r, r), r, 2)
        surface.blit(glow, (int(sx)-r, int(sy)-r))


def _tc(col, row):
    """Tile center in world pixels."""
    return (col * TILE_SIZE + TILE_SIZE // 2, row * TILE_SIZE + TILE_SIZE // 2)


def build_zones(num_cashiers: int, num_ushers: int, num_servers: int) -> list[Zone]:
    zones = []
    
    # Lobby - Security
    x, y = _tc(SECURITY_COL, SECURITY_ROW)
    zones.append(Zone("security", x, y, C_SECURITY, "[E] Security Check"))

    # Lobby - Digital Board
    x, y = _tc(BOARD_COL, BOARD_ROW)
    zones.append(Zone("board", x, y, C_WALL_TRIM, "[E] Check Schedule"))
    
    # Lobby - Posters
    x, y = _tc(1, 6)
    zones.append(Zone("poster", x, y, C_WALL_TRIM, "[E] Look at Poster"))
    x, y = _tc(28, 6)
    zones.append(Zone("poster", x, y, C_WALL_TRIM, "[E] Look at Poster"))
    x, y = _tc(3, 25)
    zones.append(Zone("poster", x, y, C_WALL_TRIM, "[E] Look at Poster"))
    x, y = _tc(27, 25)
    zones.append(Zone("poster", x, y, C_WALL_TRIM, "[E] Look at Poster"))

    # Cashier zones
    for i in range(min(num_cashiers, len(CASHIER_DESK_COLS))):
        col = CASHIER_DESK_COLS[i]
        x, y = _tc(col, CASHIER_QUEUE_ROW)
        zones.append(Zone("cashier", x, y, C_NEON_GOLD, "[E] Buy Ticket"))

    # Usher zones
    for i in range(min(num_ushers, len(USHER_DESK_COLS))):
        col = USHER_DESK_COLS[i]
        x, y = _tc(col, USHER_DESK_ROW - 1)
        zones.append(Zone("usher", x, y, C_NEON_PINK, "[E] Show Ticket"))

    # Snack bar zones
    for i in range(min(num_servers, len(SNACK_DESK_COLS))):
        col = SNACK_DESK_COLS[i]
        x, y = _tc(col, SNACK_DESK_ROW - 1)
        zones.append(Zone("snack", x, y, C_NEON_CYAN, "[E] Buy Snacks"))

    # Seat zones — sample of seats per row
    for row in SEAT_ROWS:
        for col in range(SEAT_COLS[0], SEAT_COLS[-1], 2):
            x, y = _tc(col, row)
            zones.append(Zone("seat", x, y, C_NEON_GOLD, "[E] Take Seat"))

    return zones


def find_nearest_zone(zones: list[Zone], px: float, py: float,
                      filter_name: str | None = None) -> Zone | None:
    best, best_d = None, float("inf")
    for z in zones:
        if filter_name and z.name != filter_name:
            continue
        d = math.hypot(px - z.x, py - z.y)
        if d < INTERACT_RADIUS and d < best_d:
            best, best_d = z, d
    return best
