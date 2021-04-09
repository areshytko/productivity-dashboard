
from typing import Optional

import numpy as np
import pandas as pd

import dashboard.config as config
from dashboard.kpi.base import BaseKPI
from dashboard.typed import TypedDataFrame


class BalanceCoefData(TypedDataFrame):
    LIFE_DOMAINS = ['life', 'personal', 'career', 'hobby', 'society', 'health']
    schema = {
        **{
            'Pomodoros': np.float64
        },
        **{domain: bool for domain in LIFE_DOMAINS}
    }


def mse(p, q):
    return np.sqrt(np.mean(np.sum(np.power((np.array(p) - np.array(q)), 2))))


class BalanceCoefKPI(BaseKPI):

    @staticmethod
    def desired_distr() -> pd.Series:
        return pd.Series(config.BALANCE_LIFE_DISTRIBUTION, index=BalanceCoefData.LIFE_DOMAINS)

    @staticmethod
    def compute_value(week: BalanceCoefData, desired_dist: Optional[pd.Series] = None) -> float:
        if desired_dist is not None:
            assert np.all(desired_dist.index == BalanceCoefData.LIFE_DOMAINS)
        else:
            desired_dist = BalanceCoefKPI.desired_distr()

        df = week.df
        all_pomodoros = df.Pomodoros.sum()
        actual_dist = [df.loc[df[col], 'Pomodoros'].sum() / all_pomodoros for col in BalanceCoefData.LIFE_DOMAINS]

        return mse(desired_dist, actual_dist)
