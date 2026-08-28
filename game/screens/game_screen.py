"""
CinePlex Dreams — Game Screen
The main playable world: tilemap, player, staff, interaction zones,
particles, speech bubbles, and dialogs.
"""
import pygame
import random
import time
import math
from game.settings import (
    SCREEN_W, SCREEN_H, TILE_SIZE,
    C_BG_DARK, C_NEON_GOLD, C_NEON_PINK, C_NEON_CYAN,
    C_NEON_GREEN, C_NEON_RED, C_BAD, C_TEXT_WHITE, C_TEXT_DIM,
    DEFAULT_CASHIERS, DEFAULT_USHERS, DEFAULT_SERVERS,
    CASHIER_DESK_COLS, CASHIER_DESK_ROW,
    USHER_DESK_COLS, USHER_DESK_ROW,
    SNACK_DESK_COLS, SNACK_DESK_ROW,
    MAP_COLS, MAP_ROWS, TILE_DESK, TILE_SEAT, TILE_SNACK, TILE_USHER,
    TILE_SECURITY, PLAYER_SPRITE_W, PLAYER_SPRITE_H,
    MOVIES,
)
from game.core.camera import Camera
from game.core.tilemap import TileMap, tile_at
from game.core.particles import ParticleSystem
from game.core import asset_loader as AL
from game.entities.player import Player, Stage
from game.entities.npc import build_npcs
from game.backend_bridge import TheaterSimulationBridge
from game.world.interactions import build_zones, find_nearest_zone
from game.ui.speech_bubble import SpeechBubble, DialogPrompt
from game.ui.dialog_menu import TicketDialog, ConcessionDialog, UsherDialog
from game.ui.simulation_panel import SimulationPanel
from src.stats import format_minutes_seconds


def _font(name, size, bold=False):
    try:    return pygame.font.SysFont(name, size, bold=bold)
    except: return pygame.font.Font(None, size)


# ── Simple heads-up display (no simulation stats) ─────────────────────────

class SimpleHUD:
    """Pixel-style live dashboard for the SimPy theater model."""
    LOG_MAX = 5

    def __init__(self, player, simulation):
        self.player = player
        self.simulation = simulation
        self._log: list[tuple[str, tuple]] = []
        self._tf = _font("consolas", 13, bold=True)
        self._lf = _font("consolas", 12)
        self._log_t = 0.0

    def add_log(self, text: str, color=(255, 255, 255)):
        self._log.insert(0, (text, color))
        if len(self._log) > self.LOG_MAX:
            self._log.pop()
        self._log_t = 4.0

    def update(self, dt):
        self._log_t = max(0, self._log_t - dt)

    def handle_event(self, evt):
        pass  # no interactive buttons needed

    def draw(self, surface):
        stats = self.simulation.stats

        def capsule(rect, title, value, color):
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            panel.fill((19, 22, 40, 235))
            surface.blit(panel, rect.topleft)
            pygame.draw.rect(surface, (43, 48, 76), rect, 2, border_radius=3)
            label = self._lf.render(title, True, (166, 177, 206))
            value_surf = self._tf.render(value, True, color)
            surface.blit(label, (rect.x + 8, rect.y + 5))
            surface.blit(value_surf, (rect.x + 8, rect.y + 19))

        minutes, seconds = format_minutes_seconds(stats.sim_time)
        wait_minutes, wait_seconds = format_minutes_seconds(stats.avg_wait)
        wait_color = C_NEON_GREEN if stats.goal_met else C_NEON_RED
        run_label = "RUNNING" if self.simulation.is_running else "FINISHED"
        run_color = C_NEON_GREEN if self.simulation.is_running else C_NEON_RED
        speed = f"{self.simulation.speed}×"
        capsules = [
            (pygame.Rect(6, 6, 112, 46), "SIM TIME", f"{minutes:02d}:{seconds:02d}", C_TEXT_WHITE),
            (pygame.Rect(124, 6, 92, 46), "STATUS", run_label, run_color),
            (pygame.Rect(222, 6, 68, 46), "SPEED", speed, C_NEON_CYAN),
            (pygame.Rect(296, 6, 104, 46), "GUESTS", f"{stats.total_arrived}/{stats.total_seated}", C_NEON_GOLD),
            (pygame.Rect(406, 6, 116, 46), "AVG WAIT", f"{wait_minutes}:{wait_seconds:02d}", wait_color),
            (pygame.Rect(528, 6, 112, 46), "TARGET", "≤ 10:00", C_NEON_GREEN),
        ]
        for rect, title, value, color in capsules:
            capsule(rect, title, value, color)

        queue_text = (
            f"Q  Ticket {stats.cashier_queue}  •  Usher {stats.usher_queue}  •  Snacks {stats.snack_queue}"
        )
        queue_surf = self._lf.render(queue_text, True, C_TEXT_DIM)
        queue_panel = pygame.Surface((queue_surf.get_width() + 14, queue_surf.get_height() + 8), pygame.SRCALPHA)
        queue_panel.fill((19, 22, 40, 220))
        queue_panel.blit(queue_surf, (7, 4))
        queue_x = SCREEN_W // 2 - queue_panel.get_width() // 2
        surface.blit(queue_panel, (queue_x, 55))

        # Stage badge (top-center)
        stage_labels = {
            Stage.ENTERING:   ("🚪 Enter & Buy Ticket", C_NEON_GOLD),
            Stage.NEED_TICKET:("🎟  Buy Your Ticket",   C_NEON_GOLD),
            Stage.NEED_CHECK: ("🎫 Get Ticket Checked", C_NEON_PINK),
            Stage.NEED_FOOD:  ("🍿 Buy Snacks",          C_NEON_CYAN),
            Stage.FOOD_SKIP:  ("🪑 Find a Seat",         C_NEON_CYAN),
            Stage.NEED_SEAT:  ("🪑 Find a Seat",         C_NEON_CYAN),
            Stage.SEATED:     ("✅ Enjoy the Movie!",    C_NEON_GREEN),
            Stage.NEED_EXIT:  ("🚪 Movie's Over — Find the Exit", C_NEON_RED),
        }
        lbl, col = stage_labels.get(self.player.stage, ("", C_NEON_GOLD))
        if lbl:
            surf = self._tf.render(f"  {lbl}  ", True, col)
            bx = SCREEN_W // 2 - surf.get_width() // 2
            bg = pygame.Surface((surf.get_width() + 4, surf.get_height() + 4), pygame.SRCALPHA)
            bg.fill((10, 5, 20, 180))
            surface.blit(bg, (bx - 2, 79))
            surface.blit(surf, (bx, 81))

        # Event log (bottom-left), fades out
        if self._log and self._log_t > 0:
            alpha = min(255, int(255 * self._log_t))
            for i, (txt, col) in enumerate(self._log):
                s = self._lf.render(txt, True, col)
                s.set_alpha(alpha)
                surface.blit(s, (12, SCREEN_H - 24 - i * 18))

        # Controls hint (bottom-right)
        hint = self._lf.render("[E] Interact  [F1] Simulation  [1] Collision  [+/-] Zoom  [ESC] Quit", True, (120, 100, 160))
        surface.blit(hint, (SCREEN_W - hint.get_width() - 10, SCREEN_H - 20))


# ── Game Screen ───────────────────────────────────────────────────────────

class GameScreen:

    def __init__(self, go_title):
        self.go_title   = go_title
        self._t = 0.0

        # Camera & world
        self.camera  = Camera()
        self.tilemap = TileMap()
        self._world_surface = pygame.Surface((SCREEN_W, SCREEN_H))

        # Player
        self.player = Player()
        self.player.arrival_time = time.time()

        # Staff & Zones (default counts)
        self._num_cashiers = DEFAULT_CASHIERS
        self._num_ushers   = DEFAULT_USHERS
        self._num_servers  = DEFAULT_SERVERS
        # Stall tiles already contain their cashier, usher, and concession
        # artwork. Their interaction zones and SimPy resources provide the
        # service function, so no extra staff sprite is spawned on top.
        self.staff = []
        self.zones = build_zones(self._num_cashiers, self._num_ushers, self._num_servers)

        # Particles & Bubbles
        self.particles = ParticleSystem()
        self.bubbles: list[SpeechBubble] = []
        self._dialog_prompt = DialogPrompt()

        # Visual guests are created one-for-one from SimPy arrival events.
        self.npcs = []
        self._movie_finished = False

        # Run the activity's SimPy model in parallel with the visual world.
        # This does not alter rendering or the existing player controls.
        self.simulation = TheaterSimulationBridge(
            self._num_cashiers, self._num_servers, self._num_ushers,
            seed=42, on_arrival=self._spawn_simulation_npc,
        )
        self.simulation_panel = SimulationPanel(self.simulation, self._apply_simulation_config)

        # HUD
        self.hud = SimpleHUD(self.player, self.simulation)

        # Dialogs
        self.active_dialog = None
        self.ticket_dialog = TicketDialog(self._on_ticket_selected)
        self.snack_dialog  = ConcessionDialog(self._on_snack_selected)
        self.usher_dialog  = UsherDialog(self._on_usher_complete, self._on_usher_rejected)

        # Fade to title
        self._fading     = False
        self._fade_alpha = 0
        self._fade_surf  = pygame.Surface((SCREEN_W, SCREEN_H))
        self._fade_surf.fill((0, 0, 0))
        self._ticket_gate_hint_timer = 0.0
        self._show_collision_debug = False

    # ── Player Interaction ────────────────────────────────────────────────

    def _apply_simulation_config(self, config: dict):
        """Apply a control-panel configuration as a clean, visible run."""
        bridge = self.simulation
        for key, value in config.items():
            setattr(bridge, key, value)
        bridge.reset()
        self._num_cashiers = bridge.num_cashiers
        self._num_ushers = bridge.num_ushers
        self._num_servers = bridge.num_servers
        self.zones = build_zones(self._num_cashiers, self._num_ushers, self._num_servers)
        self.npcs = []
        self._movie_finished = False
        self.hud.add_log("Simulation restarted with new settings.", C_NEON_GOLD)

    def _spawn_simulation_npc(self, moviegoer_id: int):
        """Create exactly one visual guest for every SimPy arrival."""
        guests = build_npcs(1, slot_offset=moviegoer_id)
        for guest in guests:
            guest.set_service_capacity(
                self._num_cashiers, self._num_ushers, self._num_servers,
            )
        self.npcs.extend(guests)

    def _check_interaction(self):
        if self.active_dialog:
            self._dialog_prompt.hide()
            return
        p = self.player
        if p.is_interacting:
            self._dialog_prompt.hide()
            return

        needed = None
        if p.stage in (Stage.ENTERING, Stage.NEED_TICKET): needed = "cashier"
        elif p.stage == Stage.NEED_FOOD:                   needed = "snack"
        elif p.stage in (Stage.NEED_SEAT, Stage.FOOD_SKIP): needed = "seat"
        elif p.stage == Stage.NEED_EXIT:                   needed = "exit"

        zone = find_nearest_zone(self.zones, p.x, p.y)
        if zone and (zone.name in ["poster", "board", "security"] or zone.name == needed):
            self._dialog_prompt.show(zone.label)
            return
        self._dialog_prompt.hide()

    def _try_interact(self):
        if self.active_dialog:
            return
        p = self.player
        if p.is_interacting:
            return

        zone = find_nearest_zone(self.zones, p.x, p.y)
        if not zone:
            return

        can_interact = (
            zone.name in ["poster", "board", "security"]
            or (p.stage in (Stage.ENTERING, Stage.NEED_TICKET) and zone.name == "cashier")
            or (p.stage == Stage.NEED_FOOD   and zone.name == "snack")
            or (p.stage in (Stage.NEED_SEAT, Stage.FOOD_SKIP) and zone.name == "seat")
            or (p.stage == Stage.NEED_EXIT and zone.name == "exit")
        )
        if not can_interact:
            self.hud.add_log(f"Can't do that yet!", C_BAD)
            return

        def callback():
            if zone.name == "cashier":
                self.ticket_dialog.open()
                self.active_dialog = self.ticket_dialog
            elif zone.name == "snack":
                self.snack_dialog.open()
                self.active_dialog = self.snack_dialog
            elif zone.name == "seat":
                self._on_seat_taken(zone)
            elif zone.name == "exit":
                self._on_exit_used()
            elif zone.name == "security":
                self.bubbles.append(SpeechBubble("All clear! Move along.", p.x, p.y-40, C_NEON_GOLD))
            elif zone.name == "board":
                self.bubbles.append(SpeechBubble("Checking schedule...", p.x, p.y-40, C_NEON_GOLD))
            elif zone.name == "poster":
                self.bubbles.append(SpeechBubble("Looks like a great movie!", p.x, p.y-40, C_NEON_GOLD))

        p.start_interact(callback)

    # ── Dialog Callbacks ──────────────────────────────────────────────────

    def _on_ticket_selected(self, item):
        self.active_dialog = None
        self.player.has_ticket = True
        self.player.usher_no_ticket_notified = False
        self.player.selected_movie = item["title"]
        self.player.stage = Stage.NEED_CHECK
        self.player.flash(C_NEON_GOLD)
        self.particles.burst(self.player.x, self.player.y - 20, C_NEON_GOLD, 8)
        self.bubbles.append(SpeechBubble(
            f"Got a ticket for {item['title']} ✓", self.player.x, self.player.y - 40, C_NEON_GOLD))
        self.hud.add_log(f"Bought ticket for {item['title']}!", C_NEON_GOLD)

    def _on_usher_complete(self):
        self.active_dialog = None
        self.player.ticket_checked = True
        if random.random() < 0.5:
            self.player.stage = Stage.NEED_FOOD
            self.bubbles.append(SpeechBubble("Let's get snacks!", self.player.x, self.player.y-40, C_NEON_CYAN))
        else:
            self.player.stage = Stage.FOOD_SKIP
            self.bubbles.append(SpeechBubble("Ticket checked! ✓", self.player.x, self.player.y-40, C_NEON_PINK))
        self.player.flash(C_NEON_PINK)
        self.particles.burst(self.player.x, self.player.y - 20, C_NEON_PINK, 8)
        self.hud.add_log("Ticket checked by usher!", C_NEON_PINK)

    def _on_usher_rejected(self):
        self.active_dialog = None
        self.player.stage = Stage.NEED_TICKET
        self.player.flash(C_BAD)
        self.hud.add_log("No ticket found — visit the box office first.", C_BAD)

    def _start_automatic_ticket_check(self):
        """Start the usher's scan as soon as a ticket-holder reaches the gate."""
        p = self.player
        if (p.stage not in (Stage.ENTERING, Stage.NEED_TICKET, Stage.NEED_CHECK)
                or self.active_dialog or p.is_interacting or p.ticket_checked):
            return
        if (find_nearest_zone(self.zones, p.x, p.y, "usher")
                and (p.has_ticket or not p.usher_no_ticket_notified)):
            if p.has_ticket:
                self._on_usher_complete()
            else:
                p.usher_no_ticket_notified = True
                self._on_usher_rejected()

    def _on_snack_selected(self, item):
        self.active_dialog = None
        if item["name"] != "No Thanks":
            self.player.has_food  = True
            self.player.food_order = item["name"]
            self.bubbles.append(SpeechBubble(
                f"Mmm, {item['name']}!", self.player.x, self.player.y - 40, C_NEON_CYAN))
            self.hud.add_log(f"Bought {item['name']}!", C_NEON_CYAN)
        else:
            self.bubbles.append(SpeechBubble("I'll skip snacks.", self.player.x, self.player.y - 40, C_NEON_CYAN))
        self.player.stage = Stage.NEED_SEAT
        self.player.flash(C_NEON_CYAN)
        self.particles.burst(self.player.x, self.player.y - 20, C_NEON_CYAN, 8)

    def _on_seat_taken(self, zone):
        p = self.player
        p.stage = Stage.NEED_EXIT
        p.seated_at_pos = (p.x, p.y)
        p.wait_time = time.time() - p.arrival_time
        p.flash(C_NEON_GREEN)
        self.particles.confetti(p.x, p.y - 30, count=20)
        self.particles.burst(p.x, p.y - 20, C_NEON_GOLD, 14)
        wm = int(p.wait_time // 60); ws = int(p.wait_time % 60)
        self.bubbles.append(SpeechBubble(
            f"Seated! Wait: {wm}m {ws:02d}s", p.x, p.y - 40, C_NEON_GREEN, 4.0))
        self.hud.add_log(f"Seated! Real wait: {wm}m {ws:02d}s", C_NEON_GREEN)
        self.bubbles.append(SpeechBubble(
            "Movie's over — head to the exit!", p.x, p.y - 62, C_NEON_RED, 4.0))

    def _on_exit_used(self):
        p = self.player
        p.flash(C_NEON_RED)
        self.particles.burst(p.x, p.y - 20, C_NEON_RED, 18)
        self.hud.add_log("Thanks for visiting CinePlex Dreams!", C_NEON_RED)
        self._fading = True

    # ── Main Loop ─────────────────────────────────────────────────────────

    def handle_event(self, evt):
        if self.simulation_panel.handle_event(evt):
            return
        if self.active_dialog:
            if self.active_dialog.handle_event(evt):
                if self.active_dialog and not self.active_dialog.active:
                    self.active_dialog = None
            return

        self.hud.handle_event(evt)
        if evt.type == pygame.KEYDOWN:
            if evt.key == pygame.K_F1:
                self.simulation_panel.open()
            elif evt.key == pygame.K_1:
                self._show_collision_debug = not self._show_collision_debug
                self.hud.add_log(
                    "Collision view ON" if self._show_collision_debug else "Collision view OFF",
                    C_NEON_CYAN,
                )
            elif evt.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                self.camera.adjust_zoom(0.1)
            elif evt.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.camera.adjust_zoom(-0.1)
            elif evt.key == pygame.K_e:
                self._try_interact()
        elif evt.type == pygame.MOUSEWHEEL:
            self.camera.adjust_zoom(0.1 * evt.y)

    def update(self, dt):
        self._t += dt

        self.simulation_panel.update(dt)
        if self.simulation_panel.visible:
            return

        # Speed changes advance all simulated activity by the same factor.
        # It never changes staff capacity, service rules, or NPC decisions;
        # it only fast-forwards the shared simulation clock.
        sim_dt = dt * self.simulation.speed

        # Player
        if not self.active_dialog:
            keys = pygame.key.get_pressed()
            self.player.handle_keys(keys)
        self.player.update(dt)
        self._start_automatic_ticket_check()
        self._ticket_gate_hint_timer = max(0.0, self._ticket_gate_hint_timer - dt)
        if self.player.ticket_gate_blocked and self._ticket_gate_hint_timer == 0:
            self.hud.add_log("Ticket required to enter the auditorium!", C_BAD)
            self.bubbles.append(SpeechBubble(
                "Ticket required!", self.player.x, self.player.y - 40, C_BAD, 2.0))
            self._ticket_gate_hint_timer = 1.5
        if self.player.usher_gate_blocked and self._ticket_gate_hint_timer == 0:
            self.hud.add_log("Please have an usher check your ticket.", C_BAD)
            self._ticket_gate_hint_timer = 1.5

        # Camera
        self.camera.update(self.player.x, self.player.y, dt)

        # Tilemap
        self.tilemap.update(sim_dt)

        # Staff
        for staff in self.staff:
            staff.update(sim_dt)

        # Zones
        for z in self.zones:
            z.update(sim_dt)

        # NPCs
        for npc in self.npcs:
            npc.update(sim_dt, self.npcs, movie_finished=self._movie_finished)
        self.npcs = [npc for npc in self.npcs if not npc.has_left]

        # Advance the same minute-based queue model used by src/main.py.
        self.simulation.update(dt)
        if not self.simulation.is_running:
            self._movie_finished = True

        # Interaction check
        self._check_interaction()

        # Particles
        self.particles.update(dt)

        # Speech bubbles
        for b in self.bubbles:
            b.update(dt)
        self.bubbles = [b for b in self.bubbles if b.alive]

        # Dialogs
        if self.active_dialog:
            self.active_dialog.update(dt)
        self._dialog_prompt.update(dt)

        # HUD
        self.hud.update(dt)

        # Fade out (after seated or on reset)
        if self._fading:
            self._fade_alpha = min(255, self._fade_alpha + 160 * dt)
            if self._fade_alpha >= 255:
                self.go_title()
                self._fading = False
                self._fade_alpha = 0

        # Footstep dust
        if self.player.dust_timer > 0.3 and self.player._moving:
            self.player.dust_timer = 0
            self.particles.sparkle(self.player.x, self.player.y + 10)

    def _draw_exterior(self, surface):
        """Plain backdrop visible around the theater when zoomed out."""
        surface.fill((7, 12, 28))

    def _draw_stall_availability(self, surface):
        """Label fixed visual stalls whose corresponding resource is closed."""
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

    def _draw_collision_debug(self, surface):
        """Draw the exact movement bounds used by the collision code."""
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

        # NPCs yield when their two 8px footprints touch. Draw each footprint
        # and a thin 16px contact-distance ring for quick diagnosis.
        for npc in self.npcs:
            sx, sy = self.camera.world_to_screen(npc.x, npc.y)
            pygame.draw.circle(surface, (75, 230, 255), (int(sx), int(sy)), 8, 2)
            pygame.draw.circle(surface, (75, 230, 255), (int(sx), int(sy)), 16, 1)

        p = self.player
        sx, sy = self.camera.world_to_screen(p.x, p.y)
        player_rect = pygame.Rect(
            int(sx - PLAYER_SPRITE_W + 2), int(sy - PLAYER_SPRITE_H // 2 + 2),
            PLAYER_SPRITE_W * 2 - 4, PLAYER_SPRITE_H - 4,
        )
        pygame.draw.rect(surface, (100, 255, 140), player_rect, 2)

        font = _font("consolas", 12, bold=True)
        label = font.render("COLLISION: red stall  yellow seat  cyan NPC  green player", True, (255, 255, 255))
        panel = pygame.Surface((label.get_width() + 12, label.get_height() + 8), pygame.SRCALPHA)
        panel.fill((10, 8, 24, 210))
        panel.blit(label, (6, 4))
        surface.blit(panel, (8, 32))

    def draw(self, surface):
        # Render the larger world view first, then fit it to the display.
        # This is a true camera zoom: zooming out increases the visible area.
        view_size = (
            math.ceil(SCREEN_W / self.camera.zoom),
            math.ceil(SCREEN_H / self.camera.zoom),
        )
        if self._world_surface.get_size() != view_size:
            self._world_surface = pygame.Surface(view_size)
        world = self._world_surface
        self._draw_exterior(world)

        # Tilemap
        self.tilemap.draw(world, self.camera)
        self._draw_stall_availability(world)

        # Zone glows
        p = self.player
        needed = None
        if p.stage in (Stage.ENTERING, Stage.NEED_TICKET): needed = "cashier"
        elif p.stage == Stage.NEED_FOOD:                   needed = "snack"
        elif p.stage in (Stage.NEED_SEAT, Stage.FOOD_SKIP): needed = "seat"
        elif p.stage == Stage.NEED_EXIT:                   needed = "exit"
        for z in self.zones:
            if z.name == needed or z.name in ["poster", "security", "board"]:
                z.draw_glow(world, self.camera)

        # NPCs (draw behind player for depth)
        for npc in self.npcs:
            npc.draw(world, self.camera)

        # Staff
        for staff in self.staff:
            staff.draw(world, self.camera)

        # Player
        self.player.draw(world, self.camera)

        if self._show_collision_debug:
            self._draw_collision_debug(world)

        # Particles
        self.particles.draw(world, self.camera)

        # Speech bubbles
        for b in self.bubbles:
            b.draw(world, self.camera)

        surface.blit(pygame.transform.smoothscale(world, (SCREEN_W, SCREEN_H)), (0, 0))

        # UI overlays
        if self.active_dialog:
            self.active_dialog.draw(surface)
        self._dialog_prompt.draw(surface)
        self.hud.draw(surface)
        self.simulation_panel.draw(surface)

        # Fade
        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(int(self._fade_alpha))
            surface.blit(self._fade_surf, (0, 0))
