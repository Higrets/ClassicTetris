"""
EffectsManager — частицы, ударные волны, всплывающие надписи, тряска.

Полностью headless: координаты хранятся в КЛЕТКАХ поля (float), скорость —
в клетках/сек. ui.render_effects конвертирует их в пиксели через CELL.
"""

import math
import random

from config.settings import COLS, ROWS
from effects.particles import Particle

GRAVITY = 17.0        # клеток/с^2 — «гравитация» частиц
SHAKE_MAX = 14.0      # максимальная амплитуда тряски (условные пиксели)
SHAKE_DECAY = 22.0    # затухание тряски, ед/с
WAVE_LIFE = 0.5       # длительность ударной волны, с
FLOATER_LIFE = 1.3    # длительность всплывающей надписи, с


class EffectsManager:
    def __init__(self):
        self.particles = []
        self.shockwaves = []     # dict: x, y, age, color, power (x,y — клетки)
        self.floaters = []       # dict: text, x, y, age, color (x,y — клетки)
        self.shake = 0.0

    # ---------- генераторы событий ----------
    def burst_row(self, y, color, power=1.0):
        """Мощный залп частиц по линии (y — номер строки поля)."""
        n = int(COLS * 3 * power)
        for _ in range(n):
            p = Particle()
            p.x = random.uniform(0, COLS)
            p.y = y + 0.5 + random.uniform(-0.5, 0.5)
            ang = random.uniform(0, math.tau)
            spd = random.uniform(2.0, 11.0) * power          # клеток/с
            p.vx = math.cos(ang) * spd
            p.vy = math.sin(ang) * spd - random.uniform(1.3, 5.3)
            p.max_life = p.life = random.uniform(0.4, 0.9)
            base = color if random.random() < 0.7 else (255, 255, 255)
            p.color = (_clamp(base[0] + random.randint(-20, 40)),
                       _clamp(base[1] + random.randint(-20, 40)),
                       _clamp(base[2] + random.randint(-20, 40)))
            p.size = random.uniform(2, 5)                    # пиксели — ок
            self.particles.append(p)

    def burst_cell(self, x, y, color, count=6):
        for _ in range(count):
            p = Particle()
            p.x = x + 0.5
            p.y = y + 0.5
            ang = random.uniform(0, math.tau)
            spd = random.uniform(1.0, 4.7)
            p.vx = math.cos(ang) * spd
            p.vy = math.sin(ang) * spd
            p.max_life = p.life = random.uniform(0.25, 0.55)
            p.color = color
            p.size = random.uniform(1.5, 3.5)
            self.particles.append(p)

    def shockwave(self, y, color, power=1.0):
        self.shockwaves.append({"x": COLS / 2, "y": y + 0.5,
                                "age": 0.0, "color": color, "power": power})

    def float_text(self, text, color):
        self.floaters.append({"text": text, "x": COLS / 2,
                              "y": ROWS * 0.42, "age": 0.0, "color": color})

    def add_shake(self, amount):
        self.shake = min(SHAKE_MAX, self.shake + amount)

    # ---------- симуляция ----------
    def update(self, dt):
        for p in self.particles:
            p.life -= dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += GRAVITY * dt
            p.vx *= (1 - 1.6 * dt)
        self.particles = [p for p in self.particles if p.life > 0]
        for w in self.shockwaves:
            w["age"] += dt
        self.shockwaves = [w for w in self.shockwaves if w["age"] < WAVE_LIFE]
        for f in self.floaters:
            f["age"] += dt
            f["y"] -= 1.13 * dt          # ~34 px/с при CELL=30
        self.floaters = [f for f in self.floaters if f["age"] < FLOATER_LIFE]
        self.shake = max(0.0, self.shake - dt * SHAKE_DECAY)


def _clamp(v):
    return max(0, min(255, v))
