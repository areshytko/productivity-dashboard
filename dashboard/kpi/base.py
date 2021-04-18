"""
"""

from typing import Callable, Optional
from enum import Enum
import datetime

from dashboard.data import WeeklyStats
from dashboard.config import Config


class KpiZone(Enum):
    RED = 1
    YELLOW = 2
    GREEN = 3


def get_current_week(weekly_stats: WeeklyStats) -> WeeklyStats:
    today = datetime.date.today()
    result = weekly_stats.df.loc[weekly_stats.df.Week == weekly_stats.df.Week.max(), :]
    assert result.from_date.iloc[0] <= today <= result.to_date.iloc[0]
    return WeeklyStats(result)


def get_recent_weeks(weekly_stats: WeeklyStats) -> WeeklyStats:
    current = weekly_stats.df.Week.max()
    df = weekly_stats.df
    return WeeklyStats(df.loc[(current - df.Week <= Config().KPI_HISTORICAL_WINDOW) & (current - df.Week > 0), :])


class BaseKPI:

    def __init__(self, value, target, zone: KpiZone):
        self.value = value
        self.target = target
        self.zone = zone

    def suggested_action(self, formatter: Optional[Callable[[str], str]] = None) -> str:
        return ""


class CompleteRateKPI(BaseKPI):

    def __init__(self, data: WeeklyStats):
        pass


#class RottenProjectKPI(BaseKPI):
#
#    def __init__(self, pomodoros: PomodorosProcessed, activities: ActivitiesCatalog):
#        pass
