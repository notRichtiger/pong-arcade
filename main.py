#!/usr/bin/env python3
# ── main.py ──────────────────────────────────────────────────────────────────
"""PONG — Arcade Reborn  |  main entry point & game-state machine."""

import sys, os

import pygame
from settings import *
from settings_manager import cfg
from assets.sounds.generate import sounds
from screens.menu            import MenuScreen
from screens.game            import GameScreen
from screens.scoreboard      import ScoreboardScreen, save_score, load_scores
from screens.gameover        import GameOverScreen
from screens.settings_screen import SettingsScreen


def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    screen = pygame.display.set_mode(cfg.get_resolution())
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()

    # init sounds (must be after mixer.init)
    sounds.init()

    # build all screens
    menu_screen     = MenuScreen(screen)
    game_screen     = GameScreen(screen)
    sb_screen       = ScoreboardScreen(screen)
    go_screen       = GameOverScreen(screen)
    settings_screen = SettingsScreen(screen)

    state        = "MENU"   # MENU | GAME | SCOREBOARD | GAME_OVER | SETTINGS | QUIT
    pending_rank = -1

    while state != "QUIT":
        clock.tick(FPS)

        # ── event pump ───────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                state = "QUIT"
                break

            if state == "MENU":
                action = menu_screen.handle_event(event)
                if action == "START GAME":
                    game_screen.reset_full()
                    state = "GAME"
                elif action == "SETTINGS":
                    state = "SETTINGS"
                elif action == "SCOREBOARD":
                    sb_screen.refresh()
                    state = "SCOREBOARD"
                elif action == "EXIT":
                    state = "QUIT"

            elif state == "SETTINGS":
                action = settings_screen.handle_event(event)
                if action == "MENU":
                    if cfg.pending_resize:
                        screen = pygame.display.set_mode(cfg.get_resolution())
                        cfg.pending_resize = False
                    state = "MENU"

            elif state == "GAME":
                action = game_screen.handle_event(event)
                if action == "MENU":
                    state = "MENU"

            elif state == "SCOREBOARD":
                action = sb_screen.handle_event(event)
                if action == "MENU":
                    state = "MENU"

            elif state == "GAME_OVER":
                action = go_screen.handle_event(event)
                if action is None:
                    pass
                elif isinstance(action, tuple) and action[0] == "SAVE":
                    _, name = action
                    stats = go_screen.stats
                    rank  = save_score(name, stats["points"], stats["speed"])
                    pending_rank = rank
                elif action == "RETRY":
                    game_screen.reset_full()
                    state = "GAME"
                elif action == "SCOREBOARD":
                    sb_screen.refresh(highlight_rank=pending_rank)
                    state = "SCOREBOARD"
                elif action == "EXIT":
                    state = "QUIT"

        if state == "QUIT":
            break

        # ── update ───────────────────────────────────────────────────────────
        if state == "GAME":
            result = game_screen.update()
            if result == "GAME_OVER":
                go_screen.set_stats(game_screen.final_score)
                state = "GAME_OVER"

        # ── draw ─────────────────────────────────────────────────────────────
        if state == "MENU":
            scores  = load_scores()
            best_hs = scores[0]["points"] if scores else 0
            menu_screen.draw(highscore=best_hs)

        elif state == "SETTINGS":
            settings_screen.draw()

        elif state == "GAME":
            game_screen.draw()

        elif state == "SCOREBOARD":
            sb_screen.draw()

        elif state == "GAME_OVER":
            go_screen.draw()

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
