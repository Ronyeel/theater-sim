import os

SCREEN_W   = 960
SCREEN_H   = 720
FPS        = 60
GAME_TITLE = "RR-EL - Theater Simulator"

TILE_SIZE  = 48
MAP_COLS   = 20
MAP_ROWS   = 25
WORLD_W    = MAP_COLS * TILE_SIZE
WORLD_H    = MAP_ROWS * TILE_SIZE

PLAYER_SPEED        = 130
PLAYER_SPRITE_W     = 24
PLAYER_SPRITE_H     = 32
INTERACT_RADIUS     = 60
INTERACT_HOLD_TIME  = 0.8

DEBUG_NPC_COLLISION_RANGE = False

DEFAULT_CASHIERS         = 2
DEFAULT_USHERS           = 1
DEFAULT_SERVERS          = 2

DEFAULT_RUNTIME          = 90
DEFAULT_ARRIVAL_INTERVAL = 0.20
DEFAULT_FOOD_PROB        = 0.5
RANDOM_SEED              = None
SIM_SPEEDS               = [1, 2, 5, 10]

ASSETS_DIR    = os.path.join(os.path.dirname(__file__), "assets")
TILES_DIR     = os.path.join(ASSETS_DIR, "tiles")
SPRITES_DIR   = os.path.join(ASSETS_DIR, "sprites")
UI_DIR        = os.path.join(ASSETS_DIR, "ui")
BG_DIR        = os.path.join(ASSETS_DIR, "backgrounds")

C_BG_DARK       = ( 15,  10,  30)
C_BG_MID        = ( 28,  20,  55)
C_FLOOR         = (220, 200, 160)
C_FLOOR_ALT     = (200, 180, 140)
C_CARPET_D      = (120,  20,  30)
C_CARPET_L      = (160,  40,  50)
C_WALL          = ( 55,  45,  75)
C_WALL_TRIM     = (190, 160,  90)
C_DESK          = (110,  75,  45)
C_SEAT_EMPTY    = (110,  25,  40)
C_SEAT_TAKEN    = ( 65,  15,  25)
C_SCREEN        = ( 20,  30,  80)
C_DOOR          = (160, 100,  50)
C_CORRIDOR      = ( 45,  35,  60)
C_SECURITY      = ( 70,  65,  90)
C_POSTER_BG     = ( 40,  30,  65)
C_PLANT         = ( 50, 130,  60)
C_TABLE         = (140, 100,  55)

C_NEON_PINK     = (255,  80, 180)
C_NEON_CYAN     = ( 80, 240, 255)
C_NEON_GOLD     = (255, 210,  80)
C_NEON_GREEN    = ( 80, 255, 140)
C_NEON_RED      = (255,  70,  70)

C_TEXT_WHITE    = (245, 240, 255)
C_TEXT_DIM      = (160, 150, 185)
C_TEXT_GOLD     = (255, 215,  90)
C_PANEL_BG      = ( 20,  15,  45, 210)
C_PANEL_BORDER  = (100,  80, 150)
C_BTN_BG        = ( 45,  35,  80)
C_BTN_HOVER     = ( 65,  52, 110)
C_BTN_ACTIVE    = ( 90,  70, 145)
C_GOOD          = ( 80, 230, 130)
C_BAD           = (255,  70,  70)
C_WARN          = (255, 200,  60)

NPC_COLORS = [
    (230, 100, 100),
    (100, 180, 230),
    (100, 220, 130),
    (230, 200,  80),
    (200, 130, 230),
    (230, 160, 100),
    (180, 230, 230),
    (230, 130, 180),
]

C_CASHIER_VEST   = (210, 180,  60)
C_USHER_JACKET   = (180,  40,  50)
C_SERVER_APRON   = (235, 235, 235)

TILE_EMPTY      = 0
TILE_WALL       = 1
TILE_FLOOR      = 2
TILE_CARPET     = 3
TILE_DESK       = 4
TILE_SEAT       = 5
TILE_DOOR       = 6
TILE_NEON       = 7
TILE_QUEUE      = 8
TILE_SNACK      = 9
TILE_SCREEN     = 10
TILE_USHER      = 11
TILE_SECURITY   = 12
TILE_POSTER     = 13
TILE_PLANT      = 14
TILE_TABLE      = 15
TILE_CORRIDOR   = 16
TILE_RED_CARPET = 17

PLAYER_SPAWN    = (10, 22)

AUDITORIUM_DOOR_COLS = [8, 9, 10, 11]
AUDITORIUM_DOOR_ROW  = 7

CASHIER_DESK_ROW    = 17
CASHIER_DESK_COLS   = [4, 7, 10, 13]
CASHIER_QUEUE_ROW   = 18

USHER_DESK_ROW      = 14
USHER_DESK_COLS     = [7, 12]
USHER_GATE_COLS     = list(range(1, MAP_COLS - 1))
USHER_PASSAGE_COLS  = [8, 9, 10, 11]

SNACK_DESK_ROW      = 11
SNACK_DESK_COLS     = [5, 9, 13]

CORRIDOR_ROW        = 8

SEAT_ROWS           = [2, 3, 4, 5, 6]
SEAT_COLS           = list(range(2, 18))

EXIT_DOOR_COLS      = [9, 10]
EXIT_DOOR_ROW       = 24

SECURITY_COL        = 3
SECURITY_ROW        = 21

BOARD_COL           = 15
BOARD_ROW           = 21

MOVIES = [
    {"title": "Starlight Express",  "time": "7:30 PM", "screen": 1},
    {"title": "Midnight Run",       "time": "8:00 PM", "screen": 2},
    {"title": "Ocean Dreams",       "time": "8:30 PM", "screen": 3},
]

CONCESSION_ITEMS = [
    {"name": "🍿 Popcorn",    "price": "₱120"},
    {"name": "🥤 Soda",       "price": "₱80"},
    {"name": "🍫 Chocolate",  "price": "₱60"},
    {"name": "🌭 Hotdog",     "price": "₱100"},
]

SCENARIOS = {
    "normal": {
        "label": "Normal Night",
        "arrival_interval": 0.20,
        "food_prob": 0.5,
        "runtime": 90,
    },
    "friday": {
        "label": "Friday Night",
        "arrival_interval": 0.13,
        "food_prob": 0.55,
        "runtime": 90,
    },
    "blockbuster": {
        "label": "Blockbuster Premiere",
        "arrival_interval": 0.08,
        "food_prob": 0.6,
        "runtime": 120,
    },
    "family": {
        "label": "Family Night",
        "arrival_interval": 0.18,
        "food_prob": 0.80,
        "runtime": 90,
    },
    "late": {
        "label": "Late Show",
        "arrival_interval": 0.25,
        "food_prob": 0.40,
        "runtime": 60,
    },
}
