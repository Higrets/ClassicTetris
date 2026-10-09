"""Базовые типы для экранов: контекст приложения и интерфейс экрана."""

from dataclasses import dataclass, field


@dataclass
class AppContext:
    """Всё, что нужно экранам: окно, шрифты, фон, часы, данные."""
    screen: object            # pygame.Surface (окно)
    fonts: tuple              # (big, mid, small)
    bg: object                # ui.background.BackgroundFX
    clock: object             # pygame.time.Clock
    high_scores: object = field(default=None)   # callable -> список очков


class Screen:
    """Интерфейс экрана. Наследники переопределяют три метода."""

    def handle_event(self, event):
        raise NotImplementedError

    def update(self, dt):
        raise NotImplementedError

    def render(self):
        raise NotImplementedError
