"""
CinePlex Dreams — Results Screen
Cinema-ticket styled results card with grade, stats, and recommendations.
"""
import pygame
import math
import random
from game.settings import (
    SCREEN_W, SCREEN_H, C_BG_DARK,
    C_NEON_GOLD, C_NEON_PINK, C_NEON_CYAN, C_NEON_GREEN, C_NEON_RED,
    C_TEXT_WHITE, C_TEXT_DIM, C_PANEL_BORDER, C_GOOD, C_BAD, C_WARN,
)
from game.ui.button import Button, draw_text, draw_panel
from game.core.particles import ParticleSystem


def _font(name, size, bold=False):
    try:    return pygame.font.SysFont(name, size, bold=bold)
    except: return pygame.font.Font(None, size)


class ResultsScreen:
    def __init__(self, bridge, go_setup, go_title, quit_game):
        self.bridge    = bridge
        self.go_setup  = go_setup
        self.go_title  = go_title
        self.quit_game = quit_game
        self._t = 0.0
        self._reveal = 0.0

        self._bf = _font("consolas", 36, bold=True)
        self._tf = _font("consolas", 22, bold=True)
        self._sf = _font("consolas", 18, bold=True)
        self._lf = _font("consolas", 14)
        self._sm = _font("consolas", 12)

        self.particles = ParticleSystem()
        self._fw_timer = 0.0

        cw, ch = 640, 440
        self._card = pygame.Rect(SCREEN_W//2-cw//2, SCREEN_H//2-ch//2-20, cw, ch)

        bx = self._card.x + 15
        by = self._card.bottom + 14
        bw, bh = 145, 44
        self.btn_again  = Button(pygame.Rect(bx,         by, bw, bh), "▶ PLAY AGAIN",   C_NEON_GREEN, 14)
        self.btn_setup  = Button(pygame.Rect(bx+bw+12,   by, bw, bh), "⚙ CHANGE SETUP", C_NEON_CYAN,  13)
        self.btn_title  = Button(pygame.Rect(bx+(bw+12)*2, by, bw, bh), "🏠 MAIN MENU",  C_NEON_GOLD,  13)
        self.btn_quit   = Button(pygame.Rect(bx+(bw+12)*3, by, bw, bh), "✕ QUIT",        C_NEON_RED,   14)

        self.btn_again.on_click(self._play_again)
        self.btn_setup.on_click(go_setup)
        self.btn_title.on_click(go_title)
        self.btn_quit.on_click(quit_game)

        self._slide_y = SCREEN_H
        self._animating = True

        self._spots = [
            {"x": random.uniform(0, SCREEN_W), "y": random.uniform(0, SCREEN_H),
             "vx": random.uniform(-25,25), "vy": random.uniform(-15,15),
             "r": random.randint(50,100), "ph": random.uniform(0, math.pi*2)}
            for _ in range(4)
        ]

    def _play_again(self):
        self.bridge.reset()
        self.go_setup()

    # Stats helpers
    @property
    def _avg(self): return self.bridge.stats.avg_wait
    @property
    def _seated(self): return self.bridge.stats.total_seated
    @property
    def _arrived(self): return self.bridge.stats.total_arrived

    def _grade(self):
        a = self._avg
        if a < 5:  return "S", C_NEON_CYAN
        if a < 8:  return "A", C_NEON_GREEN
        if a < 10: return "B", C_NEON_GOLD
        if a < 13: return "C", C_WARN
        return "F", C_NEON_RED

    def _recommendation(self):
        a = self._avg
        nc = self.bridge.num_cashiers
        if a < 5:   return ("Excellent! Barely any wait.",
                            "Consider reducing staff to cut costs.", C_NEON_GREEN)
        if a < 10:  return ("Great job! Under the 10-min target.",
                            f"Config ({nc} cashiers) works well.", C_NEON_GOLD)
        if a < 15:  return ("Close! Just above 10-min threshold.",
                            "Try adding 1-2 more cashiers.", C_WARN)
        return ("Wait times too long — guests will leave!",
                "Increase cashier count (try 6+).", C_NEON_RED)

    def handle_event(self, evt):
        for b in (self.btn_again, self.btn_setup, self.btn_title, self.btn_quit):
            b.handle_event(evt)

    def update(self, dt):
        self._t += dt; self._reveal += dt
        if self._animating:
            self._slide_y = max(0, self._slide_y - 800*dt)
            if self._slide_y <= 0: self._animating = False

        # Fireworks if passed
        self._fw_timer += dt
        if self._avg < 10 and self._fw_timer > 0.5:
            self._fw_timer = 0
            self.particles.burst(random.uniform(80, SCREEN_W-80),
                                 random.uniform(60, SCREEN_H//2),
                                 count=16, speed=100, lifetime=1.0)
            self.particles.confetti(random.uniform(200, SCREEN_W-200),
                                    random.uniform(80, SCREEN_H//2))
        self.particles.update(dt)

        for sp in self._spots:
            sp["x"] += sp["vx"]*dt; sp["y"] += sp["vy"]*dt
            if sp["x"]<0 or sp["x"]>SCREEN_W: sp["vx"]*=-1
            if sp["y"]<0 or sp["y"]>SCREEN_H: sp["vy"]*=-1

        for b in (self.btn_again, self.btn_setup, self.btn_title, self.btn_quit):
            b.update(dt)

    def draw(self, surface):
        surface.fill(C_BG_DARK)

        # Spotlights
        for sp in self._spots:
            glow = pygame.Surface((sp["r"]*2, sp["r"]*2), pygame.SRCALPHA)
            a = int(8 + 8 * math.sin(self._t*1.5 + sp["ph"]))
            pygame.draw.circle(glow, (255,230,150,a), (sp["r"], sp["r"]), sp["r"])
            surface.blit(glow, (int(sp["x"]-sp["r"]), int(sp["y"]-sp["r"])))

        self.particles.draw(surface, type('C', (), {'world_to_screen': lambda s,x,y:(x,y)})())

        # Card
        card = self._card.move(0, int(self._slide_y))
        draw_panel(surface, card, C_NEON_GOLD, alpha=220, radius=14, width=3)

        # Perforations
        py = card.y + 64
        for dx in range(0, card.w, 12):
            pygame.draw.circle(surface, C_BG_DARK, (card.x+dx, py), 3)

        # Header
        draw_text(surface, "🎬  SIMULATION COMPLETE  🎬", self._tf, C_NEON_GOLD,
                  (card.centerx, card.y+32), centered=True)

        # Grade badge
        gr, gc = self._grade()
        br = pygame.Rect(card.right-82, card.y+74, 62, 62)
        pygame.draw.rect(surface, gc, br, border_radius=8)
        pygame.draw.rect(surface, C_TEXT_WHITE, br, 2, border_radius=8)
        draw_text(surface, gr, self._bf, C_BG_DARK, br.center, centered=True)

        # Stats (staggered reveal)
        sx, sy = card.x+28, py+18
        delay = 0.2
        def stat(label, value, color, idx):
            if self._reveal > idx*delay:
                a = min(255, int(255*(self._reveal-idx*delay)/0.4))
                ls = self._lf.render(label, True, C_TEXT_DIM); ls.set_alpha(a)
                vs = self._sf.render(value, True, color); vs.set_alpha(a)
                surface.blit(ls, (sx, sy+idx*42))
                surface.blit(vs, (sx+200, sy+idx*42-2))

        avg = self._avg
        wm, ws = int(avg), int((avg%1)*60)
        wc = C_GOOD if avg<10 else C_BAD

        stat("Moviegoers Arrived:", str(self._arrived), C_NEON_CYAN, 0)
        stat("Moviegoers Seated:", str(self._seated), C_NEON_GREEN, 1)
        stat("Average Wait Time:", f"{wm}m {ws:02d}s", wc, 2)
        stat("Target (≤10 min):", "✅ ACHIEVED" if avg<=10 else "❌ NOT MET",
             C_GOOD if avg<=10 else C_BAD, 3)

        # Staff summary
        ssy = sy + 42*4 + 10
        if self._reveal > 5*delay:
            pygame.draw.line(surface, C_PANEL_BORDER, (sx, ssy), (card.right-28, ssy))
            ssy += 12
            draw_text(surface, "Staff:", self._lf, C_TEXT_DIM, (sx, ssy))
            ssy += 20
            for txt, col in [
                (f"🎟 Cashiers: {self.bridge.num_cashiers}", C_NEON_GOLD),
                (f"🎫 Ushers: {self.bridge.num_ushers}",     C_NEON_PINK),
                (f"🍿 Servers: {self.bridge.num_servers}",   C_NEON_CYAN),
            ]:
                draw_text(surface, txt, self._sm, col, (sx, ssy)); sx += 170
            sx = card.x + 28

        # Recommendation
        ry = ssy + 40
        if self._reveal > 7*delay:
            pygame.draw.line(surface, C_PANEL_BORDER, (sx, ry), (card.right-28, ry))
            ry += 12
            l1, l2, rc = self._recommendation()
            draw_text(surface, "Manager's Report:", self._lf, C_TEXT_DIM, (sx, ry))
            ry += 20
            p = 0.85 + 0.15*math.sin(self._t*2)
            draw_text(surface, l1, self._lf, tuple(int(c*p) for c in rc[:3]), (sx, ry))
            ry += 18
            draw_text(surface, l2, self._sm, C_TEXT_DIM, (sx, ry))

        # Buttons
        off = int(self._slide_y)
        for b in (self.btn_again, self.btn_setup, self.btn_title, self.btn_quit):
            oy = b.rect.y; b.rect.y = oy+off
            b.draw(surface); b.rect.y = oy
