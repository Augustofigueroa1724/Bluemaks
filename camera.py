from constants import SCREEN_W, GAME_H, ISO_X, ISO_Y


def world_to_screen(wx, wy, cam_wx, cam_wy):
    """
    Isometric projection used by Blue Max:
      east  (+wx) → lower-right on screen
      north (+wy) → upper-right on screen  (flight direction)
    Camera follows player so player stays at screen centre.
    Returns the LEFT vertex of the tile rhombus at world (wx, wy).
    """
    dx = wx - cam_wx
    dy = wy - cam_wy
    sx = SCREEN_W // 2 + int((dx + dy) * ISO_X)
    sy = GAME_H  // 2 + int((dx - dy) * ISO_Y)
    return sx, sy


def tile_corners(sx, sy):
    """
    Return the 4 screen vertices of the isometric tile whose left
    vertex is at (sx, sy).  Order: left, bottom, right, top (clockwise).
    """
    return [
        (sx,           sy),          # left   (NW world corner)
        (sx + ISO_X,   sy + ISO_Y),  # bottom (NE world corner)
        (sx + 2*ISO_X, sy),          # right  (SE world corner)
        (sx + ISO_X,   sy - ISO_Y),  # top    (SW world corner)
    ]


class Camera:
    def __init__(self):
        self.wx = 0.0
        self.wy = 0.0

    def follow(self, wx, wy):
        self.wx = wx
        self.wy = wy

    def w2s(self, wx, wy):
        return world_to_screen(wx, wy, self.wx, self.wy)
