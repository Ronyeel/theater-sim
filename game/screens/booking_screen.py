from typing import Callable, Optional, Tuple, List
import math
import random
import pygame

from game.settings import (
    SCREEN_W, SCREEN_H, C_NEON_GOLD, C_NEON_CYAN,
    C_NEON_GREEN, C_NEON_RED, C_TEXT_WHITE, C_TEXT_DIM,
    C_GOOD, C_BAD, C_WARN,
)
from game.core import asset_loader as AL
from game.ui.button import Button, draw_panel, draw_text
from game.ui.simulation_panel import NumberInput
from src.seating import (
    is_seat_available, is_valid_seat, get_available_seats_count,
    get_taken_seats_count, copy_chart,
)


def _get_font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


class BookingScreen:

    def __init__(
        self,
        bridge,
        go_game: Callable[[], None],
        go_back: Callable[[], None],
    ) -> None:
        self.bridge = bridge
        self.seating = bridge.seating
        self.go_game = go_game
        self.go_back = go_back
        self._t = 0.0

        self._title_font = _get_font("consolas", 22, bold=True)
        self._sub_font = _get_font("consolas", 12, bold=True)
        self._body_font = _get_font("consolas", 13)
        self._cell_font = _get_font("consolas", 18, bold=True)
        self._header_font = _get_font("consolas", 14, bold=True)

        self.panel = pygame.Rect((SCREEN_W - 780) // 2, 30, 780, 660)

        self.cell_w = 54
        self.cell_h = 44
        self.cell_gap_x = 8
        self.cell_gap_y = 8
        self.grid_origin_x = self.panel.x + 120
        self.grid_origin_y = self.panel.y + 115

        self._cell_rects: List[Tuple[int, int, pygame.Rect]] = []
        self._rebuild_cells()

        field_y = self.panel.y + 420
        self.row_input = NumberInput(
            pygame.Rect(self.panel.x + 80, field_y, 160, 36),
            "Row (1-5)", 1, self.seating.rows, 1, C_NEON_GOLD,
        )
        self.seat_input = NumberInput(
            pygame.Rect(self.panel.x + 260, field_y, 160, 36),
            "Seat (1-10)", 1, self.seating.cols, 1, C_NEON_CYAN,
        )

        self.btn_reserve = Button(
            pygame.Rect(self.panel.x + 440, field_y, 140, 36),
            "RESERVE SEAT", C_NEON_GREEN, 13,
        )
        self.btn_reserve.on_click(self._on_reserve_click)

        self.btn_reset = Button(
            pygame.Rect(self.panel.x + 600, field_y, 100, 36),
            "RESET", (180, 80, 80), 12,
        )
        self.btn_reset.on_click(self._on_reset_click)

        bottom_y = self.panel.bottom - 56
        self.btn_back = Button(
            pygame.Rect(self.panel.x + 80, bottom_y, 140, 38),
            "BACK TO MENU", (160, 150, 180), 13,
        )
        self.btn_back.on_click(self.go_back)

        self.btn_start = Button(
            pygame.Rect(self.panel.right - 260, bottom_y, 180, 38),
            "START SIMULATION", C_NEON_GOLD, 13,
        )
        self.btn_start.on_click(self.go_game)

        self.message = "Select a row and seat to reserve, or click any seat directly."
        self.message_color = C_TEXT_DIM

        self._stars = [
            (random.uniform(0, SCREEN_W), random.uniform(0, SCREEN_H), random.uniform(0, math.pi * 2))
            for _ in range(50)
        ]

    def _rebuild_cells(self) -> None:
        self._cell_rects = []
        for row in range(1, self.seating.rows + 1):
            for col in range(1, self.seating.cols + 1):
                rx = self.grid_origin_x + (col - 1) * (self.cell_w + self.cell_gap_x)
                # Add an aisle gap between column 5 and 6
                if col > 5:
                    rx += 16
                ry = self.grid_origin_y + (row - 1) * (self.cell_h + self.cell_gap_y)
                rect = pygame.Rect(rx, ry, self.cell_w, self.cell_h)
                self._cell_rects.append((row, col, rect))

    def _reserve_seat_logic(self, row: int, col: int) -> None:
        if not is_valid_seat(self.seating.chart, row, col):
            self.message = "Invalid input. Try again."
            self.message_color = C_WARN
            return

        if self.seating.chart[row - 1][col - 1] == 'X':
            self.message = "Sorry, that seat is already taken."
            self.message_color = C_BAD
            return

        ok, _ = self.seating.reserve(row, col, customer_name="Student / Player")
        if ok:
            self.bridge.final_chart = copy_chart(self.seating.chart)
            self.message = "Seat reserved successfully!"
            self.message_color = C_GOOD
        else:
            self.message = "Sorry, that seat is already taken."
            self.message_color = C_BAD

    def _on_reserve_click(self) -> None:
        row = self.row_input.value
        col = self.seat_input.value
        self._reserve_seat_logic(row, col)

    def _on_reset_click(self) -> None:
        self.seating.reset()
        self.bridge.final_chart = copy_chart(self.seating.chart)
        self.message = "All seats have been reset to Available ('A')."
        self.message_color = C_NEON_CYAN

    def handle_event(self, evt: pygame.event.Event) -> None:
        self.row_input.handle_event(evt)
        self.seat_input.handle_event(evt)
        self.btn_reserve.handle_event(evt)
        self.btn_reset.handle_event(evt)
        self.btn_back.handle_event(evt)
        self.btn_start.handle_event(evt)

        if evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
            for row, col, rect in self._cell_rects:
                if rect.collidepoint(evt.pos):
                    self.row_input.value = row
                    self.seat_input.value = col
                    self._reserve_seat_logic(row, col)
                    break

        if evt.type == pygame.KEYDOWN:
            if evt.key == pygame.K_ESCAPE:
                self.go_back()
            elif evt.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._on_reserve_click()

    def update(self, dt: float) -> None:
        self._t += dt
        self.btn_reserve.update(dt)
        self.btn_reset.update(dt)
        self.btn_back.update(dt)
        self.btn_start.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        bg = AL.menu_background(self._t)
        surface.blit(bg, (0, 0))

        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 140))
        surface.blit(ov, (0, 0))

        draw_panel(surface, self.panel, C_NEON_GOLD, alpha=235, radius=12)

        # Institution & Title
        draw_text(surface, "CAMARINES NORTE STATE COLLEGE", self._sub_font, (170, 190, 220),
                  (self.panel.x + 28, self.panel.y + 16))
        draw_text(surface, "THEATER SEAT RESERVATION SYSTEM", self._title_font, C_NEON_GOLD,
                  (self.panel.x + 28, self.panel.y + 36))
        draw_text(surface, "Procedure Steps 1–4: 5-Row × 10-Seat Layout", self._body_font, C_TEXT_DIM,
                  (self.panel.x + 28, self.panel.y + 66))

        # Legend & Stats
        avail_cnt = get_available_seats_count(self.seating.chart)
        taken_cnt = get_taken_seats_count(self.seating.chart)
        stats_str = f"Available: {avail_cnt}/50  •  Taken: {taken_cnt}/50"
        draw_text(surface, stats_str, self._header_font, C_NEON_CYAN,
                  (self.panel.right - 270, self.panel.y + 40))

        # Column numbers (1 to 10)
        for col in range(1, self.seating.cols + 1):
            rx = self.grid_origin_x + (col - 1) * (self.cell_w + self.cell_gap_x)
            if col > 5:
                rx += 16
            lbl = self._header_font.render(f"{col:>2}", True, C_NEON_GOLD)
            surface.blit(lbl, (rx + (self.cell_w - lbl.get_width()) // 2, self.grid_origin_y - 24))

        # Row labels (Row 1 to Row 5)
        for row in range(1, self.seating.rows + 1):
            ry = self.grid_origin_y + (row - 1) * (self.cell_h + self.cell_gap_y)
            lbl = self._header_font.render(f"Row {row:<2}", True, C_NEON_GOLD)
            surface.blit(lbl, (self.panel.x + 36, ry + (self.cell_h - lbl.get_height()) // 2))

        # Seat cells
        mouse_pos = pygame.mouse.get_pos()
        for row, col, rect in self._cell_rects:
            taken = self.seating.chart[row - 1][col - 1] == 'X'
            is_hover = rect.collidepoint(mouse_pos)

            if taken:
                fill_color = (95, 28, 38) if not is_hover else (120, 36, 48)
                border_color = C_NEON_RED
                text_color = (255, 180, 180)
                char = 'X'
            else:
                fill_color = (24, 68, 48) if not is_hover else (34, 94, 66)
                border_color = C_NEON_GREEN
                text_color = (180, 255, 200)
                char = 'A'

            pygame.draw.rect(surface, fill_color, rect, border_radius=5)
            pygame.draw.rect(surface, border_color, rect, 2 if is_hover else 1, border_radius=5)

            char_surf = self._cell_font.render(char, True, text_color)
            surface.blit(char_surf, (rect.centerx - char_surf.get_width() // 2,
                                     rect.centery - char_surf.get_height() // 2))

        # Screen Indicator / Stage at top
        screen_bar = pygame.Rect(self.grid_origin_x + 60, self.grid_origin_y - 34, 380, 4)
        pygame.draw.rect(surface, (100, 140, 200), screen_bar, border_radius=2)
        scr_lbl = self._sub_font.render("--- MOVIE SCREEN ---", True, (130, 160, 210))
        surface.blit(scr_lbl, (screen_bar.centerx - scr_lbl.get_width() // 2, screen_bar.y - 14))

        # Message Banner
        msg_box = pygame.Rect(self.panel.x + 80, self.panel.y + 472, self.panel.width - 160, 40)
        pygame.draw.rect(surface, (14, 18, 32), msg_box, border_radius=6)
        pygame.draw.rect(surface, (45, 55, 80), msg_box, 1, border_radius=6)
        msg_surf = self._body_font.render(self.message, True, self.message_color)
        surface.blit(msg_surf, (msg_box.centerx - msg_surf.get_width() // 2,
                                msg_box.centery - msg_surf.get_height() // 2))

        # Input fields and buttons
        self.row_input.draw(surface)
        self.seat_input.draw(surface)
        self.btn_reserve.draw(surface)
        self.btn_reset.draw(surface)

        # Footer divider and buttons
        pygame.draw.line(surface, (45, 55, 80), (self.panel.x + 28, self.panel.bottom - 74),
                         (self.panel.right - 28, self.panel.bottom - 74), 1)
        self.btn_back.draw(surface)
        self.btn_start.draw(surface)
