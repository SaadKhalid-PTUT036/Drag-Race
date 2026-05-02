# -*- coding: utf-8 -*-
"""
dragkings/utils.py
==================
Pure utility / drawing helpers shared across all modules.
No game state — import freely from anywhere.
"""

import pygame


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by factor t (0–1)."""
    return a + (b - a) * t


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp value between lo and hi."""
    return max(lo, min(hi, value))


def alpha_surf(w: int, h: int, colour: tuple, alpha: int) -> pygame.Surface:
    """Return a solid-filled SRCALPHA surface."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((*colour, alpha))
    return s


def draw_rect_alpha(surf: pygame.Surface, colour: tuple,
                    rect: tuple, alpha: int, radius: int = 0) -> None:
    """Draw a rectangle with per-call alpha onto surf."""
    s = pygame.Surface((int(rect[2]), int(rect[3])), pygame.SRCALPHA)
    pygame.draw.rect(s, (*colour, alpha),
                     (0, 0, int(rect[2]), int(rect[3])),
                     border_radius=radius)
    surf.blit(s, (rect[0], rect[1]))


def draw_glow_circle(surf: pygame.Surface, colour: tuple,
                     cx: int, cy: int, radius: int, alpha: int = 60) -> None:
    """Draw a soft circular glow centred at (cx, cy)."""
    for r in range(radius, 0, -max(1, radius // 8)):
        a = int(alpha * (r / radius) ** 0.5)
        draw_rect_alpha(surf, colour,
                        (cx - r, cy - r, r * 2, r * 2), a, radius=r)


def fmt_time(t) -> str:
    """Format a race time float as a string, or '--:--.--' if None."""
    if t is None:
        return "--:--.--"
    return f"{t:.3f}s"


def render_shadowed(font: pygame.font.Font, text: str,
                    colour: tuple, shadow: tuple = (0, 0, 0),
                    offset: int = 3) -> pygame.Surface:
    """Render text with a drop-shadow and return a surface sized to fit both."""
    base   = font.render(text, True, colour)
    shad   = font.render(text, True, shadow)
    w      = base.get_width()  + offset
    h      = base.get_height() + offset
    canvas = pygame.Surface((w, h), pygame.SRCALPHA)
    canvas.blit(shad, (offset, offset))
    canvas.blit(base, (0, 0))
    return canvas


def render_glow(font: pygame.font.Font, text: str,
                colour: tuple, glow_colour: tuple,
                glow_alpha: int = 90) -> pygame.Surface:
    """Render text with a coloured glow layer underneath."""
    base  = font.render(text, True, colour)
    glow  = font.render(text, True, glow_colour)
    pad   = 8
    w, h  = base.get_width() + pad * 2, base.get_height() + pad * 2
    canvas = pygame.Surface((w, h), pygame.SRCALPHA)
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-2, -1, 0, 1, 2):
            g = glow.copy()
            g.set_alpha(glow_alpha)
            canvas.blit(g, (pad + dx, pad + dy))
    canvas.blit(base, (pad, pad))
    return canvas
