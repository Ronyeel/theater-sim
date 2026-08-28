"""
Theater Ambiance and Dynamic Lighting System.
Provides realistic cinema lighting, projector beam volumetrics,
warm architectural sconces, illuminated movie posters, step lights,
and floating atmospheric dust motes.
"""

import math
import random
import pygame
from game.settings import (
    TILE_SIZE, MAP_COLS, MAP_ROWS, SCREEN_W, SCREEN_H,
    C_NEON_PINK, C_NEON_CYAN, C_NEON_GOLD,
    CASHIER_DESK_COLS, CASHIER_DESK_ROW,
    USHER_DESK_COLS, USHER_DESK_ROW,
    SNACK_DESK_COLS, SNACK_DESK_ROW,
)


def _make_radial_light(radius: int, color: tuple[int, int, int], intensity: float = 1.0) -> pygame.Surface:
    """Pre-renders a soft, smooth radial light gradient."""
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    r, g, b = color[:3]
    for dist in range(radius, 0, -2):
        factor = (1.0 - (dist / radius)) ** 1.8
        alpha = int(255 * factor * intensity)
        if alpha <= 0:
            continue
        pygame.draw.circle(surf, (r, g, b, min(255, alpha)), (radius, radius), dist)
    return surf


def _make_elliptical_light(width: int, height: int, color: tuple[int, int, int], intensity: float = 1.0) -> pygame.Surface:
    """Pre-renders a soft elliptical light gradient."""
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    r, g, b = color[:3]
    steps = 20
    for i in range(steps):
        factor = (1.0 - (i / steps)) ** 1.6
        alpha = int(255 * factor * intensity)
        if alpha <= 0:
            continue
        ew = int(width * (1.0 - i / steps))
        eh = int(height * (1.0 - i / steps))
        ex = (width - ew) // 2
        ey = (height - eh) // 2
        pygame.draw.ellipse(surf, (r, g, b, min(255, alpha)), (ex, ey, ew, eh))
    return surf


class DustMote:
    __slots__ = ('x', 'y', 'vx', 'vy', 'size', 'alpha', 'phase', 'speed')

    def __init__(self, x_range: tuple[float, float], y_range: tuple[float, float]):
        self.x = random.uniform(x_range[0], x_range[1])
        self.y = random.uniform(y_range[0], y_range[1])
        self.vx = random.uniform(-6, 6)
        self.vy = random.uniform(2, 8)
        self.size = random.uniform(1.0, 2.5)
        self.alpha = random.uniform(80, 200)
        self.phase = random.uniform(0, math.pi * 2)
        self.speed = random.uniform(1.5, 3.5)

    def update(self, dt: float, x_range: tuple[float, float], y_range: tuple[float, float]):
        self.phase += dt * self.speed
        self.x += (self.vx + math.sin(self.phase) * 4) * dt
        self.y += self.vy * dt
        if self.x < x_range[0] or self.x > x_range[1]:
            self.x = random.uniform(x_range[0], x_range[1])
        if self.y > y_range[1]:
            self.y = y_range[0]
            self.x = random.uniform(x_range[0], x_range[1])


class LightingSystem:
    """Manages all cinema atmosphere, volumetric projector beams, and interior lights."""

    def __init__(self):
        self._t = 0.0
        self._screen_palette_idx = 0
        self._screen_palette_t = 0.0


        self._screen_palettes = [

            {"primary": (90, 210, 255), "glow": (60, 160, 255), "intensity": 0.85},

            {"primary": (255, 190, 90), "glow": (255, 140, 50), "intensity": 0.80},

            {"primary": (130, 220, 255), "glow": (255, 120, 70), "intensity": 0.90},

            {"primary": (90, 255, 180), "glow": (50, 200, 140), "intensity": 0.75},

            {"primary": (180, 120, 255), "glow": (120, 70, 240), "intensity": 0.80},
        ]


        self._light_small = _make_radial_light(36, (255, 220, 150), 0.6)
        self._light_medium = _make_radial_light(70, (255, 230, 180), 0.55)
        self._light_large = _make_radial_light(120, (255, 235, 200), 0.5)
        self._light_snack = _make_radial_light(85, (255, 200, 100), 0.65)
        self._light_step = _make_radial_light(18, (255, 205, 110), 0.75)
        self._light_poster = _make_elliptical_light(64, 80, (255, 240, 210), 0.6)
        self._light_neon_pink = _make_radial_light(90, C_NEON_PINK, 0.5)
        self._light_neon_cyan = _make_radial_light(90, C_NEON_CYAN, 0.5)
        self._light_exit = _make_radial_light(45, (100, 255, 140), 0.6)


        self._beam_w = 14 * TILE_SIZE
        self._beam_h = 6 * TILE_SIZE
        self._projector_beam = pygame.Surface((self._beam_w + 140, self._beam_h + 50), pygame.SRCALPHA)
        self._update_projector_beam((120, 200, 255))


        mote_x = (3.5 * TILE_SIZE, 16.5 * TILE_SIZE)
        mote_y = (1.5 * TILE_SIZE, 6.5 * TILE_SIZE)
        self._motes = [DustMote(mote_x, mote_y) for _ in range(28)]
        self._mote_x_range = mote_x
        self._mote_y_range = mote_y


        self._screen_bloom = pygame.Surface((15 * TILE_SIZE, 6 * TILE_SIZE), pygame.SRCALPHA)


        self._vignette_surf = None
        self._create_vignette()

    def _create_vignette(self):
        self._vignette_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        steps = 18
        for i in range(steps):
            factor = (1.0 - i / steps) ** 1.8
            alpha = int(22 * factor)
            rect = pygame.Rect(i * 6, i * 5, SCREEN_W - i * 12, SCREEN_H - i * 10)
            layer = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.rect(layer, (4, 2, 10, alpha), (0, 0, SCREEN_W, SCREEN_H))
            pygame.draw.rect(layer, (0, 0, 0, 0), rect, border_radius=22)
            self._vignette_surf.blit(layer, (0, 0))

    def _update_projector_beam(self, color: tuple[int, int, int]):
        self._projector_beam.fill((0, 0, 0, 0))
        r, g, b = color[:3]



        cone_poly = [
            (self._beam_w // 2 + 70, self._beam_h + 20),
            (25, 8),
            (self._beam_w + 115, 8),
        ]
        pygame.draw.polygon(self._projector_beam, (r, g, b, 24), cone_poly)


        pygame.draw.polygon(self._projector_beam, (min(255, r + 40), min(255, g + 40), min(255, b + 40), 20), [
            (self._beam_w // 2 + 70, self._beam_h + 20),
            (self._beam_w // 2 - 160 + 70, 8),
            (self._beam_w // 2 + 160 + 70, 8),
        ])


        pygame.draw.polygon(self._projector_beam, (255, 255, 255, 16), [
            (self._beam_w // 2 + 70, self._beam_h + 20),
            (self._beam_w // 2 - 80 + 70, 8),
            (self._beam_w // 2 + 80 + 70, 8),
        ])

    def update(self, dt: float):
        self._t += dt
        self._screen_palette_t += dt


        if self._screen_palette_t > 9.0:
            self._screen_palette_t = 0.0
            self._screen_palette_idx = (self._screen_palette_idx + 1) % len(self._screen_palettes)
            palette = self._screen_palettes[self._screen_palette_idx]
            self._update_projector_beam(palette["primary"])


        for mote in self._motes:
            mote.update(dt, self._mote_x_range, self._mote_y_range)

    def draw_world_lighting(self, surface: pygame.Surface, camera):
        """Renders the ambient lighting and projector beam strictly inside the cinema screening room."""
        view_w, view_h = surface.get_size()
        cam_x, cam_y = int(camera.x), int(camera.y)


        lightmap = pygame.Surface((view_w, view_h), pygame.SRCALPHA)


        auditorium_rect = pygame.Rect(
            0 - cam_x,
            0 - cam_y,
            MAP_COLS * TILE_SIZE,
            7 * TILE_SIZE + 24
        )
        clipped_auditorium = auditorium_rect.clip(pygame.Rect(0, 0, view_w, view_h))
        if clipped_auditorium.width <= 0 or clipped_auditorium.height <= 0:

            return

        lightmap.fill((8, 6, 20, 95), clipped_auditorium)


        cur_palette = self._screen_palettes[self._screen_palette_idx]
        flicker = 0.85 + 0.12 * math.sin(self._t * 4.2) + 0.05 * math.sin(self._t * 11.5) + 0.03 * random.uniform(-0.1, 0.1)
        flicker *= cur_palette["intensity"]


        self._screen_bloom.fill((0, 0, 0, 0))
        br, bg, bb = cur_palette["glow"]
        for r in range(4):
            bloom_alpha = int(18 * (1.0 - r / 4.0) * flicker)
            ew = self._screen_bloom.get_width() - r * 56
            eh = self._screen_bloom.get_height() - r * 32
            pygame.draw.ellipse(self._screen_bloom, (br, bg, bb, bloom_alpha), (r * 28, r * 16, ew, eh))

        bloom_x = 2.5 * TILE_SIZE - cam_x
        bloom_y = 0.5 * TILE_SIZE - cam_y
        lightmap.blit(self._screen_bloom, (bloom_x, bloom_y))


        beam_x = 3 * TILE_SIZE - 70 - cam_x
        beam_y = 1 * TILE_SIZE - 8 - cam_y
        beam = self._projector_beam.copy()
        beam.set_alpha(int(255 * flicker))
        lightmap.blit(beam, (beam_x, beam_y))


        for mote in self._motes:
            sx = mote.x - cam_x
            sy = mote.y - cam_y
            if 0 <= sx <= view_w and 0 <= sy <= (7 * TILE_SIZE + 24 - cam_y):
                mote_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
                ma = int(mote.alpha * flicker)
                pygame.draw.circle(mote_surf, (240, 248, 255, min(255, ma)), (2, 2), int(mote.size))
                lightmap.blit(mote_surf, (int(sx) - 2, int(sy) - 2))


        surface.blit(lightmap, (0, 0))

    def draw_vignette(self, screen_surface: pygame.Surface):
        """Draws the smooth screen vignette over the final rendered frame."""
        if self._vignette_surf is not None:
            screen_surface.blit(self._vignette_surf, (0, 0))
