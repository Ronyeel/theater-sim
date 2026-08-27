"""
CinePlex Dreams — Cinema Exterior Scene (Scene 1)
The player starts outside the cinema, walks up the sidewalk past the street,
and enters through the cinema doors into the theater simulation.
"""
import os
import pygame
import math
import random
from game.settings import (
    SCREEN_W, SCREEN_H, C_BG_DARK, C_NEON_GOLD, C_NEON_CYAN, C_NEON_PINK,
    C_TEXT_WHITE, C_TEXT_DIM, PLAYER_SPEED, BG_DIR,
)
from game.core import asset_loader as AL
from game.core.particles import ParticleSystem
from game.entities.npc import moviegoer_sprite
from game.entities.player import DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIR_UP
from game.ui.speech_bubble import DialogPrompt


def _font(name, size, bold=False):
    try:    return pygame.font.SysFont(name, size, bold=bold)
    except: return pygame.font.Font(None, size)


class ExteriorScreen:
    def __init__(self, go_interior):
        self.go_interior = go_interior
        self._t = 0.0

        # Load & prepare cinema exterior background
        ext_path = os.path.join(BG_DIR, "outside cinema.png")
        if os.path.exists(ext_path):
            raw = pygame.image.load(ext_path).convert()
            # Scale to fit full height of screen (720px)
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

        # Player spawn in exterior scene (bottom center on crosswalk)
        # Scaled coordinates on the exterior background
        self.px = float(self._offset_x + self._bg_w * 0.50)
        self.py = float(self._bg_h * 0.88)

        self._vx = 0.0
        self._vy = 0.0
        self._direction = DIR_UP
        self._moving = False
        self._anim_frame = 0
        self._anim_timer = 0.0

        # Entrance door trigger zone (center front doors)
        self.door_x = self._offset_x + self._bg_w * 0.50
        self.door_y = self._bg_h * 0.70  # Door entrance position

        # Interaction & UI
        self.dialog = DialogPrompt()
        self.particles = ParticleSystem()
        self._title_font = _font("consolas", 18, bold=True)
        self._hint_font = _font("consolas", 14)

        # Transition state
        self._entering = False
        self._fade_alpha = 0.0
        self._fade_surf = pygame.Surface((SCREEN_W, SCREEN_H))
        self._fade_surf.fill((0, 0, 0))

        # Ambient visitors have different lanes, speeds and destinations so
        # the forecourt feels like a small crowd, not a looping backdrop.
        self._pedestrians = [
            self._make_pedestrian(0.22, 0.76, DIR_RIGHT, 25, 2),
            self._make_pedestrian(0.78, 0.78, DIR_LEFT, 20, 19),
            self._make_pedestrian(0.35, 0.85, DIR_RIGHT, 15, 34),
            self._make_pedestrian(0.66, 0.89, DIR_LEFT, 18, 45),
        ]

    def _make_pedestrian(self, x_ratio, y_ratio, direction, speed, character_id):
        """Create a visitor that strolls, pauses, and occasionally changes lane."""
        return {
            "x": self._offset_x + self._bg_w * x_ratio,
            "y": self._bg_h * y_ratio,
            "home_y": self._bg_h * y_ratio,
            "dir": direction,
            "spd": speed * random.uniform(0.85, 1.15),
            "fr": random.randrange(3),
            "anim": random.uniform(0.0, 0.14),
            "pause": random.uniform(0.2, 1.6),
            "turn_at": random.uniform(2.2, 5.0),
            # Use the supplied moviegoer character sheets here too, rather
            # than the simple generated figure used by the old exterior.
            "character_id": character_id,
        }

    def _update_pedestrians(self, dt):
        left_edge = self._offset_x + self._bg_w * 0.16
        right_edge = self._offset_x + self._bg_w * 0.84
        for ped in self._pedestrians:
            if ped["pause"] > 0:
                ped["pause"] -= dt
                ped["fr"] = 0
                continue

            ped["turn_at"] -= dt
            ped["x"] += (ped["spd"] if ped["dir"] == DIR_RIGHT else -ped["spd"]) * dt
            # A tiny lane drift makes the group feel less locked to a grid.
            ped["y"] = ped["home_y"] + math.sin(self._t * 1.3 + ped["character_id"]) * 3
            ped["anim"] += dt
            if ped["anim"] >= 0.16:
                ped["anim"] = 0.0
                ped["fr"] = (ped["fr"] + 1) % 3

            reached_edge = ped["x"] <= left_edge or ped["x"] >= right_edge
            if reached_edge or ped["turn_at"] <= 0:
                ped["dir"] = DIR_LEFT if ped["dir"] == DIR_RIGHT else DIR_RIGHT
                ped["x"] = max(left_edge, min(right_edge, ped["x"]))
                ped["turn_at"] = random.uniform(2.5, 5.5)
                # Some visitors stop to check the marquee before continuing.
                if random.random() < 0.45:
                    ped["pause"] = random.uniform(0.45, 1.5)

    def handle_event(self, evt):
        if self._entering:
            return
        if evt.type == pygame.KEYDOWN:
            if evt.key == pygame.K_e or evt.key == pygame.K_RETURN:
                # Check if near door
                dist = math.hypot(self.px - self.door_x, self.py - self.door_y)
                if dist < 65:
                    self._start_enter()

    def _start_enter(self):
        if not self._entering:
            self._entering = True
            self.particles.burst(self.door_x, self.door_y - 20, C_NEON_GOLD, count=25, speed=120)
            self.particles.confetti(self.door_x, self.door_y - 30, count=20)

    def update(self, dt: float):
        self._t += dt
        self.particles.update(dt)

        if self._entering:
            self._fade_alpha = min(255.0, self._fade_alpha + 320 * dt)
            if self._fade_alpha >= 255.0:
                self.go_interior()
            return

        # Player Movement
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy =  1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx =  1

        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        self._vx = dx * (PLAYER_SPEED * 1.1)
        self._vy = dy * (PLAYER_SPEED * 1.1)
        self._moving = (dx != 0 or dy != 0)

        if dx < 0:   self._direction = DIR_LEFT
        elif dx > 0: self._direction = DIR_RIGHT
        elif dy < 0: self._direction = DIR_UP
        elif dy > 0: self._direction = DIR_DOWN

        # Move with exterior boundary constraints
        new_x = self.px + self._vx * dt
        new_y = self.py + self._vy * dt

        # Sidewalk & Plaza bounds
        min_x = self._offset_x + self._bg_w * 0.12
        max_x = self._offset_x + self._bg_w * 0.88
        min_y = self._bg_h * 0.68  # Can't walk past doors
        max_y = self._bg_h * 0.94  # Street limit

        self.px = max(min_x, min(max_x, new_x))
        self.py = max(min_y, min(max_y, new_y))

        # Animation
        if self._moving:
            self._anim_timer += dt
            if self._anim_timer >= 0.14:
                self._anim_timer = 0
                self._anim_frame = (self._anim_frame + 1) % 4
        else:
            self._anim_frame = 0

        self._update_pedestrians(dt)

        # Door proximity check
        dist = math.hypot(self.px - self.door_x, self.py - self.door_y)
        if dist < 65:
            self.dialog.show("[E] ENTER CINEMA")
            # Auto-enter if walking right into the center doorway
            if self.py <= self._bg_h * 0.70:
                self._start_enter()
        else:
            self.dialog.hide()

        self.dialog.update(dt)

    def draw(self, surface: pygame.Surface):
        # Fill black / dark background pillars
        surface.fill(C_BG_DARK)

        # Draw decorative background city ambiance on the sides
        for x_pillar in (0, self._offset_x + self._bg_w):
            w_pillar = (SCREEN_W - self._bg_w) // 2 + 2
            pygame.draw.rect(surface, (18, 12, 32), (x_pillar, 0, w_pillar, SCREEN_H))
            # Glowing side neon lines
            pulse = 0.5 + 0.5 * math.sin(self._t * 3.0)
            neon_col = (*C_NEON_PINK[:3], int(120 * pulse))
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
        glow.fill((*C_NEON_GOLD[:3], int(25 * flicker)))
        surface.blit(glow, glow_rect.topleft)

        # Draw Door Entrance Pulse Ring
        pulse_r = int(18 + 6 * math.sin(self._t * 3.5))
        door_pulse = pygame.Surface((pulse_r * 2, pulse_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(door_pulse, (*C_NEON_GOLD[:3], 90), (pulse_r, pulse_r), pulse_r, 2)
        surface.blit(door_pulse, (int(self.door_x - pulse_r), int(self.door_y - pulse_r)))

        # Draw pedestrians from back to front, with a small shadow to anchor
        # them on the sidewalk.
        for ped in sorted(self._pedestrians, key=lambda item: item["y"]):
            npc_s = moviegoer_sprite(ped["character_id"], ped["fr"], ped["dir"])
            shadow = pygame.Surface((22, 7), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 65), shadow.get_rect())
            surface.blit(shadow, (int(ped["x"]) - 11, int(ped["y"]) - 4))
            surface.blit(npc_s, (int(ped["x"]) - npc_s.get_width()//2, int(ped["y"]) - npc_s.get_height()))

        # Draw Player Drop Shadow
        shadow = pygame.Surface((28, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), (0, 0, 28, 12))
        surface.blit(shadow, (int(self.px) - 14, int(self.py) - 6))

        # Draw Player Sprite
        sprite = AL.player_sprite(self._anim_frame, self._direction)
        sw, sh = sprite.get_size()
        surface.blit(sprite, (int(self.px) - sw // 2, int(self.py) - sh))

        # Particles
        class ScreenCam:
            def world_to_screen(self, x, y): return x, y
        self.particles.draw(surface, ScreenCam())

        # Dialog Prompt [E] ENTER CINEMA
        self.dialog.draw(surface)

        # Top Banner / Objective Banner
        banner = pygame.Rect(SCREEN_W // 2 - 220, 16, 440, 38)
        bg_bar = pygame.Surface((banner.w, banner.h), pygame.SRCALPHA)
        bg_bar.fill((15, 10, 30, 210))
        surface.blit(bg_bar, banner.topleft)
        pygame.draw.rect(surface, C_NEON_GOLD, banner, 2, border_radius=6)

        txt = self._title_font.render("🎬 ARRIVAL: CINEMA ENTRANCE", True, C_NEON_GOLD)
        surface.blit(txt, txt.get_rect(center=(SCREEN_W // 2, banner.centery)))

        # Bottom Walk Hint
        if not self._entering and not self.dialog._visible:
            hint = self._hint_font.render("▲ Walk up to the cinema doors to enter", True, C_TEXT_DIM)
            surface.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - 30)))

        # Fade Out Overlay
        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(int(self._fade_alpha))
            surface.blit(self._fade_surf, (0, 0))
