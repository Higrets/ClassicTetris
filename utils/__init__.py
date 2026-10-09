"""Общие утилиты, не зависящие ни от pygame, ни от игровых модулей."""

from utils.mathx import clamp, ease_out_cubic, lerp, lerp_color

__all__ = ["clamp", "lerp", "lerp_color", "ease_out_cubic"]
