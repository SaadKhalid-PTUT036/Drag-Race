# -*- coding: utf-8 -*-
"""
dragkings/screens/results.py
=============================
ResultsScreen – post-race podium display with:
  • Animated podium columns (1st / 2nd / 3rd)
  • Staggered row slide-in for each car result
  • Trophy glow for the winner
  • Confetti burst on first render
  • Reaction-time display
  • MENU and RACE AGAIN buttons
"""

import pygame
import math
import random

from dragkings.constants import (
    SW, SH,
    C_WHITE, C_BLACK, C_DIM, C_RED, C_YELLOW, C_GREEN, C_CYAN,
    C_GOLD, C_SILVER, C_BRONZE,
    F_BIG, F_MED, F_SM, F_XSM,
)
from dragkings.utils import draw_rect_alpha, fmt_time


# ── Medal colour helper ────────────────────────────────────────────────────────
_RANK_COLOURS  = [C_GOLD, C_SILVER, C_BRONZE, (140, 140, 160)]
_RANK_LABELS   = ["1ST", "2ND", "3RD", "4TH"]
_PODIUM_HEIGHTS = [170, 120, 80, 50]   # pixel height of each podium column


class ResultsScreen:
    """Animated race results / podium screen."""

    def __init__(self):
        cx = SW // 2
        self.btn_menu    = pygame.Rect(cx - 175, SH - 90, 160, 56)
        self.btn_restart = pygame.Rect(cx + 15,  SH - 90, 160, 56)

        self._t          = 0.0
        self._confetti   = []   # list of [x, y, vx, vy, col, life]
        self._conf_done  = False

    # ── Control ───────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self._t += dt

        # Spawn confetti once
        if not self._conf_done and self._t > 0.3:
            self._conf_done = True
            for _ in range(120):
                col = random.choice([C_GOLD, (0,200,255),(255,80,120),(80,255,120),C_YELLOW])
                self._confetti.append([
                    random.randint(SW // 4, SW * 3 // 4),
                    -10,
                    random.uniform(-60, 60),
                    random.uniform(80, 200),
                    col,
                    random.uniform(1.5, 3.0),   # lifetime
                ])

        # Update confetti
        new_conf = []
        for c in self._confetti:
            c[0] += c[2] * dt
            c[1] += c[3] * dt
            c[5]  -= dt
            if c[5] > 0 and c[1] < SH + 20:
                new_conf.append(c)
        self._confetti = new_conf

    def handle(self, event) -> str | None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            if self.btn_menu.collidepoint(mp):    return 'menu'
            if self.btn_restart.collidepoint(mp): return 'restart'
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:      return 'restart'
            if event.key == pygame.K_ESCAPE: return 'menu'
        return None

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf: pygame.Surface, cars: list, player) -> None:
        self._draw_background(surf)
        ranked = sorted(cars, key=lambda c: (c.finish_time or 9999, -c.dist))
        self._draw_podium(surf, ranked, player)
        self._draw_results_table(surf, ranked, player)
        self._draw_reaction(surf, player)
        self._draw_confetti(surf)
        self._draw_buttons(surf)

    # ── Sub-draw helpers ──────────────────────────────────────────────────────

    def _draw_background(self, surf: pygame.Surface) -> None:
        for y in range(SH):
            t = y / SH
            pygame.draw.line(surf,
                             (int(6 + 18 * t), int(20 + 12 * t), int(6 + 18 * t)),
                             (0, y), (SW, y))

    def _draw_podium(self, surf: pygame.Surface, ranked: list, player) -> None:
        """Draw three podium columns for the top 3 finishers."""
        title = F_BIG.render("RACE  RESULTS", True, C_GREEN)
        surf.blit(title, (SW // 2 - title.get_width() // 2, 22))

        # Podium positions: 1st centre, 2nd left, 3rd right
        base_y    = 310
        col_w     = 80
        positions = [1, 0, 2]   # render order: 2nd, 1st, 3rd
        cx_offsets = [-100, 0, 100]

        for order_i, (rank_i, cx_off) in enumerate(zip(positions, cx_offsets)):
            if rank_i >= len(ranked):
                continue
            car      = ranked[rank_i]
            ph       = _PODIUM_HEIGHTS[rank_i]
            cx       = SW // 2 + cx_off
            col_rect = (cx - col_w // 2, base_y - ph, col_w, ph)

            colour = _RANK_COLOURS[rank_i]

            # Slide-in animation: columns rise from below
            slide  = min(1.0, max(0.0, self._t - rank_i * 0.2) * 3.0)
            drawn_h = int(ph * slide)
            if drawn_h > 0:
                draw_rect_alpha(surf, colour,
                                (cx - col_w // 2, base_y - drawn_h,
                                 col_w, drawn_h),
                                160, radius=6)
                pygame.draw.rect(surf, tuple(min(255, c + 60) for c in colour),
                                 (cx - col_w // 2, base_y - drawn_h,
                                  col_w, drawn_h), 2, border_radius=6)

            # Rank label on column
            if slide >= 1.0:
                lbl = F_MED.render(_RANK_LABELS[rank_i], True, C_WHITE)
                surf.blit(lbl, (cx - lbl.get_width() // 2, base_y - ph + 6))

            # Car colour dot above column
            dot_y = base_y - ph - 20
            if slide >= 1.0:
                pygame.draw.circle(surf, car.colour, (cx, dot_y), 12)
                pygame.draw.circle(surf, C_WHITE,    (cx, dot_y), 12, 2)

                name = "YOU" if car is player else f"AI {ranked.index(car)}"
                n_t  = F_XSM.render(name, True, C_WHITE)
                surf.blit(n_t, (cx - n_t.get_width() // 2, dot_y - 22))

            # Trophy glow for 1st place
            if rank_i == 0 and slide >= 1.0:
                pulse = abs(math.sin(self._t * 3.0))
                draw_rect_alpha(surf, C_GOLD,
                                (cx - 50, base_y - ph - 50, 100, 100),
                                int(40 * pulse), radius=50)

    def _draw_results_table(self, surf: pygame.Surface, ranked: list, player) -> None:
        table_x = SW // 2 - 370
        table_y = 330

        for i, car in enumerate(ranked):
            # Staggered slide-in: rows enter from right
            slide  = min(1.0, max(0.0, self._t - 0.4 - i * 0.12) * 4.0)
            off_x  = int((1.0 - slide) * 200)

            row_y  = table_y + i * 72
            col    = _RANK_COLOURS[min(i, 3)]
            name   = "YOU" if car is player else f"AI {i}"
            ft     = car.finish_time

            # Row background
            rx = table_x + off_x
            draw_rect_alpha(surf, (20, 25, 38),
                            (rx, row_y, 740, 62), 200, radius=10)
            if car is player:
                draw_rect_alpha(surf, (30, 90, 200),
                                (rx, row_y, 740, 62), 55, radius=10)

            if slide < 0.05:
                continue

            # Car colour block
            pygame.draw.rect(surf, car.colour,
                             (rx + 10, row_y + 18, 12, 26), border_radius=3)

            # Rank
            rank_t = F_MED.render(_RANK_LABELS[min(i, 3)], True, col)
            surf.blit(rank_t, (rx + 30, row_y + 14))

            # Name
            name_t = F_MED.render(name, True, C_WHITE)
            surf.blit(name_t, (rx + 110, row_y + 14))

            # Time
            time_t = F_MED.render(fmt_time(ft), True, (130, 220, 130))
            surf.blit(time_t, (rx + 340, row_y + 14))

            # Speed at finish
            kmh_t = F_SM.render(f"{int(car.speed * 3.6)} km/h", True, C_DIM)
            surf.blit(kmh_t, (rx + 560, row_y + 18))

            # Separator
            if i < len(ranked) - 1:
                pygame.draw.line(surf, (40, 45, 60),
                                 (rx + 10, row_y + 62),
                                 (rx + 730, row_y + 62), 1)

    def _draw_reaction(self, surf: pygame.Surface, player) -> None:
        if player.reaction_time is not None and player.reaction_time > 0:
            rt_t = F_SM.render(
                f"Your reaction time: {player.reaction_time:.3f}s",
                True, C_DIM)
            surf.blit(rt_t, (SW // 2 - rt_t.get_width() // 2, SH - 130))

    def _draw_confetti(self, surf: pygame.Surface) -> None:
        for c in self._confetti:
            sz = 5
            s  = pygame.Surface((sz, sz), pygame.SRCALPHA)
            alpha = int(255 * min(1.0, c[5]))
            s.fill((*c[4], alpha))
            surf.blit(s, (int(c[0]), int(c[1])))

    def _draw_buttons(self, surf: pygame.Surface) -> None:
        mp = pygame.mouse.get_pos()
        configs = [
            (self.btn_menu,    "◀  MENU",      (25, 55, 120), (50, 100, 220)),
            (self.btn_restart, "↺  RACE AGAIN", (20, 80, 20),  (30, 160, 60)),
        ]
        for btn, label, base_col, hover_col in configs:
            hov = btn.collidepoint(mp)
            col = hover_col if hov else base_col
            pygame.draw.rect(surf, col, btn, border_radius=12)
            pygame.draw.rect(surf, tuple(min(255, c + 80) for c in col),
                             btn, 2, border_radius=12)
            bt = F_SM.render(label, True, C_WHITE)
            surf.blit(bt, (btn.x + (btn.w - bt.get_width())  // 2,
                           btn.y + (btn.h - bt.get_height()) // 2))
