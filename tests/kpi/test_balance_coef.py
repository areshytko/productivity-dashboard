import unittest

import pandas as pd

from dashboard.kpi.balance_coef import BalanceCoefKPI, BalanceCoefData


class BalanceCoefComputeCase(unittest.TestCase):

    def setUp(self) -> None:
        data = pd.DataFrame({
            'Pomodoros': [1, 1, 1, 1, 1],
            'life': [False, False, False, False, True],
            'personal': [True, True, True, False, False],
            'career': [False, False, False, False, False],
            'hobby': [False, False, False, False, False],
            'society': [False, False, False, True, False],
            'health': [False, False, False, False, False]
        })
        self.data = BalanceCoefData.convert(data)

        self.expected_zero = pd.Series([0.2, 0.6, 0, 0, 0.2, 0], index=BalanceCoefData.LIFE_DOMAINS)
        self.expected_small = pd.Series([0.2, 0.5, 0.1, 0, 0.2, 0], index=BalanceCoefData.LIFE_DOMAINS)
        self.expected_big = pd.Series([0, 0, 0, 1, 0, 0], index=BalanceCoefData.LIFE_DOMAINS)

    def test_it_works(self):
        expected_zero = BalanceCoefKPI.compute_value(self.data, self.expected_zero)
        expected_small = BalanceCoefKPI.compute_value(self.data, self.expected_small)
        expected_big = BalanceCoefKPI.compute_value(self.data, self.expected_big)
        self.assertEqual(expected_zero, 0)
        self.assertLess(expected_zero, expected_small)
        self.assertLess(expected_small, expected_big)


if __name__ == '__main__':
    unittest.main()
