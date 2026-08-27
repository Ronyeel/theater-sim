"""
CinePlex Dreams — Tile Map (30×40 Full Cinema Interior)
Renders the cinema grid: lobby → ticket area → usher → concession → corridor → auditorium.
"""
import pygame
import math
from game.settings import (
    TILE_SIZE, MAP_COLS, MAP_ROWS,
    C_BG_DARK, C_NEON_PINK, C_NEON_CYAN, C_NEON_GOLD,
    TILE_EMPTY, TILE_WALL, TILE_FLOOR, TILE_CARPET, TILE_DESK,
    TILE_SEAT, TILE_DOOR, TILE_NEON, TILE_QUEUE, TILE_SNACK,
    TILE_SCREEN, TILE_USHER, TILE_SECURITY, TILE_POSTER,
    TILE_PLANT, TILE_TABLE, TILE_CORRIDOR,
)
from game.core import asset_loader as AL

# Short aliases for readability in the map grid
W  = TILE_WALL
F  = TILE_FLOOR
C  = TILE_CARPET
D  = TILE_DESK      # cashier desk
S  = TILE_SEAT
DR = TILE_DOOR
N  = TILE_NEON
Q  = TILE_QUEUE
SN = TILE_SNACK
SC = TILE_SCREEN
U  = TILE_USHER
SE = TILE_SECURITY
P  = TILE_POSTER
PL = TILE_PLANT
T  = TILE_TABLE
CR = TILE_CORRIDOR

WALKABLE = {TILE_FLOOR, TILE_CARPET, TILE_SEAT, TILE_DOOR, TILE_QUEUE, TILE_CORRIDOR}

# ── 20 cols × 25 rows ────────────────────────────────────────────────────
# Layout (bottom-to-top flow):
#   Row  0   : Top wall
#   Row  1   : Cinema screen
#   Row  2   : Carpet aisle
#   Rows 3-6 : Auditorium seating (4 rows)
#   Row  7   : Theater entrance doors
#   Row  8   : Cinema corridor
#   Row  9   : Behind concession wall
#   Row 10   : Snack counters (behind)
#   Row 11   : Snack queue
#   Row 12   : Open walking area
#   Row 13   : Usher queue
#   Row 14   : Usher desks
#   Row 15   : Post-cashier walkway
#   Row 16   : Behind cashier wall
#   Row 17   : Cashier desks
#   Row 18   : Queue area
#   Row 19   : Queue ropes
#   Row 20   : Lobby open
#   Row 21   : Lobby (security, tables, board)
#   Row 22   : Lobby open
#   Row 23   : Neon marquee strip
#   Row 24   : Bottom wall + entrance

THEATER_MAP = [
    # Row 0: Top wall
    [W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W],
    # Row 1: Cinema screen
    [W, C, C, C,SC,SC,SC,SC,SC,SC,SC,SC,SC,SC,SC,SC, C, C, C, W],
    # Row 2: Carpet aisle
    [W, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, W],
    # Row 3: Seat row 1
    [W, C, S, S, S, S, S, S, C, C, C, C, S, S, S, S, S, S, C, W],
    # Row 4: Seat row 2
    [W, C, S, S, S, S, S, S, C, C, C, C, S, S, S, S, S, S, C, W],
    # Row 5: Seat row 3
    [W, C, S, S, S, S, S, S, C, C, C, C, S, S, S, S, S, S, C, W],
    # Row 6: Seat row 4
    [W, C, S, S, S, S, S, S, C, C, C, C, S, S, S, S, S, S, C, W],
    # Row 7: Theater entrance doors
    [W, W, W, W, W,W,W,W,DR,DR,DR,DR, W, W, W, W, W, W, W, W],
    # Row 8: Cinema corridor
    [W,CR,CR, P,CR,CR,CR,CR,CR,CR,CR,CR,CR,CR,CR,CR, P,CR,CR, W],
    # Row 9: Behind concession (wall)
    [W, W, W, W, W, W, F, F, W, W, F, F, W, W, W, W, W, W, W, W],
    # Row 10: Snack counters
    [W, W, W, W,SN,SN, F, F,SN,SN, F, F,SN,SN, W, W, W, W, W, W],
    # Row 11: Snack queue area
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    # Row 12: Open walking area
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    # Row 13: Usher queue
    [W, F, F, F, F, F, F, Q, F, F, F, F, Q, F, F, F, F, F, F, W],
    # Row 14: Usher desks
    [W, Q, Q, Q, Q, Q, Q, U, F, F, F, F, U, Q, Q, Q, Q, Q, Q, W],
    # Row 15: Post-cashier walkway
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    # Row 16: Behind cashier (wall)
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    # Row 17: Cashier desks
    [W, Q, Q, Q, D, F, F, D, F, F, D, F, F, D, Q, Q, Q, Q, Q, W],
    # Row 18: Queue area in front of cashiers
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    # Row 19: Queue ropes
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    # Row 20: Lobby open
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    # Row 21: Lobby — security (left), table (center), board (right)
    [W, F, F,SE, F, F, F, F, T, F, F, T, F, F, F, P, P, F, F, W],
    # Row 22: Lobby open
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    # Row 23: Neon marquee strip
    [W, N, N, N, N, N, N, N, N, N, N, N, N, N, N, N, N, N, N, W],
    # Row 24: Bottom wall + Entrance
    [W, W, W, W, W, W, W, W, W,DR,DR, W, W, W, W, W, W, W, W, W],
]


def tile_at(col: int, row: int) -> int:
    if 0 <= row < MAP_ROWS and 0 <= col < MAP_COLS:
        return THEATER_MAP[row][col]
    return TILE_WALL


def is_walkable(col: int, row: int) -> bool:
    return tile_at(col, row) in WALKABLE


def tile_world_rect(col: int, row: int) -> pygame.Rect:
    return pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)


class TileMap:
    def __init__(self):
        self._anim_t = 0.0
        self._tile_cache: dict[int, pygame.Surface] = {}

    def _get_tile_surf(self, tile_id: int) -> pygame.Surface | None:
        if tile_id in self._tile_cache:
            return self._tile_cache[tile_id]
        fn = AL.TILE_FUNCS.get(tile_id)
        surf = fn() if fn else None
        self._tile_cache[tile_id] = surf
        return surf

    def update(self, dt: float):
        self._anim_t += dt

    def draw(self, surface: pygame.Surface, camera):
        cam_x, cam_y = int(camera.x), int(camera.y)

        # Visible tile range
        col_start = max(0, cam_x // TILE_SIZE)
        col_end   = min(MAP_COLS, col_start + surface.get_width() // TILE_SIZE + 2)
        row_start = max(0, cam_y // TILE_SIZE)
        row_end   = min(MAP_ROWS, row_start + surface.get_height() // TILE_SIZE + 2)

        for row in range(row_start, row_end):
            for col in range(col_start, col_end):
                tile_id = THEATER_MAP[row][col]
                sx = col * TILE_SIZE - cam_x
                sy = row * TILE_SIZE - cam_y

                # Base fill
                surface.fill(C_BG_DARK, (sx, sy, TILE_SIZE, TILE_SIZE))

                surf = self._get_tile_surf(tile_id)
                if surf:
                    # If surface is taller than TILE_SIZE, offset it UP so it draws correctly in 2.5D
                    dy = sy - (surf.get_height() - TILE_SIZE)
                    surface.blit(surf, (sx, dy))

                # ── Animated effects ──────────────────────────────────

                # Neon marquee flicker
                if tile_id == TILE_NEON:
                    flicker = 0.6 + 0.4 * math.sin(self._anim_t * 4.0 + col * 0.7)
                    glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    glow.fill((*C_NEON_PINK[:3], int(30 * flicker)))
                    surface.blit(glow, (sx, sy))

                # Cinema screen glow — pulsing blue/white light
                if tile_id == TILE_SCREEN:
                    glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    pulse = int(20 + 15 * math.sin(self._anim_t * 1.5))
                    glow.fill((*C_NEON_CYAN[:3], pulse))
                    surface.blit(glow, (sx, sy))

                # Theater seat area — subtle darkness to simulate dim auditorium
                if tile_id == TILE_SEAT:
                    dim = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    dim.fill((0, 0, 0, 18))
                    surface.blit(dim, (sx, sy))

                # Carpet aisle glow — faint warm light from screen
                if tile_id == TILE_CARPET and 1 <= row <= 6:
                    # Gradient: brighter closer to screen (row 1)
                    dist = (row - 1) / 5.0
                    alpha = int(12 * (1 - dist) + 4 * math.sin(self._anim_t * 1.2))
                    glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    glow.fill((100, 160, 220, max(0, alpha)))
                    surface.blit(glow, (sx, sy))

                # Poster spotlight
                if tile_id == TILE_POSTER:
                    glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    pulse = int(8 + 6 * math.sin(self._anim_t * 2.0 + col * 1.3))
                    glow.fill((*C_NEON_GOLD[:3], pulse))
                    surface.blit(glow, (sx, sy))

                # Corridor floor — faint edge lighting
                if tile_id == TILE_CORRIDOR:
                    glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    a = int(6 + 4 * math.sin(self._anim_t * 0.8 + col * 0.5))
                    glow.fill((80, 50, 120, a))
                    surface.blit(glow, (sx, sy))

