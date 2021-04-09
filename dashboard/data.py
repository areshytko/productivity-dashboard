"""
"""

import numpy as np

from dashboard.typed import TypedDataFrame


class PomodoroStats(TypedDataFrame):
    schema = {
        'done': np.float64,
        'planned': np.float64,
        'avg_done': np.float64,
        'avg_planned': np.float64,
        'complete_rate': np.float64,
        'do_learn_ratio': np.float64,
        'red_green_ratio': np.float64,
        'balance_coef': np.float64
    }


class WeeklyStats(PomodoroStats):
    schema = {
        'Week': np.int16,
        'from_date': np.dtype('datetime64[ns]'),
        'to_date': np.dtype('datetime64[ns]')
    }
