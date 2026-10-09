"""Хранилище рекордов: простой текстовый файл с числами построчно."""

from config.settings import HIGHSCORE_PATH, MAX_HIGHSCORES


def load_high_scores(path=HIGHSCORE_PATH):
    """Возвращает список топ-N очков (по убыванию). Пустой список при ошибке."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [int(x) for x in f.read().split()][:MAX_HIGHSCORES]
    except Exception:
        return []


def save_high_score(score, path=HIGHSCORE_PATH):
    """Добавляет очко, сортирует, сохраняет топ-N; возвращает новый рейтинг."""
    scores = load_high_scores(path)
    scores.append(score)
    scores.sort(reverse=True)
    scores = scores[:MAX_HIGHSCORES]
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(map(str, scores)))
    except Exception:
        pass
    return scores
