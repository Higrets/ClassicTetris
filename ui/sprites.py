"""Спрайты: глянцевый блок и мини-фигура для панелей next/hold."""

import pygame

from config.settings import CELL, PIECE_COLORS
from config.shapes import SHAPES
from utils.mathx import lerp_color


def draw_cell(screen, px, py, color, size=CELL, glossy=True):
    """Глянцевый объёмный блок: тёмная подложка, светлая грань, блик."""
    rect = pygame.Rect(px, py, size, size)
    base = lerp_color(color, (10, 10, 18), 0.25)
    pygame.draw.rect(screen, base, rect, border_radius=3)
    light = tuple(min(255, c + 70) for c in color)
    dark = tuple(max(0, c - 90) for c in color)
    pad = max(1, size // 12)
    band_h = max(2, size // 4)
    top_band = pygame.Rect(px + pad, py + pad, size - 2 * pad, band_h)
    pygame.draw.rect(screen, light, top_band, border_radius=2)
    body = pygame.Rect(px + pad, py + pad + band_h,
                       size - 2 * pad, size - 2 * pad - band_h)
    if body.height > 0:
        pygame.draw.rect(screen, color, body, border_radius=2)
    pygame.draw.rect(screen, dark, rect.inflate(-1, -1), 1, border_radius=3)
    if glossy and size >= 20:
        hl = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(
            hl, (255, 255, 255, 42),
            [(pad + 1, pad + 1), (size // 2, pad + 1),
             (pad + 1, size // 2)])
        screen.blit(hl, (px, py))


def draw_mini_piece(screen, surface_pos, kind, cell=20):
    """Рисует фигуру вида kind, центрированную в области 4*cell x 2*cell."""
    if kind is None:
        return
    cells = SHAPES[kind][0]
    min_x = min(cx for cx, _ in cells)
    max_x = max(cx for cx, _ in cells)
    min_y = min(cy for _, cy in cells)
    max_y = max(cy for _, cy in cells)
    w = (max_x - min_x + 1) * cell
    h = (max_y - min_y + 1) * cell
    ox, oy = surface_pos
    ox += (4 * cell - w) // 2
    oy += (2 * cell - h) // 2
    color = PIECE_COLORS[kind]
    for cx, cy in cells:
        draw_cell(screen, ox + (cx - min_x) * cell,
                  oy + (cy - min_y) * cell, color, size=cell, glossy=False)
