"""
CinePlex Dreams — Particles
Lightweight particle system: bursts, confetti, floating text, sparkles.
"""
import pygame
import random
import math
from game.settings import C_NEON_GOLD, C_NEON_PINK, C_NEON_CYAN


class Particle:
    __slots__ = ['x','y','vx','vy','life','max_life','color','size','gravity']
    def __init__(self, x,y,vx,vy,life,color,size=3,gravity=0):
        self.x,self.y,self.vx,self.vy=x,y,vx,vy
        self.life=life; self.max_life=life
        self.color=color; self.size=size; self.gravity=gravity


class FloatingText:
    def __init__(self, x, y, text, color, font):
        self.x = float(x); self.y = float(y)
        self.text = text; self.color = color
        self._surf = font.render(text, True, color)
        self.life = 1.8; self.alive = True

    def update(self, dt):
        self.y -= 28 * dt
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface, camera):
        if not self.alive: return
        alpha = min(255, int(255 * (self.life / 1.8)))
        surf = self._surf.copy()
        surf.set_alpha(alpha)
        sx, sy = camera.world_to_screen(self.x, self.y)
        surface.blit(surf, (sx - surf.get_width()//2, int(sy)))


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle] = []
        self.floating_texts: list[FloatingText] = []

    def burst(self, wx, wy, color=C_NEON_GOLD, count=12, speed=80, lifetime=0.7):
        for _ in range(count):
            a = random.uniform(0, math.pi * 2)
            v = random.uniform(speed * 0.4, speed)
            self.particles.append(Particle(
                wx, wy, math.cos(a)*v, math.sin(a)*v,
                random.uniform(lifetime*0.6, lifetime),
                color, random.randint(2, 5), gravity=60,
            ))

    def confetti(self, wx, wy, count=16):
        colors = [C_NEON_GOLD, C_NEON_PINK, C_NEON_CYAN, (255,255,255)]
        for _ in range(count):
            c = random.choice(colors)
            vx = random.uniform(-60, 60)
            vy = random.uniform(-100, -30)
            self.particles.append(Particle(
                wx, wy, vx, vy,
                random.uniform(1.0, 2.0),
                c, random.randint(3, 6), gravity=80,
            ))

    def sparkle(self, wx, wy):
        for _ in range(4):
            a = random.uniform(0, math.pi*2)
            v = random.uniform(20, 50)
            self.particles.append(Particle(
                wx, wy, math.cos(a)*v, math.sin(a)*v,
                0.5, C_NEON_GOLD, 2, 0,
            ))

    def smoke(self, wx, wy, count=2):
        for _ in range(count):
            self.particles.append(Particle(
                wx + random.uniform(-6,6), wy,
                random.uniform(-8, 8), random.uniform(-20, -8),
                random.uniform(1.5, 3.0),
                (200, 200, 220), random.randint(4, 8), gravity=-5,
            ))

    def add_text(self, wx, wy, text, color, font):
        self.floating_texts.append(FloatingText(wx, wy, text, color, font))

    def update(self, dt):
        alive = []
        for p in self.particles:
            p.x  += p.vx * dt
            p.y  += p.vy * dt
            p.vy += p.gravity * dt
            p.vx *= (1 - 1.5 * dt)
            p.life -= dt
            if p.life > 0:
                alive.append(p)
        self.particles = alive

        for ft in self.floating_texts:
            ft.update(dt)
        self.floating_texts = [ft for ft in self.floating_texts if ft.alive]

    def draw(self, surface, camera):
        for p in self.particles:
            a = max(0, int(255 * p.life / p.max_life))
            sx, sy = camera.world_to_screen(p.x, p.y)
            color = (*p.color[:3], a)
            s = pygame.Surface((p.size*2, p.size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p.size, p.size), p.size)
            surface.blit(s, (int(sx)-p.size, int(sy)-p.size))

        for ft in self.floating_texts:
            ft.draw(surface, camera)
