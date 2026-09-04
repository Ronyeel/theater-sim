
from typing import Callable, Tuple, List
import pygame
from game.settings import (
    SCREEN_W, SCREEN_H, C_BG_DARK,
    C_NEON_GOLD, C_NEON_CYAN, C_NEON_GREEN, C_NEON_RED,
    C_TEXT_WHITE, C_TEXT_DIM, C_GOOD, C_BAD, C_WARN,
)
from game.ui.button import Button
from src.stats import format_minutes_seconds


def _font(size: int, bold: bool = False) -> pygame.font.Font:
    for font_name in ("segoeui", "helvetica", "arial", "consolas"):
        try:
            return pygame.font.SysFont(font_name, size, bold=bold)
        except Exception:
            continue
    return pygame.font.Font(None, size)


class ResultsScreen:

    def __init__(
        self,
        bridge,
        go_game: Callable[[], None],
        go_setup: Callable[[], None],
        go_title: Callable[[], None],
        quit_game: Callable[[], None],
    ) -> None:
        self.bridge = bridge
        self.go_game = go_game
        self.go_setup = go_setup
        self.go_title = go_title
        self.quit_game = quit_game
        self._t = 0.0
        self._page = 0

        self._title_f = _font(20, bold=True)
        self._val_f = _font(22, bold=True)
        self._sec_f = _font(13, bold=True)
        self._body_f = _font(12)
        self._sub_f = _font(11)
        self._mono_f = _font(10)

        bw, bh = 200, 38
        by = SCREEN_H - 52
        spacing = 16
        total_w = bw * 4 + spacing * 3
        start_x = SCREEN_W // 2 - total_w // 2

        self.btn_again = Button(pygame.Rect(start_x, by, bw, bh), "Run Again", C_NEON_GREEN, 12)
        self.btn_setup = Button(pygame.Rect(start_x + (bw + spacing), by, bw, bh), "Edit Parameters", C_NEON_CYAN, 12)
        self.btn_title = Button(pygame.Rect(start_x + (bw + spacing) * 2, by, bw, bh), "Main Menu", (180, 190, 210), 12)
        self.btn_quit = Button(pygame.Rect(start_x + (bw + spacing) * 3, by, bw, bh), "Quit", (220, 100, 110), 12)
        self.btn_page = Button(
            pygame.Rect(SCREEN_W // 2 - 90, by - 42, 180, 30),
            "SEAT LAYOUT >>", C_NEON_CYAN, 11,
        )

        self.btn_again.on_click(self._play_again)
        self.btn_setup.on_click(self.go_setup)
        self.btn_title.on_click(self.go_title)
        self.btn_quit.on_click(self.quit_game)
        self.btn_page.on_click(self._toggle_page)

    def _play_again(self) -> None:
        self.bridge.reset()
        self.go_game()

    def _toggle_page(self) -> None:
        self._page = 1 - self._page

    @property
    def _avg(self) -> float:
        return self.bridge.stats.avg_wait

    @property
    def _seated(self) -> int:
        return self.bridge.stats.total_seated

    @property
    def _arrived(self) -> int:
        return self.bridge.stats.total_arrived

    def _get_grade(self) -> Tuple[str, str, Tuple[int, int, int]]:
        avg = self._avg
        if avg == 0.0 and self._seated == 0:
            return "F", "No Flow", (239, 68, 68)
        if avg <= 5.0:
            return "A+", "Optimal", (34, 197, 94)
        if avg <= 8.0:
            return "A", "Target Met", (34, 197, 94)
        if avg <= 10.0:
            return "B+", "Compliant", (234, 179, 8)
        if avg <= 14.0:
            return "C", "Moderate Delay", (249, 115, 22)
        if avg <= 20.0:
            return "D", "Heavy Bottleneck", (249, 115, 22)
        return "F", "Congested", (239, 68, 68)

    def _get_recommendations(self) -> List[Tuple[str, str, Tuple[int, int, int]]]:
        avg = self._avg
        c = self.bridge.num_cashiers
        u = self.bridge.num_ushers
        s = self.bridge.num_servers
        recs = []

        if avg <= 10.0:
            recs.append((
                "SLA Target Passed",
                f"Average wait of {avg:.2f} min satisfies the 10-minute maximum constraint.",
                (34, 197, 94),
            ))
            if c > 6:
                recs.append((
                    "Cost Optimization",
                    f"Cashier staffing ({c}) is high. Reducing to 4–5 counters during off-peak hours preserves target wait times with lower labor costs.",
                    (148, 163, 184),
                ))
            else:
                recs.append((
                    "Staff Allocation",
                    f"Staffing ({c} Cashiers, {u} Ushers, {s} Servers) maintains stable queue flow.",
                    (148, 163, 184),
                ))
        else:
            recs.append((
                "SLA Target Exceeded",
                f"Average wait time of {avg:.2f} min exceeds the 10.0-minute target by {avg - 10.0:.2f} minutes.",
                (239, 68, 68),
            ))
            if c < 4:
                recs.append((
                    "Box Office Bottleneck",
                    f"Ticket service duration (1–3 min) causes delays. Increase Cashiers from {c} to at least 4–6 counters.",
                    (234, 179, 8),
                ))
            if s < 2 and self.bridge.food_prob > 0.4:
                recs.append((
                    "Concession Load",
                    f"Food orders take 1–5 min. Add at least 1 additional server to clear snack queues faster.",
                    (56, 189, 248),
                ))

        return recs

    def handle_event(self, evt: pygame.event.Event) -> None:
        if evt.type == pygame.KEYDOWN:
            if evt.key in (pygame.K_RIGHT, pygame.K_PAGEDOWN):
                self._page = min(1, self._page + 1)
                return
            if evt.key in (pygame.K_LEFT, pygame.K_PAGEUP):
                self._page = max(0, self._page - 1)
                return
        self.btn_page.handle_event(evt)
        for b in (self.btn_again, self.btn_setup, self.btn_title, self.btn_quit):
            b.handle_event(evt)

    def update(self, dt: float) -> None:
        self._t += dt
        self.btn_page.update(dt)
        for b in (self.btn_again, self.btn_setup, self.btn_title, self.btn_quit):
            b.update(dt)

    def _draw_histogram(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, (15, 19, 32), rect, border_radius=6)
        pygame.draw.rect(surface, (30, 38, 58), rect, 1, border_radius=6)

        t_surf = self._sec_f.render("Wait Time Distribution", True, (241, 245, 249))
        surface.blit(t_surf, (rect.x + 14, rect.y + 12))

        wait_times = self.bridge.wait_times
        bins = [
            ("0-3m", sum(1 for w in wait_times if 0 <= w < 3)),
            ("3-6m", sum(1 for w in wait_times if 3 <= w < 6)),
            ("6-10m", sum(1 for w in wait_times if 6 <= w <= 10)),
            ("10-15m", sum(1 for w in wait_times if 10 < w <= 15)),
            ("15-20m", sum(1 for w in wait_times if 15 < w <= 20)),
            ("20m+", sum(1 for w in wait_times if w > 20)),
        ]
        max_count = max([b[1] for b in bins] + [1])

        chart_x = rect.x + 36
        chart_y = rect.y + 40
        chart_w = rect.width - 50
        chart_h = rect.height - 70

        for i in (0.0, 0.5, 1.0):
            gy = chart_y + int(chart_h * (1.0 - i))
            val = int(max_count * i)
            pygame.draw.line(surface, (24, 30, 48), (chart_x, gy), (chart_x + chart_w, gy), 1)
            v_lbl = self._mono_f.render(str(val), True, (100, 116, 139))
            surface.blit(v_lbl, (chart_x - v_lbl.get_width() - 5, gy - 6))

        n_bins = len(bins)
        gap = 12
        bar_w = (chart_w - (n_bins + 1) * gap) // n_bins

        for i, (label, count) in enumerate(bins):
            bx = chart_x + gap + i * (bar_w + gap)
            bh = int((count / max_count) * (chart_h - 12)) if max_count > 0 else 0
            by = chart_y + chart_h - bh

            is_compliant = (i < 3)
            col = (34, 197, 94) if is_compliant else (239, 68, 68)

            if bh > 0:
                bar_rect = pygame.Rect(bx, by, bar_w, bh)
                pygame.draw.rect(surface, col, bar_rect, border_radius=3)
                cnt_lbl = self._mono_f.render(str(count), True, (241, 245, 249))
                surface.blit(cnt_lbl, (bx + bar_w // 2 - cnt_lbl.get_width() // 2, by - 12))

            lbl = self._mono_f.render(label, True, (148, 163, 184))
            surface.blit(lbl, (bx + bar_w // 2 - lbl.get_width() // 2, chart_y + chart_h + 6))

        pygame.draw.line(surface, (40, 50, 75), (chart_x, chart_y + chart_h), (chart_x + chart_w, chart_y + chart_h), 1)

    def _draw_timeline(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, (15, 19, 32), rect, border_radius=6)
        pygame.draw.rect(surface, (30, 38, 58), rect, 1, border_radius=6)

        t_surf = self._sec_f.render("Journey Wait Timeline", True, (241, 245, 249))
        surface.blit(t_surf, (rect.x + 14, rect.y + 12))

        chart_x = rect.x + 40
        chart_y = rect.y + 40
        chart_w = rect.width - 54
        chart_h = rect.height - 70

        wait_times = self.bridge.wait_times or [0.0]
        max_val = max(max(wait_times), 15.0)

        for val, col, label_str in ((0, (24, 30, 48), "0m"), (10, (120, 90, 30), "10m"), (max_val, (24, 30, 48), f"{int(max_val)}m")):
            gy = chart_y + chart_h - int((val / max_val) * chart_h)
            pygame.draw.line(surface, col if val != 10 else (160, 110, 35), (chart_x, gy), (chart_x + chart_w, gy), 1)
            v_lbl = self._mono_f.render(label_str, True, (234, 179, 8) if val == 10 else (100, 116, 139))
            surface.blit(v_lbl, (chart_x - v_lbl.get_width() - 5, gy - 6))

        t_lbl = self._mono_f.render("10.0m SLA Target", True, (234, 179, 8))
        t_y = chart_y + chart_h - int((10.0 / max_val) * chart_h)
        surface.blit(t_lbl, (chart_x + chart_w - t_lbl.get_width() - 4, max(chart_y + 2, t_y - 12)))

        pts = []
        n_points = min(len(wait_times), 60)
        step = max(1, len(wait_times) // n_points)
        sampled = wait_times[::step]

        for i, val in enumerate(sampled):
            px = chart_x + int((i / max(1, len(sampled) - 1)) * chart_w)
            py = chart_y + chart_h - int((val / max_val) * chart_h)
            pts.append((px, py))

        if len(pts) >= 2:
            area_poly = [(chart_x, chart_y + chart_h)] + pts + [(pts[-1][0], chart_y + chart_h)]
            poly_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.polygon(poly_surf, (56, 189, 248, 30), area_poly)
            surface.blit(poly_surf, (0, 0))

            pygame.draw.lines(surface, (56, 189, 248), False, pts, 2)
            for px, py in pts:
                pygame.draw.circle(surface, (125, 211, 252), (px, py), 2)

        pygame.draw.line(surface, (40, 50, 75), (chart_x, chart_y + chart_h), (chart_x + chart_w, chart_y + chart_h), 1)
        x_lbl1 = self._mono_f.render("t=0m (Open)", True, (100, 116, 139))
        x_lbl2 = self._mono_f.render(f"t={int(self.bridge.runtime)}m (Close)", True, (100, 116, 139))
        surface.blit(x_lbl1, (chart_x, chart_y + chart_h + 6))
        surface.blit(x_lbl2, (chart_x + chart_w - x_lbl2.get_width(), chart_y + chart_h + 6))

    def _draw_rec_card(self, surface: pygame.Surface, rect: pygame.Rect,
                       title: str, detail: str, col: Tuple[int,int,int]) -> None:
        card_bg = (*[max(0, c - 6) for c in (15, 19, 32)],)
        pygame.draw.rect(surface, (18, 23, 40), rect, border_radius=7)
        pygame.draw.rect(surface, col, rect, 1, border_radius=7)

        dot_r = 4
        pygame.draw.circle(surface, col, (rect.x + 16, rect.y + 16), dot_r)

        t_title = self._sec_f.render(title, True, col)
        surface.blit(t_title, (rect.x + 28, rect.y + 8))

        pygame.draw.line(surface, (30, 40, 60), (rect.x + 12, rect.y + 26),
                         (rect.right - 12, rect.y + 26), 1)

        words = detail.split()
        lines, line = [], []
        max_w = rect.width - 26
        for word in words:
            test = self._body_f.render(" ".join(line + [word]), True, (255,255,255))
            if test.get_width() > max_w and line:
                lines.append(" ".join(line))
                line = [word]
            else:
                line.append(word)
        if line:
            lines.append(" ".join(line))

        for i, ln in enumerate(lines):
            surf = self._body_f.render(ln, True, (194, 210, 230))
            surface.blit(surf, (rect.x + 14, rect.y + 32 + i * 16))

    def _draw_final_seating(self, surface: pygame.Surface) -> None:
        hx, hy = 28, 18
        title_surf = self._title_f.render("Final Reserved Seat Layout", True, (248, 250, 252))
        surface.blit(title_surf, (hx, hy))
        page_label = self._mono_f.render("PAGE 2 / 2", True, (120, 140, 170))
        surface.blit(page_label, (SCREEN_W - 28 - page_label.get_width(), hy + 5))
        pygame.draw.line(
            surface, (30, 38, 60),
            (hx, hy + title_surf.get_height() + 8),
            (SCREEN_W - hx, hy + title_surf.get_height() + 8),
            1,
        )

        seating = self.bridge.seating
        panel = pygame.Rect(62, 100, SCREEN_W - 124, 438)
        pygame.draw.rect(surface, (14, 18, 30), panel, border_radius=8)
        pygame.draw.rect(surface, (28, 36, 56), panel, 1, border_radius=8)

        screen_label = self._sec_f.render("SEATING CHART", True, C_NEON_CYAN)
        surface.blit(screen_label, (panel.centerx - screen_label.get_width() // 2, panel.y + 18))
        pygame.draw.line(
            surface, C_NEON_CYAN,
            (panel.x + 260, panel.y + 42),
            (panel.right - 260, panel.y + 42),
            2,
        )

        seat_w, seat_h, gap = 34, 34, 6
        grid_w = seating.cols * seat_w + (seating.cols - 1) * gap
        grid_x = panel.centerx - grid_w // 2
        grid_y = panel.y + 74
        row_font = self._mono_f
        seat_font = self._sec_f

        for row in range(1, seating.rows + 1):
            row_label = row_font.render(f"R{row}", True, (148, 163, 184))
            surface.blit(row_label, (grid_x - row_label.get_width() - 12,
                                     grid_y + (row - 1) * (seat_h + gap) + 18))
            for col in range(1, seating.cols + 1):
                x = grid_x + (col - 1) * (seat_w + gap)
                y = grid_y + (row - 1) * (seat_h + gap)
                taken = seating.chart[row - 1][col - 1] == "X"
                color = C_NEON_RED if taken else C_NEON_GREEN
                fill = (92, 32, 48) if taken else (28, 72, 52)
                rect = pygame.Rect(x, y, seat_w, seat_h)
                pygame.draw.rect(surface, fill, rect, border_radius=5)
                pygame.draw.rect(surface, color, rect, 1, border_radius=5)

                mark = seat_font.render("X" if taken else "A", True, C_TEXT_WHITE)
                surface.blit(mark, (rect.centerx - mark.get_width() // 2,
                                    rect.centery - mark.get_height() // 2))

        reserved_count = sum(
            1 for row in seating.chart for value in row if value == "X"
        )
        legend_y = panel.bottom - 34
        pygame.draw.rect(surface, C_NEON_RED, (panel.x + 24, legend_y, 12, 12), border_radius=2)
        reserved_text = self._sub_f.render(f"Reserved: {reserved_count}", True, (220, 225, 235))
        surface.blit(reserved_text, (panel.x + 42, legend_y - 2))
        pygame.draw.rect(surface, (52, 110, 78), (panel.x + 180, legend_y, 12, 12), border_radius=2)
        open_text = self._sub_f.render("Open", True, (220, 225, 235))
        surface.blit(open_text, (panel.x + 198, legend_y - 2))

        hint = self._sub_f.render("LEFT: summary    RIGHT: seat layout", True, (120, 140, 170))
        surface.blit(hint, (SCREEN_W - 28 - hint.get_width(), legend_y - 2))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((11, 14, 23))

        if self._page == 1:
            self._draw_final_seating(surface)
            self.btn_page.text = "<< SUMMARY"
            self.btn_page.draw(surface)
            for b in (self.btn_again, self.btn_setup, self.btn_title, self.btn_quit):
                b.draw(surface)
            return

        hx, hy = 28, 18
        title_surf = self._title_f.render("Simulation Performance Summary", True, (248, 250, 252))
        surface.blit(title_surf, (hx, hy))
        page_label = self._mono_f.render("PAGE 1 / 2   RIGHT: seat layout", True, (120, 140, 170))
        surface.blit(page_label, (SCREEN_W - 28 - page_label.get_width(), hy + 5))

        pygame.draw.line(surface, (30, 38, 60), (hx, hy + title_surf.get_height() + 8), (SCREEN_W - hx, hy + title_surf.get_height() + 8), 1)

        grade_letter, grade_status, grade_col = self._get_grade()
        badge_w = 210
        badge_rect = pygame.Rect(SCREEN_W - 28 - badge_w, hy + 4, badge_w, 34)
        pygame.draw.rect(surface, (18, 24, 38), badge_rect, border_radius=6)
        pygame.draw.rect(surface, grade_col, badge_rect, 1, border_radius=6)
        b_txt = self._sec_f.render(f"Grade: {grade_letter}  —  {grade_status}", True, grade_col)
        surface.blit(b_txt, (badge_rect.centerx - b_txt.get_width() // 2,
                             badge_rect.centery - b_txt.get_height() // 2))

        kpi_y = hy + title_surf.get_height() + 18
        kpi_rect = pygame.Rect(hx, kpi_y, SCREEN_W - 56, 76)
        pygame.draw.rect(surface, (14, 18, 30), kpi_rect, border_radius=8)
        pygame.draw.rect(surface, (28, 36, 56), kpi_rect, 1, border_radius=8)

        avg = self._avg
        wm, ws = format_minutes_seconds(avg)
        sla_pass = avg <= 10.0
        sla_col = (34, 197, 94) if sla_pass else (239, 68, 68)

        kpis = [
            ("AVG WAIT",       f"{wm}m {ws:02d}s",           "<= 10m SLA Target",                sla_col),
            ("SEATED",         f"{self._seated}",             f"{self._arrived} arrived",         (248, 250, 252)),
            ("STAFF",          f"{self.bridge.num_cashiers}C · {self.bridge.num_ushers}U · {self.bridge.num_servers}S",
                                "Cashiers · Ushers · Servers", (203, 213, 225)),
            ("SLA STATUS",     "PASSED" if sla_pass else "FAILED",
                                f"Target: ≤ 10 min  |  Grade: {grade_letter}", sla_col),
        ]

        col_w = kpi_rect.width // 4
        for i, (lbl, val, sub, col) in enumerate(kpis):
            cx = kpi_rect.x + i * col_w

            if i > 0:
                pygame.draw.line(surface, (32, 42, 64),
                                 (cx, kpi_rect.y + 10), (cx, kpi_rect.bottom - 10), 1)

            t_lbl = self._mono_f.render(lbl, True, (120, 140, 170))
            t_val = self._val_f.render(val, True, col)
            t_sub = self._sub_f.render(sub, True, (175, 195, 220))

            px = cx + 18
            surface.blit(t_lbl, (px, kpi_rect.y + 8))
            surface.blit(t_val, (px, kpi_rect.y + 22))
            surface.blit(t_sub, (px, kpi_rect.y + 56))

        chart_y = kpi_y + kpi_rect.height + 14
        chart_w = (SCREEN_W - 56 - 14) // 2
        chart_h = 230

        rect_hist = pygame.Rect(hx, chart_y, chart_w, chart_h)
        rect_time = pygame.Rect(hx + chart_w + 14, chart_y, chart_w, chart_h)

        self._draw_histogram(surface, rect_hist)
        self._draw_timeline(surface, rect_time)

        rec_y = chart_y + chart_h + 14
        remaining_h = SCREEN_H - 54 - rec_y

        rec_hdr = self._sec_f.render("Operational Analysis & Recommendations", True, (200, 215, 240))
        surface.blit(rec_hdr, (hx, rec_y))
        pygame.draw.line(surface, (35, 44, 68),
                         (hx, rec_y + rec_hdr.get_height() + 3),
                         (SCREEN_W - hx, rec_y + rec_hdr.get_height() + 3), 1)

        recs = self._get_recommendations()
        card_y = rec_y + rec_hdr.get_height() + 10
        card_h = max(62, (remaining_h - rec_hdr.get_height() - 16) // max(1, len(recs)))
        card_h = min(card_h, 78)

        for i, (rec_title, detail, col) in enumerate(recs):
            card_rect = pygame.Rect(hx, card_y + i * (card_h + 6),
                                    SCREEN_W - 56, card_h)
            self._draw_rec_card(surface, card_rect, rec_title, detail, col)

        for b in (self.btn_again, self.btn_setup, self.btn_title, self.btn_quit):
            b.draw(surface)
        self.btn_page.text = "SEAT LAYOUT >>"
        self.btn_page.draw(surface)

