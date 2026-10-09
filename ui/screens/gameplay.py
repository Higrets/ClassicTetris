"""
Игровой экран: цикл партии. Композиция — core.Tetris (логика) +
effects.EffectsManager (симуляция эффектов) + ui.render_* (отрисовка).

Экран сам ничего не рисует «в лоб»: он делегирует отрисовку модулям ui,
а сохранение рекордов — слою data.
"""

import pygame

from config.settings import FPS, WINDOW_H, WINDOW_W
from core.autorepeat import HorizontalAutoRepeat
from core.game import Tetris
from data.highscores import save_high_score
from effects.manager import EffectsManager
from ui.render_board import render_board
from ui.render_effects import apply_shake
from ui.render_hud import render_hud


class GameScreen:
    def __init__(self, ctx):
        self.ctx = ctx
        self.effects = EffectsManager()
        self.game = Tetris(effects=self.effects)
        self.ar = HorizontalAutoRepeat()
        self.saved = False

    # ---------- события ----------
    def handle_event(self, event):
        game = self.game
        if event.type == pygame.KEYDOWN:
            key = event.key
            if key == pygame.K_ESCAPE:
                self._save_score()
                return "menu"
            elif key == pygame.K_r:
                # R работает всегда: и во время игры, и после Game Over
                self._save_score()
                game.reset()
                self.ar.reset()
                self.saved = False
            elif key == pygame.K_p and not game.game_over:
                game.paused = not game.paused
            elif game.game_over or game.paused:
                pass
            elif key in (pygame.K_LEFT, pygame.K_a):
                game.try_move(-1, 0)
                self.ar.press(-1)
            elif key in (pygame.K_RIGHT, pygame.K_d):
                game.try_move(1, 0)
                self.ar.press(1)
            elif key in (pygame.K_DOWN, pygame.K_s):
                game.soft_drop = True
            elif key in (pygame.K_UP, pygame.K_x):
                game.try_rotate(1)
            elif key == pygame.K_z:
                game.try_rotate(-1)
            elif key == pygame.K_SPACE:
                game.hard_drop()
            elif key == pygame.K_c:
                game.hold_piece()
        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.ar.release(-1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.ar.release(1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                game.soft_drop = False
        return None

    def _save_score(self):
        if not self.saved and self.game.score > 0:
            save_high_score(self.game.score)
            self.saved = True

    # ---------- симуляция ----------
    def update(self, dt):
        game = self.game
        self.ar.update(dt, lambda d: game.try_move(d, 0))
        game.update(dt)
        if game.game_over:
            self._save_score()

    # ---------- отрисовка ----------
    def render(self):
        time = pygame.time.get_ticks() / 1000.0
        # буфер сцены — чтобы применить тряску экрана
        scene = pygame.Surface((WINDOW_W, WINDOW_H))
        render_board(scene, self.game, self.ctx.fonts, self.ctx.bg, time)
        render_hud(scene, self.game, self.ctx.fonts, time)
        apply_shake(self.ctx.screen, scene, self.game.effects.shake)

    def run(self):
        """Локальный цикл экрана; возвращает 'menu' | 'quit'."""
        screen, clock, bg = self.ctx.screen, self.ctx.clock, self.ctx.bg
        while True:
            dt = clock.tick(FPS) / 1000.0
            bg.update(dt)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                result = self.handle_event(event)
                if result:
                    return result
            self.update(dt)
            self.render()
            pygame.display.flip()
