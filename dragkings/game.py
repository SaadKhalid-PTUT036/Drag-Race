# -*- coding: utf-8 -*-
"""
dragkings/game.py
=================
Game – main game loop encapsulated in a class.

State machine:
  MENU     → player clicks Start → STAGING
  STAGING  → Christmas Tree goes green → RACE
  RACE     → all cars finish → RESULTS
  RESULTS  → player clicks Restart → STAGING | Menu → MENU
"""

import pygame
import random
import sys

from dragkings.constants import (
    screen, clock, FPS,
    SW, SH,
    NUM_LANES, CAR_COLOURS, AI_SKILLS,
    C_BG, C_RED, C_DIM,
    F_MED, F_BIG,
    SHIFT_LIGHT,
)
from dragkings.utils  import lerp
from dragkings.particles    import Particles
from dragkings.car          import Car
from dragkings.track        import draw_track
from dragkings.hud          import HUD
from dragkings.christmas_tree import ChristmasTree
from dragkings.touch        import TouchInterface
from dragkings.screens.menu    import MenuScreen
from dragkings.screens.results import ResultsScreen


# ── State constants ────────────────────────────────────────────────────────────
STATE_MENU    = 0
STATE_STAGING = 1
STATE_RACE    = 2
STATE_RESULTS = 3


class Game:
    """Owns the main loop. Call Game().run() to start."""

    def __init__(self):
        # Persistent UI objects (survive across races)
        self._menu    = MenuScreen()
        self._results = ResultsScreen()
        self._hud     = HUD()
        self._touch   = TouchInterface()

        # Race-specific state (reset each new race)
        self._player: Car      = None
        self._cars:   list[Car] = []
        self._particles = Particles()
        self._tree      = ChristmasTree()

        self._state      = STATE_MENU
        self._race_time  = 0.0
        self._cam_x      = 0.0
        self._notif_text = ""
        self._notif_timer = 0.0

        # Edge-detect for SHIFT key
        self._prev_shift = False

        self._new_race()

    # ── Race factory ──────────────────────────────────────────────────────────

    def _new_race(self) -> None:
        self._player = Car(lane=0, colour=CAR_COLOURS[0], is_player=True)
        self._cars   = [self._player]
        for i in range(1, NUM_LANES):
            self._cars.append(Car(lane=i, colour=CAR_COLOURS[i],
                                  is_player=False, ai_skill=AI_SKILLS[i]))
        self._particles  = Particles()
        self._tree       = ChristmasTree()
        self._race_time  = 0.0
        self._cam_x      = 0.0
        self._notif_text = ""
        self._notif_timer = 0.0
        self._prev_shift = False

    def _show_notif(self, text: str, dur: float = 2.0) -> None:
        self._notif_text  = text
        self._notif_timer = dur

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        while True:
            dt = min(clock.tick(FPS) / 1000.0, 0.05)

            events = pygame.event.get()
            self._touch.process_events(events)

            self._handle_events(events)
            self._update(dt)
            self._draw()

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_events(self, events: list) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ── Menu ──────────────────────────────────────────────────────────
            if self._state == STATE_MENU:
                r = self._menu.handle(event)
                if r == 'start':
                    self._start_race()
                elif r == 'quit':
                    pygame.quit()
                    sys.exit()

            # ── Staging ───────────────────────────────────────────────────────
            elif self._state == STATE_STAGING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._state = STATE_MENU
                    if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                        if not self._tree.green:
                            self._tree.false_start = True
                            self._show_notif("FALSE START!  -0.3s penalty", 3.0)

            # ── Race ──────────────────────────────────────────────────────────
            elif self._state == STATE_RACE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._state = STATE_MENU
                    if event.key == pygame.K_r:
                        self._start_race()

            # ── Results ───────────────────────────────────────────────────────
            elif self._state == STATE_RESULTS:
                r = self._results.handle(event)
                if r == 'menu':
                    self._state = STATE_MENU
                elif r == 'restart':
                    self._start_race()

    def _start_race(self) -> None:
        self._new_race()
        self._state = STATE_STAGING
        self._tree.start()

    # ── Update ────────────────────────────────────────────────────────────────

    def _update(self, dt: float) -> None:
        state = self._state

        if state == STATE_MENU:
            self._menu.update(dt)

        elif state == STATE_STAGING:
            self._tree.update(dt)

            # Transition to RACE when green
            if self._tree.green:
                self._state = STATE_RACE
                self._player.reaction_time = 0.0

            # False-start detection via touch/keyboard hold
            keys        = pygame.key.get_pressed()
            kb_throttle = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
            if (self._touch.throttle_held or kb_throttle) \
               and not self._tree.green \
               and not self._tree.false_start:
                self._tree.false_start = True
                self._show_notif("FALSE START!  -0.3s penalty", 3.0)

        elif state == STATE_RACE:
            self._update_race(dt)

        elif state == STATE_RESULTS:
            self._results.update(dt)

    def _update_race(self, dt: float) -> None:
        self._race_time  += dt
        self._notif_timer = max(0.0, self._notif_timer - dt)

        keys        = pygame.key.get_pressed()
        kb_throttle = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        throttle    = 1.0 if (kb_throttle or self._touch.throttle_held) else 0.0

        mods      = pygame.key.get_mods()
        nitro_key = bool(mods & pygame.KMOD_CTRL) or self._touch.nitro_held

        # Reaction time: first frame player presses throttle
        if self._player.reaction_time == 0.0 and throttle > 0.5:
            self._player.reaction_time = self._race_time

        # Gear-shift (edge-detect SHIFT key)
        cur_shift        = bool(mods & pygame.KMOD_SHIFT)
        shift_up         = self._touch.shift_tapped or (cur_shift and not self._prev_shift)
        self._prev_shift = cur_shift

        # Player
        self._player.update(dt, throttle, shift_up, False,
                             nitro_key, self._race_time, self._particles)

        # AI cars
        for ai in self._cars[1:]:
            ai._ai_shift_t += dt
            ai_shift = False
            if ai.rpm >= int(SHIFT_LIGHT * ai.ai_skill):
                if ai._ai_shift_t >= ai._ai_shift_delay:
                    ai_shift           = True
                    ai._ai_shift_t     = 0.0
                    ai._ai_shift_delay = random.uniform(0.0, 0.1)

            ai._ai_nitro_t -= dt
            ai_nitro = False
            if ai._ai_nitro_t <= 0 and ai.nitro > 1.0:
                ai_nitro       = True
                ai._ai_nitro_t = random.uniform(2.0, 5.0)

            ai.update(dt, 1.0, ai_shift, False,
                      ai_nitro, self._race_time, self._particles)

        # Smooth camera tracking player
        target_cam  = self._player.dist_px - 200
        self._cam_x = lerp(self._cam_x, max(0.0, target_cam),
                           min(1.0, dt * 6))

        self._particles.update(dt)

        # Check if all cars have finished
        if all(c.finished for c in self._cars):
            self._state      = STATE_RESULTS
            self._results._t = 0.0
            self._results._conf_done = False

    # ── Draw ──────────────────────────────────────────────────────────────────

    def _draw(self) -> None:
        screen.fill(C_BG)

        if self._state == STATE_MENU:
            self._menu.draw(screen)

        elif self._state in (STATE_STAGING, STATE_RACE):
            draw_track(screen, self._cam_x, NUM_LANES)
            self._particles.draw(screen, self._cam_x)
            for car in self._cars:
                car.draw(screen, self._cam_x)

            self._tree.draw(screen)

            if self._state == STATE_STAGING:
                wait_t = F_MED.render(
                    "Hold THROTTLE when lights go GREEN!", True, C_DIM)
                screen.blit(wait_t,
                            (SW // 2 - wait_t.get_width() // 2, SH - 80))

            if self._state == STATE_RACE:
                self._hud.draw(screen, self._player, self._race_time, self._cars)

            self._touch.draw_hud(screen, self._state)

            # Notification banner
            if self._notif_timer > 0:
                alpha = int(255 * min(1.0, self._notif_timer))
                ns    = F_BIG.render(self._notif_text, True, C_RED)
                ns.set_alpha(alpha)
                screen.blit(ns, (SW // 2 - ns.get_width() // 2, SH // 2 - 40))

        elif self._state == STATE_RESULTS:
            self._results.draw(screen, self._cars, self._player)

        pygame.display.flip()
