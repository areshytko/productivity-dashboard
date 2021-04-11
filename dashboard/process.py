

from typing import Dict, Iterable, List

import pandas as pd

from dashboard.load import PomodorosProcessed
from dashboard.data import WeeklyStats, PomodoroStats, ActivityPomodorosData
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


def compute_descendants(children: Dict[str, List[str]], nodes: Iterable[str]) -> Dict[str, List[str]]:
    result = {}
    for node in nodes:
        descendants = []
        unprocessed = children.get(node, []).copy()
        while unprocessed:
            child = unprocessed.pop()
            descendants.append(child)
            unprocessed += children.get(child, [])
        result[node] = descendants
    return result


def compute_activity_pomodoros(data: PomodorosProcessed) -> ActivityPomodorosData:
    df = data.df.groupby('Activity').agg({
        'Pomodoros': 'sum',
        'Parent': 'max'
    }).reset_index()

    children = df.groupby('Parent').agg({
        'Activity': lambda x: x.to_list()
    }).reset_index()
    children = children.loc[children.Parent.str.len() > 0, :].set_index('Parent')
    children = children.Activity.to_dict()
    descendants_dict = compute_descendants(children, df.Activity)

    df.loc[:, 'Pomodoros_With_Subprojects'] = 0
    df.loc[:, 'Root_Project'] = df.Activity
    for idx, row in df.iterrows():
        descendants = descendants_dict[row['Activity']]
        descendants = df.Activity.isin(descendants)
        df.loc[idx, 'Pomodoros_With_Subprojects'] = df.loc[descendants, 'Pomodoros'].sum()
        if not row['Parent']:
            df.loc[descendants, 'Root_Project'] = row['Activity']

    df.loc[:, 'Pomodoros_With_Subprojects'] = df.Pomodoros_With_Subprojects + df.Pomodoros
    df.loc[:, ['Pomodoros', 'Pomodoros_With_Subprojects']].fillna(0, inplace=True)
    all_pomodoros = df.Pomodoros.sum()
    df.loc[:, 'Fraction'] = df.Pomodoros_With_Subprojects / all_pomodoros if all_pomodoros > 0 else 0
    df.sort_values('Pomodoros_With_Subprojects', ascending=False, inplace=True)

    return ActivityPomodorosData.convert(df)
