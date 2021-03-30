
from enum import Enum

import numpy as np

from dashboard.load import ActivitiesCatalog, PomodorosProcessed
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


class KpiZone(Enum):
    RED = 1
    YELLOW = 2
    GREEN = 3


class BaseKPI:

    def __init__(self, value, target, zone: KpiZone):
        self.value = value
        self.target = target
        self.zone = zone

    def suggested_action(self) -> str:
        return ""


class WeeklyDoneKPI(BaseKPI):

    def __init__(self, data: WeeklyStats):
        pass


class CompleteRateKPI(BaseKPI):

    def __init__(self, data: WeeklyStats):
        pass


class RottenProjectKPI(BaseKPI):

    def __init__(self, pomodoros: PomodorosProcessed, activities: ActivitiesCatalog):
        pass


def mse(p, q):
    return np.sqrt(np.mean(np.sum(np.power((np.array(p) - np.array(q)), 2))))


# function 1: () -> WeeklyStats

# last_n_weeks_mean: (WeeklyStats, N) -> WeeklyStats

# current_kpi: (WeeklyStats) -> WeeklyStats

# today_done, planned: (PomodorosProcessed) -> tuple[int, int]

# current week KPI zones mechanism: percentage improvement from historical period

# suggested actions

# result: WeeklyDoneKPI, CompleteRateKPI, WeeklyStats
