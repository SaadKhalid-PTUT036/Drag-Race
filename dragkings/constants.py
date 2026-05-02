# -*- coding: utf-8 -*-
"""
dragkings/constants.py
======================
Initialises pygame, creates the display, and defines every game-wide
constant: screen dimensions, colours, fonts, track geometry and physics.

All other modules import from here so there is a single source of truth.
"""

import pygame

pygame.init()

# ── Display ────────────────────────────────────────────────────────────────────
_info = pygame.display.Info()
SW: int = _info.current_w
SH: int = _info.current_h
if SW < 800 or SH < 400:          # fallback for PC / windowed mode
    SW, SH = 1280, 720

screen = pygame.display.set_mode((SW, SH), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("DRAG KINGS  |  Quarter Mile Challenge")
clock  = pygame.time.Clock()
FPS    = 60

# ── Colour palette ─────────────────────────────────────────────────────────────
C_BG        = ( 12,  14,  22)
C_ROAD      = ( 35,  38,  48)
C_ROAD_DARK = ( 28,  30,  40)
C_LINE_Y    = (240, 200,  30)
C_LINE_W    = (220, 220, 220)
C_GRASS_L   = ( 25,  80,  30)
C_GRASS_D   = ( 18,  60,  22)
C_KERB_R    = (200,  30,  30)
C_KERB_W    = (230, 230, 230)
C_WHITE     = (255, 255, 255)
C_BLACK     = (  0,   0,   0)
C_RED       = (220,  30,  30)
C_ORANGE    = (255, 140,   0)
C_YELLOW    = (255, 220,  20)
C_GREEN     = ( 30, 220,  80)
C_CYAN      = ( 30, 200, 255)
C_PURPLE    = (160,  30, 220)
C_HUD       = (200, 210, 230)
C_DIM       = ( 80,  90, 110)
C_GOLD      = (255, 215,   0)
C_SILVER    = (192, 192, 192)
C_BRONZE    = (205, 127,  50)

# ── Fonts ──────────────────────────────────────────────────────────────────────
F_HUGE  = pygame.font.SysFont("arial",     88, bold=True)
F_TITLE = pygame.font.SysFont("arial",     72, bold=True)
F_BIG   = pygame.font.SysFont("arial",     52, bold=True)
F_MED   = pygame.font.SysFont("consolas",  30, bold=True)
F_SM    = pygame.font.SysFont("consolas",  20, bold=True)
F_XSM   = pygame.font.SysFont("consolas",  15)
F_TINY  = pygame.font.SysFont("consolas",  12)

# ── Track geometry ─────────────────────────────────────────────────────────────
TRACK_LEN_M  = 402.0          # 1/4 mile in metres
PX_PER_M     = 3.4            # world pixels per metre
TRACK_LEN_PX = TRACK_LEN_M * PX_PER_M   # ≈ 1367 px
LANE_W       = 110            # width of each lane in pixels
NUM_LANES    = 4              # player + 3 AI cars
ROAD_TOP     = 80             # y-coordinate of road top edge
ROAD_BOT     = ROAD_TOP + NUM_LANES * LANE_W

# ── Physics ────────────────────────────────────────────────────────────────────
MAX_RPM      = 9000
IDLE_RPM     = 800
REDLINE_RPM  = 8500
SHIFT_LIGHT  = 7800           # optimal shift point (RPM)
MAX_GEAR     = 6

# Index 0 is unused (neutral placeholder)
GEAR_RATIOS  = [0.0, 3.5, 2.5, 1.80, 1.35, 1.05, 0.85]
FINAL_DRIVE  = 3.7
WHEEL_CIRC   = 1.9            # metres

ACCEL_BASE   = 55.0           # base m/s² at peak torque, 1st gear
CLUTCH_SLIP  = 0.15           # clutch slip duration after shifting (s)
NITRO_BOOST  = 14.0           # extra m/s² while nitro is active
NITRO_MAX    = 4.0            # total nitro tank (seconds)
NITRO_REGEN  = 0.5
RPM_RISE     = 7000           # RPM rise rate at wide-open throttle
RPM_FALL     = 4500           # RPM fall rate off-throttle / shifting

# ── Car colours ────────────────────────────────────────────────────────────────
CAR_COLOURS = [
    ( 40, 120, 255),   # Lane 0  – player  – electric blue
    (220,  50,  50),   # Lane 1  – AI 1    – crimson red
    (255, 165,   0),   # Lane 2  – AI 2    – amber orange
    ( 50, 200,  80),   # Lane 3  – AI 3    – lime green
]

AI_SKILLS = [0.0, 0.90, 0.98, 1.05]   # index 0 unused (player)
