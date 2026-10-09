"""
Правая панель HUD (счёт, уровень, hold, next, подсказки) и оверлеи
паузы / Game Over. Чистый визуал: читает состояние game, ничего не меняет.
"""

import math

import pygame

from config.settings import (ACCENT, BOARD_H, BOARD_W, CELL, GOLD,
                             SIDE_PANEL_W, TEXT_COLOR)
from ui.colors import with_alpha
from ui.sprites import draw_mini_piece
from utils.mathx import ease_out_cubic, lerp_color


def render_hud(screen, game, fonts, time):
    """Рисует правую панель и поверх — оверлеи паузы/Game Over."""
    big, mid, small = fonts
    bx, by = CELL, CELL
    px = bx + BOARD_W + CELL // 2

    panel_rect = pygame.Rect(px - CELL // 2, by, SIDE_PANEL_W, BOARD_H)
    panel_bg = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
    panel_bg.fill((28, 28, 46, 235))
    screen.blit(panel_bg, panel_rect.topleft)
    pygame.draw.rect(screen, (70, 70, 100), panel_rect, 2, border_radius=8)

    label_score = small.render("СЧЁТ", True, (150, 150, 175))
    screen.blit(label_score, (px + 6, by + 10))
    score_s = mid.render(str(game.score), True, GOLD)
    screen.blit(score_s, (px + 6, by + 30))

    label_level = small.render(f"УРОВЕНЬ: {game.level}", True, ACCENT)
    screen.blit(label_level, (px + 6, by + 68))
    label_lines = small.render(f"ЛИНИИ: {game.lines}", True, TEXT_COLOR)
    screen.blit(label_lines, (px + 6, by + 90))

    hold_label = small.render("УДЕРЖАНИЕ (C)", True, (150, 150, 175))
    screen.blit(hold_label, (px + 6, by + 128))
    hold_box = pygame.Rect(px + 6, by + 150, SIDE_PANEL_W - 16, 2 * 20 + 8)
    pygame.draw.rect(screen, (20, 20, 34), hold_box, border_radius=6)
    draw_mini_piece(screen, (px + 12, by + 154), game.hold, cell=20)
    if not game.can_hold and game.hold is not None:
        dim = pygame.Surface(hold_box.size, pygame.SRCALPHA)
        dim.fill((8, 8, 14, 150))
        screen.blit(dim, hold_box.topleft)

    next_label = small.render("СЛЕДУЮЩИЕ", True, (150, 150, 175))
    screen.blit(next_label, (px + 6, by + 228))
    for i, kind in enumerate(game.next_queue):
        box = pygame.Rect(px + 6, by + 250 + i * 70,
                          SIDE_PANEL_W - 16, 2 * 20 + 8)
        pygame.draw.rect(screen, (20, 20, 34), box, border_radius=6)
        draw_mini_piece(screen, (px + 12, by + 254 + i * 70), kind, cell=20)
        if i == 0:
            a = int(120 + 80 * (0.5 + 0.5 * math.sin(time * 3)))
            pygame.draw.rect(screen, with_alpha(ACCENT, a), box, 1,
                             border_radius=6)

    hints = ["← → : движение", "↓ : мягкое падение", "Пробел : сброс",
             "↑ / X : поворот", "Z : поворот назад", "C : удержание",
             "P : пауза", "R : рестарт", "ESC : меню"]
    for i, h in enumerate(hints):
        t = small.render(h, True, (130, 130, 155))
        screen.blit(t, (px + 6, by + BOARD_H - 185 + i * 19))

    # ------- оверлеи -------
    if game.paused and not game.game_over:
        _draw_pause(screen, fonts, bx, by, time)
    if game.game_over:
        _draw_game_over(screen, game, fonts, bx, by, time)


def _draw_pause(screen, fonts, bx, by, time):
    big, mid, small = fonts
    overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (bx, by))
    breathe = 0.5 + 0.5 * math.sin(time * 3)
    t = big.render("ПАУЗА", True,
                   lerp_color((255, 255, 255), ACCENT, breathe))
    screen.blit(t, t.get_rect(center=(bx + BOARD_W // 2,
                                       by + BOARD_H // 2 - 10)))
    t2 = small.render("P — продолжить", True, (180, 180, 200))
    screen.blit(t2, t2.get_rect(center=(bx + BOARD_W // 2,
                                         by + BOARD_H // 2 + 30)))


def _draw_game_over(screen, game, fonts, bx, by, time):
    big, mid, small = fonts
    # ступенчатое затемнение с красным оттенком
    dark = min(190, int(200 * ease_out_cubic(game.over_age / 0.8)))
    overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
    overlay.fill((20, 0, 10, dark))
    screen.blit(overlay, (bx, by))
    appear = ease_out_cubic(game.over_age / 0.5)
    wob = 1 + 0.03 * math.sin(time * 2.6)
    t1 = big.render("GAME OVER", True, (240, 70, 90))
    w = max(1, int(t1.get_width() * appear * wob))
    h = max(1, int(t1.get_height() * appear * wob))
    t1 = pygame.transform.smoothscale(t1, (w, h))
    cx = bx + BOARD_W // 2
    screen.blit(t1, t1.get_rect(center=(cx, by + BOARD_H // 2 - 46)))
    if game.over_age > 0.35:
        t2 = mid.render(f"Счёт: {game.score}", True, GOLD)
        screen.blit(t2, t2.get_rect(center=(cx, by + BOARD_H // 2 + 2)))
    if game.over_age > 0.55:
        t3 = small.render("R — заново · ESC — в меню", True,
                          (200, 200, 220))
        screen.blit(t3, t3.get_rect(center=(cx, by + BOARD_H // 2 + 40)))
