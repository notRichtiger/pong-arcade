# ── screens/menu.py ──────────────────────────────────────────────────────────

import pygame, math
from settings import *
from assets.sounds.generate import sounds


def _draw_rounded_btn(surf, rect, text, font, active=False, danger=False):
    border_col = PINK if danger else (CYAN if active else GRAY)
    fill_col   = (*((PINK_DIM if danger else CYAN_DIM)),) if active else GRAY_DARK
    pygame.draw.rect(surf, fill_col,   rect, border_radius=RADIUS)
    pygame.draw.rect(surf, border_col, rect, 1, border_radius=RADIUS)
    label = font.render(text, True, PINK if danger else (WHITE if active else GRAY))
    surf.blit(label, label.get_rect(center=rect.center))


class MenuScreen:
    ITEMS = ["START GAME", "SCOREBOARD", "SETTINGS", "EXIT"]

    def __init__(self, screen: pygame.Surface):
        self.screen  = screen
        self.sel     = 0
        self.tick    = 0

        self.font_title = pygame.font.SysFont(FONT_MONO, 52, bold=True)
        self.font_sub   = pygame.font.SysFont(FONT_MONO, 13)
        self.font_btn   = pygame.font.SysFont(FONT_MONO, 17, bold=True)
        self.font_hs    = pygame.font.SysFont(FONT_MONO, 12)

    # ── event handling ───────────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % len(self.ITEMS)
                sounds.play("blip")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % len(self.ITEMS)
                sounds.play("blip")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.ITEMS[self.sel]
        return None

    # ── draw ─────────────────────────────────────────────────────────────────
    def draw(self, highscore: int = 0):
        surf = self.screen
        surf.fill(BLACK)
        self.tick += 1

        # animated grid overlay
        self._draw_grid()

        # title
        pulse = abs(math.sin(self.tick * 0.04))
        col   = tuple(int(CYAN[i] * (0.7 + 0.3 * pulse)) for i in range(3))
        title = self.font_title.render("PONG", True, col)
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 130)))

        sub = self.font_sub.render("A R C A D E   R E B O R N", True, GRAY)
        surf.blit(sub, sub.get_rect(center=(WIDTH // 2, 185)))

        # mini decorative divider
        pygame.draw.line(surf, BORDER, (WIDTH // 2 - 80, 205), (WIDTH // 2 + 80, 205), 1)

        # menu buttons
        btn_w, btn_h, gap = 280, 46, 12
        start_y = 235
        for i, item in enumerate(self.ITEMS):
            rect = pygame.Rect(
                WIDTH // 2 - btn_w // 2,
                start_y + i * (btn_h + gap),
                btn_w, btn_h,
            )
            active  = (i == self.sel)
            danger  = (item == "EXIT")
            prefix  = "▶  " if active else "   "
            _draw_rounded_btn(surf, rect, prefix + item,
                              self.font_btn, active=active, danger=danger)

        # highscore footer
        if highscore > 0:
            hs = self.font_hs.render(f"BEST  {highscore:>6}  PTS", True, YELLOW_DIM)
            surf.blit(hs, hs.get_rect(center=(WIDTH // 2, HEIGHT - 30)))

        # controls hint
        hint = self.font_hs.render("W / S  or  ↑ / ↓   ENTER to select", True, GRAY_DARK)
        surf.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 14)))

    def _draw_grid(self):
        surf = self.screen
        spacing = 60
        offset  = (self.tick // 2) % spacing
        col     = (20, 20, 32)
        for x in range(-spacing, WIDTH + spacing, spacing):
            pygame.draw.line(surf, col, (x + offset, 0), (x + offset, HEIGHT), 1)
        for y in range(0, HEIGHT + spacing, spacing):
            pygame.draw.line(surf, col, (0, y), (WIDTH, y), 1)
