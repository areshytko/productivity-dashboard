"""
Defines the schema and retrieval for the data
"""
import datetime
from typing import Any, List

import numpy as np
import pandas as pd

from dashboard.gheets import Credentials, get_data
from dashboard.jsondata import JsonData
from dashboard.typed import TypedDataFrame


class Pomodoros(TypedDataFrame):
    schema = {
        'Week': np.int16,
        'Date': np.dtype('datetime64[ns]'),
        'Activity': object,
        'Comment': object,
        'Pomodoros': np.float64,
        'Planned': np.float64,
        'Weekly Done KPI': np.float64
    }


class ActivitiesCatalog(JsonData):

    TAGS = ['learn', 'do', 'career', 'green', 'red',
            'personal', 'hobby', 'society', 'life', 'health']

    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "Activity": {
                    "type": "string"
                },
                "Active": {
                    "type": "boolean"
                },
                "Tags": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": TAGS
                    },
                    "uniqueItems": True
                },
                "Comment": {
                    "type": "string"
                },
                "Parent": {
                    "type": "string"
                }
            },
            "required": ['Activity', "Active"]
        }
    }


class PomodorosProcessed(Pomodoros):
    schema = {
        **{tag: bool for tag in ActivitiesCatalog.TAGS},
        **{"Parent": object}
    }
    active_projects = []


def load(credentials: Credentials,
         pomodoros_spreadsheet_id: str,
         pomodoros_range: str,
         activities_spreadsheet_id: str,
         activities_range: str) -> PomodorosProcessed:
    pomodoros = load_pomodoros(
        credentials=credentials,
        spreadsheet_id=pomodoros_spreadsheet_id,
        range_name=pomodoros_range
    )
    catalog = load_catalog(
        credentials=credentials,
        spreadsheet_id=activities_spreadsheet_id,
        range_name=activities_range
    )

    PomodorosProcessed.active_projects = [x['Activity'] for x in catalog.data if x['Active']]

    result = merge_data(pomodoros=pomodoros, catalog=catalog)
    return result


def load_pomodoros(credentials: Credentials,
                   spreadsheet_id: str,
                   range_name: str) -> Pomodoros:
    data = get_data(
        token=credentials,
        spreadsheet_id=spreadsheet_id,
        range_name=range_name,
        merged_cols=['Week', 'Date', 'Weekly Done KPI']
    )

    return Pomodoros.convert(data)


def load_catalog(credentials: Credentials,
                 spreadsheet_id: str,
                 range_name: str) -> ActivitiesCatalog:
    data = get_data(
        token=credentials,
        spreadsheet_id=spreadsheet_id,
        range_name=range_name
    )

    data.Active = data.Active.map(lambda x: x == 'TRUE')
    data.Tags = data.Tags.map(lambda x: x.split(',') if x else [])
    activities = data.to_dict(orient='records')
    activities = [{k: v for k, v in x.items() if v is not None} for x in activities]
    activities = ActivitiesCatalog(activities)

    return activities


def fill_all_activities(pomodoros: Pomodoros, catalog: ActivitiesCatalog) -> Pomodoros:
    activities = (x['Activity'] for x in catalog.data)
    week = pomodoros.df.Week.min()
    date = pomodoros.df.Date.min()
    template = {key: None for key in Pomodoros.schema.keys()}
    template = {**template, **{'Week': week, 'Date': date}}
    addon = pd.DataFrame([{**template, **{'Activity': x}} for x in activities])
    return Pomodoros.convert(pd.concat([pomodoros.df, addon]))


def assert_active_projects(pomodoros: Pomodoros, catalog: ActivitiesCatalog) -> List[str]:
    active_projects = [c['Activity'] for c in catalog.data if c['Active']]
    cond = (pomodoros.df.Date == (pd.to_datetime(datetime.date.today())))
    today_projects = set(pomodoros.df.loc[cond,]['Activity'])
    return [project for project in active_projects if project not in today_projects]


def merge_data(pomodoros: Pomodoros, catalog: ActivitiesCatalog) -> PomodorosProcessed:
    pomodoros = fill_all_activities(pomodoros=pomodoros, catalog=catalog)
    activity_dict = {x['Activity']: x for x in catalog.data}
    tags = pomodoros.df.Activity.map(lambda x: activity_dict[x].get('Tags', []))
    tags_df = boolean_df(tags, ActivitiesCatalog.TAGS)
    df = pd.concat([pomodoros.df, tags_df], axis=1)
    df.loc[:, 'Parent'] = pomodoros.df.Activity.map(lambda x: activity_dict[x].get('Parent', ""))
    return PomodorosProcessed(df)


def boolean_df(item_lists: pd.Series, unique_items: List[Any]) -> pd.DataFrame:
    bool_dict = {}

    for item in unique_items:
        bool_dict[item] = item_lists.apply(lambda x: item in x)
    return pd.DataFrame(bool_dict)
