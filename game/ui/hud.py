"""
Live Heads-Up Display (HUD)
Pixel-styled telemetry dashboard for live simulation metrics, queue counts, player objective badges, and event logs.
"""

from typing import List, Tuple, Optional
import pygame
from game.settings import (
    SCREEN_W, SCREEN_H, C_TEXT_WHITE, C_TEXT_DIM, C_NEON_GOLD,
    C_NEON_CYAN, C_NEON_PINK, C_NEON_GREEN, C_NEON_RED,
)
from src.stats import format_minutes_seconds


def _get_font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


class HUD:
    """Live simulation heads-up display rendering SimPy simulation metrics and sandbox spectator controls."""

    LOG_MAX = 5

    def __init__(self, simulation, player=None, npcs_provider: Optional[Callable] = None) -> None:
        self.simulation = simulation
        self.player = player
        self.npcs_provider = npcs_provider
        self._log: List[Tuple[str, Tuple[int, int, int]]] = []
        self._tf = _get_font("consolas", 13, bold=True)
        self._lf = _get_font("consolas", 12)
        self._sm = _get_font("consolas", 11)
        self._log_t = 0.0

    def add_log(self, text: str, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """Add a timed entry to the on-screen event log."""
        self._log.insert(0, (text, color))
        if len(self._log) > self.LOG_MAX:
            self._log.pop()
        self._log_t = 4.0

    def update(self, dt: float) -> None:
        """Update event log fade timers."""
        self._log_t = max(0.0, self._log_t - dt)

    def handle_event(self, evt: pygame.event.Event) -> None:
        """Process any HUD-specific events."""
        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Render HUD elements over the world surface."""
        stats = self.simulation.stats

        def capsule(rect: pygame.Rect, title: str, value: str, color: Tuple[int, int, int]) -> None:
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            panel.fill((19, 22, 40, 235))
            surface.blit(panel, rect.topleft)
            pygame.draw.rect(surface, (43, 48, 76), rect, 2, border_radius=3)
            label = self._lf.render(title, True, (166, 177, 206))
            value_surf = self._tf.render(value, True, color)
            surface.blit(label, (rect.x + 8, rect.y + 5))
            surface.blit(value_surf, (rect.x + 8, rect.y + 19))

        # Time and Status values
        minutes, seconds = format_minutes_seconds(stats.sim_time)
        wait_minutes, wait_seconds = format_minutes_seconds(stats.avg_wait)
        wait_color = C_NEON_GREEN if stats.goal_met else C_NEON_RED

        if getattr(self.simulation, "is_paused", False):
            run_label = "PAUSED"
            run_color = C_NEON_GOLD
        elif self.simulation.is_running:
            run_label = "RUNNING"
            run_color = C_NEON_GREEN
        else:
            run_label = "FINISHED"
            run_color = C_NEON_RED

        # Compute accurate live queue counts from active NPC entities
        npcs = self.npcs_provider() if callable(self.npcs_provider) else []
        if npcs:
            ticket_count = sum(1 for n in npcs if n.state in (n.TICKET_LINE, n.BUYING_TICKET))
            usher_count = sum(1 for n in npcs if n.state in (n.USHER_LINE, n.CHECKING_TICKET))
            snack_count = sum(1 for n in npcs if n.state in (n.SNACK_LINE, n.BUYING_SNACK))
            seated_count = sum(1 for n in npcs if n.state == n.SEATED)
            total_active = len([n for n in npcs if not n.has_left])
            guests_display = f"{seated_count} S | {total_active} T"
        else:
            ticket_count = stats.cashier_queue
            usher_count = stats.usher_queue
            snack_count = stats.snack_queue
            guests_display = f"{stats.total_arrived}/{stats.total_seated}"

        speed_text = f"{self.simulation.speed}x"
        capsules = [
            (pygame.Rect(6, 6, 112, 46), "SIM TIME", f"{minutes:02d}:{seconds:02d}", C_TEXT_WHITE),
            (pygame.Rect(124, 6, 92, 46), "STATUS", run_label, run_color),
            (pygame.Rect(222, 6, 68, 46), "SPEED", speed_text, C_NEON_CYAN),
            (pygame.Rect(296, 6, 104, 46), "GUESTS", guests_display, C_NEON_GOLD),
            (pygame.Rect(406, 6, 116, 46), "AVG WAIT", f"{wait_minutes}:{wait_seconds:02d}", wait_color),
            (pygame.Rect(528, 6, 112, 46), "TARGET", "<= 10:00", C_NEON_GREEN),
        ]
        for rect, title, value, color in capsules:
            capsule(rect, title, value, color)

        # Accurate Live Queue Status Strip
        queue_text = (
            f"Live Queues: Ticket ({ticket_count}) • Usher ({usher_count}) • Concession ({snack_count})"
        )
        queue_surf = self._lf.render(queue_text, True, C_NEON_GOLD if (ticket_count + usher_count + snack_count) > 0 else C_TEXT_DIM)
        queue_panel = pygame.Surface(
            (queue_surf.get_width() + 16, queue_surf.get_height() + 8), pygame.SRCALPHA
        )
        queue_panel.fill((19, 22, 40, 220))
        queue_panel.blit(queue_surf, (8, 4))
        queue_x = SCREEN_W // 2 - queue_panel.get_width() // 2
        surface.blit(queue_panel, (queue_x, 55))


        # Live Event Log (bottom-left)
        if self._log and self._log_t > 0:
            alpha = min(255, int(255 * (self._log_t / 4.0)))
            for i, (txt, col) in enumerate(self._log):
                s = self._lf.render(txt, True, col)
                s.set_alpha(alpha)
                surface.blit(s, (12, SCREEN_H - 26 - i * 18))

        # Sandbox Controls Hint (bottom bar)
        hint_text = "[Click & Drag] Pan Camera  •  [Scroll / +/-] Zoom  •  [WASD / Arrows] Move  •  [Space] Pause  •  [F1] Settings"
        hint = self._lf.render(hint_text, True, (175, 185, 215))
        hint_panel = pygame.Surface((hint.get_width() + 16, hint.get_height() + 8), pygame.SRCALPHA)
        hint_panel.fill((12, 14, 28, 220))
        pygame.draw.rect(hint_panel, (45, 52, 85), hint_panel.get_rect(), 1, border_radius=4)
        hint_panel.blit(hint, (8, 4))
        surface.blit(hint_panel, (SCREEN_W // 2 - hint_panel.get_width() // 2, SCREEN_H - 28))

