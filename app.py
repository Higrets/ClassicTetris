"""
Приложение: инициализация pygame, контекст экранов и главный цикл
переключения «меню ↔ игра». Всё остальное lives в слоях core/ui/data.
"""

import pygame

from config.settings import APP_TITLE, FPS, WINDOW_H, WINDOW_W
from data.highscores import load_high_scores
from ui.background import BackgroundFX
from ui.fonts import build_fonts
from ui.screens.base import AppContext
from ui.screens.gameplay import GameScreen
from ui.screens.menu import MainMenu


class App:
    def __init__(self):
        pygame.display.set_caption(APP_TITLE)
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock = pygame.time.Clock()
        self.bg = BackgroundFX(WINDOW_W, WINDOW_H)
        self.ctx = AppContext(screen=self.screen, fonts=build_fonts(),
                              bg=self.bg, clock=self.clock,
                              high_scores=load_high_scores)
        self.menu = MainMenu(self.ctx)

    # ---------- цикл меню ----------
    def run_menu(self):
        menu = self.menu
        while menu.next_action in ("menu", "records", "controls"):
            dt = self.clock.tick(FPS) / 1000.0
            self.bg.update(dt)
            menu.update(dt)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                menu.handle_event(event)
            menu.render()
            pygame.display.flip()
        return menu.next_action          # 'play' | 'quit'

    # ---------- главный цикл ----------
    def run(self):
        while True:
            action = self.run_menu()
            if action == "quit":
                return
            if action == "play":
                game = GameScreen(self.ctx)
                result = game.run()
                if result == "quit":
                    return
                self.menu.restart()


def main():
    pygame.init()
    try:
        App().run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
