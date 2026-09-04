"""
RPG-inspired dialog system for theater interactions.
Inspired by Undertale, Stardew Valley, Pokémon, and Persona 5 UI styles.
"""
import pygame
import math
import random
from typing import Callable, Any, List, Tuple, Optional
from game.settings import (
    C_PANEL_BG, C_PANEL_BORDER, C_TEXT_WHITE, C_TEXT_GOLD, C_TEXT_DIM,
    C_BTN_BG, C_BTN_HOVER, C_BTN_ACTIVE, C_GOOD, C_BAD, SCREEN_W, SCREEN_H,
    MOVIES, CONCESSION_ITEMS,
    C_DIALOG_BG_TOP, C_DIALOG_BG_BOT, C_DIALOG_BORDER_OUT,
    C_DIALOG_BORDER_IN, C_DIALOG_ORNAMENT, C_CURSOR_ARROW,
    C_NEON_GOLD, C_NEON_CYAN, C_NEON_GREEN, C_NEON_RED, C_NEON_PINK,
)


def _font(size, bold=False):
    try:
        return pygame.font.SysFont("consolas", size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


# ─── Drawing helpers for the RPG ornamental frame ───────────────────


def _draw_gradient_rect(surface: pygame.Surface, rect: pygame.Rect,
                        color_top: Tuple, color_bot: Tuple, alpha: int = 230):
    """Draw a vertical gradient rectangle."""
    grad = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    for y in range(rect.height):
        t = y / max(1, rect.height - 1)
        r = int(color_top[0] + (color_bot[0] - color_top[0]) * t)
        g = int(color_top[1] + (color_bot[1] - color_top[1]) * t)
        b = int(color_top[2] + (color_bot[2] - color_top[2]) * t)
        pygame.draw.line(grad, (r, g, b, alpha), (0, y), (rect.width, y))
    surface.blit(grad, rect.topleft)


def _draw_ornamental_border(surface: pygame.Surface, rect: pygame.Rect,
                            outer_color=C_DIALOG_BORDER_OUT,
                            inner_color=C_DIALOG_BORDER_IN,
                            ornament_color=C_DIALOG_ORNAMENT):
    """Draw a double-line border with decorative corner flourishes."""
    x, y, w, h = rect.x, rect.y, rect.width, rect.height

    # Outer border
    pygame.draw.rect(surface, outer_color, rect, 3, border_radius=4)
    # Inner border (inset by 5px)
    inner = pygame.Rect(x + 5, y + 5, w - 10, h - 10)
    pygame.draw.rect(surface, inner_color, inner, 1, border_radius=3)

    # Corner flourishes — small L-shaped ornaments
    corner_len = 14
    ct = 2  # thickness
    corners = [
        # top-left
        ((x + 2, y + 2), (x + 2 + corner_len, y + 2), (x + 2, y + 2 + corner_len)),
        # top-right
        ((x + w - 3, y + 2), (x + w - 3 - corner_len, y + 2), (x + w - 3, y + 2 + corner_len)),
        # bottom-left
        ((x + 2, y + h - 3), (x + 2 + corner_len, y + h - 3), (x + 2, y + h - 3 - corner_len)),
        # bottom-right
        ((x + w - 3, y + h - 3), (x + w - 3 - corner_len, y + h - 3), (x + w - 3, y + h - 3 - corner_len)),
    ]
    for center, h_end, v_end in corners:
        pygame.draw.line(surface, ornament_color, center, h_end, ct)
        pygame.draw.line(surface, ornament_color, center, v_end, ct)

    # Small diamond at each corner
    for cx, cy in [(x + 2, y + 2), (x + w - 3, y + 2),
                   (x + 2, y + h - 3), (x + w - 3, y + h - 3)]:
        pts = [(cx, cy - 3), (cx + 3, cy), (cx, cy + 3), (cx - 3, cy)]
        pygame.draw.polygon(surface, ornament_color, pts)


def _draw_golden_divider(surface: pygame.Surface, x: int, y: int,
                         width: int, color=C_DIALOG_ORNAMENT):
    """Draw an ornate golden divider line with a diamond in the center."""
    cx = x + width // 2
    # Left line
    pygame.draw.line(surface, color, (x + 8, y), (cx - 10, y), 1)
    # Right line
    pygame.draw.line(surface, color, (cx + 10, y), (x + width - 8, y), 1)
    # Center diamond
    pts = [(cx, y - 4), (cx + 5, y), (cx, y + 4), (cx - 5, y)]
    pygame.draw.polygon(surface, color, pts)
    # Small dots beside diamond
    pygame.draw.circle(surface, color, (cx - 12, y), 2)
    pygame.draw.circle(surface, color, (cx + 12, y), 2)


def _draw_bouncing_cursor(surface: pygame.Surface, x: int, y: int,
                          time_val: float, color=C_CURSOR_ARROW):
    """Draw a bouncing ▶ arrow cursor (Undertale-inspired)."""
    offset = int(4 * math.sin(time_val * 6.0))
    ax = x + offset
    # Triangle arrow
    pts = [(ax, y - 6), (ax + 10, y), (ax, y + 6)]
    pygame.draw.polygon(surface, color, pts)
    # Subtle glow behind
    glow_surf = pygame.Surface((20, 16), pygame.SRCALPHA)
    pygame.draw.polygon(glow_surf, (*color[:3], 60),
                        [(2, 2), (16, 8), (2, 14)])
    surface.blit(glow_surf, (ax - 4, y - 8))


# ─── Sparkle / particle helpers ────────────────────────────────────


class _Sparkle:
    __slots__ = ('x', 'y', 'life', 'max_life', 'size', 'color', 'vx', 'vy')

    def __init__(self, x, y, color=(255, 255, 200)):
        self.x = x
        self.y = y
        self.life = random.uniform(0.4, 0.9)
        self.max_life = self.life
        self.size = random.uniform(1.5, 3.5)
        self.color = color
        self.vx = random.uniform(-25, 25)
        self.vy = random.uniform(-40, -10)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / self.max_life))
        s = max(1, int(self.size * (self.life / self.max_life)))
        glow = pygame.Surface((s * 4, s * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color[:3], alpha), (s * 2, s * 2), s)
        pygame.draw.circle(glow, (*self.color[:3], alpha // 3), (s * 2, s * 2), s * 2)
        surface.blit(glow, (int(self.x) - s * 2, int(self.y) - s * 2))


# ─── Base DialogMenu (RPG-style) ───────────────────────────────────


class DialogMenu:
    """
    RPG-style dialog box with ornamental double-borders,
    gradient background, bouncing arrow cursor, and footer hints.
    """

    def __init__(self, title: str, items: list[dict], on_select: Callable[[Any], None],
                 icon_emoji: str = "", accent_color: Tuple = C_NEON_GOLD):
        self.title = title
        self.items = items
        self.on_select = on_select
        self.icon_emoji = icon_emoji
        self.accent_color = accent_color

        self.active = False
        self.selected_idx = 0
        self._anim_t = 0.0
        self._cursor_t = 0.0
        self._sparkles: List[_Sparkle] = []
        self._prev_idx = -1

        self.font_title = _font(22, bold=True)
        self.font_item = _font(17, bold=True)
        self.font_desc = _font(13)
        self.font_hint = _font(11)

        self.width = 440
        self.item_h = 56
        self.padding = 22
        self.header_h = 60
        self.footer_h = 32
        self.height = (self.header_h + (len(self.items) * self.item_h)
                       + self.padding * 2 + self.footer_h)

        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (SCREEN_W // 2, SCREEN_H // 2)

    def open(self):
        self.active = True
        self.selected_idx = 0
        self._anim_t = 0.0
        self._cursor_t = 0.0
        self._prev_idx = -1
        self._sparkles.clear()

    def close(self):
        self.active = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.active:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._prev_idx = self.selected_idx
                self.selected_idx = (self.selected_idx - 1) % len(self.items)
                self._on_selection_change()
                return True
            elif event.key == pygame.K_DOWN:
                self._prev_idx = self.selected_idx
                self.selected_idx = (self.selected_idx + 1) % len(self.items)
                self._on_selection_change()
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.on_select(self.items[self.selected_idx])
                self.close()
                return True
            elif event.key == pygame.K_ESCAPE:
                self.close()
                return True

        return False

    def _on_selection_change(self):
        """Spawn sparkles when cursor moves."""
        start_y = self.padding + self.header_h
        iy = start_y + self.selected_idx * self.item_h
        sx = self.rect.x + self.padding + 8
        sy = self.rect.y + iy + self.item_h // 2
        for _ in range(5):
            self._sparkles.append(_Sparkle(sx, sy, self.accent_color))

    def update(self, dt: float):
        if self.active:
            self._anim_t += dt * 4.5
            self._anim_t = min(1.0, self._anim_t)
            self._cursor_t += dt

            alive = []
            for sp in self._sparkles:
                sp.update(dt)
                if sp.life > 0:
                    alive.append(sp)
            self._sparkles = alive

    def draw(self, surface: pygame.Surface):
        if not self.active or self._anim_t <= 0:
            return

        t = self._anim_t
        # Overshoot spring ease: goes past 1.0 then settles
        if t < 1.0:
            ease = 1.0 - (1.0 - t) ** 3
            ease = ease * (1.0 + 0.12 * math.sin(t * math.pi))
        else:
            ease = 1.0

        # Dark overlay
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(170 * min(1.0, ease))))
        surface.blit(overlay, (0, 0))

        # Build panel at full size, then scale for animation
        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        panel_rect = pygame.Rect(0, 0, self.width, self.height)

        # Gradient background
        _draw_gradient_rect(panel, panel_rect, C_DIALOG_BG_TOP, C_DIALOG_BG_BOT, 235)

        # Ornamental double-border
        _draw_ornamental_border(panel, panel_rect,
                                ornament_color=self.accent_color)

        # ── Header ──
        hx = self.padding + 4
        hy = self.padding

        # Icon area (colored square)
        icon_rect = pygame.Rect(hx, hy, 30, 30)
        pygame.draw.rect(panel, (*self.accent_color[:3],), icon_rect, border_radius=5)
        pygame.draw.rect(panel, (255, 255, 255), icon_rect, 1, border_radius=5)
        # Draw icon emoji as text if available
        if self.icon_emoji:
            icon_surf = self.font_item.render(self.icon_emoji, True, (20, 15, 40))
            panel.blit(icon_surf, (hx + 15 - icon_surf.get_width() // 2,
                                   hy + 15 - icon_surf.get_height() // 2))

        # Title text
        title_surf = self.font_title.render(self.title, True, self.accent_color)
        panel.blit(title_surf, (hx + 38, hy + 4))

        # Golden divider under header
        div_y = hy + 40
        _draw_golden_divider(panel, self.padding, div_y,
                             self.width - self.padding * 2, self.accent_color)

        # ── Items ──
        start_y = self.padding + self.header_h
        for i, item in enumerate(self.items):
            iy = start_y + i * self.item_h
            irect = pygame.Rect(self.padding + 2, iy,
                                self.width - self.padding * 2 - 4, self.item_h - 6)

            is_sel = (i == self.selected_idx)

            if is_sel:
                # Highlighted row — glowing background
                glow_surf = pygame.Surface((irect.width, irect.height), pygame.SRCALPHA)
                pulse = 0.7 + 0.3 * math.sin(self._cursor_t * 4.0)
                ga = int(45 * pulse)
                glow_surf.fill((*self.accent_color[:3], ga))
                panel.blit(glow_surf, irect.topleft)
                pygame.draw.rect(panel, self.accent_color, irect, 1, border_radius=6)

                # Bouncing arrow cursor
                _draw_bouncing_cursor(panel, irect.x + 6,
                                      irect.y + irect.height // 2,
                                      self._cursor_t, self.accent_color)
            else:
                # Subtle dim row background
                dim_surf = pygame.Surface((irect.width, irect.height), pygame.SRCALPHA)
                dim_surf.fill((40, 30, 70, 35))
                panel.blit(dim_surf, irect.topleft)

            # Draw item content (subclasses override)
            item_x = irect.x + (24 if is_sel else 12)
            item_y = irect.y + 8
            self.draw_item(panel, item, item_x, item_y, is_sel)

        # ── Footer hint ──
        footer_y = self.height - self.footer_h
        pygame.draw.line(panel, C_DIALOG_BORDER_IN,
                         (self.padding + 8, footer_y),
                         (self.width - self.padding - 8, footer_y), 1)
        hint_text = "[↑↓] Navigate    [SPACE] Select    [ESC] Close"
        hint_surf = self.font_hint.render(hint_text, True, (120, 110, 150))
        panel.blit(hint_surf, (self.width // 2 - hint_surf.get_width() // 2,
                               footer_y + 8))

        # ── Scale & blit panel ──
        pw = int(self.width * ease)
        ph = int(self.height * ease)
        if pw > 0 and ph > 0:
            scaled = pygame.transform.smoothscale(panel, (pw, ph))
            rect = scaled.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
            surface.blit(scaled, rect)

            # Draw sparkles on top (in screen space)
            offset_x = rect.x - self.rect.x
            offset_y = rect.y - self.rect.y
            for sp in self._sparkles:
                sp.draw(surface)

    def draw_item(self, surface: pygame.Surface, item: dict,
                  x: int, y: int, is_selected: bool):
        """Override in subclasses for custom item rendering."""
        pass


# ─── Ticket Dialog ──────────────────────────────────────────────────


class TicketDialog(DialogMenu):
    """Movie selection dialog with film reel icons and RPG styling."""

    def __init__(self, on_select: Callable[[dict], None]):
        super().__init__("SELECT A MOVIE", MOVIES, on_select,
                         icon_emoji="🎬", accent_color=C_NEON_GOLD)

    def draw_item(self, surface, item, x, y, is_selected):
        color = C_TEXT_WHITE if is_selected else C_TEXT_DIM

        # Film reel icon (small circles)
        reel_x = x + 2
        reel_y = y + 10
        reel_col = self.accent_color if is_selected else (100, 90, 130)
        pygame.draw.circle(surface, reel_col, (reel_x, reel_y), 8, 2)
        pygame.draw.circle(surface, reel_col, (reel_x, reel_y), 3)
        # Sprocket holes
        for angle in range(0, 360, 90):
            sx = reel_x + int(5 * math.cos(math.radians(angle)))
            sy = reel_y + int(5 * math.sin(math.radians(angle)))
            pygame.draw.circle(surface, reel_col, (sx, sy), 1)

        # Movie title
        t_surf = self.font_item.render(item["title"], True, color)
        surface.blit(t_surf, (x + 18, y))

        # Screen & time info — right-aligned
        info = f"Screen {item['screen']}  •  {item['time']}"
        i_color = C_TEXT_GOLD if is_selected else (100, 90, 130)
        i_surf = self.font_desc.render(info, True, i_color)
        surface.blit(i_surf, (x + 18, y + 22))


# ─── Concession Dialog ──────────────────────────────────────────────


class ConcessionDialog(DialogMenu):
    """Snack menu with emoji icons, coin badges for prices."""

    def __init__(self, on_select: Callable[[dict], None]):
        items = list(CONCESSION_ITEMS)
        items.append({"name": "No Thanks", "price": "", "emoji": "👋"})
        super().__init__("CONCESSION STAND", items, on_select,
                         icon_emoji="🍿", accent_color=C_NEON_CYAN)

    def draw_item(self, surface, item, x, y, is_selected):
        color = C_TEXT_WHITE if is_selected else C_TEXT_DIM

        # Item name (already has emoji in the name for concession items)
        t_surf = self.font_item.render(item["name"], True, color)
        surface.blit(t_surf, (x + 4, y + 4))

        # Price in a coin badge
        if item.get("price"):
            price_text = item["price"]
            p_surf = self.font_item.render(price_text, True, (40, 30, 15))
            pw = p_surf.get_width() + 16
            ph = p_surf.get_height() + 6

            bx = self.width - self.padding * 2 - pw - 20
            by = y + 2

            # Gold coin background
            coin_rect = pygame.Rect(bx, by, pw, ph)
            badge_color = C_NEON_GOLD if is_selected else (160, 140, 80)
            pygame.draw.rect(surface, badge_color, coin_rect, border_radius=10)
            pygame.draw.rect(surface, (255, 245, 200), coin_rect, 1, border_radius=10)

            surface.blit(p_surf, (bx + 8, by + 3))


# ─── Usher Dialog (Dramatic Ticket Scan) ────────────────────────────


class UsherDialog:
    """
    Dramatic ticket validation animation inspired by Persona 5 transitions.
    Features a large animated ticket graphic, scan line, and result reveal.
    """

    def __init__(self, on_complete: Callable[[], None],
                 on_rejected: Callable[[], None]):
        self.on_complete = on_complete
        self.on_rejected = on_rejected
        self.active = False
        self._t = 0.0
        self.ticket_is_valid = False

        self.font_lg = _font(26, bold=True)
        self.font_md = _font(18, bold=True)
        self.font_sm = _font(13)
        self.font_status = _font(36, bold=True)

        self.width = 380
        self.height = 300
        self._sparkles: List[_Sparkle] = []
        self._result_shown = False
        self._shake_x = 0.0
        self._shake_y = 0.0

    def open(self, ticket_is_valid: bool):
        self.active = True
        self._t = 0.0
        self.ticket_is_valid = ticket_is_valid
        self._sparkles.clear()
        self._result_shown = False

    def close(self):
        self.active = False

    def update(self, dt: float):
        if not self.active:
            return
        self._t += dt

        # Spawn sparkles during result reveal
        if 1.4 < self._t < 1.8 and not self._result_shown:
            self._result_shown = True
            cx = SCREEN_W // 2
            cy = SCREEN_H // 2
            color = C_NEON_GREEN if self.ticket_is_valid else C_NEON_RED
            for _ in range(20):
                sp = _Sparkle(cx + random.randint(-40, 40),
                              cy + random.randint(-20, 20), color)
                sp.vy = random.uniform(-60, -20)
                sp.vx = random.uniform(-40, 40)
                self._sparkles.append(sp)

        # Shake on rejection
        if not self.ticket_is_valid and 1.4 < self._t < 2.0:
            self._shake_x = random.uniform(-4, 4) * max(0, 1 - (self._t - 1.4) / 0.6)
            self._shake_y = random.uniform(-3, 3) * max(0, 1 - (self._t - 1.4) / 0.6)
        else:
            self._shake_x = 0
            self._shake_y = 0

        for sp in self._sparkles:
            sp.update(dt)
        self._sparkles = [sp for sp in self._sparkles if sp.life > 0]

        if self._t >= 2.5:
            if self.ticket_is_valid:
                self.on_complete()
            else:
                self.on_rejected()
            self.close()

    def handle_event(self, event):
        return self.active

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return

        # Dark overlay
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        # Panel
        px = SCREEN_W // 2 - self.width // 2 + int(self._shake_x)
        py = SCREEN_H // 2 - self.height // 2 + int(self._shake_y)
        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        panel_rect = pygame.Rect(0, 0, self.width, self.height)

        _draw_gradient_rect(panel, panel_rect, C_DIALOG_BG_TOP, C_DIALOG_BG_BOT, 240)

        # Border changes color based on phase
        if self._t < 1.4:
            border_col = C_DIALOG_BORDER_OUT
            ornament_col = C_NEON_GOLD
        elif self.ticket_is_valid:
            border_col = C_NEON_GREEN
            ornament_col = C_NEON_GREEN
        else:
            border_col = C_NEON_RED
            ornament_col = C_NEON_RED

        _draw_ornamental_border(panel, panel_rect, border_col, C_DIALOG_BORDER_IN,
                                ornament_col)

        # ── Header ──
        header_text = "TICKET VERIFICATION"
        h_surf = self.font_md.render(header_text, True, C_NEON_GOLD)
        panel.blit(h_surf, (self.width // 2 - h_surf.get_width() // 2, 18))

        _draw_golden_divider(panel, 20, 46, self.width - 40, C_NEON_GOLD)

        # ── Ticket graphic ──
        ticket_w, ticket_h = 200, 80
        tx = self.width // 2 - ticket_w // 2
        ty = 65

        # Ticket body
        ticket_color = (240, 230, 200) if self._t < 1.4 else (
            (200, 255, 210) if self.ticket_is_valid else (255, 200, 200))
        pygame.draw.rect(panel, ticket_color,
                         (tx, ty, ticket_w, ticket_h), border_radius=8)
        pygame.draw.rect(panel, (180, 160, 120),
                         (tx, ty, ticket_w, ticket_h), 2, border_radius=8)

        # Perforated edge (dashed vertical line)
        perf_x = tx + ticket_w - 50
        for dy in range(0, ticket_h, 6):
            pygame.draw.line(panel, (180, 160, 120),
                             (perf_x, ty + dy), (perf_x, ty + dy + 3), 1)

        # Ticket text
        t_title = self.font_sm.render("ADMIT ONE", True, (80, 60, 40))
        panel.blit(t_title, (tx + 12, ty + 8))
        t_movie = self.font_sm.render("Starlight Express", True, (60, 40, 25))
        panel.blit(t_movie, (tx + 12, ty + 26))
        t_seat = self.font_sm.render("Screen 1 • 7:30 PM", True, (100, 80, 60))
        panel.blit(t_seat, (tx + 12, ty + 44))

        # Stub section
        stub_text = self.font_sm.render("STUB", True, (100, 80, 60))
        panel.blit(stub_text, (perf_x + 10, ty + 30))

        # ── Scan line animation ──
        if self._t < 1.4:
            scan_pct = (self._t % 0.7) / 0.7
            scan_y = ty + int(ticket_h * scan_pct)
            scan_surf = pygame.Surface((ticket_w, 3), pygame.SRCALPHA)
            scan_surf.fill((*C_NEON_CYAN[:3], 200))
            panel.blit(scan_surf, (tx, scan_y))
            # Glow around scan line
            glow_h = 12
            scan_glow = pygame.Surface((ticket_w, glow_h), pygame.SRCALPHA)
            scan_glow.fill((*C_NEON_CYAN[:3], 40))
            panel.blit(scan_glow, (tx, scan_y - glow_h // 2))

        # ── Status message ──
        if self._t < 1.2:
            msg = "Scanning Ticket..."
            msg_color = C_TEXT_WHITE
            # Animated dots
            dots = "." * (int(self._t * 3) % 4)
            msg = f"Scanning Ticket{dots}"
        elif self._t < 1.5:
            msg = "Processing..."
            msg_color = C_NEON_CYAN
        elif self.ticket_is_valid:
            msg = "✓  VALID"
            msg_color = C_NEON_GREEN
        else:
            msg = "✗  NO TICKET"
            msg_color = C_NEON_RED

        msg_surf = self.font_lg.render(msg, True, msg_color)
        panel.blit(msg_surf, (self.width // 2 - msg_surf.get_width() // 2, 165))

        # ── Progress bar ──
        bar_w = 240
        bar_h = 14
        bx = self.width // 2 - bar_w // 2
        by = 205

        # Bar track
        pygame.draw.rect(panel, (40, 30, 60), (bx, by, bar_w, bar_h), border_radius=7)

        if self._t < 1.4:
            pct = min(1.0, self._t / 1.4)
            bar_color = C_NEON_CYAN
        elif self.ticket_is_valid:
            pct = 1.0
            bar_color = C_NEON_GREEN
        else:
            pct = 1.0
            bar_color = C_NEON_RED

        fill_w = int(bar_w * pct)
        if fill_w > 0:
            # Segmented progress bar (retro loading style)
            seg_w = 8
            seg_gap = 2
            filled_x = bx
            while filled_x < bx + fill_w - seg_gap:
                sw = min(seg_w, bx + fill_w - filled_x)
                pygame.draw.rect(panel, bar_color,
                                 (filled_x, by, sw, bar_h), border_radius=2)
                filled_x += seg_w + seg_gap

        # Bar border
        pygame.draw.rect(panel, (100, 90, 130),
                         (bx, by, bar_w, bar_h), 1, border_radius=7)

        # ── Sub-message ──
        if self._t >= 1.5:
            if self.ticket_is_valid:
                sub = "Welcome! Enjoy your movie."
                sub_col = (160, 255, 190)
            else:
                sub = "Please purchase a ticket first."
                sub_col = (255, 160, 160)
            sub_surf = self.font_sm.render(sub, True, sub_col)
            panel.blit(sub_surf, (self.width // 2 - sub_surf.get_width() // 2, 232))

        # ── Footer ──
        _draw_golden_divider(panel, 20, self.height - 35,
                             self.width - 40, ornament_col)
        status_text = "Please wait..." if self._t < 1.5 else "Proceeding..."
        st_surf = self.font_sm.render(status_text, True, (120, 110, 150))
        panel.blit(st_surf, (self.width // 2 - st_surf.get_width() // 2,
                             self.height - 24))

        # Scale in animation for first 0.3s
        if self._t < 0.3:
            scale = self._t / 0.3
            scale = 1.0 - (1.0 - scale) ** 3  # ease out cubic
            scale = scale * (1.0 + 0.08 * math.sin(scale * math.pi))
            sw = max(1, int(self.width * scale))
            sh = max(1, int(self.height * scale))
            panel = pygame.transform.smoothscale(panel, (sw, sh))
            px = SCREEN_W // 2 - sw // 2 + int(self._shake_x)
            py = SCREEN_H // 2 - sh // 2 + int(self._shake_y)

        surface.blit(panel, (px, py))

        # Sparkles on top
        for sp in self._sparkles:
            sp.draw(surface)
