# ── settings_manager.py ──────────────────────────────────────────────────────
"""
Central config object.  Import `cfg` everywhere you need a setting.

All changes are persisted to user_settings.json next to this file.
"""

import json, os, pygame

_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_settings.json")

# ── Color schemes ─────────────────────────────────────────────────────────────
SCHEMES = {
    "NEON":   {"p1": (0, 245, 212),   "p2": (247, 37, 133),  "ball": (255, 214, 10),  "bg": (5, 5, 15)},
    "RETRO":  {"p1": (255, 165, 0),   "p2": (0, 200, 255),   "ball": (255, 255, 255), "bg": (10, 10, 30)},
    "PASTEL": {"p1": (180, 140, 255), "p2": (255, 180, 120), "ball": (150, 255, 200), "bg": (20, 15, 35)},
    "OCEAN":  {"p1": (0, 180, 255),   "p2": (0, 255, 180),   "ball": (255, 240, 80),  "bg": (0, 8, 28)},
    "FIRE":   {"p1": (255, 80, 20),   "p2": (255, 200, 0),   "ball": (255, 255, 255), "bg": (15, 5, 0)},
    "CUSTOM": {"p1": (0, 245, 212),   "p2": (247, 37, 133),  "ball": (255, 214, 10),  "bg": (5, 5, 15)},
}
SCHEME_NAMES = list(SCHEMES.keys())

# Palette the user cycles through in CUSTOM mode
COLOR_PALETTE = [
    (0,   245, 212),   # cyan
    (247,  37, 133),   # pink / magenta
    (255, 214,  10),   # yellow
    ( 80, 200, 255),   # sky blue
    (255,  80,  20),   # orange
    (160,  80, 255),   # purple
    ( 80, 255, 120),   # green
    (255, 255, 255),   # white
    (255, 100, 100),   # red
    (100, 100, 255),   # blue
    (255, 180, 200),   # blush
    ( 20,  20,  40),   # near-black (good for bg)
]

# ── Difficulty presets ────────────────────────────────────────────────────────
DIFFICULTIES = {
    "EASY":   {"paddle_h": 120, "ai_reaction": 0.06, "ai_speed":  4, "ball_speed_init": 5, "ball_accel": 0.15},
    "NORMAL": {"paddle_h":  90, "ai_reaction": 0.12, "ai_speed":  6, "ball_speed_init": 6, "ball_accel": 0.20},
    "HARD":   {"paddle_h":  70, "ai_reaction": 0.20, "ai_speed":  8, "ball_speed_init": 7, "ball_accel": 0.25},
    "INSANE": {"paddle_h":  55, "ai_reaction": 0.35, "ai_speed": 11, "ball_speed_init": 9, "ball_accel": 0.35},
}
DIFFICULTY_NAMES = list(DIFFICULTIES.keys())

# ── Resolutions ───────────────────────────────────────────────────────────────
RESOLUTIONS = {
    "720p":  (1280,  720),
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "4K":    (3840, 2160),
}
RESOLUTION_NAMES = list(RESOLUTIONS.keys())


# ── Config class ──────────────────────────────────────────────────────────────

class Config:
    def __init__(self):
        # defaults
        self.scheme      = "NEON"
        self.difficulty  = "NORMAL"
        self.volume      = 0.7
        self.resolution  = "1080p"

        # custom per-element colors (only used when scheme == "CUSTOM")
        self._custom: dict[str, list[int]] = {
            "p1":   list(SCHEMES["NEON"]["p1"]),
            "p2":   list(SCHEMES["NEON"]["p2"]),
            "ball": list(SCHEMES["NEON"]["ball"]),
            "bg":   list(SCHEMES["NEON"]["bg"]),
        }

        # set True when resolution is changed; main loop applies it
        self.pending_resize = False

        self.load()

    # ── Color properties ──────────────────────────────────────────────────────

    def _scheme_color(self, key: str) -> tuple:
        if self.scheme == "CUSTOM":
            return tuple(self._custom[key])
        return SCHEMES[self.scheme][key]

    @property
    def p1_color(self)   -> tuple: return self._scheme_color("p1")
    @property
    def p2_color(self)   -> tuple: return self._scheme_color("p2")
    @property
    def ball_color(self) -> tuple: return self._scheme_color("ball")
    @property
    def bg_color(self)   -> tuple: return self._scheme_color("bg")

    # ── Difficulty properties ──────────────────────────────────────────────────

    def _diff(self, key): return DIFFICULTIES[self.difficulty][key]

    @property
    def paddle_h(self)        -> int:   return self._diff("paddle_h")
    @property
    def ball_speed_init(self) -> float: return self._diff("ball_speed_init")
    @property
    def ball_accel(self)      -> float: return self._diff("ball_accel")
    @property
    def ai_reaction(self)     -> float: return self._diff("ai_reaction")
    @property
    def ai_speed(self)        -> float: return self._diff("ai_speed")

    # ── Resolution ────────────────────────────────────────────────────────────

    def get_resolution(self) -> tuple[int, int]:
        return RESOLUTIONS.get(self.resolution, (1280, 720))

    def set_resolution(self, name: str):
        if name in RESOLUTIONS and name != self.resolution:
            self.resolution = name
            self.pending_resize = True

    # ── Volume ────────────────────────────────────────────────────────────────

    def apply_volume(self):
        try:
            pygame.mixer.music.set_volume(self.volume)
            for ch in range(pygame.mixer.get_num_channels()):
                pygame.mixer.Channel(ch).set_volume(self.volume)
        except Exception:
            pass

    # ── Custom color cycling ──────────────────────────────────────────────────

    def cycle_custom_color(self, target: str, d: int):
        """Advance the palette index for target ('p1'|'p2'|'ball'|'bg') by d."""
        current = tuple(self._custom[target])
        try:
            idx = COLOR_PALETTE.index(current)
        except ValueError:
            idx = 0
        self._custom[target] = list(COLOR_PALETTE[(idx + d) % len(COLOR_PALETTE)])

    def get_custom_color(self, target: str) -> tuple:
        return tuple(self._custom[target])

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self):
        data = {
            "scheme":     self.scheme,
            "difficulty": self.difficulty,
            "volume":     round(self.volume, 3),
            "resolution": self.resolution,
            "custom":     {k: list(v) for k, v in self._custom.items()},
        }
        try:
            with open(_SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass

    def load(self):
        try:
            with open(_SETTINGS_FILE) as f:
                data = json.load(f)

            self.scheme     = data.get("scheme",     self.scheme)
            self.difficulty = data.get("difficulty", self.difficulty)
            self.volume     = float(data.get("volume", self.volume))
            self.resolution = data.get("resolution", self.resolution)

            if "custom" in data:
                for k, v in data["custom"].items():
                    if k in self._custom and isinstance(v, list) and len(v) == 3:
                        self._custom[k] = [int(c) for c in v]

            # validate
            if self.scheme     not in SCHEME_NAMES:     self.scheme     = "NEON"
            if self.difficulty not in DIFFICULTY_NAMES: self.difficulty = "NORMAL"
            if self.resolution not in RESOLUTION_NAMES: self.resolution = "1080p"
            self.volume = max(0.0, min(1.0, self.volume))

        except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError):
            pass   # stay with defaults


# ── Module-level singleton ────────────────────────────────────────────────────
cfg = Config()
