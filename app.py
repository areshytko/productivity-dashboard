
import streamlit as st

from dashboard.auth import authenticate
from dashboard.widgets import *
import dashboard.config as config
from dashboard.gheets import Credentials
from dashboard.load import PomodorosProcessed, load
from dashboard.process import compute_weekly_stats, compute_overall_stats,compute_activity_pomodoros
from dashboard.kpi import WeeklyDoneKPI
from dashboard.widgets import print_projects_pomodoros, projects_bar_chart

st.set_page_config(layout="wide")


@st.cache
def load_data(credentials: Credentials) -> PomodorosProcessed:
    return load(
        credentials=credentials,
        pomodoros_spreadsheet_id=config.POMODOROS_SPREADSHEET_ID,
        pomodoros_range=config.POMODOROS_RANGE,
        activities_spreadsheet_id=config.ACTIVITIES_SPREADSHEET_ID,
        activities_range=config.ACTIVITIES_RANGE
    )


sidebar()

creds = authenticate()
if creds:
    raw_data = load_data(creds)
    weekly_stats = compute_weekly_stats(raw_data)
    overall_stats = compute_overall_stats(raw_data)
    weekly_done_kpi = WeeklyDoneKPI(weekly_stats, raw_data)
    projects = compute_activity_pomodoros(raw_data)

    print_current_kpi(weekly_done_kpi)
    print_suggested_action(weekly_done_kpi)

    pomodoros_bar_chart(weekly_stats)

    left_column, right_column = st.beta_columns(2)

    with left_column:
        red_green_pomodoros_bar_chart(weekly_stats)
        done_planned_pomodoros_bar_chart(weekly_stats)

    with right_column:
        do_learn_pomodoros_bar_chart(weekly_stats)
        balance_coef_line_chart(weekly_stats)

    projects_bar_chart(weeks=raw_data, projects=projects)

    left_column, right_column = st.beta_columns(2)
    with left_column:
        projects_treemap_chart(raw_data)
    with right_column:
        st.subheader(" ")
        print_projects_pomodoros(projects)

    _, center_column, _ = st.beta_columns(3)
    with center_column:
        overall_stats_table(overall_stats)

    historical_data_table(weekly_stats)
