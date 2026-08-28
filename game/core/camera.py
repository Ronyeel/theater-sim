import pygame
from game.settings import SCREEN_W, SCREEN_H, WORLD_W, WORLD_H


class Camera:
    def __init__(self):
        self.x = (WORLD_W - SCREEN_W) / 2
        self.y = (WORLD_H - SCREEN_H) / 2
        self.vx = 0.0
        self.vy = 0.0
        self.zoom = 0.85
        self.min_zoom = 0.45
        self.max_zoom = 1.60
        self.is_dragging = False
        self._last_mouse_pos = (0, 0)
        self.pan_speed = 650.0

    def start_drag(self, pos: tuple[int, int]):
        self.is_dragging = True
        self._last_mouse_pos = pos
        self.vx = 0.0
        self.vy = 0.0

    def handle_mouse_motion(self, pos: tuple[int, int], buttons: tuple[int, ...]):
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

        self.x -= dx / self.zoom
        self.y -= dy / self.zoom
        self._clamp_bounds()

    def stop_drag(self):
        self.is_dragging = False

    def pan(self, dx: float, dy: float, dt: float):
        if dx != 0 or dy != 0:
            speed = self.pan_speed / self.zoom
            self.x += dx * speed * dt
            self.y += dy * speed * dt
            self._clamp_bounds()

    def adjust_zoom(self, amount: float, focus_pos: tuple[int, int] | None = None):
        old_zoom = self.zoom
        new_zoom = max(self.min_zoom, min(self.max_zoom, self.zoom + amount))
        if abs(new_zoom - old_zoom) < 0.001:
            return

        if focus_pos is not None:
            fx, fy = focus_pos
            wx = self.x + fx / old_zoom
            wy = self.y + fy / old_zoom
            self.zoom = new_zoom
            self.x = wx - fx / new_zoom
            self.y = wy - fy / new_zoom
        else:
            cx = SCREEN_W / 2
            cy = SCREEN_H / 2
            wx = self.x + cx / old_zoom
            wy = self.y + cy / old_zoom
            self.zoom = new_zoom
            self.x = wx - cx / new_zoom
            self.y = wy - cy / new_zoom

        self._clamp_bounds()

    def _clamp_bounds(self):
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
