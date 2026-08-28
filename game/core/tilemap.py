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

W  = TILE_WALL
F  = TILE_FLOOR
C  = TILE_CARPET
D  = TILE_DESK
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


WALKABLE = {TILE_FLOOR, TILE_CARPET, TILE_SEAT, TILE_DOOR, TILE_CORRIDOR}

THEATER_MAP = [
    [W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W],
    [W, C, C, C,SC,SC,SC,SC,SC,SC,SC,SC,SC,SC,SC,SC, C, C, C, W],
    [W, C, S, S, S, S, S, C, C, C, C, C, C, S, S, S, S, S, C, W],
    [W, C, S, S, S, S, S, C, C, C, C, C, C, S, S, S, S, S, C, W],
    [W, C, S, S, S, S, S, C, C, C, C, C, C, S, S, S, S, S, C, W],
    [W, C, S, S, S, S, S, C, C, C, C, C, C, S, S, S, S, S, C, W],
    [W, C, S, S, S, S, S, C, C, C, C, C, C, S, S, S, S, S, C, W],
    [W, W, W, W, W, W, W, W,DR,DR,DR,DR, W, W, W, W, W, W, W, W],
    [W,CR,CR, P,CR,CR,CR,CR,CR,CR,CR,CR,CR,CR,CR,CR, P,CR,CR, W],
    [W, W, W, W, W, W, F, F, W, W, F, F, W, W, W, W, W, W, W, W],
    [W, W, W, W,SN,SN, F, F,SN,SN, F, F,SN,SN, W, W, W, W, W, W],
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    [W, F, F, F, F, F, F, Q, F, F, F, F, Q, F, F, F, F, F, F, W],
    [W, Q, Q, Q, Q, Q, Q, U, F, F, F, F, U, Q, Q, Q, Q, Q, Q, W],
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    [W, Q, Q, Q, D, F, F, D, F, F, D, F, F, D, Q, Q, Q, Q, Q, W],
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    [W, F, F,SE, F, F, F, F, T, F, F, T, F, F, F, P, P, F, F, W],
    [W, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, W],
    [W, N, N, N, N, N, N, N, N,DR,DR, N, N, N, N, N, N, N, N, W],
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
        self._glow_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self._dim_seat_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self._dim_seat_surf.fill((0, 0, 0, 18))

    def _get_tile_surf(self, tile_id: int, col: int = 0, row: int = 0) -> pygame.Surface | None:
        if tile_id == TILE_POSTER:
            return AL.tile_poster_for(col, row)
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

        col_start = max(0, cam_x // TILE_SIZE)
        col_end   = min(MAP_COLS, col_start + surface.get_width() // TILE_SIZE + 2)
        row_start = max(0, cam_y // TILE_SIZE)
        row_end   = min(MAP_ROWS, row_start + surface.get_height() // TILE_SIZE + 2)

        glow = self._glow_surf

        for row in range(row_start, row_end):
            for col in range(col_start, col_end):
                tile_id = THEATER_MAP[row][col]
                sx = col * TILE_SIZE - cam_x
                sy = row * TILE_SIZE - cam_y

                surface.fill(C_BG_DARK, (sx, sy, TILE_SIZE, TILE_SIZE))

                surf = self._get_tile_surf(tile_id, col, row)
                if surf:
                    dy = sy - (surf.get_height() - TILE_SIZE)
                    surface.blit(surf, (sx, dy))

                if tile_id == TILE_SCREEN:
                    pulse = int(20 + 15 * math.sin(self._anim_t * 1.5))
                    glow.fill((*C_NEON_CYAN[:3], pulse))
                    surface.blit(glow, (sx, sy))

                elif tile_id == TILE_SEAT:
                    surface.blit(self._dim_seat_surf, (sx, sy))

    def draw_seats(self, surface: pygame.Surface, camera):
        cam_x, cam_y = int(camera.x), int(camera.y)
        col_start = max(0, cam_x // TILE_SIZE)
        col_end   = min(MAP_COLS, col_start + surface.get_width() // TILE_SIZE + 2)
        row_start = max(0, cam_y // TILE_SIZE)
        row_end   = min(MAP_ROWS, row_start + surface.get_height() // TILE_SIZE + 2)

        for row in range(row_start, row_end):
            for col in range(col_start, col_end):
                if THEATER_MAP[row][col] == TILE_SEAT:
                    sx = col * TILE_SIZE - cam_x
                    sy = row * TILE_SIZE - cam_y
                    surf = self._get_tile_surf(TILE_SEAT)
                    if surf:
                        dy = sy - (surf.get_height() - TILE_SIZE)
                        surface.blit(surf, (sx, dy))
                        surface.blit(self._dim_seat_surf, (sx, sy))

