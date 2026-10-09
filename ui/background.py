"""
Анимированный фон меню/игры: градиент + туманности + звёзды + фигуры.

Классы Star / FallingPiece — мелкие визуальные сущности; BackgroundFX —
композиция всего слоя фона. Используется всеми экранами.
"""

import math
import random

import pygame

from config.settings import PIECE_COLORS
from config.shapes import SHAPES
from ui.colors import make_radial_glow, make_vgrad


class Star:
    def __init__(self, w, h):
        self.reset(w, h, first=True)

    def reset(self, w, h, first=False):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h) if first else -4
        self.r = random.uniform(0.6, 2.0)
        self.speed = random.uniform(4, 18)
        self.phase = random.uniform(0, math.tau)
        self.twinkle = random.uniform(1.2, 3.5)

    def update(self, dt, w, h):
        self.y += self.speed * dt
        if self.y > h + 4:
            self.reset(w, h)

    def draw(self, screen, t):
        a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * self.twinkle + self.phase))
        col = (int(180 * a), int(200 * a), int(255 * a))
        pygame.draw.circle(screen, col, (int(self.x), int(self.y)),
                           int(round(self.r)))


class FallingPiece:
    """Декоративная падающая фигура на фоне меню."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.reset(first=random.random() < 0.7)

    def reset(self, first=False):
        self.kind = random.choice(list(SHAPES.keys()))
        self.color = PIECE_COLORS[self.kind]
        self.cell = random.uniform(10, 22)
        self.x = random.uniform(-20, self.w)
        self.y = random.uniform(-self.h, self.h) if first else \
            random.uniform(-self.h * 0.4, -20)
        self.speed = random.uniform(22, 60)
        self.rot = random.uniform(0, math.tau)
        self.spin = random.uniform(-1.1, 1.1)
        self.alpha = random.randint(28, 60)

    def update(self, dt):
        self.y += self.speed * dt
        self.rot += self.spin * dt
        if self.y - 4 * self.cell > self.h + 40:
            self.reset()

    def draw(self, screen):
        cells = SHAPES[self.kind][0]
        side = int(5 * self.cell) + 8
        surf = pygame.Surface((side, side), pygame.SRCALPHA)
        for cx, cy in cells:
            r = pygame.Rect(int((cx + 0.5) * self.cell) + 4,
                            int((cy + 0.5) * self.cell) + 4,
                            int(self.cell), int(self.cell))
            pygame.draw.rect(surf, (*self.color, self.alpha), r,
                             border_radius=3)
            pygame.draw.rect(surf, (*self.color, min(255, self.alpha + 45)),
                             r, 1, border_radius=3)
        rotd = pygame.transform.rotate(surf, math.degrees(self.rot))
        rect = rotd.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotd, rect)


class BackgroundFX:
    """Общий анимированный фон: градиент + туманности + звёзды + фигуры."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.grad = make_vgrad((w, h), (8, 10, 24), (26, 14, 48))
        self.stars = [Star(w, h) for _ in range(70)]
        self.pieces = [FallingPiece(w, h) for _ in range(11)]
        self.nebula1 = make_radial_glow(max(w, h) // 2, (70, 30, 140), 60)
        self.nebula2 = make_radial_glow(max(w, h) // 3, (0, 120, 160), 45)
        self.time = 0.0

    def update(self, dt):
        self.time += dt
        for s in self.stars:
            s.update(dt, self.w, self.h)
        for p in self.pieces:
            p.update(dt)

    def draw(self, screen, pieces_visible=True):
        screen.blit(self.grad, (0, 0))
        t = self.time
        # дрейфующие туманности
        x1 = int(self.w * 0.25 + math.sin(t * 0.11) * 60)
        y1 = int(self.h * 0.3 + math.cos(t * 0.09) * 40)
        screen.blit(self.nebula1,
                    self.nebula1.get_rect(center=(x1, y1)),
                    special_flags=pygame.BLEND_ADD)
        x2 = int(self.w * 0.75 + math.cos(t * 0.08) * 70)
        y2 = int(self.h * 0.7 + math.sin(t * 0.12) * 50)
        screen.blit(self.nebula2,
                    self.nebula2.get_rect(center=(x2, y2)),
                    special_flags=pygame.BLEND_ADD)
        for s in self.stars:
            s.draw(screen, t)
        if pieces_visible:
            for p in self.pieces:
                p.draw(screen)
