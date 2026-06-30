"""
Handles all drawing: isometric terrain, ground targets, player,
enemy planes, bullets, bombs, and explosions.
"""

import pygame
import math
from constants import (
    SCREEN_W, GAME_H, ISO_X, ISO_Y,
    TERRAIN_COLORS, TERRAIN_EDGE_COLORS,
    BLACK, WHITE, GRAY, DARK_GRAY, LIGHT_GRAY,
    RED, LIGHT_RED, BROWN, ORANGE, YELLOW, GREEN, DARK_GREEN,
    BLUE, LIGHT_BLUE, CYAN, TAN, SAND,
    ALTITUDE_PX, MAX_ALTITUDE,
)
from camera import tile_corners

# Visible tile render range from camera centre
VIS_X = 18
VIS_Y = 28


# -----------------------------------------------------------------------
# Low-level tile drawing
# -----------------------------------------------------------------------

def draw_tile(surface, sx, sy, terrain_type, clip_rect=None):
    """Draw one isometric tile whose left vertex is at (sx, sy)."""
    pts = tile_corners(sx, sy)
    # Quick cull: skip tiles completely off the game viewport
    min_x = min(p[0] for p in pts)
    max_x = max(p[0] for p in pts)
    min_y = min(p[1] for p in pts)
    max_y = max(p[1] for p in pts)
    if max_x < 0 or min_x > SCREEN_W or max_y < 0 or min_y > GAME_H:
        return

    fill  = TERRAIN_COLORS.get(terrain_type, (34, 120, 34))
    edge  = TERRAIN_EDGE_COLORS.get(terrain_type, (20, 80, 20))
    pygame.draw.polygon(surface, fill, pts)
    pygame.draw.polygon(surface, edge, pts, 1)


# -----------------------------------------------------------------------
# World terrain
# -----------------------------------------------------------------------

def render_terrain(surface, world, camera):
    """
    Render all visible tiles back-to-front (painter's algorithm).
    Render order: descending wy (far first), ascending wx (left first).
    """
    cam_wx = int(camera.wx)
    cam_wy = int(camera.wy)

    for dwy in range(VIS_Y, -VIS_Y - 1, -1):
        wy = cam_wy + dwy
        if wy < 0 or wy >= world.length:
            continue
        for dwx in range(-VIS_X, VIS_X + 1):
            wx = cam_wx + dwx
            if wx < 0 or wx >= world.width:
                continue
            sx, sy = camera.w2s(wx, wy)
            draw_tile(surface, sx, sy, world.terrain[wy][wx])


# -----------------------------------------------------------------------
# Target sprites (ground entities)
# -----------------------------------------------------------------------

_TARGET_DRAW = {}   # populated below


def _draw_tank(surface, sx, sy):
    # Body
    pygame.draw.polygon(surface, (80, 70, 40), [
        (sx - 4, sy), (sx, sy - 4), (sx + 8, sy - 2),
        (sx + 4, sy + 4), (sx, sy + 3)
    ])
    # Turret
    pygame.draw.circle(surface, (60, 55, 30), (sx + 2, sy - 1), 3)
    # Barrel
    pygame.draw.line(surface, DARK_GRAY, (sx + 2, sy - 1), (sx + 10, sy - 5), 2)


def _draw_ship(surface, sx, sy):
    # Hull (elongated iso-diamond)
    pygame.draw.polygon(surface, (50, 50, 100), [
        (sx - 2, sy + 2), (sx + 6, sy - 4),
        (sx + 14, sy - 2), (sx + 8, sy + 4)
    ])
    # Superstructure
    pygame.draw.rect(surface, GRAY, (sx + 4, sy - 5, 5, 4))
    # Mast
    pygame.draw.line(surface, DARK_GRAY, (sx + 6, sy - 5), (sx + 6, sy - 12), 1)


def _draw_bridge(surface, sx, sy):
    pygame.draw.polygon(surface, (110, 95, 70), [
        (sx, sy), (sx + ISO_X, sy + ISO_Y),
        (sx + 2*ISO_X, sy), (sx + ISO_X, sy - ISO_Y)
    ])
    # Girder lines across
    for i in range(1, 4):
        x0 = sx + i * ISO_X // 2
        y0 = sy - i * ISO_Y // 4
        pygame.draw.line(surface, (80, 70, 50), (x0 - 4, y0 + 2), (x0 + 4, y0 - 2), 1)


def _draw_building(surface, sx, sy):
    # Ground floor
    pygame.draw.polygon(surface, (140, 95, 70), [
        (sx - 2, sy + 1), (sx + 3, sy - 3),
        (sx + 9, sy - 1), (sx + 4, sy + 3)
    ])
    # Roof
    pygame.draw.polygon(surface, (170, 120, 90), [
        (sx - 2, sy - 3), (sx + 3, sy - 7),
        (sx + 9, sy - 5), (sx + 4, sy - 1)
    ])
    pygame.draw.polygon(surface, (100, 70, 50), [
        (sx - 2, sy + 1), (sx - 2, sy - 3),
        (sx + 4, sy - 1), (sx + 4, sy + 3)
    ])


def _draw_flak(surface, sx, sy):
    pygame.draw.circle(surface, (60, 60, 60), (sx + 4, sy), 4)
    # Gun barrel pointing northeast
    pygame.draw.line(surface, DARK_GRAY, (sx + 4, sy), (sx + 10, sy - 5), 2)


TARGET_DRAW_FN = {
    "tank":     _draw_tank,
    "ship":     _draw_ship,
    "bridge":   _draw_bridge,
    "building": _draw_building,
    "flak":     _draw_flak,
}


def render_targets(surface, world, camera):
    for t in world.targets:
        if not t.alive:
            if t.anim > 0:
                _draw_explosion(surface, *camera.w2s(t.wx, t.wy), t.anim, 14)
            continue
        sx, sy = camera.w2s(t.wx, t.wy)
        # Cull off-screen
        if sx < -40 or sx > SCREEN_W + 40 or sy < -40 or sy > GAME_H + 40:
            continue
        fn = TARGET_DRAW_FN.get(t.kind)
        if fn:
            fn(surface, sx, sy)


# -----------------------------------------------------------------------
# Explosion helper
# -----------------------------------------------------------------------

def _draw_explosion(surface, sx, sy, anim, max_r):
    """anim: time since destruction (seconds). Vivid orange-yellow fireball."""
    life = min(1.0, anim / 0.5)        # 0→1 over half a second
    r = int(max_r * min(1.0, life * 4))  # quickly expands to max_r
    if r < 1:
        return
    # Stays bright for the first 60% of lifetime, then fades
    alpha = 255 if life < 0.6 else max(0, int(255 * (1.0 - (life - 0.6) / 0.4)))
    tmp = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
    c = r + 2
    pygame.draw.circle(tmp, (*RED,    alpha),            (c, c), r)
    pygame.draw.circle(tmp, (*ORANGE, min(255, alpha + 40)), (c, c), max(1, r - 3))
    pygame.draw.circle(tmp, (*YELLOW, min(255, alpha + 80)), (c, c), max(1, r - 7))
    surface.blit(tmp, (sx - c, sy - c))


# -----------------------------------------------------------------------
# Player plane sprite
# -----------------------------------------------------------------------

def render_player(surface, player, camera):
    # Shadow at ground level
    gx, gy = camera.w2s(player.wx, player.wy)
    _draw_shadow(surface, gx, gy, player.alt_f)

    # Plane at altitude height (above shadow)
    px = gx
    py = gy - player.altitude_px

    # Blink during invincibility
    if player.invincible > 0 and int(player.invincible * 10) % 2 == 0:
        return

    _draw_biplane(surface, px, py, player.bank)


def _draw_shadow(surface, gx, gy, alt):
    """Oval shadow below plane — grows fainter/smaller at high altitude."""
    alpha  = max(40, 180 - int(alt * 40))
    rw = max(8, 18 - int(alt * 3))
    rh = max(4, 10 - int(alt * 2))
    tmp = pygame.Surface((rw * 2 + 2, rh * 2 + 2), pygame.SRCALPHA)
    pygame.draw.ellipse(tmp, (0, 0, 0, alpha), (0, 0, rw * 2, rh * 2))
    surface.blit(tmp, (gx - rw, gy - rh))


def _draw_biplane(surface, px, py, bank):
    """
    WWI Sopwith Camel sprite (~2x original size), viewed isometrically.
    bank: -1 = banking left, 0 = level, 1 = banking right.
    """
    col_body = (110, 80,  40)   # khaki fuselage
    col_wing = (170, 148, 90)   # lighter wing fabric
    col_dark = (70,  50,  20)   # struts / dark detail
    col_prop = (60,  50,  40)   # propeller

    # Fuselage: elongated northeast-pointing shape
    pts_fuse = [
        (px - 4,  py + 7),   # tail
        (px + 0,  py + 1),   # mid-rear
        (px + 10, py - 7),   # nose
        (px + 8,  py - 6),
        (px + 2,  py - 1),
        (px - 5,  py + 5),
    ]
    pygame.draw.polygon(surface, col_body, pts_fuse)
    # Cockpit highlight
    pygame.draw.polygon(surface, (130, 100, 55), [
        (px + 1, py + 0), (px + 4, py - 3), (px + 6, py - 5), (px + 3, py - 2)
    ])

    # Upper wing (main lift surface, tapered by banking)
    wl = -10 if bank >= 0 else -16
    wr =  22 if bank <= 0 else  14
    pygame.draw.polygon(surface, col_wing, [
        (px + wl, py - 1),
        (px + wl, py - 4),
        (px + wr, py - 8),
        (px + wr, py - 5),
    ])
    # Wing stripes for definition
    pygame.draw.line(surface, col_dark, (px + wl, py - 2), (px + wr, py - 6), 1)

    # Lower wing (shorter, below fuselage)
    wl2 = -7  if bank >= 0 else -12
    wr2 =  17 if bank <= 0 else  10
    pygame.draw.polygon(surface, col_wing, [
        (px + wl2, py + 3),
        (px + wl2, py + 1),
        (px + wr2, py - 3),
        (px + wr2, py - 1),
    ])

    # Vertical inter-plane struts
    pygame.draw.line(surface, col_dark, (px + 0,  py + 1),  (px + 0,  py - 2),  2)
    pygame.draw.line(surface, col_dark, (px + 8,  py - 5),  (px + 8,  py - 8),  2)
    pygame.draw.line(surface, col_dark, (px + 14, py - 6),  (px + 14, py - 8),  1)

    # Tail fin
    pygame.draw.polygon(surface, col_body, [
        (px - 4, py + 7), (px - 7, py + 4), (px - 2, py + 2)
    ])
    # Horizontal stabiliser
    pygame.draw.line(surface, col_dark, (px - 5, py + 6), (px + 1, py + 1), 2)

    # Propeller (two-blade, vertical)
    pygame.draw.line(surface, col_prop, (px + 11, py - 11), (px + 11, py - 3), 3)
    pygame.draw.line(surface, (90, 75, 55), (px + 11, py - 7), (px + 13, py - 7), 2)


# -----------------------------------------------------------------------
# Enemy planes
# -----------------------------------------------------------------------

def render_enemies(surface, enemies, camera):
    for e in enemies:
        if not e.alive:
            sx, sy = camera.w2s(e.wx, e.wy)
            _draw_explosion(surface, sx, sy, e.anim, 18)
            continue
        sx, sy = camera.w2s(e.wx, e.wy)
        if sx < -40 or sx > SCREEN_W + 40 or sy < -40 or sy > GAME_H + 40:
            continue
        _draw_enemy_plane(surface, sx, sy, e.bank)


def _draw_enemy_plane(surface, px, py, bank):
    """German enemy biplane (Fokker-style) — dark green, flying toward player."""
    col_body = (35, 75,  35)
    col_wing = (50, 105, 55)
    col_dark = (25, 50,  25)

    # Fuselage (mirrored: nose points southwest = toward player)
    pygame.draw.polygon(surface, col_body, [
        (px + 4,  py + 7),   # tail
        (px + 0,  py + 1),
        (px - 10, py - 7),   # nose
        (px - 8,  py - 6),
        (px - 2,  py - 1),
        (px + 5,  py + 5),
    ])

    # Upper wing
    wl = -20 if bank >= 0 else -12
    wr =  8  if bank <= 0 else  14
    pygame.draw.polygon(surface, col_wing, [
        (px + wr, py + 1),
        (px + wr, py - 2),
        (px + wl, py - 6),
        (px + wl, py - 3),
    ])
    pygame.draw.line(surface, col_dark, (px + wl, py - 4), (px + wr, py - 1), 1)

    # Lower wing (shorter)
    wl2 = -14 if bank >= 0 else -8
    wr2 =  5  if bank <= 0 else  10
    pygame.draw.polygon(surface, col_wing, [
        (px + wr2, py + 4),
        (px + wr2, py + 2),
        (px + wl2, py - 1),
        (px + wl2, py + 1),
    ])

    # Iron cross marking
    pygame.draw.line(surface, (160, 160, 160), (px - 3, py - 2), (px - 7, py - 4), 2)

    # Propeller
    pygame.draw.line(surface, col_dark, (px - 11, py - 10), (px - 11, py - 3), 3)


# -----------------------------------------------------------------------
# Bullets and bombs
# -----------------------------------------------------------------------

def render_bullets(surface, player, enemies, camera):
    # Player bullets
    for b in player.bullets:
        sx, sy = camera.w2s(b.wx, b.wy)
        pygame.draw.circle(surface, YELLOW, (sx, sy - 4), 2)

    # Enemy bullets
    for e in enemies:
        for b in e.bullets:
            sx, sy = camera.w2s(b.wx, b.wy)
            pygame.draw.circle(surface, LIGHT_RED, (sx, sy - 4), 2)


def render_bombs(surface, player, camera):
    for bm in player.active_bombs:
        # Ground shadow (landing spot)
        gx, gy = camera.w2s(bm.wx, bm.wy)
        pygame.draw.ellipse(surface, (30, 30, 30), (gx - 4, gy - 2, 8, 4))

        if bm.exploding:
            _draw_explosion(surface, gx, gy, bm.explode_t, 20)
        else:
            # Bomb sprite at current falling altitude
            alt_px = int(bm.vis_alt / max(0.01, bm.drop_alt) * ALTITUDE_PX[min(3, int(bm.drop_alt + 0.5))])
            bsx = gx
            bsy = gy - alt_px
            pygame.draw.polygon(surface, DARK_GRAY, [
                (bsx, bsy - 4), (bsx + 2, bsy), (bsx, bsy + 2), (bsx - 2, bsy)
            ])
