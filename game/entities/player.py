"""
CinePlex Dreams — Player Entity
WASD/Arrow key controlled moviegoer with 4-direction walk animation,
interaction system, and per-stage progress tracking.
"""
import pygame
import math
from game.settings import (
    TILE_SIZE, PLAYER_SPEED, PLAYER_SPRITE_W, PLAYER_SPRITE_H,
    INTERACT_RADIUS, INTERACT_HOLD_TIME, PLAYER_SPAWN,
    AUDITORIUM_DOOR_COLS, AUDITORIUM_DOOR_ROW,
    USHER_DESK_ROW, USHER_GATE_COLS,
    C_NEON_GOLD, C_NEON_GREEN,
)
from game.core import asset_loader as AL
from game.core.tilemap import is_walkable


# ── Journey stages ────────────────────────────────────────────────────────
class Stage:
    ENTERING      = "entering"
    AT_SECURITY   = "at_security"
    BROWSING      = "browsing"
    NEED_TICKET   = "need_ticket"
    NEED_CHECK    = "need_check"
    NEED_FOOD     = "need_food"    # optional — decided randomly
    FOOD_SKIP     = "food_skip"
    NEED_SEAT     = "need_seat"
    SEATED        = "seated"
    NEED_EXIT     = "need_exit"


# ── Direction indices for sprite ──────────────────────────────────────────
DIR_DOWN  = 0
DIR_UP    = 3
DIR_LEFT  = 1
DIR_RIGHT = 2


class Player:
    def __init__(self):
        # World position (pixels, center of sprite)
        self.x = float(PLAYER_SPAWN[0] * TILE_SIZE + TILE_SIZE // 2)
        self.y = float(PLAYER_SPAWN[1] * TILE_SIZE + TILE_SIZE // 2)

        # Movement
        self._vx = 0.0
        self._vy = 0.0
        self._direction = DIR_DOWN
        self._moving = False

        # Animation
        self._anim_timer = 0.0
        self._anim_frame = 0
        self._idle_bob   = 0.0
        self._idle_t     = 0.0

        # Journey progress
        self.stage         = Stage.ENTERING
        self.has_ticket    = False
        self.ticket_checked= False
        self.has_food      = False
        self.seated_at_pos = None
        self.selected_movie = None
        self.food_order    = None

        # Interaction state
        self._interacting  = False
        self._interact_t   = 0.0
        self._interact_cb  = None
        self.arrival_time  = 0.0   # set by game_screen when sim starts
        self.wait_time     = 0.0   # filled when seated

        # Visual flash
        self._flash_color  = None
        self._flash_timer  = 0.0

        # Footstep dust timer
        self.dust_timer = 0.0
        self.ticket_gate_blocked = False
        self.usher_gate_blocked = False
        self.usher_no_ticket_notified = False

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def rect(self) -> pygame.Rect:
        w, h = PLAYER_SPRITE_W * 2, PLAYER_SPRITE_H * 2
        return pygame.Rect(int(self.x) - w//2, int(self.y) - h//2, w, h)

    @property
    def tile_col(self) -> int:
        return int(self.x) // TILE_SIZE

    @property
    def tile_row(self) -> int:
        return int(self.y) // TILE_SIZE

    @property
    def is_interacting(self) -> bool:
        return self._interacting

    # ── Input ─────────────────────────────────────────────────────────────

    def handle_keys(self, keys):
        if self._interacting:
            self._vx = 0.0; self._vy = 0.0
            return
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy =  1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx =  1
        if dx != 0 and dy != 0:
            dx *= 0.707; dy *= 0.707
        self._vx = dx * PLAYER_SPEED
        self._vy = dy * PLAYER_SPEED
        self._moving = dx != 0 or dy != 0
        if dx < 0: self._direction = DIR_LEFT
        elif dx > 0: self._direction = DIR_RIGHT
        elif dy < 0: self._direction = DIR_UP
        elif dy > 0: self._direction = DIR_DOWN

    def start_interact(self, callback=None):
        """Called by interaction system when player presses E near a zone."""
        if self._interacting: return
        self._interacting = True
        self._interact_t  = INTERACT_HOLD_TIME
        self._interact_cb = callback
        self._vx = 0.0; self._vy = 0.0

    def flash(self, color, duration=0.4):
        self._flash_color = color
        self._flash_timer = duration

    # ── Update ────────────────────────────────────────────────────────────

    def update(self, dt: float):
        # Interaction cooldown
        if self._interacting:
            self._interact_t -= dt
            if self._interact_t <= 0:
                self._interacting = False
                if self._interact_cb:
                    self._interact_cb()
                    self._interact_cb = None
            return

        # Movement + collision
        self.ticket_gate_blocked = False
        self.usher_gate_blocked = False
        new_x = self.x + self._vx * dt
        new_y = self.y + self._vy * dt

        # Tile-based AABB collision (shrink hitbox a bit)
        hw, hh = PLAYER_SPRITE_W, PLAYER_SPRITE_H // 2  # half-size for feet

        def passable(px, py):
            col = int(px) // TILE_SIZE
            row = int(py) // TILE_SIZE
            if (row == AUDITORIUM_DOOR_ROW and col in AUDITORIUM_DOOR_COLS
                    and not self.has_ticket):
                self.ticket_gate_blocked = True
                return False
            if (row == USHER_DESK_ROW and col in USHER_GATE_COLS
                    and not self.ticket_checked):
                self.usher_gate_blocked = True
                return False
            return is_walkable(col, row)

        # Test all foot-box corners. The former centre-line test let the
        # player visibly overlap a counter or seat when approaching diagonally.
        def foot_box_passable(cx, cy):
            return all(passable(px, py) for px, py in (
                (cx - hw + 2, cy - hh + 2),
                (cx + hw - 2, cy - hh + 2),
                (cx - hw + 2, cy + hh - 2),
                (cx + hw - 2, cy + hh - 2),
            ))

        if foot_box_passable(new_x, self.y):
            self.x = new_x
        if foot_box_passable(self.x, new_y):
            self.y = new_y

        # Animation
        self._idle_t += dt
        self._idle_bob = math.sin(self._idle_t * 2.5) * 1.5

        if self._moving:
            self._anim_timer += dt
            if self._anim_timer >= 0.14:
                self._anim_timer = 0
                self._anim_frame = (self._anim_frame + 1) % 4
            self.dust_timer += dt
        else:
            self._anim_frame = 0

        # Flash timer
        if self._flash_timer > 0:
            self._flash_timer -= dt

    # ── Draw ──────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        sprite = AL.player_sprite(self._anim_frame, self._direction)
        sw, sh = sprite.get_size()

        # Drop shadow under feet
        shadow = pygame.Surface((28, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 80), (0, 0, 28, 12))
        surface.blit(shadow, (int(sx) - 14, int(sy) - 6))

        draw_x = int(sx) - sw // 2
        draw_y = int(sy) - sh + int(self._idle_bob if not self._moving else 0)

        # Interaction pulse ring
        if self._interacting:
            t = 1.0 - (self._interact_t / INTERACT_HOLD_TIME)
            r = int(8 + 20 * t)
            a = int(180 * (1 - t))
            ring = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*C_NEON_GOLD[:3], a), (r, r), r, 2)
            surface.blit(ring, (int(sx) - r, int(sy) - r))

        # Flash tint
        if self._flash_timer > 0 and self._flash_color:
            tinted = sprite.copy()
            tint = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
            a = int(160 * (self._flash_timer / 0.4))
            tint.fill((*self._flash_color[:3], a))
            tinted.blit(tint, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(tinted, (draw_x, draw_y))
        else:
            surface.blit(sprite, (draw_x, draw_y))
