"""
CinePlex Dreams — Asset Loader

Loads PNGs from game/assets/ if they exist.
Falls back to programmatically generated placeholder surfaces.
"""

import os
import pygame
from game.settings import (
    TILE_SIZE, ASSETS_DIR, TILES_DIR, SPRITES_DIR, UI_DIR, BG_DIR,
    C_FLOOR, C_FLOOR_ALT, C_CARPET_D, C_CARPET_L, C_WALL, C_WALL_TRIM,
    C_DESK, C_SEAT_EMPTY, C_SEAT_TAKEN, C_DOOR, C_SCREEN,
    C_NEON_PINK, C_NEON_CYAN, C_NEON_GOLD, C_BG_DARK,
    NPC_COLORS, C_CASHIER_VEST, C_USHER_JACKET, C_SERVER_APRON,
    PLAYER_SPRITE_W, PLAYER_SPRITE_H, SCREEN_W, SCREEN_H,
    C_SECURITY, C_POSTER_BG, C_PLANT, C_TABLE, C_CORRIDOR,
)

_cache: dict[str, pygame.Surface] = {}


def _get(key):
    return _cache.get(key)


def _put(key, surf):
    _cache[key] = surf
    return surf


def _darken(c, amt=35):
    return tuple(max(0, v - amt) for v in c[:3])


def _lighten(c, amt=35):
    return tuple(min(255, v + amt) for v in c[:3])


def _make(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


# ── Tile generators & image loader ───────────────────────────────────────

_tileset_sheet_surf: pygame.Surface | None = None

def get_tileset_sheet() -> pygame.Surface | None:
    global _tileset_sheet_surf
    if _tileset_sheet_surf is not None:
        return _tileset_sheet_surf
    for fname in ("tileset.png", "tileset.jpg", "tileset.jpeg"):
        path = os.path.join(TILES_DIR, fname)
        if os.path.exists(path):
            _tileset_sheet_surf = pygame.image.load(path).convert_alpha()
            return _tileset_sheet_surf
    return None


def _slice_tileset_tile(col: int, row: int, key_out_bg: bool = False, base_surf: pygame.Surface | None = None) -> pygame.Surface | None:
    sheet = get_tileset_sheet()
    if not sheet:
        return None
    sw, sh = sheet.get_size()
    # 5 columns, 2 rows centered in the tileset image
    x = int(col * (sw / 5.0))
    w = int((col + 1) * (sw / 5.0)) - x
    y = int(307 * (sh / 1024.0)) if row == 0 else int(512 * (sh / 1024.0))
    h = int(205 * (sh / 1024.0))

    tile = pygame.Surface((w, h), pygame.SRCALPHA)
    tile.blit(sheet, (0, 0), (x, y, w, h))

    if key_out_bg:
        px = pygame.PixelArray(tile)
        for ix in range(w):
            for iy in range(h):
                color = tile.unmap_rgb(px[ix, iy])
                if abs(color.r - color.g) < 14 and abs(color.g - color.b) < 14 and color.r > 140:
                    px[ix, iy] = (0, 0, 0, 0)
        del px

    scaled = pygame.transform.smoothscale(tile, (TILE_SIZE, TILE_SIZE))

    if base_surf is not None:
        result = base_surf.copy()
        result.blit(scaled, (0, 0))
        return result
    return scaled


def _load_tile_img(filename: str) -> pygame.Surface | None:
    """Loads a tile image from assets/tiles/ if it exists, scaling its width to TILE_SIZE
    while maintaining aspect ratio, so tall objects aren't squished."""
    for ext in (".png", ".jpg", ".jpeg"):
        path = os.path.join(TILES_DIR, filename + ext)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            w, h = img.get_size()
            new_w = TILE_SIZE
            new_h = int(h * (TILE_SIZE / w))
            return pygame.transform.smoothscale(img, (new_w, new_h))
    return None


def _load_custom_tileset():
    """Load the custom 'new tileset.png' spritesheet once."""
    c = _get("_custom_tileset")
    if c: return c
    path = os.path.join(TILES_DIR, "new tileset.png")
    if os.path.exists(path):
        sheet = pygame.image.load(path).convert_alpha()
        return _put("_custom_tileset", sheet)
    return None


def _slice_custom(x: int, y: int, w: int, h: int, target_w=TILE_SIZE, target_h=TILE_SIZE) -> pygame.Surface | None:
    """Slice a rectangle from the custom tileset and scale to target size."""
    sheet = _load_custom_tileset()
    if sheet is None:
        return None
    tile = pygame.Surface((w, h), pygame.SRCALPHA)
    tile.blit(sheet, (0, 0), (x, y, w, h))
    return pygame.transform.smoothscale(tile, (target_w, target_h))


def _gen_tile(color, detail_fn=None):
    s = _make(TILE_SIZE, TILE_SIZE)
    s.fill(color)
    if detail_fn:
        detail_fn(s)
    return s


def tile_floor():
    c = _get("t_floor")
    if c: return c
    img = _load_tile_img("floor") or _slice_tileset_tile(0, 0)
    if img: return _put("t_floor", img)
    def detail(s):
        h = TILE_SIZE // 2
        pygame.draw.rect(s, C_FLOOR_ALT, (0, 0, h, h))
        pygame.draw.rect(s, C_FLOOR_ALT, (h, h, h, h))
    return _put("t_floor", _gen_tile(C_FLOOR, detail))


def tile_carpet():
    c = _get("t_carpet")
    if c: return c
    img = _load_tile_img("carpet") or _slice_tileset_tile(1, 0)
    if img: return _put("t_carpet", img)
    def detail(s):
        for x in range(0, TILE_SIZE, 12):
            for y in range(0, TILE_SIZE, 12):
                pygame.draw.rect(s, C_CARPET_L, (x+4, y+4, 4, 4))
    return _put("t_carpet", _gen_tile(C_CARPET_D, detail))


def tile_wall():
    c = _get("t_wall")
    if c: return c
    img = _load_tile_img("wall") or _slice_tileset_tile(2, 0)
    if img: return _put("t_wall", img)
    def detail(s):
        for y in range(0, TILE_SIZE, 12):
            pygame.draw.line(s, _darken(C_WALL, 20), (0, y), (TILE_SIZE, y))
            off = 16 if (y // 12) % 2 == 0 else 0
            for x in range(off, TILE_SIZE, 32):
                pygame.draw.line(s, _darken(C_WALL, 20), (x, y), (x, y + 12))
        pygame.draw.rect(s, C_WALL_TRIM, (0, TILE_SIZE - 4, TILE_SIZE, 4))
    return _put("t_wall", _gen_tile(C_WALL, detail))


def tile_desk():
    c = _get("t_desk")
    if c: return c
    # Try: individual file > counter.png > custom tileset ticket booth > old tileset > procedural
    img = (_load_tile_img("ticket_booth") or _load_tile_img("counter")
           or _load_tile_img("desk") or _slice_tileset_tile(3, 0, key_out_bg=True, base_surf=tile_floor()))
    if img: return _put("t_desk", img)
    def detail(s):
        pygame.draw.rect(s, _lighten(C_DESK, 20), (0, 0, TILE_SIZE, 4))
        for y in range(8, TILE_SIZE, 10):
            pygame.draw.line(s, _darken(C_DESK, 15), (0, y), (TILE_SIZE, y))
    return _put("t_desk", _gen_tile(C_DESK, detail))


def tile_seat():
    c = _get("t_seat")
    if c: return c
    # Try custom tileset seats (3 red seats block at ~0, 272, 128, 80)
    img = _load_tile_img("seat") or _slice_custom(0, 272, 42, 80)
    if not img:
        img = _slice_tileset_tile(0, 1, key_out_bg=True, base_surf=tile_carpet())
    if img: return _put("t_seat", img)
    def detail(s):
        pygame.draw.rect(s, C_SEAT_EMPTY, (8, 4, TILE_SIZE - 16, 16))
        pygame.draw.rect(s, _darken(C_SEAT_EMPTY, 20), (8, 4, TILE_SIZE - 16, 3))
        pygame.draw.rect(s, _lighten(C_SEAT_EMPTY, 15), (8, 22, TILE_SIZE - 16, 16))
        pygame.draw.rect(s, _darken(C_SEAT_EMPTY, 30), (4, 10, 4, 28))
        pygame.draw.rect(s, _darken(C_SEAT_EMPTY, 30), (TILE_SIZE - 8, 10, 4, 28))
    return _put("t_seat", _gen_tile(C_FLOOR, detail))


def tile_door():
    c = _get("t_door")
    if c: return c
    img = _load_tile_img("door") or _slice_tileset_tile(4, 0, key_out_bg=True, base_surf=tile_wall())
    if img: return _put("t_door", img)
    def detail(s):
        pygame.draw.rect(s, C_DOOR, (8, 4, TILE_SIZE - 16, TILE_SIZE - 8))
        pygame.draw.rect(s, C_WALL_TRIM, (8, 4, TILE_SIZE - 16, TILE_SIZE - 8), 2)
        pygame.draw.circle(s, C_WALL_TRIM, (TILE_SIZE - 14, TILE_SIZE // 2), 3)
    return _put("t_door", _gen_tile(C_WALL, detail))


def tile_neon():
    c = _get("t_neon")
    if c: return c
    img = _load_tile_img("neon") or _slice_tileset_tile(1, 1, key_out_bg=True, base_surf=tile_wall())
    if img: return _put("t_neon", img)
    def detail(s):
        pygame.draw.rect(s, C_NEON_PINK, (4, 16, TILE_SIZE - 8, 16))
        glow = _make(TILE_SIZE, TILE_SIZE)
        glow.fill((*C_NEON_PINK[:3], 40))
        s.blit(glow, (0, 0))
    return _put("t_neon", _gen_tile(C_WALL, detail))


def tile_queue() -> pygame.Surface:
    c = _get("t_queue")
    if c: return c
    img = _load_tile_img("queue") or _slice_tileset_tile(2, 1, key_out_bg=True, base_surf=tile_floor())
    if img: return _put("t_queue", img)
    def detail(s):
        pygame.draw.rect(s, C_WALL_TRIM, (6, 8, 4, 32))
        pygame.draw.rect(s, C_WALL_TRIM, (TILE_SIZE - 10, 8, 4, 32))
        pygame.draw.line(s, (200, 50, 60), (8, 22), (TILE_SIZE - 8, 22), 3)
    return _put("t_queue", _gen_tile(C_FLOOR, detail))


def tile_snack() -> pygame.Surface:
    c = _get("t_snack")
    if c: return c
    # Try: popcorn.png > drinks.png > snack.png > old tileset > procedural
    img = (_load_tile_img("popcorn") or _load_tile_img("drinks")
           or _load_tile_img("snack") or _slice_tileset_tile(3, 1, key_out_bg=True, base_surf=tile_floor()))
    if img: return _put("t_snack", img)
    def detail(s):
        pygame.draw.rect(s, (200, 220, 240), (4, 4, TILE_SIZE - 8, 18))
        pygame.draw.rect(s, _darken(C_DESK), (4, 22, TILE_SIZE - 8, 6))
        pygame.draw.rect(s, (240, 60, 60), (14, 30, 10, 12))
        pygame.draw.rect(s, (255, 255, 200), (16, 28, 6, 4))
    return _put("t_snack", _gen_tile(C_DESK, detail))


def tile_screen() -> pygame.Surface:
    c = _get("t_screen")
    if c: return c
    # Try custom tileset cinema screen (red U shape, top-left of sheet: 0, 0, 128, 96)
    img = _load_tile_img("screen") or _slice_custom(0, 0, 128, 96)
    if not img:
        img = _slice_tileset_tile(4, 1)
    if img: return _put("t_screen", img)
    def detail(s):
        pygame.draw.rect(s, C_SCREEN, (2, 2, TILE_SIZE - 4, TILE_SIZE - 4))
        pygame.draw.rect(s, (40, 60, 120), (2, 2, TILE_SIZE - 4, TILE_SIZE - 4), 2)
        glow = _make(TILE_SIZE, TILE_SIZE)
        glow.fill((*C_NEON_CYAN[:3], 20))
        s.blit(glow, (0, 0))
    return _put("t_screen", _gen_tile(C_BG_DARK, detail))


def tile_usher() -> pygame.Surface:
    c = _get("t_usher")
    if c: return c
    img = _load_tile_img("usher")
    if img: return _put("t_usher", img)
    # Procedural fallback
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(C_FLOOR)
    pygame.draw.rect(surf, (150, 50, 50), (4, 4, 40, 40), border_radius=4)
    pygame.draw.circle(surf, (255, 200, 100), (24, 24), 12)
    return _put("t_usher", surf)


def tile_security() -> pygame.Surface:
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(C_FLOOR)
    pygame.draw.rect(surf, C_SECURITY, (0, 10, TILE_SIZE, 28), border_radius=4)
    pygame.draw.rect(surf, (50, 50, 50), (10, 14, 28, 20)) # scanner
    return surf


def tile_poster() -> pygame.Surface:
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(C_WALL)
    pygame.draw.rect(surf, C_POSTER_BG, (8, 4, 32, 40))
    pygame.draw.rect(surf, (200, 200, 200), (8, 4, 32, 40), 2) # frame
    # abstract poster art
    pygame.draw.circle(surf, (255, 100, 100), (24, 20), 8)
    pygame.draw.line(surf, (200, 200, 200), (12, 34), (36, 34), 2)
    return surf


def tile_plant() -> pygame.Surface:
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(C_FLOOR)
    # pot
    pygame.draw.rect(surf, (100, 70, 50), (14, 24, 20, 24))
    # leaves
    pygame.draw.circle(surf, C_PLANT, (16, 16), 12)
    pygame.draw.circle(surf, C_PLANT, (32, 16), 12)
    pygame.draw.circle(surf, (40, 100, 50), (24, 8), 14)
    return surf


def tile_table() -> pygame.Surface:
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(C_FLOOR)
    pygame.draw.circle(surf, C_TABLE, (24, 24), 20)
    pygame.draw.circle(surf, (100, 70, 40), (24, 24), 16)
    return surf


def tile_corridor() -> pygame.Surface:
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(C_CORRIDOR)
    # subtle pattern
    pygame.draw.line(surf, (35, 25, 50), (0, 0), (TILE_SIZE, TILE_SIZE))
    pygame.draw.line(surf, (35, 25, 50), (TILE_SIZE, 0), (0, TILE_SIZE))
    return surf


# Tile lookup by ID
TILE_FUNCS = {
    1: tile_wall,
    2: tile_floor,
    3: tile_carpet,
    4: tile_desk,
    5: tile_seat,
    6: tile_door,
    7: tile_neon,
    8: tile_queue,
    9: tile_snack,
    10: tile_screen,
    11: tile_usher,
    12: tile_security,
    13: tile_poster,
    14: tile_plant,
    15: tile_table,
    16: tile_corridor,
}


# ── Character sprite generators ──────────────────────────────────────────

def _gen_char(body_color, head_color=(235, 200, 170), frame=0, direction=0,
              accessory=None, hat_color=None):
    """Generate a small character sprite at native resolution, then scale."""
    w, h = 16, 24
    s = _make(w, h)
    bob = -1 if frame in (1, 3) else 0
    leg_off = [-1, 0, 1, 0][frame % 4]

    # shadow
    pygame.draw.ellipse(s, (0, 0, 0, 50), (3, 20, 10, 4))
    # legs
    pygame.draw.rect(s, _darken(body_color, 50), (5 - leg_off, 17 + bob, 3, 4))
    pygame.draw.rect(s, _darken(body_color, 50), (8 + leg_off, 17 + bob, 3, 4))
    # shoes
    pygame.draw.rect(s, (50, 40, 35), (5 - leg_off, 20 + bob, 3, 2))
    pygame.draw.rect(s, (50, 40, 35), (8 + leg_off, 20 + bob, 3, 2))
    # body
    pygame.draw.rect(s, body_color, (4, 11 + bob, 8, 7))
    pygame.draw.line(s, _darken(body_color, 25), (8, 12 + bob), (8, 17 + bob))
    # accessory overlay
    if accessory:
        pygame.draw.rect(s, accessory, (5, 13 + bob, 6, 4))
    # arms
    pygame.draw.rect(s, body_color, (2, 12 + bob, 2, 5))
    pygame.draw.rect(s, body_color, (12, 12 + bob, 2, 5))
    pygame.draw.rect(s, head_color, (2, 16 + bob, 2, 2))
    pygame.draw.rect(s, head_color, (12, 16 + bob, 2, 2))
    # head
    pygame.draw.rect(s, head_color, (4, 3 + bob, 8, 8))
    # hair
    hair = _darken(head_color, 80)
    pygame.draw.rect(s, hair, (4, 2 + bob, 8, 2))
    if direction == 0:  # down
        pygame.draw.rect(s, hair, (4, 3 + bob, 1, 3))
        pygame.draw.rect(s, hair, (11, 3 + bob, 1, 3))
        # eyes
        pygame.draw.rect(s, (40, 30, 30), (5, 6 + bob, 2, 2))
        pygame.draw.rect(s, (40, 30, 30), (9, 6 + bob, 2, 2))
        s.set_at((5, 6 + bob), (255, 255, 255))
        s.set_at((9, 6 + bob), (255, 255, 255))
        pygame.draw.line(s, (180, 100, 100), (6, 9 + bob), (9, 9 + bob))
    elif direction == 3:  # up
        pygame.draw.rect(s, hair, (4, 3 + bob, 8, 4))
    elif direction == 1:  # left
        pygame.draw.rect(s, (40, 30, 30), (4, 6 + bob, 2, 2))
        s.set_at((4, 6 + bob), (255, 255, 255))
    elif direction == 2:  # right
        pygame.draw.rect(s, (40, 30, 30), (10, 6 + bob, 2, 2))
        s.set_at((11, 6 + bob), (255, 255, 255))
    # hat
    if hat_color:
        pygame.draw.rect(s, hat_color, (3, 1 + bob, 10, 3))
        pygame.draw.rect(s, _darken(hat_color, 20), (2, 3 + bob, 12, 1))

    # scale to game size
    return pygame.transform.scale(s, (PLAYER_SPRITE_W * 2, PLAYER_SPRITE_H * 2))


def get_player_sheet():
    c = _get("player_sheet")
    if c is not None: return c
    # Check for jush player.png or player.png
    for fname in ("jush player.png", "jush player.jpg", "player.png", "player.jpg"):
        path = os.path.join(SPRITES_DIR, fname)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            return _put("player_sheet", img)
    return _put("player_sheet", False)

def player_sprite(frame=0, direction=0):
    key = f"player_{frame}_{direction}"
    c = _get(key)
    if c: return c

    sheet = get_player_sheet()
    if sheet:
        fw = sheet.get_width() // 4
        fh = sheet.get_height() // 4

        # Directions: 0=Down, 1=Left, 2=Right, 3=Up
        # In jush player sprite sheet: Row 0=Down, Row 1=Left, Row 3=Up
        if direction == 0:     # Down
            row = 0
            flip_x = False
        elif direction == 1:   # Left (Row 1 naturally faces left)
            row = 1
            flip_x = False
        elif direction == 2:   # Right (flip Row 1 to face right)
            row = 1
            flip_x = True
        elif direction == 3:   # Up
            row = 3
            flip_x = False
        else:
            row = 0
            flip_x = False

        s = _make(fw, fh)
        s.blit(sheet, (0, 0), (frame * fw, row * fh, fw, fh))
        if flip_x:
            s = pygame.transform.flip(s, True, False)

        # Scale cleanly to player size (approx 52px high, 48px wide)
        target_w = 48
        target_h = int(target_w * (fh / fw))
        s = pygame.transform.smoothscale(s, (target_w, target_h))
    else:
        s = _gen_char((70, 100, 180), frame=frame, direction=direction)

    return _put(key, s)


def npc_sprite(color_idx=0, frame=0, direction=0):
    key = f"npc_{color_idx}_{frame}_{direction}"
    c = _get(key)
    if c: return c
    color = NPC_COLORS[color_idx % len(NPC_COLORS)]
    return _put(key, _gen_char(color, frame=frame, direction=direction))


def cashier_sprite(frame=0, direction=0):
    key = f"cashier_{frame}_{direction}"
    c = _get(key)
    if c: return c
    return _put(key, _gen_char(C_CASHIER_VEST, frame=frame, direction=direction))


def usher_sprite(frame=0, direction=0):
    key = f"usher_{frame}_{direction}"
    c = _get(key)
    if c: return c
    return _put(key, _gen_char(C_USHER_JACKET, hat_color=(60, 20, 25),
                               frame=frame, direction=direction))


def server_sprite(frame=0, direction=0):
    key = f"server_{frame}_{direction}"
    c = _get(key)
    if c: return c
    return _put(key, _gen_char((60, 60, 120), accessory=C_SERVER_APRON,
                               frame=frame, direction=direction))


# ── Bubble / UI generators ───────────────────────────────────────────────

def _gen_bubble(icon_fn, bg=(255, 255, 255, 220)):
    s = _make(28, 32)
    pygame.draw.rect(s, bg, (1, 1, 26, 24), border_radius=5)
    pygame.draw.rect(s, (120, 120, 120), (1, 1, 26, 24), 1, border_radius=5)
    # tail
    pygame.draw.polygon(s, bg, [(12, 25), (16, 25), (14, 31)])
    if icon_fn:
        icon_fn(s)
    return s


def bubble_waiting():
    c = _get("bub_wait")
    if c: return c
    def icon(s):
        pygame.draw.polygon(s, (240, 190, 50), [(8, 6), (20, 6), (14, 14)])
        pygame.draw.polygon(s, (240, 190, 50), [(8, 22), (20, 22), (14, 14)])
    return _put("bub_wait", _gen_bubble(icon))


def bubble_happy():
    c = _get("bub_happy")
    if c: return c
    def icon(s):
        pygame.draw.circle(s, (80, 200, 80), (10, 10), 2)
        pygame.draw.circle(s, (80, 200, 80), (18, 10), 2)
        pygame.draw.arc(s, (80, 200, 80), (8, 12, 12, 8), 3.14, 6.28, 2)
    return _put("bub_happy", _gen_bubble(icon))


def bubble_angry():
    c = _get("bub_angry")
    if c: return c
    def icon(s):
        pygame.draw.circle(s, (240, 60, 60), (10, 10), 2)
        pygame.draw.circle(s, (240, 60, 60), (18, 10), 2)
        pygame.draw.line(s, (240, 60, 60), (8, 7), (12, 9), 2)
        pygame.draw.line(s, (240, 60, 60), (20, 7), (16, 9), 2)
        pygame.draw.arc(s, (240, 60, 60), (8, 16, 12, 6), 0, 3.14, 2)
    return _put("bub_angry", _gen_bubble(icon))


def bubble_star():
    c = _get("bub_star")
    if c: return c
    def icon(s):
        pts = [(14, 4), (16, 10), (22, 10), (17, 14),
               (19, 20), (14, 16), (9, 20), (11, 14), (6, 10), (12, 10)]
        pygame.draw.polygon(s, C_NEON_GOLD, pts)
    return _put("bub_star", _gen_bubble(icon))


def bubble_food():
    c = _get("bub_food")
    if c: return c
    def icon(s):
        # question mark
        pygame.draw.arc(s, (200, 160, 60), (9, 5, 10, 10), 0, 4.0, 2)
        pygame.draw.rect(s, (200, 160, 60), (13, 14, 2, 3))
        pygame.draw.rect(s, (200, 160, 60), (13, 19, 2, 2))
    return _put("bub_food", _gen_bubble(icon))


def bubble_speech(text, font):
    """Generate a speech bubble with custom text. Not cached."""
    rendered = font.render(text, True, (50, 40, 60))
    tw, th = rendered.get_size()
    pad = 8
    w = tw + pad * 2
    h = th + pad * 2 + 8
    s = _make(w, h)
    pygame.draw.rect(s, (255, 255, 255, 230), (0, 0, w, h - 8), border_radius=6)
    pygame.draw.rect(s, (120, 120, 120), (0, 0, w, h - 8), 1, border_radius=6)
    pygame.draw.polygon(s, (255, 255, 255, 230), [(w//2 - 4, h - 8), (w//2 + 4, h - 8), (w//2, h)])
    s.blit(rendered, (pad, pad))
    return s


# ── Background ────────────────────────────────────────────────────────────

def menu_background():
    c = _get("menu_bg")
    if c: return c
    path = os.path.join(BG_DIR, "main_menu.jpg")
    if os.path.exists(path):
        img = pygame.image.load(path).convert()
        img = pygame.transform.scale(img, (SCREEN_W, SCREEN_H))
        return _put("menu_bg", img)
    # fallback
    s = pygame.Surface((SCREEN_W, SCREEN_H))
    s.fill(C_BG_DARK)
    return _put("menu_bg", s)


def clear_cache():
    _cache.clear()
