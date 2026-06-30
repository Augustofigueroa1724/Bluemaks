# Blue Max (C64 1983) - Pygame Recreation
# Game-wide constants

SCREEN_W = 800
SCREEN_H = 600
FPS = 60
TITLE = "Blue Max"

HUD_H = 80
GAME_H = SCREEN_H - HUD_H  # 520 pixels for game viewport

# Isometric tile geometry (2:1 ratio)
TILE_W = 32
TILE_H = 16
ISO_X = TILE_W // 2   # 16 — horizontal step per tile
ISO_Y = TILE_H // 2   # 8  — vertical step per tile

# C64-inspired palette
BLACK       = (0,   0,   0)
WHITE       = (255, 255, 255)
DARK_GRAY   = (51,  51,  51)
GRAY        = (119, 119, 119)
LIGHT_GRAY  = (187, 187, 187)
RED         = (136, 0,   0)
LIGHT_RED   = (255, 100, 100)
BROWN       = (102, 68,  0)
ORANGE      = (221, 136, 85)
YELLOW      = (238, 238, 119)
GREEN       = (0,   160, 60)
DARK_GREEN  = (20,  80,  20)
LIGHT_GREEN = (100, 210, 80)
DARK_BLUE   = (0,   0,   140)
BLUE        = (30,  100, 200)
LIGHT_BLUE  = (100, 180, 255)
CYAN        = (100, 220, 220)
TAN         = (175, 150, 95)
SAND        = (210, 190, 120)

# Terrain tile colors
TERRAIN_COLORS = {
    0: (34,  120, 34),   # grass
    1: (25,  90,  185),  # river
    2: (155, 135, 85),   # road
    3: (110, 95,  70),   # bridge
    4: (140, 95,  70),   # town
    5: (210, 190, 115),  # airstrip
    6: (18,  75,  18),   # forest
}
TERRAIN_EDGE_COLORS = {
    0: (24,  90,  24),
    1: (15,  65,  150),
    2: (120, 100, 60),
    3: (80,  70,  50),
    4: (110, 70,  50),
    5: (170, 150, 80),
    6: (10,  55,  10),
}

# Terrain type IDs
T_GRASS    = 0
T_RIVER    = 1
T_ROAD     = 2
T_BRIDGE   = 3
T_TOWN     = 4
T_AIRSTRIP = 5
T_FOREST   = 6

# World dimensions
WORLD_W    = 30   # tiles wide
WORLD_LEN  = 600  # tiles long (one river sector)
AIRSTRIP_Y = WORLD_LEN - 30  # landing zone near end

# Player
PLAYER_SPEED_X  = 100.0  # world-units/sec lateral
SCROLL_SPEED    = 70.0   # world-units/sec forward (wy increases)
MAX_ALTITUDE    = 3
ALTITUDE_PX     = [0, 22, 48, 80]  # screen pixels above shadow per altitude level
ALTITUDE_CHANGE = 2.0   # levels/sec

# Bombs
MAX_BOMBS      = 30
FALL_DURATION  = [0, 0.5, 1.0, 1.8]  # seconds to fall from each altitude level

# Bullets
BULLET_SPEED   = 200.0  # world-units/sec forward

# Enemy
ENEMY_SPEED    = 55.0
ENEMY_SPAWN_AHEAD = 25   # tiles ahead of player

# Damage system (4 hits allowed; 5th destroys plane)
DAMAGE_GUNS  = "guns"
DAMAGE_BOMBS = "bomb_gear"
DAMAGE_FUEL  = "fuel"
DAMAGE_MANEUV= "maneuverability"
MAX_HITS     = 4

# Score values
SCORE_TANK     = 50
SCORE_SHIP     = 100
SCORE_BRIDGE   = 150
SCORE_BUILDING = 25
SCORE_FLAK     = 30
SCORE_PLANE    = 200

# Rank thresholds (ascending)
RANKS = [
    (25000, "General"),
    (16000, "Colonel"),
    (10000, "Major"),
    (6000,  "Captain"),
    (3000,  "Lieutenant"),
    (1500,  "Sergeant"),
    (500,   "Corporal"),
    (0,     "Private"),
]

# Difficulty modifiers
DIFFICULTIES = ["Easy", "Normal", "Hard"]
DIFF_SETTINGS = {
    "Easy":   {"fire_rate": 0.5, "flak_chance": 0.3, "spawn_rate": 0.4},
    "Normal": {"fire_rate": 1.0, "flak_chance": 0.6, "spawn_rate": 0.7},
    "Hard":   {"fire_rate": 1.8, "flak_chance": 1.0, "spawn_rate": 1.0},
}

# Game states
S_MENU     = "menu"
S_FLYING   = "flying"
S_LANDING  = "landing"
S_GAMEOVER = "gameover"
