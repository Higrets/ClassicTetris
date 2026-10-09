"""DAS/ARR автоповтор горизонтального движения (без pygame)."""

from config.settings import ARR, DAS_DELAY


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
