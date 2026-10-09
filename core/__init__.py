"""
СлойCore — чистая игровая логика Тетриса.

Подпакеты:
    core.game       — класс партии Tetris (поле, фигуры, очки, линии)
    core.pieces     — активная фигура Piece
    core.bag        — 7-bag генератор фигур
    core.autorepeat — DAS/ARR автоповтор горизонтального движения

ВАЖНО: core НЕ импортирует pygame (кроме случаев работы с цветами-кортежами,
которые остаются обычными tuple). Это позволяет тестировать логику без
дисплея и переиспользовать её, например, в ботe или веб-версии.
"""

from core.bag import BagRandomizer
from core.pieces import Piece
from core.game import Tetris
from core.autorepeat import HorizontalAutoRepeat

__all__ = ["Tetris", "Piece", "BagRandomizer", "HorizontalAutoRepeat"]
