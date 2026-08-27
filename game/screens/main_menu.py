"""
CinePlex Dreams — Main Menu Screen
Animated title over the generated background image with particle stars.
"""
import pygame
import math
import random
from game.settings import (
    SCREEN_W, SCREEN_H, C_BG_DARK, C_NEON_GOLD, C_NEON_PINK,
    C_NEON_CYAN, C_TEXT_WHITE, C_TEXT_DIM,
)
from game.core import asset_loader as AL
from game.ui.button import Button, draw_text


def _font(name, size, bold=False):
    try:    return pygame.font.SysFont(name, size, bold=bold)
    except: return pygame.font.Font(None, size)


class Star:
    def __init__(self):
        self.x = random.uniform(0, SCREEN_W)
        self.y = random.uniform(0, SCREEN_H * 0.45)
        self.r = random.uniform(0.5, 2.5)
        self.spd = random.uniform(1.5, 4.0)
        self.phase = random.uniform(0, math.pi*2)
        self.bright = random.randint(140, 255)

    def draw(self, surface, t):
        a = self.bright * (0.6 + 0.4 * math.sin(t * self.spd + self.phase))
        pygame.draw.circle(surface, (int(a), int(a), int(a*0.9)),
                           (int(self.x), int(self.y)), max(1, int(self.r)))


class MainMenu:
    def __init__(self, go_setup):
        self.go_setup = go_setup
        self._t = 0.0

        self._title_f  = _font("consolas", 56, bold=True)
        self._sub_f    = _font("consolas", 22, bold=True)
        self._body_f   = _font("consolas", 14)
        self._credit_f = _font("consolas", 11)

        self._stars = [Star() for _ in range(100)]

        self._marquee_t = 0.0
        self._marquee = ("   ★ NOW SHOWING: THE SIMULATION OF A LIFETIME ★   "
                         "★ MANAGE YOUR THEATER  •  SEAT YOUR GUESTS  •  BEAT THE CLOCK ★   ")

        self.btn_start = Button(
            pygame.Rect(SCREEN_W//2-150, SCREEN_H//2+140, 300, 52),
            "▶  PRESS ENTER TO START", C_NEON_GOLD, 16,
        )
        self.btn_start.on_click(go_setup)

    def handle_event(self, evt):
        self.btn_start.handle_event(evt)
        if evt.type == pygame.KEYDOWN and evt.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.go_setup()

    def update(self, dt):
        self._t += dt
        self._marquee_t += 70 * dt
        self.btn_start.update(dt)

    def draw(self, surface):
        # Background image
        bg = AL.menu_background()
        surface.blit(bg, (0, 0))

        # Darken overlay for readability
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 120))
        surface.blit(ov, (0, 0))

        # Stars
        for star in self._stars:
            star.draw(surface, self._t)

        # Marquee strip at top
        mq = pygame.Rect(0, 0, SCREEN_W, 38)
        pygame.draw.rect(surface, (15, 8, 30), mq)
        pygame.draw.rect(surface, C_NEON_GOLD, mq, 2)
        try:
            mf = _font("consolas", 18, bold=True)
            ms = mf.render(self._marquee, True, C_NEON_GOLD)
            mx = int(-self._marquee_t % (ms.get_width() + SCREEN_W))
            surface.blit(ms, (SCREEN_W - mx, 8))
            surface.blit(ms, (SCREEN_W - mx + ms.get_width(), 8))
        except Exception:
            pass

        # Title
        ty = SCREEN_H // 2 - 100
        # Glow
        glow = pygame.Surface((600, 90), pygame.SRCALPHA)
        glow.fill((*C_NEON_PINK[:3], 30))
        surface.blit(glow, (SCREEN_W//2-300, ty-10))

        t1 = self._title_f.render("CINEPLEX", True, C_NEON_PINK)
        surface.blit(t1, t1.get_rect(center=(SCREEN_W//2, ty)))
        t2 = self._title_f.render("DREAMS", True, C_NEON_CYAN)
        surface.blit(t2, t2.get_rect(center=(SCREEN_W//2, ty+64)))

        # Subtitle
        sa = int(200 + 55 * math.sin(self._t * 1.2))
        ss = self._sub_f.render("★  THEATER QUEUE SIMULATION  ★", True, C_NEON_GOLD)
        ss.set_alpha(sa)
        surface.blit(ss, ss.get_rect(center=(SCREEN_W//2, ty+140)))

        # Description
        for i, line in enumerate([
            "Control your moviegoer through the cinema.",
            "Buy tickets, grab snacks, find your seat!",
            "Keep the average wait under 10 minutes.",
        ]):
            ds = self._body_f.render(line, True, C_TEXT_DIM)
            ds.set_alpha(int(160 + 40*math.sin(self._t*0.8 + i*0.5)))
            surface.blit(ds, ds.get_rect(center=(SCREEN_W//2, ty+185+i*20)))

        # Start button
        self.btn_start.draw(surface)

        # Credits
        cr = self._credit_f.render(
            "CinePlex Dreams  •  Theater Queuing Simulation  •  Pygame + SimPy",
            True, (80, 70, 100))
        surface.blit(cr, cr.get_rect(center=(SCREEN_W//2, SCREEN_H-18)))
