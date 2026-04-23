# ── assets/sounds/generate.py ───────────────────────────────────────────────
"""Procedurally generate all game sounds with numpy → pygame Sound objects."""

import numpy as np
import pygame

_RATE = 44100   # sample rate

def _make_buf(samples: np.ndarray) -> pygame.sndarray.make_sound:
    """Convert float32 array (‑1…1) to a stereo pygame Sound."""
    arr = np.clip(samples, -1.0, 1.0)
    # stereo: duplicate channel
    stereo = np.column_stack((arr, arr))
    buf = (stereo * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(buf)


def _envelope(n: int, attack: float = 0.01, release: float = 0.3) -> np.ndarray:
    env = np.ones(n)
    a = int(n * attack)
    r = int(n * release)
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if r > 0 and r <= n:
        env[n - r:] *= np.linspace(1, 0, r)
    return env


def _sine(freq: float, dur: float) -> np.ndarray:
    t = np.linspace(0, dur, int(_RATE * dur), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def _square(freq: float, dur: float, duty: float = 0.5) -> np.ndarray:
    t = np.linspace(0, dur, int(_RATE * dur), endpoint=False)
    phase = (t * freq) % 1.0
    return np.where(phase < duty, 1.0, -1.0).astype(np.float32)


# ── Individual sounds ────────────────────────────────────────────────────────

def make_paddle_hit(speed_factor: float = 1.0) -> pygame.mixer.Sound:
    """Short bip whose pitch rises with ball speed (speed_factor 1‒3)."""
    freq = 220 + int(speed_factor * 180)   # 220 Hz … 760 Hz
    dur  = 0.07
    n    = int(_RATE * dur)
    wave = _sine(freq, dur) * 0.6 + _square(freq * 2, dur, 0.3) * 0.25
    wave *= _envelope(n, attack=0.005, release=0.5)
    return _make_buf(wave)


def make_wall_hit() -> pygame.mixer.Sound:
    """Lower, softer thud for wall/ceiling bounces."""
    dur = 0.06
    n   = int(_RATE * dur)
    wave = _sine(110, dur) * 0.5 + _square(55, dur, 0.4) * 0.25
    wave *= _envelope(n, attack=0.003, release=0.6)
    return _make_buf(wave)


def make_score() -> pygame.mixer.Sound:
    """Quick ascending arpeggio on score."""
    freqs = [261.63, 329.63, 392.00, 523.25]   # C4 E4 G4 C5
    dur_each = 0.09
    parts = []
    for f in freqs:
        n    = int(_RATE * dur_each)
        seg  = _sine(f, dur_each) * _envelope(n, release=0.4)
        parts.append(seg)
    wave = np.concatenate(parts)
    return _make_buf(wave * 0.7)


def make_game_over() -> pygame.mixer.Sound:
    """Descending chromatic glide — game-over feel."""
    dur  = 0.9
    n    = int(_RATE * dur)
    t    = np.linspace(0, dur, n, endpoint=False)
    freq = np.linspace(440, 110, n)          # glide 440→110 Hz
    phase = np.cumsum(2 * np.pi * freq / _RATE)
    wave  = np.sin(phase) * 0.55
    wave += np.sin(phase * 0.5) * 0.25      # sub-octave warmth
    wave *= _envelope(n, attack=0.02, release=0.45)
    return _make_buf(wave)


def make_menu_blip() -> pygame.mixer.Sound:
    """Tiny UI tick for menu navigation."""
    dur = 0.04
    n   = int(_RATE * dur)
    wave = _sine(660, dur) * _envelope(n, release=0.7) * 0.4
    return _make_buf(wave)


def make_countdown_beep(high: bool = False) -> pygame.mixer.Sound:
    """3-2-1 countdown beep; high=True for the final 'go' beep."""
    freq = 880 if high else 440
    dur  = 0.15
    n    = int(_RATE * dur)
    wave = _sine(freq, dur) * _envelope(n, release=0.5) * 0.55
    return _make_buf(wave)


# ── Sound manager ────────────────────────────────────────────────────────────

class SoundManager:
    """Lazy-init sound cache; call .init() after pygame.mixer.init()."""

    def __init__(self):
        self._ready   = False
        self.wall     = None
        self.score    = None
        self.gameover = None
        self.blip     = None
        self._paddles: dict[int, pygame.mixer.Sound] = {}

    def init(self):
        pygame.mixer.set_num_channels(16)
        self.wall     = make_wall_hit()
        self.score    = make_score()
        self.gameover = make_game_over()
        self.blip     = make_menu_blip()
        self.count_lo = make_countdown_beep(False)
        self.count_hi = make_countdown_beep(True)
        # pre-bake a range of paddle pitches (speed 1 … 3 in 0.1 steps)
        for i in range(10, 31):
            sf = i / 10.0
            self._paddles[i] = make_paddle_hit(sf)
        self._ready = True

    def paddle(self, speed_factor: float = 1.0):
        if not self._ready:
            return
        key = max(10, min(30, round(speed_factor * 10)))
        snd = self._paddles.get(key) or self._paddles[10]
        snd.play()

    def play(self, name: str):
        if not self._ready:
            return
        snd = getattr(self, name, None)
        if snd:
            snd.play()


sounds = SoundManager()
