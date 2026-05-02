# -*- coding: utf-8 -*-
"""
dragkings/car.py
================
make_dragster()  – procedural side-view dragster sprite generator.
Car              – vehicle physics, RPM simulation, gear shifting, nitro.
torque_at()      – torque curve helper.
"""

import pygame
import math
import random

from dragkings.constants import (
    IDLE_RPM, MAX_RPM, REDLINE_RPM, SHIFT_LIGHT, MAX_GEAR,
    GEAR_RATIOS, FINAL_DRIVE, WHEEL_CIRC,
    ACCEL_BASE, CLUTCH_SLIP, NITRO_BOOST, NITRO_MAX,
    RPM_RISE, RPM_FALL, TRACK_LEN_M, PX_PER_M,
    ROAD_TOP, LANE_W,
)
from dragkings.utils import lerp


# ── Torque curve ───────────────────────────────────────────────────────────────

def torque_at(rpm: float) -> float:
    """Simplified torque curve peaking at 5 500 RPM (returns 0–1 multiplier)."""
    if rpm < 1500:
        return 0.40
    if rpm < 5500:
        return 0.40 + 0.60 * (rpm - 1500) / 4000
    if rpm < 7500:
        return 1.00
    return 1.00 - 0.70 * (rpm - 7500) / (MAX_RPM - 7500)


# ── Sprite generator ──────────────────────────────────────────────────────────

def make_dragster(colour: tuple, w: int = 80, h: int = 34) -> pygame.Surface:
    """Draw and return a sleek side-view dragster surface."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    bc = colour
    dk = tuple(max(0, c - 60) for c in bc)
    lt = tuple(min(255, c + 80) for c in bc)

    # Main body
    body_pts = [
        (0, h // 2 + 4), (8, h - 4), (w - 10, h - 4),
        (w - 2, h // 2 + 2), (w - 2, h // 2 - 4),
        (w - 10, 4), (20, 4), (8, h // 2 - 6),
    ]
    pygame.draw.polygon(surf, bc, body_pts)
    pygame.draw.polygon(surf, dk, body_pts, 2)

    # Cockpit dome
    dome_pts = [(22, 4), (20, h // 2 - 4), (46, h // 2 - 6), (50, 4)]
    pygame.draw.polygon(surf, (140, 200, 255, 200), dome_pts)
    pygame.draw.polygon(surf, lt, dome_pts, 1)

    # Rear spoiler
    pygame.draw.rect(surf, dk, (w - 14, 2, 6, h // 2 + 2), border_radius=2)
    pygame.draw.rect(surf, bc, (w - 18, 2, 14, 5),          border_radius=2)

    # Front splitter
    pygame.draw.rect(surf, dk, (0, h // 2 + 2, 10, 4), border_radius=1)

    # Wheels
    wc  = (25, 25, 30)
    rim = (160, 160, 190)
    pygame.draw.circle(surf, wc,  (w - 16, h - 6), 9)   # rear
    pygame.draw.circle(surf, rim, (w - 16, h - 6), 5)
    pygame.draw.circle(surf, wc,  (14, h - 6), 6)        # front
    pygame.draw.circle(surf, rim, (14, h - 6), 3)

    # Exhaust pipes
    pygame.draw.rect(surf, (60, 60, 70), (w - 6, h // 2 - 1, 8, 4), border_radius=1)
    pygame.draw.rect(surf, (60, 60, 70), (w - 6, h // 2 + 4, 8, 4), border_radius=1)

    # Highlight stripe
    pygame.draw.line(surf, lt, (22, 8), (w - 12, 8), 2)

    return surf


# ── Car class ─────────────────────────────────────────────────────────────────

class Car:
    """
    A single drag-racing vehicle.

    Parameters
    ----------
    lane       : int   – 0 = player lane, 1-3 = AI lanes
    colour     : tuple – RGB colour for the body
    is_player  : bool  – enables player input; disables AI logic
    ai_skill   : float – 0.9 (slow) … 1.1 (fast)
    """

    def __init__(self, lane: int, colour: tuple,
                 is_player: bool = False, ai_skill: float = 1.0):
        self.lane      = lane
        self.is_player = is_player
        self.colour    = colour
        self.ai_skill  = ai_skill

        # Physics state
        self.dist     = 0.0       # metres from start line
        self.speed    = 0.0       # m/s
        self.gear     = 1
        self.rpm      = float(IDLE_RPM)
        self.nitro    = float(NITRO_MAX)
        self.nitro_on = False
        self.clutch   = 0.0       # slip timer (seconds)

        # Race state
        self.finished              = False
        self.finish_time: float | None = None
        self.reaction_time: float | None = None
        self._waiting_launch       = True

        # AI timing state
        self._ai_shift_delay = random.uniform(0.0, 0.15) / ai_skill
        self._ai_shift_t     = 0.0
        self._ai_nitro_t     = random.uniform(0.5, 2.0) / ai_skill

        # Sprite
        self.surf = make_dragster(colour)
        self.sw   = self.surf.get_width()
        self.sh   = self.surf.get_height()

        # Fixed screen-Y centre of this lane
        self.screen_y = ROAD_TOP + (lane + 0.5) * LANE_W

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def dist_px(self) -> float:
        """World-space X position in pixels."""
        return self.dist * PX_PER_M

    # ── Private helpers ───────────────────────────────────────────────────────

    def _speed_to_rpm(self) -> float:
        """Theoretical RPM derived from current speed and gear ratio."""
        if self.gear == 0 or self.speed < 0.1:
            return float(IDLE_RPM)
        ratio = GEAR_RATIOS[self.gear]
        rps   = self.speed / WHEEL_CIRC * ratio * FINAL_DRIVE
        return rps * 60.0

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float, throttle: float,
               shift_up: bool, shift_down: bool,
               nitro_key: bool, race_time: float,
               particles, reaction_offset: float = 0.0) -> None:
        """
        Advance physics by dt seconds.

        Parameters
        ----------
        dt             : delta-time in seconds
        throttle       : 0.0 = off, 1.0 = full
        shift_up/down  : gear change requests (one-shot this frame)
        nitro_key      : True if nitro button is held
        race_time      : elapsed race time (for finish timestamp)
        particles      : Particles instance for visual effects
        """
        if self.finished:
            return

        # ── Clutch slip ───────────────────────────────────────────────────────
        if self.clutch > 0:
            self.clutch         = max(0.0, self.clutch - dt)
            effective_throttle  = throttle * (1.0 - self.clutch / CLUTCH_SLIP)
        else:
            effective_throttle  = throttle

        # ── Gear shift up ─────────────────────────────────────────────────────
        if shift_up and self.gear < MAX_GEAR and self.speed > 2.0:
            old_ratio  = GEAR_RATIOS[self.gear]
            self.gear += 1
            new_ratio  = GEAR_RATIOS[self.gear]
            self.rpm   = max(IDLE_RPM, self.rpm * new_ratio / old_ratio)
            self.clutch = CLUTCH_SLIP

        # ── Gear shift down ───────────────────────────────────────────────────
        if shift_down and self.gear > 1:
            old_ratio  = GEAR_RATIOS[self.gear]
            self.gear -= 1
            new_ratio  = GEAR_RATIOS[self.gear]
            self.rpm   = min(REDLINE_RPM, self.rpm * new_ratio / old_ratio)
            self.clutch = CLUTCH_SLIP * 0.5

        # ── Nitro ─────────────────────────────────────────────────────────────
        self.nitro_on = False
        if nitro_key and self.nitro > 0 and effective_throttle > 0.5:
            self.nitro_on = True
            self.nitro    = max(0.0, self.nitro - dt)

        # ── RPM simulation ────────────────────────────────────────────────────
        target_rpm = self._speed_to_rpm() if self.speed > 1 else IDLE_RPM
        if effective_throttle > 0.1:
            self.rpm += RPM_RISE * dt * effective_throttle
        else:
            self.rpm -= RPM_FALL * dt
        self.rpm = max(IDLE_RPM, min(MAX_RPM, self.rpm))

        if self.speed > 5:
            blend    = min(1.0, self.speed / 30.0)
            self.rpm = lerp(self.rpm, target_rpm, blend * dt * 3)
            self.rpm = max(IDLE_RPM, min(MAX_RPM, self.rpm))

        # ── Acceleration ──────────────────────────────────────────────────────
        if effective_throttle > 0.01:
            torque   = torque_at(self.rpm)
            gear_fac = 1.0 / (GEAR_RATIOS[self.gear] * 0.45)
            accel    = ACCEL_BASE * torque * gear_fac * effective_throttle
            if self.nitro_on:
                accel += NITRO_BOOST
            self.speed += accel * dt
        else:
            self.speed = max(0.0, self.speed - 4.0 * dt)   # engine braking

        # Aerodynamic drag
        drag       = 0.0006 * self.speed * self.speed
        self.speed = max(0.0, self.speed - drag * dt)

        # Soft top-speed cap
        top = 95.0
        if self.speed > top:
            self.speed = lerp(self.speed, top, dt * 2)

        # ── Position & finish ─────────────────────────────────────────────────
        self.dist += self.speed * dt
        if self.dist >= TRACK_LEN_M and not self.finished:
            self.finished    = True
            self.finish_time = race_time

        # ── Particles ─────────────────────────────────────────────────────────
        px = self.dist_px
        py = self.screen_y

        if self.nitro_on:
            particles.nitro(px - self.sw, py)

        if effective_throttle > 0.5 and self.speed > 1:
            particles.smoke(px - self.sw + 10, py)

        if self.clutch > 0.05 and self.speed < 15:
            particles.burnout(px - self.sw // 2, py + 12)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf: pygame.Surface, cam_x: float) -> None:
        """Blit the car sprite at its screen position."""
        sx = int(self.dist_px - cam_x)
        sy = int(self.screen_y - self.sh // 2)
        surf.blit(self.surf, (sx, sy))

        # Shift-light glow overlay when near redline
        if self.rpm >= SHIFT_LIGHT and not self.finished:
            glow  = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
            alpha = int(80 + 60 * math.sin(pygame.time.get_ticks() * 0.015))
            glow.fill((255, 220, 0, max(0, alpha)))
            surf.blit(glow, (sx, sy), special_flags=pygame.BLEND_RGBA_ADD)
