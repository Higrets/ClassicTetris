"""Фабрика шрифтов — единая точка создания SysFont для всего UI."""

import pygame

# (big, mid, small) — три размера, используемые в игре и HUD
SIZES = {"title": 78, "big": 36, "mid": 24, "small": 15,
         "head": 40, "body": 22, "body2": 20, "foot": 16, "tiny": 15}


def build_fonts():
    """Возвращает кортеж (big, mid, small) для игрового рендера."""
    big = pygame.font.SysFont("arial", SIZES["big"], bold=True)
    mid = pygame.font.SysFont("arial", SIZES["mid"], bold=True)
    small = pygame.font.SysFont("arial", SIZES["small"])
    return big, mid, small


def font(name, bold=False):
    return pygame.font.SysFont("arial", SIZES[name], bold=bold)
