import pygame

from game.settings import (
    SCREEN_W, SCREEN_H, SCENARIOS,
    C_NEON_GOLD, C_NEON_PINK, C_NEON_CYAN, C_NEON_GREEN, C_TEXT_WHITE, C_TEXT_DIM,
)
from game.ui.button import Button, draw_panel, draw_text


def _font(name, size, bold=False):
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


class SimulationPanel:

    def __init__(self, bridge, on_apply):
        self.bridge = bridge
        self._on_apply = on_apply
        self.visible = False
        self._scenario_key: str | None = None
        self._title_font = _font("consolas", 24, bold=True)
        self._body_font = _font("consolas", 13)
        self._small_font = _font("consolas", 11)

        self.panel = pygame.Rect((SCREEN_W - 620) // 2, 42, 620, 565)
        x = self.panel.x + 28
        width = self.panel.width - 56
        self._scenario_rects: list[tuple[str, pygame.Rect]] = []
        for index, key in enumerate(SCENARIOS):
            self._scenario_rects.append((key, pygame.Rect(x, self.panel.y + 66 + index * 38, width, 32)))

        field_y = self.panel.y + 280
        self.cashiers = NumberInput(pygame.Rect(x, field_y, 250, 34), "Cashiers", 0, 9999,
                                    bridge.num_cashiers, C_NEON_GOLD)
        self.ushers = NumberInput(pygame.Rect(x + 310, field_y, 250, 34), "Ushers", 0, 9999,
                                  bridge.num_ushers, C_NEON_PINK)
        self.servers = NumberInput(pygame.Rect(x, field_y + 67, 250, 34), "Servers", 0, 9999,
                                   bridge.num_servers, C_NEON_CYAN)
        self.arrivals = NumberInput(pygame.Rect(x + 310, field_y + 67, 250, 34), "Arrival gap (sec)", 1, 9999,
                                    round(bridge.arrival_interval * 100), C_TEXT_WHITE)
        self.runtime = NumberInput(pygame.Rect(x, field_y + 134, 250, 34), "Runtime (minutes)", 1, 9999,
                                   bridge.runtime, C_TEXT_WHITE)
        self.food = NumberInput(pygame.Rect(x + 310, field_y + 134, 250, 34), "Food demand (%)", 0, 100,
                                round(bridge.food_prob * 100), C_NEON_CYAN)
        self.fields = [self.cashiers, self.ushers, self.servers, self.arrivals, self.runtime, self.food]

        btn_y = self.panel.bottom - 65
        self.apply_button = Button(
            pygame.Rect(self.panel.x + 32, btn_y, 260, 42),
            "APPLY CHANGES (LIVE)", C_NEON_GREEN, 13
        )
        self.apply_button.on_click(lambda: self.apply(reset=False))

        self.reset_button = Button(
            pygame.Rect(self.panel.x + 310, btn_y, 260, 42),
            "RESET SIMULATION", (180, 160, 205), 13
        )
        self.reset_button.on_click(lambda: self.apply(reset=True))

    def open(self):
        self.visible = True
        self._sync_from_bridge()

    def close(self):
        self.visible = False

    def _sync_from_bridge(self):
        b = self.bridge
        self.cashiers.value = b.num_cashiers
        self.ushers.value = b.num_ushers
        self.servers.value = b.num_servers
        self.arrivals.value = round(b.arrival_interval * 100)
        self.runtime.value = b.runtime
        self.food.value = round(b.food_prob * 100)

    def _select_scenario(self, key):
        config = SCENARIOS[key]
        self._scenario_key = key
        self.arrivals.value = round(config["arrival_interval"] * 100)
        self.food.value = round(config["food_prob"] * 100)
        self.runtime.value = config["runtime"]

    def apply(self, reset: bool = False):
        config = {
            "num_cashiers": self.cashiers.value,
            "num_ushers": self.ushers.value,
            "num_servers": self.servers.value,
            "arrival_interval": self.arrivals.value / 100.0,
            "food_prob": self.food.value / 100.0,
            "runtime": self.runtime.value,
            "speed": self.bridge.speed,
            "reset": reset,
        }
        self._on_apply(config)
        self.close()

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_F1):
            self.close()
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for key, rect in self._scenario_rects:
                if rect.collidepoint(event.pos):
                    self._select_scenario(key)
                    return True
        for field in self.fields:
            field.handle_event(event)
        self.apply_button.handle_event(event)
        self.reset_button.handle_event(event)
        return True


    def update(self, dt):
        if not self.visible:
            return
        self.apply_button.update(dt)
        self.reset_button.update(dt)

    def draw(self, surface):
        if not self.visible:
            return
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((5, 3, 15, 185))
        surface.blit(shade, (0, 0))
        draw_panel(surface, self.panel, C_NEON_GOLD, alpha=240, radius=12)
        draw_text(surface, "Simulation Parameters & Staffing", self._title_font, C_NEON_GOLD,
                  (self.panel.x + 20, self.panel.y + 17))
        draw_text(surface, "Select a preset or fine-tune staff in real-time.", self._small_font,
                  C_TEXT_DIM, (self.panel.x + 22, self.panel.y + 46))

        for key, rect in self._scenario_rects:
            config = SCENARIOS[key]
            selected = key == self._scenario_key
            fill = (91, 65, 142) if selected else (48, 35, 78)
            pygame.draw.rect(surface, fill, rect, border_radius=7)
            pygame.draw.rect(surface, C_NEON_GOLD if selected else (76, 57, 113), rect,
                             2 if selected else 1, border_radius=7)
            draw_text(surface, config["label"], self._body_font,
                      C_TEXT_WHITE if selected else (190, 178, 215), (rect.x + 13, rect.centery), centered=False)
            details = f"{round(config['arrival_interval'] * 100)}s gap • {config['food_prob']:.0%} food • {config['runtime']} min"
            detail = self._small_font.render(details, True, C_NEON_GOLD if selected else (150, 128, 190))
            surface.blit(detail, (rect.right - detail.get_width() - 12, rect.y + 10))

        pygame.draw.line(surface, (85, 65, 120), (self.panel.x + 28, self.panel.y + 260),
                         (self.panel.right - 28, self.panel.y + 260), 1)
        for field in self.fields:
            field.draw(surface)
        self.apply_button.draw(surface)
        self.reset_button.draw(surface)
        draw_text(surface, "[F1] Close", self._small_font, C_TEXT_DIM,
                  (self.panel.right - 120, self.panel.y + 20))


class NumberInput:

    def __init__(self, rect, label, min_value, max_value, value, color):
        self.rect = rect
        self.label = label
        self.min_value = int(min_value)
        self.max_value = int(max_value)
        self.color = color
        self._font = _font("consolas", 16, bold=True)
        self._label_font = _font("consolas", 13)
        self._text = str(int(float(value)))
        self.focused = False
        self._select_all = False

    @property
    def value(self):
        try:
            val = int(float(self._text))
            return max(self.min_value, min(self.max_value, val))
        except (ValueError, TypeError):
            return self.min_value

    @value.setter
    def value(self, val):
        self._text = str(int(max(self.min_value, min(self.max_value, float(val)))))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = self.rect.collidepoint(event.pos)
            if clicked and not self.focused:
                self._select_all = True
            elif not clicked and self.focused:
                self._text = str(self.value)
                self._select_all = False
            self.focused = clicked
            return self.focused

        if not self.focused or event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_BACKSPACE:
            if self._select_all:
                self._text = ""
                self._select_all = False
            else:
                self._text = self._text[:-1]
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
            self._text = str(self.value)
            self.focused = False
            self._select_all = False
        elif event.unicode.isdigit():
            if self._select_all or self._text == "0":
                self._text = event.unicode
                self._select_all = False
            elif len(self._text) < 4:
                self._text += event.unicode

            if len(self._text) > 1 and self._text.startswith("0"):
                self._text = str(int(self._text))

        return True

    def draw(self, surface):
        draw_text(surface, self.label, self._label_font, C_TEXT_DIM, (self.rect.x, self.rect.y - 18))
        pygame.draw.rect(surface, (38, 27, 64), self.rect, border_radius=6)
        pygame.draw.rect(surface, self.color if self.focused else (92, 70, 128), self.rect,
                         2 if self.focused else 1, border_radius=6)

        displayed = self._text if self._text else "0"
        text = self._font.render(displayed, True, self.color)
        surface.blit(text, (self.rect.x + 12, self.rect.centery - text.get_height() // 2))

        if self.focused and not self._select_all and (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = self.rect.x + 14 + text.get_width()
            pygame.draw.line(surface, self.color, (cx, self.rect.centery - 8), (cx, self.rect.centery + 8), 2)

        limit = self._label_font.render(f"{self.min_value}–{self.max_value}", True, C_TEXT_DIM)
        surface.blit(limit, (self.rect.right - limit.get_width() - 10,
                             self.rect.centery - limit.get_height() // 2))

