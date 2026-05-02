# -*- coding: utf-8 -*-
"""
DRAG KINGS — Quarter Mile Challenge
====================================
Entry point.  All game logic lives in the dragkings/ package.

Controls
--------
SPACE / UP / W  — Throttle (hold to accelerate)
SHIFT           — Shift up a gear
CTRL            — Nitro boost
R               — Restart race
ESC             — Quit to menu
"""

from dragkings.game import Game

if __name__ == "__main__":
    Game().run()
