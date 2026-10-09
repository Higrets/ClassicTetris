# Тетрис — Neon Edition

Классический Тетрис на Python + Pygame с неоновым визуалом,
модульной (послойной) архитектурой и юнит-тестами чистой логики.

## Запуск

```bash
pip install pygame
python tetris.py        # точка входа
```

Тесты (не требуют дисплея):

```bash
python -m unittest discover tests   # или python tests/test_core.py
```

## Архитектура

Зависимости направлены строго «вниз», циклов нет:

```
tetris.py ──> app.py (композиция, переключение экранов)
                │
      ┌─────────┼──────────────┬───────────┐
      ▼         ▼              ▼           ▼
   ui/       core/          effects/      data/     utils/
 (pygame)  (логика,      (симуляция    (файлы,   (матем.
            без pygame)   частиц,      рекорды)  хелперы)
                          без pygame)
      │
      ▼
   config/  (все константы: размеры, скорость, палитра, формы фигур)
```

| Слой | Что внутри |
|---|---|
| `config/` | `settings.py` — все константы и палитра; `shapes.py` — формы тетрамино |
| `core/` | `game.py` — партия Tetris (поле, коллизии, линии, очки); `pieces.py`, `bag.py` (7-bag), `autorepeat.py` (DAS/ARR). **Не импортирует pygame** |
| `effects/` | `manager.py` — частицы, ударные волны, всплывающие надписи, тряска (headless-симуляция в клеточных координатах) |
| `data/` | `highscores.py` — загрузка/сохранение топ-5 рекордов в `highscores.txt` |
| `ui/` | `background.py` — анимированный фон; `sprites.py` — блоки/мини-фигуры; `render_board.py` — поле; `render_hud.py` — панель и оверлеи; `render_effects.py` — рендер эффектов; `colors.py`, `fonts.py`; `screens/` — экраны `menu.py` и `gameplay.py` |
| `utils/` | `mathx.py` — clamp/lerp/lerp_color/easing |
| `tests/` | юнит-тесты core/effects/data |

Слои `core`, `effects`, `data`, `utils` полностью независимы от pygame —
их можно тестировать и переиспользовать (бот, headless-сервер и т.п.).

## Управление

Меню: ↑/↓ или мышь — выбор, Enter/ЛКМ — открыть, Esc — выход.

Игра: ←/→ (A/D) — движение, ↓ (S) — мягкое падение, Пробел — жёсткий сброс,
↑/X — поворот, Z — обратный поворот, C — hold, P — пауза, R — рестарт,
ESC — главное меню.
