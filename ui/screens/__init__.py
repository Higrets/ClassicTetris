"""
Экраны приложения («страницы»).

Каждый экран реализует интерфейс Screen: handle_event / update / render.
    ui.screens.menu     — главное меню, рекорды, управление
    ui.screens.gameplay — игровой экран (цикл партии)

Связка с приложением — через AppContext (ui/screens/base.py).
"""

from ui.screens.base import Screen, AppContext
from ui.screens.menu import MainMenu
from ui.screens.gameplay import GameScreen

__all__ = ["Screen", "AppContext", "MainMenu", "GameScreen"]
