import pygame
import random
from constants import (
    WORLD_W, PLAYER_SPEED_X, SCROLL_SPEED, ALTITUDE_PX,
    MAX_ALTITUDE, ALTITUDE_CHANGE, MAX_BOMBS, FALL_DURATION,
    BULLET_SPEED, DAMAGE_GUNS, DAMAGE_BOMBS, DAMAGE_FUEL, DAMAGE_MANEUV,
    MAX_HITS, RANKS,
)
from entities import Bullet, Bomb


class Player:
    def __init__(self, start_wx, start_wy):
        self.wx          = float(start_wx)
        self.wy          = float(start_wy)
        self.alt         = 2       # integer altitude level 0-3
        self.alt_f       = 2.0    # smooth float version
        self.bank        = 0      # -1 / 0 / 1 for visual tilt
        self.scroll_spd  = SCROLL_SPEED
        self.fuel        = 100.0
        self.bombs       = MAX_BOMBS
        self.hits        = 0
        self.damage      = {}     # {damage_type: True}
        self.alive       = True
        self.invincible  = 0.0   # seconds of post-hit invincibility
        self.bullets     = []
        self.active_bombs= []
        self.shoot_cd    = 0.0
        self.bomb_cd     = 0.0

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_input(self, keys, dt):
        """Apply player controls; return (fire_pressed, bomb_pressed)."""
        lateral = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: lateral = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: lateral =  1

        if keys[pygame.K_UP]   or keys[pygame.K_w]:
            self.alt_f = min(MAX_ALTITUDE, self.alt_f + ALTITUDE_CHANGE * dt)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.alt_f = max(0.0, self.alt_f - ALTITUDE_CHANGE * dt)

        maneuv = 0.5 if DAMAGE_MANEUV in self.damage else 1.0
        self.wx    += lateral * PLAYER_SPEED_X / 32 * dt * maneuv
        self.wx     = max(1.5, min(WORLD_W - 2.5, self.wx))
        self.bank   = lateral
        self.alt    = int(self.alt_f)

        fire  = keys[pygame.K_SPACE]
        bomb  = keys[pygame.K_LCTRL] or keys[pygame.K_z] or keys[pygame.K_x]
        return fire, bomb

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt, fire, bomb):
        if not self.alive:
            return

        # Advance forward
        self.wy += self.scroll_spd / 32 * dt

        # Fuel drain (leak doubles consumption)
        drain = 2.5 if DAMAGE_FUEL in self.damage else 1.0
        self.fuel = max(0.0, self.fuel - drain * dt)
        if self.fuel <= 0:
            self.alive = False
            return

        # Crash at altitude 0 while flying
        if self.alt_f < 0.05:
            self.alive = False
            return

        self.invincible = max(0.0, self.invincible - dt)

        # Shoot (fire key, not holding bomb key at same time)
        self.shoot_cd = max(0.0, self.shoot_cd - dt)
        if fire and not bomb and self.shoot_cd <= 0:
            self.shoot_cd = 0.10
            spd = BULLET_SPEED / 32
            self.bullets.append(Bullet(self.wx, self.wy, 0.0, spd, friendly=True))

        # Drop bomb
        self.bomb_cd = max(0.0, self.bomb_cd - dt)
        if bomb and self.bombs > 0 and self.bomb_cd <= 0 and not fire:
            self.bomb_cd = 0.4
            self.bombs  -= 1
            self.active_bombs.append(Bomb(self.wx, self.wy, self.alt_f))
            # Slight altitude loss on release
            self.alt_f = max(0.0, self.alt_f - 0.25)

        # Advance bullets; cull when more than 2 tiles behind or 15 ahead of player
        for b in self.bullets:
            b.wy += b.vy * dt
        self.bullets = [b for b in self.bullets
                        if b.alive and self.wy - 2 < b.wy < self.wy + 15]

        # Advance bombs
        for bm in self.active_bombs:
            bm.update(dt)
        self.active_bombs = [bm for bm in self.active_bombs if bm.alive]

    # ------------------------------------------------------------------
    # Damage
    # ------------------------------------------------------------------

    def take_hit(self):
        """Return True if the hit destroyed the plane."""
        if self.invincible > 0:
            return False
        self.hits += 1
        self.invincible = 1.5
        # Assign a damage type not yet applied
        for dtype in [DAMAGE_GUNS, DAMAGE_BOMBS, DAMAGE_FUEL, DAMAGE_MANEUV]:
            if dtype not in self.damage:
                self.damage[dtype] = True
                break
        if self.hits > MAX_HITS:
            self.alive = False
            return True
        return False

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    @property
    def altitude_px(self):
        """Screen pixels above shadow for current fractional altitude."""
        lo = ALTITUDE_PX[int(self.alt_f)]
        hi = ALTITUDE_PX[min(MAX_ALTITUDE, int(self.alt_f) + 1)]
        frac = self.alt_f - int(self.alt_f)
        return int(lo + (hi - lo) * frac)

    def refuel(self):
        """Called on successful landing."""
        self.fuel    = 100.0
        self.bombs   = MAX_BOMBS
        self.damage  = {}
        self.hits    = 0
        self.alt_f   = 1.0
        self.alt     = 1

    @staticmethod
    def rank_for(score):
        for threshold, name in RANKS:
            if score >= threshold:
                return name
        return RANKS[-1][1]
