"""
Слой эффектов (чистая логика, без pygame-отрисовки).

Эффекты живут в «логических координатах» поля: x, y — клетки, время —
секунды. Конкретный рендер частиц/волн выполняет ui.render_effects,
получив готовый список «прожитых» состояний. Благодаря этому логику
эффектов можно тестировать и переиспользовать без дисплея.
"""

from effects.particles import Particle
from effects.manager import EffectsManager

__all__ = ["Particle", "EffectsManager"]
