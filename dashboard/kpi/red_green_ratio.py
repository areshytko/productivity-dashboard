

from typing import Optional

import numpy as np

from dashboard.kpi.base import BaseKPI
from typedframe import TypedDataFrame


class RedGreenData(TypedDataFrame):
    schema = {
        'green': bool,
        'red': bool,
        'Pomodoros': np.float64
    }


class RedGreenRatioKPI(BaseKPI):

    @staticmethod
    def compute_value(week: RedGreenData) -> Optional[float]:
        df = week.df
        green = df.loc[df['green'], 'Pomodoros'].sum()
        red = df.loc[df['red'], 'Pomodoros'].sum()

        if green == 0 and red == 0:
            return None

        return red / (green + red)
