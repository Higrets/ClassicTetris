"""pygame-хелперы для работы с цветом и поверхностями."""

import pygame

from utils.mathx import clamp, lerp, lerp_color  # noqa: F401 (реэкспорт)


def make_vgrad(size, top, bottom):
    """Вертикальный градиент."""
    w, h = size
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        surf.fill(lerp_color(top, bottom, t), (0, y, w, 1))
    return surf


def make_radial_glow(radius, color, peak_alpha=160):
    """Мягкое круглое свечение (для фона и neon-эффектов)."""
    radius = max(2, int(radius))
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    steps = 14
    for i in range(steps, 0, -1):
        t = i / steps
        alpha = int(peak_alpha * (1 - t) ** 2)
        r = max(1, int(radius * t))
        pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
    return surf


def with_alpha(color, alpha):
    """Кортеж RGB -> кортеж RGBA."""
    a = int(clamp(alpha, 0, 255))
    return (color[0], color[1], color[2], a)


def lighten(color, amount=70):
    return tuple(min(255, c + amount) for c in color)


def darken(color, amount=90):
    return tuple(max(0, c - amount) for c in color)
