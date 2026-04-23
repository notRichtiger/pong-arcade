# ── settings.py ─────────────────────────────────────────────────────────────

import pygame

# Window
WIDTH, HEIGHT = 900, 600
FPS = 60
TITLE = "PONG — ARCADE REBORN"

# Colors (retro-neon palette)
BLACK      = (10,  10,  15)
DARK       = (18,  18,  28)
PANEL      = (22,  22,  38)
BORDER     = (40,  40,  60)
CYAN       = (0,   245, 212)
CYAN_DIM   = (0,   120, 100)
PINK       = (247, 37,  133)
PINK_DIM   = (120, 18,  65)
YELLOW     = (255, 214, 10)
YELLOW_DIM = (120, 100, 5)
WHITE      = (220, 220, 230)
GRAY       = (80,  80,  100)
GRAY_DARK  = (35,  35,  50)

# Gameplay
PADDLE_W, PADDLE_H = 10, 80
PADDLE_SPEED        = 7
BALL_SIZE           = 10
BALL_SPEED_INIT     = 5.0
BALL_SPEED_MAX      = 18.0
BALL_ACCEL          = 0.18   # added per hit
AI_SPEED            = 5.5
AI_REACTION         = 0.82   # 0‒1, higher = smarter
WINNING_SCORE       = 7
LIVES               = 3

# UI
FONT_MONO = "Courier New"
RADIUS    = 12          # rounded-corner default
