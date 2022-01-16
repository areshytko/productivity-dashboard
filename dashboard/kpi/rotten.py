"""
Rotten Projects Table
"""
import datetime

import numpy as np
import pandas as pd

from dashboard.load import PomodorosProcessed
from typedframe import TypedDataFrame


class RottenTable(TypedDataFrame):
    schema={
        'Activity': object,
        'Inactive Days': np.int16
    }


def build_rotten_projects_table(raw_data: PomodorosProcessed) -> RottenTable:
    today = pd.to_datetime(datetime.date.today())
    result = []
    non_zero_pomodoros = (raw_data.df.Pomodoros > 0)
    for project in PomodorosProcessed.active_projects:
        current_project = (raw_data.df.Activity == project)
        history = raw_data.df.loc[current_project & non_zero_pomodoros, ]
        if len(history) > 0:
            last_active_day = history.Date.max()
            result.append((project, (today - last_active_day).days))
        else:
            result.append((project, -1))
    return RottenTable.convert(pd.DataFrame(result, columns=['Activity', 'Inactive Days']))
