# -*- coding: utf-8 -*-
"""
dragkings/christmas_tree.py
============================
ChristmasTree – staging / launch-light sequence.

Sequence:
  • 3 amber bulbs light up 0.5 s apart
  • Green GO light fires at 2.2 s
  • Detects false starts before green
"""

import pygame

from dragkings.constants import (
    C_ORANGE, C_GREEN, C_WHITE, C_DIM,
    F_XSM, F_MED,
)
from dragkings.utils import draw_rect_alpha


class ChristmasTree:
    """Staging lights that count down to GO.  Call start() to begin."""

    STAGE_TIMES = [0.5, 1.0, 1.5, 2.2]   # seconds to illuminate each stage

    def __init__(self):
        self.timer       = 0.0
        self.stage       = -1       # -1 = idle
        self.started     = False
        self.green       = False
        self.false_start = False

    # ── Control ───────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Begin the countdown sequence."""
        self.started = True
        self.timer   = 0.0
        self.stage   = 0

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if not self.started or self.green:
            return
        self.timer += dt
        for i, t in enumerate(self.STAGE_TIMES):
            if self.timer >= t:
                self.stage = i
        if self.timer >= self.STAGE_TIMES[-1]:
            self.green = True

    # ── Property ──────────────────────────────────────────────────────────────

    @property
    def go(self) -> bool:
        """True once the green light is lit."""
        return self.green

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf: pygame.Surface) -> None:
        """Draw the panel on the left side of the screen."""
        cx = 80

        # Panel background
        draw_rect_alpha(surf, (10, 12, 20), (20, 60, 120, 340), 220, radius=14)
        pygame.draw.rect(surf, (40, 50, 70), (20, 60, 120, 340), 2, border_radius=14)

        label = F_XSM.render("CHRISTMAS TREE", True, C_DIM)
        surf.blit(label, (25, 68))

        # 3 amber bulbs
        for i in range(3):
            gy  = 100 + i * 70
            lit = self.started and self.stage >= i and not self.green
            col = C_ORANGE if lit else (50, 35, 10)
            pygame.draw.circle(surf, col, (cx, gy), 22)
            pygame.draw.circle(surf, (200, 200, 200), (cx, gy), 22, 2)
            if lit:
                draw_rect_alpha(surf, C_ORANGE,
                                (cx - 30, gy - 30, 60, 60), 50, radius=30)

        # Green GO light
        gy_g = 100 + 3 * 70
        gcol = C_GREEN if self.green else (10, 50, 20)
        pygame.draw.circle(surf, gcol, (cx, gy_g), 28)
        pygame.draw.circle(surf, (200, 200, 200), (cx, gy_g), 28, 2)
        if self.green:
            draw_rect_alpha(surf, C_GREEN,
                            (cx - 38, gy_g - 38, 76, 76), 60, radius=38)
            go_t = F_MED.render("GO!", True, C_WHITE)
            surf.blit(go_t, (cx - go_t.get_width()  // 2,
                              gy_g - go_t.get_height() // 2))
