# -*- coding: utf-8 -*-
"""
dragkings/hud.py
================
HUD – in-race heads-up display.

Panels:
  • Arc-style tachometer (RPM gauge)
  • Speed readout (km/h)
  • Gear indicator
  • Nitro bar with shimmer
  • Race info bar (timer, distance progress, position)
  • Shift indicator flash
"""

import pygame
import math

from dragkings.constants import (
    SW, SH,
    MAX_RPM, IDLE_RPM, REDLINE_RPM, SHIFT_LIGHT, MAX_GEAR, NITRO_MAX,
    C_WHITE, C_BLACK, C_RED, C_ORANGE, C_YELLOW, C_GREEN, C_CYAN,
    C_HUD, C_DIM,
    F_HUGE, F_BIG, F_MED, F_SM, F_XSM,
    TRACK_LEN_M,
)
from dragkings.utils import draw_rect_alpha, lerp


# ── Helper: arc tachometer ────────────────────────────────────────────────────

def _draw_arc_gauge(surf: pygame.Surface, cx: int, cy: int,
                    radius: int, rpm: float) -> None:
    """
    Draw a circular arc RPM gauge.

    The arc sweeps from 225° (start) to 315° (end, clockwise),
    giving a 270° spread. Colour zones shift green → yellow → red.
    """
    START_ANG = 225   # degrees, measured counter-clockwise from 3 o'clock
    SWEEP     = 270   # total arc degrees

    # Background ring
    pygame.draw.circle(surf, (20, 22, 35), (cx, cy), radius)
    pygame.draw.circle(surf, (40, 45, 65), (cx, cy), radius, 3)

    # Colour zones (fraction of full range)
    zones = [
        (0.00, 0.55, ( 30, 180,  80)),   # green
        (0.55, 0.78, (200, 160,  10)),   # yellow
        (0.78, 0.92, (200,  60,  10)),   # orange
        (0.92, 1.00, (200,  20,  20)),   # red
    ]

    ratio = rpm / MAX_RPM

    for z0, z1, zc in zones:
        # How much of this zone is lit?
        lit_in_zone = max(0.0, min(ratio, z1) - z0) / (z1 - z0) if z1 > z0 else 0
        if lit_in_zone <= 0:
            break

        ang_start = START_ANG - z0 * SWEEP
        ang_end   = START_ANG - min(ratio, z1) * SWEEP

        # Draw arc segments as a series of thick lines
        steps = max(2, int(abs(ang_start - ang_end) * 1.2))
        prev  = None
        for s in range(steps + 1):
            t   = s / steps
            ang = math.radians(lerp(ang_start, ang_end, t))
            px  = cx + int(math.cos(ang) * (radius - 8))
            py  = cy - int(math.sin(ang) * (radius - 8))
            if prev:
                pygame.draw.line(surf, zc, prev, (px, py), 10)
            prev = (px, py)

    # Tick marks at every 1 000 RPM
    for r in range(0, MAX_RPM + 1, 1000):
        frac = r / MAX_RPM
        ang  = math.radians(START_ANG - frac * SWEEP)
        x1   = cx + int(math.cos(ang) * (radius - 18))
        y1   = cy - int(math.sin(ang) * (radius - 18))
        x2   = cx + int(math.cos(ang) * (radius - 4))
        y2   = cy - int(math.sin(ang) * (radius - 4))
        col  = (200, 200, 200) if r % 2000 == 0 else (80, 85, 100)
        pygame.draw.line(surf, col, (x1, y1), (x2, y2), 2 if r % 2000 == 0 else 1)

    # Redline marker
    rl_frac = REDLINE_RPM / MAX_RPM
    rl_ang  = math.radians(START_ANG - rl_frac * SWEEP)
    x1 = cx + int(math.cos(rl_ang) * (radius - 20))
    y1 = cy - int(math.sin(rl_ang) * (radius - 20))
    x2 = cx + int(math.cos(rl_ang) * (radius))
    y2 = cy - int(math.sin(rl_ang) * (radius))
    pygame.draw.line(surf, C_RED, (x1, y1), (x2, y2), 3)

    # Needle
    needle_ang = math.radians(START_ANG - ratio * SWEEP)
    nx = cx + int(math.cos(needle_ang) * (radius - 14))
    ny = cy - int(math.sin(needle_ang) * (radius - 14))
    pygame.draw.line(surf, C_WHITE, (cx, cy), (nx, ny), 2)
    pygame.draw.circle(surf, (50, 55, 75), (cx, cy), 8)
    pygame.draw.circle(surf, C_WHITE,      (cx, cy), 4)


# ── HUD class ─────────────────────────────────────────────────────────────────

class HUD:
    """Draws the complete in-race heads-up display each frame."""

    def draw(self, surf: pygame.Surface, player, race_time: float,
             all_cars: list) -> None:
        self._tachometer(surf, player)
        self._speed_display(surf, player)
        self._gear_display(surf, player)
        self._nitro_bar(surf, player)
        self._race_info(surf, player, race_time, all_cars)
        self._shift_indicator(surf, player)

    # ── Tachometer ────────────────────────────────────────────────────────────

    def _tachometer(self, surf: pygame.Surface, car) -> None:
        cx, cy = SW - 130, SH - 130
        r      = 100

        # Panel bg
        draw_rect_alpha(surf, (12, 14, 26),
                        (cx - r - 10, cy - r - 10, (r + 10) * 2, (r + 10) * 2),
                        200, radius=r + 10)

        _draw_arc_gauge(surf, cx, cy, r, car.rpm)

        # RPM text in centre
        rpm_val = F_SM.render(f"{int(car.rpm):,}", True, C_HUD)
        surf.blit(rpm_val, (cx - rpm_val.get_width() // 2, cy + 18))
        rpm_lbl = F_XSM.render("RPM", True, C_DIM)
        surf.blit(rpm_lbl, (cx - rpm_lbl.get_width() // 2, cy + 42))

    # ── Speed display ─────────────────────────────────────────────────────────

    def _speed_display(self, surf: pygame.Surface, car) -> None:
        sx, sy = SW - 265, SH - 185
        draw_rect_alpha(surf, (15, 18, 30), (sx - 8, sy - 8, 120, 90), 200, radius=12)

        kmh  = int(car.speed * 3.6)
        st   = F_BIG.render(f"{kmh}", True, C_WHITE)
        sl   = F_XSM.render("km/h", True, C_DIM)
        lbl  = F_XSM.render("SPEED", True, C_DIM)
        surf.blit(lbl, (sx, sy))
        surf.blit(st,  (sx + 52 - st.get_width() // 2, sy + 18))
        surf.blit(sl,  (sx + 52 - sl.get_width() // 2, sy + 68))

    # ── Gear display ──────────────────────────────────────────────────────────

    def _gear_display(self, surf: pygame.Surface, car) -> None:
        gx, gy = SW - 265, SH - 100
        draw_rect_alpha(surf, (15, 18, 30), (gx - 8, gy - 8, 100, 70), 200, radius=12)

        g_label = F_XSM.render("GEAR", True, C_DIM)
        surf.blit(g_label, (gx, gy))

        col = C_YELLOW if car.rpm >= SHIFT_LIGHT else C_CYAN
        gt  = F_BIG.render(str(car.gear), True, col)
        surf.blit(gt, (gx + 40 - gt.get_width() // 2, gy + 16))

    # ── Nitro bar ─────────────────────────────────────────────────────────────

    def _nitro_bar(self, surf: pygame.Surface, car) -> None:
        nx, ny, nw, nh = SW - 265, SH - 215, 230, 14
        draw_rect_alpha(surf, (10, 12, 20), (nx - 4, ny - 4, nw + 8, nh + 8), 180, radius=8)

        fill = int(nw * car.nitro / NITRO_MAX)
        nc   = C_CYAN if car.nitro > NITRO_MAX * 0.3 else C_RED
        if fill > 4:
            pygame.draw.rect(surf, nc, (nx, ny, fill, nh), border_radius=5)

            # Shimmer effect when nitro is active
            if car.nitro_on:
                t     = pygame.time.get_ticks() * 0.004
                shim  = int(nx + (math.sin(t) * 0.5 + 0.5) * max(0, fill - 20))
                sw_   = min(20, fill)
                draw_rect_alpha(surf, C_WHITE,
                                (shim, ny, sw_, nh), 80, radius=5)

        pygame.draw.rect(surf, C_DIM, (nx, ny, nw, nh), 1, border_radius=5)
        nl = F_XSM.render("NITRO", True, C_CYAN)
        surf.blit(nl, (nx, ny - 17))

    # ── Race info strip ───────────────────────────────────────────────────────

    def _race_info(self, surf: pygame.Surface, car, race_time: float,
                   all_cars: list) -> None:
        rx, ry = 170, 14
        draw_rect_alpha(surf, (15, 18, 30), (rx - 6, ry - 4, 520, 52), 190, radius=10)

        # Timer
        rt_t = F_MED.render(f"{race_time:.2f}s", True, C_YELLOW)
        surf.blit(rt_t, (rx, ry + 4))

        # Progress bar
        pct      = min(1.0, car.dist / TRACK_LEN_M)
        bx, by_  = rx + 170, ry + 8
        bw, bh_  = 300, 14
        pygame.draw.rect(surf, (30, 35, 50), (bx, by_, bw, bh_), border_radius=6)
        fw = int(pct * bw)
        if fw > 0:
            pygame.draw.rect(surf, C_CYAN, (bx, by_, fw, bh_), border_radius=6)
        pygame.draw.rect(surf, C_DIM, (bx, by_, bw, bh_), 1, border_radius=6)
        fin_t = F_XSM.render("FINISH", True, C_DIM)
        surf.blit(fin_t, (bx + bw + 6, by_ - 1))

        # Distance label
        d_t = F_SM.render(f"{int(car.dist)}m / {int(TRACK_LEN_M)}m", True, C_DIM)
        surf.blit(d_t, (bx, ry + 28))

        # Race position
        ranked = sorted(all_cars, key=lambda c: -c.dist)
        pos    = next((i + 1 for i, c in enumerate(ranked) if c is car), 1)
        suf    = {1: "ST", 2: "ND", 3: "RD"}.get(pos, "TH")
        pos_t  = F_SM.render(f"{pos}{suf} / {len(all_cars)}", True, C_WHITE)
        surf.blit(pos_t, (rx, ry + 28))

    # ── Shift indicator ───────────────────────────────────────────────────────

    def _shift_indicator(self, surf: pygame.Surface, car) -> None:
        if car.rpm >= SHIFT_LIGHT and car.gear < MAX_GEAR:
            flash = int(pygame.time.get_ticks() / 80) % 2 == 0
            if flash:
                s  = F_BIG.render("SHIFT!", True, C_YELLOW)
                sx = SW // 2 - s.get_width() // 2
                # Glow behind text
                draw_rect_alpha(surf, C_YELLOW,
                                (sx - 10, 14, s.get_width() + 20, s.get_height() + 8),
                                50, radius=8)
                surf.blit(s, (sx, 18))
