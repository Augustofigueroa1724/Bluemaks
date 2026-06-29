import math
import random
from constants import (
    WORLD_W, BULLET_SPEED, ENEMY_SPEED, ENEMY_SPAWN_AHEAD, SCORE_PLANE,
    FALL_DURATION,
)


class Bullet:
    def __init__(self, wx, wy, vx, vy, friendly=True):
        self.wx       = wx
        self.wy       = wy
        self.vx       = vx
        self.vy       = vy
        self.friendly = friendly
        self.alive    = True


class Bomb:
    """
    A released bomb fixed at its drop world-position; altitude falls to 0.
    The shadow at (wx, wy) on the ground shows where it will land.
    """

    def __init__(self, wx, wy, altitude):
        self.wx           = wx
        self.wy           = wy
        self.drop_alt     = altitude
        self.vis_alt      = altitude   # float, falls toward 0
        # Use FALL_DURATION table so higher altitude = longer hang time
        alt_idx = min(3, max(1, round(altitude)))
        fall_dur = FALL_DURATION[alt_idx] if altitude >= 0.5 else 0.3
        self.fall_speed   = altitude / fall_dur if altitude > 0 else 1.0
        self.alive        = True
        self.exploding    = False
        self.explode_t    = 0.0
        self.explode_r    = 0.0  # explosion radius for drawing

    @property
    def landed(self):
        return self.vis_alt <= 0

    def update(self, dt):
        if self.exploding:
            self.explode_t += dt
            self.explode_r  = min(18, self.explode_r + 60 * dt)
            if self.explode_t > 0.45:
                self.alive = False
        elif not self.landed:
            self.vis_alt -= self.fall_speed * dt
            if self.vis_alt < 0:
                self.vis_alt = 0


class EnemyPlane:
    """
    Basic enemy biplane: spawns ahead, flies toward player, shoots periodically.
    """

    def __init__(self, wx, wy):
        self.wx         = wx
        self.wy         = wy
        self.alive      = True
        self.hp         = 1
        self.score      = SCORE_PLANE
        self.shoot_cd   = random.uniform(1.0, 2.5)
        self.bullets    = []
        self.anim       = 0.0   # explosion anim timer
        self.bank       = 0     # -1 left, 0, 1 right

    def update(self, player_wx, player_wy, fire_rate_mult, dt):
        if not self.alive:
            self.anim += dt
            return

        # Simple intercept: fly directly toward player
        dx = player_wx - self.wx
        dy = player_wy - self.wy
        dist = math.hypot(dx, dy)
        if dist > 0.1:
            nx = dx / dist
            ny = dy / dist
            self.wx += nx * ENEMY_SPEED / 32 * dt
            self.wy += ny * ENEMY_SPEED / 32 * dt
            self.bank = -1 if dx < -0.3 else (1 if dx > 0.3 else 0)

        # Shoot at player when reasonably close
        self.shoot_cd -= dt * fire_rate_mult
        if self.shoot_cd <= 0 and dist < 18:
            self.shoot_cd = random.uniform(1.2, 2.8) / fire_rate_mult
            if dist > 0.1:
                spd = BULLET_SPEED / 32
                self.bullets.append(Bullet(self.wx, self.wy, nx * spd, ny * spd, friendly=False))

        # Update own bullets
        for b in self.bullets:
            b.wx += b.vx * dt
            b.wy += b.vy * dt

        self.bullets = [b for b in self.bullets if b.alive]

    def take_hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False
            return True
        return False
