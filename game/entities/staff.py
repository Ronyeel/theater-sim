"""
CinePlex Dreams — Staff Entities
Fixed-position cashiers, ushers, and servers with idle/serving animations.
"""
import pygame
import math
from game.settings import TILE_SIZE, C_NEON_GOLD, C_NEON_PINK, C_NEON_CYAN
from game.core import asset_loader as AL

DIR_DOWN=0


class StaffMember:
    CASHIER = "cashier"
    USHER   = "usher"
    SERVER  = "server"

    LABELS = {
        CASHIER: ("BOX OFFICE", C_NEON_GOLD),
        USHER:   ("USHER GATE", C_NEON_PINK),
        SERVER:  ("CONCESSION", C_NEON_CYAN),
    }

    def __init__(self, role: str, tile_col: int, tile_row: int):
        self.role  = role
        self.x     = float(tile_col * TILE_SIZE + TILE_SIZE//2)
        self.y     = float(tile_row * TILE_SIZE)
        self._t    = 0.0
        self._serving_t = 0.0
        self._is_serving = False
        try:
            self._font = pygame.font.SysFont("consolas", 11, bold=True)
        except Exception:
            self._font = pygame.font.Font(None, 11)

    def serve(self, duration=0.8):
        self._is_serving = True
        self._serving_t  = duration

    def update(self, dt):
        self._t += dt
        if self._serving_t > 0:
            self._serving_t -= dt
            if self._serving_t <= 0:
                self._is_serving = False

    def draw(self, surface: pygame.Surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        frame = 1 if self._is_serving else int(self._t / 0.8) % 2
        if self.role == self.CASHIER:
            sprite = AL.cashier_sprite(frame, DIR_DOWN)
        elif self.role == self.USHER:
            sprite = AL.usher_sprite(frame, DIR_DOWN)
        else:
            sprite = AL.server_sprite(frame, DIR_DOWN)

        sw, sh = sprite.get_size()
        lean = -4 if self._is_serving else 0
        surface.blit(sprite, (int(sx)-sw//2, int(sy)-sh+lean))

        # Label
        label, color = self.LABELS[self.role]
        ls = self._font.render(label, True, color)
        surface.blit(ls, (int(sx) - ls.get_width()//2, int(sy)-sh-ls.get_height()-2))


def build_staff(num_cashiers: int, num_ushers: int, num_servers: int) -> list[StaffMember]:
    from game.settings import CASHIER_DESK_COLS, CASHIER_DESK_ROW, USHER_DESK_COLS, USHER_DESK_ROW, SNACK_DESK_COLS, SNACK_DESK_ROW
    staff = []
    # Cashiers
    for i in range(min(num_cashiers, len(CASHIER_DESK_COLS))):
        staff.append(StaffMember(StaffMember.CASHIER, CASHIER_DESK_COLS[i], CASHIER_DESK_ROW))
    # Ushers
    for i in range(min(num_ushers, len(USHER_DESK_COLS))):
        staff.append(StaffMember(StaffMember.USHER, USHER_DESK_COLS[i], USHER_DESK_ROW))
    # Servers
    for i in range(min(num_servers, len(SNACK_DESK_COLS))):
        staff.append(StaffMember(StaffMember.SERVER, SNACK_DESK_COLS[i], SNACK_DESK_ROW))
    return staff
