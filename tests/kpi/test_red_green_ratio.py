import unittest

import pandas as pd

from dashboard.kpi.red_green_ratio import RedGreenRatioKPI, RedGreenData


class RedGreenComputeCase(unittest.TestCase):

    def test_balanced(self):
        df = pd.DataFrame({
            'Pomodoros': [1, 1, 1, 1],
            'green': [False, False, True, True],
            'red': [True, True, False, False],
        })
        actual = RedGreenRatioKPI.compute_value(RedGreenData.convert(df))
        self.assertEqual(actual, 0.5)

    def test_all_green(self):
        df = pd.DataFrame({
            'Pomodoros': [1, 1, 1, 1],
            'green': [True, True, True, True],
            'red': [False, False, False, False],
        })
        actual = RedGreenRatioKPI.compute_value(RedGreenData.convert(df))
        self.assertEqual(actual, 0)

    def test_all_red(self):
        df = pd.DataFrame({
            'Pomodoros': [1, 1, 1, 1],
            'red': [True, True, True, True],
            'green': [False, False, False, False],
        })
        actual = RedGreenRatioKPI.compute_value(RedGreenData.convert(df))
        self.assertEqual(actual, 1)


if __name__ == '__main__':
    unittest.main()
