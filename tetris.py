"""
Классический Тетрис на Python + Pygame — Neon Edition.

Экраны:
    ГЛАВНОЕ МЕНЮ   — анимированный фон (падающие фигуры, звёзды, туманности,
                     градиент), «дышащий» неоновый заголовок с волной,
                     кнопки с подсветкой при наведении (мышь / стрелки).
    ИГРА           — частицы при сборе линий, ударные волны, тряска экрана,
                     жёсткий сброс со шлейфом, подсветка приземления,
                     плавное появление фигур, переливающийся призрак,
                     glow-рамка поля, всплывающие надписи («КВАДРИС!!»),
                     «прощающий» градиент при Game Over.
    ПАУЗА          — затемнение + пульсирующая надпись.

Управление в меню:
    ↑/↓ или мышь — выбор пункта, Enter/ЛКМ — открыть, Esc — выход.

Управление в игре:
    <- / ->            — двигать фигуру влево/вправо
    стрелка вниз       — мягкое падение (soft drop)
    пробел             — жёсткое падение (hard drop)
    стрелка вверх / X  — поворот по часовой
    Z                  — поворот против часовой
    C                  — сохранить фигуру в «удержание» (hold)
    P                  — пауза
    R                  — рестарт партии
    ESC                — вернуться в главное меню

Запуск:  python tetris.py
"""

import math
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

# Скорость мягкого падения при зажатой стрелке вниз (секунда на клетку).
SOFT_DROP_INTERVAL = 0.08

# Задержка фиксации фигуры, когда она стоит на опоре (секунды)
LOCK_DELAY = 0.5

# Максимум поворотов для одной фигуры. После превышения лимита фигура
# фиксируется по таймеру lock_delay, поэтому бесконечное вращение больше
# не может «вечить» фигуру в воздухе.
MAX_ROTATES_PER_PIECE = 15

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

ACCENT = (0, 229, 255)       # неоновый циан
ACCENT2 = (255, 0, 170)      # маджента
GOLD = (255, 210, 80)

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


# ----------------------------- Утилиты --------------------------------------

def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    t = clamp(t, 0.0, 1.0)
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def ease_out_cubic(t):
    t = clamp(t, 0.0, 1.0)
    return 1 - (1 - t) ** 3


def make_vgrad(size, top, bottom):
    """Вертикальный градиент."""
    w, h = size
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        surf.fill(lerp_color(top, bottom, t), (0, y, w, 1))
    return surf


def make_radial_glow(radius, color, peak_alpha=160):
    """Мягкое круглое свечение (для фона и neon-эффектов)."""
    radius = max(2, int(radius))
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    steps = 14
    for i in range(steps, 0, -1):
        t = i / steps
        alpha = int(peak_alpha * (1 - t) ** 2)
        r = max(1, int(radius * t))
        pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
    return surf


# ----------------------------- Фоновая сцена --------------------------------

class Star:
    def __init__(self, w, h):
        self.reset(w, h, first=True)

    def reset(self, w, h, first=False):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h) if first else -4
        self.r = random.uniform(0.6, 2.0)
        self.speed = random.uniform(4, 18)
        self.phase = random.uniform(0, math.tau)
        self.twinkle = random.uniform(1.2, 3.5)

    def update(self, dt, w, h):
        self.y += self.speed * dt
        if self.y > h + 4:
            self.reset(w, h)

    def draw(self, screen, t):
        a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * self.twinkle + self.phase))
        col = (int(180 * a), int(200 * a), int(255 * a))
        pygame.draw.circle(screen, col, (int(self.x), int(self.y)),
                           int(round(self.r)))


class FallingPiece:
    """Декоративная падающая фигура на фоне меню."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.reset(first=random.random() < 0.7)

    def reset(self, first=False):
        self.kind = random.choice(list(SHAPES.keys()))
        self.color = PIECE_COLORS[self.kind]
        self.cell = random.uniform(10, 22)
        self.x = random.uniform(-20, self.w)
        self.y = random.uniform(-self.h, self.h) if first else \
            random.uniform(-self.h * 0.4, -20)
        self.speed = random.uniform(22, 60)
        self.rot = random.uniform(0, math.tau)
        self.spin = random.uniform(-1.1, 1.1)
        self.alpha = random.randint(28, 60)

    def update(self, dt):
        self.y += self.speed * dt
        self.rot += self.spin * dt
        if self.y - 4 * self.cell > self.h + 40:
            self.reset()

    def draw(self, screen):
        cells = SHAPES[self.kind][0]
        side = int(5 * self.cell) + 8
        surf = pygame.Surface((side, side), pygame.SRCALPHA)
        for cx, cy in cells:
            r = pygame.Rect(int((cx + 0.5) * self.cell) + 4,
                            int((cy + 0.5) * self.cell) + 4,
                            int(self.cell), int(self.cell))
            pygame.draw.rect(surf, (*self.color, self.alpha), r,
                             border_radius=3)
            pygame.draw.rect(surf, (*self.color, min(255, self.alpha + 45)),
                             r, 1, border_radius=3)
        rotd = pygame.transform.rotate(surf, math.degrees(self.rot))
        rect = rotd.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotd, rect)


class BackgroundFX:
    """Общий анимированный фон: градиент + туманности + звёзды + фигуры."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.grad = make_vgrad((w, h), (8, 10, 24), (26, 14, 48))
        self.stars = [Star(w, h) for _ in range(70)]
        self.pieces = [FallingPiece(w, h) for _ in range(11)]
        self.nebula1 = make_radial_glow(max(w, h) // 2, (70, 30, 140), 60)
        self.nebula2 = make_radial_glow(max(w, h) // 3, (0, 120, 160), 45)
        self.time = 0.0

    def update(self, dt):
        self.time += dt
        for s in self.stars:
            s.update(dt, self.w, self.h)
        for p in self.pieces:
            p.update(dt)

    def draw(self, screen, pieces_visible=True):
        screen.blit(self.grad, (0, 0))
        t = self.time
        # дрейфующие туманности
        x1 = int(self.w * 0.25 + math.sin(t * 0.11) * 60)
        y1 = int(self.h * 0.3 + math.cos(t * 0.09) * 40)
        screen.blit(self.nebula1,
                    self.nebula1.get_rect(center=(x1, y1)),
                    special_flags=pygame.BLEND_ADD)
        x2 = int(self.w * 0.75 + math.cos(t * 0.08) * 70)
        y2 = int(self.h * 0.7 + math.sin(t * 0.12) * 50)
        screen.blit(self.nebula2,
                    self.nebula2.get_rect(center=(x2, y2)),
                    special_flags=pygame.BLEND_ADD)
        for s in self.stars:
            s.draw(screen, t)
        if pieces_visible:
            for p in self.pieces:
                p.draw(screen)


# ----------------------------- Эффекты --------------------------------------

class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")


class EffectsManager:
    """Частицы, ударные волны, всплывающие надписи, тряска экрана."""

    def __init__(self):
        self.particles = []
        self.shockwaves = []     # dict: x, y, age, color, power
        self.floaters = []       # dict: text, x, y, age, color
        self.shake = 0.0

    def burst_row(self, y, color, power=1.0):
        """Мощный залп частиц по линии."""
        n = int(COLS * 3 * power)
        for _ in range(n):
            p = Particle()
            p.x = random.uniform(0, BOARD_W)
            p.y = y * CELL + CELL / 2 + random.uniform(-CELL / 2, CELL / 2)
            ang = random.uniform(0, math.tau)
            spd = random.uniform(60, 320) * power
            p.vx = math.cos(ang) * spd
            p.vy = math.sin(ang) * spd - random.uniform(40, 160)
            p.max_life = p.life = random.uniform(0.4, 0.9)
            base = color if random.random() < 0.7 else (255, 255, 255)
            p.color = (clamp(base[0] + random.randint(-20, 40), 0, 255),
                       clamp(base[1] + random.randint(-20, 40), 0, 255),
                       clamp(base[2] + random.randint(-20, 40), 0, 255))
            p.size = random.uniform(2, 5)
            self.particles.append(p)

    def burst_cell(self, x, y, color, count=6):
        for _ in range(count):
            p = Particle()
            p.x = x * CELL + CELL / 2
            p.y = y * CELL + CELL / 2
            ang = random.uniform(0, math.tau)
            spd = random.uniform(30, 140)
            p.vx = math.cos(ang) * spd
            p.vy = math.sin(ang) * spd
            p.max_life = p.life = random.uniform(0.25, 0.55)
            p.color = color
            p.size = random.uniform(1.5, 3.5)
            self.particles.append(p)

    def shockwave(self, y, color, power=1.0):
        self.shockwaves.append({"x": BOARD_W / 2, "y": y * CELL + CELL / 2,
                                "age": 0.0, "color": color, "power": power})

    def float_text(self, text, color):
        self.floaters.append({"text": text, "x": BOARD_W / 2,
                              "y": BOARD_H * 0.42, "age": 0.0, "color": color})

    def add_shake(self, amount):
        self.shake = min(14.0, self.shake + amount)

    def update(self, dt):
        for p in self.particles:
            p.life -= dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 520 * dt          # гравитация частиц
            p.vx *= (1 - 1.6 * dt)
        self.particles = [p for p in self.particles if p.life > 0]
        for w in self.shockwaves:
            w["age"] += dt
        self.shockwaves = [w for w in self.shockwaves if w["age"] < 0.5]
        for f in self.floaters:
            f["age"] += dt
            f["y"] -= 34 * dt
        self.floaters = [f for f in self.floaters if f["age"] < 1.3]
        self.shake = max(0.0, self.shake - dt * 22)

    def render(self, screen, board_pos, fonts):
        mid = fonts[1]
        bx, by = board_pos
        psurf = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        # частицы
        for p in self.particles:
            t = p.life / p.max_life
            alpha = int(255 * t)
            s = max(1, int(p.size * t))
            pygame.draw.rect(psurf, (*p.color, alpha),
                             (int(p.x) - s // 2, int(p.y) - s // 2, s, s))
        # ударные волны
        for w in self.shockwaves:
            t = w["age"] / 0.5
            radius = ease_out_cubic(t) * BOARD_W * 0.85 * w["power"]
            if radius < 2:
                continue
            alpha = int(200 * (1 - t))
            r = pygame.Rect(0, 0, int(radius * 2), int(radius * 2))
            r.center = (int(w["x"]), int(w["y"]))
            pygame.draw.ellipse(psurf, (*w["color"], alpha), r,
                                width=max(1, int(4 * (1 - t))))
        screen.blit(psurf, (bx, by))
        # всплывающие надписи
        for f in self.floaters:
            t = f["age"] / 1.3
            alpha = int(255 * (1 - t) ** 1.5)
            scale = 1.0 + 0.35 * (1 - min(1.0, f["age"] * 4))
            txt = mid.render(f["text"], True, f["color"])
            if abs(scale - 1) > 0.02:
                txt = pygame.transform.smoothscale(
                    txt, (max(1, int(txt.get_width() * scale)),
                          max(1, int(txt.get_height() * scale))))
            txt.set_alpha(alpha)
            rect = txt.get_rect(center=(bx + f["x"], by + f["y"]))
            screen.blit(txt, rect)


# ----------------------------- Логика игры ----------------------------------

class Piece:
    """Текущая активная фигура."""

    def __init__(self, kind):
        self.kind = kind
        self.rotation = 0
        self.x = COLS // 2 - 2      # левый край bounding box 4x4
        self.y = 0                  # спавн у верхнего края поля
        self.color = PIECE_COLORS[kind]
        self.age = 0.0              # для анимации появления

    def cells(self, rotation=None, dx=0, dy=0):
        r = self.rotation if rotation is None else rotation
        return [(self.x + cx + dx, self.y + cy + dy)
                for cx, cy in SHAPES[self.kind][r]]

    def rotated(self, direction):
        return (self.rotation + direction) % 4


class Tetris:
    def __init__(self):
        self.effects = EffectsManager()
        self.drop_trail = []        # шлейф hard drop: [cells, color, age, order]
        self.land_flash = 0.0       # подсветка приземления
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
        self.over_age = 0.0
        self.drop_timer = 0.0
        self.lock_delay = 0.0
        self.rotate_count = 0
        self.soft_drop = False
        self.effects = EffectsManager()
        self.drop_trail = []
        self.land_flash = 0.0
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
            self.effects.add_shake(min(6.0, 1.5 + dy * 0.35))
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
            if 0 <= y < ROWS:
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
        self.effects.add_shake(2.5 + 3.0 * n)
        names = {1: "+1 ЛИНИЯ", 2: "ДВОЙНАЯ!", 3: "ТУТРИС!", 4: "КВАДРИС!!"}
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


# ----------------------------- Отрисовка игры --------------------------------

def draw_cell(screen, px, py, color, size=CELL, glossy=True):
    """Глянцевый объёмный блок: тёмная подложка, светлая грань, блик."""
    rect = pygame.Rect(px, py, size, size)
    base = lerp_color(color, (10, 10, 18), 0.25)
    pygame.draw.rect(screen, base, rect, border_radius=3)
    light = tuple(min(255, c + 70) for c in color)
    dark = tuple(max(0, c - 90) for c in color)
    pad = max(1, size // 12)
    band_h = max(2, size // 4)
    top_band = pygame.Rect(px + pad, py + pad, size - 2 * pad, band_h)
    pygame.draw.rect(screen, light, top_band, border_radius=2)
    body = pygame.Rect(px + pad, py + pad + band_h,
                       size - 2 * pad, size - 2 * pad - band_h)
    if body.height > 0:
        pygame.draw.rect(screen, color, body, border_radius=2)
    pygame.draw.rect(screen, dark, rect.inflate(-1, -1), 1, border_radius=3)
    if glossy and size >= 20:
        hl = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(
            hl, (255, 255, 255, 42),
            [(pad + 1, pad + 1), (size // 2, pad + 1),
             (pad + 1, size // 2)])
        screen.blit(hl, (px, py))


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
                  oy + (cy - min_y) * cell, color, size=cell, glossy=False)


def render_game(screen, game, fonts, bg, time):
    big, mid, small = fonts
    bx, by = CELL, CELL  # origin игрового поля

    # приглушённый анимированный фон
    screen.blit(bg.grad, (0, 0))
    veil = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    veil.fill((8, 8, 18, 225))
    screen.blit(veil, (0, 0))

    # glow за игровым полем
    glow = make_radial_glow(BOARD_H // 2 + 60, (40, 60, 160), 70)
    screen.blit(glow, glow.get_rect(center=(bx + BOARD_W // 2,
                                            by + BOARD_H // 2)),
                special_flags=pygame.BLEND_ADD)

    # фон поля + сетка
    field_bg = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
    field_bg.fill((8, 8, 16, 220))
    screen.blit(field_bg, (bx, by))
    for x in range(0, BOARD_W + 1, CELL):
        pygame.draw.line(screen, GRID_COLOR, (bx + x, by),
                         (bx + x, by + BOARD_H))
    for y in range(0, BOARD_H + 1, CELL):
        pygame.draw.line(screen, GRID_COLOR, (bx, by + y),
                         (bx + BOARD_W, by + y))

    # «линия отрыва» у низа поля — пульсирующая
    pulse = 0.5 + 0.5 * math.sin(time * 2.2)
    lane = pygame.Surface((BOARD_W, 3), pygame.SRCALPHA)
    lane.fill((*ACCENT, int(40 + 60 * pulse)))
    screen.blit(lane, (bx, by + BOARD_H - 3))

    # зафиксированные блоки
    for y, row in game.board.items():
        if 0 <= y < ROWS:
            for x, color in row.items():
                draw_cell(screen, bx + x * CELL, by + y * CELL, color)

    # шлейф hard drop
    if game.drop_trail:
        tsurf = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        for cells, color, age, order in game.drop_trail:
            t = 1 - age / 0.28
            alpha = int(90 * t * (0.3 + 0.7 * order))
            for x, y in cells:
                if 0 <= y < ROWS:
                    r = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
                    pygame.draw.rect(tsurf, (*color, alpha), r,
                                     border_radius=3)
        screen.blit(tsurf, (bx, by))

    if not game.game_over:
        # призрак — переливающаяся рамка
        shimmer = int(40 + 40 * (0.5 + 0.5 * math.sin(time * 4)))
        gsurf = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        for x, y in game.ghost_cells():
            if y >= 0:
                r = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
                pygame.draw.rect(gsurf, (*game.current.color, shimmer), r,
                                 border_radius=3)
                pygame.draw.rect(gsurf,
                                 (*game.current.color, GHOST_ALPHA + 60),
                                 r, 2, border_radius=3)
        screen.blit(gsurf, (bx, by))

        # текущая фигура с плавным появлением (pop-in)
        pop = ease_out_cubic(game.current.age / 0.18)
        csurf = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        for x, y in game.current.cells():
            if y >= 0:
                draw_cell(csurf, x * CELL, y * CELL, game.current.color)
        if pop < 0.999:
            w = max(1, int(BOARD_W * pop))
            h = max(1, int(BOARD_H * pop))
            scaled = pygame.transform.smoothscale(csurf, (w, h))
            screen.blit(scaled, (bx + (BOARD_W - w) // 2,
                                  by + (BOARD_H - h) // 2))
        else:
            screen.blit(csurf, (bx, by))

        # подсветка приземления — мягкое цветное пятно под фигурой
        if game.land_flash > 0.01:
            gx = bx + (game.current.x + 2) * CELL
            gy = by + clamp(game.current.y, 0, ROWS - 1) * CELL + CELL
            spot = make_radial_glow(int(CELL * 2.2), game.current.color,
                                    int(120 * game.land_flash))
            screen.blit(spot, spot.get_rect(center=(gx, gy)),
                        special_flags=pygame.BLEND_ADD)

    # эффекты (частицы/волны/надписи) — поверх поля
    game.effects.render(screen, (bx, by), fonts)

    # glow-рамка поля (подсвечивается цианом при тряске)
    frame_col = lerp_color((80, 80, 110), ACCENT,
                           min(1.0, game.effects.shake / 8))
    pygame.draw.rect(screen, frame_col, (bx, by, BOARD_W, BOARD_H), 2,
                     border_radius=4)
    outer = pygame.Surface((BOARD_W + 12, BOARD_H + 12), pygame.SRCALPHA)
    pygame.draw.rect(outer, (*frame_col, 60), outer.get_rect(), 6,
                     border_radius=8)
    screen.blit(outer, (bx - 6, by - 6))

    # ------- правая панель -------
    px = bx + BOARD_W + CELL // 2
    panel_rect = pygame.Rect(px - CELL // 2, by, SIDE_PANEL_W, BOARD_H)
    panel_bg = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
    panel_bg.fill((28, 28, 46, 235))
    screen.blit(panel_bg, panel_rect.topleft)
    pygame.draw.rect(screen, (70, 70, 100), panel_rect, 2, border_radius=8)

    label_score = small.render("СЧЁТ", True, (150, 150, 175))
    screen.blit(label_score, (px + 6, by + 10))
    score_s = mid.render(str(game.score), True, GOLD)
    screen.blit(score_s, (px + 6, by + 30))

    label_level = small.render(f"УРОВЕНЬ: {game.level}", True, ACCENT)
    screen.blit(label_level, (px + 6, by + 68))
    label_lines = small.render(f"ЛИНИИ: {game.lines}", True, TEXT_COLOR)
    screen.blit(label_lines, (px + 6, by + 90))

    hold_label = small.render("УДЕРЖАНИЕ (C)", True, (150, 150, 175))
    screen.blit(hold_label, (px + 6, by + 128))
    hold_box = pygame.Rect(px + 6, by + 150, SIDE_PANEL_W - 16, 2 * 20 + 8)
    pygame.draw.rect(screen, (20, 20, 34), hold_box, border_radius=6)
    draw_mini_piece(screen, (px + 12, by + 154), game.hold, cell=20)
    if not game.can_hold and game.hold is not None:
        dim = pygame.Surface(hold_box.size, pygame.SRCALPHA)
        dim.fill((8, 8, 14, 150))
        screen.blit(dim, hold_box.topleft)

    next_label = small.render("СЛЕДУЮЩИЕ", True, (150, 150, 175))
    screen.blit(next_label, (px + 6, by + 228))
    for i, kind in enumerate(game.next_queue):
        box = pygame.Rect(px + 6, by + 250 + i * 70,
                          SIDE_PANEL_W - 16, 2 * 20 + 8)
        pygame.draw.rect(screen, (20, 20, 34), box, border_radius=6)
        draw_mini_piece(screen, (px + 12, by + 254 + i * 70), kind, cell=20)
        if i == 0:
            a = int(120 + 80 * (0.5 + 0.5 * math.sin(time * 3)))
            pygame.draw.rect(screen, (*ACCENT, a), box, 1, border_radius=6)

    hints = ["← → : движение", "↓ : мягкое падение", "Пробел : сброс",
             "↑ / X : поворот", "Z : поворот назад", "C : удержание",
             "P : пауза", "R : рестарт", "ESC : меню"]
    for i, h in enumerate(hints):
        t = small.render(h, True, (130, 130, 155))
        screen.blit(t, (px + 6, by + BOARD_H - 185 + i * 19))

    # ------- оверлеи -------
    if game.paused and not game.game_over:
        overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (bx, by))
        breathe = 0.5 + 0.5 * math.sin(time * 3)
        t = big.render("ПАУЗА", True,
                       lerp_color((255, 255, 255), ACCENT, breathe))
        screen.blit(t, t.get_rect(center=(bx + BOARD_W // 2,
                                          by + BOARD_H // 2 - 10)))
        t2 = small.render("P — продолжить", True, (180, 180, 200))
        screen.blit(t2, t2.get_rect(center=(bx + BOARD_W // 2,
                                             by + BOARD_H // 2 + 30)))

    if game.game_over:
        # ступенчатое затемнение с красным оттенком
        dark = min(190, int(200 * ease_out_cubic(game.over_age / 0.8)))
        overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        overlay.fill((20, 0, 10, dark))
        screen.blit(overlay, (bx, by))
        appear = ease_out_cubic(game.over_age / 0.5)
        wob = 1 + 0.03 * math.sin(time * 2.6)
        t1 = big.render("GAME OVER", True, (240, 70, 90))
        w = max(1, int(t1.get_width() * appear * wob))
        h = max(1, int(t1.get_height() * appear * wob))
        t1 = pygame.transform.smoothscale(t1, (w, h))
        cx = bx + BOARD_W // 2
        screen.blit(t1, t1.get_rect(center=(cx, by + BOARD_H // 2 - 46)))
        if game.over_age > 0.35:
            t2 = mid.render(f"Счёт: {game.score}", True, GOLD)
            screen.blit(t2, t2.get_rect(center=(cx, by + BOARD_H // 2 + 2)))
        if game.over_age > 0.55:
            t3 = small.render("R — заново · ESC — в меню", True,
                              (200, 200, 220))
            screen.blit(t3, t3.get_rect(center=(cx, by + BOARD_H // 2 + 40)))


# ----------------------------- Главное меню ----------------------------------

MENU_ITEMS = [("ИГРАТЬ", "play"), ("РЕКОРДЫ", "records"),
              ("УПРАВЛЕНИЕ", "controls"), ("ВЫХОД", "quit")]


class MenuButton:
    def __init__(self, label, action, rect):
        self.label = label
        self.action = action
        self.rect = rect
        self.hover = 0.0      # 0..1 плавная анимация наведения


class MainMenu:
    def __init__(self, bg, get_high_scores):
        self.bg = bg
        self.get_high_scores = get_high_scores
        self.index = 0
        self.time = 0.0
        self.state = "menu"           # menu | records | controls | play | quit
        self.fade = 1.0               # чёрный экран при входе -> прозрачный
        self.buttons = []
        self._layout_buttons()

    def _layout_buttons(self):
        bw, bh = 300, 52
        cx = WINDOW_W // 2
        y0 = WINDOW_H // 2 - 20
        self.buttons = []
        for i, (label, act) in enumerate(MENU_ITEMS):
            rect = pygame.Rect(cx - bw // 2, y0 + i * (bh + 14), bw, bh)
            self.buttons.append(MenuButton(label, act, rect))

    def handle_event(self, event):
        if self.state in ("records", "controls"):
            if event.type == pygame.KEYDOWN or \
               (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                self.state = "menu"
            return
        if self.state != "menu":
            return
        if event.type == pygame.MOUSEMOTION:
            for i, b in enumerate(self.buttons):
                if b.rect.collidepoint(event.pos):
                    self.index = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, b in enumerate(self.buttons):
                if b.rect.collidepoint(event.pos):
                    self.index = i
                    self._activate()
                    break
        elif event.type == pygame.KEYDOWN:
            if self.state in ("records", "controls"):
                # любая клавиша — возврат в меню (не срабатываем дважды)
                self.state = "menu"
                return
            if event.key in (pygame.K_UP, pygame.K_w):
                self.index = (self.index - 1) % len(self.buttons)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.index = (self.index + 1) % len(self.buttons)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                               pygame.K_SPACE):
                self._activate()
            elif event.key == pygame.K_ESCAPE:
                self.state = "quit"

    def _activate(self):
        act = self.buttons[self.index].action
        if act == "quit":
            self.state = "quit"
        elif act == "play":
            self.state = "play"
        else:
            self.state = act

    def update(self, dt):
        self.time += dt
        self.fade = max(0.0, self.fade - dt * 2.2)
        for i, b in enumerate(self.buttons):
            target = 1.0 if i == self.index else 0.0
            b.hover += (target - b.hover) * min(1.0, dt * 12)

    # ---------- отрисовка ----------
    def _title(self, screen):
        t_font = pygame.font.SysFont("arial", 78, bold=True)
        sub_font = pygame.font.SysFont("arial", 20, bold=True)

        title = "ТЕТРИС"
        # побуквенная радуга + синусоидальная волна + неоновое свечение
        letters = []
        total_w = 0
        hue_shift = self.time * 40
        for i, ch in enumerate(title):
            hue = ((i * 28 + hue_shift) % 360) / 360
            col = pygame.Color(0, 0, 0, 255)
            col.hsva = (hue * 360, 85, 100, 100)
            srf = t_font.render(ch, True, col)
            letters.append((srf, col, i))
            total_w += srf.get_width()
        x = WINDOW_W // 2 - total_w // 2
        base_y = WINDOW_H // 2 - 190
        for srf, col, i in letters:
            wave = math.sin(self.time * 2.4 + i * 0.55) * 7
            # glow-копия буквы
            shadow = pygame.Surface(srf.get_size(), pygame.SRCALPHA)
            shadow.fill((col.r, col.g, col.b, 120))
            shadow.blit(srf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            bigglow = pygame.transform.smoothscale(
                shadow, (srf.get_width() + 16, srf.get_height() + 16))
            screen.blit(bigglow,
                        bigglow.get_rect(
                            center=(x + srf.get_width() // 2,
                                    base_y + srf.get_height() // 2 +
                                    int(wave))),
                        special_flags=pygame.BLEND_ADD)
            screen.blit(srf, (x, base_y + int(wave)))
            x += srf.get_width()
        # подзаголовок
        sub_col = lerp_color((160, 160, 190), ACCENT,
                             0.5 + 0.5 * math.sin(self.time * 2))
        sub = sub_font.render("NEON EDITION · АНИМАЦИИ · ЭФФЕКТЫ",
                              True, sub_col)
        screen.blit(sub, sub.get_rect(
            center=(WINDOW_W // 2, base_y + 86)))

    def _draw_menu(self, screen):
        self._title(screen)
        font = pygame.font.SysFont("arial", 24, bold=True)
        for b in self.buttons:
            hov = b.hover
            r = b.rect.copy()
            r.inflate_ip(int(10 * hov), int(6 * hov))
            base_col = lerp_color((24, 24, 40), (44, 36, 74), hov)
            bg_s = pygame.Surface(r.size, pygame.SRCALPHA)
            bg_s.fill((*base_col, int(180 + 60 * hov)))
            screen.blit(bg_s, r.topleft)
            border = lerp_color((70, 70, 100), ACCENT, hov)
            if hov > 0.05:
                halo = pygame.Surface((r.w + 12, r.h + 12), pygame.SRCALPHA)
                pygame.draw.rect(halo, (*ACCENT, int(70 * hov)),
                                 halo.get_rect(), 6, border_radius=14)
                screen.blit(halo, (r.x - 6, r.y - 6))
                tri = [(r.x - 20, r.centery - 8),
                       (r.x - 20, r.centery + 8),
                       (r.x - 9, r.centery)]
                pygame.draw.polygon(screen, ACCENT, tri)
            pygame.draw.rect(screen, border, r, 2, border_radius=10)
            col = lerp_color((200, 200, 215), (255, 255, 255), hov)
            txt = font.render(b.label, True, col)
            screen.blit(txt, txt.get_rect(center=r.center))
        foot = pygame.font.SysFont("arial", 15).render(
            "Enter / клик — выбрать · Esc — выход", True, (140, 140, 165))
        screen.blit(foot, foot.get_rect(
            center=(WINDOW_W // 2, WINDOW_H - 26)))

    def _draw_records(self, screen):
        head = pygame.font.SysFont("arial", 40, bold=True)
        body = pygame.font.SysFont("arial", 22, bold=True)
        t = head.render("РЕКОРДЫ", True, GOLD)
        wob = math.sin(self.time * 3) * 3
        screen.blit(t, t.get_rect(center=(WINDOW_W // 2, 90 + wob)))
        scores = self.get_high_scores()
        if not scores:
            msg = body.render("Пока пусто — сыграй партию!", True,
                              (190, 190, 210))
            screen.blit(msg, msg.get_rect(center=(WINDOW_W // 2,
                                                  WINDOW_H // 2)))
        for i, s in enumerate(scores[:5]):
            line = body.render(f"{i + 1}.  {s}", True,
                               GOLD if i == 0 else TEXT_COLOR)
            screen.blit(line, line.get_rect(
                midleft=(WINDOW_W // 2 - 110, 170 + i * 40)))
        back = pygame.font.SysFont("arial", 16).render(
            "Любая клавиша — назад", True, (150, 150, 175))
        screen.blit(back, back.get_rect(center=(WINDOW_W // 2,
                                                 WINDOW_H - 40)))

    def _draw_controls(self, screen):
        head = pygame.font.SysFont("arial", 40, bold=True)
        body = pygame.font.SysFont("arial", 20)
        t = head.render("УПРАВЛЕНИЕ", True, ACCENT)
        screen.blit(t, t.get_rect(center=(WINDOW_W // 2, 90)))
        rows = [("← / →  или  A / D", "движение"),
                ("↓  или  S", "мягкое падение"),
                ("ПРОБЕЛ", "жёсткий сброс"),
                ("↑  /  X", "поворот по часовой"),
                ("Z", "поворот против часовой"),
                ("C", "удержание (hold)"),
                ("P", "пауза"),
                ("R", "рестарт"),
                ("ESC", "главное меню")]
        cy = 150
        for i, (k, v) in enumerate(rows):
            kk = body.render(k, True, GOLD)
            vv = body.render(v, True, TEXT_COLOR)
            screen.blit(kk, (WINDOW_W // 2 - 230, cy + i * 36))
            screen.blit(vv, (WINDOW_W // 2 + 10, cy + i * 36))
        back = pygame.font.SysFont("arial", 16).render(
            "Любая клавиша — назад", True, (150, 150, 175))
        screen.blit(back, back.get_rect(center=(WINDOW_W // 2,
                                                 WINDOW_H - 40)))

    def render(self, screen):
        self.bg.draw(screen, pieces_visible=True)
        if self.state == "menu":
            self._draw_menu(screen)
        elif self.state == "records":
            self._draw_records(screen)
        elif self.state == "controls":
            self._draw_controls(screen)
        # затемнение при переходе fade-in
        if self.fade > 0.01:
            black = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            black.fill((5, 5, 12, int(255 * self.fade)))
            screen.blit(black, (0, 0))


# ----------------------------- Автоповтор движения ---------------------------

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


# ----------------------------- Рекорды ---------------------------------------

HIGHSCORE_PATH = "highscores.txt"


def load_high_scores(path=HIGHSCORE_PATH):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [int(x) for x in f.read().split()][:5]
    except Exception:
        return []


def save_high_score(score, path=HIGHSCORE_PATH):
    scores = load_high_scores(path)
    scores.append(score)
    scores.sort(reverse=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(map(str, scores[:5])))
    except Exception:
        pass
    return scores[:5]


# ----------------------------- Приложения / main ----------------------------

def run_game(screen, fonts, bg, clock):
    """Игровой цикл; возвращает 'menu' | 'quit'."""
    game = Tetris()
    ar = HorizontalAutoRepeat()
    saved = False
    while True:
        dt = clock.tick(FPS) / 1000.0
        bg.update(dt)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                key = event.key
                if key == pygame.K_ESCAPE:
                    if not saved and game.score > 0:
                        save_high_score(game.score)
                    return "menu"
                elif key == pygame.K_r:
                    # R работает всегда: и во время игры, и после Game Over
                    if not saved and game.score > 0:
                        save_high_score(game.score)
                    game.reset()
                    ar.reset()
                    saved = False
                elif key == pygame.K_p and not game.game_over:
                    game.paused = not game.paused
                elif game.game_over or game.paused:
                    pass
                elif key in (pygame.K_LEFT, pygame.K_a):
                    game.try_move(-1, 0)
                    ar.press(-1)
                elif key in (pygame.K_RIGHT, pygame.K_d):
                    game.try_move(1, 0)
                    ar.press(1)
                elif key in (pygame.K_DOWN, pygame.K_s):
                    game.soft_drop = True
                elif key in (pygame.K_UP, pygame.K_x):
                    game.try_rotate(1)
                elif key == pygame.K_z:
                    game.try_rotate(-1)
                elif key == pygame.K_SPACE:
                    game.hard_drop()
                elif key == pygame.K_c:
                    game.hold_piece()
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    ar.release(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    ar.release(1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    game.soft_drop = False

        game.update(dt)

        if game.game_over and not saved and game.score > 0:
            save_high_score(game.score)
            saved = True

        time = pygame.time.get_ticks() / 1000.0
        # буфер сцены — чтобы применить тряску экрана
        scene = pygame.Surface((WINDOW_W, WINDOW_H))
        render_game(scene, game, fonts, bg, time)
        sh = game.effects.shake
        if sh > 0.2:
            ox = random.uniform(-sh, sh)
            oy = random.uniform(-sh, sh)
            screen.fill(BG_COLOR)
            screen.blit(scene, (ox, oy))
        else:
            screen.blit(scene, (0, 0))
        pygame.display.flip()


def main():
    pygame.display.set_caption("Тетрис — Neon Edition")
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock = pygame.time.Clock()

    big = pygame.font.SysFont("arial", 36, bold=True)
    mid = pygame.font.SysFont("arial", 24, bold=True)
    small = pygame.font.SysFont("arial", 15)
    fonts = (big, mid, small)

    bg = BackgroundFX(WINDOW_W, WINDOW_H)
    menu = MainMenu(bg, load_high_scores)

    while True:
        # ---- цикл меню ----
        menu.state = "menu"
        menu.time = 0.0
        menu.fade = 1.0
        while menu.state in ("menu", "records", "controls"):
            dt = clock.tick(FPS) / 1000.0
            bg.update(dt)
            menu.update(dt)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                menu.handle_event(event)
            menu.render(screen)
            pygame.display.flip()

        if menu.state == "quit":
            pygame.quit()
            return
        if menu.state == "play":
            result = run_game(screen, fonts, bg, clock)
            if result == "quit":
                pygame.quit()
                return


if __name__ == "__main__":
    pygame.init()
    main()
