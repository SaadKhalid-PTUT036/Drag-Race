# -*- coding: utf-8 -*-
"""
dragkings/particles.py
======================
Particle and Particles classes.

Particles:
  • smoke   – tyre smoke at launch
  • nitro   – blue/purple nitro exhaust
  • spark   – sparks during hard shifts
  • burnout – dark rubber smoke on burnout
"""

import pygame
import math
import random


class Particle:
    """Single lightweight particle — uses __slots__ for performance."""
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'size', 'colour')

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 size: float, life: float, colour: tuple):
        self.x, self.y   = x, y
        self.vx, self.vy = vx, vy
        self.size        = size
        self.life        = life
        self.max_life    = life
        self.colour      = colour

    def update(self, dt: float) -> None:
        self.x    += self.vx * dt
        self.y    += self.vy * dt
        self.life -= dt
        self.size  = max(0.0, self.size - self.size * dt * 1.8)

    def draw(self, surf: pygame.Surface, cam_x: float) -> None:
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / self.max_life))
        sz    = max(1, int(self.size))
        s     = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.colour, alpha), (sz, sz), sz)
        surf.blit(s, (self.x - cam_x - sz, self.y - sz))


class Particles:
    """Manages a pool of live Particle objects."""

    def __init__(self):
        self.pool: list[Particle] = []

    # ── Emitters ──────────────────────────────────────────────────────────────

    def _add(self, x, y, vx, vy, size, life, colour) -> None:
        self.pool.append(Particle(x, y, vx, vy, size, life, colour))

    def smoke(self, x: float, y: float) -> None:
        for _ in range(2):
            self._add(x, y,
                      random.uniform(-12, -3),
                      random.uniform(-15, 15),
                      random.uniform(5, 12),
                      random.uniform(0.3, 0.7),
                      (180, 180, 180))

    def nitro(self, x: float, y: float) -> None:
        for _ in range(5):
            col = random.choice([(0, 200, 255), (120, 80, 255), (255, 255, 255)])
            self._add(x, y,
                      random.uniform(-200, -60),
                      random.uniform(-20,   20),
                      random.uniform(4,  12),
                      random.uniform(0.08, 0.28),
                      col)

    def spark(self, x: float, y: float) -> None:
        for _ in range(6):
            ang = random.uniform(2.5, 3.7)
            spd = random.uniform(60, 180)
            self._add(x, y,
                      math.cos(ang) * spd,
                      math.sin(ang) * spd,
                      random.uniform(2, 5),
                      random.uniform(0.1, 0.35),
                      (255, 200, 60))

    def burnout(self, x: float, y: float) -> None:
        for _ in range(3):
            self._add(x, y,
                      random.uniform(-30, 10),
                      random.uniform(-20, 20),
                      random.uniform(6, 14),
                      random.uniform(0.4, 0.9),
                      (30, 25, 20))

    def confetti(self, x: float, y: float) -> None:
        """Victory confetti burst."""
        for _ in range(8):
            col = random.choice([
                (255, 215, 0), (0, 200, 255), (255, 80, 120),
                (80, 255, 120), (255, 165, 0)
            ])
            self._add(x, y,
                      random.uniform(-120, 120),
                      random.uniform(-250, -60),
                      random.uniform(4, 10),
                      random.uniform(0.6, 1.4),
                      col)

    # ── Update / Draw ─────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self.pool = [p for p in self.pool if p.life > 0]
        for p in self.pool:
            p.update(dt)

    def draw(self, surf: pygame.Surface, cam_x: float) -> None:
        for p in self.pool:
            p.draw(surf, cam_x)
