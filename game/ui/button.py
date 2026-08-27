"""
CinePlex Dreams — UI Widgets
Reusable Button, Slider, and StaffControl widgets.
"""
import pygame
import math
from game.settings import (
    C_BTN_BG, C_BTN_HOVER, C_BTN_ACTIVE, C_PANEL_BORDER,
    C_TEXT_WHITE, C_TEXT_DIM, C_NEON_GOLD, C_NEON_CYAN,
)


def _font(name, size, bold=False):
    try:    return pygame.font.SysFont(name, size, bold=bold)
    except: return pygame.font.Font(None, size)


def draw_panel(surface, rect, border_color=None, alpha=210, radius=8, width=2):
    bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    bg.fill((20, 15, 45, alpha))
    surface.blit(bg, rect.topleft)
    pygame.draw.rect(surface, border_color or C_PANEL_BORDER, rect, width, border_radius=radius)


def draw_text(surface, text, font, color, pos, centered=False, shadow=True):
    if shadow:
        sh = font.render(text, True, (0,0,0))
        r = sh.get_rect(center=pos) if centered else sh.get_rect(topleft=pos)
        surface.blit(sh, r.move(1,1))
    s = font.render(text, True, color)
    r = s.get_rect(center=pos) if centered else s.get_rect(topleft=pos)
    surface.blit(s, r)
    return r


class Button:
    def __init__(self, rect: pygame.Rect, text: str,
                 color=C_NEON_GOLD, font_size=16, radius=6):
        self.rect   = rect
        self.text   = text
        self.color  = color
        self.radius = radius
        self._font  = _font("consolas", font_size, bold=True)
        self._hov   = False
        self._press = False
        self._t     = 0.0
        self._cbs   = []

    def on_click(self, cb):
        self._cbs.append(cb); return self

    def handle_event(self, evt) -> bool:
        if evt.type == pygame.MOUSEMOTION:
            self._hov = self.rect.collidepoint(evt.pos)
        elif evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
            if self.rect.collidepoint(evt.pos): self._press = True
        elif evt.type == pygame.MOUSEBUTTONUP and evt.button == 1:
            if self._press and self.rect.collidepoint(evt.pos):
                self._press = False
                for cb in self._cbs: cb()
                return True
            self._press = False
        return False

    def update(self, dt): self._t += dt

    def draw(self, surface):
        if self._hov:
            glow = pygame.Surface((self.rect.w+8, self.rect.h+8), pygame.SRCALPHA)
            a = int(30 + 20*math.sin(self._t*5))
            glow.fill((*self.color[:3], a))
            surface.blit(glow, (self.rect.x-4, self.rect.y-4))
        bg = C_BTN_ACTIVE if self._press else (C_BTN_HOVER if self._hov else C_BTN_BG)
        pygame.draw.rect(surface, bg, self.rect, border_radius=self.radius)
        bc = self.color if self._hov else C_PANEL_BORDER
        pygame.draw.rect(surface, bc, self.rect, 2, border_radius=self.radius)
        tc = self.color if self._hov else C_TEXT_WHITE
        draw_text(surface, self.text, self._font, tc, self.rect.center, centered=True)


class Slider:
    def __init__(self, rect, label, min_val, max_val, value, color=C_NEON_CYAN):
        self.rect    = rect
        self.label   = label
        self.min_val = min_val
        self.max_val = max_val
        self.value   = value
        self.color   = color
        self._drag   = False
        self._lf     = _font("consolas", 13)
        self._vf     = _font("consolas", 16, bold=True)

    def handle_event(self, evt) -> bool:
        if evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
            if self.rect.collidepoint(evt.pos):
                self._drag = True; return self._set(evt.pos[0])
        elif evt.type == pygame.MOUSEBUTTONUP and evt.button == 1:
            self._drag = False
        elif evt.type == pygame.MOUSEMOTION and self._drag:
            return self._set(evt.pos[0])
        return False

    def _set(self, mx) -> bool:
        tx = self.rect.x + 10; tw = self.rect.w - 20
        t = max(0.0, min(1.0, (mx - tx) / tw))
        v = round(self.min_val + t * (self.max_val - self.min_val))
        if v != self.value: self.value = v; return True
        return False

    def draw(self, surface):
        draw_text(surface, self.label, self._lf, C_TEXT_DIM,
                  (self.rect.x, self.rect.y - 18))
        tr = pygame.Rect(self.rect.x+10, self.rect.centery-2, self.rect.w-20, 4)
        pygame.draw.rect(surface, (50,40,70), tr, border_radius=2)
        t = (self.value-self.min_val)/max(1, self.max_val-self.min_val)
        fw = int(tr.w * t)
        if fw > 0:
            pygame.draw.rect(surface, self.color,
                             pygame.Rect(tr.x, tr.y, fw, 4), border_radius=2)
        hx = tr.x + fw
        pygame.draw.circle(surface, self.color, (hx, self.rect.centery), 8)
        pygame.draw.circle(surface, C_TEXT_WHITE, (hx, self.rect.centery), 5)
        draw_text(surface, str(self.value), self._vf, self.color,
                  (self.rect.right-24, self.rect.centery), centered=False)
