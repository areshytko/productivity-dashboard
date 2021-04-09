

import pandas as pd

from dashboard.load import PomodorosProcessed
from dashboard.data import WeeklyStats, PomodoroStats
from dashboard.kpi import DoLearnRatioKPI, DoLearnData, RedGreenRatioKPI, RedGreenData, BalanceCoefKPI, BalanceCoefData


def process_week(week: int, df: pd.DataFrame) -> pd.DataFrame:

    result = {
        'from_date': df.Date.min(),
        'to_date': df.Date.max(),
        'done': df.Pomodoros.sum(),
        'planned': df.Planned.sum(),
        'avg_done': None,
        'avg_planned': None,
        'do_learn_ratio': DoLearnRatioKPI.compute_value(DoLearnData(df)),
        'red_green_ratio': RedGreenRatioKPI.compute_value(RedGreenData(df)),
        'balance_coef': BalanceCoefKPI.compute_value(BalanceCoefData(df))
    }
    result['avg_done'] = result['done'] / 7
    result['avg_planned'] = result['planned'] / 7
    return pd.DataFrame(result, index=[week])


def complete_rate(df: pd.DataFrame) -> pd.Series:
    return df['done'] / df['planned']


def compute_weekly_stats(data: PomodorosProcessed) -> WeeklyStats:
    result = pd.concat([process_week(week, df) for week, df in data.df.groupby('Week')])
    result['complete_rate'] = complete_rate(result)
    result = WeeklyStats.convert(result.reset_index().rename(columns={'index':'Week'}))
    return result


def compute_overall_stats(data: PomodorosProcessed) -> PomodoroStats:
    df = data.df
    result = {
        'done': df.Pomodoros.sum(),
        'planned': df.Planned.sum(),
        'avg_done': None,
        'avg_planned': None,
        'do_learn_ratio': DoLearnRatioKPI.compute_value(DoLearnData(df)),
        'red_green_ratio': RedGreenRatioKPI.compute_value(RedGreenData(df)),
        'balance_coef': BalanceCoefKPI.compute_value(BalanceCoefData(df))
    }
    result['complete_rate'] = result['done'] / result['planned']
    num_days = len(df['Date'].unique())
    result['avg_done'] = result['done'] / num_days
    result['avg_planned'] = result['planned'] / num_days
    return PomodoroStats.convert(pd.DataFrame(result, index=[0]))


# last_n_weeks_mean: (WeeklyStats, N) -> WeeklyStats

# current_kpi: (WeeklyStats) -> WeeklyStats

# today_done, planned: (PomodorosProcessed) -> tuple[int, int]

# current week KPI zones mechanism: percentage improvement from historical period

# suggested actions

# result: WeeklyDoneKPI, CompleteRateKPI, WeeklyStats
