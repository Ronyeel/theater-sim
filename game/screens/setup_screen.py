"""
Pre-Simulation Setup Screen
Provides interactive situation presets and fine-tuning number fields for staff configuration
(cashiers, ushers, servers), arrival intervals, runtime duration, food demand, and simulation speed.
"""

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
    """Pre-simulation configuration screen with scenario presets and custom number fields."""

    def __init__(self, bridge, go_game: Callable[[], None], go_back: Optional[Callable[[], None]] = None) -> None:
        self.bridge = bridge
        self.go_game = go_game
        self.go_back = go_back
        self._t = 0.0
        self._scenario_key: Optional[str] = "normal"

        self._title_font = _get_font("consolas", 24, bold=True)
        self._body_font = _get_font("consolas", 13)
        self._small_font = _get_font("consolas", 11)

        self.panel = pygame.Rect((SCREEN_W - 640) // 2, 45, 640, 590)
        x = self.panel.x + 28
        width = self.panel.width - 56

        self._scenario_rects: List[Tuple[str, pygame.Rect]] = []
        for index, key in enumerate(SCENARIOS):
            self._scenario_rects.append((key, pygame.Rect(x, self.panel.y + 66 + index * 38, width, 32)))

        field_y = self.panel.y + 276
        self.cashiers = NumberInput(pygame.Rect(x, field_y, 260, 34), "Cashiers (box office)", 0, 9999,
                                    bridge.num_cashiers, C_NEON_GOLD)
        self.ushers = NumberInput(pygame.Rect(x + 320, field_y, 260, 34), "Ushers (ticket checkpoint)", 0, 9999,
                                  bridge.num_ushers, C_NEON_PINK)
        self.servers = NumberInput(pygame.Rect(x, field_y + 67, 260, 34), "Servers (concession stand)", 0, 9999,
                                   bridge.num_servers, C_NEON_CYAN)
        self.arrivals = NumberInput(pygame.Rect(x + 320, field_y + 67, 260, 34), "Arrival gap (sec)", 1, 9999,
                                    round(bridge.arrival_interval * 100), C_TEXT_WHITE)
        self.runtime = NumberInput(pygame.Rect(x, field_y + 134, 260, 34), "Runtime (minutes)", 1, 9999,
                                   bridge.runtime, C_TEXT_WHITE)
        self.food = NumberInput(pygame.Rect(x + 320, field_y + 134, 260, 34), "Food demand (%)", 0, 100,
                                round(bridge.food_prob * 100), C_NEON_CYAN)
        self.fields = [self.cashiers, self.ushers, self.servers, self.arrivals, self.runtime, self.food]

        self._speed = bridge.speed
        self.speed_buttons: List[Tuple[int, Button]] = []
        for index, speed in enumerate((1, 2, 5, 10)):
            button = Button(pygame.Rect(x + index * 70, self.panel.bottom - 74, 60, 30),
                            f"{speed}×", C_NEON_CYAN, 13)
            button.on_click(lambda value=speed: self._set_speed(value))
            self.speed_buttons.append((speed, button))

        # Back & Start Simulation Buttons
        self.btn_back = Button(pygame.Rect(self.panel.right - 350, self.panel.bottom - 76, 120, 36),
                               "← BACK", (170, 160, 190), 13)
        if self.go_back:
            self.btn_back.on_click(self.go_back)

        self.btn_start = Button(pygame.Rect(self.panel.right - 215, self.panel.bottom - 76, 190, 36),
                                "▶  START SIMULATION", C_NEON_GOLD, 13)
        self.btn_start.on_click(self._on_start)

        # Background ambient stars
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
        """Apply the chosen situation parameters to the simulation bridge and launch."""
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

        # Ambient twinkling stars
        for x, y, phase in self._stars:
            alpha = int(140 + 90 * math.sin(self._t * 2.0 + phase))
            pygame.draw.circle(surface, (alpha, alpha, int(alpha * 0.9)), (int(x), int(y)), 1)

        draw_panel(surface, self.panel, C_NEON_GOLD, alpha=245, radius=12)
        draw_text(surface, "Simulation Setup", self._title_font, C_NEON_GOLD,
                  (self.panel.x + 24, self.panel.y + 17))
        draw_text(surface, "Choose a preset or customize parameters before starting the simulation.",
                  self._small_font, C_TEXT_DIM, (self.panel.x + 26, self.panel.y + 46))

        # Scenario Presets
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

        # Divider line
        pygame.draw.line(surface, (85, 65, 120), (self.panel.x + 28, self.panel.y + 258),
                         (self.panel.right - 28, self.panel.y + 258), 1)

        # Number input fields
        for field in self.fields:
            field.draw(surface)

        # Speed selector
        draw_text(surface, "Simulation speed", self._small_font, C_TEXT_DIM,
                  (self.panel.x + 28, self.panel.bottom - 100))
        for speed, button in self.speed_buttons:
            if speed == self._speed:
                pygame.draw.rect(surface, C_NEON_CYAN, button.rect, 2, border_radius=6)
            button.draw(surface)

        # Action buttons
        self.btn_back.draw(surface)
        self.btn_start.draw(surface)
