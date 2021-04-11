"""
Defines the schema and retrieval for the data
"""

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
        'Planned': np.float64
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
    result = merge_data(pomodoros=pomodoros, catalog=catalog)
    return result


def load_pomodoros(credentials: Credentials,
                   spreadsheet_id: str,
                   range_name: str) -> Pomodoros:
    data = get_data(
        token=credentials,
        spreadsheet_id=spreadsheet_id,
        range_name=range_name,
        merged_cols=['Week', 'Date']
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


def merge_data(pomodoros: Pomodoros, catalog: ActivitiesCatalog) -> PomodorosProcessed:
    activity_dict = {x['Activity']: (x.get('Tags', []), x.get('Parent', "")) for x in catalog.data}
    tags = pomodoros.df.Activity.map(lambda x: activity_dict[x][0])
    tags_df = boolean_df(tags, ActivitiesCatalog.TAGS)
    df = pd.concat([pomodoros.df, tags_df], axis=1)
    df.loc[:, 'Parent'] = pomodoros.df.Activity.map(lambda x: activity_dict[x][1])
    return PomodorosProcessed(df)


def boolean_df(item_lists: pd.Series, unique_items: List[Any]) -> pd.DataFrame:
    bool_dict = {}

    for item in unique_items:
        bool_dict[item] = item_lists.apply(lambda x: item in x)
    return pd.DataFrame(bool_dict)
