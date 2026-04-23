# ── components/paddle.py ─────────────────────────────────────────────────────

import pygame, random
from settings import *


class Paddle:
    def __init__(self, side: str):
        """side = 'left' (player) or 'right' (AI/P2)."""
        self.side   = side
        self.color  = CYAN if side == "left" else PINK
        self.dim    = CYAN_DIM if side == "left" else PINK_DIM
        self.speed  = PADDLE_SPEED
        self.trail: list[tuple[int, int, float]] = []  # (y, alpha)

        x = 30 if side == "left" else WIDTH - 30 - PADDLE_W
        self.rect = pygame.Rect(x, (HEIGHT - PADDLE_H) // 2, PADDLE_W, PADDLE_H)
        self.impact_timer = 0

    # ── movement ─────────────────────────────────────────────────────────────
    def move_by(self, dy: float, top: int, bottom: int):
        self.trail.append((self.rect.y, 1.0))
        self.trail = [(y, a - 0.25) for y, a in self.trail if a > 0.1]

        self.rect.y += int(dy)
        self.rect.y  = max(top, min(bottom - PADDLE_H, self.rect.y))

    def handle_input(self, keys: pygame.key.ScancodeWrapper, top: int, bottom: int):
        """Human player: W/S or arrow keys."""
        dy = 0
        if self.side == "left":
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy -= self.speed
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy += self.speed
        else:
            if keys[pygame.K_UP]:
                dy -= self.speed
            if keys[pygame.K_DOWN]:
                dy += self.speed
        if dy:
            self.move_by(dy, top, bottom)

    def ai_move(self, ball_y: float, top: int, bottom: int):
        """Simple predictive AI with configurable reaction."""
        centre = self.rect.centery
        target = ball_y + random.uniform(-12, 12) * (1 - AI_REACTION)
        diff   = target - centre
        move   = max(-AI_SPEED, min(AI_SPEED, diff * AI_REACTION))
        self.move_by(move, top, bottom)

    # ── hit flash ────────────────────────────────────────────────────────────
    def flash(self):
        self.impact_timer = 10

    # ── draw ─────────────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface):
        # ghost trail
        for i, (y, alpha) in enumerate(self.trail):
            col = tuple(int(c * alpha * 0.35) for c in self.color)
            r   = pygame.Rect(self.rect.x, y, PADDLE_W, PADDLE_H)
            pygame.draw.rect(surf, col, r, border_radius=5)

        # glow when recently hit
        if self.impact_timer > 0:
            g = int(150 * self.impact_timer / 10)
            glow = pygame.Surface((PADDLE_W + 20, PADDLE_H + 20), pygame.SRCALPHA)
            glow.fill((0, 0, 0, 0))
            pygame.draw.rect(
                glow,
                (*self.color, g),
                (10, 10, PADDLE_W, PADDLE_H),
                border_radius=6,
            )
            surf.blit(glow, (self.rect.x - 10, self.rect.y - 10))
            self.impact_timer -= 1

        # main body
        pygame.draw.rect(surf, self.color, self.rect, border_radius=5)
        # bright centre stripe
        stripe = pygame.Rect(
            self.rect.x + 2, self.rect.centery - 8, PADDLE_W - 4, 16
        )
        pygame.draw.rect(surf, WHITE, stripe, border_radius=3)
