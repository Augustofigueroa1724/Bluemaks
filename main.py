"""
Blue Max — Pygame Recreation
WWI biplane shooter with diagonal-scrolling isometric view.
Based on the Commodore 64 original by Bob Polin / Synapse Software (1983).

Controls:
  Arrow keys / WASD  — move left/right, climb/dive
  SPACE              — fire machine gun
  LCTRL / Z / X     — drop bomb
  ESC                — quit / back to menu
"""

import sys
import math
import random
import pygame

from constants import (
    SCREEN_W, SCREEN_H, GAME_H, FPS, TITLE,
    WORLD_W, WORLD_LEN, AIRSTRIP_Y,
    S_MENU, S_FLYING, S_LANDING, S_GAMEOVER,
    DIFFICULTIES, DIFF_SETTINGS, SCORE_PLANE,
    BLACK, WHITE, GRAY, DARK_GRAY, LIGHT_GRAY,
    RED, LIGHT_RED, YELLOW, GREEN, ORANGE, BLUE, LIGHT_BLUE, CYAN,
    ENEMY_SPAWN_AHEAD, DAMAGE_GUNS, DAMAGE_BOMBS,
)
from camera   import Camera
from world    import World
from player   import Player
from entities import EnemyPlane
from renderer import (
    render_terrain, render_targets, render_player,
    render_enemies, render_bullets, render_bombs,
)
from hud import HUD


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Game class
# ---------------------------------------------------------------------------

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen  = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock   = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("Courier New,monospace", 32, bold=True)
        self.font_md = pygame.font.SysFont("Courier New,monospace", 20, bold=True)
        self.font_sm = pygame.font.SysFont("Courier New,monospace", 14)

        self.state      = S_MENU
        self.diff_idx   = 1          # 0=Easy 1=Normal 2=Hard
        self.score      = 0
        self.world      = None
        self.player     = None
        self.camera     = None
        self.hud        = HUD()
        self.enemies    = []
        self.enemy_cd   = 0.0       # cooldown before next enemy spawn
        self.land_timer   = 0.0     # used in landing sequence
        self.land_phase   = 0       # 0=approach 1=touchdown 2=refuel
        self.landed_once  = False   # prevents re-triggering after refuel
        self.gameover_t   = 0.0

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)   # cap delta so pausing doesn't blow things up

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self._handle_event(event)

            self._update(dt)
            self._draw()
            pygame.display.flip()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def _handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        k = event.key

        if self.state == S_MENU:
            if k in (pygame.K_LEFT, pygame.K_a):
                self.diff_idx = (self.diff_idx - 1) % len(DIFFICULTIES)
            if k in (pygame.K_RIGHT, pygame.K_d):
                self.diff_idx = (self.diff_idx + 1) % len(DIFFICULTIES)
            if k in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_game()

        elif self.state in (S_FLYING, S_LANDING):
            if k == pygame.K_ESCAPE:
                self.state = S_MENU

        elif self.state == S_GAMEOVER:
            if k in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.state = S_MENU

    # ------------------------------------------------------------------
    # State initialisation
    # ------------------------------------------------------------------

    def _start_game(self):
        self.score       = 0
        self.landed_once = False
        self.world    = World(seed=random.randint(0, 99999))
        self.player   = Player(WORLD_W / 2, 5.0)
        self.camera   = Camera()
        self.enemies  = []
        self.enemy_cd = 2.0
        self.state    = S_FLYING

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def _update(self, dt):
        self.hud.update(dt)

        if self.state == S_FLYING:
            self._update_flying(dt)
        elif self.state == S_LANDING:
            self._update_landing(dt)
        elif self.state == S_GAMEOVER:
            self.gameover_t += dt

    def _update_flying(self, dt):
        keys  = pygame.key.get_pressed()
        fire, bomb = self.player.handle_input(keys, dt)
        self.player.update(dt, fire, bomb)

        if not self.player.alive:
            self._trigger_gameover()
            return

        self.camera.follow(self.player.wx, self.player.wy)

        diff  = DIFF_SETTINGS[DIFFICULTIES[self.diff_idx]]
        self._update_enemies(dt, diff)
        self._check_bullet_hits(diff)
        self._check_bomb_hits()
        self._update_target_anims(dt)
        self._check_enemy_bullet_hits()

        # Trigger landing sequence when player first nears airstrip
        if not self.landed_once and self.player.wy >= AIRSTRIP_Y - 5:
            self.land_timer = 0.0
            self.land_phase = 0
            self.state = S_LANDING

    def _update_landing(self, dt):
        keys = pygame.key.get_pressed()
        self.land_timer += dt

        if self.land_phase == 0:
            # Approach: player must descend and slow down
            fire, bomb = self.player.handle_input(keys, dt)
            self.player.update(dt, False, False)
            self.camera.follow(self.player.wx, self.player.wy)

            # Check if player is over airstrip at low altitude
            on_strip = self.world.is_airstrip(self.player.wx, self.player.wy)
            if on_strip and self.player.alt_f <= 0.4:
                self.land_phase = 1
                self.land_timer = 0.0
            elif self.land_timer > 15.0:
                # Missed the runway — crash
                self.player.alive = False
                self._trigger_gameover()

        elif self.land_phase == 1:
            # Touchdown: slow to stop
            self.player.scroll_spd = max(0.0, self.player.scroll_spd - 40 * dt)
            self.player.alt_f      = max(0.0, self.player.alt_f - 2 * dt)
            self.camera.follow(self.player.wx, self.player.wy)
            if self.land_timer > 2.0:
                self.land_phase = 2
                self.land_timer = 0.0

        elif self.land_phase == 2:
            # Refuel / repair screen
            if self.land_timer > 3.0:
                self.player.refuel()
                self.player.scroll_spd = 70.0
                self.landed_once = True
                self.player.wy   = AIRSTRIP_Y + 20
                self.state       = S_FLYING

    def _update_enemies(self, dt, diff):
        fire_rate  = diff["fire_rate"]
        spawn_rate = diff["spawn_rate"]

        # Advance existing enemies
        for e in self.enemies:
            e.update(self.player.wx, self.player.wy, fire_rate, dt)

        # Cull dead (explosion finished) and far-behind enemies
        self.enemies = [
            e for e in self.enemies
            if e.alive or e.anim < 0.6
        ]
        self.enemies = [
            e for e in self.enemies
            if e.wy > self.player.wy - 30
        ]

        # Spawn new enemies ahead of player
        self.enemy_cd -= dt * spawn_rate
        if self.enemy_cd <= 0 and self.player.wy < AIRSTRIP_Y - 20:
            self.enemy_cd = random.uniform(5, 12) / spawn_rate
            ex = self.player.wx + random.uniform(-8, 8)
            ey = self.player.wy + ENEMY_SPAWN_AHEAD + random.uniform(-5, 5)
            ex = clamp(ex, 2, WORLD_W - 3)
            self.enemies.append(EnemyPlane(ex, ey))

    def _check_bullet_hits(self, diff):
        """Player bullets hitting ground targets and enemies."""
        for b in self.player.bullets[:]:
            # vs enemies
            for e in self.enemies:
                if not e.alive:
                    continue
                if abs(b.wx - e.wx) < 1.2 and abs(b.wy - e.wy) < 1.2:
                    b.alive = False
                    if e.take_hit():
                        self.score += e.score
                    break
            # vs ground targets (only effective at low altitude for strafing)
            if self.player.alt <= 1:
                for t in self.world.targets:
                    if not t.alive:
                        continue
                    if abs(b.wx - t.wx) < 1.0 and abs(b.wy - t.wy) < 1.0:
                        b.alive = False
                        t.hp -= 1
                        if t.hp <= 0:
                            t.alive = False
                            self.score += t.score
                        break

    def _check_bomb_hits(self):
        """Bombs landing and checking targets within blast radius."""
        for bm in self.player.active_bombs:
            if bm.landed and not bm.exploding:
                bm.exploding = True
                for t in self.world.living_targets_near(bm.wx, bm.wy, radius=1.8):
                    t.alive = False
                    self.score += t.score

    def _check_enemy_bullet_hits(self):
        """Enemy bullets hitting the player."""
        for e in self.enemies:
            for b in e.bullets[:]:
                if abs(b.wx - self.player.wx) < 1.0 and abs(b.wy - self.player.wy) < 1.5:
                    b.alive = False
                    destroyed = self.player.take_hit()
                    if destroyed:
                        self._trigger_gameover()
                        return

    def _update_target_anims(self, dt):
        for t in self.world.targets:
            if not t.alive:
                t.anim += dt

    def _trigger_gameover(self):
        self.gameover_t = 0.0
        self.state      = S_GAMEOVER

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def _draw(self):
        self.screen.fill((74, 143, 209))  # sky blue

        if self.state == S_MENU:
            self._draw_menu()
        elif self.state in (S_FLYING, S_LANDING):
            self._draw_game()
        elif self.state == S_GAMEOVER:
            self._draw_gameover()

    def _draw_game(self):
        # Clip drawing to game viewport (above HUD)
        clip = pygame.Rect(0, 0, SCREEN_W, GAME_H)
        self.screen.set_clip(clip)

        render_terrain(self.screen, self.world, self.camera)
        render_targets(self.screen, self.world, self.camera)
        render_bombs(self.screen, self.player, self.camera)
        render_bullets(self.screen, self.player, self.enemies, self.camera)
        render_enemies(self.screen, self.enemies, self.camera)
        render_player(self.screen, self.player, self.camera)

        # Landing overlay
        if self.state == S_LANDING:
            self._draw_landing_overlay()

        self.screen.set_clip(None)

        # Status msg
        status = self._status_message()
        self.hud.draw(self.screen, self.player, self.score,
                      DIFFICULTIES[self.diff_idx], status)

    def _status_message(self):
        if self.state == S_LANDING:
            if self.land_phase == 0:
                return "LAND NOW"
            if self.land_phase == 1:
                return "TOUCHDOWN"
            return "REFUELLING..."
        if self.player.fuel < 20:
            return "LOW FUEL"
        if self.player.wy >= AIRSTRIP_Y - 25:
            return "APPROACH AIRSTRIP"
        return ""

    def _draw_landing_overlay(self):
        if self.land_phase == 2:
            # Refuel screen overlay
            s = pygame.Surface((SCREEN_W, GAME_H), pygame.SRCALPHA)
            s.fill((0, 0, 0, 160))
            self.screen.blit(s, (0, 0))
            lines = [
                "LANDED SAFELY",
                "",
                f"SCORE:  {self.score:6d}",
                f"RANK:   {self.player.rank_for(self.score)}",
                "",
                "REFUELLING AND REARMING...",
            ]
            for i, line in enumerate(lines):
                col = YELLOW if i == 0 else WHITE
                surf = self.font_md.render(line, True, col)
                self.screen.blit(surf, (SCREEN_W // 2 - surf.get_width() // 2,
                                        GAME_H // 2 - 80 + i * 28))

    # ------------------------------------------------------------------
    # Menu screen
    # ------------------------------------------------------------------

    def _draw_menu(self):
        self.screen.fill((10, 20, 60))
        self._centered(self.font_lg, "BLUE MAX", SCREEN_H // 2 - 160, YELLOW)
        self._centered(self.font_sm, "WWI BIPLANE COMBAT", SCREEN_H // 2 - 120, LIGHT_GRAY)
        self._centered(self.font_sm,
                       "Based on the Commodore 64 original by Synapse Software (1983)",
                       SCREEN_H // 2 - 98, GRAY)

        # Difficulty selector
        self._centered(self.font_md, "DIFFICULTY", SCREEN_H // 2 - 50, WHITE)
        diff_names = DIFFICULTIES
        total_w    = len(diff_names) * 120
        start_x    = SCREEN_W // 2 - total_w // 2
        for i, name in enumerate(diff_names):
            col = YELLOW if i == self.diff_idx else GRAY
            rect = pygame.Rect(start_x + i * 120, SCREEN_H // 2 - 20, 110, 34)
            pygame.draw.rect(self.screen, (30, 30, 60), rect, border_radius=4)
            if i == self.diff_idx:
                pygame.draw.rect(self.screen, YELLOW, rect, 2, border_radius=4)
            s = self.font_md.render(name, True, col)
            self.screen.blit(s, (rect.x + rect.w // 2 - s.get_width() // 2,
                                  rect.y + 6))

        self._centered(self.font_md, "PRESS ENTER TO FLY", SCREEN_H // 2 + 40, GREEN)

        # Controls
        controls = [
            "ARROW KEYS / WASD   Move & Altitude",
            "SPACE               Machine Gun",
            "LCTRL / Z / X       Drop Bomb",
            "ESC                 Quit to Menu",
        ]
        for i, line in enumerate(controls):
            s = self.font_sm.render(line, True, LIGHT_GRAY)
            self.screen.blit(s, (SCREEN_W // 2 - s.get_width() // 2,
                                  SCREEN_H // 2 + 90 + i * 22))

        # Rank table
        from constants import RANKS
        self._centered(self.font_sm, "RANKS", SCREEN_H // 2 + 195, CYAN)
        for i, (pts, name) in enumerate(reversed(RANKS)):
            s = self.font_sm.render(f"{pts:5d}  {name}", True, GRAY)
            self.screen.blit(s, (SCREEN_W // 2 - s.get_width() // 2,
                                  SCREEN_H // 2 + 215 + i * 18))

    # ------------------------------------------------------------------
    # Game-over screen
    # ------------------------------------------------------------------

    def _draw_gameover(self):
        self.screen.fill((30, 0, 0))
        rank = Player.rank_for(self.score)

        lines = [
            ("PLANE DESTROYED!", LIGHT_RED,  self.font_lg),
            ("",                 WHITE,       self.font_sm),
            (f"SCORE  {self.score:6d}", YELLOW, self.font_md),
            (f"RANK   {rank}",   LIGHT_BLUE,  self.font_md),
            ("",                 WHITE,       self.font_sm),
            ("PRESS ENTER TO CONTINUE", WHITE, self.font_sm),
        ]
        y = SCREEN_H // 2 - 110
        for text, col, font in lines:
            if text:
                s = font.render(text, True, col)
                self.screen.blit(s, (SCREEN_W // 2 - s.get_width() // 2, y))
            y += 40 if font is self.font_lg else 28

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _centered(self, font, text, y, colour):
        s = font.render(text, True, colour)
        self.screen.blit(s, (SCREEN_W // 2 - s.get_width() // 2, y))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    Game().run()
