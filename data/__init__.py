"""
Слой данных: всё, что связано с файлами и сохранением.

    data.highscores — загрузка/сохранение топ-рекордов (highscores.txt)

Модули слоя данных не знают ни про pygame, ни про игровую логику —
только про формат файлов.
"""

from data.highscores import load_high_scores, save_high_score

__all__ = ["load_high_scores", "save_high_score"]
