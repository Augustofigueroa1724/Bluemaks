import random
from constants import (
    WORLD_W, WORLD_LEN, AIRSTRIP_Y,
    T_GRASS, T_RIVER, T_ROAD, T_BRIDGE, T_TOWN, T_AIRSTRIP, T_FOREST,
    SCORE_TANK, SCORE_SHIP, SCORE_BRIDGE, SCORE_BUILDING, SCORE_FLAK,
)


class Target:
    """A destroyable ground entity (tank, ship, bridge, building, flak)."""

    _SCORES = {
        "tank":     SCORE_TANK,
        "ship":     SCORE_SHIP,
        "bridge":   SCORE_BRIDGE,
        "building": SCORE_BUILDING,
        "flak":     SCORE_FLAK,
    }

    def __init__(self, kind, wx, wy):
        self.kind  = kind
        self.wx    = wx
        self.wy    = wy
        self.alive = True
        self.hp    = 2 if kind == "bridge" else 1
        self.score = self._SCORES.get(kind, 25)
        self.anim  = 0.0   # explosion animation timer


class World:
    """
    Generates a single river-sector map.

    terrain[y][x] → terrain-type int
    targets        → list[Target]
    river_cx[y]    → river centre tile-x at row y (for queries)
    """

    def __init__(self, seed=None):
        rng = random.Random(seed)
        self.width   = WORLD_W
        self.length  = WORLD_LEN
        self.terrain = []
        self.targets  = []
        self.river_cx = []   # river centre per row
        self._generate(rng)

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def _generate(self, rng):
        river_cx = self.width // 2
        river_w  = 4   # tiles

        for y in range(self.length):
            # Gentle river meander every 20 rows
            if y > 0 and y % 20 == 0:
                river_cx += rng.choice([-1, 0, 0, 1])
                river_cx  = max(5, min(self.width - 6, river_cx))
            self.river_cx.append(river_cx)

            row = []
            for x in range(self.width):
                dist = abs(x - river_cx)
                if dist < river_w // 2:
                    row.append(T_RIVER)
                elif dist == river_w // 2:
                    row.append(T_ROAD if rng.random() < 0.25 else T_GRASS)
                elif rng.random() < 0.04:
                    row.append(T_FOREST)
                elif rng.random() < 0.015:
                    row.append(T_TOWN)
                else:
                    row.append(T_GRASS)
            self.terrain.append(row)

        # Landing airstrip near the end
        for y in range(AIRSTRIP_Y, AIRSTRIP_Y + 10):
            for x in range(2, 9):
                self.terrain[y][x] = T_AIRSTRIP

        self._place_targets(rng)

    def _place_targets(self, rng):
        y = 25
        while y < AIRSTRIP_Y - 10:
            rcx = self.river_cx[y]
            roll = rng.random()

            if roll < 0.22:
                # Bridge spanning river
                for x in range(rcx - 2, rcx + 3):
                    self.targets.append(Target("bridge", x, y))
                    self.terrain[y][x] = T_BRIDGE

            elif roll < 0.44:
                # Ship in river + flanking flak
                self.targets.append(Target("ship", rcx, y))
                for side in (-rcx + rcx - 2, rcx + 2):
                    self.targets.append(Target("flak", side, y))

            elif roll < 0.66:
                # Tank column on road (west bank)
                count = rng.randint(2, 4)
                for i in range(count):
                    self.targets.append(Target("tank", rcx - 3 - i, y + i))

            else:
                # Building cluster on east bank
                count = rng.randint(2, 4)
                for i in range(count):
                    bx = rcx + 3 + rng.randint(0, 2)
                    by = y + rng.randint(-1, 1)
                    self.targets.append(Target("building", bx, by))

            y += rng.randint(6, 14)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def tile_at(self, x, y):
        xi, yi = int(x), int(y)
        if 0 <= yi < self.length and 0 <= xi < self.width:
            return self.terrain[yi][xi]
        return T_GRASS

    def is_airstrip(self, wx, wy):
        return self.tile_at(wx, wy) == T_AIRSTRIP

    def living_targets_near(self, wx, wy, radius=1.5):
        r2 = radius * radius
        return [
            t for t in self.targets
            if t.alive and (t.wx - wx) ** 2 + (t.wy - wy) ** 2 <= r2
        ]
