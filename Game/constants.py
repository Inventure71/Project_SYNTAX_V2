
# --------- Config ---------
import pygame


SCREEN_W, SCREEN_H = 900, 600
WORLD_W, WORLD_H = 2400, 1800
BG_COLOR = (25, 28, 35)
WHITE = (240, 240, 240)
GREEN = (80, 200, 120)
RED = (220, 80, 90)
YELLOW = (245, 210, 85)
CYAN = (80, 200, 220)
BORDER = (70, 74, 86)
UI_DARK = (50, 54, 64)
UI_DARK_2 = (70, 76, 90)
UI_STROKE = (90, 96, 110)

FONT = None
BIGFONT = None

PLAYER_SPEED = 280.0         # world px / second
BULLET_SPEED = 520.0
ENEMY_SPEED  = 120.0

ZOOM = 1.3  # >1.0 means zoomed-in (see less of the world)

# Camera zoom bounds and step
ZOOM_STEP = 0.2
ZOOM_MAX = 8.0

COLLISION_EVENT = pygame.USEREVENT + 1