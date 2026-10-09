"""Юнит-тесты чистой логики (core/effects/data) — без pygame-дисплея."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import COLS, ROWS
from core.game import Tetris
from core.bag import BagRandomizer
from data.highscores import load_high_scores, save_high_score
from effects.manager import EffectsManager


class TestBag(unittest.TestCase):
    def test_seven_bag(self):
        bag = BagRandomizer()
        seq = [bag.next_kind() for _ in range(14)]
        self.assertEqual(sorted(set(seq[:7])), list("IJLOSTZ"))
        self.assertEqual(sorted(set(seq[7:])), list("IJLOSTZ"))


class TestTetris(unittest.TestCase):
    def make_full_row(self, y=ROWS - 1, except_x=None):
        for x in range(COLS):
            if x == except_x:
                continue
            self.game.board.setdefault(y, {})[x] = (200, 50, 50)

    def setUp(self):
        self.game = Tetris()

    def test_collision_walls(self):
        # заводим фигуру к стене — дальше не пускает
        while self.game.try_move(-1, 0):
            pass
        cells = self.game.current.cells()
        self.assertGreaterEqual(min(x for x, _ in cells), 0)

    def test_hard_drop_locks(self):
        kind = self.game.current.kind
        score_before = self.game.score
        self.game.hard_drop()
        self.assertNotEqual(self.game.current.kind or "X", "" )
        self.assertTrue(self.game.board)   # что-то зафиксировано
        self.assertGreaterEqual(self.game.score, score_before)
        self.assertIsInstance(kind, str)

    def test_clear_single_line(self):
        fx = EffectsManager()
        game = Tetris(effects=fx)
        # заполняем нижнюю строку, кроме одной клетки под текущей фигурой I
        y = ROWS - 1
        # ставим I вертикально? проще: очистим board и вручную заполним
        game.board = {}
        for x in range(COLS):
            game.board.setdefault(y, {})[x] = (10, 10, 10)
        lines_before = game.lines
        game.clear_lines()
        self.assertEqual(game.lines, lines_before + 1)
        self.assertTrue(fx.particles)      # эффекты сгенерированы
        self.assertTrue(fx.shockwaves)
        self.assertTrue(fx.floaters)

    def test_hold_once_per_piece(self):
        first = self.game.current.kind
        self.game.hold_piece()
        self.assertEqual(self.game.hold, first)
        second = self.game.current.kind
        self.game.hold_piece()             # второй hold подряд запрещён
        self.assertEqual(self.game.hold, first)
        self.assertEqual(self.game.current.kind, second)

    def test_game_over_on_top_out(self):
        # забиваем верх поля — новая фигура должна дать game over
        for y in range(ROWS):
            for x in range(COLS):
                self.game.board.setdefault(y, {})[x] = (5, 5, 5)
        self.game.new_piece()
        self.assertTrue(self.game.game_over)

    def test_rotate_limit_locks(self):
        from config.settings import MAX_ROTATES_PER_PIECE
        for _ in range(MAX_ROTATES_PER_PIECE + 2):
            self.game.try_rotate(1)
        self.assertGreaterEqual(self.game.rotate_count, MAX_ROTATES_PER_PIECE)


class TestEffects(unittest.TestCase):
    def test_particles_decay(self):
        fx = EffectsManager()
        fx.burst_row(ROWS - 1, (255, 0, 0))
        n = len(fx.particles)
        self.assertGreater(n, 0)
        for _ in range(120):
            fx.update(1 / 60)
        self.assertEqual(len(fx.particles), 0)
        self.assertEqual(len(fx.shockwaves), 0)

    def test_shake_decays(self):
        fx = EffectsManager()
        fx.add_shake(10)
        for _ in range(60):
            fx.update(1 / 60)
        self.assertEqual(fx.shake, 0.0)


class TestHighscores(unittest.TestCase):
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "hs.txt")
            save_high_score(100, path)
            save_high_score(300, path)
            save_high_score(200, path)
            self.assertEqual(load_high_scores(path), [300, 200, 100])

    def test_top5_only(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "hs.txt")
            for s in range(1, 12):
                save_high_score(s * 10, path)
            scores = load_high_scores(path)
            self.assertEqual(len(scores), 5)
            self.assertEqual(scores, sorted(scores, reverse=True))

    def test_missing_file(self):
        self.assertEqual(load_high_scores("/nonexistent/dir/hs.txt"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
