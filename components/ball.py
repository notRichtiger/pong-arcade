# ── components/ball.py ───────────────────────────────────────────────────────

import pygame, math, random
from settings import *


class Trail:
    """Fading ghost copies of the ball for the motion trail."""
    def __init__(self):
        self.points: list[tuple[float, float, float]] = []  # (x, y, age 0‒1)
        self.max_len = 12

    def add(self, x: float, y: float):
        self.points.append((x, y, 1.0))
        if len(self.points) > self.max_len:
            self.points.pop(0)

    def update(self):
        self.points = [(x, y, a - 0.09) for x, y, a in self.points if a > 0.05]

    def draw(self, surf: pygame.Surface):
        for x, y, alpha in self.points:
            r = max(1, int(BALL_SIZE * 0.5 * alpha))
            col = (
                int(YELLOW[0] * alpha),
                int(YELLOW[1] * alpha * 0.6),
                int(YELLOW[2] * alpha * 0.05),
            )
            pygame.draw.circle(surf, col, (int(x), int(y)), r)


class Ball:
    def __init__(self):
        self.trail  = Trail()
        self.reset()

    # ── state ────────────────────────────────────────────────────────────────
    def reset(self, direction: int = 1):
        """Place ball in centre, shoot toward `direction` (+1 right / -1 left)."""
        self.x   = WIDTH  / 2
        self.y   = HEIGHT / 2
        self.speed = BALL_SPEED_INIT
        angle = random.uniform(-30, 30)
        rad   = math.radians(angle)
        self.vx = math.cos(rad) * self.speed * direction
        self.vy = math.sin(rad) * self.speed
        self.trail.points.clear()
        self.hit_count    = 0
        self.impact_timer = 0   # frames of glow after hit
        self.rect = pygame.Rect(
            int(self.x) - BALL_SIZE // 2,
            int(self.y) - BALL_SIZE // 2,
            BALL_SIZE, BALL_SIZE,
        )

    # ── physics ──────────────────────────────────────────────────────────────
    def update(self, top_wall: int, bottom_wall: int) -> str | None:
        """
        Move ball, bounce on top/bottom walls.
        Returns 'wall' if a wall bounce happened, else None.
        """
        self.x += self.vx
        self.y += self.vy

        event = None

        # top / bottom bounce
        if self.y - BALL_SIZE / 2 <= top_wall:
            self.y  = top_wall + BALL_SIZE / 2
            self.vy = abs(self.vy)
            event   = "wall"
            self.impact_timer = 8
        elif self.y + BALL_SIZE / 2 >= bottom_wall:
            self.y  = bottom_wall - BALL_SIZE / 2
            self.vy = -abs(self.vy)
            event   = "wall"
            self.impact_timer = 8

        self.trail.add(self.x, self.y)
        self.trail.update()

        if self.impact_timer > 0:
            self.impact_timer -= 1

        self._update_rect()
        return event

    def bounce_off_paddle(self, paddle_rect: pygame.Rect, is_left: bool):
        """
        Reflect ball off a paddle; add spin based on where it hits.
        Accelerate slightly each hit.
        """
        self.hit_count += 1
        # relative hit position ‑1 (top) … +1 (bottom)
        rel = (self.y - paddle_rect.centery) / (paddle_rect.height / 2)
        rel = max(-0.95, min(0.95, rel))

        angle = rel * 60   # max 60° deflection
        rad   = math.radians(angle)

        self.speed = min(self.speed + BALL_ACCEL, BALL_SPEED_MAX)
        direction  = 1 if is_left else -1
        self.vx    = math.cos(rad) * self.speed * direction
        self.vy    = math.sin(rad) * self.speed

        # push ball clear of paddle to prevent sticking
        if is_left:
            self.x = paddle_rect.right + BALL_SIZE / 2 + 1
        else:
            self.x = paddle_rect.left  - BALL_SIZE / 2 - 1

        self.impact_timer = 10
        self._update_rect()

    # ── helpers ──────────────────────────────────────────────────────────────
    def _update_rect(self):
        self.rect.topleft = (
            int(self.x) - BALL_SIZE // 2,
            int(self.y) - BALL_SIZE // 2,
        )

    @property
    def speed_factor(self) -> float:
        return self.speed / BALL_SPEED_INIT   # 1.0 → ~3.0

    # ── draw ─────────────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface):
        self.trail.draw(surf)

        cx, cy = int(self.x), int(self.y)
        r      = BALL_SIZE // 2

        # glow ring when recently hit
        if self.impact_timer > 0:
            glow_alpha = int(180 * self.impact_timer / 10)
            glow_surf  = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*YELLOW, glow_alpha), (r * 3, r * 3), r * 3)
            surf.blit(glow_surf, (cx - r * 3, cy - r * 3))

        pygame.draw.circle(surf, YELLOW, (cx, cy), r)
        # inner bright highlight
        pygame.draw.circle(surf, WHITE,  (cx - 1, cy - 1), max(1, r - 3))
