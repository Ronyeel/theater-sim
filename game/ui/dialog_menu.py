import pygame
import math
from typing import Callable, Any
from game.settings import (
    C_PANEL_BG, C_PANEL_BORDER, C_TEXT_WHITE, C_TEXT_GOLD, C_TEXT_DIM,
    C_BTN_BG, C_BTN_HOVER, C_BTN_ACTIVE, C_GOOD, C_BAD, SCREEN_W, SCREEN_H,
    MOVIES, CONCESSION_ITEMS
)

def _font(size, bold=False):
    return pygame.font.SysFont("consolas", size, bold=bold)


class DialogMenu:
    def __init__(self, title: str, items: list[dict], on_select: Callable[[Any], None]):
        self.title = title
        self.items = items
        self.on_select = on_select

        self.active = False
        self.selected_idx = 0
        self._anim_t = 0.0

        self.font_title = _font(24, bold=True)
        self.font_item = _font(18)
        self.font_desc = _font(14)

        self.width = 400
        self.item_h = 60
        self.padding = 20
        self.header_h = 50
        self.height = self.header_h + (len(self.items) * self.item_h) + self.padding * 2

        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (SCREEN_W // 2, SCREEN_H // 2)

    def open(self):
        self.active = True
        self.selected_idx = 0
        self._anim_t = 0.0

    def close(self):
        self.active = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.active:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_idx = (self.selected_idx - 1) % len(self.items)
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_idx = (self.selected_idx + 1) % len(self.items)
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.on_select(self.items[self.selected_idx])
                self.close()
                return True
            elif event.key == pygame.K_ESCAPE:
                self.close()
                return True

        return False

    def update(self, dt: float):
        if self.active:
            self._anim_t += dt * 5.0
            self._anim_t = min(1.0, self._anim_t)

    def draw(self, surface: pygame.Surface):
        if not self.active or self._anim_t <= 0:
            return

        t = self._anim_t
        ease = 1.0 - (1.0 - t) * (1.0 - t) * (1.0 - t)

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(150 * ease)))

        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, C_PANEL_BG, panel.get_rect(), border_radius=12)
        pygame.draw.rect(panel, C_PANEL_BORDER, panel.get_rect(), 2, border_radius=12)

        title_surf = self.font_title.render(self.title, True, C_TEXT_GOLD)
        panel.blit(title_surf, (self.padding, self.padding))
        pygame.draw.line(panel, C_PANEL_BORDER, 
                         (self.padding, self.padding + 35), 
                         (self.width - self.padding, self.padding + 35))

        start_y = self.padding + self.header_h
        for i, item in enumerate(self.items):
            iy = start_y + i * self.item_h
            irect = pygame.Rect(self.padding, iy, self.width - self.padding*2, self.item_h - 10)

            is_sel = (i == self.selected_idx)
            bg_color = C_BTN_ACTIVE if is_sel else C_BTN_BG

            pulse = 0
            if is_sel:
                pulse = int(10 * math.sin(pygame.time.get_ticks() * 0.005))
                bg_color = (max(0, min(255, bg_color[0] + pulse)),
                            max(0, min(255, bg_color[1] + pulse)),
                            max(0, min(255, bg_color[2] + pulse)))

            pygame.draw.rect(panel, bg_color, irect, border_radius=8)
            if is_sel:
                pygame.draw.rect(panel, C_TEXT_GOLD, irect, 2, border_radius=8)

            self.draw_item(panel, item, irect.x + 15, irect.y + 12, is_sel)

        pw = int(self.width * ease)
        ph = int(self.height * ease)
        if pw > 0 and ph > 0:
            scaled = pygame.transform.smoothscale(panel, (pw, ph))
            rect = scaled.get_rect(center=(SCREEN_W//2, SCREEN_H//2))
            overlay.blit(scaled, rect)

        surface.blit(overlay, (0, 0))

    def draw_item(self, surface: pygame.Surface, item: dict, x: int, y: int, is_selected: bool):
        pass


class TicketDialog(DialogMenu):
    def __init__(self, on_select: Callable[[dict], None]):
        super().__init__("Select a Movie", MOVIES, on_select)

    def draw_item(self, surface, item, x, y, is_selected):
        color = C_TEXT_WHITE if is_selected else C_TEXT_DIM

        t_surf = self.font_item.render(item["title"], True, color)
        surface.blit(t_surf, (x, y))

        info = f"Screen {item['screen']} • {item['time']}"
        i_surf = self.font_desc.render(info, True, C_TEXT_GOLD if is_selected else C_PANEL_BORDER)
        surface.blit(i_surf, (self.width - self.padding - 30 - i_surf.get_width(), y + 3))


class ConcessionDialog(DialogMenu):
    def __init__(self, on_select: Callable[[dict], None]):
        items = list(CONCESSION_ITEMS)
        items.append({"name": "No Thanks", "price": ""})
        super().__init__("Concession Stand", items, on_select)

    def draw_item(self, surface, item, x, y, is_selected):
        color = C_TEXT_WHITE if is_selected else C_TEXT_DIM
        t_surf = self.font_item.render(item["name"], True, color)
        surface.blit(t_surf, (x, y))

        if item["price"]:
            p_surf = self.font_item.render(item["price"], True, C_GOOD if is_selected else C_TEXT_DIM)
            surface.blit(p_surf, (self.width - self.padding - 30 - p_surf.get_width(), y))


class UsherDialog:
    def __init__(self, on_complete: Callable[[], None], on_rejected: Callable[[], None]):
        self.on_complete = on_complete
        self.on_rejected = on_rejected
        self.active = False
        self._t = 0.0
        self.ticket_is_valid = False

        self.font_lg = _font(28, bold=True)
        self.font_sm = _font(16)

        self.width = 300
        self.height = 200

    def open(self, ticket_is_valid: bool):
        self.active = True
        self._t = 0.0
        self.ticket_is_valid = ticket_is_valid

    def close(self):
        self.active = False

    def update(self, dt: float):
        if not self.active: return
        self._t += dt
        if self._t >= 2.0:
            if self.ticket_is_valid:
                self.on_complete()
            else:
                self.on_rejected()
            self.close()

    def handle_event(self, event):
        return self.active

    def draw(self, surface: pygame.Surface):
        if not self.active: return

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))

        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, C_PANEL_BG, panel.get_rect(), border_radius=12)
        pygame.draw.rect(panel, C_PANEL_BORDER, panel.get_rect(), 2, border_radius=12)

        if self._t < 1.5:
            msg, color = "Scanning Ticket...", C_TEXT_WHITE
        elif self.ticket_is_valid:
            msg, color = "Ticket Valid!", C_GOOD
        else:
            msg, color = "No Ticket Found!", C_BAD

        msg_surf = self.font_lg.render(msg, True, color)
        panel.blit(msg_surf, (self.width//2 - msg_surf.get_width()//2, 40))

        bar_w = 200
        bar_h = 20
        bx = self.width//2 - bar_w//2
        by = 100

        pygame.draw.rect(panel, C_BTN_BG, (bx, by, bar_w, bar_h), border_radius=10)

        if self._t < 1.5:
            pct = min(1.0, self._t / 1.5)
            pygame.draw.rect(panel, C_TEXT_GOLD, (bx, by, int(bar_w * pct), bar_h), border_radius=10)
        elif self.ticket_is_valid:
            pygame.draw.rect(panel, C_GOOD, (bx, by, bar_w, bar_h), border_radius=10)
        else:
            pygame.draw.rect(panel, C_BAD, (bx, by, bar_w, bar_h), border_radius=10)

        rect = panel.get_rect(center=(SCREEN_W//2, SCREEN_H//2))
        overlay.blit(panel, rect)
        surface.blit(overlay, (0, 0))
