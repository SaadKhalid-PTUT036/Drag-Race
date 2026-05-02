# -*- coding: utf-8 -*-
"""
dragkings/track.py
==================
draw_track() – renders the full race track for one frame.

Draws (back to front):
  • Grass areas (checker pattern)
  • Road lanes
  • Kerb stripes
  • Distance markers
  • Lane divider dashes
  • Start / finish lines
  • Speed-trap warning line
"""

import pygame

from dragkings.constants import (
    SW, SH,
    ROAD_TOP, LANE_W, TRACK_LEN_M, TRACK_LEN_PX, PX_PER_M,
    C_ROAD, C_GRASS_L, C_GRASS_D, C_KERB_R, C_KERB_W,
    C_LINE_Y, C_LINE_W, C_WHITE, C_BLACK, C_RED, C_YELLOW, C_DIM,
    F_XSM, F_SM, F_MED,
)
from dragkings.utils import draw_rect_alpha


def draw_track(surf: pygame.Surface, cam_x: float, num_lanes: int) -> None:
    """
    Render the track onto *surf* with the camera offset *cam_x* (pixels).

    Parameters
    ----------
    surf      : destination surface (usually the main screen)
    cam_x     : horizontal camera offset in world pixels
    num_lanes : total number of lanes
    """
    road_h    = num_lanes * LANE_W
    finish_px = int(TRACK_LEN_PX - cam_x)

    # ── Grass ─────────────────────────────────────────────────────────────────
    pygame.draw.rect(surf, C_GRASS_L, (0, 0, SW, ROAD_TOP))
    pygame.draw.rect(surf, C_GRASS_L, (0, ROAD_TOP + road_h, SW,
                                        SH - ROAD_TOP - road_h))

    # Checker pattern on grass
    tile = 60
    for row in range(ROAD_TOP // tile + 2):
        for col in range(SW // tile + 2):
            cx_ = col * tile - (int(cam_x) % tile)
            cy_ = row * tile
            if (row + col) % 2 == 0:
                pygame.draw.rect(surf, C_GRASS_D, (cx_, cy_, tile, tile))

    bottom_grass_top = ROAD_TOP + road_h
    for row in range((SH - ROAD_TOP - road_h) // tile + 2):
        for col in range(SW // tile + 2):
            cx_ = col * tile - (int(cam_x) % tile)
            cy_ = bottom_grass_top + row * tile
            if (row + col) % 2 == 0:
                pygame.draw.rect(surf, C_GRASS_D, (cx_, cy_, tile, tile))

    # ── Road surface ──────────────────────────────────────────────────────────
    for lane in range(num_lanes):
        ly = ROAD_TOP + lane * LANE_W
        pygame.draw.rect(surf, C_ROAD, (0, ly, SW, LANE_W))

    # ── Distance markers (every 50 m) ─────────────────────────────────────────
    for m in range(0, int(TRACK_LEN_M) + 1, 50):
        mx = int(m * PX_PER_M - cam_x)
        if -20 < mx < SW + 20:
            pygame.draw.line(surf, (60, 65, 80),
                             (mx, ROAD_TOP), (mx, ROAD_TOP + road_h), 1)
            if m % 100 == 0:
                lbl = F_XSM.render(f"{m}m", True, (80, 90, 110))
                surf.blit(lbl, (mx - lbl.get_width() // 2, ROAD_TOP - 18))

    # ── Kerb stripes ──────────────────────────────────────────────────────────
    kerb_h = 16
    stripe  = 40
    for col in range(SW // stripe + 2):
        cx_  = col * stripe - (int(cam_x) % stripe)
        kc   = C_KERB_R if col % 2 == 0 else C_KERB_W
        pygame.draw.rect(surf, kc, (cx_, ROAD_TOP, stripe, kerb_h))
        pygame.draw.rect(surf, kc, (cx_, ROAD_TOP + road_h - kerb_h, stripe, kerb_h))

    # ── Lane divider dashes ───────────────────────────────────────────────────
    dash_len = 50
    gap_len  = 35
    period   = dash_len + gap_len
    offset   = int(cam_x) % period
    for lane in range(1, num_lanes):
        ly = ROAD_TOP + lane * LANE_W
        x  = -offset
        while x < SW:
            pygame.draw.line(surf, (100, 105, 120), (x, ly), (x + dash_len, ly), 2)
            x += period

    # ── Start line ────────────────────────────────────────────────────────────
    start_px = -int(cam_x)
    if -10 < start_px < SW + 10:
        for k in range(road_h // 16):
            col = C_LINE_W if k % 2 == 0 else C_LINE_Y
            pygame.draw.rect(surf, col, (start_px, ROAD_TOP + k * 16, 16, 16))
        sl = F_SM.render("START", True, C_WHITE)
        surf.blit(sl, (start_px - sl.get_width() - 4, ROAD_TOP - 22))

    # ── Finish line ───────────────────────────────────────────────────────────
    if -10 < finish_px < SW + 10:
        for k in range(road_h // 16):
            col = C_LINE_W if k % 2 == 0 else C_LINE_Y
            pygame.draw.rect(surf, col, (finish_px, ROAD_TOP + k * 16, 18, 16))
        fl = F_MED.render("FINISH", True, C_YELLOW)
        surf.blit(fl, (finish_px - fl.get_width() - 6, ROAD_TOP - 26))
        # Chequered flag
        for ci in range(6):
            for ri in range(4):
                fc = C_WHITE if (ci + ri) % 2 == 0 else C_BLACK
                pygame.draw.rect(surf, fc,
                                 (finish_px + 18 + ci * 10,
                                  ROAD_TOP + ri * 10, 10, 10))

    # ── Speed-trap marker at 300 m ────────────────────────────────────────────
    sp_trap = int(300 * PX_PER_M - cam_x)
    if -40 < sp_trap < SW:
        pygame.draw.line(surf, C_RED,
                         (sp_trap, ROAD_TOP),
                         (sp_trap, ROAD_TOP + road_h), 1)
        st_ = F_XSM.render("SPEED TRAP", True, C_RED)
        surf.blit(st_, (sp_trap - st_.get_width() // 2,
                        ROAD_TOP + road_h + 4))
