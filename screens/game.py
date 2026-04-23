# ── screens/game.py ──────────────────────────────────────────────────────────

import pygame, math, random
from settings import *
from components.ball    import Ball
from components.paddle  import Paddle
from components.effects import (
    ParticleManager, ScreenShake, FlashOverlay,
    draw_court, draw_speed_bar,
)
from assets.sounds.generate import sounds

# court vertical bounds (leave room for HUD)
HUD_H    = 70
COURT_T  = HUD_H
COURT_B  = HEIGHT - 20


class GameScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen

        self.font_score  = pygame.font.SysFont(FONT_MONO, 48, bold=True)
        self.font_mid    = pygame.font.SysFont(FONT_MONO, 22, bold=True)
        self.font_sm     = pygame.font.SysFont(FONT_MONO, 13)
        self.font_count  = pygame.font.SysFont(FONT_MONO, 72, bold=True)

        self.particles = ParticleManager()
        self.shake     = ScreenShake()
        self.flash     = FlashOverlay()

        self._reset_round()
        self.p_score = 0
        self.ai_score = 0
        self.lives    = LIVES

    # ── public API ───────────────────────────────────────────────────────────
    def reset_full(self):
        self.p_score  = 0
        self.ai_score = 0
        self.lives    = LIVES
        self._reset_round()

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "MENU"
        return None

    def update(self) -> str | None:
        """Returns 'GAME_OVER' when the game ends, else None."""
        self.tick += 1

        # ── countdown ────────────────────────────────────────────────────────
        if self.countdown > 0:
            self.countdown_timer += 1
            if self.countdown_timer >= FPS * 0.75:
                self.countdown_timer = 0
                if self.countdown == 1:
                    sounds.play("count_hi")
                else:
                    sounds.play("count_lo")
                self.countdown -= 1
            return None

        # ── ball movement ─────────────────────────────────────────────────────
        wall_event = self.ball.update(COURT_T, COURT_B)
        if wall_event:
            sounds.play("wall")
            self.particles.burst(self.ball.x, self.ball.y, GRAY, n=6)
            self.shake.trigger(2, 5)

        # ── player paddle ─────────────────────────────────────────────────────
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys, COURT_T, COURT_B)

        # ── AI paddle ────────────────────────────────────────────────────────
        self.ai.ai_move(self.ball.y, COURT_T, COURT_B)

        # ── collisions ───────────────────────────────────────────────────────
        self._check_paddle_collision(self.player, is_left=True)
        self._check_paddle_collision(self.ai,     is_left=False)

        # ── scoring ──────────────────────────────────────────────────────────
        if self.ball.x < 0:
            self._point_scored(player_scored=False)
        elif self.ball.x > WIDTH:
            self._point_scored(player_scored=True)

        # ── win check ────────────────────────────────────────────────────────
        if self.p_score >= WINNING_SCORE or self.lives <= 0:
            sounds.play("gameover")
            return "GAME_OVER"

        return None

    def draw(self):
        surf   = self.screen
        ox, oy = self.shake.get_offset()

        # background
        surf.fill(BLACK)
        game_surf = surf
        if ox or oy:
            game_surf = pygame.Surface((WIDTH, HEIGHT))
            game_surf.fill(BLACK)

        draw_court(game_surf, COURT_T, COURT_B)

        self.player.draw(game_surf)
        self.ai.draw(game_surf)
        self.ball.draw(game_surf)
        self.particles.update_draw(game_surf)
        self.flash.update_draw(game_surf)
        self._draw_hud(game_surf)

        if ox or oy:
            surf.blit(game_surf, (ox, oy))

        # countdown overlay drawn on top (no shake)
        if self.countdown > 0:
            self._draw_countdown()

    # ── internals ────────────────────────────────────────────────────────────
    def _reset_round(self, direction: int = 1):
        self.ball     = Ball()
        self.player   = Paddle("left")
        self.ai       = Paddle("right")
        self.tick     = 0
        self.countdown      = 3
        self.countdown_timer = 0

    def _check_paddle_collision(self, paddle: Paddle, is_left: bool):
        b = self.ball
        if not b.rect.colliderect(paddle.rect):
            return
        # only register if ball moving toward the paddle
        if is_left  and b.vx > 0: return
        if not is_left and b.vx < 0: return

        b.bounce_off_paddle(paddle.rect, is_left)
        paddle.flash()
        sounds.paddle(b.speed_factor)

        col = CYAN if is_left else PINK
        self.particles.burst(b.x, b.y, col, n=16)
        self.flash.trigger(col, alpha=60)
        self.shake.trigger(4 + int(b.speed_factor * 2), 8)

    def _point_scored(self, player_scored: bool):
        sounds.play("score")
        if player_scored:
            self.p_score += 1
            col = CYAN
        else:
            self.lives   -= 1
            col = PINK

        self.particles.burst(WIDTH // 2, HEIGHT // 2, col, n=30)
        self.flash.trigger(col, alpha=120)
        self.shake.trigger(8, 16)

        direction = 1 if not player_scored else -1
        self._respawn_ball(direction)

    def _respawn_ball(self, direction: int):
        self.ball = Ball()
        self.ball.reset(direction)
        self.countdown       = 3
        self.countdown_timer = 0

    def _draw_hud(self, surf: pygame.Surface):
        # HUD background strip
        hud_rect = pygame.Rect(0, 0, WIDTH, HUD_H - 4)
        pygame.draw.rect(surf, DARK, hud_rect)
        pygame.draw.line(surf, BORDER, (0, HUD_H - 4), (WIDTH, HUD_H - 4), 1)

        # player score (left)
        ps = self.font_score.render(str(self.p_score).zfill(2), True, CYAN)
        surf.blit(ps, (WIDTH // 4 - ps.get_width() // 2, 6))

        # ai score (right)
        ai = self.font_score.render(str(self.ai_score).zfill(2), True, PINK)
        surf.blit(ai, (3 * WIDTH // 4 - ai.get_width() // 2, 6))

        # labels
        pl = self.font_sm.render("PLAYER", True, CYAN_DIM)
        cp = self.font_sm.render("CPU",    True, PINK_DIM)
        surf.blit(pl, (WIDTH // 4  - pl.get_width() // 2, 56))
        surf.blit(cp, (3*WIDTH // 4 - cp.get_width() // 2, 56))

        # lives (hearts)
        hearts = "♥ " * self.lives + "♡ " * (LIVES - self.lives)
        hrt = self.font_sm.render(hearts.strip(), True, PINK)
        surf.blit(hrt, (WIDTH // 2 - hrt.get_width() // 2, 10))

        # speed bar (centre bottom of HUD)
        draw_speed_bar(
            surf, self.font_sm, self.ball.speed_factor,
            x=WIDTH // 2 - 90, y=38, w=180,
        )

        # ESC hint
        esc = self.font_sm.render("ESC menu", True, GRAY_DARK)
        surf.blit(esc, (WIDTH - esc.get_width() - 10, HEIGHT - 18))

    def _draw_countdown(self):
        surf = self.screen
        num  = str(self.countdown) if self.countdown > 0 else "GO!"
        col  = YELLOW
        txt  = self.font_count.render(num, True, col)
        # glow
        glow = pygame.Surface((txt.get_width() + 40, txt.get_height() + 40), pygame.SRCALPHA)
        glow.fill((0,0,0,0))
        for r in range(20, 0, -4):
            a = max(0, 60 - r * 3)
            pygame.draw.rect(
                glow, (*col, a),
                (20 - r, 20 - r, txt.get_width() + r*2, txt.get_height() + r*2),
                border_radius=12,
            )
        surf.blit(glow, (WIDTH // 2 - txt.get_width() // 2 - 20,
                         HEIGHT // 2 - txt.get_height() // 2 - 20))
        surf.blit(txt,  txt.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    @property
    def final_score(self) -> dict:
        return {
            "player": self.p_score,
            "cpu":    self.ai_score,
            "lives":  self.lives,
            "speed":  round(self.ball.speed_factor, 1),
            "points": self.p_score * 1000 + self.lives * 200,
        }
