"""
CinePlex Dreams — NPC Entities
Ambient townspeople that wander around the cinema lobby, making the world feel alive.
Uses the Townspeople_Animations.png spritesheet from assets/sprites/.
"""
import os
import pygame
import random
import math
from game.settings import (
    TILE_SIZE, SPRITES_DIR,
    PLAYER_SPRITE_W, PLAYER_SPRITE_H,
)
from game.core.tilemap import is_walkable

# ── Spritesheet constants ──────────────────────────────────────────────────
# Townspeople_Animations.png: 216×416, 12 cols × 16 rows, 18×26px per frame
# Each character: 3 animation frames (walk cycle), 4 directions (D, L, R, U)
# So one character = 3 cols × 4 rows = 12 frames
# 4 characters per row-group, 4 row-groups => 16 characters total
_FRAME_W = 18
_FRAME_H = 26
_ANIM_FRAMES = 3       # walk frames per direction
_DIR_DOWN  = 0
_DIR_LEFT  = 1
_DIR_RIGHT = 2
_DIR_UP    = 3

# Character indices (0-15) in row-major order:
# Row-group 0: chars 0-3    (rows 0-3)
# Row-group 1: chars 4-7    (rows 4-7)
# Row-group 2: chars 8-11   (rows 8-11)
# Row-group 3: chars 12-15  (rows 12-15)

_npc_sheet: pygame.Surface | None = None
_npc_frame_cache: dict[str, pygame.Surface] = {}

# Scale target for NPC sprites (match player roughly)
_NPC_DRAW_W = 42
_NPC_DRAW_H = 58


def _load_npc_sheet() -> pygame.Surface | None:
    global _npc_sheet
    if _npc_sheet is not None:
        return _npc_sheet
    path = os.path.join(SPRITES_DIR, "Townspeople_Animations.png")
    if os.path.exists(path):
        _npc_sheet = pygame.image.load(path).convert_alpha()
        return _npc_sheet
    return None


def _get_npc_frame(char_idx: int, direction: int, frame: int) -> pygame.Surface:
    """Extract a single animation frame for a character from the spritesheet."""
    key = f"npc_{char_idx}_{direction}_{frame}"
    if key in _npc_frame_cache:
        return _npc_frame_cache[key]

    sheet = _load_npc_sheet()
    if sheet is None:
        # Fallback: colored rectangle
        s = pygame.Surface((_NPC_DRAW_W, _NPC_DRAW_H), pygame.SRCALPHA)
        pygame.draw.rect(s, (200, 100, 100), (4, 4, _NPC_DRAW_W-8, _NPC_DRAW_H-8), border_radius=6)
        _npc_frame_cache[key] = s
        return s

    # Character position in the grid
    row_group = char_idx // 4    # which group of 4 rows (0-3)
    col_group = char_idx % 4     # which character within that group (0-3)

    # Source rect in sheet
    sx = col_group * _ANIM_FRAMES * _FRAME_W + frame * _FRAME_W
    sy = row_group * 4 * _FRAME_H + direction * _FRAME_H

    s = pygame.Surface((_FRAME_W, _FRAME_H), pygame.SRCALPHA)
    s.blit(sheet, (0, 0), (sx, sy, _FRAME_W, _FRAME_H))

    # Scale up
    s = pygame.transform.scale(s, (_NPC_DRAW_W, _NPC_DRAW_H))
    _npc_frame_cache[key] = s
    return s


# ── NPC Character Names & Personality ─────────────────────────────────────

_NPC_NAMES = [
    "Alex", "Sam", "Jordan", "Casey", "Riley",
    "Morgan", "Avery", "Quinn", "Blake", "Drew",
    "Taylor", "Reese", "Harper", "Skyler", "Finley",
    "Logan",
]

_NPC_IDLE_LINES = [
    "The movie starts soon!",
    "I love this place.",
    "Popcorn smells amazing!",
    "Which movie should I see?",
    "I heard this film is great!",
    "Where's my ticket...",
    "Need more snacks!",
    "Let's find our seats!",
    "This carpet is so plush!",
    "What a cool cinema!",
]


class NPC:
    """An ambient NPC that wanders the cinema lobby."""

    # Movement states
    IDLE     = 0
    WALKING  = 1

    # Walkable rows for NPC wandering (lobby area only: rows 11-22)
    WANDER_ROW_MIN = 11
    WANDER_ROW_MAX = 22
    WANDER_COL_MIN = 1
    WANDER_COL_MAX = 18

    def __init__(self, char_idx: int, start_col: int, start_row: int, name: str = ""):
        self.char_idx = char_idx
        self.name = name or _NPC_NAMES[char_idx % len(_NPC_NAMES)]

        # World position
        self.x = float(start_col * TILE_SIZE + TILE_SIZE // 2)
        self.y = float(start_row * TILE_SIZE + TILE_SIZE // 2)

        # Movement
        self.state = self.IDLE
        self.direction = _DIR_DOWN
        self.speed = random.uniform(40, 65)  # slower than player
        self._target_x = self.x
        self._target_y = self.y

        # Animation
        self._anim_t = random.uniform(0, 3)  # offset so NPCs don't sync
        self._frame = 0

        # Idle timer (seconds until next wander)
        self._idle_timer = random.uniform(1.5, 4.0)

        # Speech bubble
        self._speech_text = ""
        self._speech_timer = 0.0
        self._speech_cooldown = random.uniform(8.0, 20.0)
        try:
            self._font = pygame.font.SysFont("consolas", 11)
        except Exception:
            self._font = pygame.font.Font(None, 11)

    def _pick_wander_target(self):
        """Choose a random walkable tile in the lobby to walk toward."""
        for _ in range(30):  # try up to 30 times
            col = random.randint(self.WANDER_COL_MIN, self.WANDER_COL_MAX)
            row = random.randint(self.WANDER_ROW_MIN, self.WANDER_ROW_MAX)
            if is_walkable(col, row):
                self._target_x = float(col * TILE_SIZE + TILE_SIZE // 2)
                self._target_y = float(row * TILE_SIZE + TILE_SIZE // 2)
                self.state = self.WALKING
                return
        # If no valid target found, stay idle
        self._idle_timer = random.uniform(2.0, 5.0)

    def update(self, dt: float):
        self._anim_t += dt

        # Speech cooldown
        self._speech_cooldown -= dt
        if self._speech_cooldown <= 0 and self._speech_timer <= 0:
            if random.random() < 0.3:
                self._speech_text = random.choice(_NPC_IDLE_LINES)
                self._speech_timer = 3.0
            self._speech_cooldown = random.uniform(10.0, 25.0)

        if self._speech_timer > 0:
            self._speech_timer -= dt
            if self._speech_timer <= 0:
                self._speech_text = ""

        if self.state == self.IDLE:
            self._frame = 0  # standing still
            self._idle_timer -= dt
            if self._idle_timer <= 0:
                self._pick_wander_target()

        elif self.state == self.WALKING:
            # Move toward target
            dx = self._target_x - self.x
            dy = self._target_y - self.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 4:
                # Arrived
                self.state = self.IDLE
                self._idle_timer = random.uniform(2.0, 6.0)
                self._frame = 0
            else:
                # Determine direction
                if abs(dx) > abs(dy):
                    self.direction = _DIR_RIGHT if dx > 0 else _DIR_LEFT
                else:
                    self.direction = _DIR_DOWN if dy > 0 else _DIR_UP

                # Move
                step = min(dist, self.speed * dt)
                self.x += (dx / dist) * step
                self.y += (dy / dist) * step

                # Animate walk cycle
                self._frame = int(self._anim_t / 0.2) % _ANIM_FRAMES

                # Collision check: if current tile not walkable, stop
                cur_col = int(self.x // TILE_SIZE)
                cur_row = int(self.y // TILE_SIZE)
                if not is_walkable(cur_col, cur_row):
                    # Revert and pick new target
                    self.x -= (dx / dist) * step
                    self.y -= (dy / dist) * step
                    self.state = self.IDLE
                    self._idle_timer = random.uniform(1.0, 3.0)

    def draw(self, surface: pygame.Surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)

        # Get sprite frame
        sprite = _get_npc_frame(self.char_idx, self.direction, self._frame)
        sw, sh = sprite.get_size()

        # Draw shadow
        shadow = pygame.Surface((sw - 8, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 40), shadow.get_rect())
        surface.blit(shadow, (int(sx) - sw // 2 + 4, int(sy) - 2))

        # Draw sprite
        surface.blit(sprite, (int(sx) - sw // 2, int(sy) - sh + 4))

        # Draw speech bubble if speaking
        if self._speech_text and self._speech_timer > 0:
            alpha = min(255, int(255 * min(1.0, self._speech_timer / 0.5)))
            text_surf = self._font.render(self._speech_text, True, (50, 40, 60))
            tw, th = text_surf.get_size()
            bw = tw + 10
            bh = th + 8

            bubble = pygame.Surface((bw, bh + 4), pygame.SRCALPHA)
            pygame.draw.rect(bubble, (255, 255, 255, 220), (0, 0, bw, bh), border_radius=4)
            pygame.draw.rect(bubble, (150, 140, 160), (0, 0, bw, bh), 1, border_radius=4)
            # Tail
            pygame.draw.polygon(bubble, (255, 255, 255, 220),
                                [(bw // 2 - 3, bh), (bw // 2 + 3, bh), (bw // 2, bh + 4)])
            bubble.blit(text_surf, (5, 4))
            bubble.set_alpha(alpha)

            bx = int(sx) - bw // 2
            by = int(sy) - sh - bh - 6
            surface.blit(bubble, (bx, by))


def build_npcs(count: int = 5) -> list[NPC]:
    """Create a list of ambient NPCs placed randomly in the lobby."""
    npcs = []
    # Pick unique character indices from the spritesheet (0-15)
    char_indices = random.sample(range(16), min(count, 16))

    # Spawn positions — spread across lobby walkable areas
    spawn_spots = [
        (5,  20),   # left lobby
        (14, 20),   # right lobby
        (10, 19),   # center lobby
        (3,  12),   # left snack area
        (16, 12),   # right snack area
        (8,  15),   # post-cashier walkway left
        (12, 16),   # post-cashier walkway right
        (6,  22),   # near entrance left
        (13, 22),   # near entrance right
        (10, 11),   # snack queue center
    ]
    random.shuffle(spawn_spots)

    for i, char_idx in enumerate(char_indices):
        col, row = spawn_spots[i % len(spawn_spots)]
        name = _NPC_NAMES[char_idx % len(_NPC_NAMES)]
        npc = NPC(char_idx, col, row, name)
        npcs.append(npc)

    return npcs
