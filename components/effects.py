# ── components/effects.py ────────────────────────────────────────────────────

import pygame, random, math
from settings import *


# ── Particle ─────────────────────────────────────────────────────────────────

class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")

    def __init__(self, x, y, color, count=1):
        self.x       = float(x)
        self.y       = float(y)
        angle        = random.uniform(0, 2 * math.pi)
        speed        = random.uniform(1.5, 5.0)
        self.vx      = math.cos(angle) * speed
        self.vy      = math.sin(angle) * speed
        self.max_life = random.randint(18, 36)
        self.life    = self.max_life
        self.color   = color
        self.size    = random.uniform(2, 5)

    def update(self) -> bool:
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += 0.12          # gravity
        self.vx   *= 0.96          # drag
        self.life -= 1
        return self.life > 0

    def draw(self, surf: pygame.Surface):
        alpha = self.life / self.max_life
        r     = max(1, int(self.size * alpha))
        col   = tuple(int(c * alpha) for c in self.color[:3])
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), r)


# ── Screen shake ─────────────────────────────────────────────────────────────

class ScreenShake:
    def __init__(self):
        self.dur   = 0
        self.mag   = 0

    def trigger(self, magnitude: int = 6, duration: int = 12):
        self.mag  = max(self.mag, magnitude)
        self.dur  = max(self.dur, duration)

    def get_offset(self) -> tuple[int, int]:
        if self.dur <= 0:
            return (0, 0)
        self.dur -= 1
        factor = self.dur / 12
        ox = int(random.uniform(-self.mag, self.mag) * factor)
        oy = int(random.uniform(-self.mag, self.mag) * factor)
        return (ox, oy)


# ── Flash overlay ─────────────────────────────────────────────────────────────

class FlashOverlay:
    def __init__(self):
        self.alpha = 0
        self.color = WHITE

    def trigger(self, color=WHITE, alpha: int = 180):
        self.color = color
        self.alpha = alpha

    def update_draw(self, surf: pygame.Surface):
        if self.alpha <= 0:
            return
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((*self.color, self.alpha))
        surf.blit(overlay, (0, 0))
        self.alpha = max(0, self.alpha - 18)


# ── Particle manager ─────────────────────────────────────────────────────────

class ParticleManager:
    def __init__(self):
        self.particles: list[Particle] = []

    def burst(self, x: float, y: float, color, n: int = 12):
        for _ in range(n):
            self.particles.append(Particle(x, y, color))

    def update_draw(self, surf: pygame.Surface):
        self.particles = [p for p in self.particles if p.update()]
        for p in self.particles:
            p.draw(surf)


# ── Centre dashed line ───────────────────────────────────────────────────────

def draw_court(surf: pygame.Surface, top: int, bottom: int):
    # dotted centre line
    seg_h, gap = 14, 8
    x = WIDTH // 2
    y = top
    while y < bottom:
        end_y = min(y + seg_h, bottom)
        pygame.draw.line(surf, BORDER, (x, y), (x, end_y), 2)
        y += seg_h + gap

    # top / bottom walls
    pygame.draw.line(surf, BORDER, (0, top),    (WIDTH, top),    1)
    pygame.draw.line(surf, BORDER, (0, bottom), (WIDTH, bottom), 1)


# ── Speed bar ────────────────────────────────────────────────────────────────

def draw_speed_bar(surf: pygame.Surface, font_sm, speed_factor: float,
                   x: int, y: int, w: int = 180, h: int = 6):
    ratio = min(1.0, (speed_factor - 1.0) / 2.0)   # 0 at base, 1 at max
    # background
    bg = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surf, GRAY_DARK, bg, border_radius=3)
    # fill — colour shifts cyan → yellow → pink with speed
    if ratio < 0.5:
        t   = ratio * 2
        col = tuple(int(CYAN[i] + (YELLOW[i] - CYAN[i]) * t) for i in range(3))
    else:
        t   = (ratio - 0.5) * 2
        col = tuple(int(YELLOW[i] + (PINK[i] - YELLOW[i]) * t) for i in range(3))
    fill = pygame.Rect(x, y, int(w * ratio), h)
    pygame.draw.rect(surf, col, fill, border_radius=3)

    label = font_sm.render(f"×{speed_factor:.1f}", True, GRAY)
    surf.blit(label, (x + w + 8, y - 2))
