# ── screens/scoreboard.py ────────────────────────────────────────────────────

import pygame, json, os
from datetime import date
from settings import *
from assets.sounds.generate import sounds

SCORE_FILE = os.path.join(os.path.dirname(__file__), "..", "scores.json")
MAX_ENTRIES = 10


def load_scores() -> list[dict]:
    try:
        with open(SCORE_FILE, "r") as f:
            data = json.load(f)
            return sorted(data, key=lambda e: e["points"], reverse=True)[:MAX_ENTRIES]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_score(name: str, points: int, speed: float) -> int:
    """Append score, sort, trim. Returns rank (1-based)."""
    scores = load_scores()
    entry  = {
        "name":   name[:3].upper(),
        "points": points,
        "speed":  speed,
        "date":   date.today().isoformat(),
    }
    scores.append(entry)
    scores.sort(key=lambda e: e["points"], reverse=True)
    scores = scores[:MAX_ENTRIES]
    os.makedirs(os.path.dirname(SCORE_FILE), exist_ok=True)
    with open(SCORE_FILE, "w") as f:
        json.dump(scores, f, indent=2)
    rank = next((i + 1 for i, e in enumerate(scores) if e is entry), MAX_ENTRIES)
    return rank


def _draw_rounded_panel(surf, rect, col=PANEL):
    pygame.draw.rect(surf, col, rect, border_radius=RADIUS)
    pygame.draw.rect(surf, BORDER, rect, 1, border_radius=RADIUS)


class ScoreboardScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen     = screen
        self.font_title = pygame.font.SysFont(FONT_MONO, 26, bold=True)
        self.font_hdr   = pygame.font.SysFont(FONT_MONO, 12, bold=True)
        self.font_row   = pygame.font.SysFont(FONT_MONO, 15, bold=True)
        self.font_hint  = pygame.font.SysFont(FONT_MONO, 12)
        self.scores     = []
        self.highlight  = -1   # index of the just-added score

    def refresh(self, highlight_rank: int = -1):
        self.scores    = load_scores()
        self.highlight = highlight_rank - 1   # 0-based

    # ── events ───────────────────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                sounds.play("blip")
                return "MENU"
        return None

    # ── draw ─────────────────────────────────────────────────────────────────
    def draw(self):
        surf = self.screen
        surf.fill(BLACK)
        self._draw_grid()

        # title
        title = self.font_title.render("◆  SCOREBOARD  ◆", True, YELLOW)
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 55)))
        pygame.draw.line(surf, BORDER,
                         (WIDTH // 2 - 200, 80), (WIDTH // 2 + 200, 80), 1)

        # panel
        panel = pygame.Rect(WIDTH // 2 - 320, 95, 640, 420)
        _draw_rounded_panel(surf, panel)

        # header row
        y      = 110
        cols_x = [panel.x + 20, panel.x + 70, panel.x + 300, panel.x + 440, panel.x + 570]
        hdrs   = ["#", "NAME", "SCORE", "SPEED", "DATE"]
        for cx, h in zip(cols_x, hdrs):
            lbl = self.font_hdr.render(h, True, GRAY)
            surf.blit(lbl, (cx, y))

        y += 28
        pygame.draw.line(surf, BORDER,
                         (panel.x + 10, y), (panel.right - 10, y), 1)
        y += 10

        # rows
        row_h = 36
        for i, entry in enumerate(self.scores):
            is_hi = (i == self.highlight)
            row_rect = pygame.Rect(panel.x + 6, y - 4, panel.width - 12, row_h)

            if is_hi:
                pygame.draw.rect(surf, (0, 60, 50), row_rect, border_radius=6)
                pygame.draw.rect(surf, CYAN_DIM, row_rect, 1, border_radius=6)

            rank_col = (YELLOW if i == 0 else CYAN if is_hi else GRAY)
            texts = [
                (f"{i+1:02}", rank_col),
                (entry["name"], WHITE if is_hi else WHITE),
                (f"{entry['points']:,}", YELLOW if i == 0 else (CYAN if is_hi else GRAY)),
                (f"×{entry.get('speed', 1.0):.1f}", GRAY),
                (entry["date"][5:],  GRAY_DARK),          # MM-DD only
            ]
            for cx, (txt, col) in zip(cols_x, texts):
                lbl = self.font_row.render(txt, True, col)
                surf.blit(lbl, (cx, y + 4))

            # crown for #1
            if i == 0:
                crown = self.font_hdr.render("👑", True, YELLOW)
                surf.blit(crown, (panel.right - 44, y + 4))

            y += row_h

        # back hint
        hint = self.font_hint.render("ESC / ENTER  →  back to menu", True, GRAY_DARK)
        surf.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 20)))

    def _draw_grid(self):
        col = (18, 18, 26)
        for x in range(0, WIDTH, 60):
            pygame.draw.line(self.screen, col, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 60):
            pygame.draw.line(self.screen, col, (0, y), (WIDTH, y))
