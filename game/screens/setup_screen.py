"""
CinePlex Dreams — Setup Screen
Sliders for staff counts, runtime, speed before launching the game.
"""
import pygame
import math
from game.settings import (
    SCREEN_W, SCREEN_H, C_BG_DARK, C_NEON_GOLD, C_NEON_PINK,
    C_NEON_CYAN, C_TEXT_WHITE, C_TEXT_DIM,
)
from game.ui.button import Button, Slider, draw_text, draw_panel


def _font(name, size, bold=False):
    try:    return pygame.font.SysFont(name, size, bold=bold)
    except: return pygame.font.Font(None, size)


class SetupScreen:
    def __init__(self, bridge, go_game):
        self.bridge  = bridge
        self.go_game = go_game
        self._t = 0.0

        self._tf = _font("consolas", 32, bold=True)
        self._bf = _font("consolas", 13)

        cx = SCREEN_W // 2
        pw, ph = 500, 500
        px = cx - pw//2
        py = 70
        self._panel = pygame.Rect(px, py, pw, ph)

        sx, sw = px + 40, pw - 80
        sy = py + 80

        self.sl_cashiers = Slider(pygame.Rect(sx, sy, sw, 36),
            "🎟  Cashiers (box office)", 1, 6, bridge.num_cashiers, C_NEON_GOLD)
        self.sl_ushers   = Slider(pygame.Rect(sx, sy+80, sw, 36),
            "🎫  Ushers (ticket checkers)", 1, 3, bridge.num_ushers, C_NEON_PINK)
        self.sl_servers  = Slider(pygame.Rect(sx, sy+160, sw, 36),
            "🍿  Servers (concession stand)", 1, 4, bridge.num_servers, C_NEON_CYAN)
        self.sl_runtime  = Slider(pygame.Rect(sx, sy+240, sw, 36),
            "⏱  Runtime (simulated minutes)", 30, 120, bridge.runtime, C_TEXT_WHITE)
        self.sl_food     = Slider(pygame.Rect(sx, sy+320, sw, 36),
            "🍿  Food probability (%)", 0, 100, int(bridge.food_prob*100), (200,200,100))

        self.sliders = [self.sl_cashiers, self.sl_ushers, self.sl_servers,
                        self.sl_runtime, self.sl_food]

        # Speed
        self._speed = bridge.speed
        self._spd_btns: list[tuple[int, Button]] = []
        for i, (v, lbl) in enumerate([(1,"1×"),(2,"2×"),(5,"5×"),(10,"10×")]):
            btn = Button(pygame.Rect(sx+i*110, py+440, 96, 30), lbl,
                         C_NEON_CYAN, font_size=14)
            btn.on_click(lambda s=v: self._set_speed(s))
            self._spd_btns.append((v, btn))

        self.btn_start = Button(
            pygame.Rect(cx-130, py+490, 260, 50),
            "▶  START SIMULATION", C_NEON_GOLD, 17,
        )
        self.btn_start.on_click(self._on_start)

        # Background dots
        import random
        self._dots = [
            (random.uniform(0, SCREEN_W), random.uniform(0, SCREEN_H),
             random.uniform(0, math.pi*2))
            for _ in range(50)
        ]

    def _set_speed(self, v):
        self._speed = v

    def _on_start(self):
        b = self.bridge
        b.num_cashiers = self.sl_cashiers.value
        b.num_ushers   = self.sl_ushers.value
        b.num_servers  = self.sl_servers.value
        b.runtime      = self.sl_runtime.value
        b.food_prob    = self.sl_food.value / 100.0
        b.speed        = self._speed
        b.start()
        self.go_game()

    def handle_event(self, evt):
        for sl in self.sliders: sl.handle_event(evt)
        for _, btn in self._spd_btns: btn.handle_event(evt)
        self.btn_start.handle_event(evt)

    def update(self, dt):
        self._t += dt
        for _, btn in self._spd_btns: btn.update(dt)
        self.btn_start.update(dt)

    def draw(self, surface):
        surface.fill(C_BG_DARK)

        # Dots
        for dx, dy, ph in self._dots:
            a = int(40 + 30 * math.sin(self._t*1.2 + ph))
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_NEON_GOLD[:3], a), (3, 3), 2)
            surface.blit(s, (int(dx), int(dy)))

        # Panel
        draw_panel(surface, self._panel, C_NEON_GOLD, alpha=210, radius=12)
        draw_text(surface, "⚙  SETUP", self._tf, C_NEON_GOLD,
                  (SCREEN_W//2, self._panel.y+34), centered=True)

        # Sliders
        for sl in self.sliders: sl.draw(surface)

        # Speed buttons
        draw_text(surface, "SPEED:", self._bf, C_TEXT_DIM,
                  (self._panel.x+40, self._panel.y+424))
        for v, btn in self._spd_btns:
            if v == self._speed:
                pygame.draw.rect(surface, C_NEON_CYAN, btn.rect, 3, border_radius=6)
            btn.draw(surface)

        # Staff dot preview
        configs = [
            (self.sl_cashiers, C_NEON_GOLD),
            (self.sl_ushers,   C_NEON_PINK),
            (self.sl_servers,  C_NEON_CYAN),
        ]
        for sl, col in configs:
            for i in range(sl.max_val):
                a = 220 if i < sl.value else 40
                d = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.rect(d, (*col[:3], a), (0,0,10,10), border_radius=3)
                surface.blit(d, (sl.rect.x + i*13, sl.rect.y+42))

        # Start button
        self.btn_start.draw(surface)
