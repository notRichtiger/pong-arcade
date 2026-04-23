# ── screens/gameover.py ──────────────────────────────────────────────────────

import pygame, math
from settings import *
from assets.sounds.generate import sounds

ALLOWED_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def _draw_btn(surf, rect, text, font, active=False, danger=False):
    border = PINK if danger else (CYAN if active else GRAY)
    fill   = CYAN_DIM if active else (PINK_DIM if danger else GRAY_DARK)
    pygame.draw.rect(surf, fill,   rect, border_radius=RADIUS)
    pygame.draw.rect(surf, border, rect, 1, border_radius=RADIUS)
    col  = WHITE if active else (PINK if danger else GRAY)
    lbl  = font.render(text, True, col)
    surf.blit(lbl, lbl.get_rect(center=rect.center))


class GameOverScreen:
    BTNS = ["RETRY", "SCOREBOARD", "EXIT"]

    def __init__(self, screen: pygame.Surface):
        self.screen     = screen
        self.font_big   = pygame.font.SysFont(FONT_MONO, 36, bold=True)
        self.font_score = pygame.font.SysFont(FONT_MONO, 56, bold=True)
        self.font_mid   = pygame.font.SysFont(FONT_MONO, 18, bold=True)
        self.font_sm    = pygame.font.SysFont(FONT_MONO, 13)
        self.font_stat  = pygame.font.SysFont(FONT_MONO, 14)

        self.stats      = {}
        self.tick       = 0
        self.sel        = 0

        # name entry
        self.name          = ["A", "A", "A"]
        self.name_cursor   = 0
        self.entering_name = True

    def set_stats(self, stats: dict):
        self.stats         = stats
        self.tick          = 0
        self.sel           = 0
        self.name          = ["A", "A", "A"]
        self.name_cursor   = 0
        self.entering_name = True

    # ── events ───────────────────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        """Returns action string or None. Special: ('SAVE', name) tuple."""
        if event.type != pygame.KEYDOWN:
            return None

        if self.entering_name:
            return self._handle_name_input(event)

        # button nav
        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.sel = (self.sel - 1) % len(self.BTNS)
            sounds.play("blip")
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.sel = (self.sel + 1) % len(self.BTNS)
            sounds.play("blip")
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            sounds.play("blip")
            return self.BTNS[self.sel]
        return None

    def _handle_name_input(self, event: pygame.event.Event):
        k = event.key
        if k == pygame.K_LEFT:
            self.name_cursor = max(0, self.name_cursor - 1)
            sounds.play("blip")
        elif k == pygame.K_RIGHT:
            self.name_cursor = min(2, self.name_cursor + 1)
            sounds.play("blip")
        elif k == pygame.K_UP:
            ch = self.name[self.name_cursor]
            idx = (ALLOWED_CHARS.index(ch) + 1) % len(ALLOWED_CHARS)
            self.name[self.name_cursor] = ALLOWED_CHARS[idx]
            sounds.play("blip")
        elif k == pygame.K_DOWN:
            ch = self.name[self.name_cursor]
            idx = (ALLOWED_CHARS.index(ch) - 1) % len(ALLOWED_CHARS)
            self.name[self.name_cursor] = ALLOWED_CHARS[idx]
            sounds.play("blip")
        elif k == pygame.K_RETURN:
            name = "".join(self.name)
            self.entering_name = False
            sounds.play("score")
            return ("SAVE", name)
        return None

    # ── draw ─────────────────────────────────────────────────────────────────
    def draw(self):
        surf = self.screen
        surf.fill(BLACK)
        self.tick += 1
        self._draw_bg()

        pulse = abs(math.sin(self.tick * 0.05))
        title_col = tuple(int(PINK[i] * (0.7 + 0.3 * pulse)) for i in range(3))

        # GAME OVER
        go = self.font_big.render("G A M E   O V E R", True, title_col)
        surf.blit(go, go.get_rect(center=(WIDTH // 2, 65)))

        # score
        pts   = self.stats.get("points", 0)
        score = self.font_score.render(f"{pts:,}", True, CYAN)
        surf.blit(score, score.get_rect(center=(WIDTH // 2, 145)))
        lbl = self.font_sm.render("P O I N T S", True, GRAY)
        surf.blit(lbl, lbl.get_rect(center=(WIDTH // 2, 178)))

        # divider
        pygame.draw.line(surf, BORDER,
                         (WIDTH // 2 - 220, 196), (WIDTH // 2 + 220, 196), 1)

        # stats panel
        self._draw_stats(210)

        # name entry or buttons
        if self.entering_name:
            self._draw_name_entry(370)
        else:
            self._draw_buttons(390)

    # ── helpers ──────────────────────────────────────────────────────────────
    def _draw_stats(self, top_y: int):
        surf = self.screen
        items = [
            ("PLAYER SCORE", f"{self.stats.get('player', 0)}"),
            ("CPU SCORE",    f"{self.stats.get('cpu', 0)}"),
            ("LIVES LEFT",   f"{self.stats.get('lives', 0)}"),
            ("MAX SPEED",    f"×{self.stats.get('speed', 1.0):.1f}"),
        ]
        col_x = [WIDTH // 2 - 200, WIDTH // 2 + 40]
        y     = top_y
        for i, (k, v) in enumerate(items):
            x = col_x[i % 2]
            if i % 2 == 0 and i > 0:
                y += 36
            kl = self.font_sm.render(k, True, GRAY)
            vl = self.font_stat.render(v, True, WHITE)
            surf.blit(kl, (x, y))
            surf.blit(vl, (x, y + 16))
        # last odd item
        if len(items) % 2:
            pass   # already placed above

    def _draw_name_entry(self, y: int):
        surf = self.screen
        prompt = self.font_sm.render("ENTER YOUR NAME  ↑ ↓ change  ← → move  ENTER confirm", True, GRAY)
        surf.blit(prompt, prompt.get_rect(center=(WIDTH // 2, y)))

        y += 28
        box_w, box_h = 64, 64
        gap = 16
        total = 3 * box_w + 2 * gap
        sx = WIDTH // 2 - total // 2

        for i, ch in enumerate(self.name):
            rect = pygame.Rect(sx + i * (box_w + gap), y, box_w, box_h)
            active = (i == self.name_cursor)
            blink  = active and (self.tick // 20) % 2 == 0
            border = CYAN if active else BORDER
            fill   = (0, 40, 35) if active else DARK
            pygame.draw.rect(surf, fill,   rect, border_radius=8)
            pygame.draw.rect(surf, border, rect, 1 if not blink else 2, border_radius=8)
            letter = self.font_big.render(ch, True, CYAN if active else WHITE)
            surf.blit(letter, letter.get_rect(center=rect.center))

    def _draw_buttons(self, y: int):
        surf = self.screen
        btn_w, btn_h, gap = 170, 44, 16
        total = len(self.BTNS) * btn_w + (len(self.BTNS) - 1) * gap
        sx = WIDTH // 2 - total // 2
        for i, label in enumerate(self.BTNS):
            rect = pygame.Rect(sx + i * (btn_w + gap), y, btn_w, btn_h)
            _draw_btn(
                surf, rect, f"▶ {label}" if i == self.sel else label,
                self.font_mid,
                active=(i == self.sel),
                danger=(label == "EXIT"),
            )
        hint = self.font_sm.render("← → to select   ENTER to confirm", True, GRAY_DARK)
        surf.blit(hint, hint.get_rect(center=(WIDTH // 2, y + btn_h + 18)))

    def _draw_bg(self):
        surf = self.screen
        for i in range(0, WIDTH, 80):
            pygame.draw.line(surf, (18, 18, 28), (i, 0), (i, HEIGHT))
        for i in range(0, HEIGHT, 80):
            pygame.draw.line(surf, (18, 18, 28), (0, i), (WIDTH, i))
