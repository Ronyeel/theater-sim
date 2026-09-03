from typing import Optional, Callable
import math
import random
import pygame
from game.settings import (
    SCREEN_W, SCREEN_H, TILE_SIZE,
    C_BG_DARK, C_NEON_GOLD, C_NEON_PINK, C_NEON_CYAN,
    C_NEON_GREEN, C_NEON_RED, C_BAD, C_TEXT_WHITE, C_TEXT_DIM,
    DEFAULT_CASHIERS, DEFAULT_USHERS, DEFAULT_SERVERS,
    CASHIER_DESK_COLS, CASHIER_DESK_ROW,
    USHER_DESK_COLS, USHER_DESK_ROW,
    SNACK_DESK_COLS, SNACK_DESK_ROW,
    MAP_COLS, MAP_ROWS, TILE_DESK, TILE_SEAT, TILE_SNACK, TILE_USHER,
    TILE_SECURITY, PLAYER_SPAWN,
)
from game.core.camera import Camera
from game.core.tilemap import TileMap, tile_at
from game.core.particles import ParticleSystem
from game.core import asset_loader as AL
from game.entities.npc import build_npcs
from game.entities.player import Player
from game.backend_bridge import TheaterSimulationBridge
from game.world.interactions import build_zones, find_nearest_zone
from game.ui.speech_bubble import SpeechBubble
from game.ui.simulation_panel import SimulationPanel
from game.ui.hud import HUD
from game.ui.seating_chart import SeatingChartPanel
from game.world.seat_chart import chart_to_tile, tile_to_chart


from game.core.lighting import LightingSystem


def _font(name, size, bold=False):
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


class GameScreen:

    def __init__(
        self,
        go_title: Callable[[], None],
        go_results: Optional[Callable[[], None]] = None,
        bridge: Optional[TheaterSimulationBridge] = None,
    ) -> None:
        self.go_title = go_title
        self.go_results = go_results or go_title
        self._t = 0.0

        self.camera = Camera()
        self.tilemap = TileMap()
        self._world_surface = pygame.Surface((SCREEN_W, SCREEN_H))

        if bridge is not None:
            self.simulation = bridge
            self._num_cashiers = bridge.num_cashiers
            self._num_ushers = bridge.num_ushers
            self._num_servers = bridge.num_servers
            self.simulation._on_arrival = self._spawn_simulation_npc
        else:
            self._num_cashiers = DEFAULT_CASHIERS
            self._num_ushers = DEFAULT_USHERS
            self._num_servers = DEFAULT_SERVERS
            self.simulation = TheaterSimulationBridge(
                self._num_cashiers, self._num_servers, self._num_ushers,
                seed=42, on_arrival=self._spawn_simulation_npc,
            )

        self.staff = []
        self.zones = build_zones(self._num_cashiers, self._num_ushers, self._num_servers)

        self.particles = ParticleSystem()
        self.bubbles: list[SpeechBubble] = []
        self.lighting = LightingSystem()

        self.npcs = []
        self._movie_finished = False
        self._finish_timer = 0.0
        self._finish_notified = False
        self._finish_banner_rect = pygame.Rect(SCREEN_W // 2 - 250, 95, 500, 48)

        self.simulation_panel = SimulationPanel(self.simulation, self._apply_simulation_config)
        self.seating_panel = SeatingChartPanel(self.simulation.seating)
        self.seating_panel.on_reserve_callback = self._on_player_seat_reserved
        self.hud = HUD(
            self.simulation,
            npcs_provider=lambda: self.npcs,
            on_toggle_seats=self.seating_panel.toggle,
        )

        self._fading = False
        self._fade_alpha = 0
        self._fade_surf = pygame.Surface((SCREEN_W, SCREEN_H))
        self._fade_surf.fill((0, 0, 0))
        self._show_collision_debug = False

        self.controlled_player = Player()
        self._player_mode = False
        self._player_msg = ""
        self._player_msg_t = 0.0
        self._player_msg_color = C_TEXT_WHITE

        for pos, data in self.simulation.seating.seat_data.items():
            if data.get("customer_name") in ("Player", "Student / Player"):
                self.controlled_player.has_ticket = True
                self.controlled_player.seated_at_pos = pos
                break

    def _apply_simulation_config(self, config: dict):
        should_reset = config.get("reset", False)
        bridge = self.simulation
        for key, value in config.items():
            if key != "reset":
                setattr(bridge, key, value)

        if should_reset:
            bridge.reset()
            self._num_cashiers = bridge.num_cashiers
            self._num_ushers = bridge.num_ushers
            self._num_servers = bridge.num_servers
            self.zones = build_zones(self._num_cashiers, self._num_ushers, self._num_servers)
            self.npcs = []
            self._movie_finished = False
            self._finish_timer = 0.0
            self._finish_notified = False
            self.seating_panel.bind(bridge.seating)
            self.hud.add_log("Simulation restarted with new settings.", C_NEON_GOLD)
        else:
            self._num_cashiers = bridge.num_cashiers
            self._num_ushers = bridge.num_ushers
            self._num_servers = bridge.num_servers

            if hasattr(bridge, "theater") and bridge.theater is not None:
                bridge.theater.num_cashiers = self._num_cashiers
                bridge.theater.num_ushers = self._num_ushers
                bridge.theater.num_servers = self._num_servers
                if hasattr(bridge.theater.cashier, "_capacity"):
                    bridge.theater.cashier._capacity = max(1, self._num_cashiers)
                if hasattr(bridge.theater.usher, "_capacity"):
                    bridge.theater.usher._capacity = max(1, self._num_ushers)
                if hasattr(bridge.theater.server, "_capacity"):
                    bridge.theater.server._capacity = max(1, self._num_servers)

            self.zones = build_zones(self._num_cashiers, self._num_ushers, self._num_servers)
            for npc in self.npcs:
                npc.set_service_capacity(self._num_cashiers, self._num_ushers, self._num_servers)

            self.hud.add_log(
                f"Live staffing updated: {self._num_cashiers}C | {self._num_ushers}U | {self._num_servers}S",
                C_NEON_CYAN,
            )



    _MAX_VISUAL_NPCS = 30

    def _spawn_simulation_npc(self, moviegoer_id: int):
        # Only spawn a new visual sprite if under the cap.
        if len(self.npcs) >= self._MAX_VISUAL_NPCS:
            return
        guests = build_npcs(1, slot_offset=moviegoer_id)
        for guest in guests:
            guest.seating = self.simulation.seating
            guest.set_service_capacity(
                self._num_cashiers, self._num_ushers, self._num_servers,
            )
        self.npcs.extend(guests)


    def handle_event(self, evt: pygame.event.Event):
        if self.simulation_panel.handle_event(evt):
            return
        if self.seating_panel.handle_event(evt):
            return

        if not self.simulation.is_running:
            if evt.type == pygame.KEYDOWN and evt.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.go_results()
                return
            if evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
                if self._finish_banner_rect.collidepoint(evt.pos):
                    self.go_results()
                    return

        if self.hud.handle_event(evt):
            return

        if evt.type == pygame.MOUSEBUTTONDOWN:
            if evt.button in (1, 2, 3):
                self.camera.start_drag(evt.pos)

        elif evt.type == pygame.MOUSEBUTTONUP:
            if evt.button in (1, 2, 3):
                self.camera.stop_drag()
        elif evt.type == pygame.MOUSEMOTION:
            self.camera.handle_mouse_motion(evt.pos, evt.buttons)
        elif evt.type == pygame.MOUSEWHEEL:
            self.camera.adjust_zoom(0.08 * evt.y, focus_pos=pygame.mouse.get_pos())

        elif evt.type == pygame.KEYDOWN:
            # F3: toggle between player mode and spectator mode
            if evt.key == pygame.K_F3:
                self._player_mode = not self._player_mode
                if self._player_mode:
                    self.hud.add_log("PLAYER MODE — use WASD to walk around", C_NEON_GREEN)
                else:
                    self.hud.add_log("SPECTATOR MODE — drag/scroll to pan camera", C_NEON_CYAN)
                return
            if evt.key == pygame.K_F1:
                self.simulation_panel.open()
            elif evt.key == pygame.K_F2:
                self.seating_panel.toggle()
            elif evt.key == pygame.K_SPACE:
                if self._player_mode:
                    self._player_interact()
                    return
                is_p = getattr(self.simulation, "is_paused", False)
                self.simulation.is_paused = not is_p
                self.hud.add_log("Simulation PAUSED" if self.simulation.is_paused else "Simulation RESUMED", C_NEON_CYAN)
            elif evt.key == pygame.K_f:
                speeds = [1, 2, 5, 10]
                cur_idx = speeds.index(self.simulation.speed) if self.simulation.speed in speeds else 0
                next_speed = speeds[(cur_idx + 1) % len(speeds)]
                self.simulation.speed = next_speed
                self.hud.add_log(f"Fast Forward: {next_speed}x", C_NEON_CYAN)
            elif evt.key in (pygame.K_r, pygame.K_TAB):
                if not self._player_mode:
                    self.simulation.reset()
                    self.seating_panel.bind(self.simulation.seating)
                    self.npcs = []
                    self._movie_finished = False
                    self._finish_timer = 0.0
                    self._finish_notified = False
                    self.hud.add_log("Simulation reset.", C_NEON_GOLD)
            elif evt.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                self.camera.adjust_zoom(0.1)
            elif evt.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.camera.adjust_zoom(-0.1)
            elif evt.key == pygame.K_ESCAPE:
                if self._player_mode:
                    self._player_mode = False
                    self.hud.add_log("SPECTATOR MODE — drag/scroll to pan camera", C_NEON_CYAN)
                else:
                    self._show_final_seating_layout()
                    self.go_title()


    def update(self, dt: float):
        self._t += dt

        self.simulation_panel.update(dt)
        self.seating_panel.update(dt)
        if self.simulation_panel.visible:
            return

        keys = pygame.key.get_pressed()

        if self._player_mode:
            # Player mode: WASD drives the controlled player; camera follows
            self.controlled_player.handle_keys(keys)
            self.controlled_player.update(dt)

            if self.controlled_player.usher_gate_blocked and not self.controlled_player.ticket_checked:
                if not self.controlled_player.has_ticket:
                    self._player_set_msg("GATE BLOCKED: Purchase a ticket at the Cashier first!", C_NEON_RED)
                else:
                    self._player_set_msg("GATE BLOCKED: Present your ticket to an Usher to pass!", C_NEON_RED)
            elif self.controlled_player.ticket_gate_blocked and not self.controlled_player.ticket_checked:
                self._player_set_msg("DOOR LOCKED: Ticket must be checked by an Usher first!", C_NEON_RED)

            # Centre camera on player with gentle lerp
            target_cx = self.controlled_player.x - SCREEN_W / (2 * self.camera.zoom)
            target_cy = self.controlled_player.y - SCREEN_H / (2 * self.camera.zoom)
            self.camera.x += (target_cx - self.camera.x) * min(1.0, 8.0 * dt)
            self.camera.y += (target_cy - self.camera.y) * min(1.0, 8.0 * dt)
            self.camera._clamp_bounds()
        else:
            # Spectator mode: arrow/WASD pans the free camera
            pdx = (1 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0)
            pdy = (1 if keys[pygame.K_s] or keys[pygame.K_DOWN] else 0) - (1 if keys[pygame.K_w] or keys[pygame.K_UP] else 0)
            if pdx != 0 or pdy != 0:
                self.camera.pan(pdx, pdy, dt)

        self.camera.update(dt)

        is_paused = getattr(self.simulation, "is_paused", False)
        sim_dt = 0.0 if is_paused else (dt * self.simulation.speed)

        if not is_paused:
            self.tilemap.update(sim_dt)

            for staff in self.staff:
                staff.update(sim_dt)

            for z in self.zones:
                z.update(sim_dt)

            for npc in self.npcs:
                npc.update(sim_dt, self.npcs, movie_finished=self._movie_finished)
            # Prune sprites that have left so new ones can spawn up to the cap.
            self.npcs = [npc for npc in self.npcs if not npc.has_left]

            self.simulation.update(dt)
            if not self.simulation.is_running:
                if not self._finish_notified:
                    self._movie_finished = True
                    self._finish_notified = True
                    self.hud.add_log("SIMULATION FINISHED! Generating report card...", C_NEON_GOLD)

                self._finish_timer += dt
                if self._finish_timer >= 2.0:
                    self.go_results()
                    return

            self.particles.update(dt)
            for b in self.bubbles:
                b.update(dt)
            self.bubbles = [b for b in self.bubbles if b.alive]

        self.lighting.update(sim_dt if not is_paused else dt * 0.5)
        self.hud.update(dt)
        if self._fading:
            self._fade_alpha = min(255, self._fade_alpha + 160 * dt)
            if self._fade_alpha >= 255:
                self.go_title()
                self._fading = False
        if self._player_msg_t > 0:
            self._player_msg_t -= dt


    def _on_player_seat_reserved(self, row: int, col: int):
        p = self.controlled_player
        p.has_ticket = True
        p.stage = "need_check"
        p.seated_at_pos = (row, col)
        p.flash(C_NEON_GOLD)
        self._player_set_msg(f"Ticket Purchased (₱250)! Reserved Row {row} Seat {col}. Proceed to Usher gate.", C_NEON_GOLD)
        self.hud.add_log(f"[Box Office] Ticket purchased! Reserved Row {row}, Seat {col}.", C_NEON_GOLD)

    def _player_set_msg(self, msg: str, color=None):
        self._player_msg = msg
        self._player_msg_t = 3.5
        self._player_msg_color = color or C_TEXT_WHITE

    def _player_interact(self):
        p = self.controlled_player
        seating = self.simulation.seating
        zone = find_nearest_zone(self.zones, p.x, p.y)

        if zone is None:
            self._player_set_msg("Nothing nearby to interact with.", C_TEXT_DIM)
            return

        name = zone.name

        if name == "security":
            if p.stage in ("entering", "at_security"):
                p.stage = "browsing"
                self._player_set_msg("Security check passed! Please purchase a ticket at the Cashier.", C_NEON_GREEN)
                self.hud.add_log("[Player] Passed security checkpoint.", C_NEON_GREEN)
                p.flash(C_NEON_GREEN)
            else:
                self._player_set_msg("Security check already completed.", C_TEXT_DIM)
            return

        if name in ("board", "poster"):
            self._player_set_msg("Now Showing: Starlight Express (Screen 1, 7:30 PM)", C_NEON_CYAN)
            return

        if name == "cashier":
            desk_col = int(zone.x) // TILE_SIZE
            if desk_col in CASHIER_DESK_COLS:
                idx = CASHIER_DESK_COLS.index(desk_col)
                if idx >= self._num_cashiers:
                    self._player_set_msg(f"Cashier #{idx + 1} is CLOSED. Please use an open cashier counter.", C_NEON_RED)
                    p.flash(C_NEON_RED)
                    return

            npcs_in_line = [
                npc for npc in self.npcs
                if not npc.has_left and npc.state in (npc.TICKET_LINE, npc.BUYING_TICKET)
                and abs(npc.x - zone.x) < 28 and npc.y <= p.y + 12
            ]
            if npcs_in_line:
                self._player_set_msg("Please wait in line! A customer is being served ahead.", C_NEON_RED)
                p.flash(C_NEON_RED)
                return

            if p.has_ticket and p.seated_at_pos:
                self._player_set_msg("You already hold a ticket! Head to the Usher gate.", C_TEXT_DIM)
                return

            self.seating_panel.open()
            self._player_set_msg("Welcome to the Box Office! Select your seat on the chart.", C_NEON_GOLD)
            self.hud.add_log("[Box Office] Please select your seat reservation on the chart.", C_NEON_GOLD)
            return

        if name == "usher":
            desk_col = int(zone.x) // TILE_SIZE
            if desk_col in USHER_DESK_COLS:
                idx = USHER_DESK_COLS.index(desk_col)
                if idx >= self._num_ushers:
                    self._player_set_msg(f"Usher Station #{idx + 1} is CLOSED. Please use an active usher station.", C_NEON_RED)
                    p.flash(C_NEON_RED)
                    return

            npcs_at_usher = [
                npc for npc in self.npcs
                if not npc.has_left and npc.state in (npc.USHER_LINE, npc.CHECKING_TICKET)
                and abs(npc.x - zone.x) < 28 and npc.y <= p.y + 12
            ]
            if npcs_at_usher:
                self._player_set_msg("Please wait in line! Another guest is at the Usher station.", C_NEON_RED)
                p.flash(C_NEON_RED)
                return

            if not p.has_ticket:
                self._player_set_msg("ACCESS DENIED: You must purchase a ticket from the Cashier first!", C_NEON_RED)
                p.flash(C_NEON_RED)
                return

            if p.ticket_checked:
                self._player_set_msg("Your ticket is already validated. You may enter the theater.", C_TEXT_DIM)
                return

            p.ticket_checked = True
            p.stage = "need_seat"
            p.flash(C_NEON_CYAN)
            self._player_set_msg("Ticket Validated! Usher gate unlocked. Enjoy your movie!", C_NEON_CYAN)
            self.hud.add_log("[Player] Ticket validated by Usher. Gate opened.", C_NEON_CYAN)
            return

        if name == "snack":
            desk_col = int(zone.x) // TILE_SIZE
            if desk_col in SNACK_DESK_COLS:
                idx = SNACK_DESK_COLS.index(desk_col)
                if idx >= self._num_servers:
                    self._player_set_msg(f"Concession Counter #{idx + 1} is CLOSED. Please use an open counter.", C_NEON_RED)
                    p.flash(C_NEON_RED)
                    return

            npcs_at_snack = [
                npc for npc in self.npcs
                if not npc.has_left and npc.state in (npc.SNACK_LINE, npc.BUYING_SNACK)
                and abs(npc.x - zone.x) < 28 and abs(npc.y - zone.y) < 24
            ]
            if npcs_at_snack:
                self._player_set_msg("Please wait in line! Another customer is ordering at the counter.", C_NEON_RED)
                p.flash(C_NEON_RED)
                return

            if not p.ticket_checked:
                self._player_set_msg("Please validate your ticket with an Usher before buying concessions.", C_NEON_RED)
                p.flash(C_NEON_RED)
                return

            if p.has_food:
                self._player_set_msg("You already purchased Popcorn & Soda!", C_TEXT_DIM)
                return

            p.has_food = True
            p.flash(C_NEON_CYAN)
            self._player_set_msg("🍿 Bought Popcorn & Soda! Head inside the auditorium to sit.", C_NEON_CYAN)
            self.hud.add_log("[Player] Purchased Popcorn & Soda at concessions.", C_NEON_CYAN)
            return

        if name == "seat":
            if not p.ticket_checked:
                self._player_set_msg("AUDITORIUM RESTRICTION: Ticket must be validated by an Usher first!", C_NEON_RED)
                p.flash(C_NEON_RED)
                return

            p_col = int(p.x) // TILE_SIZE
            p_row = int(p.y) // TILE_SIZE
            chart_pos = tile_to_chart(p_col, p_row)

            if not chart_pos:
                best_d = float("inf")
                for chart_r in range(1, seating.rows + 1):
                    for chart_c in range(1, seating.cols + 1):
                        scol, srow = chart_to_tile(chart_r, chart_c)
                        wx = scol * TILE_SIZE + TILE_SIZE // 2
                        wy = srow * TILE_SIZE + TILE_SIZE // 2
                        d = math.hypot(p.x - wx, p.y - wy)
                        if d < best_d and d < 48:
                            best_d = d
                            chart_pos = (chart_r, chart_c)

            if not chart_pos:
                self._player_set_msg("Please step directly adjacent to a seat to sit down.", C_TEXT_DIM)
                return

            cr, cc = chart_pos
            info = seating.seat_data.get((cr, cc), {})
            is_player_seat = (p.seated_at_pos == (cr, cc)) or (info.get("customer_name") in ("Player", "Student / Player"))

            if is_player_seat:
                p.stage = "seated"
                p.seated_at_pos = (cr, cc)
                scol, srow = chart_to_tile(cr, cc)
                p.x = float(scol * TILE_SIZE + TILE_SIZE // 2)
                p.y = float(srow * TILE_SIZE + TILE_SIZE // 2)
                p._direction = 3
                p.flash(C_NEON_GREEN)
                self._player_set_msg(f"You sat down in your reserved seat (Row {cr}, Seat {cc}). Enjoy the show!", C_NEON_GREEN)
                self.hud.add_log(f"[Theater] Player seated at Row {cr}, Seat {cc}.", C_NEON_GREEN)
                return

            if p.seated_at_pos is not None:
                old_r, old_c = p.seated_at_pos
                self._player_set_msg(f"Your assigned seat is Row {old_r} Seat {old_c}. Please sit in your reserved seat!", C_NEON_RED)
                p.flash(C_NEON_RED)
                return

            if seating.chart[cr - 1][cc - 1] == 'X':
                occupant = info.get("customer_name", "another guest")
                self._player_set_msg(f"Sorry, Row {cr} Seat {cc} is already taken by {occupant}!", C_NEON_RED)
                p.flash(C_NEON_RED)
                return

            ok, msg = seating.reserve(cr, cc, customer_name="Player")
            if ok:
                p.stage = "seated"
                p.seated_at_pos = (cr, cc)
                scol, srow = chart_to_tile(cr, cc)
                p.x = float(scol * TILE_SIZE + TILE_SIZE // 2)
                p.y = float(srow * TILE_SIZE + TILE_SIZE // 2)
                p._direction = 3
                p.flash(C_NEON_GREEN)
                self._player_set_msg(f"Seat Reserved: Row {cr} Seat {cc}. Enjoy the film!", C_NEON_GREEN)
                self.hud.add_log(f"[Reservation] Player reserved seat Row {cr}, Seat {cc}.", C_NEON_GREEN)
                self.seating_panel.bind(seating)
            else:
                self._player_set_msg(f"Reservation failed: {msg}", C_NEON_RED)
                p.flash(C_NEON_RED)
            return

        if name == "exit":
            if p.stage not in ("seated", "need_exit") and not self._movie_finished:
                self._player_set_msg("Find a seat and watch the movie before exiting!", C_NEON_RED)
                return
            p.stage = "need_exit"
            self._player_set_msg("You exited the theater. Thanks for visiting!", C_NEON_GOLD)
            self.hud.add_log("[Player] Exited the theater.", C_NEON_GOLD)
            return

        self._player_set_msg(f"Interact: {zone.label or zone.name}", C_TEXT_WHITE)

    def _show_final_seating_layout(self):
        seating = self.simulation.seating
        filled = sum(
            1 for r in range(seating.rows)
            for c in range(seating.cols)
            if seating.chart[r][c] == 'X'
        )
        total = seating.rows * seating.cols
        self.hud.add_log(
            f"[Exit] Final seating: {filled}/{total} seats occupied.",
            C_NEON_GOLD,
        )
        self.seating_panel.open()

    def _draw_exterior(self, surface: pygame.Surface):
        surface.fill((7, 12, 28))

    def _draw_seat_occupancy(self, surface: pygame.Surface):
        seating = self.simulation.seating
        font = _font("consolas", 11, bold=True)
        show_letters = self.camera.zoom >= 0.8
        for chart_row in range(1, seating.rows + 1):
            for chart_col in range(1, seating.cols + 1):
                col, row = chart_to_tile(chart_row, chart_col)
                taken = seating.chart[chart_row - 1][chart_col - 1] == 'X'

                sx, sy = self.camera.world_to_screen(
                    col * TILE_SIZE + TILE_SIZE // 2,
                    row * TILE_SIZE + TILE_SIZE // 2,
                )
                overlay = pygame.Surface((TILE_SIZE - 8, TILE_SIZE - 8), pygame.SRCALPHA)
                if taken:
                    overlay.fill((40, 8, 16, 110))
                else:
                    overlay.fill((20, 90, 45, 50))
                surface.blit(overlay, (int(sx) - overlay.get_width() // 2,
                                       int(sy) - overlay.get_height() // 2))

                if show_letters:
                    mark = font.render('X' if taken else 'A', True,
                                       (255, 150, 150) if taken else (160, 255, 190))
                    surface.blit(mark, (int(sx) - mark.get_width() // 2,
                                        int(sy) - mark.get_height() // 2))

    def _draw_stall_availability(self, surface: pygame.Surface):
        groups = (
            (CASHIER_DESK_COLS, CASHIER_DESK_ROW, self._num_cashiers),
            (USHER_DESK_COLS, USHER_DESK_ROW, self._num_ushers),
            (SNACK_DESK_COLS, SNACK_DESK_ROW - 1, self._num_servers),
        )
        font = _font("consolas", 9, bold=True)
        for cols, row, capacity in groups:
            for index, col in enumerate(cols):
                if index < capacity:
                    continue
                sx, sy = self.camera.world_to_screen(
                    col * TILE_SIZE + TILE_SIZE // 2,
                    row * TILE_SIZE + TILE_SIZE // 2,
                )
                text = font.render("CLOSED", True, (255, 220, 220))
                badge = pygame.Rect(int(sx) - text.get_width() // 2 - 4, int(sy) - 8,
                                    text.get_width() + 8, text.get_height() + 4)
                pygame.draw.rect(surface, (120, 35, 48), badge, border_radius=3)
                pygame.draw.rect(surface, C_NEON_RED, badge, 1, border_radius=3)
                surface.blit(text, (badge.x + 4, badge.y + 2))

    def _draw_collision_debug(self, surface: pygame.Surface):
        stall_tiles = {TILE_DESK, TILE_SNACK, TILE_USHER, TILE_SECURITY}
        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                tile = tile_at(col, row)
                if tile not in stall_tiles and tile != TILE_SEAT:
                    continue
                sx, sy = self.camera.world_to_screen(col * TILE_SIZE, row * TILE_SIZE)
                rect = pygame.Rect(int(sx), int(sy), TILE_SIZE, TILE_SIZE)
                color = (255, 75, 75) if tile in stall_tiles else (255, 210, 75)
                pygame.draw.rect(surface, color, rect, 2)

        for npc in self.npcs:
            sx, sy = self.camera.world_to_screen(npc.x, npc.y)
            pygame.draw.circle(surface, (75, 230, 255), (int(sx), int(sy)), 8, 2)
            pygame.draw.circle(surface, (75, 230, 255), (int(sx), int(sy)), 16, 1)

        font = _font("consolas", 12, bold=True)
        label = font.render("COLLISION: red stall  yellow seat  cyan NPC", True, (255, 255, 255))
        panel = pygame.Surface((label.get_width() + 12, label.get_height() + 8), pygame.SRCALPHA)
        panel.fill((10, 8, 24, 210))
        panel.blit(label, (6, 4))
        surface.blit(panel, (8, 32))

    def draw(self, surface: pygame.Surface):
        view_size = (
            math.ceil(SCREEN_W / self.camera.zoom),
            math.ceil(SCREEN_H / self.camera.zoom),
        )
        if self._world_surface.get_size() != view_size:
            self._world_surface = pygame.Surface(view_size)
        world = self._world_surface
        self._draw_exterior(world)

        self.tilemap.draw(world, self.camera)
        self._draw_seat_occupancy(world)
        self._draw_stall_availability(world)

        for npc in self.npcs:
            npc.draw(world, self.camera)

        for staff in self.staff:
            staff.draw(world, self.camera)

        if self._player_mode:
            self.controlled_player.draw(world, self.camera)

        if self._player_mode:
            zone = find_nearest_zone(self.zones, self.controlled_player.x, self.controlled_player.y)
            if zone:
                zsx, zsy = self.camera.world_to_screen(zone.x, zone.y)
                r = int(18 + 4 * math.sin(self._t * 4))
                glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*C_NEON_GOLD[:3], 90), (r, r), r)
                world.blit(glow, (int(zsx) - r, int(zsy) - r))
                label_f = _font("consolas", 11, bold=True)
                hint = label_f.render(zone.label or zone.name, True, C_NEON_GOLD)
                world.blit(hint, (int(zsx) - hint.get_width() // 2, int(zsy) - 28))

        if self._show_collision_debug:
            self._draw_collision_debug(world)

        self.particles.draw(world, self.camera)

        for b in self.bubbles:
            b.draw(world, self.camera)

        self.lighting.draw_world_lighting(world, self.camera)

        if abs(self.camera.zoom - 1.0) < 0.001:
            surface.blit(world, (0, 0))
        else:
            surface.blit(pygame.transform.scale(world, (SCREEN_W, SCREEN_H)), (0, 0))

        self.lighting.draw_vignette(surface)

        mode_text = "● PLAYER MODE" if self._player_mode else "○ SPECTATOR"
        self.hud.draw(surface, mode_text=mode_text)
        self.simulation_panel.draw(surface)
        self.seating_panel.draw(surface)

        if self._player_mode and self._player_msg_t > 0 and self._player_msg:
            msg_font = _font("consolas", 12, bold=True)
            msg_surf = msg_font.render(self._player_msg, True, self._player_msg_color)
            mw = msg_surf.get_width() + 24
            mh = 30
            mx = SCREEN_W // 2 - mw // 2
            my = SCREEN_H - 56
            m_panel = pygame.Surface((mw, mh), pygame.SRCALPHA)
            m_panel.fill((10, 14, 28, 220))
            surface.blit(m_panel, (mx, my))
            pygame.draw.rect(surface, self._player_msg_color, pygame.Rect(mx, my, mw, mh), 1, border_radius=4)
            surface.blit(msg_surf, (mx + 12, my + 7))

        if not self.simulation.is_running:
            rect = self._finish_banner_rect
            banner = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            banner.fill((12, 10, 30, 240))
            surface.blit(banner, rect.topleft)
            pygame.draw.rect(surface, C_NEON_GOLD, rect, 2, border_radius=6)

            title_f = _font("consolas", 14, bold=True)
            sub_f = _font("consolas", 11)
            t1 = title_f.render("SIMULATION COMPLETED", True, C_NEON_GOLD)
            t2 = sub_f.render("Opening Summary Report Card... [Press ENTER or Click]", True, C_TEXT_WHITE)
            surface.blit(t1, (rect.centerx - t1.get_width() // 2, rect.y + 6))
            surface.blit(t2, (rect.centerx - t2.get_width() // 2, rect.y + 26))

        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(int(self._fade_alpha))
            surface.blit(self._fade_surf, (0, 0))
