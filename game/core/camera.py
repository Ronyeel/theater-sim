"""
CinePlex Dreams — Camera
Smooth lerp camera that follows the player inside the world bounds.
"""
import pygame
from game.settings import SCREEN_W, SCREEN_H, WORLD_W, WORLD_H


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.lerp_speed = 6.0  # higher = snappier follow
        self.zoom = 1.0
        # At 55%, the 960×720 display can show the full 960×1200 theater.
        self.min_zoom = 0.55
        self.max_zoom = 1.35

    def adjust_zoom(self, amount: float):
        """Adjust the theater view scale, keeping it within a useful range."""
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom + amount))

    def update(self, target_x: float, target_y: float, dt: float):
        """Smoothly follow target world position (center of screen)."""
        view_w = SCREEN_W / self.zoom
        view_h = SCREEN_H / self.zoom
        ideal_x = target_x - view_w / 2
        ideal_y = target_y - view_h / 2
        # When zoomed out beyond the map, center the whole theater in view.
        if view_w >= WORLD_W:
            ideal_x = (WORLD_W - view_w) / 2
        else:
            ideal_x = max(0, min(ideal_x, WORLD_W - view_w))
        if view_h >= WORLD_H:
            ideal_y = (WORLD_H - view_h) / 2
        else:
            ideal_y = max(0, min(ideal_y, WORLD_H - view_h))
        # Lerp toward ideal
        t = min(1.0, self.lerp_speed * dt)
        self.x += (ideal_x - self.x) * t
        self.y += (ideal_y - self.y) * t

    def world_to_screen(self, wx: float, wy: float):
        return wx - self.x, wy - self.y

    def screen_to_world(self, sx: float, sy: float):
        return sx + self.x, sy + self.y

    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        return rect.move(-int(self.x), -int(self.y))

    @property
    def offset(self):
        return pygame.Vector2(-self.x, -self.y)
