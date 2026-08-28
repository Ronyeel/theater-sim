
from typing import Callable, List, Tuple, Optional
import math
import random
import pygame
from game.settings import (
    SCREEN_W, SCREEN_H, C_BG_DARK, C_NEON_GOLD, C_NEON_PINK,
    C_NEON_CYAN, C_TEXT_WHITE, C_TEXT_DIM, SCENARIOS,
)
from game.ui.button import Button, draw_text, draw_panel
from game.ui.simulation_panel import NumberInput


def _get_font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


class SetupScreen:

    def __init__(self, bridge, go_game: Callable[[], None], go_back: Optional[Callable[[], None]] = None) -> None:
        self.bridge = bridge
        self.go_game = go_game
        self.go_back = go_back
        self._t = 0.0
        self._scenario_key: Optional[str] = "normal"

        self._title_font = _get_font("consolas", 24, bold=True)
        self._body_font = _get_font("consolas", 13)
        self._small_font = _get_font("consolas", 11)

        self.panel = pygame.Rect((SCREEN_W - 680) // 2, 35, 680, 650)
        x = self.panel.x + 28
        width = self.panel.width - 56

        self._scenario_rects: List[Tuple[str, pygame.Rect]] = []
        for index, key in enumerate(SCENARIOS):
            self._scenario_rects.append((key, pygame.Rect(x, self.panel.y + 68 + index * 36, width, 30)))

        field_y = self.panel.y + 266
        col_w = 295
        col2_x = x + 325

        cashiers_val = bridge.num_cashiers if bridge.num_cashiers > 0 else 2
        ushers_val = bridge.num_ushers if bridge.num_ushers > 0 else 1
        servers_val = bridge.num_servers if bridge.num_servers > 0 else 2

        self.cashiers = NumberInput(pygame.Rect(x, field_y, col_w, 34), "Cashiers (box office)", 1, 9999,
                                    cashiers_val, C_NEON_GOLD)
        self.ushers = NumberInput(pygame.Rect(col2_x, field_y, col_w, 34), "Ushers (ticket checkpoint)", 1, 9999,
                                  ushers_val, C_NEON_PINK)
        self.servers = NumberInput(pygame.Rect(x, field_y + 68, col_w, 34), "Servers (concession stand)", 1, 9999,
                                   servers_val, C_NEON_CYAN)
        self.arrivals = NumberInput(pygame.Rect(col2_x, field_y + 68, col_w, 34), "Arrival gap (sec)", 1, 9999,
                                    round(bridge.arrival_interval * 100), C_TEXT_WHITE)
        self.runtime = NumberInput(pygame.Rect(x, field_y + 136, col_w, 34), "Runtime (minutes)", 1, 9999,
                                   bridge.runtime, C_TEXT_WHITE)
        self.food = NumberInput(pygame.Rect(col2_x, field_y + 136, col_w, 34), "Food demand (%)", 0, 100,
                                round(bridge.food_prob * 100), C_NEON_CYAN)
        self.fields = [self.cashiers, self.ushers, self.servers, self.arrivals, self.runtime, self.food]

        self._speed = bridge.speed
        self.speed_buttons: List[Tuple[int, Button]] = []
        speed_w = 44
        speed_gap = 8
        for index, speed in enumerate((1, 2, 5, 10)):
            button = Button(pygame.Rect(x + index * (speed_w + speed_gap), self.panel.bottom - 54, speed_w + (4 if speed == 10 else 0), 32),
                            f"{speed}×", C_NEON_CYAN, 13)
            button.on_click(lambda value=speed: self._set_speed(value))
            self.speed_buttons.append((speed, button))

        btn_y = self.panel.bottom - 54
        self.btn_back = Button(pygame.Rect(self.panel.right - 28 - 180 - 14 - 120, btn_y, 120, 34),
                               "BACK", (170, 160, 190), 13)
        if self.go_back:
            self.btn_back.on_click(self.go_back)

        self.btn_start = Button(pygame.Rect(self.panel.right - 28 - 180, btn_y, 180, 34),
                                "START SIMULATION", C_NEON_GOLD, 13)
        self.btn_start.on_click(self._on_start)



        self._stars = [
            (random.uniform(0, SCREEN_W), random.uniform(0, SCREEN_H), random.uniform(0, math.pi * 2))
            for _ in range(50)
        ]

    def _set_speed(self, speed: int) -> None:
        self._speed = speed

    def _select_scenario(self, key: str) -> None:
        config = SCENARIOS[key]
        self._scenario_key = key
        self.arrivals.value = round(config["arrival_interval"] * 100)
        self.food.value = round(config["food_prob"] * 100)
        self.runtime.value = config["runtime"]

    def _on_start(self) -> None:
        b = self.bridge
        b.num_cashiers = self.cashiers.value
        b.num_ushers = self.ushers.value
        b.num_servers = self.servers.value
        b.arrival_interval = self.arrivals.value / 100.0
        b.food_prob = self.food.value / 100.0
        b.runtime = float(self.runtime.value)
        b.speed = self._speed
        b.reset()
        self.go_game()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for key, rect in self._scenario_rects:
                if rect.collidepoint(event.pos):
                    self._select_scenario(key)
                    return

        for field in self.fields:
            field.handle_event(event)

        for _, button in self.speed_buttons:
            button.handle_event(event)

        self.btn_back.handle_event(event)
        self.btn_start.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if not any(f.focused for f in self.fields):
                    self._on_start()
            elif event.key == pygame.K_ESCAPE:
                if self.go_back:
                    self.go_back()

    def update(self, dt: float) -> None:
        self._t += dt
        for _, button in self.speed_buttons:
            button.update(dt)
        self.btn_back.update(dt)
        self.btn_start.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(C_BG_DARK)

        for x, y, phase in self._stars:
            alpha = int(140 + 90 * math.sin(self._t * 2.0 + phase))
            pygame.draw.circle(surface, (alpha, alpha, int(alpha * 0.9)), (int(x), int(y)), 1)

        draw_panel(surface, self.panel, C_NEON_GOLD, alpha=245, radius=12)
        draw_text(surface, "Simulation Setup", self._title_font, C_NEON_GOLD,
                  (self.panel.x + 24, self.panel.y + 17))
        draw_text(surface, "Choose a preset or customize parameters before starting the simulation.",
                  self._small_font, C_TEXT_DIM, (self.panel.x + 26, self.panel.y + 46))

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

        pygame.draw.line(surface, (85, 65, 120), (self.panel.x + 28, self.panel.y + 258),
                         (self.panel.right - 28, self.panel.y + 258), 1)

        for field in self.fields:
            field.draw(surface)

        draw_text(surface, "Simulation speed", self._small_font, C_TEXT_DIM,
                  (self.panel.x + 28, self.panel.bottom - 74))

        for speed, button in self.speed_buttons:
            if speed == self._speed:
                pygame.draw.rect(surface, C_NEON_CYAN, button.rect, 2, border_radius=6)
            button.draw(surface)

        self.btn_back.draw(surface)
        self.btn_start.draw(surface)
