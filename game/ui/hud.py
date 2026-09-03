from typing import List, Tuple, Optional, Callable
import pygame
from game.settings import (
    SCREEN_W, SCREEN_H, C_TEXT_WHITE, C_TEXT_DIM,
    C_NEON_GOLD, C_NEON_CYAN, C_NEON_GREEN, C_NEON_RED, C_GOOD, C_BAD, C_WARN,
)
from src.stats import format_minutes_seconds


def _get_font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


class HUD:

    LOG_MAX = 4

    def __init__(
        self,
        simulation,
        player=None,
        npcs_provider: Optional[Callable] = None,
        on_toggle_seats: Optional[Callable[[], None]] = None,
    ) -> None:
        self.simulation = simulation
        self.player = player
        self.npcs_provider = npcs_provider
        self.on_toggle_seats = on_toggle_seats
        self._log: List[Tuple[str, Tuple[int, int, int]]] = []
        self._log_t = 0.0

        self._val_f = _get_font("consolas", 13, bold=True)
        self._val_compact_f = _get_font("consolas", 12, bold=True)
        self._time_f = _get_font("consolas", 15, bold=True)
        self._lbl_f = _get_font("consolas", 9, bold=True)
        self._sub_f = _get_font("consolas", 10)
        self._tag_f = _get_font("consolas", 11, bold=True)

        self._bar_rect = pygame.Rect(0, 0, SCREEN_W, 46)

        # Segment coordinates balanced across SCREEN_W (960px)
        self._status_rect = pygame.Rect(96, 10, 80, 26)
        self._seats_btn_rect = pygame.Rect(722, 10, 82, 26)

        self._speed_capsule_rect = pygame.Rect(814, 8, 142, 30)
        self._speed_rects: List[Tuple[int, pygame.Rect]] = [
            (1, pygame.Rect(818, 11, 30, 24)),
            (2, pygame.Rect(852, 11, 30, 24)),
            (5, pygame.Rect(886, 11, 30, 24)),
            (10, pygame.Rect(920, 11, 34, 24)),
        ]

    def add_log(self, text: str, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        self._log.insert(0, (text, color))
        if len(self._log) > self.LOG_MAX:
            self._log.pop()
        self._log_t = 4.0

    def update(self, dt: float) -> None:
        self._log_t = max(0.0, self._log_t - dt)

    def handle_event(self, evt: pygame.event.Event) -> bool:
        if evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
            for speed, rect in self._speed_rects:
                if rect.collidepoint(evt.pos):
                    self.simulation.speed = speed
                    self.add_log(f"Playback speed set to {speed}x", C_NEON_CYAN)
                    return True

            if self._speed_capsule_rect.collidepoint(evt.pos):
                speeds = [1, 2, 5, 10]
                cur_idx = speeds.index(self.simulation.speed) if self.simulation.speed in speeds else 0
                next_speed = speeds[(cur_idx + 1) % len(speeds)]
                self.simulation.speed = next_speed
                self.add_log(f"Playback speed set to {next_speed}x", C_NEON_CYAN)
                return True

            if self._seats_btn_rect.collidepoint(evt.pos):
                if callable(self.on_toggle_seats):
                    self.on_toggle_seats()
                return True

            if self._status_rect.collidepoint(evt.pos):
                is_p = getattr(self.simulation, "is_paused", False)
                self.simulation.is_paused = not is_p
                self.add_log("Simulation PAUSED" if self.simulation.is_paused else "Simulation RESUMED", C_NEON_CYAN)
                return True

            if self._bar_rect.collidepoint(evt.pos):
                return True

        return False

    def draw(self, surface: pygame.Surface, mode_text: str = "") -> None:
        stats = self.simulation.stats

        top_bar = self._bar_rect
        bar_surf = pygame.Surface((top_bar.width, top_bar.height), pygame.SRCALPHA)
        bar_surf.fill((12, 16, 28, 245))
        surface.blit(bar_surf, (0, 0))
        pygame.draw.line(surface, (40, 52, 80), (0, top_bar.bottom), (SCREEN_W, top_bar.bottom), 1)

        mins, secs = format_minutes_seconds(stats.sim_time)
        wait_m, wait_s = format_minutes_seconds(stats.avg_wait)
        is_target_met = stats.avg_wait <= 10.0
        sla_color = C_GOOD if is_target_met else C_BAD

        if getattr(self.simulation, "is_paused", False):
            st_text, st_col, st_bg = "❚❚ PAUSED", C_NEON_GOLD, (35, 30, 15)
        elif self.simulation.is_running:
            st_text, st_col, st_bg = "● RUNNING", C_NEON_GREEN, (15, 35, 20)
        else:
            st_text, st_col, st_bg = "■ FINISHED", C_NEON_RED, (35, 15, 15)

        # -------------------------------------------------------------
        # 1. Sim Time + Status
        # -------------------------------------------------------------
        x1 = 12
        lbl_time = self._lbl_f.render("SIM TIME", True, (130, 145, 175))
        val_time = self._time_f.render(f"{mins:02d}:{secs:02d}", True, C_TEXT_WHITE)
        max_time = self._sub_f.render(f"/{int(self.simulation.runtime)}m", True, (120, 130, 155))
        surface.blit(lbl_time, (x1, 7))
        surface.blit(val_time, (x1, 20))
        surface.blit(max_time, (x1 + val_time.get_width() + 2, 23))

        pygame.draw.rect(surface, st_bg, self._status_rect, border_radius=4)
        pygame.draw.rect(surface, st_col, self._status_rect, 1, border_radius=4)
        st_surf = self._tag_f.render(st_text, True, st_col)
        surface.blit(st_surf, (self._status_rect.centerx - st_surf.get_width() // 2,
                                self._status_rect.centery - st_surf.get_height() // 2))

        pygame.draw.line(surface, (35, 45, 70), (184, 8), (184, 38), 1)

        # -------------------------------------------------------------
        # 2. Avg Wait Time
        # -------------------------------------------------------------
        x2 = 194
        lbl_wait = self._lbl_f.render("AVG WAIT TIME", True, (130, 145, 175))
        val_wait = self._val_f.render(f"{wait_m}m {wait_s:02d}s", True, sla_color)
        surface.blit(lbl_wait, (x2, 7))
        surface.blit(val_wait, (x2, 21))

        pygame.draw.line(surface, (35, 45, 70), (306, 8), (306, 38), 1)

        # -------------------------------------------------------------
        # 3. Customer Flow & Seating
        # -------------------------------------------------------------
        x3 = 316
        lbl_vol = self._lbl_f.render("CUSTOMER FLOW", True, (130, 145, 175))
        val_vol = self._val_f.render(
            f"{stats.total_seated}/{stats.total_arrived} · {stats.seats_reserved}/50 seats",
            True, C_TEXT_WHITE,
        )
        surface.blit(lbl_vol, (x3, 7))
        surface.blit(val_vol, (x3, 21))

        pygame.draw.line(surface, (35, 45, 70), (484, 8), (484, 38), 1)

        # -------------------------------------------------------------
        # 4. Staff on Duty (with smart fallback to prevent clipping)
        # -------------------------------------------------------------
        x4 = 494
        lbl_staff = self._lbl_f.render("STAFF ON DUTY", True, (130, 145, 175))
        c_count = self.simulation.num_cashiers
        u_count = self.simulation.num_ushers
        s_count = self.simulation.num_servers

        staff_full = f"{c_count} Cashier{'s' if c_count != 1 else ''} • {u_count} Usher{'s' if u_count != 1 else ''} • {s_count} Server{'s' if s_count != 1 else ''}"
        staff_compact = f"{c_count} Cash • {u_count} Ush • {s_count} Serv"
        staff_minimal = f"{c_count}C • {u_count}U • {s_count}S"

        val_staff = self._val_compact_f.render(staff_full, True, C_NEON_GOLD)
        if val_staff.get_width() > 214:
            val_staff = self._val_compact_f.render(staff_compact, True, C_NEON_GOLD)
            if val_staff.get_width() > 214:
                val_staff = self._val_compact_f.render(staff_minimal, True, C_NEON_GOLD)

        surface.blit(lbl_staff, (x4, 7))
        surface.blit(val_staff, (x4, 21))

        pygame.draw.line(surface, (35, 45, 70), (714, 8), (714, 38), 1)

        # -------------------------------------------------------------
        # 5. [F2] SEATS button
        # -------------------------------------------------------------
        mouse_pos = pygame.mouse.get_pos()
        is_seats_hover = self._seats_btn_rect.collidepoint(mouse_pos)
        s_fill = (26, 68, 46) if is_seats_hover else (16, 38, 28)
        s_border = C_NEON_GREEN if is_seats_hover else (45, 140, 80)
        s_txt_col = (230, 255, 235) if is_seats_hover else (150, 230, 175)

        pygame.draw.rect(surface, s_fill, self._seats_btn_rect, border_radius=4)
        pygame.draw.rect(surface, s_border, self._seats_btn_rect, 1, border_radius=4)
        s_tag = self._tag_f.render("[F2] SEATS", True, s_txt_col)
        surface.blit(s_tag, (self._seats_btn_rect.centerx - s_tag.get_width() // 2,
                             self._seats_btn_rect.centery - s_tag.get_height() // 2))

        pygame.draw.line(surface, (35, 45, 70), (810, 8), (810, 38), 1)

        # -------------------------------------------------------------
        # 6. Playback Speed Selector
        # -------------------------------------------------------------
        for speed, rect in self._speed_rects:
            is_active = (self.simulation.speed == speed)
            is_hover = rect.collidepoint(mouse_pos)

            if is_active:
                pygame.draw.rect(surface, (20, 70, 110), rect, border_radius=3)
                pygame.draw.rect(surface, C_NEON_CYAN, rect, 1, border_radius=3)
                txt_col = (255, 255, 255)
            elif is_hover:
                pygame.draw.rect(surface, (35, 45, 70), rect, border_radius=3)
                pygame.draw.rect(surface, (80, 120, 180), rect, 1, border_radius=3)
                txt_col = C_NEON_CYAN
            else:
                pygame.draw.rect(surface, (16, 20, 36), rect, border_radius=3)
                pygame.draw.rect(surface, (35, 42, 65), rect, 1, border_radius=3)
                txt_col = (140, 150, 175)

            btn_txt = self._tag_f.render(f"{speed}x", True, txt_col)
            surface.blit(btn_txt, (rect.centerx - btn_txt.get_width() // 2,
                                   rect.centery - btn_txt.get_height() // 2))

        # -------------------------------------------------------------
        # Bottom Status Bar & Shortcuts
        # -------------------------------------------------------------
        b_rect = pygame.Rect(0, SCREEN_H - 24, SCREEN_W, 24)
        b_surf = pygame.Surface((b_rect.width, b_rect.height), pygame.SRCALPHA)
        b_surf.fill((10, 13, 24, 230))
        surface.blit(b_surf, (0, SCREEN_H - 24))
        pygame.draw.line(surface, (32, 40, 60), (0, SCREEN_H - 24), (SCREEN_W, SCREEN_H - 24), 1)

        bx = 12
        if mode_text:
            mode_surf = self._sub_f.render(mode_text, True, C_NEON_CYAN if "SPECTATOR" in mode_text else C_NEON_GREEN)
            surface.blit(mode_surf, (bx, SCREEN_H - 18))
            bx += mode_surf.get_width() + 16

        if self._log and self._log_t > 0:
            latest_msg, latest_col = self._log[0]
            log_txt = self._sub_f.render(f"SYSTEM LOG: {latest_msg}", True, latest_col)
            surface.blit(log_txt, (bx, SCREEN_H - 18))

        shortcuts = "[F] Speed  •  [Space] Pause  •  [Click & Drag] Pan  •  [Scroll / +/-] Zoom  •  [F1] Settings  •  [F2] Seating"
        s_surf = self._sub_f.render(shortcuts, True, (150, 160, 190))
        surface.blit(s_surf, (SCREEN_W - s_surf.get_width() - 12, SCREEN_H - 18))
