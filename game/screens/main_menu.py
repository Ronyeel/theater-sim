
from typing import Callable, Optional
import math
import random
import pygame
from game.settings import (
    SCREEN_W, SCREEN_H, C_NEON_GOLD, C_NEON_PINK,
    C_NEON_CYAN, C_BG_DARK, C_TEXT_WHITE, C_TEXT_DIM,
)
from game.core import asset_loader as AL
from game.ui.button import Button


def _get_font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


class Star:

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

    def __init__(
        self,
        go_start: Callable[[], None],
        go_setup: Optional[Callable[[], None]] = None,
        go_booking: Optional[Callable[[], None]] = None,
    ) -> None:
        self.go_start = go_start
        self.go_setup = go_setup or go_start
        self.go_booking = go_booking or go_start
        self._t = 0.0

        self._title_f = _get_font("consolas", 56, bold=True)
        self._sub_f = _get_font("consolas", 20, bold=True)
        self._body_f = _get_font("consolas", 14)
        self._credit_f = _get_font("consolas", 11)

        self._stars = [Star() for _ in range(80)]

        cx = SCREEN_W // 2
        by = SCREEN_H // 2 + 50

        self.btn_start = Button(
            pygame.Rect(cx - 150, by, 300, 44),
            "START SIMULATION", C_NEON_GOLD, 15,
        )
        self.btn_start.on_click(self.go_start)

        self.btn_setup = Button(
            pygame.Rect(cx - 150, by + 52, 300, 40),
            "CUSTOM SETUP", C_NEON_CYAN, 14,
        )
        self.btn_setup.on_click(self.go_setup)

        self.btn_booking = Button(
            pygame.Rect(cx - 150, by + 100, 300, 40),
            "RESERVE SEATS (BOOKING)", (100, 220, 140), 14,
        )
        self.btn_booking.on_click(self.go_booking)


    def handle_event(self, evt: pygame.event.Event) -> None:
        self.btn_start.handle_event(evt)
        self.btn_setup.handle_event(evt)
        self.btn_booking.handle_event(evt)
        if evt.type == pygame.KEYDOWN:
            if evt.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.go_start()

    def update(self, dt: float) -> None:
        self._t += dt
        self.btn_start.update(dt)
        self.btn_setup.update(dt)
        self.btn_booking.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        bg = AL.menu_background(self._t)
        surface.blit(bg, (0, 0))

        frames = AL.menu_background_frames()
        # Animated GIF has multiple frames; static fallback has exactly one
        has_custom_bg = len(frames) > 1

        if not has_custom_bg:
            # Fallback starry night if no background asset is present
            ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 120))
            surface.blit(ov, (0, 0))
            for star in self._stars:
                star.draw(surface, self._t)
        else:
            # Soft glassmorphic backdrop behind the menu buttons
            btn_rect = pygame.Rect(SCREEN_W // 2 - 170, SCREEN_H // 2 + 40, 340, 165)
            btn_backdrop = pygame.Surface((btn_rect.width, btn_rect.height), pygame.SRCALPHA)
            btn_backdrop.fill((8, 12, 22, 140))
            surface.blit(btn_backdrop, btn_rect.topleft)
            pygame.draw.rect(surface, (45, 58, 85), btn_rect, 1, border_radius=12)

        logo = AL.menu_title_logo()
        if logo:
            logo_rect = logo.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 70))
            glow = pygame.Surface((logo_rect.width + 80, logo_rect.height + 40), pygame.SRCALPHA)
            flicker = 0.85 + 0.15 * math.sin(self._t * 3.5)
            glow.fill((*C_NEON_GOLD[:3], int(25 * flicker)))
            surface.blit(glow, glow.get_rect(center=logo_rect.center))
            surface.blit(logo, logo_rect)
        else:
            ty = SCREEN_H // 2 - 20
            glow = pygame.Surface((640, 80), pygame.SRCALPHA)
            glow.fill((*C_NEON_GOLD[:3], 35))
            surface.blit(glow, (SCREEN_W // 2 - 320, ty - 25))
            title_surf = self._title_f.render("THEATER SIMULATOR", True, C_NEON_GOLD)
            surface.blit(title_surf, title_surf.get_rect(center=(SCREEN_W // 2, ty + 10)))

        self.btn_start.draw(surface)
        self.btn_setup.draw(surface)
        self.btn_booking.draw(surface)


