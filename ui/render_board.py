"""
Отрисовка игрового поля: фон, сетка, блоки, призрак, текущая фигура,
шлейф hard drop, glow-рамка. Координаты полей/окон — из config.settings.
"""

import math

import pygame

from config.settings import (ACCENT, BOARD_H, BOARD_W, CELL,
                             GHOST_ALPHA, GRID_COLOR, ROWS, SIDE_PANEL_W,
                             WINDOW_H, WINDOW_W)
from ui.colors import make_radial_glow, with_alpha
from ui.render_effects import render_effects
from ui.sprites import draw_cell
from utils.mathx import ease_out_cubic, lerp_color


def render_board(screen, game, fonts, bg, time):
    """Рисует всё игровое поле со всеми эффектами на surface `screen`."""
    bx, by = CELL, CELL  # origin игрового поля

    # приглушённый анимированный фон
    screen.blit(bg.grad, (0, 0))
    veil = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    veil.fill((8, 8, 18, 225))
    screen.blit(veil, (0, 0))

    # glow за игровым полем
    glow = make_radial_glow(BOARD_H // 2 + 60, (40, 60, 160), 70)
    screen.blit(glow, glow.get_rect(center=(bx + BOARD_W // 2,
                                            by + BOARD_H // 2)),
                special_flags=pygame.BLEND_ADD)

    # фон поля + сетка
    field_bg = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
    field_bg.fill((8, 8, 16, 220))
    screen.blit(field_bg, (bx, by))
    for x in range(0, BOARD_W + 1, CELL):
        pygame.draw.line(screen, GRID_COLOR, (bx + x, by),
                         (bx + x, by + BOARD_H))
    for y in range(0, BOARD_H + 1, CELL):
        pygame.draw.line(screen, GRID_COLOR, (bx, by + y),
                         (bx + BOARD_W, by + y))

    # «линия отрыва» у низа поля — пульсирующая
    pulse = 0.5 + 0.5 * math.sin(time * 2.2)
    lane = pygame.Surface((BOARD_W, 3), pygame.SRCALPHA)
    lane.fill(with_alpha(ACCENT, 40 + 60 * pulse))
    screen.blit(lane, (bx, by + BOARD_H - 3))

    # зафиксированные блоки
    for y, row in game.board.items():
        if 0 <= y < ROWS:
            for x, color in row.items():
                draw_cell(screen, bx + x * CELL, by + y * CELL, color)

    # шлейф hard drop
    if game.drop_trail:
        tsurf = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        for cells, color, age, order in game.drop_trail:
            t = 1 - age / 0.28
            alpha = int(90 * t * (0.3 + 0.7 * order))
            for x, y in cells:
                if 0 <= y < ROWS:
                    r = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
                    pygame.draw.rect(tsurf, (*color, alpha), r,
                                     border_radius=3)
        screen.blit(tsurf, (bx, by))

    if not game.game_over:
        _draw_ghost(screen, game, bx, by, time)
        _draw_current(screen, game, bx, by)

        # подсветка приземления — мягкое цветное пятно под фигурой
        if game.land_flash > 0.01:
            gx = bx + (game.current.x + 2) * CELL
            gy = by + max(0, min(game.current.y, ROWS - 1)) * CELL + CELL
            spot = make_radial_glow(int(CELL * 2.2), game.current.color,
                                    int(120 * game.land_flash))
            screen.blit(spot, spot.get_rect(center=(gx, gy)),
                        special_flags=pygame.BLEND_ADD)

    # эффекты (частицы/волны/надписи) — поверх поля
    render_effects(screen, game.effects, (bx, by), fonts)

    # glow-рамка поля (подсвечивается цианом при тряске)
    frame_col = lerp_color((80, 80, 110), ACCENT,
                           min(1.0, game.effects.shake / 8))
    pygame.draw.rect(screen, frame_col, (bx, by, BOARD_W, BOARD_H), 2,
                     border_radius=4)
    outer = pygame.Surface((BOARD_W + 12, BOARD_H + 12), pygame.SRCALPHA)
    pygame.draw.rect(outer, (*frame_col, 60), outer.get_rect(), 6,
                     border_radius=8)
    screen.blit(outer, (bx - 6, by - 6))


def _draw_ghost(screen, game, bx, by, time):
    """Призрак — переливающаяся рамка."""
    shimmer = int(40 + 40 * (0.5 + 0.5 * math.sin(time * 4)))
    gsurf = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
    for x, y in game.ghost_cells():
        if y >= 0:
            r = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
            pygame.draw.rect(gsurf, (*game.current.color, shimmer), r,
                             border_radius=3)
            pygame.draw.rect(gsurf,
                             (*game.current.color, GHOST_ALPHA + 60),
                             r, 2, border_radius=3)
    screen.blit(gsurf, (bx, by))


def _draw_current(screen, game, bx, by):
    """Текущая фигура с плавным появлением (pop-in)."""
    pop = ease_out_cubic(game.current.age / 0.18)
    csurf = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
    for x, y in game.current.cells():
        if y >= 0:
            draw_cell(csurf, x * CELL, y * CELL, game.current.color)
    if pop < 0.999:
        w = max(1, int(BOARD_W * pop))
        h = max(1, int(BOARD_H * pop))
        scaled = pygame.transform.smoothscale(csurf, (w, h))
        screen.blit(scaled, (bx + (BOARD_W - w) // 2,
                              by + (BOARD_H - h) // 2))
    else:
        screen.blit(csurf, (bx, by))
