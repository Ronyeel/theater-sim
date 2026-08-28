"""
Main Menu Screen
Animated title over retro neon cinema marquee with star particles and mode selection.
"""

from typing import Callable, Optional
import math
import random
import pygame
from game.settings import (
    SCREEN_W, SCREEN_H, C_NEON_GOLD, C_NEON_PINK,
    C_NEON_CYAN, C_TEXT_WHITE, C_TEXT_DIM,
)
from game.core import asset_loader as AL
from game.ui.button import Button


def _get_font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


class Star:
    """Twinkling background star particle."""

    def __init__(self) -> None:
        self.x = random.uniform(0, SCREEN_W)
        self.y = random.uniform(0, SCREEN_H * 0.45)
        self.r = random.uniform(0.5, 2.5)
        self.spd = random.uniform(1.5, 4.0)
        self.phase = random.uniform(0, math.pi * 2)
        self.bright = random.randint(140, 255)

    def draw(self, surface: pygame.Surface, t: float) -> None:
        a = self.bright * (0.6 + 0.4 * math.sin(t * self.spd + self.phase))
        pygame.draw.circle(
            surface,
            (int(a), int(a), int(a * 0.9)),
            (int(self.x), int(self.y)),
            max(1, int(self.r)),
        )


class MainMenu:
    """Main menu title screen."""

    def __init__(self, go_start: Callable[[], None], go_setup: Optional[Callable[[], None]] = None) -> None:
        self.go_start = go_start
        self.go_setup = go_setup or go_start
        self._t = 0.0

        self._title_f = _get_font("consolas", 56, bold=True)
        self._sub_f = _get_font("consolas", 20, bold=True)
        self._body_f = _get_font("consolas", 14)
        self._credit_f = _get_font("consolas", 11)

        self._stars = [Star() for _ in range(80)]

        cx = SCREEN_W // 2
        by = SCREEN_H // 2 + 65

        self.btn_start = Button(
            pygame.Rect(cx - 150, by, 300, 46),
            "▶  START SIMULATION", C_NEON_GOLD, 15,
        )
        self.btn_start.on_click(self.go_start)

        self.btn_setup = Button(
            pygame.Rect(cx - 150, by + 56, 300, 42),
            "⚙  CUSTOM SETUP", C_NEON_CYAN, 14,
        )
        self.btn_setup.on_click(self.go_setup)

    def handle_event(self, evt: pygame.event.Event) -> None:
        self.btn_start.handle_event(evt)
        self.btn_setup.handle_event(evt)
        if evt.type == pygame.KEYDOWN:
            if evt.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.go_start()

    def update(self, dt: float) -> None:
        self._t += dt
        self.btn_start.update(dt)
        self.btn_setup.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        # Animated GIF Background
        bg = AL.menu_background(self._t)
        surface.blit(bg, (0, 0))

        # Dark overlay for readability
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 120))
        surface.blit(ov, (0, 0))

        # Stars
        for star in self._stars:
            star.draw(surface, self._t)

        # Title: Theater Simulator

        ty = SCREEN_H // 2 - 20
        glow = pygame.Surface((640, 80), pygame.SRCALPHA)
        glow.fill((*C_NEON_GOLD[:3], 35))
        surface.blit(glow, (SCREEN_W // 2 - 320, ty - 25))

        title_surf = self._title_f.render("THEATER SIMULATOR", True, C_NEON_GOLD)
        surface.blit(title_surf, title_surf.get_rect(center=(SCREEN_W // 2, ty + 10)))

        # Buttons
        self.btn_start.draw(surface)
        self.btn_setup.draw(surface)

