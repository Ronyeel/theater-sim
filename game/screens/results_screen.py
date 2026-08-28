"""
Results and Performance Screen
Cinema-ticket styled report card showing simulation grade (S/A/B/C/F), average wait times,
throughput metrics, staffing recommendations, and navigation options.
"""

from typing import Callable, Tuple
import math
import random
import pygame
from game.settings import (
    SCREEN_W, SCREEN_H, C_BG_DARK,
    C_NEON_GOLD, C_NEON_PINK, C_NEON_CYAN, C_NEON_GREEN, C_NEON_RED,
    C_TEXT_WHITE, C_TEXT_DIM, C_PANEL_BORDER, C_GOOD, C_BAD, C_WARN,
)
from game.ui.button import Button, draw_text, draw_panel
from game.core.particles import ParticleSystem
from src.stats import format_minutes_seconds


def _get_font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


class _ScreenSpaceCamera:
    """Pass-through camera for drawing screen-space particle effects."""
    @staticmethod
    def world_to_screen(x: float, y: float) -> Tuple[float, float]:
        return x, y


class ResultsScreen:
    """Simulation results card with grade, performance metrics, and replay controls."""

    def __init__(
        self,
        bridge,
        go_game: Callable[[], None],
        go_setup: Callable[[], None],
        go_title: Callable[[], None],
        quit_game: Callable[[], None],
    ) -> None:
        self.bridge = bridge
        self.go_game = go_game
        self.go_setup = go_setup
        self.go_title = go_title
        self.quit_game = quit_game
        self._t = 0.0
        self._reveal = 0.0

        self._bf = _get_font("consolas", 36, bold=True)
        self._tf = _get_font("consolas", 22, bold=True)
        self._sf = _get_font("consolas", 18, bold=True)
        self._lf = _get_font("consolas", 14)
        self._sm = _get_font("consolas", 12)

        self.particles = ParticleSystem()
        self._screen_cam = _ScreenSpaceCamera()
        self._fw_timer = 0.0

        cw, ch = 640, 440
        self._card = pygame.Rect(SCREEN_W // 2 - cw // 2, SCREEN_H // 2 - ch // 2 - 20, cw, ch)

        bx = self._card.x + 15
        by = self._card.bottom + 14
        bw, bh = 145, 44
        self.btn_again = Button(pygame.Rect(bx, by, bw, bh), "▶ PLAY AGAIN", C_NEON_GREEN, 14)
        self.btn_setup = Button(pygame.Rect(bx + bw + 12, by, bw, bh), "⚙ SETUP", C_NEON_CYAN, 13)
        self.btn_title = Button(pygame.Rect(bx + (bw + 12) * 2, by, bw, bh), "🏠 MAIN MENU", C_NEON_GOLD, 13)
        self.btn_quit = Button(pygame.Rect(bx + (bw + 12) * 3, by, bw, bh), "✕ QUIT", C_NEON_RED, 14)

        self.btn_again.on_click(self._play_again)
        self.btn_setup.on_click(self.go_setup)
        self.btn_title.on_click(self.go_title)
        self.btn_quit.on_click(self.quit_game)

        self._slide_y = float(SCREEN_H)
        self._animating = True

        self._spots = [
            {
                "x": random.uniform(0, SCREEN_W),
                "y": random.uniform(0, SCREEN_H),
                "vx": random.uniform(-25, 25),
                "vy": random.uniform(-15, 15),
                "r": random.randint(50, 100),
                "ph": random.uniform(0, math.pi * 2),
            }
            for _ in range(4)
        ]

    def _play_again(self) -> None:
        self.bridge.reset()
        self.go_game()

    @property
    def _avg(self) -> float:
        return self.bridge.stats.avg_wait

    @property
    def _seated(self) -> int:
        return self.bridge.stats.total_seated

    @property
    def _arrived(self) -> int:
        return self.bridge.stats.total_arrived

    def _grade(self) -> Tuple[str, Tuple[int, int, int]]:
        a = self._avg
        if a < 5.0:
            return "S", C_NEON_CYAN
        if a < 8.0:
            return "A", C_NEON_GREEN
        if a < 10.0:
            return "B", C_NEON_GOLD
        if a < 13.0:
            return "C", C_WARN
        return "F", C_NEON_RED

    def _recommendation(self) -> Tuple[str, str, Tuple[int, int, int]]:
        a = self._avg
        nc = self.bridge.num_cashiers
        if a < 5.0:
            return (
                "Excellent! Minimal queueing across all service points.",
                "High efficiency — staffing exceeds minimum requirements.",
                C_NEON_GREEN,
            )
        if a <= 10.0:
            return (
                "Great job! Target constraint (<= 10 min) achieved.",
                f"Configuration ({nc} cashiers) balances cost and wait time well.",
                C_NEON_GOLD,
            )
        if a < 15.0:
            return (
                "Near target, but average wait slightly exceeds 10 minutes.",
                "Recommendation: Increase cashier staff by 1 to alleviate ticketing bottleneck.",
                C_WARN,
            )
        return (
            "Severe bottleneck! Long queue delays observed.",
            "Recommendation: Increase cashier count to at least 4 and ensure ushers are staffed.",
            C_NEON_RED,
        )

    def handle_event(self, evt: pygame.event.Event) -> None:
        for b in (self.btn_again, self.btn_setup, self.btn_title, self.btn_quit):
            b.handle_event(evt)

    def update(self, dt: float) -> None:
        self._t += dt
        self._reveal += dt
        if self._animating:
            self._slide_y = max(0.0, self._slide_y - 800.0 * dt)
            if self._slide_y <= 0:
                self._animating = False

        # Celebratory fireworks when target is met
        self._fw_timer += dt
        if self._avg <= 10.0 and self._fw_timer > 0.5:
            self._fw_timer = 0.0
            self.particles.burst(
                random.uniform(80, SCREEN_W - 80),
                random.uniform(60, SCREEN_H // 2),
                count=16,
                speed=100,
                lifetime=1.0,
            )
            self.particles.confetti(
                random.uniform(200, SCREEN_W - 200),
                random.uniform(80, SCREEN_H // 2),
            )
        self.particles.update(dt)

        for sp in self._spots:
            sp["x"] += sp["vx"] * dt
            sp["y"] += sp["vy"] * dt
            if sp["x"] < 0 or sp["x"] > SCREEN_W:
                sp["vx"] *= -1
            if sp["y"] < 0 or sp["y"] > SCREEN_H:
                sp["vy"] *= -1

        for b in (self.btn_again, self.btn_setup, self.btn_title, self.btn_quit):
            b.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(C_BG_DARK)

        # Ambient spotlights
        for sp in self._spots:
            glow = pygame.Surface((sp["r"] * 2, sp["r"] * 2), pygame.SRCALPHA)
            a = int(8 + 8 * math.sin(self._t * 1.5 + sp["ph"]))
            pygame.draw.circle(glow, (255, 230, 150, a), (sp["r"], sp["r"]), sp["r"])
            surface.blit(glow, (int(sp["x"] - sp["r"]), int(sp["y"] - sp["r"])))

        self.particles.draw(surface, self._screen_cam)

        # Results Ticket Card
        card = self._card.move(0, int(self._slide_y))
        draw_panel(surface, card, C_NEON_GOLD, alpha=225, radius=14, width=3)

        # Perforations
        py = card.y + 64
        for dx in range(0, card.w, 12):
            pygame.draw.circle(surface, C_BG_DARK, (card.x + dx, py), 3)

        # Header
        draw_text(
            surface, "🎬  SIMULATION REPORT CARD  🎬", self._tf, C_NEON_GOLD,
            (card.centerx, card.y + 32), centered=True
        )

        # Grade Badge
        gr, gc = self._grade()
        br = pygame.Rect(card.right - 82, card.y + 74, 62, 62)
        pygame.draw.rect(surface, gc, br, border_radius=8)
        pygame.draw.rect(surface, C_TEXT_WHITE, br, 2, border_radius=8)
        draw_text(surface, gr, self._bf, C_BG_DARK, br.center, centered=True)

        # Statistics with staggered entrance
        sx, sy = card.x + 28, py + 18
        delay = 0.15

        def render_stat(label: str, value: str, color: Tuple[int, int, int], idx: int) -> None:
            if self._reveal > idx * delay:
                alpha = min(255, int(255 * (self._reveal - idx * delay) / 0.3))
                ls = self._lf.render(label, True, C_TEXT_DIM)
                ls.set_alpha(alpha)
                vs = self._sf.render(value, True, color)
                vs.set_alpha(alpha)
                surface.blit(ls, (sx, sy + idx * 40))
                surface.blit(vs, (sx + 210, sy + idx * 40 - 2))

        avg = self._avg
        wm, ws = format_minutes_seconds(avg)
        wc = C_GOOD if avg <= 10.0 else C_BAD

        render_stat("Moviegoers Arrived:", str(self._arrived), C_NEON_CYAN, 0)
        render_stat("Moviegoers Seated:", str(self._seated), C_NEON_GREEN, 1)
        render_stat("Average Wait Time:", f"{wm}m {ws:02d}s", wc, 2)
        render_stat(
            "Target (<= 10 min):",
            "ACHIEVED" if avg <= 10.0 else "NOT MET",
            C_GOOD if avg <= 10.0 else C_BAD,
            3,
        )

        # Staffing Configuration Summary
        ssy = sy + 40 * 4 + 8
        if self._reveal > 5 * delay:
            pygame.draw.line(surface, C_PANEL_BORDER, (sx, ssy), (card.right - 28, ssy))
            ssy += 10
            draw_text(surface, "Staffing Configuration:", self._lf, C_TEXT_DIM, (sx, ssy))
            ssy += 20
            staff_items = [
                (f"Cashiers: {self.bridge.num_cashiers}", C_NEON_GOLD),
                (f"Ushers: {self.bridge.num_ushers}", C_NEON_PINK),
                (f"Servers: {self.bridge.num_servers}", C_NEON_CYAN),
            ]
            for txt, col in staff_items:
                draw_text(surface, txt, self._sm, col, (sx, ssy))
                sx += 180
            sx = card.x + 28

        # Manager's Recommendation
        ry = ssy + 36
        if self._reveal > 7 * delay:
            pygame.draw.line(surface, C_PANEL_BORDER, (sx, ry), (card.right - 28, ry))
            ry += 10
            l1, l2, rc = self._recommendation()
            draw_text(surface, "Manager's Evaluation:", self._lf, C_TEXT_DIM, (sx, ry))
            ry += 18
            pulse = 0.85 + 0.15 * math.sin(self._t * 2.0)
            draw_text(surface, l1, self._lf, tuple(int(c * pulse) for c in rc[:3]), (sx, ry))
            ry += 18
            draw_text(surface, l2, self._sm, C_TEXT_DIM, (sx, ry))

        # Bottom Action Buttons
        off = int(self._slide_y)
        for b in (self.btn_again, self.btn_setup, self.btn_title, self.btn_quit):
            oy = b.rect.y
            b.rect.y = oy + off
            b.draw(surface)
            b.rect.y = oy
