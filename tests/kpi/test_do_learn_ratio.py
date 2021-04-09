import unittest

import pandas as pd

from dashboard.kpi.do_learn_ratio import DoLearnRatioKPI, DoLearnData


class DoLearnComputeCase(unittest.TestCase):

    def test_balanced(self):
        df = pd.DataFrame({
            'Pomodoros': [1, 1, 1, 1],
            'do': [False, False, True, True],
            'learn': [True, True, False, False],
        })
        actual = DoLearnRatioKPI.compute_value(DoLearnData.convert(df))
        self.assertEqual(actual, 0.5)

    def test_all_do(self):
        df = pd.DataFrame({
            'Pomodoros': [1, 1, 1, 1],
            'do': [True, True, True, True],
            'learn': [False, False, False, False],
        })
        actual = DoLearnRatioKPI.compute_value(DoLearnData.convert(df))
        self.assertEqual(actual, 1)

    def test_all_learn(self):
        df = pd.DataFrame({
            'Pomodoros': [1, 1, 1, 1],
            'learn': [True, True, True, True],
            'do': [False, False, False, False],
        })
        actual = DoLearnRatioKPI.compute_value(DoLearnData.convert(df))
        self.assertEqual(actual, 0)


if __name__ == '__main__':
    unittest.main()
