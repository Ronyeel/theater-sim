"""
CinePlex Dreams — Cinema Exterior Cutscene
Cinematic transition screen: moviegoers walking into the cinema entrance under
the glowing retro marquee before fading smoothly into the theater simulation.
"""
import os
import pygame
import math
import random
from game.settings import (
    SCREEN_W, SCREEN_H, C_BG_DARK, C_NEON_GOLD, C_NEON_CYAN, C_NEON_PINK,
    C_TEXT_WHITE, C_TEXT_DIM, BG_DIR,
)
from game.core import asset_loader as AL
from game.core.particles import ParticleSystem
from game.entities.npc import moviegoer_sprite
from game.entities.player import DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIR_UP


def _font(name, size, bold=False):
    try:    return pygame.font.SysFont(name, size, bold=bold)
    except: return pygame.font.Font(None, size)


class ExteriorScreen:
    """Cinematic exterior cutscene showing guests entering the cinema."""

    def __init__(self, go_interior):
        self.go_interior = go_interior
        self._t = 0.0
        self.duration = 3.2  # Total cutscene duration in seconds

        # Load & prepare cinema exterior background
        ext_path = os.path.join(BG_DIR, "outside cinema.png")
        if os.path.exists(ext_path):
            raw = pygame.image.load(ext_path).convert()
            raw_w, raw_h = raw.get_size()
            self._scale = SCREEN_H / raw_h
            self._bg_w = int(raw_w * self._scale)
            self._bg_h = SCREEN_H
            self._bg = pygame.transform.smoothscale(raw, (self._bg_w, self._bg_h))
            self._offset_x = (SCREEN_W - self._bg_w) // 2
        else:
            self._bg = pygame.Surface((SCREEN_W, SCREEN_H))
            self._bg.fill((30, 25, 45))
            self._scale = 1.0
            self._bg_w = SCREEN_W
            self._bg_h = SCREEN_H
            self._offset_x = 0

        # Entrance door coordinates
        self.door_x = self._offset_x + self._bg_w * 0.50
        self.door_y = self._bg_h * 0.70

        # Particles & Fonts
        self.particles = ParticleSystem()
        self._hint_font = _font("consolas", 12)

        # Transition state
        self._entering = False
        self._fade_alpha = 0.0
        self._fade_surf = pygame.Surface((SCREEN_W, SCREEN_H))
        self._fade_surf.fill((0, 0, 0))

        # Animated cinematic pedestrians entering the cinema
        self._pedestrians = [
            # Group walking up into the front doors
            self._make_cinematic_guest(0.50, 0.90, target_door=True, speed=38, character_id=6, delay=0.0),
            self._make_cinematic_guest(0.46, 0.94, target_door=True, speed=34, character_id=14, delay=0.4),
            self._make_cinematic_guest(0.54, 0.96, target_door=True, speed=36, character_id=22, delay=0.7),
            self._make_cinematic_guest(0.48, 0.98, target_door=True, speed=32, character_id=38, delay=1.1),
            # Sidewalk pedestrians strolling across
            self._make_cinematic_guest(0.18, 0.77, target_door=False, direction=DIR_RIGHT, speed=26, character_id=2),
            self._make_cinematic_guest(0.82, 0.78, target_door=False, direction=DIR_LEFT, speed=24, character_id=19),
            self._make_cinematic_guest(0.30, 0.86, target_door=False, direction=DIR_RIGHT, speed=20, character_id=34),
            self._make_cinematic_guest(0.72, 0.88, target_door=False, direction=DIR_LEFT, speed=22, character_id=45),
        ]

    def _make_cinematic_guest(self, x_ratio, y_ratio, target_door=False, direction=DIR_UP, speed=30, character_id=0, delay=0.0):
        return {
            "x": self._offset_x + self._bg_w * x_ratio,
            "y": self._bg_h * y_ratio,
            "target_door": target_door,
            "dir": direction,
            "spd": speed,
            "fr": 0,
            "anim": 0.0,
            "delay": delay,
            "entered": False,
            "character_id": character_id,
        }

    def _update_pedestrians(self, dt):
        for ped in self._pedestrians:
            if ped["delay"] > 0:
                ped["delay"] -= dt
                continue

            if ped["entered"]:
                continue

            if ped["target_door"]:
                # Walk UP toward center doors
                target_x = self.door_x
                target_y = self.door_y
                dx = target_x - ped["x"]
                dy = target_y - ped["y"]
                dist = math.hypot(dx, dy)

                if dist < 12:
                    ped["entered"] = True
                    self.particles.burst(self.door_x, self.door_y - 20, C_NEON_GOLD, count=14, speed=90)
                else:
                    ped["x"] += (dx / dist) * ped["spd"] * dt
                    ped["y"] += (dy / dist) * ped["spd"] * dt
                    ped["dir"] = DIR_UP
                    ped["anim"] += dt
                    if ped["anim"] >= 0.14:
                        ped["anim"] = 0.0
                        ped["fr"] = (ped["fr"] + 1) % 4
            else:
                # Stroll sideways
                left_edge = self._offset_x + self._bg_w * 0.16
                right_edge = self._offset_x + self._bg_w * 0.84
                ped["x"] += (ped["spd"] if ped["dir"] == DIR_RIGHT else -ped["spd"]) * dt
                ped["anim"] += dt
                if ped["anim"] >= 0.16:
                    ped["anim"] = 0.0
                    ped["fr"] = (ped["fr"] + 1) % 4

                if ped["x"] <= left_edge:
                    ped["dir"] = DIR_RIGHT
                elif ped["x"] >= right_edge:
                    ped["dir"] = DIR_LEFT

    def handle_event(self, evt):
        # Allow skipping cutscene on any key or click
        if evt.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self._start_enter()

    def _start_enter(self):
        self._entering = True

    def update(self, dt: float):
        self._t += dt
        self.particles.update(dt)
        self._update_pedestrians(dt)

        # Automatic transition after cutscene duration
        if self._t >= (self.duration - 0.8) or self._entering:
            self._fade_alpha = min(255.0, self._fade_alpha + 360 * dt)
            if self._fade_alpha >= 255.0:
                self.go_interior()

    def draw(self, surface: pygame.Surface):
        # Fill black / dark backdrop
        surface.fill(C_BG_DARK)

        # Draw decorative glowing pillars on widescreen sides
        for x_pillar in (0, self._offset_x + self._bg_w):
            w_pillar = (SCREEN_W - self._bg_w) // 2 + 2
            pygame.draw.rect(surface, (18, 12, 32), (x_pillar, 0, w_pillar, SCREEN_H))
            line_x = self._offset_x if x_pillar == 0 else self._offset_x + self._bg_w
            pygame.draw.line(surface, C_NEON_GOLD, (line_x, 0), (line_x, SCREEN_H), 2)

        # Draw Cinema Exterior Background
        surface.blit(self._bg, (self._offset_x, 0))

        # Marquee animated glow
        flicker = 0.8 + 0.2 * math.sin(self._t * 5.0)
        glow_rect = pygame.Rect(
            int(self._offset_x + self._bg_w * 0.26),
            int(self._bg_h * 0.46),
            int(self._bg_w * 0.48),
            int(self._bg_h * 0.14)
        )
        glow = pygame.Surface((glow_rect.w, glow_rect.h), pygame.SRCALPHA)
        glow.fill((*C_NEON_GOLD[:3], int(28 * flicker)))
        surface.blit(glow, glow_rect.topleft)

        # Draw Door Entrance Pulse
        pulse_r = int(18 + 6 * math.sin(self._t * 3.5))
        door_pulse = pygame.Surface((pulse_r * 2, pulse_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(door_pulse, (*C_NEON_GOLD[:3], 90), (pulse_r, pulse_r), pulse_r, 2)
        surface.blit(door_pulse, (int(self.door_x - pulse_r), int(self.door_y - pulse_r)))

        # Draw walking pedestrians (sorted by Y for natural depth)
        for ped in sorted(self._pedestrians, key=lambda item: item["y"]):
            if ped["delay"] > 0 or ped["entered"]:
                continue
            npc_s = moviegoer_sprite(ped["character_id"], ped["fr"], ped["dir"])
            shadow = pygame.Surface((22, 7), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 75), shadow.get_rect())
            surface.blit(shadow, (int(ped["x"]) - 11, int(ped["y"]) - 4))
            surface.blit(npc_s, (int(ped["x"]) - npc_s.get_width() // 2, int(ped["y"]) - npc_s.get_height()))

        # Particles
        class ScreenCam:
            def world_to_screen(self, x, y): return x, y
        self.particles.draw(surface, ScreenCam())

        # Subtle Skip Hint (bottom-right)
        hint_alpha = int(140 + 60 * math.sin(self._t * 2.0))
        hint = self._hint_font.render("[Press Any Key / Click to Skip]", True, (190, 190, 220))
        hint.set_alpha(hint_alpha)
        surface.blit(hint, (SCREEN_W - hint.get_width() - 16, SCREEN_H - 24))

        # Smooth Fade Out Overlay
        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(int(self._fade_alpha))
            surface.blit(self._fade_surf, (0, 0))
