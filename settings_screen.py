# ── screens/settings_screen.py ───────────────────────────────────────────────
"""
Settings screen — replaces the old 3-row version.

New features
────────────
• COLOR SCHEME  — NEON / RETRO / PASTEL / OCEAN / FIRE / CUSTOM
  └ CUSTOM expands four sub-rows: P1 COLOR, P2 COLOR, BALL COLOR, BG COLOR
    each showing the 12-colour palette with ← / → to cycle
• RESOLUTION    — 720p / 1080p / 1440p / 4K
    (applied on next launch; a warning banner appears immediately)
• DIFFICULTY    — EASY / NORMAL / HARD / INSANE  (unchanged)
• VOLUME        — smooth slider  (unchanged)

Integration note for main.py
─────────────────────────────
After creating the pygame window, check cfg.pending_resize each frame:

    if cfg.pending_resize:
        screen = pygame.display.set_mode(cfg.get_resolution())
        cfg.pending_resize = False

Or, more simply, read cfg.get_resolution() before pygame.display.set_mode() on
startup and the saved resolution will be used automatically on the next launch.
"""

import pygame, math
from settings import *
from settings_manager import (
    cfg,
    SCHEME_NAMES, DIFFICULTY_NAMES, RESOLUTION_NAMES,
    SCHEMES, DIFFICULTIES, RESOLUTIONS, COLOR_PALETTE,
)
from assets.sounds.generate import sounds


# ── helpers ───────────────────────────────────────────────────────────────────

def _dim(col, factor=0.35):
    return tuple(max(0, min(255, int(c * factor))) for c in col)

def _lerp_col(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def _draw_panel_bg(surf, rect):
    pygame.draw.rect(surf, PANEL,  rect, border_radius=RADIUS + 4)
    pygame.draw.rect(surf, BORDER, rect, 1, border_radius=RADIUS + 4)


# ── main class ────────────────────────────────────────────────────────────────

class SettingsScreen:

    # Static rows; colour sub-rows are injected dynamically via `rows` property
    _BASE_ROWS = [
        ("COLOR SCHEME", "scheme"),
        ("RESOLUTION",   "resolution"),
        ("DIFFICULTY",   "difficulty"),
        ("VOLUME",       "volume"),
    ]
    _COLOR_SUBROWS = [
        ("  ├ P1 COLOR",   "p1_color"),
        ("  ├ P2 COLOR",   "p2_color"),
        ("  ├ BALL COLOR", "ball_color"),
        ("  └ BG COLOR",   "bg_color"),
    ]

    # Height of each row in pixels
    _ROW_H = {
        "scheme":     68,
        "p1_color":   46,
        "p2_color":   46,
        "ball_color": 46,
        "bg_color":   46,
        "resolution": 58,
        "difficulty": 66,
        "volume":     52,
    }

    def __init__(self, screen: pygame.Surface):
        self.screen       = screen
        self.tick         = 0
        self.preview_tick = 0
        self.sel          = 0
        self._res_warn    = 0   # frames to show the restart-required banner

        self.font_title = pygame.font.SysFont(FONT_MONO, 26, bold=True)
        self.font_lbl   = pygame.font.SysFont(FONT_MONO, 14, bold=True)
        self.font_val   = pygame.font.SysFont(FONT_MONO, 15, bold=True)
        self.font_sm    = pygame.font.SysFont(FONT_MONO, 11)

    # ── dynamic row list ─────────────────────────────────────────────────────

    @property
    def rows(self) -> list[tuple[str, str]]:
        result = []
        for label, attr in self._BASE_ROWS:
            result.append((label, attr))
            if attr == "scheme" and cfg.scheme == "CUSTOM":
                result.extend(self._COLOR_SUBROWS)
        return result

    # ── events ───────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return None
        k = event.key

        if k == pygame.K_ESCAPE:
            cfg.save()
            sounds.play("blip")
            return "MENU"

        rows = self.rows
        if k in (pygame.K_UP, pygame.K_w):
            self.sel = (self.sel - 1) % len(rows)
            sounds.play("blip")
        elif k in (pygame.K_DOWN, pygame.K_s):
            self.sel = (self.sel + 1) % len(rows)
            sounds.play("blip")
        elif k in (pygame.K_LEFT, pygame.K_a):
            self._change(-1)
        elif k in (pygame.K_RIGHT, pygame.K_d):
            self._change(+1)
        elif k == pygame.K_RETURN:
            cfg.save()
            sounds.play("score")
            return "MENU"

        # clamp selection in case rows shrank (e.g. left CUSTOM scheme)
        self.sel = min(self.sel, len(self.rows) - 1)
        return None

    def _change(self, d: int):
        sounds.play("blip")
        rows = self.rows
        if self.sel >= len(rows):
            return
        _, attr = rows[self.sel]

        if attr == "scheme":
            i = SCHEME_NAMES.index(cfg.scheme)
            cfg.scheme = SCHEME_NAMES[(i + d) % len(SCHEME_NAMES)]

        elif attr == "difficulty":
            i = DIFFICULTY_NAMES.index(cfg.difficulty)
            cfg.difficulty = DIFFICULTY_NAMES[(i + d) % len(DIFFICULTY_NAMES)]

        elif attr == "volume":
            cfg.volume = max(0.0, min(1.0, cfg.volume + d * 0.05))
            cfg.apply_volume()

        elif attr == "resolution":
            i = RESOLUTION_NAMES.index(cfg.resolution)
            new = RESOLUTION_NAMES[(i + d) % len(RESOLUTION_NAMES)]
            if new != cfg.resolution:
                cfg.resolution = new
                self._res_warn = 240   # show warning for ~4 s at 60 fps

        elif attr in ("p1_color", "p2_color", "ball_color", "bg_color"):
            target = attr.replace("_color", "")   # "p1" / "p2" / "ball" / "bg"
            cfg.cycle_custom_color(target, d)

    # ── draw ─────────────────────────────────────────────────────────────────

    def draw(self):
        surf = self.screen
        surf.fill(cfg.bg_color)
        self.tick         += 1
        self.preview_tick += 1
        if self._res_warn > 0:
            self._res_warn -= 1
        self._draw_grid()

        # ── header ───────────────────────────────────────────────────────────
        title = self.font_title.render("⚙  SETTINGS", True, cfg.p1_color)
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 44)))
        pygame.draw.line(surf, BORDER, (WIDTH//2 - 220, 66), (WIDTH//2 + 220, 66), 1)

        # live preview mini-court
        self._draw_preview(surf, pygame.Rect(WIDTH - 196, 10, 178, 52))

        # ── panel ────────────────────────────────────────────────────────────
        rows = self.rows
        total_h = sum(self._ROW_H.get(attr, 60) for _, attr in rows) + 24
        panel_h = min(total_h, HEIGHT - 110)
        panel   = pygame.Rect(WIDTH//2 - 350, 74, 700, panel_h)
        _draw_panel_bg(surf, panel)

        y = panel.top + 12
        for i, (label, attr) in enumerate(rows):
            rh = self._ROW_H.get(attr, 60)
            self._draw_row(surf, i, label, attr, y, panel, rh)
            y += rh

        # ── hints ────────────────────────────────────────────────────────────
        hints = [("W/S  ↑↓", "select row"), ("A/D  ←→", "change value"), ("ENTER / ESC", "save & back")]
        hx = WIDTH//2 - 300
        hy = panel.bottom + 12
        for key_str, desc in hints:
            ks = self.font_sm.render(key_str, True, cfg.p1_color)
            ds = self.font_sm.render(f"  {desc}", True, GRAY)
            surf.blit(ks, (hx, hy))
            surf.blit(ds, (hx + ks.get_width(), hy))
            hx += 210

        # ── restart warning ───────────────────────────────────────────────────
        if self._res_warn > 0:
            alpha_frac = min(1.0, self._res_warn / 60)
            col = tuple(int(c * alpha_frac) for c in YELLOW)
            msg = self.font_sm.render(
                f"⚠  Resolution will be applied on next launch  ({cfg.resolution})", True, col
            )
            surf.blit(msg, msg.get_rect(center=(WIDTH//2, panel.bottom + 30)))

    # ── row renderer ─────────────────────────────────────────────────────────

    def _draw_row(self, surf: pygame.Surface, idx: int, label: str, attr: str,
                  ry: int, panel: pygame.Rect, rh: int):
        active = (idx == self.sel)
        is_sub = attr in ("p1_color", "p2_color", "ball_color", "bg_color")

        # highlight background
        row_rect = pygame.Rect(panel.left + 8, ry, panel.width - 16, rh - 4)
        if active:
            pygame.draw.rect(surf, _dim(cfg.p1_color, 0.13), row_rect, border_radius=8)
            pygame.draw.rect(surf, _dim(cfg.p1_color, 0.5),  row_rect, 1, border_radius=8)

        # label
        indent = panel.left + (48 if is_sub else 24)
        lbl_col = cfg.p1_color if active else (_dim(cfg.p1_color, 0.55) if is_sub else GRAY)
        lbl = self.font_lbl.render(label.strip(), True, lbl_col)
        surf.blit(lbl, (indent, ry + 4))

        # control widget — positioned below the label
        wy = ry + 22
        if   attr == "scheme":     self._draw_scheme_picker  (surf, panel, wy)
        elif attr == "resolution": self._draw_resolution_picker(surf, panel, wy)
        elif attr == "difficulty": self._draw_difficulty_picker(surf, panel, wy)
        elif attr == "volume":     self._draw_volume_bar      (surf, panel, wy)
        elif is_sub:
            target = attr.replace("_color", "")
            self._draw_color_picker(surf, panel, wy, target)

    # ── individual widgets ────────────────────────────────────────────────────

    def _draw_scheme_picker(self, surf: pygame.Surface, panel: pygame.Rect, y: int):
        sw, gap = 72, 8
        total   = len(SCHEME_NAMES) * sw + (len(SCHEME_NAMES) - 1) * gap
        sx      = panel.left + (panel.width - total) // 2

        for i, name in enumerate(SCHEME_NAMES):
            if name == "CUSTOM":
                c1 = cfg.get_custom_color("p1")
                c2 = cfg.get_custom_color("p2")
            else:
                c1, c2 = SCHEMES[name]["p1"], SCHEMES[name]["p2"]

            rect = pygame.Rect(sx + i * (sw + gap), y, sw, 20)
            # gradient fill
            for px in range(sw):
                pygame.draw.line(surf, _lerp_col(c1, c2, px / sw),
                                 (rect.x + px, rect.y), (rect.x + px, rect.bottom))

            selected = (name == cfg.scheme)
            pygame.draw.rect(surf, WHITE if selected else BORDER,
                             rect, 2 if selected else 1, border_radius=4)
            nl = self.font_sm.render(name, True, WHITE if selected else GRAY)
            surf.blit(nl, nl.get_rect(center=(rect.centerx, rect.bottom + 9)))

    def _draw_color_picker(self, surf: pygame.Surface, panel: pygame.Rect,
                           y: int, target: str):
        sw, gap = 26, 5
        sx = panel.left + 52
        current = cfg.get_custom_color(target)

        for i, col in enumerate(COLOR_PALETTE):
            rect = pygame.Rect(sx + i * (sw + gap), y, sw, 20)
            pygame.draw.rect(surf, col, rect, border_radius=4)
            selected = (col == current)
            border_col = WHITE if selected else (50, 50, 70)
            pygame.draw.rect(surf, border_col, rect, 2 if selected else 1, border_radius=4)
            if selected:
                # small tick
                cx, cy = rect.centerx, rect.bottom + 6
                pygame.draw.circle(surf, WHITE, (cx, cy), 3)

        # large swatch showing current pick
        bx = sx + len(COLOR_PALETTE) * (sw + gap) + 8
        big = pygame.Rect(bx, y, 36, 20)
        pygame.draw.rect(surf, current, big, border_radius=4)
        pygame.draw.rect(surf, WHITE, big, 1, border_radius=4)

    def _draw_difficulty_picker(self, surf: pygame.Surface, panel: pygame.Rect, y: int):
        bw, gap = 108, 10
        sx = panel.left + 24
        diff_cols  = {
            "EASY":   (0,   220, 100),
            "NORMAL": (255, 214,  10),
            "HARD":   (255, 100,  30),
            "INSANE": (255,  30,  80),
        }
        diff_descs = {
            "EASY":   "big paddle / slow ball",
            "NORMAL": "balanced",
            "HARD":   "small paddle / fast",
            "INSANE": "good luck",
        }
        for i, name in enumerate(DIFFICULTY_NAMES):
            sel  = (name == cfg.difficulty)
            col  = diff_cols[name]
            rect = pygame.Rect(sx + i * (bw + gap), y, bw, 26)
            pygame.draw.rect(surf, _dim(col, 0.25) if sel else GRAY_DARK, rect, border_radius=7)
            pygame.draw.rect(surf, col if sel else BORDER, rect, 2 if sel else 1, border_radius=7)
            txt = self.font_val.render(name, True, col if sel else GRAY)
            surf.blit(txt, txt.get_rect(center=rect.center))

        desc = self.font_sm.render(diff_descs.get(cfg.difficulty, ""), True, GRAY)
        surf.blit(desc, (sx, y + 32))

    def _draw_resolution_picker(self, surf: pygame.Surface, panel: pygame.Rect, y: int):
        rw, gap = 86, 10
        sx = panel.left + 24
        res_cols = {
            "720p":  (100, 180, 255),
            "1080p": (  0, 245, 212),
            "1440p": (255, 200,   0),
            "4K":    (247,  37, 133),
        }
        for i, name in enumerate(RESOLUTION_NAMES):
            sel  = (name == cfg.resolution)
            col  = res_cols[name]
            rect = pygame.Rect(sx + i * (rw + gap), y, rw, 26)
            pygame.draw.rect(surf, _dim(col, 0.25) if sel else GRAY_DARK, rect, border_radius=7)
            pygame.draw.rect(surf, col if sel else BORDER, rect, 2 if sel else 1, border_radius=7)
            txt = self.font_val.render(name, True, col if sel else GRAY)
            surf.blit(txt, txt.get_rect(center=rect.center))

        # pixel-dimension hint beside the buttons
        w, h   = RESOLUTIONS[cfg.resolution]
        suffix = "  ⚠ restart to apply" if self._res_warn > 0 else ""
        info   = self.font_sm.render(f"{w} × {h}{suffix}", True,
                                     YELLOW if self._res_warn > 0 else GRAY)
        ix = sx + len(RESOLUTION_NAMES) * (rw + gap) + 8
        surf.blit(info, (ix, y + 6))

    def _draw_volume_bar(self, surf: pygame.Surface, panel: pygame.Rect, y: int):
        bw = panel.width - 72
        bx = panel.left + 24
        bh = 16

        # track
        pygame.draw.rect(surf, GRAY_DARK, pygame.Rect(bx, y + 3, bw, bh), border_radius=8)

        # fill — green → p1_color
        fill_w = int(bw * cfg.volume)
        if fill_w > 0:
            col = _lerp_col((0, 180, 100), cfg.p1_color, cfg.volume)
            pygame.draw.rect(surf, col, pygame.Rect(bx, y + 3, fill_w, bh), border_radius=8)

        # knob
        kx = bx + fill_w
        ky = y + 3 + bh // 2
        pygame.draw.circle(surf, WHITE,        (kx, ky), 9)
        pygame.draw.circle(surf, cfg.p1_color, (kx, ky), 6)

        pct = self.font_val.render(f"{int(cfg.volume * 100):3d}%", True, WHITE)
        surf.blit(pct, (bx + bw + 10, y + 1))

    # ── animated mini preview ─────────────────────────────────────────────────

    def _draw_preview(self, surf: pygame.Surface, rect: pygame.Rect):
        # bg
        pygame.draw.rect(surf, cfg.bg_color, rect, border_radius=7)
        pygame.draw.rect(surf, BORDER,       rect, 1, border_radius=7)

        # animated ball
        t  = self.preview_tick * 0.045
        bx = rect.left + int((math.sin(t)        * 0.38 + 0.5) * rect.width)
        by = rect.top  + int((math.cos(t * 0.71) * 0.38 + 0.5) * rect.height)
        bx = max(rect.left + 8,  min(rect.right  - 8,  bx))
        by = max(rect.top  + 8,  min(rect.bottom - 8,  by))

        ph = 15
        # left paddle
        pygame.draw.rect(surf, cfg.p1_color,
                         pygame.Rect(rect.left + 4, by - ph//2, 3, ph), border_radius=2)
        # right paddle
        pygame.draw.rect(surf, cfg.p2_color,
                         pygame.Rect(rect.right - 7, rect.centery - ph//2, 3, ph), border_radius=2)
        # centre line
        pygame.draw.line(surf, BORDER,
                         (rect.centerx, rect.top + 3), (rect.centerx, rect.bottom - 3), 1)
        # ball
        pygame.draw.circle(surf, cfg.ball_color, (bx, by), 4)

    # ── background grid ───────────────────────────────────────────────────────

    def _draw_grid(self):
        col = _dim(cfg.p1_color, 0.055)
        for x in range(0, WIDTH, 60):
            pygame.draw.line(self.screen, col, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 60):
            pygame.draw.line(self.screen, col, (0, y), (WIDTH, y))
