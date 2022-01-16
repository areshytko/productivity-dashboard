

from typing import Optional

import numpy as np

from dashboard.kpi.base import BaseKPI
from typedframe import TypedDataFrame


class DoLearnData(TypedDataFrame):
    schema = {
        'do': bool,
        'learn': bool,
        'Pomodoros': np.float64
    }


class DoLearnRatioKPI(BaseKPI):

    @staticmethod
    def compute_value(week: DoLearnData) -> Optional[float]:
        df = week.df
        do = df.loc[df['do'], 'Pomodoros'].sum()
        learn = df.loc[df['learn'], 'Pomodoros'].sum()

        if do == 0 and learn == 0:
            return None

        return do / (do + learn)
