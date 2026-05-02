# -*- coding: utf-8 -*-
"""
dragkings/touch.py
==================
TouchInterface – on-screen buttons for mobile / touch devices (Pydroid 3).

Buttons:
  • THROTTLE  – bottom-right, hold to accelerate
  • SHIFT UP  – middle-right, tap to change gear
  • NITRO     – bottom-left,  hold for boost
"""

import pygame

from dragkings.constants import (
    SW, SH,
    C_CYAN, C_ORANGE, C_GREEN, C_WHITE,
    F_MED,
)
from dragkings.utils import draw_rect_alpha


class TouchInterface:
    """Translates finger / mouse events into virtual button states."""

    def __init__(self):
        padding = 20
        bw, bh  = 200, 100

        self.rect_nitro    = pygame.Rect(padding,            SH - bh - padding,       bw, bh)
        self.rect_throttle = pygame.Rect(SW - bw - padding,  SH - bh - padding,       bw, bh)
        self.rect_shift    = pygame.Rect(SW - bw - padding,  SH - bh * 2 - padding * 2, bw, bh)

        self.throttle_held  = False
        self.nitro_held     = False
        self.shift_tapped   = False
        self._active_touches: dict = {}

    # ── Input processing ──────────────────────────────────────────────────────

    def process_events(self, events: list) -> None:
        """Call once per frame with the full event list."""
        self.shift_tapped = False

        for e in events:
            # Multi-touch (FINGER) events
            if hasattr(pygame, 'FINGERDOWN') and \
               e.type == getattr(pygame, 'FINGERDOWN'):
                x, y = e.x * SW, e.y * SH
                self._active_touches[e.finger_id] = (x, y)
                if self.rect_shift.collidepoint(x, y):
                    self.shift_tapped = True

            elif hasattr(pygame, 'FINGERMOTION') and \
                 e.type == getattr(pygame, 'FINGERMOTION'):
                x, y = e.x * SW, e.y * SH
                self._active_touches[e.finger_id] = (x, y)

            elif hasattr(pygame, 'FINGERUP') and \
                 e.type == getattr(pygame, 'FINGERUP'):
                self._active_touches.pop(e.finger_id, None)

            # Mouse fallback (for Pydroid and PC testing)
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                x, y = e.pos
                self._active_touches['mouse'] = (x, y)
                if self.rect_shift.collidepoint(x, y):
                    self.shift_tapped = True

            elif e.type == pygame.MOUSEMOTION and 'mouse' in self._active_touches:
                self._active_touches['mouse'] = e.pos

            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                self._active_touches.pop('mouse', None)

        # Determine held states from current touch positions
        self.throttle_held = False
        self.nitro_held    = False
        for x, y in self._active_touches.values():
            if self.rect_throttle.collidepoint(x, y):
                self.throttle_held = True
            if self.rect_nitro.collidepoint(x, y):
                self.nitro_held = True

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw_hud(self, surf: pygame.Surface, state: int) -> None:
        """
        Draw on-screen buttons when in STAGING (1) or RACE (2) state.
        """
        if state not in (1, 2):
            return

        btn_alpha = 110

        buttons = [
            (self.rect_nitro,    C_CYAN,   "NITRO",    self.nitro_held),
            (self.rect_shift,    C_ORANGE, "SHIFT UP", self.shift_tapped),
            (self.rect_throttle, C_GREEN,  "THROTTLE", self.throttle_held),
        ]

        for rect, colour, label, active in buttons:
            draw_rect_alpha(surf, colour, rect,
                            btn_alpha if active else 40, radius=12)
            pygame.draw.rect(surf, colour, rect, 3, border_radius=12)
            txt = F_MED.render(label, True, C_WHITE)
            surf.blit(txt, (rect.centerx - txt.get_width()  // 2,
                            rect.centery - txt.get_height() // 2))
