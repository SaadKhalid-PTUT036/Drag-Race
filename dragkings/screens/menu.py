# -*- coding: utf-8 -*-
"""
dragkings/screens/menu.py
=========================
MenuScreen – animated main menu with:
  • Deep-space gradient background
  • Twinkling star field
  • Neon perspective road vanishing into the horizon
  • Floating ember particles
  • Chrome glow title ("DRAG KINGS")
  • Animated car silhouettes sliding across
  • Pulsing glowing buttons
"""

import pygame
import math
import random

from dragkings.constants import (
    SW, SH,
    C_WHITE, C_DIM, C_CYAN, C_YELLOW, C_ORANGE,
    F_HUGE, F_BIG, F_MED, F_SM, F_XSM,
    CAR_COLOURS,
)
from dragkings.utils import draw_rect_alpha, render_glow
from dragkings.car import make_dragster


# ── Simple ember particle for menu ────────────────────────────────────────────

class _Ember:
    __slots__ = ('x', 'y', 'vy', 'size', 'alpha', 'colour')

    def __init__(self):
        self._reset()

    def _reset(self):
        self.x      = random.randint(0, SW)
        self.y      = random.randint(0, SH)
        self.vy     = random.uniform(-18, -6)
        self.size   = random.uniform(1.5, 4.0)
        self.alpha  = random.randint(80, 200)
        self.colour = random.choice([
            (255, 180,  40),
            (255, 100,  20),
            ( 30, 180, 255),
            (180,  60, 255),
        ])

    def update(self, dt):
        self.y     += self.vy * dt
        self.alpha -= int(dt * 60)
        if self.y < 0 or self.alpha <= 0:
            self._reset()
            self.y = SH + 5

    def draw(self, surf):
        sz = max(1, int(self.size))
        s  = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.colour, max(0, self.alpha)), (sz, sz), sz)
        surf.blit(s, (int(self.x) - sz, int(self.y) - sz))


# ── MenuScreen ────────────────────────────────────────────────────────────────

class MenuScreen:
    """Animated main menu screen."""

    def __init__(self):
        self._t   = 0.0
        cx        = SW // 2

        self.btn_start = pygame.Rect(cx - 160, SH // 2 + 80,  320, 64)
        self.btn_quit  = pygame.Rect(cx - 160, SH // 2 + 160, 320, 64)

        # Pre-bake glowing title surface
        self._title_surf = render_glow(
            F_HUGE, "DRAG  KINGS",
            colour      = (255, 255, 255),
            glow_colour = (40, 120, 255),
            glow_alpha  = 110,
        )

        # Star field (static positions, animated alpha)
        self._stars = [
            (random.randint(0, SW), random.randint(0, SH * 2 // 3),
             random.uniform(0.5, 2.5), random.uniform(0, math.pi * 2))
            for _ in range(120)
        ]

        # Embers
        self._embers = [_Ember() for _ in range(55)]

        # Sliding car preview state  (x position per car, starting off-screen)
        self._car_surfs = [make_dragster(c, w=90, h=38) for c in CAR_COLOURS]
        self._car_x     = [-(120 + i * 160) for i in range(4)]  # start off left
        self._car_speed = [random.uniform(90, 150) for _ in range(4)]

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self._t += dt
        for e in self._embers:
            e.update(dt)
        for i in range(4):
            self._car_x[i] += self._car_speed[i] * dt
            if self._car_x[i] > SW + 120:
                self._car_x[i] = -random.randint(80, 200)
                self._car_speed[i] = random.uniform(90, 160)

    # ── Events ────────────────────────────────────────────────────────────────

    def handle(self, event) -> str | None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            if self.btn_start.collidepoint(mp):
                return 'start'
            if self.btn_quit.collidepoint(mp):
                return 'quit'
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return 'start'
            if event.key == pygame.K_ESCAPE:
                return 'quit'
        return None

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf: pygame.Surface) -> None:
        self._draw_background(surf)
        self._draw_road(surf)
        self._draw_stars(surf)
        self._draw_embers(surf)
        self._draw_cars(surf)
        self._draw_title(surf)
        self._draw_subtitle(surf)
        self._draw_controls(surf)
        self._draw_buttons(surf)

    # ── Sub-draw helpers ──────────────────────────────────────────────────────

    def _draw_background(self, surf: pygame.Surface) -> None:
        """Deep-space gradient: near-black top → deep navy bottom."""
        for y in range(SH):
            t = y / SH
            r = int(6  + 16 * t)
            g = int(8  + 14 * t)
            b = int(18 + 28 * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (SW, y))

    def _draw_road(self, surf: pygame.Surface) -> None:
        """
        Perspective road vanishing at a centre point on the horizon.
        The road widens as it nears the bottom of the screen.
        Lane lines scroll outward over time.
        """
        horizon_y = SH // 2 - 20
        vp_x      = SW // 2          # vanishing point x

        # Road fill (trapezoid)
        road_top_w  = 60
        road_bot_w  = SW
        road_top_y  = horizon_y
        road_bot_y  = SH

        pts = [
            (vp_x - road_top_w // 2, road_top_y),
            (vp_x + road_top_w // 2, road_top_y),
            (vp_x + road_bot_w // 2, road_bot_y),
            (vp_x - road_bot_w // 2, road_bot_y),
        ]
        pygame.draw.polygon(surf, (28, 30, 42), pts)

        # Glow horizon line
        pygame.draw.line(surf, (40, 80, 180),
                         (vp_x - 200, horizon_y),
                         (vp_x + 200, horizon_y), 2)

        # Scrolling perspective lane lines (4 lanes)
        scroll = (self._t * 0.6) % 1.0
        for lane in range(-3, 4):
            if lane == 0:
                continue
            for seg in range(6):
                t0 = (seg + scroll) / 6.0
                t1 = (seg + scroll + 0.35) / 6.0
                if t0 > 1.0:
                    t0 -= 1.0
                if t1 > 1.0:
                    t1 -= 1.0
                if t0 > t1:
                    continue

                half_w = road_top_w // 2 + (road_bot_w // 2 - road_top_w // 2)

                def interp(tt):
                    y  = road_top_y + tt * (road_bot_y - road_top_y)
                    hw = road_top_w // 2 + tt * (road_bot_w // 2 - road_top_w // 2)
                    x  = vp_x + lane * hw // 4
                    return int(x), int(y)

                p0 = interp(t0)
                p1 = interp(t1)
                alpha = int(30 + 100 * t0)
                pygame.draw.line(surf, (60, 65, 90), p0, p1,
                                 max(1, int(t0 * 3)))

        # Kerb stripes at road edges
        kerb_colors = [(200, 30, 30), (230, 230, 230)]
        stripe_w    = 40
        for i in range(int(SW / stripe_w) + 2):
            kc = kerb_colors[i % 2]
            # bottom kerb
            xL = vp_x - SW // 2 + i * stripe_w
            pygame.draw.rect(surf, kc, (xL, SH - 18, stripe_w, 18))

    def _draw_stars(self, surf: pygame.Surface) -> None:
        for sx, sy, size, phase in self._stars:
            a = int(120 + 100 * math.sin(self._t * 1.2 + phase))
            r = max(1, int(size))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, max(0, a)), (r, r), r)
            surf.blit(s, (sx - r, sy - r))

    def _draw_embers(self, surf: pygame.Surface) -> None:
        for e in self._embers:
            e.draw(surf)

    def _draw_cars(self, surf: pygame.Surface) -> None:
        """Animated cars sliding from left to right across the road."""
        y_base = SH - 60
        for i, (car_surf, cx) in enumerate(zip(self._car_surfs, self._car_x)):
            lane_y = y_base - i * 6   # slight vertical stagger
            surf.blit(car_surf, (int(cx), lane_y))

    def _draw_title(self, surf: pygame.Surface) -> None:
        """Pulsing chrome glow title."""
        ts    = self._title_surf
        pulse = math.sin(self._t * 2.0) * 0.15 + 0.85
        scale = pygame.transform.smoothscale(
            ts,
            (int(ts.get_width() * pulse), int(ts.get_height() * pulse))
        )
        tx = SW // 2 - scale.get_width()  // 2
        ty = SH // 4 - scale.get_height() // 2
        surf.blit(scale, (tx, ty))

    def _draw_subtitle(self, surf: pygame.Surface) -> None:
        sub = F_SM.render("QUARTER MILE DRAG RACING", True, (120, 160, 220))
        surf.blit(sub, (SW // 2 - sub.get_width() // 2, SH // 4 + 80))

    def _draw_controls(self, surf: pygame.Surface) -> None:
        hints = [
            ("SPACE", "Throttle"),
            ("SHIFT", "Shift Up"),
            ("CTRL",  "Nitro"),
            ("R",     "Restart"),
            ("ESC",   "Menu"),
        ]
        total_w = 0
        renders = []
        for key, action in hints:
            k = F_XSM.render(f" {key} ", True, C_WHITE)
            a = F_XSM.render(f" {action}  ", True, C_DIM)
            renders.append((k, a))
            total_w += k.get_width() + a.get_width()

        x = SW // 2 - total_w // 2
        y = SH // 2 + 40
        for k_surf, a_surf in renders:
            draw_rect_alpha(surf, (40, 50, 80),
                            (x - 2, y - 2, k_surf.get_width() + 4, k_surf.get_height() + 4),
                            180, radius=4)
            surf.blit(k_surf, (x, y))
            x += k_surf.get_width()
            surf.blit(a_surf, (x, y))
            x += a_surf.get_width()

    def _draw_buttons(self, surf: pygame.Surface) -> None:
        mp    = pygame.mouse.get_pos()
        pulse = abs(math.sin(self._t * 3.0))

        configs = [
            (self.btn_start, "▶   START RACE", (30, 110, 255), (0, 160, 255)),
            (self.btn_quit,  "✕   QUIT",       (100, 20, 20),  (200, 40, 40)),
        ]

        for btn, label, base_col, hover_col in configs:
            hov = btn.collidepoint(mp)
            col = hover_col if hov else base_col

            # Glow behind button when hovered
            if hov:
                glow_alpha = int(50 + 30 * pulse)
                draw_rect_alpha(surf, col,
                                (btn.x - 8, btn.y - 8, btn.w + 16, btn.h + 16),
                                glow_alpha, radius=18)

            pygame.draw.rect(surf, col, btn, border_radius=14)

            # Animated border
            border_col = tuple(min(255, c + 80 + int(60 * pulse)) for c in col)
            pygame.draw.rect(surf, border_col, btn, 2, border_radius=14)

            # Label
            bt = F_MED.render(label, True, C_WHITE)
            surf.blit(bt, (btn.x + (btn.w - bt.get_width())  // 2,
                           btn.y + (btn.h - bt.get_height()) // 2))
