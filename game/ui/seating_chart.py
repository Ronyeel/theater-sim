from typing import Optional, Tuple

import pygame

from game.settings import (
    SCREEN_W, C_NEON_GOLD, C_NEON_CYAN, C_NEON_GREEN, C_NEON_RED,
    C_TEXT_WHITE, C_TEXT_DIM, C_GOOD, C_BAD,
)
from game.ui.button import Button, draw_panel, draw_text
from game.ui.simulation_panel import NumberInput
from src.seating import TheaterSeating, is_seat_available


def _font(name, size, bold=False):
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


class SeatingChartPanel:

    def __init__(self, seating: TheaterSeating):
        self.seating = seating
        self.visible = False
        self.message = "Click a seat or enter row and seat number."
        self.message_color = C_TEXT_DIM
        self._title_font = _font("consolas", 16, bold=True)
        self._cell_font = _font("consolas", 13, bold=True)
        self._small_font = _font("consolas", 11)

        self.panel = pygame.Rect(SCREEN_W - 318, 54, 306, 352)
        self.cell_size = 24
        self.grid_origin = (self.panel.x + 46, self.panel.y + 62)
        self._cell_rects: list[tuple[int, int, pygame.Rect]] = []
        self._rebuild_cells()

        field_y = self.panel.y + 242
        self.row_input = NumberInput(
            pygame.Rect(self.panel.x + 16, field_y, 130, 30),
            "Row", 1, seating.rows, 1, C_NEON_GOLD,
        )
        self.seat_input = NumberInput(
            pygame.Rect(self.panel.x + 160, field_y, 130, 30),
            "Seat", 1, seating.cols, 1, C_NEON_CYAN,
        )
        self.reserve_btn = Button(
            pygame.Rect(self.panel.x + 16, self.panel.bottom - 44, 132, 30),
            "RESERVE", C_NEON_GREEN, 12,
        )
        self.cancel_btn = Button(
            pygame.Rect(self.panel.x + 158, self.panel.bottom - 44, 132, 30),
            "CANCEL", C_NEON_RED, 12,
        )
        self.reserve_btn.on_click(self._reserve_typed)
        self.cancel_btn.on_click(self._cancel_typed)
        self.on_reserve_callback = None

    def bind(self, seating: TheaterSeating) -> None:
        self.seating = seating
        self.row_input.max_value = seating.rows
        self.seat_input.max_value = seating.cols

    def open(self) -> None:
        self.visible = True
        self.message = "A = available, X = taken. Select seat."
        self.message_color = C_TEXT_DIM

    def close(self) -> None:
        self.visible = False

    def toggle(self) -> None:
        if self.visible:
            self.close()
        else:
            self.open()

    def _rebuild_cells(self) -> None:
        self._cell_rects = []
        ox, oy = self.grid_origin
        for row in range(1, self.seating.rows + 1):
            for col in range(1, self.seating.cols + 1):
                rect = pygame.Rect(
                    ox + (col - 1) * self.cell_size,
                    oy + (row - 1) * self.cell_size,
                    self.cell_size - 2,
                    self.cell_size - 2,
                )
                self._cell_rects.append((row, col, rect))

    def _set_message(self, text: str, color: Tuple[int, int, int]) -> None:
        self.message = text
        self.message_color = color

    def _reserve_at(self, row: int, col: int) -> None:
        if not (1 <= row <= self.seating.rows and 1 <= col <= self.seating.cols):
            self._set_message("Invalid input. Try again.", C_BAD)
            return
        if is_seat_available(self.seating.chart, row, col):
            ok, msg = self.seating.reserve(row, col, customer_name="Player")
            if ok:
                self._set_message(f"Seat Row {row} Seat {col} reserved!", C_GOOD)
                if self.on_reserve_callback:
                    self.on_reserve_callback(row, col)
            else:
                self._set_message("Sorry, that seat is already taken.", C_BAD)
            return
        self._set_message("Sorry, that seat is already taken.", C_BAD)

    def _cancel_at(self, row: int, col: int) -> None:
        info = self.seating.seat_data.get((row, col))
        if info and info.get("customer_name") not in ("Player", "Student / Player"):
            self._set_message("That seat belongs to another moviegoer.", C_BAD)
            return
        ok, msg = self.seating.cancel(row, col)
        self._set_message("Reservation canceled." if ok else msg, C_GOOD if ok else C_BAD)

    def _reserve_typed(self) -> None:
        self._reserve_at(self.row_input.value, self.seat_input.value)

    def _cancel_typed(self) -> None:
        self._cancel_at(self.row_input.value, self.seat_input.value)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_F2):
            self.close()
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for row, col, rect in self._cell_rects:
                if rect.collidepoint(event.pos):
                    self.row_input.value = row
                    self.seat_input.value = col
                    if is_seat_available(self.seating.chart, row, col):
                        self._reserve_at(row, col)
                    else:
                        self._cancel_at(row, col)
                    return True
        self.row_input.handle_event(event)
        self.seat_input.handle_event(event)
        self.reserve_btn.handle_event(event)
        self.cancel_btn.handle_event(event)
        return True

    def update(self, dt: float) -> None:
        if not self.visible:
            return
        self.reserve_btn.update(dt)
        self.cancel_btn.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        draw_panel(surface, self.panel, C_NEON_GOLD, alpha=235, radius=10)
        draw_text(surface, "Seating Chart", self._title_font, C_NEON_GOLD,
                  (self.panel.x + 14, self.panel.y + 10))

        stats = f"{self.seating.available_seats} open  •  {self.seating.reserved_seats} taken"
        draw_text(surface, stats, self._small_font, C_TEXT_DIM,
                  (self.panel.x + 14, self.panel.y + 30))
        draw_text(surface, "[F2] Close", self._small_font, C_TEXT_DIM,
                  (self.panel.right - 88, self.panel.y + 12))

        ox, oy = self.grid_origin
        for col in range(1, self.seating.cols + 1):
            label = self._small_font.render(str(col), True, C_TEXT_DIM)
            surface.blit(label, (ox + (col - 1) * self.cell_size + 6, oy - 16))

        for row in range(1, self.seating.rows + 1):
            label = self._small_font.render(f"R{row}", True, C_TEXT_DIM)
            surface.blit(label, (self.panel.x + 14, oy + (row - 1) * self.cell_size + 4))

        for row, col, rect in self._cell_rects:
            taken = self.seating.chart[row - 1][col - 1] == 'X'
            fill = (92, 32, 48) if taken else (28, 72, 52)
            border = C_NEON_RED if taken else C_NEON_GREEN
            mark_char = 'X' if taken else 'A'

            pygame.draw.rect(surface, fill, rect, border_radius=3)
            pygame.draw.rect(surface, border, rect, 1, border_radius=3)
            mark = self._cell_font.render(mark_char, True, C_TEXT_WHITE)
            surface.blit(mark, (rect.centerx - mark.get_width() // 2,
                                rect.centery - mark.get_height() // 2))

        msg = self._small_font.render(self.message[:44], True, self.message_color)
        surface.blit(msg, (self.panel.x + 14, self.panel.y + 188))

        self.row_input.draw(surface)
        self.seat_input.draw(surface)
        self.reserve_btn.draw(surface)
        self.cancel_btn.draw(surface)
