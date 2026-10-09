"""Частица — простой контейнер состояния (без отрисовки)."""


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")
