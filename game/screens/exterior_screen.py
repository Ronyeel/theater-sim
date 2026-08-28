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

    def __init__(self, go_interior):
        self.go_interior = go_interior
        self._t = 0.0
        self.duration = 3.2

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

        self.door_x = self._offset_x + self._bg_w * 0.50
        self.door_y = self._bg_h * 0.70

        self.particles = ParticleSystem()
        self._hint_font = _font("consolas", 12)

        self._entering = False
        self._fade_alpha = 0.0
        self._fade_surf = pygame.Surface((SCREEN_W, SCREEN_H))
        self._fade_surf.fill((0, 0, 0))

        _rng = random.Random()

        used_char_ids: set = set()
        self._pedestrians = []

        def _pick_char():
            cid = _rng.randint(0, 63)
            while cid in used_char_ids:
                cid = _rng.randint(0, 63)
            used_char_ids.add(cid)
            return cid

        num_door = _rng.randint(2, 9)
        cumulative_delay = _rng.uniform(0.0, 0.4)
        for _ in range(num_door):
            self._pedestrians.append(
                self._make_cinematic_guest(
                    _rng.uniform(0.43, 0.57),
                    _rng.uniform(0.86, 1.00),
                    target_door=True,
                    speed=_rng.uniform(22, 55),
                    character_id=_pick_char(),
                    delay=cumulative_delay,
                )
            )
            cumulative_delay += _rng.uniform(0.08, 0.65)

        num_stroll = _rng.randint(1, 7)
        for _ in range(num_stroll):
            from_right = _rng.random() < 0.5
            self._pedestrians.append(
                self._make_cinematic_guest(
                    _rng.uniform(0.76, 0.95) if from_right else _rng.uniform(0.05, 0.24),
                    _rng.uniform(0.72, 0.91),
                    target_door=False,
                    direction=DIR_LEFT if from_right else DIR_RIGHT,
                    speed=_rng.uniform(14, 38),
                    character_id=_pick_char(),
                    delay=_rng.uniform(0.0, 1.8),
                )
            )

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
                dx = self.door_x - ped["x"]
                dy = self.door_y - ped["y"]
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
        if evt.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self._start_enter()

    def _start_enter(self):
        self._entering = True

    def update(self, dt: float):
        self._t += dt
        self.particles.update(dt)
        self._update_pedestrians(dt)

        if self._t >= (self.duration - 0.8) or self._entering:
            self._fade_alpha = min(255.0, self._fade_alpha + 360 * dt)
            if self._fade_alpha >= 255.0:
                self.go_interior()

    def draw(self, surface: pygame.Surface):
        surface.fill(C_BG_DARK)

        for x_pillar in (0, self._offset_x + self._bg_w):
            w_pillar = (SCREEN_W - self._bg_w) // 2 + 2
            pygame.draw.rect(surface, (18, 12, 32), (x_pillar, 0, w_pillar, SCREEN_H))
            line_x = self._offset_x if x_pillar == 0 else self._offset_x + self._bg_w
            pygame.draw.line(surface, C_NEON_GOLD, (line_x, 0), (line_x, SCREEN_H), 2)

        surface.blit(self._bg, (self._offset_x, 0))

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

        pulse_r = int(18 + 6 * math.sin(self._t * 3.5))
        door_pulse = pygame.Surface((pulse_r * 2, pulse_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(door_pulse, (*C_NEON_GOLD[:3], 90), (pulse_r, pulse_r), pulse_r, 2)
        surface.blit(door_pulse, (int(self.door_x - pulse_r), int(self.door_y - pulse_r)))

        for ped in sorted(self._pedestrians, key=lambda item: item["y"]):
            if ped["delay"] > 0 or ped["entered"]:
                continue
            npc_s = moviegoer_sprite(ped["character_id"], ped["fr"], ped["dir"])
            shadow = pygame.Surface((22, 7), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 75), shadow.get_rect())
            surface.blit(shadow, (int(ped["x"]) - 11, int(ped["y"]) - 4))
            surface.blit(npc_s, (int(ped["x"]) - npc_s.get_width() // 2, int(ped["y"]) - npc_s.get_height()))

        class ScreenCam:
            def world_to_screen(self, x, y): return x, y
        self.particles.draw(surface, ScreenCam())

        hint_alpha = int(140 + 60 * math.sin(self._t * 2.0))
        hint = self._hint_font.render("[Press Any Key / Click to Skip]", True, (190, 190, 220))
        hint.set_alpha(hint_alpha)
        surface.blit(hint, (SCREEN_W - hint.get_width() - 16, SCREEN_H - 24))

        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(int(self._fade_alpha))
            surface.blit(self._fade_surf, (0, 0))
