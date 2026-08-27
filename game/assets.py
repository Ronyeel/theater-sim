"""
CinePlex Dreams — Programmatic Pixel Art Asset Generator

All sprites and tiles are drawn in code at runtime using Pygame draw
calls on small surfaces, then cached.  No external image files needed.
"""

import pygame
import math
from game.settings import (
    TILE_SIZE, MOVIEGOER_COLORS, COLOR_CASHIER_VEST,
    COLOR_USHER_JACKET, COLOR_SERVER_APRON, COLOR_CARPET_DARK,
    COLOR_CARPET_LIGHT, COLOR_WALL, COLOR_WALL_TRIM, COLOR_FLOOR,
    COLOR_FLOOR_ALT, COLOR_SEAT_EMPTY, COLOR_SEAT_TAKEN, COLOR_DESK,
    COLOR_NEON_PINK, COLOR_NEON_CYAN, COLOR_NEON_GOLD, COLOR_BG_DARK,
)


# ── Cache ────────────────────────────────────────────────────────────────
_cache: dict[str, pygame.Surface] = {}


def _key(name: str) -> pygame.Surface | None:
    return _cache.get(name)


def _put(name: str, surf: pygame.Surface) -> pygame.Surface:
    _cache[name] = surf
    return surf


# ── Helpers ──────────────────────────────────────────────────────────────

def _scale(surf: pygame.Surface, factor: int = 4) -> pygame.Surface:
    """Scale a small pixel-art surface up by an integer factor."""
    w, h = surf.get_size()
    return pygame.transform.scale(surf, (w * factor, h * factor))


def _make(w: int, h: int) -> pygame.Surface:
    """Create a transparent surface at native pixel-art resolution."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    return s


def _darken(color, amount=40):
    return tuple(max(0, c - amount) for c in color[:3])


def _lighten(color, amount=40):
    return tuple(min(255, c + amount) for c in color[:3])


# =====================================================================
#                           TILE ASSETS
# =====================================================================

def tile_floor() -> pygame.Surface:
    cached = _key("tile_floor")
    if cached:
        return cached
    s = _make(16, 16)
    s.fill(COLOR_FLOOR)
    # subtle grid pattern
    pygame.draw.line(s, COLOR_FLOOR_ALT, (0, 0), (15, 0), 1)
    pygame.draw.line(s, COLOR_FLOOR_ALT, (0, 0), (0, 15), 1)
    # small speckle detail
    s.set_at((4, 4), _lighten(COLOR_FLOOR, 15))
    s.set_at((11, 9), _lighten(COLOR_FLOOR, 10))
    return _put("tile_floor", _scale(s))


def tile_wall() -> pygame.Surface:
    cached = _key("tile_wall")
    if cached:
        return cached
    s = _make(16, 16)
    s.fill(COLOR_WALL)
    # horizontal brick lines
    pygame.draw.line(s, _darken(COLOR_WALL, 20), (0, 4), (15, 4), 1)
    pygame.draw.line(s, _darken(COLOR_WALL, 20), (0, 10), (15, 10), 1)
    # vertical brick offsets
    pygame.draw.line(s, _darken(COLOR_WALL, 20), (8, 0), (8, 4), 1)
    pygame.draw.line(s, _darken(COLOR_WALL, 20), (4, 5), (4, 10), 1)
    pygame.draw.line(s, _darken(COLOR_WALL, 20), (12, 5), (12, 10), 1)
    pygame.draw.line(s, _darken(COLOR_WALL, 20), (8, 11), (8, 15), 1)
    # gold trim at bottom
    pygame.draw.line(s, COLOR_WALL_TRIM, (0, 14), (15, 14), 1)
    pygame.draw.line(s, COLOR_WALL_TRIM, (0, 15), (15, 15), 1)
    return _put("tile_wall", _scale(s))


def tile_carpet() -> pygame.Surface:
    cached = _key("tile_carpet")
    if cached:
        return cached
    s = _make(16, 16)
    s.fill(COLOR_CARPET_DARK)
    # diamond pattern
    for i in range(0, 16, 4):
        for j in range(0, 16, 4):
            s.set_at((i + 2, j + 2), COLOR_CARPET_LIGHT)
            s.set_at((i + 1, j + 2), _darken(COLOR_CARPET_LIGHT, 30))
            s.set_at((i + 3, j + 2), _darken(COLOR_CARPET_LIGHT, 30))
            s.set_at((i + 2, j + 1), _darken(COLOR_CARPET_LIGHT, 30))
            s.set_at((i + 2, j + 3), _darken(COLOR_CARPET_LIGHT, 30))
    return _put("tile_carpet", _scale(s))


def tile_desk() -> pygame.Surface:
    cached = _key("tile_desk")
    if cached:
        return cached
    s = _make(16, 16)
    s.fill(COLOR_DESK)
    # wood grain
    pygame.draw.line(s, _darken(COLOR_DESK, 15), (0, 3), (15, 3), 1)
    pygame.draw.line(s, _darken(COLOR_DESK, 10), (0, 7), (15, 7), 1)
    pygame.draw.line(s, _darken(COLOR_DESK, 15), (0, 12), (15, 12), 1)
    # edge highlight
    pygame.draw.line(s, _lighten(COLOR_DESK, 30), (0, 0), (15, 0), 1)
    # counter lip
    pygame.draw.line(s, _darken(COLOR_DESK, 30), (0, 15), (15, 15), 1)
    return _put("tile_desk", _scale(s))


def tile_seat_empty() -> pygame.Surface:
    cached = _key("tile_seat_empty")
    if cached:
        return cached
    s = _make(16, 16)
    s.fill(COLOR_FLOOR)
    # seat back
    pygame.draw.rect(s, COLOR_SEAT_EMPTY, (3, 2, 10, 5))
    pygame.draw.rect(s, _darken(COLOR_SEAT_EMPTY, 20), (3, 2, 10, 1))
    # seat cushion
    pygame.draw.rect(s, _lighten(COLOR_SEAT_EMPTY, 15), (3, 8, 10, 5))
    # arm rests
    pygame.draw.rect(s, _darken(COLOR_SEAT_EMPTY, 30), (2, 4, 1, 9))
    pygame.draw.rect(s, _darken(COLOR_SEAT_EMPTY, 30), (13, 4, 1, 9))
    return _put("tile_seat_empty", _scale(s))


def tile_seat_taken() -> pygame.Surface:
    cached = _key("tile_seat_taken")
    if cached:
        return cached
    s = _make(16, 16)
    s.fill(COLOR_FLOOR)
    # seat back (darker when someone's sitting)
    pygame.draw.rect(s, COLOR_SEAT_TAKEN, (3, 2, 10, 5))
    # glow aura
    pygame.draw.rect(s, (255, 210, 80, 60), (1, 0, 14, 16))
    # seat cushion
    pygame.draw.rect(s, _lighten(COLOR_SEAT_TAKEN, 10), (3, 8, 10, 5))
    # arm rests
    pygame.draw.rect(s, _darken(COLOR_SEAT_TAKEN, 30), (2, 4, 1, 9))
    pygame.draw.rect(s, _darken(COLOR_SEAT_TAKEN, 30), (13, 4, 1, 9))
    return _put("tile_seat_taken", _scale(s))


def tile_entrance() -> pygame.Surface:
    cached = _key("tile_entrance")
    if cached:
        return cached
    s = _make(16, 16)
    s.fill(COLOR_CARPET_DARK)
    # door frame
    pygame.draw.rect(s, COLOR_WALL_TRIM, (0, 0, 16, 2))
    pygame.draw.rect(s, COLOR_WALL_TRIM, (0, 0, 2, 16))
    pygame.draw.rect(s, COLOR_WALL_TRIM, (14, 0, 2, 16))
    # welcome mat
    pygame.draw.rect(s, (60, 90, 60), (4, 10, 8, 4))
    return _put("tile_entrance", _scale(s))


def tile_neon_sign() -> pygame.Surface:
    """A tile-sized neon accent strip."""
    cached = _key("tile_neon_sign")
    if cached:
        return cached
    s = _make(16, 16)
    s.fill(COLOR_WALL)
    # neon strip
    pygame.draw.rect(s, COLOR_NEON_PINK, (2, 6, 12, 4))
    # glow
    pygame.draw.rect(s, (*COLOR_NEON_PINK, 80), (1, 5, 14, 6))
    return _put("tile_neon_sign", _scale(s))


def tile_queue_marker() -> pygame.Surface:
    """Floor tile with a queue rope marker."""
    cached = _key("tile_queue_marker")
    if cached:
        return cached
    s = _make(16, 16)
    s.fill(COLOR_FLOOR)
    # stanchion posts
    pygame.draw.rect(s, COLOR_WALL_TRIM, (2, 3, 2, 10))
    pygame.draw.rect(s, COLOR_WALL_TRIM, (12, 3, 2, 10))
    # rope
    pygame.draw.line(s, COLOR_NEON_GOLD, (3, 7), (13, 7), 1)
    pygame.draw.line(s, _darken(COLOR_NEON_GOLD, 30), (3, 8), (13, 8), 1)
    return _put("tile_queue_marker", _scale(s))


def tile_snack_bar() -> pygame.Surface:
    """Concession stand counter tile."""
    cached = _key("tile_snack_bar")
    if cached:
        return cached
    s = _make(16, 16)
    s.fill(COLOR_DESK)
    # counter top glass display
    pygame.draw.rect(s, (160, 200, 220), (2, 2, 12, 6))
    pygame.draw.rect(s, _darken(COLOR_DESK, 15), (2, 8, 12, 2))
    # popcorn bucket icon
    pygame.draw.rect(s, (255, 80, 80), (5, 10, 6, 5))
    pygame.draw.rect(s, (255, 255, 200), (6, 9, 4, 2))  # popcorn
    return _put("tile_snack_bar", _scale(s))


# =====================================================================
#                       CHARACTER SPRITES
# =====================================================================

def _draw_character(body_color, head_color=(240, 210, 180),
                    hat_color=None, accessory_color=None,
                    frame=0, direction=0):
    """
    Draw a 16×24 character sprite.
    direction: 0=down, 1=left, 2=right, 3=up
    frame: 0-3 walk cycle
    """
    s = _make(16, 24)

    # Bob offset for walk animation
    bob = 0
    if frame in (1, 3):
        bob = -1

    # ── Shadow ──
    pygame.draw.ellipse(s, (0, 0, 0, 40), (3, 20, 10, 4))

    # ── Legs ──
    leg_offset = [-1, 0, 1, 0][frame]
    pygame.draw.rect(s, _darken(body_color, 40), (5 - leg_offset, 17 + bob, 3, 4))
    pygame.draw.rect(s, _darken(body_color, 40), (8 + leg_offset, 17 + bob, 3, 4))
    # Shoes
    pygame.draw.rect(s, (50, 40, 35), (5 - leg_offset, 20 + bob, 3, 2))
    pygame.draw.rect(s, (50, 40, 35), (8 + leg_offset, 20 + bob, 3, 2))

    # ── Body ──
    pygame.draw.rect(s, body_color, (4, 11 + bob, 8, 7))
    # shirt detail
    pygame.draw.line(s, _darken(body_color, 20), (8, 12 + bob), (8, 17 + bob), 1)

    # ── Accessory (apron, vest overlay) ──
    if accessory_color:
        pygame.draw.rect(s, accessory_color, (5, 13 + bob, 6, 4))

    # ── Arms ──
    pygame.draw.rect(s, body_color, (2, 12 + bob, 2, 5))
    pygame.draw.rect(s, body_color, (12, 12 + bob, 2, 5))
    # Hands
    pygame.draw.rect(s, head_color, (2, 16 + bob, 2, 2))
    pygame.draw.rect(s, head_color, (12, 16 + bob, 2, 2))

    # ── Head ──
    pygame.draw.rect(s, head_color, (4, 3 + bob, 8, 8))

    # ── Face (depends on direction) ──
    if direction == 0:  # down (facing camera)
        # Eyes
        pygame.draw.rect(s, (40, 30, 30), (5, 6 + bob, 2, 2))
        pygame.draw.rect(s, (40, 30, 30), (9, 6 + bob, 2, 2))
        # Eye highlights
        s.set_at((5, 6 + bob), (255, 255, 255))
        s.set_at((9, 6 + bob), (255, 255, 255))
        # Mouth
        pygame.draw.line(s, (180, 100, 100), (6, 9 + bob), (9, 9 + bob), 1)
    elif direction == 3:  # up (facing away)
        pass  # no face features
    elif direction == 1:  # left
        pygame.draw.rect(s, (40, 30, 30), (4, 6 + bob, 2, 2))
        s.set_at((4, 6 + bob), (255, 255, 255))
    elif direction == 2:  # right
        pygame.draw.rect(s, (40, 30, 30), (10, 6 + bob, 2, 2))
        s.set_at((11, 6 + bob), (255, 255, 255))

    # ── Hair ──
    hair_color = _darken(head_color, 80)
    pygame.draw.rect(s, hair_color, (4, 2 + bob, 8, 2))
    if direction == 0:
        pygame.draw.rect(s, hair_color, (4, 3 + bob, 1, 3))
        pygame.draw.rect(s, hair_color, (11, 3 + bob, 1, 3))
    elif direction == 3:
        pygame.draw.rect(s, hair_color, (4, 3 + bob, 8, 4))

    # ── Hat (optional for staff) ──
    if hat_color:
        pygame.draw.rect(s, hat_color, (3, 1 + bob, 10, 3))
        pygame.draw.rect(s, _darken(hat_color, 20), (2, 3 + bob, 12, 1))

    return _scale(s)


def moviegoer_sprite(color_index: int = 0, frame: int = 0,
                     direction: int = 0) -> pygame.Surface:
    """Get a moviegoer sprite with the given color, frame, and direction."""
    key = f"moviegoer_{color_index}_{frame}_{direction}"
    cached = _key(key)
    if cached:
        return cached
    color = MOVIEGOER_COLORS[color_index % len(MOVIEGOER_COLORS)]
    surf = _draw_character(color, frame=frame, direction=direction)
    return _put(key, surf)


def cashier_sprite(frame: int = 0, direction: int = 0) -> pygame.Surface:
    key = f"cashier_{frame}_{direction}"
    cached = _key(key)
    if cached:
        return cached
    surf = _draw_character(
        COLOR_CASHIER_VEST, accessory_color=None,
        hat_color=None, frame=frame, direction=direction
    )
    return _put(key, surf)


def usher_sprite(frame: int = 0, direction: int = 0) -> pygame.Surface:
    key = f"usher_{frame}_{direction}"
    cached = _key(key)
    if cached:
        return cached
    surf = _draw_character(
        COLOR_USHER_JACKET, hat_color=(60, 20, 25),
        frame=frame, direction=direction
    )
    return _put(key, surf)


def server_sprite(frame: int = 0, direction: int = 0) -> pygame.Surface:
    key = f"server_{frame}_{direction}"
    cached = _key(key)
    if cached:
        return cached
    surf = _draw_character(
        (60, 60, 120), accessory_color=COLOR_SERVER_APRON,
        frame=frame, direction=direction
    )
    return _put(key, surf)


# =====================================================================
#                        UI / ICON ASSETS
# =====================================================================

def icon_ticket() -> pygame.Surface:
    cached = _key("icon_ticket")
    if cached:
        return cached
    s = _make(12, 8)
    pygame.draw.rect(s, COLOR_NEON_GOLD, (0, 0, 12, 8))
    pygame.draw.rect(s, _darken(COLOR_NEON_GOLD, 40), (0, 0, 12, 8), 1)
    # perforation
    for y in range(0, 8, 2):
        s.set_at((4, y), COLOR_FLOOR)
    # text line
    pygame.draw.line(s, _darken(COLOR_NEON_GOLD, 60), (6, 3), (10, 3), 1)
    return _put("icon_ticket", _scale(s, 3))


def icon_popcorn() -> pygame.Surface:
    cached = _key("icon_popcorn")
    if cached:
        return cached
    s = _make(10, 12)
    # bucket
    pygame.draw.rect(s, (255, 60, 60), (2, 4, 6, 7))
    pygame.draw.line(s, (255, 255, 255), (2, 6), (7, 6), 1)
    # popcorn puffs
    for pos in [(3, 3), (5, 2), (7, 3), (4, 1), (6, 1)]:
        pygame.draw.rect(s, (255, 255, 200), (pos[0], pos[1], 2, 2))
    return _put("icon_popcorn", _scale(s, 3))


def star_particle() -> pygame.Surface:
    """A small glowing star for particle effects."""
    cached = _key("star_particle")
    if cached:
        return cached
    s = _make(8, 8)
    # diamond shape
    points = [(4, 0), (6, 3), (8, 4), (6, 5), (4, 8), (2, 5), (0, 4), (2, 3)]
    pygame.draw.polygon(s, COLOR_NEON_GOLD, points)
    return _put("star_particle", _scale(s, 2))


# =====================================================================
#                    EMOTION BUBBLE ICONS
# =====================================================================

def bubble_waiting() -> pygame.Surface:
    """Yellow hourglass bubble."""
    cached = _key("bubble_waiting")
    if cached:
        return cached
    s = _make(12, 14)
    # bubble bg
    pygame.draw.rect(s, (255, 255, 255, 200), (1, 1, 10, 10), border_radius=2)
    pygame.draw.rect(s, (100, 100, 100), (1, 1, 10, 10), 1)
    # hourglass
    pygame.draw.polygon(s, (255, 200, 60), [(3, 3), (9, 3), (6, 6)])
    pygame.draw.polygon(s, (255, 200, 60), [(3, 9), (9, 9), (6, 6)])
    # tail
    s.set_at((6, 12), (255, 255, 255, 200))
    s.set_at((5, 13), (255, 255, 255, 200))
    return _put("bubble_waiting", _scale(s, 2))


def bubble_happy() -> pygame.Surface:
    """Green smiley bubble."""
    cached = _key("bubble_happy")
    if cached:
        return cached
    s = _make(12, 14)
    pygame.draw.rect(s, (255, 255, 255, 200), (1, 1, 10, 10), border_radius=2)
    pygame.draw.rect(s, (100, 100, 100), (1, 1, 10, 10), 1)
    # smiley
    s.set_at((4, 4), (80, 200, 80))
    s.set_at((8, 4), (80, 200, 80))
    pygame.draw.line(s, (80, 200, 80), (4, 7), (5, 8), 1)
    pygame.draw.line(s, (80, 200, 80), (7, 8), (8, 7), 1)
    pygame.draw.line(s, (80, 200, 80), (5, 8), (7, 8), 1)
    s.set_at((6, 12), (255, 255, 255, 200))
    return _put("bubble_happy", _scale(s, 2))


def bubble_angry() -> pygame.Surface:
    """Red frustrated bubble."""
    cached = _key("bubble_angry")
    if cached:
        return cached
    s = _make(12, 14)
    pygame.draw.rect(s, (255, 255, 255, 200), (1, 1, 10, 10), border_radius=2)
    pygame.draw.rect(s, (100, 100, 100), (1, 1, 10, 10), 1)
    # angry face
    s.set_at((4, 5), (255, 60, 60))
    s.set_at((8, 5), (255, 60, 60))
    # angry eyebrows
    pygame.draw.line(s, (255, 60, 60), (3, 3), (5, 4), 1)
    pygame.draw.line(s, (255, 60, 60), (9, 3), (7, 4), 1)
    # frown
    pygame.draw.line(s, (255, 60, 60), (4, 8), (5, 7), 1)
    pygame.draw.line(s, (255, 60, 60), (7, 7), (8, 8), 1)
    s.set_at((6, 12), (255, 255, 255, 200))
    return _put("bubble_angry", _scale(s, 2))


def bubble_food() -> pygame.Surface:
    """Question mark bubble (deciding on food)."""
    cached = _key("bubble_food")
    if cached:
        return cached
    s = _make(12, 14)
    pygame.draw.rect(s, (255, 255, 255, 200), (1, 1, 10, 10), border_radius=2)
    pygame.draw.rect(s, (100, 100, 100), (1, 1, 10, 10), 1)
    # question mark
    pygame.draw.line(s, (200, 160, 60), (5, 3), (7, 3), 1)
    s.set_at((8, 4), (200, 160, 60))
    pygame.draw.line(s, (200, 160, 60), (6, 5), (7, 5), 1)
    s.set_at((6, 6), (200, 160, 60))
    s.set_at((6, 8), (200, 160, 60))
    s.set_at((6, 12), (255, 255, 255, 200))
    return _put("bubble_food", _scale(s, 2))


def bubble_star() -> pygame.Surface:
    """Gold star bubble (just seated)."""
    cached = _key("bubble_star")
    if cached:
        return cached
    s = _make(12, 14)
    pygame.draw.rect(s, (255, 255, 255, 200), (1, 1, 10, 10), border_radius=2)
    pygame.draw.rect(s, (100, 100, 100), (1, 1, 10, 10), 1)
    # star
    star_pts = [(6, 2), (7, 5), (10, 5), (8, 7), (9, 10), (6, 8), (3, 10), (4, 7), (2, 5), (5, 5)]
    pygame.draw.polygon(s, COLOR_NEON_GOLD, star_pts)
    s.set_at((6, 12), (255, 255, 255, 200))
    return _put("bubble_star", _scale(s, 2))


def clear_cache():
    """Clear all cached assets (call on reset)."""
    _cache.clear()
