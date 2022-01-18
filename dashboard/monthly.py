import datetime
import calendar
import dataclasses
from typing import Tuple, Callable

import streamlit as st
import numpy as np
import pandas as pd

from typedframe import TypedDataFrame, DATE_TIME_DTYPE

from dashboard.gheets import Credentials, get_data
from dashboard.kpi import KpiZone
from dashboard.config import Config


class MonthlyGoalsData(TypedDataFrame):
    schema = {
        "Month": DATE_TIME_DTYPE,
        "Strategic Track": str,
        "Goal": str,
        "Subgoal": str,
        "GP": np.int64,
        "SP": np.int64,
        "Done": np.float64
    }

    def get_current_goals(self) -> 'MonthlyGoalsData':
        today = datetime.datetime.now()
        result = self.df.loc[(self.df.Month.dt.month == today.month) & (self.df.Month.dt.year == today.year), :]
        assert (len(result) == 1, "No current month in a monthly data")
        return MonthlyGoalsData(result)

    def as_tree(self, node_formatter: Callable[[dict], dict] = lambda x: x) -> dict:
        goals = self.get_current_goals()

        def process_st(st: str, st_df: pd.DataFrame) -> dict:
            goals = []
            done = 0
            gp = 0
            for goal, goal_df in st_df.groupby('Goal'):
                goal_item = process_goal(str(goal), goal_df)
                goals.append(goal_item)
                gp += goal_item['gp']
                done += goal_item['gp'] * goal_item['done']
            done = round(done / gp if gp > 0 else done / len(st_df), 2)
            return node_formatter({
                'name': st,
                'children': goals,
                'value': gp,
                'done': done
            })

        def process_goal(goal: str, goal_df: pd.DataFrame) -> dict:
            subgoals = []
            for _, row in goal_df.iterrows():
                if row['Subgoal'] is not None and len(row['Subgoal']) > 0 and row['Subgoal'] != 'None':
                    subgoal = node_formatter({
                        'name': row['Subgoal'],
                        "value": row["SP"],
                        "done": float(row['Done'])
                    })
                    subgoals.append(subgoal)
            gp = int(goal_df.loc[goal_df.index[0], 'GP'])
            done = (goal_df.Done * goal_df.SP).sum() / goal_df.SP.sum()
            return node_formatter({
                'name': goal,
                "children": subgoals,
                "value": gp,
                "done": done,
                'gp': gp
            })

        children = []
        done = 0
        for st, df in goals.df.groupby('Strategic Track'):
            children.append(process_st(str(st), df))

        today = datetime.date.today()
        root = f"{today.year}-{today.month}"
        return node_formatter({
            'name': root,
            'children': children,
            'done': done
        })

    @staticmethod
    def load(credentials: Credentials,
             spreadsheet_id: str,
             range_name: str) -> 'MonthlyGoalsData':
        data = get_data(
            token=credentials,
            spreadsheet_id=spreadsheet_id,
            range_name=range_name,
            merged_cols=['Month', 'Strategic Track', 'Goal']
        )

        data.GP = data.GP.fillna(1)
        data.SP = data.SP.fillna(1)
        data.Done = data.Done.replace('FALSE', 0)
        data.Done = data.Done.replace('TRUE', 1)

        return MonthlyGoalsData.convert(data)


@dataclasses.dataclass
class CurrentMonthlyPercentageKPI:
    month: DATE_TIME_DTYPE
    kpi: np.float32
    goals_planned: np.int16
    goals_done: np.int16
    goal_points_planned: np.int16
    goal_points_done: np.float32


class MonthlyPercentageKPI(TypedDataFrame):
    schema = {
        "month": DATE_TIME_DTYPE,
        "kpi": np.float32,
        "goals_planned": np.int16,
        "goals_done": np.int16,
        "goal_points_planned": np.int16,
        "goal_points_done": np.float32
    }

    @staticmethod
    def compute(data: MonthlyGoalsData) -> 'MonthlyPercentageKPI':

        def process_subgoals(x):
            weight = x.SP / x.SP.sum()
            done = (x.Done * weight).sum()
            return pd.DataFrame({'GP': x.loc[x.index[0], 'GP'], 'Done': done}, index=[x.index[0]])

        def process_goals(x):
            weight = x.GP / x.GP.sum()
            kpi = (x.Done * weight).sum()
            return pd.DataFrame({
                'kpi': kpi,
                'goals_planned': len(x),
                'goals_done': x.Done.sum(),
                'goal_points_planned': x.GP.sum(),
                'goal_points_done': (x.GP * x.Done).sum()
            }, index=[x.index[0]])

        goals = data.df.groupby(['Month', 'Goal']).apply(process_subgoals)
        result = goals.reset_index().groupby('Month').apply(process_goals)
        result = result.reset_index(level=0).rename(columns={'Month': 'month'})
        return MonthlyPercentageKPI.convert(result)

    def get_current_kpi(self) -> dict:
        today = datetime.datetime.now()
        result = self.df.loc[(self.df.month.dt.month == today.month) & (self.df.month.dt.year == today.year), :]
        assert (len(result) == 1, "No current month in a monthly data")
        result = result.to_dict('records')[0]

        def months_between_dates(dates, end_date):
            return (end_date.year - dates.dt.year) * 12 + (end_date.month - dates.dt.month)

        window = months_between_dates(self.df.month, today)
        window = (1 <= window) & (window <= Config().KPI_HISTORICAL_WINDOW)
        history = self.df.loc[window, 'kpi']
        yellow_target, green_target = compute_kpi_target(history, Config().KPI_IMPROVEMENT_RATE)
        result['target'] = green_target
        result['zone'] = compute_kpi_zone(
            dt=today,
            kpi_value=result['kpi'],
            green_target=green_target,
            yellow_target=yellow_target
        )
        return result

    def gp_to_finish_this_week(self) -> Tuple[int, datetime.date]:
        today = datetime.datetime.today()
        kpi = self.get_current_kpi()
        planned = kpi['goal_points_planned']
        done = kpi['goal_points_done']
        return gp_to_finish(dt=today, planned_gp=planned, done_gp=done)


def get_next_reporting_day(dt: datetime.date) -> datetime.date:
    _, month_days = calendar.monthrange(dt.year, dt.month)
    next_sunday = dt + datetime.timedelta(days=6 - dt.weekday())
    if next_sunday.month == dt.month:
        return next_sunday
    else:
        return datetime.date(year=dt.year, month=dt.month, day=month_days)


def gp_to_finish(dt: datetime.date, planned_gp: int, done_gp: float) -> Tuple[int, datetime.date]:
    till = get_next_reporting_day(dt)
    _, month_days = calendar.monthrange(dt.year, dt.month)
    month_days_left = month_days - dt.day + 1
    gps = round((till.day - dt.day + 1) * (planned_gp - done_gp) / month_days_left)
    return gps, till


def compute_kpi_target(kpi_history: pd.Series, kpi_improve_rate: float) -> Tuple[float, float]:
    if 0 < len(kpi_history):
        target_min = kpi_history.median()
        target = target_min * kpi_improve_rate
        target_min, target = min(target_min, target), max(target_min, target)
    else:
        # st.info("Monthly history is empty. Using 100% KPI for monthly goals")
        target_min, target = 1, 1
    return target_min, target


def compute_kpi_zone(dt: datetime.date,
                     kpi_value: float,
                     green_target: float,
                     yellow_target: float) -> KpiZone:
    """
    What value of KPI is okay at the end?
    Assumption: KPI should improve monotonously during the month
    """
    _, month_days = calendar.monthrange(dt.year, dt.month)
    month_perc = dt.day / month_days

    if kpi_value >= green_target * month_perc:
        result = KpiZone.GREEN
    elif kpi_value >= yellow_target * month_perc:
        result = KpiZone.YELLOW
    else:
        result = KpiZone.RED

    return result
