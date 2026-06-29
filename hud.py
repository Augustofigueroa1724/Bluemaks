"""
HUD bar drawn beneath the game viewport (y = GAME_H to SCREEN_H).
Shows: score, rank, altitude, fuel, bombs, damage indicators, status messages.
"""

import pygame
from constants import (
    SCREEN_W, GAME_H, HUD_H,
    BLACK, WHITE, GRAY, DARK_GRAY, LIGHT_GRAY,
    RED, LIGHT_RED, YELLOW, GREEN, ORANGE, BLUE, LIGHT_BLUE,
    DAMAGE_GUNS, DAMAGE_BOMBS, DAMAGE_FUEL, DAMAGE_MANEUV,
)

_DAMAGE_LABELS = {
    DAMAGE_GUNS:  "GUNS",
    DAMAGE_BOMBS: "BMBS",
    DAMAGE_FUEL:  "FUEL",
    DAMAGE_MANEUV: "MNVR",
}


class HUD:
    def __init__(self):
        pygame.font.init()
        self._font  = pygame.font.SysFont("Courier New,monospace", 14, bold=True)
        self._big   = pygame.font.SysFont("Courier New,monospace", 20, bold=True)
        self._small = pygame.font.SysFont("Courier New,monospace", 11)
        self._flash = 0.0

    def update(self, dt):
        self._flash = (self._flash + dt * 4) % 2.0  # blink period

    @property
    def _blink_on(self):
        return self._flash < 1.0

    # ------------------------------------------------------------------

    def draw(self, surface, player, score, difficulty, status_msg=""):
        # Background bar
        bar = pygame.Rect(0, GAME_H, SCREEN_W, HUD_H)
        pygame.draw.rect(surface, (10, 10, 20), bar)
        pygame.draw.line(surface, GRAY, (0, GAME_H), (SCREEN_W, GAME_H), 2)

        x, y = 8, GAME_H + 6

        # Score & rank
        rank = player.rank_for(score)
        self._text(surface, f"SCORE {score:06d}", x, y, YELLOW)
        self._text(surface, rank.upper(), x + 160, y, LIGHT_BLUE)

        # Altitude indicator
        alt_colours = [YELLOW, (170, 150, 40), GREEN, LIGHT_BLUE]
        col = alt_colours[player.alt]
        bar_str = "▮" * (player.alt + 1) + "▯" * (MAX_ALT - player.alt)
        self._text(surface, f"ALT {bar_str}", x + 310, y, col)

        # Fuel gauge
        fuel_pct = player.fuel / 100.0
        fuel_col = RED if fuel_pct < 0.25 else (ORANGE if fuel_pct < 0.5 else GREEN)
        self._text(surface, "FUEL", x + 490, y, WHITE)
        gauge_rect = pygame.Rect(x + 540, y + 2, 80, 10)
        pygame.draw.rect(surface, DARK_GRAY, gauge_rect)
        fill_rect  = pygame.Rect(x + 540, y + 2, int(80 * fuel_pct), 10)
        pygame.draw.rect(surface, fuel_col, fill_rect)
        pygame.draw.rect(surface, GRAY, gauge_rect, 1)

        # Bombs remaining
        self._text(surface, f"BOMB {player.bombs:02d}", x + 640, y, WHITE)

        # Difficulty
        diff_colours = {"Easy": GREEN, "Normal": YELLOW, "Hard": RED}
        self._text(surface, difficulty.upper(), x + 730, y,
                   diff_colours.get(difficulty, WHITE))

        # Second row: damage indicators
        y2 = GAME_H + 28
        self._text(surface, "DMG:", x, y2, LIGHT_GRAY)
        dx = x + 50
        for dtype, label in _DAMAGE_LABELS.items():
            active = dtype in player.damage
            col    = LIGHT_RED if active else DARK_GRAY
            self._text(surface, label, dx, y2, col)
            dx += 58

        # Hits bar (| per hit taken, colour-coded)
        hit_x = x + 310
        self._text(surface, "HITS:", hit_x, y2, LIGHT_GRAY)
        for i in range(4):
            col = LIGHT_RED if i < player.hits else DARK_GRAY
            pygame.draw.rect(surface, col, (hit_x + 50 + i * 14, y2 + 2, 10, 10))

        # Status message (flashing)
        if status_msg and self._blink_on:
            surf = self._big.render(status_msg, True, YELLOW)
            surface.blit(surf, (SCREEN_W // 2 - surf.get_width() // 2, y2))

        # Invincibility flash bar
        if player.invincible > 0:
            alpha = int(player.invincible * 100)
            tmp = pygame.Surface((SCREEN_W, 2), pygame.SRCALPHA)
            tmp.fill((*LIGHT_RED, min(255, alpha * 10)))
            surface.blit(tmp, (0, GAME_H))

    # ------------------------------------------------------------------

    def _text(self, surface, msg, x, y, colour):
        surf = self._font.render(msg, True, colour)
        surface.blit(surf, (x, y))


MAX_ALT = 3
