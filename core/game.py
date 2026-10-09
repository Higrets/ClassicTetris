"""
Класс партии Tetris — вся чистая логика игры без единой отрисовки.

Модуль не импортирует pygame. Событийные hooks (on_lines_cleared,
on_hard_drop, on_lock) вызываются для слоя эффектов — визуал подписывается
на них, а логика остаётся независимой.
"""

from config.settings import (ACCENT, DROP_TABLE, GOLD, KICKS,
                             LINES_PER_LEVEL, LOCK_DELAY,
                             MAX_ROTATES_PER_PIECE, SCORE_TABLE,
                             SOFT_DROP_INTERVAL, TEXT_COLOR, COLS, ROWS)
from core.bag import BagRandomizer
from core.pieces import Piece


class Tetris:
    def __init__(self, effects=None):
        # effects — необязательный объект-слушатель событий партии
        # (обычно ui.effects.EffectsManager). Логика вызывает только его
        # методы и никогда не рисует сама.
        self.effects = effects
        self.drop_trail = []        # шлейф hard drop: [cells, color, age, order]
        self.land_flash = 0.0       # подсветка приземления
        self.reset()

    def reset(self):
        # board[y][x] — только видимые строки 0..ROWS-1;
        # спавн фигур — вверху видимого поля, game over — при заторе там
        self.board = {}
        self.bag = BagRandomizer()
        self.next_queue = [self.bag.next_kind() for _ in range(3)]
        self.hold = None
        self.can_hold = True
        self.score = 0
        self.lines = 0
        self.level = 0
        self.game_over = False
        self.paused = False
        self.over_age = 0.0
        self.drop_timer = 0.0
        self.lock_delay = 0.0
        self.rotate_count = 0
        self.soft_drop = False
        self.drop_trail = []
        self.land_flash = 0.0
        self.new_piece()

    # ---------- генерация фигур ----------
    def new_piece(self):
        kind = self.next_queue.pop(0)
        self.next_queue.append(self.bag.next_kind())
        self.current = Piece(kind)
        self.drop_timer = 0.0
        self.lock_delay = 0.0
        self.rotate_count = 0
        self.can_hold = True
        if not self.is_valid(self.current.cells()):
            self.game_over = True

    # ---------- проверка коллизий ----------
    def cell_occupied(self, x, y):
        if x < 0 or x >= COLS or y >= ROWS:
            return True
        return self.board.get(y, {}).get(x, None) is not None

    def is_valid(self, cells):
        return all(not self.cell_occupied(x, y) for x, y in cells)

    # ---------- движения ----------
    def try_move(self, dx, dy, from_input=True):
        cells = self.current.cells(dx=dx, dy=dy)
        if self.is_valid(cells):
            self.current.x += dx
            self.current.y += dy
            # Сбрасываем таймер фиксации только при движении игрока
            # (horizontal/soft drop), но не при автоматическом шаге гравитации.
            if dx != 0 and from_input:
                self.lock_delay = 0.0
            return True
        return False

    def try_rotate(self, direction):
        r = self.current.rotated(direction)
        for kx, ky in KICKS:
            # Поворот не должен двигать фигуру ВНИЗ (ky > 0): иначе при
            # быстром вращении разные фигуры получают разные «нырки» вниз
            # по kick-смещениям — выглядит как разная скорость падения.
            if ky > 0:
                continue
            cells = self.current.cells(rotation=r, dx=kx, dy=ky)
            if self.is_valid(cells):
                self.current.rotation = r
                self.current.x += kx
                self.current.y += ky
                # НЕ сбрасываем lock_delay при повороте: иначе бесконечное
                # вращение «зависает» фигуру над полем и она не падает.
                self.rotate_count += 1
                if self.rotate_count > MAX_ROTATES_PER_PIECE:
                    self.lock_delay = LOCK_DELAY  # лимит исчерпан — фиксируем
                return True
        return False

    def ghost_cells(self):
        dy = 0
        while self.is_valid(self.current.cells(dy=dy + 1)):
            dy += 1
        return self.current.cells(dy=dy)

    def hard_drop(self):
        dy = 0
        while self.is_valid(self.current.cells(dy=dy + 1)):
            dy += 1
        if dy > 0:
            # шлейф: силуэт на каждом пройденном шаге падения
            for step in range(dy):
                self.drop_trail.append(
                    [self.current.cells(dy=step), self.current.color,
                     0.0, (step + 1) / dy])
            self._fx_shake(min(6.0, 1.5 + dy * 0.35))
        self.current.y += dy
        self.score += dy * 2
        self.land_flash = 1.0
        self.lock_piece()

    def hold_piece(self):
        if not self.can_hold:
            return
        kind = self.current.kind
        if self.hold is None:
            self.hold = kind
            self.new_piece()
        else:
            self.hold, kind = kind, self.hold
            self.current = Piece(kind)
            self.drop_timer = 0.0
            self.lock_delay = 0.0
            if not self.is_valid(self.current.cells()):
                self.game_over = True
        self.can_hold = False

    # ---------- фиксация и очистка линий ----------
    def grounded(self):
        return not self.is_valid(self.current.cells(dy=1))

    def lock_piece(self):
        for x, y in self.current.cells():
            self.board.setdefault(y, {})[x] = self.current.color
            if 0 <= y < ROWS and self.effects is not None:
                self.effects.burst_cell(x, y, self.current.color, count=3)
        self.clear_lines()
        self.new_piece()

    def clear_lines(self):
        full = [y for y in range(ROWS)
                if len(self.board.get(y, {})) == COLS]
        if not full:
            return
        for y in full:
            row_colors = list(self.board[y].values())
            if self.effects is not None:
                self.effects.burst_row(y, row_colors[0],
                                       power=1.0 + 0.25 * len(full))
                self.effects.shockwave(y, row_colors[0],
                                       power=0.7 + 0.2 * len(full))
        for y in full:
            del self.board[y]
        # сдвигаем всё, что выше снятых линий, вниз
        for y in sorted(self.board.keys(), reverse=True):
            if y < max(full):
                shifted = y + sum(1 for f in full if f > y)
                self.board[shifted] = self.board.pop(y)
        n = len(full)
        self.lines += n
        self.score += SCORE_TABLE.get(n, 0) * (self.level + 1)
        old_level = self.level
        self.level = self.lines // LINES_PER_LEVEL
        if self.effects is not None:
            self.effects.add_shake(2.5 + 3.0 * n)
            names = {1: "+1 ЛИНИЯ", 2: "ДВОЙНАЯ!", 3: "ТУТРИС!",
                     4: "КВАДРИС!!"}
            hot = GOLD if n >= 2 else TEXT_COLOR
            self.effects.float_text(names.get(n, ""), hot)
            if self.level > old_level:
                self.effects.float_text(f"УРОВЕНЬ {self.level + 1}", ACCENT)

    # ---------- игровой цикл по времени ----------
    def update(self, dt):
        # анимации живут всегда (частицы дотлевают даже после game over)
        self.current.age += dt
        self.land_flash = max(0.0, self.land_flash - dt * 3.5)
        for tr in self.drop_trail:
            tr[2] += dt
        self.drop_trail = [t for t in self.drop_trail if t[2] < 0.28]
        if self.effects is not None:
            self.effects.update(dt)
        if self.game_over:
            self.over_age += dt
            return
        if self.paused:
            return
        self.step(dt)

    def step(self, dt):
        """Один шаг физики: падение, мягкое падение, блокировка.

        Гравитация и soft drop разделены: скорость мягкого падения
        (SOFT_DROP_INTERVAL) одинакова для всех фигур и не зависит от
        уровня — это чинит баг «одни фигуры падают на стрелке вниз быстрее
        других».
        """
        grav = self.drop_interval()
        speed = SOFT_DROP_INTERVAL if self.soft_drop else grav
        # Пока зажата стрелка вниз, таймер обычного падения не копит
        # «остаток», иначе после отпускания клавиши фигура делает лишний
        # мгновенный шаг вниз.
        if self.soft_drop:
            self.drop_timer = min(self.drop_timer, speed)
        self.drop_timer += dt
        while self.drop_timer >= speed:
            self.drop_timer -= speed
            if not self.try_move(0, 1, from_input=self.soft_drop):
                break
        if self.grounded():
            self.lock_delay += dt
            if self.lock_delay >= LOCK_DELAY:
                self.lock_piece()
        else:
            self.lock_delay = 0.0

    def drop_interval(self):
        return DROP_TABLE[min(self.level, len(DROP_TABLE) - 1)]

    # ---------- хелперы обращений к эффектам ----------
    def _fx_shake(self, amount):
        if self.effects is not None:
            self.effects.add_shake(amount)
