"""
Рендер эффектов поверх игрового поля: частицы, ударные волны, надписи.

Принимает EffectsManager из слоя effects и конвертирует его «клеточные»
координаты в пиксели. Никакой логики симуляции здесь нет — только отрисовка.
"""

import random

import pygame

from config.settings import BOARD_H, BOARD_W, CELL
from effects.manager import FLOATER_LIFE, WAVE_LIFE
from utils.mathx import ease_out_cubic


def render_effects(screen, fx, board_pos, fonts):
    """fx — EffectsManager; board_pos — (x, y) левого верха поля в пикселях."""
    mid = fonts[1]
    bx, by = board_pos
    psurf = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
    # частицы
    for p in fx.particles:
        t = p.life / p.max_life
        alpha = int(255 * t)
        s = max(1, int(p.size * t))
        px = p.x * CELL - s / 2
        py = p.y * CELL - s / 2
        pygame.draw.rect(psurf, (*p.color, alpha), (int(px), int(py), s, s))
    # ударные волны
    for w in fx.shockwaves:
        t = w["age"] / WAVE_LIFE
        radius = ease_out_cubic(t) * BOARD_W * 0.85 * w["power"]
        if radius < 2:
            continue
        alpha = int(200 * (1 - t))
        r = pygame.Rect(0, 0, int(radius * 2), int(radius * 2))
        r.center = (int(w["x"] * CELL), int(w["y"] * CELL))
        pygame.draw.ellipse(psurf, (*w["color"], alpha), r,
                            width=max(1, int(4 * (1 - t))))
    screen.blit(psurf, (bx, by))
    # всплывающие надписи
    for f in fx.floaters:
        t = f["age"] / FLOATER_LIFE
        alpha = int(255 * (1 - t) ** 1.5)
        scale = 1.0 + 0.35 * (1 - min(1.0, f["age"] * 4))
        txt = mid.render(f["text"], True, f["color"])
        if abs(scale - 1) > 0.02:
            txt = pygame.transform.smoothscale(
                txt, (max(1, int(txt.get_width() * scale)),
                      max(1, int(txt.get_height() * scale))))
        txt.set_alpha(alpha)
        rect = txt.get_rect(center=(bx + f["x"] * CELL, by + f["y"] * CELL))
        screen.blit(txt, rect)


def apply_shake(screen, scene, shake):
    """Копирует сцену на экран со случайным смещением (тряска экрана)."""
    if shake > 0.2:
        ox = random.uniform(-shake, shake)
        oy = random.uniform(-shake, shake)
        screen.fill((20, 20, 30))
        screen.blit(scene, (ox, oy))
    else:
        screen.blit(scene, (0, 0))
