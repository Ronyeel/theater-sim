"""
CinePlex Dreams — Spectator Simulation Screen
Sandbox view: interactive draggable camera, real-time tilemap, staff, NPCs,
SimPy queue simulation telemetry, particles, and speech bubbles.
"""
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
    TILE_SECURITY,
)
from game.core.camera import Camera
from game.core.tilemap import TileMap, tile_at
from game.core.particles import ParticleSystem
from game.core import asset_loader as AL
from game.entities.npc import build_npcs
from game.backend_bridge import TheaterSimulationBridge
from game.world.interactions import build_zones
from game.ui.speech_bubble import SpeechBubble
from game.ui.simulation_panel import SimulationPanel
from game.ui.hud import HUD


def _font(name, size, bold=False):
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


class GameScreen:
    """Main spectator sandbox and real-time theater simulation screen."""

    def __init__(
        self,
        go_title: Callable[[], None],
        go_results: Optional[Callable[[], None]] = None,
        bridge: Optional[TheaterSimulationBridge] = None,
    ) -> None:
        self.go_title = go_title
        self.go_results = go_results or go_title
        self._t = 0.0

        # Sandbox Camera & world
        self.camera = Camera()
        self.tilemap = TileMap()
        self._world_surface = pygame.Surface((SCREEN_W, SCREEN_H))

        # Simulation backend
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

        # Zones & staff
        self.staff = []
        self.zones = build_zones(self._num_cashiers, self._num_ushers, self._num_servers)

        # Particles & UI bubbles
        self.particles = ParticleSystem()
        self.bubbles: list[SpeechBubble] = []

        # NPCs
        self.npcs = []
        self._movie_finished = False

        # In-game control panel & HUD
        self.simulation_panel = SimulationPanel(self.simulation, self._apply_simulation_config)
        self.hud = HUD(self.simulation, npcs_provider=lambda: self.npcs)


        # Screen transition fade
        self._fading = False
        self._fade_alpha = 0
        self._fade_surf = pygame.Surface((SCREEN_W, SCREEN_H))
        self._fade_surf.fill((0, 0, 0))
        self._show_collision_debug = False

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

    # ── Event Handling ───────────────────────────────────────────────────

    def handle_event(self, evt: pygame.event.Event):
        # Allow simulation configuration panel to intercept events first
        if self.simulation_panel.handle_event(evt):
            return

        self.hud.handle_event(evt)

        # Mouse Drag-to-Pan (Sandbox camera)
        if evt.type == pygame.MOUSEBUTTONDOWN:
            if evt.button in (1, 2, 3):  # Left, Middle, or Right drag
                self.camera.start_drag(evt.pos)
        elif evt.type == pygame.MOUSEBUTTONUP:
            if evt.button in (1, 2, 3):
                self.camera.stop_drag()
        elif evt.type == pygame.MOUSEMOTION:
            self.camera.handle_mouse_motion(evt.pos, evt.buttons)
        elif evt.type == pygame.MOUSEWHEEL:
            # Zoom anchored at cursor position
            self.camera.adjust_zoom(0.08 * evt.y, focus_pos=pygame.mouse.get_pos())

        # Keyboard shortcuts
        elif evt.type == pygame.KEYDOWN:
            if evt.key == pygame.K_F1:
                self.simulation_panel.open()
            elif evt.key == pygame.K_SPACE:
                is_p = getattr(self.simulation, "is_paused", False)
                self.simulation.is_paused = not is_p
                self.hud.add_log("Simulation PAUSED" if self.simulation.is_paused else "Simulation RESUMED", C_NEON_CYAN)
            elif evt.key in (pygame.K_r, pygame.K_TAB):
                self.simulation.reset()
                self.npcs = []
                self._movie_finished = False
                self.hud.add_log("Simulation reset.", C_NEON_GOLD)
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
            elif evt.key == pygame.K_ESCAPE:
                self.go_title()

    # ── Update ───────────────────────────────────────────────────────────

    def update(self, dt: float):
        self._t += dt

        self.simulation_panel.update(dt)
        if self.simulation_panel.visible:
            return

        # Keyboard camera panning (WASD / Arrow keys)
        keys = pygame.key.get_pressed()
        pdx = (1 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0)
        pdy = (1 if keys[pygame.K_s] or keys[pygame.K_DOWN] else 0) - (1 if keys[pygame.K_w] or keys[pygame.K_UP] else 0)
        if pdx != 0 or pdy != 0:
            self.camera.pan(pdx, pdy, dt)

        self.camera.update(dt)

        # Simulation clock and speed
        sim_dt = dt * self.simulation.speed

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

        # Advance backend queue simulation
        self.simulation.update(dt)
        if not self.simulation.is_running:
            self._movie_finished = True

        # Particles & Speech bubbles
        self.particles.update(dt)
        for b in self.bubbles:
            b.update(dt)
        self.bubbles = [b for b in self.bubbles if b.alive]

        # HUD
        self.hud.update(dt)

        # Fade out
        if self._fading:
            self._fade_alpha = min(255, self._fade_alpha + 160 * dt)
            if self._fade_alpha >= 255:
                self.go_title()
                self._fading = False

    # ── Render ───────────────────────────────────────────────────────────

    def _draw_exterior(self, surface: pygame.Surface):
        """Plain backdrop visible around the theater when zoomed out."""
        surface.fill((7, 12, 28))

    def _draw_stall_availability(self, surface: pygame.Surface):
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

    def _draw_collision_debug(self, surface: pygame.Surface):
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
        # Render the world view at current zoom
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
        for z in self.zones:
            z.draw_glow(world, self.camera)

        # NPCs
        for npc in self.npcs:
            npc.draw(world, self.camera)

        # Staff
        for staff in self.staff:
            staff.draw(world, self.camera)

        if self._show_collision_debug:
            self._draw_collision_debug(world)

        # Particles
        self.particles.draw(world, self.camera)

        # Speech bubbles
        for b in self.bubbles:
            b.draw(world, self.camera)

        # Blit world view to display
        if abs(self.camera.zoom - 1.0) < 0.001:
            surface.blit(world, (0, 0))
        else:
            surface.blit(pygame.transform.scale(world, (SCREEN_W, SCREEN_H)), (0, 0))

        # UI overlays (HUD & Simulation Settings panel)
        self.hud.draw(surface)
        self.simulation_panel.draw(surface)
        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(int(self._fade_alpha))
            surface.blit(self._fade_surf, (0, 0))
