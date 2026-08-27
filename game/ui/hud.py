"""
CinePlex Dreams — HUD
Live stats panel, event log ticker, and mini-map zone indicators.
"""
import pygame
import math
from game.settings import (
    SCREEN_W, SCREEN_H,
    C_NEON_GOLD, C_NEON_CYAN, C_NEON_PINK, C_NEON_GREEN, C_NEON_RED,
    C_TEXT_WHITE, C_TEXT_DIM, C_TEXT_GOLD, C_PANEL_BORDER, C_GOOD, C_BAD, C_WARN,
)
from game.ui.button import draw_panel, draw_text, Button


def _font(name, size, bold=False):
    try:    return pygame.font.SysFont(name, size, bold=bold)
    except: return pygame.font.Font(None, size)


def _bar(surface, rect, value, max_val, color, bg=(40,30,60), radius=4):
    pygame.draw.rect(surface, bg, rect, border_radius=radius)
    if max_val > 0:
        fw = int(rect.w * min(1.0, value/max_val))
        if fw > 0:
            pygame.draw.rect(surface, color,
                             pygame.Rect(rect.x, rect.y, fw, rect.h),
                             border_radius=radius)
    pygame.draw.rect(surface, C_PANEL_BORDER, rect, 1, border_radius=radius)


class HUD:
    LOG_MAX = 6

    def __init__(self, bridge, player):
        self.bridge = bridge
        self.player = player

        self._tf = _font("consolas", 13, bold=True)
        self._sf = _font("consolas", 18, bold=True)
        self._lf = _font("consolas", 12)
        self._sm = _font("consolas", 11)

        # Left stats panel
        self._left  = pygame.Rect(8, 8, 210, 300)
        # Right controls panel
        self._right = pygame.Rect(SCREEN_W - 218, 8, 210, 180)

        # Buttons on right panel
        rx, ry = self._right.x + 10, self._right.y + 36
        self.btn_pause = Button(pygame.Rect(rx,      ry, 88, 30), "⏸ PAUSE",
                                C_NEON_GOLD, font_size=13)
        self.btn_reset = Button(pygame.Rect(rx+96,   ry, 88, 30), "↺ RESET",
                                C_NEON_RED,  font_size=13)
        # Speed buttons
        self._spd_btns: list[tuple[int, Button]] = []
        for i, (v, lbl) in enumerate([(1,"1×"),(2,"2×"),(5,"5×"),(10,"10×")]):
            btn = Button(pygame.Rect(rx + i*46, ry+40, 40, 26), lbl,
                         C_NEON_CYAN, font_size=13)
            btn.on_click(lambda s=v: setattr(self.bridge, 'speed', s))
            self._spd_btns.append((v, btn))

        # Journey status strip
        self._journey_rect = pygame.Rect(SCREEN_W//2 - 200, 8, 400, 36)

        # Event log
        self._log_rect = pygame.Rect(8, SCREEN_H - 100, SCREEN_W - 16, 92)
        self._log: list[tuple[str, tuple]] = []
        self._t = 0.0

    def add_log(self, text: str, color=C_TEXT_WHITE):
        self._log.append((text, color))
        if len(self._log) > 40:
            self._log = self._log[-40:]

    def handle_event(self, evt):
        self.btn_pause.handle_event(evt)
        self.btn_reset.handle_event(evt)
        for _, b in self._spd_btns: b.handle_event(evt)

    def update(self, dt):
        self._t += dt
        self.btn_pause.update(dt)
        self.btn_reset.update(dt)
        for _, b in self._spd_btns: b.update(dt)
        # Update pause button label
        self.btn_pause.text = "▶ RESUME" if self.bridge.is_paused else "⏸ PAUSE"

    def draw(self, surface: pygame.Surface):
        stats = self.bridge.stats
        p     = self.player

        # ── Left stats panel ─────────────────────────────────────────────
        draw_panel(surface, self._left, C_NEON_GOLD, alpha=210, radius=8)
        x, y = self._left.x + 10, self._left.y + 8

        draw_text(surface, "◆ LIVE STATS ◆", self._tf, C_NEON_GOLD,
                  (self._left.centerx, y), centered=True)
        y += 26

        sim_m = int(stats.sim_time); sim_s = int((stats.sim_time%1)*60)
        draw_text(surface, f"⏱  {sim_m:02d}:{sim_s:02d}", self._sf,
                  C_TEXT_WHITE, (x, y)); y += 28

        draw_text(surface, f"🧍 Arrived: {stats.total_arrived}", self._lf,
                  C_TEXT_DIM, (x, y)); y += 18
        draw_text(surface, f"🪑 Seated:  {stats.total_seated}", self._lf,
                  C_TEXT_DIM, (x, y)); y += 24

        avg = stats.avg_wait
        wm, ws = int(avg), int((avg%1)*60)
        wc = C_GOOD if avg < 8 else C_WARN if avg < 10 else C_BAD
        draw_text(surface, "AVG WAIT:", self._lf, C_TEXT_DIM, (x, y)); y += 18
        draw_text(surface, f"  {wm}m {ws:02d}s", self._sf, wc, (x, y)); y += 28
        # Pulse border if over limit
        if avg >= 10 and self.bridge.is_running:
            a = int(180 * abs(math.sin(self._t*3)))
            pygame.draw.rect(surface, C_BAD, self._left, 2, border_radius=8)

        # Queue bars
        draw_text(surface, "QUEUES:", self._lf, C_TEXT_DIM, (x, y)); y += 18
        for label, val, maxv, col in [
            ("🎟 Cashier", stats.cashier_queue, 15, C_NEON_GOLD),
            ("🎫 Usher",   stats.usher_queue,    5, C_NEON_PINK),
            ("🍿 Snack",   stats.snack_queue,    10, C_NEON_CYAN),
        ]:
            draw_text(surface, f"{label}: {val}", self._sm, C_TEXT_DIM, (x, y)); y += 14
            _bar(surface, pygame.Rect(x, y, self._left.w-20, 8), val, maxv, col); y += 16

        # ── Right controls panel ──────────────────────────────────────────
        draw_panel(surface, self._right, C_NEON_CYAN, alpha=210, radius=8)
        draw_text(surface, "◆ CONTROLS ◆", self._tf, C_NEON_CYAN,
                  (self._right.centerx, self._right.y+8), centered=True)
        self.btn_pause.draw(surface)
        self.btn_reset.draw(surface)
        draw_text(surface, "SPEED:", self._sm, C_TEXT_DIM,
                  (self._right.x+10, self._right.y+80))
        for v, b in self._spd_btns:
            if v == self.bridge.speed:
                pygame.draw.rect(surface, C_NEON_CYAN, b.rect, 2, border_radius=6)
            b.draw(surface)

        # ── Journey progress strip (top center) ───────────────────────────
        self._draw_journey(surface)

        # ── Event log ─────────────────────────────────────────────────────
        draw_panel(surface, self._log_rect, C_PANEL_BORDER, alpha=180, radius=4)
        visible = self._log[-self.LOG_MAX:]
        for i, (txt, col) in enumerate(visible):
            draw_text(surface, txt, self._sm, col,
                      (self._log_rect.x+8, self._log_rect.y+6+i*14), shadow=False)

        # ── Paused overlay ────────────────────────────────────────────────
        if self.bridge.is_paused:
            ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            ov.fill((0,0,0,100))
            surface.blit(ov, (0,0))
            pf = _font("consolas", 52, bold=True)
            pt = pf.render("⏸  PAUSED", True, C_NEON_GOLD)
            pt.set_alpha(int(180+75*abs(math.sin(self._t*2))))
            surface.blit(pt, pt.get_rect(center=(SCREEN_W//2, SCREEN_H//2)))

    def _draw_journey(self, surface):
        """Progress strip showing player's current stage."""
        from game.entities.player import Stage
        p = self.player
        stages = [
            ("🎟 Ticket",   p.has_ticket,     C_NEON_GOLD),
            ("🎫 Checked",  p.ticket_checked, C_NEON_PINK),
            ("🍿 Snacks",   p.has_food,        C_NEON_CYAN),
            ("🪑 Seated",   p.stage==Stage.SEATED, C_NEON_GREEN),
        ]
        rect = self._journey_rect
        draw_panel(surface, rect, C_NEON_GOLD, alpha=190, radius=6)
        sw = rect.w // len(stages)
        for i, (label, done, col) in enumerate(stages):
            ix = rect.x + i*sw + sw//2
            iy = rect.centery
            c  = col if done else C_TEXT_DIM
            draw_text(surface, label, self._sm, c, (ix, iy), centered=True, shadow=False)
