"""
"""
import math
from typing import Callable, Optional
import datetime

import pandas as pd

from dashboard.kpi.base import BaseKPI, KpiZone, get_current_week, get_recent_weeks
from dashboard.data import WeeklyStats
from dashboard.load import PomodorosProcessed
import dashboard.config as config


class WeeklyDoneKPI(BaseKPI):

    def __init__(self, data: WeeklyStats, raw_data: PomodorosProcessed):
        self.data = data
        self.raw_data = raw_data
        current = get_current_week(data)
        recent = get_recent_weeks(data)
        value = int(current.df.done.iloc[0])
        target = round(recent.df.done.median() * config.KPI_IMPROVEMENT_RATE)
        self.pomodoros_left_7_days = None
        self.pomodoros_left_6_days = None
        self.pomodoros_left_5_days = None
        zone = self._compute_zone(value=value, target=target)
        super().__init__(value=value, target=target, zone=zone)

    def _compute_zone(self, value: int, target: int) -> KpiZone:

        today_done = self.raw_data.df.loc[self.raw_data.df.Date == pd.to_datetime(datetime.date.today()), 'Pomodoros'].sum()

        backlog = target - value + today_done

        today = datetime.date.today().weekday()
        no_rest_est = target / 7
        no_rest_actual = backlog / (7 - today) if 7 > today else math.inf
        self.pomodoros_left_7_days = max(0, no_rest_actual - today_done)

        # day_rest_est = target / 6
        day_rest_actual = backlog / (6 - today) if 6 > today else math.inf
        self.pomodoros_left_6_days = max(0, day_rest_actual - today_done)

        weekend_rest_est = target / 5
        weekend_rest_actual = backlog / (5 - today) if 5 > today else math.inf
        self.pomodoros_left_5_days = max(0, weekend_rest_actual - today_done)

        if weekend_rest_actual <= weekend_rest_est or backlog - today_done <= 0:
            return KpiZone.GREEN
        elif no_rest_actual <= no_rest_est:
            return KpiZone.YELLOW
        else:
            return KpiZone.RED

    def suggested_action(self, formatter: Optional[Callable[[str], str]] = None) -> str:
        formatter = formatter or (lambda x: x)
        pomodoros_5_days = formatter(str(round(self.pomodoros_left_5_days))
                                     if not math.isinf(self.pomodoros_left_5_days)
                                     else "--")
        pomodoros_6_days = formatter(str(round(self.pomodoros_left_6_days))
                                     if not math.isinf(self.pomodoros_left_6_days)
                                     else "--")
        pomodoros_7_days = formatter(str(round(self.pomodoros_left_7_days))
                                     if not math.isinf(self.pomodoros_left_7_days)
                                     else "--")

        return (f"{pomodoros_5_days} pomodoros left today in case of two days rest, " +
                f"{pomodoros_6_days} for one day rest, " +
                f"{pomodoros_7_days} for no rest days this week.")
