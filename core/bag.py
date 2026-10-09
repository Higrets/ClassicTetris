"""7-bag randomizer: все 7 фигур выдаются по одному разу до перемешивания."""

import random

from config.shapes import SHAPES


class BagRandomizer:
    def __init__(self):
        self.bag = []

    def next_kind(self):
        if not self.bag:
            self.bag = list(SHAPES.keys())
            random.shuffle(self.bag)
        return self.bag.pop()

    def reset(self):
        self.bag = []
