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

    def update(self, target_x: float, target_y: float, dt: float):
        """Smoothly follow target world position (center of screen)."""
        ideal_x = target_x - SCREEN_W / 2
        ideal_y = target_y - SCREEN_H / 2
        # Clamp so camera never shows outside the world
        ideal_x = max(0, min(ideal_x, WORLD_W - SCREEN_W))
        ideal_y = max(0, min(ideal_y, WORLD_H - SCREEN_H))
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
