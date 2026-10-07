"""
Классический Тетрис на Python + Pygame.

Управление:
    <- / ->   — двигать фигуру влево/вправо
    стрелка вниз — мягкое падение (soft drop)
    пробел     — жёсткое падение (hard drop)
    стрелка вверх / X — поворот по часовой
    Z          — поворот против часовой
    C          — сохранить фигуру в «удержание» (hold)
    P          — пауза
    R          — рестарт после Game Over
    ESC        — выход

Запуск:  python tetris.py
"""

import random
import sys

import pygame

# ----------------------------- Настройки -----------------------------------
CELL = 30                    # размер клетки в пикселях
COLS = 10                    # ширина поля
ROWS = 20                    # высота поля

BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL

SIDE_PANEL_W = 6 * CELL      # панель со счётом/next/hold
WINDOW_W = BOARD_W + SIDE_PANEL_W + 2 * CELL
WINDOW_H = BOARD_H + 2 * CELL

FPS = 60

# Скорость падения (секунда на строку) по уровням — классическая таблица NES
DROP_TABLE = [1.0, 0.8, 0.7, 0.6, 0.5, 0.43, 0.36, 0.29, 0.22, 0.17,
              0.13, 0.10, 0.08, 0.06, 0.05]

LINES_PER_LEVEL = 10

# Очки за количество снятых линий сразу
SCORE_TABLE = {1: 100, 2: 300, 3: 500, 4: 800}

# Цвета фигур (классическая палитра)
PIECE_COLORS = {
    "I": (0, 200, 200),
    "O": (220, 200, 40),
    "T": (160, 60, 200),
    "S": (60, 200, 80),
    "Z": (220, 60, 60),
    "J": (60, 90, 220),
    "L": (230, 140, 40),
}

GHOST_ALPHA = 70

BG_COLOR = (20, 20, 30)
BOARD_BG = (12, 12, 20)
GRID_COLOR = (35, 35, 50)
TEXT_COLOR = (230, 230, 230)
PANEL_COLOR = (28, 28, 42)

# Формы фигур: список вращений, каждое — список (x, y) относительно центра
SHAPES = {
    "I": [[(0, 1), (1, 1), (2, 1), (3, 1)],
          [(2, 0), (2, 1), (2, 2), (2, 3)],
          [(0, 2), (1, 2), (2, 2), (3, 2)],
          [(1, 0), (1, 1), (1, 2), (1, 3)]],
    "O": [[(1, 0), (2, 0), (1, 1), (2, 1)]] * 4,
    "T": [[(1, 0), (0, 1), (1, 1), (2, 1)],
          [(1, 0), (1, 1), (2, 1), (1, 2)],
          [(0, 1), (1, 1), (2, 1), (1, 2)],
          [(1, 0), (0, 1), (1, 1), (1, 2)]],
    "S": [[(1, 0), (2, 0), (0, 1), (1, 1)],
          [(1, 0), (1, 1), (2, 1), (2, 2)],
          [(1, 1), (2, 1), (0, 2), (1, 2)],
          [(0, 0), (0, 1), (1, 1), (1, 2)]],
    "Z": [[(0, 0), (1, 0), (1, 1), (2, 1)],
          [(2, 0), (1, 1), (2, 1), (1, 2)],
          [(0, 1), (1, 1), (1, 2), (2, 2)],
          [(1, 0), (0, 1), (1, 1), (0, 2)]],
    "J": [[(0, 0), (0, 1), (1, 1), (2, 1)],
          [(1, 0), (2, 0), (1, 1), (1, 2)],
          [(0, 1), (1, 1), (2, 1), (2, 2)],
          [(1, 0), (1, 1), (0, 2), (1, 2)]],
    "L": [[(2, 0), (0, 1), (1, 1), (2, 1)],
          [(1, 0), (1, 1), (1, 2), (2, 2)],
          [(0, 1), (1, 1), (2, 1), (0, 2)],
          [(0, 0), (1, 0), (1, 1), (1, 2)]],
}

# Простые wall kicks: смещения при неудачном повороте
KICKS = [(0, 0), (-1, 0), (1, 0), (0, -1), (-2, 0), (2, 0)]


class Piece:
    """Текущая активная фигура."""

    def __init__(self, kind):
        self.kind = kind
        self.rotation = 0
        self.x = COLS // 2 - 2      # левый край bounding box 4x4
        self.y = 0                  # спавн у верхнего края поля
        self.color = PIECE_COLORS[kind]

    def cells(self, rotation=None, dx=0, dy=0):
        r = self.rotation if rotation is None else rotation
        return [(self.x + cx + dx, self.y + cy + dy)
                for cx, cy in SHAPES[self.kind][r]]

    def rotated(self, direction):
        return (self.rotation + direction) % 4


class Tetris:
    def __init__(self):
        self.reset()

    def reset(self):
        # board[y][x] — только видимые строки 0..ROWS-1;
        # спавн фигур — вверху видимого поля, game over — при заторе там
        self.board = {}
        self.bag = []
        self.next_queue = [self._from_bag() for _ in range(3)]
        self.hold = None
        self.can_hold = True
        self.score = 0
        self.lines = 0
        self.level = 0
        self.game_over = False
        self.paused = False
        self.drop_timer = 0.0
        self.lock_delay = 0.0
        self.soft_drop = False
        self.new_piece()

    # ---------- генерация фигур (7-bag randomizer) ----------
    def _from_bag(self):
        if not self.bag:
            self.bag = list(SHAPES.keys())
            random.shuffle(self.bag)
        return self.bag.pop()

    def new_piece(self):
        kind = self.next_queue.pop(0)
        self.next_queue.append(self._from_bag())
        self.current = Piece(kind)
        self.drop_timer = 0.0
        self.lock_delay = 0.0
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
    def try_move(self, dx, dy):
        cells = self.current.cells(dx=dx, dy=dy)
        if self.is_valid(cells):
            self.current.x += dx
            self.current.y += dy
            self.lock_delay = 0.0
            return True
        return False

    def try_rotate(self, direction):
        r = self.current.rotated(direction)
        for kx, ky in KICKS:
            cells = self.current.cells(rotation=r, dx=kx, dy=ky)
            if self.is_valid(cells):
                self.current.rotation = r
                self.current.x += kx
                self.current.y += ky
                self.lock_delay = 0.0
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
        self.current.y += dy
        self.score += dy * 2
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
        self.clear_lines()
        self.new_piece()

    def clear_lines(self):
        full = [y for y in range(ROWS)
                if len(self.board.get(y, {})) == COLS]
        if not full:
            return
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
        self.level = self.lines // LINES_PER_LEVEL

    # ---------- игровой цикл по времени ----------
    def update(self, dt):
        self.step(dt)

    def step(self, dt):
        """Один шаг физики: падение, мягкое падение, блокировка."""
        speed = self.drop_interval()
        self.drop_timer += dt
        while self.drop_timer >= speed:
            self.drop_timer -= speed
            if not self.try_move(0, 1):
                break
        if self.grounded():
            self.lock_delay += dt
            if self.lock_delay >= 0.5:
                self.lock_piece()
        else:
            self.lock_delay = 0.0

    def drop_interval(self):
        base = DROP_TABLE[min(self.level, len(DROP_TABLE) - 1)]
        if self.soft_drop:
            return min(base, 0.03)
        return base


# ----------------------------- Отрисовка ------------------------------------

def draw_cell(screen, px, py, color, size=CELL):
    rect = pygame.Rect(px, py, size, size)
    pygame.draw.rect(screen, color, rect)
    light = tuple(min(255, c + 60) for c in color)
    dark = tuple(max(0, c - 80) for c in color)
    pygame.draw.line(screen, light, rect.topleft, rect.topright)
    pygame.draw.line(screen, light, rect.topleft, rect.bottomleft)
    pygame.draw.line(screen, dark, rect.bottomleft, rect.bottomright)
    pygame.draw.line(screen, dark, rect.topright, rect.bottomright)


def draw_mini_piece(screen, surface_pos, kind, cell=20):
    if kind is None:
        return
    cells = SHAPES[kind][0]
    min_x = min(cx for cx, _ in cells)
    max_x = max(cx for cx, _ in cells)
    min_y = min(cy for _, cy in cells)
    max_y = max(cy for _, cy in cells)
    w = (max_x - min_x + 1) * cell
    h = (max_y - min_y + 1) * cell
    ox, oy = surface_pos
    ox += (4 * cell - w) // 2
    oy += (2 * cell - h) // 2
    color = PIECE_COLORS[kind]
    for cx, cy in cells:
        draw_cell(screen, ox + (cx - min_x) * cell,
                  oy + (cy - min_y) * cell, color, cell)


def render(screen, game, fonts):
    big, mid, small = fonts
    screen.fill(BG_COLOR)

    bx, by = CELL, CELL  # origin игрового поля

    # фон поля + сетка
    pygame.draw.rect(screen, BOARD_BG, (bx, by, BOARD_W, BOARD_H))
    for x in range(0, BOARD_W + 1, CELL):
        pygame.draw.line(screen, GRID_COLOR, (bx + x, by), (bx + x, by + BOARD_H))
    for y in range(0, BOARD_H + 1, CELL):
        pygame.draw.line(screen, GRID_COLOR, (bx, by + y), (bx + BOARD_W, by + y))

    # зафиксированные блоки
    for y, row in game.board.items():
        if 0 <= y < ROWS:
            for x, color in row.items():
                draw_cell(screen, bx + x * CELL, by + y * CELL, color)

    if not game.game_over:
        # призрак
        gsurf = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        for x, y in game.ghost_cells():
            if y >= 0:
                r = pygame.Rect(bx + x * CELL - bx, by + y * CELL - by, CELL, CELL)
                pygame.draw.rect(gsurf, (*game.current.color, GHOST_ALPHA), r, 2)
        screen.blit(gsurf, (bx, by))

        # текущая фигура
        for x, y in game.current.cells():
            if y >= 0:
                draw_cell(screen, bx + x * CELL, by + y * CELL, game.current.color)

    # рамка поля
    pygame.draw.rect(screen, (80, 80, 110), (bx, by, BOARD_W, BOARD_H), 2)

    # правая панель
    px = bx + BOARD_W + CELL // 2
    panel_rect = pygame.Rect(px - CELL // 2, by, SIDE_PANEL_W, BOARD_H)
    pygame.draw.rect(screen, PANEL_COLOR, panel_rect, border_radius=8)

    label_score = small.render("СЧЁТ", True, TEXT_COLOR)
    screen.blit(label_score, (px + 6, by + 10))
    score_s = mid.render(str(game.score), True, TEXT_COLOR)
    screen.blit(score_s, (px + 6, by + 32))

    label_level = small.render(f"УРОВЕНЬ: {game.level}", True, TEXT_COLOR)
    screen.blit(label_level, (px + 6, by + 70))
    label_lines = small.render(f"ЛИНИИ: {game.lines}", True, TEXT_COLOR)
    screen.blit(label_lines, (px + 6, by + 92))

    # hold
    hold_label = small.render("УДЕРЖАНИЕ (C)", True, TEXT_COLOR)
    screen.blit(hold_label, (px + 6, by + 130))
    draw_mini_piece(screen, (px + 10, by + 155), game.hold)

    # next
    next_label = small.render("СЛЕДУЮЩИЕ", True, TEXT_COLOR)
    screen.blit(next_label, (px + 6, by + 230))
    for i, kind in enumerate(game.next_queue):
        draw_mini_piece(screen, (px + 10, by + 255 + i * 70), kind)

    # подсказки управления
    hints = ["← → : движение", "↓ : мягкое падение", "Пробел : сброс",
             "↑ / X : поворот", "Z : поворот назад", "P : пауза", "R : рестарт"]
    for i, h in enumerate(hints):
        t = small.render(h, True, (150, 150, 170))
        screen.blit(t, (px + 6, by + BOARD_H - 150 + i * 20))

    # оверлеи
    if game.paused and not game.game_over:
        overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (bx, by))
        t = big.render("ПАУЗА", True, TEXT_COLOR)
        screen.blit(t, t.get_rect(center=(bx + BOARD_W // 2, by + BOARD_H // 2)))

    if game.game_over:
        overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (bx, by))
        t1 = big.render("GAME OVER", True, (240, 80, 80))
        t2 = mid.render(f"Счёт: {game.score}", True, TEXT_COLOR)
        t3 = small.render("R — начать заново, ESC — выход", True, TEXT_COLOR)
        cx = bx + BOARD_W // 2
        screen.blit(t1, t1.get_rect(center=(cx, by + BOARD_H // 2 - 40)))
        screen.blit(t2, t2.get_rect(center=(cx, by + BOARD_H // 2 + 5)))
        screen.blit(t3, t3.get_rect(center=(cx, by + BOARD_H // 2 + 45)))


# ----------------------------- Ввод и main ----------------------------------

DAS_DELAY = 0.17   # сек до автоповтора горизонтального движения
ARR = 0.033        # интервал автоповтора


class HorizontalAutoRepeat:
    def __init__(self):
        self.reset()

    def reset(self):
        self.pressed = set()
        self.direction = 0
        self.timer = 0.0
        self.charged = False

    def press(self, d):
        self.pressed.add(d)
        self.direction = d
        self.timer = 0.0
        self.charged = False

    def release(self, d):
        self.pressed.discard(d)
        remaining = max(self.pressed, default=0)
        self.direction = remaining
        self.timer = 0.0
        self.charged = False

    def update(self, dt, action):
        if self.direction == 0:
            return
        self.timer += dt
        if not self.charged:
            if self.timer >= DAS_DELAY:
                self.charged = True
                self.timer = 0.0
                action(self.direction)
        else:
            while self.timer >= ARR:
                self.timer -= ARR
                action(self.direction)


def main():
    pygame.display.set_caption("Тетрис")
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock = pygame.time.Clock()

    big = pygame.font.SysFont("arial", 36, bold=True)
    mid = pygame.font.SysFont("arial", 24, bold=True)
    small = pygame.font.SysFont("arial", 15)
    fonts = (big, mid, small)

    game = Tetris()
    ar = HorizontalAutoRepeat()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and game.game_over:
                    game.reset()
                    ar.reset()
                elif event.key == pygame.K_p and not game.game_over:
                    game.paused = not game.paused
                elif game.game_over or game.paused:
                    pass
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    game.try_move(-1, 0)
                    ar.press(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    game.try_move(1, 0)
                    ar.press(1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    game.soft_drop = True
                elif event.key in (pygame.K_UP, pygame.K_x):
                    game.try_rotate(1)
                elif event.key == pygame.K_z:
                    game.try_rotate(-1)
                elif event.key == pygame.K_SPACE:
                    game.hard_drop()
                elif event.key == pygame.K_c:
                    game.hold_piece()
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    ar.release(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    ar.release(1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    game.soft_drop = False

        if not game.game_over and not game.paused:
            ar.update(dt, lambda d: game.try_move(d, 0))
            game.step(dt)

        render(screen, game, fonts)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    pygame.init()
    main()
