"""
CinePlex Dreams — Sandbox Camera
Interactive spectator camera with smooth mouse drag-to-pan, keyboard panning (WASD/Arrows),
and mouse-wheel zoom for sandbox simulation viewing.
"""
import pygame
from game.settings import SCREEN_W, SCREEN_H, WORLD_W, WORLD_H


class Camera:
    def __init__(self):
        # Start centered on the lobby / entrance
        self.x = (WORLD_W - SCREEN_W) / 2
        self.y = (WORLD_H - SCREEN_H) / 2
        self.vx = 0.0
        self.vy = 0.0
        self.zoom = 0.85
        self.min_zoom = 0.45
        self.max_zoom = 1.60
        self.is_dragging = False
        self._last_mouse_pos = (0, 0)
        self.pan_speed = 650.0  # pixels per second for keyboard panning

    def start_drag(self, pos: tuple[int, int]):
        """Begin dragging the camera view with the mouse."""
        self.is_dragging = True
        self._last_mouse_pos = pos
        self.vx = 0.0
        self.vy = 0.0

    def handle_mouse_motion(self, pos: tuple[int, int], buttons: tuple[int, ...]):
        """Process mouse movement while dragging."""
        if not self.is_dragging:
            if any(buttons):
                self.start_drag(pos)
            return

        if not any(buttons):
            self.stop_drag()
            return

        dx = pos[0] - self._last_mouse_pos[0]
        dy = pos[1] - self._last_mouse_pos[1]
        self._last_mouse_pos = pos

        # Move opposite to mouse drag for intuitive grab-and-pull navigation
        self.x -= dx / self.zoom
        self.y -= dy / self.zoom
        self._clamp_bounds()

    def stop_drag(self):
        """Stop dragging the camera view."""
        self.is_dragging = False

    def pan(self, dx: float, dy: float, dt: float):
        """Pan the camera view using keyboard input (WASD / Arrows)."""
        if dx != 0 or dy != 0:
            speed = self.pan_speed / self.zoom
            self.x += dx * speed * dt
            self.y += dy * speed * dt
            self._clamp_bounds()

    def adjust_zoom(self, amount: float, focus_pos: tuple[int, int] | None = None):
        """Adjust zoom level while optionally keeping the mouse pointer anchored."""
        old_zoom = self.zoom
        new_zoom = max(self.min_zoom, min(self.max_zoom, self.zoom + amount))
        if abs(new_zoom - old_zoom) < 0.001:
            return

        if focus_pos is not None:
            # Zoom toward cursor position
            fx, fy = focus_pos
            wx = self.x + fx / old_zoom
            wy = self.y + fy / old_zoom
            self.zoom = new_zoom
            self.x = wx - fx / new_zoom
            self.y = wy - fy / new_zoom
        else:
            # Zoom toward screen center
            cx = SCREEN_W / 2
            cy = SCREEN_H / 2
            wx = self.x + cx / old_zoom
            wy = self.y + cy / old_zoom
            self.zoom = new_zoom
            self.x = wx - cx / new_zoom
            self.y = wy - cy / new_zoom

        self._clamp_bounds()

    def _clamp_bounds(self):
        """Keep camera within world boundaries or center if zoomed out."""
        view_w = SCREEN_W / self.zoom
        view_h = SCREEN_H / self.zoom

        if view_w >= WORLD_W:
            self.x = (WORLD_W - view_w) / 2
        else:
            self.x = max(0, min(self.x, WORLD_W - view_w))

        if view_h >= WORLD_H:
            self.y = (WORLD_H - view_h) / 2
        else:
            self.y = max(0, min(self.y, WORLD_H - view_h))

    def update(self, dt: float):
        """Update camera bounds and momentum."""
        self._clamp_bounds()

    def world_to_screen(self, wx: float, wy: float):
        return wx - self.x, wy - self.y

    def screen_to_world(self, sx: float, sy: float):
        return sx / self.zoom + self.x, sy / self.zoom + self.y

    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        return rect.move(-int(self.x), -int(self.y))


    @property
    def offset(self):
        return pygame.Vector2(-self.x, -self.y)
