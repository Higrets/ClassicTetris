"""Активная падающая фигура."""

from config.settings import COLS, PIECE_COLORS
from config.shapes import SHAPES


class Piece:
    """Текущая активная фигура.

    x, y — координаты левого верхнего угла bounding box 4x4 на поле.
    age  — время жизни (используется визуалом для pop-in анимации).
    """

    def __init__(self, kind):
        self.kind = kind
        self.rotation = 0
        self.x = COLS // 2 - 2      # левый край bounding box 4x4
        self.y = 0                  # спавн у верхнего края поля
        self.color = PIECE_COLORS[kind]
        self.age = 0.0              # для анимации появления

    def cells(self, rotation=None, dx=0, dy=0):
        r = self.rotation if rotation is None else rotation
        return [(self.x + cx + dx, self.y + cy + dy)
                for cx, cy in SHAPES[self.kind][r]]

    def rotated(self, direction):
        return (self.rotation + direction) % 4
