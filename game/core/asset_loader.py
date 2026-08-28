
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


_TILESET_RECTS = {
    (0, 0): (  0, 307, 204, 205),
    (1, 0): (204, 307, 205, 205),
    (2, 0): (409, 307, 204, 205),
    (3, 0): (600, 307, 225, 205),
    (4, 0): (830, 307, 190, 205),
    (0, 1): (  0, 527, 170, 195),
    (1, 1): (170, 527, 220, 175),
    (2, 1): (390, 527, 175, 195),
    (3, 1): (560, 527, 260, 195),
    (4, 1): (830, 527, 190, 195),
}


def _slice_tileset_tile(col: int, row: int, key_out_bg: bool = False,
                        base_surf: pygame.Surface | None = None,
                        target_w: int = TILE_SIZE,
                        target_h: int = TILE_SIZE) -> pygame.Surface | None:
    sheet = get_tileset_sheet()
    if not sheet:
        return None
    rect = _TILESET_RECTS.get((col, row))
    if not rect:
        return None
    x, y, w, h = rect

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

    scaled = pygame.transform.smoothscale(tile, (target_w, target_h))

    if base_surf is not None:
        result = base_surf.copy()
        result.blit(scaled, (0, 0))
        return result
    return scaled


def _load_tile_img(filename: str) -> pygame.Surface | None:
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
    c = _get("_custom_tileset")
    if c: return c
    path = os.path.join(TILES_DIR, "new tileset.png")
    if os.path.exists(path):
        sheet = pygame.image.load(path).convert_alpha()
        return _put("_custom_tileset", sheet)
    return None


def _slice_custom(x: int, y: int, w: int, h: int, target_w=TILE_SIZE, target_h=TILE_SIZE) -> pygame.Surface | None:
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

    img = _load_tile_img("seat")
    if img:
        return _put("t_seat", img)

    img = _slice_tileset_tile(0, 1, key_out_bg=True, base_surf=tile_carpet())
    if img:
        return _put("t_seat", img)

    s = tile_carpet().copy()
    seat_c = (140, 25, 35)
    pygame.draw.rect(s, (80, 60, 40), (4, 8, 5, 32))
    pygame.draw.rect(s, (80, 60, 40), (TILE_SIZE-9, 8, 5, 32))
    pygame.draw.rect(s, _darken(seat_c, 40), (9, 4, TILE_SIZE-18, 18), border_radius=3)
    pygame.draw.rect(s, seat_c, (9, 20, TILE_SIZE-18, 18), border_radius=4)
    pygame.draw.rect(s, _lighten(seat_c, 30), (11, 6, TILE_SIZE-22, 3), border_radius=2)
    pygame.draw.rect(s, _lighten(seat_c, 20), (11, 22, TILE_SIZE-22, 4), border_radius=2)
    pygame.draw.circle(s, (200, 170, 80), (6, 12), 2)
    pygame.draw.circle(s, (200, 170, 80), (TILE_SIZE-7, 12), 2)
    return _put("t_seat", s)


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
    img = _load_tile_img("screen") or _slice_tileset_tile(4, 1)
    if img: return _put("t_screen", img)
    s = _make(TILE_SIZE, TILE_SIZE)
    s.fill((5, 5, 15))
    frame_c = (40, 35, 55)
    pygame.draw.rect(s, frame_c, (0, 0, TILE_SIZE, TILE_SIZE), border_radius=2)
    pygame.draw.rect(s, (8, 15, 40), (3, 3, TILE_SIZE-6, TILE_SIZE-6), border_radius=1)
    glow = _make(TILE_SIZE-8, TILE_SIZE-8)
    for y in range(glow.get_height()):
        a = int(15 * (1 - y / glow.get_height()))
        pygame.draw.line(glow, (100, 180, 255, a), (0, y), (glow.get_width(), y))
    s.blit(glow, (4, 4))
    pygame.draw.rect(s, _lighten(frame_c, 15), (2, TILE_SIZE-5, TILE_SIZE-4, 3))
    return _put("t_screen", s)


def tile_usher() -> pygame.Surface:
    c = _get("t_usher")
    if c: return c
    img = _load_tile_img("usher")
    if img: return _put("t_usher", img)
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(C_FLOOR)
    pygame.draw.rect(surf, (150, 50, 50), (4, 4, 40, 40), border_radius=4)
    pygame.draw.circle(surf, (255, 200, 100), (24, 24), 12)
    return _put("t_usher", surf)


def tile_security() -> pygame.Surface:
    c = _get("t_security")
    if c: return c
    surf = tile_floor().copy()
    pygame.draw.rect(surf, (60, 65, 75), (2, 6, TILE_SIZE-4, 34), border_radius=4)
    pygame.draw.rect(surf, (80, 85, 95), (6, 10, TILE_SIZE-12, 26), border_radius=3)
    pygame.draw.rect(surf, (20, 40, 30), (14, 14, 20, 16), border_radius=2)
    pygame.draw.circle(surf, (50, 200, 80), (12, 18), 2)
    pygame.draw.circle(surf, (200, 50, 50), (12, 24), 2)
    return _put("t_security", surf)


_POSTER_SLICES = [
    pygame.Rect(8, 11, 58, 74),
    pygame.Rect(72, 11, 55, 71),
    pygame.Rect(135, 11, 55, 73),
    pygame.Rect(206, 18, 42, 65),
]


def _load_poster_sprite(variant: int = 0) -> pygame.Surface | None:
    key = f"poster_sprite_{variant % len(_POSTER_SLICES)}"
    c = _get(key)
    if c is not None:
        return c
    path = os.path.join(TILES_DIR, "movie_posters.png")
    if os.path.exists(path):
        try:
            sheet = pygame.image.load(path).convert_alpha()
            rect = _POSTER_SLICES[variant % len(_POSTER_SLICES)]
            sub = sheet.subsurface(rect).copy()
            target_h = 44
            target_w = int(target_h * (sub.get_width() / sub.get_height()))
            scaled = pygame.transform.smoothscale(sub, (target_w, target_h))
            return _put(key, scaled)
        except Exception:
            pass
    return _put(key, None)


def tile_poster(variant: int = 0) -> pygame.Surface:
    key = f"t_poster_{variant}"
    c = _get(key)
    if c: return c
    sprite = _load_poster_sprite(variant)
    surf = tile_corridor().copy()
    if sprite:
        sx = (TILE_SIZE - sprite.get_width()) // 2
        sy = (TILE_SIZE - sprite.get_height()) // 2
        surf.blit(sprite, (sx, sy))
        return _put(key, surf)

    frame_c = (180, 150, 80)
    pygame.draw.rect(surf, frame_c, (6, 2, 36, 44), border_radius=2)
    pygame.draw.rect(surf, _darken(frame_c, 30), (6, 2, 36, 44), 2, border_radius=2)
    pygame.draw.rect(surf, (30, 20, 50), (10, 6, 28, 36))
    pygame.draw.circle(surf, (200, 60, 80), (24, 18), 8)
    pygame.draw.circle(surf, (240, 180, 60), (24, 18), 4)
    pygame.draw.line(surf, (200, 200, 200), (14, 32), (34, 32), 2)
    pygame.draw.line(surf, (160, 160, 160), (16, 36), (32, 36), 1)
    return _put(key, surf)


def tile_poster_for(col: int, row: int) -> pygame.Surface:
    variant = (col * 3 + row * 7) % len(_POSTER_SLICES)
    key = f"t_poster_pos_{col}_{row}"
    c = _get(key)
    if c: return c
    sprite = _load_poster_sprite(variant)
    base = tile_floor().copy() if row >= 18 else tile_corridor().copy()
    if sprite:
        sx = (TILE_SIZE - sprite.get_width()) // 2
        sy = (TILE_SIZE - sprite.get_height()) // 2
        base.blit(sprite, (sx, sy))
        return _put(key, base)
    return tile_poster(variant)



def tile_plant() -> pygame.Surface:
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(C_FLOOR)
    pygame.draw.rect(surf, (100, 70, 50), (14, 24, 20, 24))
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
    c = _get("t_corridor")
    if c: return c
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(C_CORRIDOR)
    for y in range(0, TILE_SIZE, 8):
        for x in range(0, TILE_SIZE, 8):
            if (x + y) % 16 == 0:
                pygame.draw.rect(surf, _lighten(C_CORRIDOR, 8), (x, y, 8, 8))
    pygame.draw.line(surf, (60, 40, 80), (0, 0), (0, TILE_SIZE))
    pygame.draw.line(surf, (60, 40, 80), (TILE_SIZE-1, 0), (TILE_SIZE-1, TILE_SIZE))
    return _put("t_corridor", surf)


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


def _gen_char(body_color, head_color=(235, 200, 170), frame=0, direction=0,
              accessory=None, hat_color=None):
    w, h = 16, 24
    s = _make(w, h)
    bob = -1 if frame in (1, 3) else 0
    leg_off = [-1, 0, 1, 0][frame % 4]

    pygame.draw.ellipse(s, (0, 0, 0, 50), (3, 20, 10, 4))
    pygame.draw.rect(s, _darken(body_color, 50), (5 - leg_off, 17 + bob, 3, 4))
    pygame.draw.rect(s, _darken(body_color, 50), (8 + leg_off, 17 + bob, 3, 4))
    pygame.draw.rect(s, (50, 40, 35), (5 - leg_off, 20 + bob, 3, 2))
    pygame.draw.rect(s, (50, 40, 35), (8 + leg_off, 20 + bob, 3, 2))
    pygame.draw.rect(s, body_color, (4, 11 + bob, 8, 7))
    pygame.draw.line(s, _darken(body_color, 25), (8, 12 + bob), (8, 17 + bob))
    if accessory:
        pygame.draw.rect(s, accessory, (5, 13 + bob, 6, 4))
    pygame.draw.rect(s, body_color, (2, 12 + bob, 2, 5))
    pygame.draw.rect(s, body_color, (12, 12 + bob, 2, 5))
    pygame.draw.rect(s, head_color, (2, 16 + bob, 2, 2))
    pygame.draw.rect(s, head_color, (12, 16 + bob, 2, 2))
    pygame.draw.rect(s, head_color, (4, 3 + bob, 8, 8))
    hair = _darken(head_color, 80)
    pygame.draw.rect(s, hair, (4, 2 + bob, 8, 2))
    if direction == 0:
        pygame.draw.rect(s, hair, (4, 3 + bob, 1, 3))
        pygame.draw.rect(s, hair, (11, 3 + bob, 1, 3))
        pygame.draw.rect(s, (40, 30, 30), (5, 6 + bob, 2, 2))
        pygame.draw.rect(s, (40, 30, 30), (9, 6 + bob, 2, 2))
        s.set_at((5, 6 + bob), (255, 255, 255))
        s.set_at((9, 6 + bob), (255, 255, 255))
        pygame.draw.line(s, (180, 100, 100), (6, 9 + bob), (9, 9 + bob))
    elif direction == 3:
        pygame.draw.rect(s, hair, (4, 3 + bob, 8, 4))
    elif direction == 1:
        pygame.draw.rect(s, (40, 30, 30), (4, 6 + bob, 2, 2))
        s.set_at((4, 6 + bob), (255, 255, 255))
    elif direction == 2:
        pygame.draw.rect(s, (40, 30, 30), (10, 6 + bob, 2, 2))
        s.set_at((11, 6 + bob), (255, 255, 255))
    if hat_color:
        pygame.draw.rect(s, hat_color, (3, 1 + bob, 10, 3))
        pygame.draw.rect(s, _darken(hat_color, 20), (2, 3 + bob, 12, 1))

    return pygame.transform.scale(s, (PLAYER_SPRITE_W * 2, PLAYER_SPRITE_H * 2))


def get_player_sheet():
    c = _get("player_sheet")
    if c is not None: return c
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

        if direction == 0:
            row = 0
            flip_x = False
        elif direction == 1:
            row = 1
            flip_x = False
        elif direction == 2:
            row = 1
            flip_x = True
        elif direction == 3:
            row = 3
            flip_x = False
        else:
            row = 0
            flip_x = False

        s = _make(fw, fh)
        s.blit(sheet, (0, 0), (frame * fw, row * fh, fw, fh))
        if flip_x:
            s = pygame.transform.flip(s, True, False)

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


_STAFF_CHARACTER_SPECS = {
    "cashier": ("Townspeople_Animations.png", 0),
    "usher":   ("MinersConstruction_Animations.png", 3),
    "server":  ("ForestNpcs_Animations.png", 1),
}


def _staff_character_sprite(role, frame=0, direction=0):
    key = f"staff_character_{role}_{frame % 3}_{direction}"
    cached = _get(key)
    if cached is not None:
        return cached

    filename, character_index = _STAFF_CHARACTER_SPECS[role]
    path = os.path.join(SPRITES_DIR, filename)
    if not os.path.exists(path):
        return False
    sheet = pygame.image.load(path).convert_alpha()
    row_group, col_group = divmod(character_index, 4)
    source = pygame.Rect(
        col_group * 3 * 18 + (frame % 3) * 18,
        row_group * 4 * 26 + direction * 26,
        18, 26,
    )
    cropped = pygame.Surface(source.size, pygame.SRCALPHA)
    cropped.blit(sheet, (0, 0), source)
    return _put(key, pygame.transform.scale(cropped, (42, 58)))


def cashier_sprite(frame=0, direction=0):
    key = f"cashier_{frame}_{direction}"
    c = _get(key)
    if c: return c
    sprite = _staff_character_sprite("cashier", frame, direction)
    return _put(key, sprite or _gen_char(C_CASHIER_VEST, frame=frame, direction=direction))


def usher_sprite(frame=0, direction=0):
    key = f"usher_{frame}_{direction}"
    c = _get(key)
    if c: return c
    sprite = _staff_character_sprite("usher", frame, direction)
    return _put(key, sprite or _gen_char(C_USHER_JACKET, hat_color=(60, 20, 25),
                                          frame=frame, direction=direction))


def server_sprite(frame=0, direction=0):
    key = f"server_{frame}_{direction}"
    c = _get(key)
    if c: return c
    sprite = _staff_character_sprite("server", frame, direction)
    return _put(key, sprite or _gen_char((60, 60, 120), accessory=C_SERVER_APRON,
                                          frame=frame, direction=direction))


def _gen_bubble(icon_fn, bg=(255, 255, 255, 220)):
    s = _make(28, 32)
    pygame.draw.rect(s, bg, (1, 1, 26, 24), border_radius=5)
    pygame.draw.rect(s, (120, 120, 120), (1, 1, 26, 24), 1, border_radius=5)
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


def _gen_bubble(icon_fn, bg=(255, 255, 255, 220)):
    s = _make(28, 32)
    pygame.draw.rect(s, bg, (1, 1, 26, 24), border_radius=5)
    pygame.draw.rect(s, (120, 120, 120), (1, 1, 26, 24), 1, border_radius=5)
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
        pygame.draw.arc(s, (200, 160, 60), (9, 5, 10, 10), 0, 4.0, 2)
        pygame.draw.rect(s, (200, 160, 60), (13, 14, 2, 3))
        pygame.draw.rect(s, (200, 160, 60), (13, 19, 2, 2))
    return _put("bub_food", _gen_bubble(icon))


def bubble_speech(text, font):
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


def menu_background_frames():
    c = _get("menu_bg_frames")
    if c:
        return c
    path_gif = os.path.join(BG_DIR, "main_menu.gif")
    path_jpg = os.path.join(BG_DIR, "main_menu.jpg")
    frames = []
    if os.path.exists(path_gif):
        try:
            anim = pygame.image.load_animation(path_gif)
            for surf, dur in anim:
                s = surf.convert()
                if s.get_size() != (SCREEN_W, SCREEN_H):
                    s = pygame.transform.scale(s, (SCREEN_W, SCREEN_H))
                frames.append((s, dur / 1000.0 if dur > 0 else 0.17))
        except Exception:
            pass
    if not frames and os.path.exists(path_jpg):
        img = pygame.image.load(path_jpg).convert()
        img = pygame.transform.scale(img, (SCREEN_W, SCREEN_H))
        frames.append((img, 1.0))
    if not frames:
        s = pygame.Surface((SCREEN_W, SCREEN_H))
        s.fill(C_BG_DARK)
        frames.append((s, 1.0))
    return _put("menu_bg_frames", frames)


def menu_background(anim_t: float = 0.0):
    frames = menu_background_frames()
    if len(frames) == 1:
        return frames[0][0]
    total_dur = sum(dur for _, dur in frames)
    if total_dur <= 0:
        return frames[0][0]
    t = anim_t % total_dur
    acc = 0.0
    for surf, dur in frames:
        acc += dur
        if t < acc:
            return surf
    return frames[-1][0]


def menu_title_logo() -> pygame.Surface | None:
    c = _get("menu_title_logo")
    if c is not None:
        return c
    for fname in ("text.png", "text.jpg", "logo.png", "title.png"):
        path = os.path.join(UI_DIR, fname)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                bbox = img.get_bounding_rect()
                if bbox.width > 0 and bbox.height > 0:
                    cropped = img.subsurface(bbox).copy()
                else:
                    cropped = img
                target_w = 460
                target_h = int(target_w * (cropped.get_height() / cropped.get_width()))
                scaled = pygame.transform.smoothscale(cropped, (target_w, target_h))
                return _put("menu_title_logo", scaled)
            except Exception:
                pass
    return _put("menu_title_logo", None)


def clear_cache():
    _cache.clear()

