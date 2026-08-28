
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

    def __init__(self, simulation, player=None, npcs_provider: Optional[Callable] = None) -> None:
        self.simulation = simulation
        self.player = player
        self.npcs_provider = npcs_provider
        self._log: List[Tuple[str, Tuple[int, int, int]]] = []
        self._log_t = 0.0

        self._val_f = _get_font("consolas", 14, bold=True)
        self._time_f = _get_font("consolas", 16, bold=True)
        self._lbl_f = _get_font("consolas", 9, bold=True)
        self._sub_f = _get_font("consolas", 10)
        self._tag_f = _get_font("consolas", 11, bold=True)

        self._bar_rect = pygame.Rect(0, 0, SCREEN_W, 46)
        self._status_rect = pygame.Rect(112, 10, 82, 26)

        self._speed_capsule_rect = pygame.Rect(SCREEN_W - 165, 8, 155, 30)
        self._speed_rects: List[Tuple[int, pygame.Rect]] = [
            (1, pygame.Rect(802, 11, 32, 24)),
            (2, pygame.Rect(840, 11, 32, 24)),
            (5, pygame.Rect(878, 11, 32, 24)),
            (10, pygame.Rect(916, 11, 36, 24)),
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

            if self._status_rect.collidepoint(evt.pos):
                is_p = getattr(self.simulation, "is_paused", False)
                self.simulation.is_paused = not is_p
                self.add_log("Simulation PAUSED" if self.simulation.is_paused else "Simulation RESUMED", C_NEON_CYAN)
                return True

            if self._bar_rect.collidepoint(evt.pos):
                return True

        return False

    def draw(self, surface: pygame.Surface) -> None:
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

        x1 = 14
        lbl_time = self._lbl_f.render("SIM TIME", True, (130, 145, 175))
        val_time = self._time_f.render(f"{mins:02d}:{secs:02d}", True, C_TEXT_WHITE)
        max_time = self._sub_f.render(f"/{int(self.simulation.runtime)}m", True, (120, 130, 155))
        surface.blit(lbl_time, (x1, 7))
        surface.blit(val_time, (x1, 19))
        surface.blit(max_time, (x1 + val_time.get_width() + 2, 23))

        pygame.draw.rect(surface, st_bg, self._status_rect, border_radius=4)
        pygame.draw.rect(surface, st_col, self._status_rect, 1, border_radius=4)
        st_surf = self._tag_f.render(st_text, True, st_col)
        surface.blit(st_surf, (self._status_rect.centerx - st_surf.get_width() // 2,
                               self._status_rect.centery - st_surf.get_height() // 2))

        pygame.draw.line(surface, (35, 45, 70), (204, 8), (204, 38), 1)

        x2 = 216
        lbl_wait = self._lbl_f.render("AVG WAIT TIME", True, (130, 145, 175))
        val_wait = self._val_f.render(f"{wait_m}m {wait_s:02d}s", True, sla_color)
        surface.blit(lbl_wait, (x2, 7))
        surface.blit(val_wait, (x2, 21))

        pygame.draw.line(surface, (35, 45, 70), (336, 8), (336, 38), 1)

        x3 = 348
        npcs = self.npcs_provider() if callable(self.npcs_provider) else []
        if npcs:
            ticket_q = sum(1 for n in npcs if n.state in (n.TICKET_LINE, n.BUYING_TICKET))
            usher_q = sum(1 for n in npcs if n.state in (n.USHER_LINE, n.CHECKING_TICKET))
            snack_q = sum(1 for n in npcs if n.state in (n.SNACK_LINE, n.BUYING_SNACK))
            seated = sum(1 for n in npcs if n.state == n.SEATED)
            total_active = len([n for n in npcs if not n.has_left])
        else:
            ticket_q = stats.cashier_queue
            usher_q = stats.usher_queue
            snack_q = stats.snack_queue
            seated = stats.total_seated
            total_active = stats.active_guests

        lbl_vol = self._lbl_f.render("CUSTOMER FLOW", True, (130, 145, 175))
        val_vol = self._val_f.render(f"{stats.total_seated} Seated / {stats.total_arrived} Total", True, C_TEXT_WHITE)
        surface.blit(lbl_vol, (x3, 7))
        surface.blit(val_vol, (x3, 21))

        pygame.draw.line(surface, (35, 45, 70), (530, 8), (530, 38), 1)

        x4 = 542
        lbl_staff = self._lbl_f.render("STAFF ON DUTY", True, (130, 145, 175))
        c_count = self.simulation.num_cashiers
        u_count = self.simulation.num_ushers
        s_count = self.simulation.num_servers
        staff_text = f"{c_count} Cashier{'s' if c_count != 1 else ''} • {u_count} Usher{'s' if u_count != 1 else ''} • {s_count} Server{'s' if s_count != 1 else ''}"
        val_staff = self._val_f.render(staff_text, True, C_NEON_GOLD)
        if val_staff.get_width() > 240:
            val_staff = self._sub_f.render(staff_text, True, C_NEON_GOLD)

        surface.blit(lbl_staff, (x4, 7))
        surface.blit(val_staff, (x4, 21))

        pygame.draw.line(surface, (35, 45, 70), (790, 8), (790, 38), 1)


        mouse_pos = pygame.mouse.get_pos()
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

        b_rect = pygame.Rect(0, SCREEN_H - 24, SCREEN_W, 24)
        b_surf = pygame.Surface((b_rect.width, b_rect.height), pygame.SRCALPHA)
        b_surf.fill((10, 13, 24, 230))
        surface.blit(b_surf, (0, SCREEN_H - 24))
        pygame.draw.line(surface, (32, 40, 60), (0, SCREEN_H - 24), (SCREEN_W, SCREEN_H - 24), 1)

        if self._log and self._log_t > 0:
            latest_msg, latest_col = self._log[0]
            log_txt = self._sub_f.render(f"SYSTEM LOG: {latest_msg}", True, latest_col)
            surface.blit(log_txt, (12, SCREEN_H - 18))

        shortcuts = "[F] Speed  •  [Space] Pause  •  [Click & Drag] Pan Camera  •  [Scroll / +/-] Zoom  •  [F1] Settings"
        s_surf = self._sub_f.render(shortcuts, True, (150, 160, 190))
        surface.blit(s_surf, (SCREEN_W - s_surf.get_width() - 12, SCREEN_H - 18))



