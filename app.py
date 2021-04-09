
from typing import Optional
import json

import streamlit as st
import plotly.express as px
import numpy as np

import dashboard.config as config
from dashboard.gheets import Credentials, ManualFlow
from dashboard.load import PomodorosProcessed, load
from dashboard.process import compute_weekly_stats, compute_overall_stats, WeeklyStats, PomodoroStats
from dashboard.kpi import WeeklyDoneKPI, KpiZone


st.set_page_config(layout="wide")


def rerun():
    raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))


def authenticate() -> Optional[Credentials]:
    flow = ManualFlow()
    creds = flow.get_google_token()
    if not creds:
        url = flow.get_url()
        st.write("Follow the URL for authentication:")
        st.write(url)
        code = st.text_input('Enter the obtained code here:')
        if code:
            flow.put_code(code)
            rerun()
    return creds


@st.cache
def load_data(credentials: Credentials) -> PomodorosProcessed:
    return load(
        credentials=credentials,
        pomodoros_spreadsheet_id=config.POMODOROS_SPREADSHEET_ID,
        pomodoros_range=config.POMODOROS_RANGE,
        activities_spreadsheet_id=config.ACTIVITIES_SPREADSHEET_ID,
        activities_range=config.ACTIVITIES_RANGE
    )


def red_green_pomodoros_bar_chart(weekly_stats: WeeklyStats):
    st.subheader("Red/Green Pomodoros Weekly Done History:")
    df = weekly_stats.df[['Week']]
    df['red'] = weekly_stats.df.done * weekly_stats.df['red_green_ratio']
    df['green'] = weekly_stats.df.done * (1 - weekly_stats.df['red_green_ratio'])
    st.bar_chart(df.set_index('Week'))


def do_learn_pomodoros_bar_chart(weekly_stats: WeeklyStats):
    st.subheader("Do/Learn Pomodoros Weekly Done History:")
    # st.bar_chart(weekly_stats.df.set_index('from_date')['done'])
    df = weekly_stats.df[['Week']]
    df['do'] = weekly_stats.df.done * weekly_stats.df['do_learn_ratio']
    df['learn'] = weekly_stats.df.done * (1 - weekly_stats.df['do_learn_ratio'])
    st.bar_chart(df.set_index('Week'))


def balance_coef_line_chart(weekly_stats: WeeklyStats):
    st.subheader("Balance Coefficient History:")
    st.line_chart(weekly_stats.df.set_index('from_date')['balance_coef'])


def overall_stats_table(overall_stats: PomodoroStats):
    st.subheader(f"Overall Statistics:")
    df = overall_stats.df.transpose()
    df.rename(columns={0: 'value'}, inplace=True)
    # df = df.style.format("{:.2f}").set_table_styles('styles')
    st.dataframe(df)


def historical_data_table(weekly_stats: WeeklyStats):
    st.subheader("Weekly Stats Historical Data:")
    float_cols = [x for x in weekly_stats.df.columns if weekly_stats.df.dtypes[x] == np.float64]
    style = {
        'from_date': lambda x: "{}".format(x.strftime('%m/%d/%Y')),
        'to_date': lambda x: "{}".format(x.strftime('%m/%d/%Y')),
        'done': "{:.0f}",
        'planned': "{:.0f}",
        'avg_done': "{:.0f}",
        'avg_planned': "{:.0f}"
    }
    style = {**{col: "{:.2f}" for col in float_cols}, **style}
    df = weekly_stats.df.style.format(style).set_table_styles('styles')
    st.dataframe(df)


def done_planned_pomodoros_bar_chart(weekly_stats: WeeklyStats):
    st.subheader("Done and Planned Pomodoros Weekly History:")
    st.bar_chart(weekly_stats.df[['Week', 'planned', 'done']].set_index('Week'))


def projects_pie_chart(raw_data: PomodorosProcessed):
    st.subheader("Projects:")
    fig = px.pie(raw_data.df, values='Pomodoros', names='Activity',
                 color_discrete_sequence=px.colors.qualitative.Set3)
    fig.update_traces(textposition='inside')
    st.plotly_chart(fig, use_container_width=True)


def _text(text: str, color: str, size: int = 1) -> str:
    return f"<span style='color:{color};font-size:{size}rem;'>{text}</span>"


def zone_color(zone: KpiZone) -> str:
    if zone == KpiZone.GREEN:
        return 'green'
    elif zone == KpiZone.YELLOW:
        return 'orange'
    elif zone == KpiZone.RED:
        return 'red'
    else:
        raise ValueError(f"Unknown KPI Zone: {zone}")


def print_current_kpi(weekly_done_kpi: WeeklyDoneKPI):
    value = _text(weekly_done_kpi.value, color=zone_color(weekly_done_kpi.zone), size=2)
    target = _text(weekly_done_kpi.target, color=zone_color(weekly_done_kpi.zone), size=2)
    st.markdown(value + " of " + target + " pomodoros done this week.", unsafe_allow_html=True)


def print_suggested_action(weekly_done_kpi: WeeklyDoneKPI):
    formatter = lambda x: _text(x, color=zone_color(weekly_done_kpi.zone), size=2)
    st.markdown(weekly_done_kpi.suggested_action(formatter=formatter), unsafe_allow_html=True)


def sidebar():
    config.KPI_IMPROVEMENT_RATE = st.sidebar.number_input(
        "KPI improvement rate",
        min_value=1.0,
        max_value=10.0,
        value=config.KPI_IMPROVEMENT_RATE
    )

    config.KPI_HISTORICAL_WINDOW = st.sidebar.slider(
        "KPI historical window",
        min_value=1,
        max_value=10,
        value=config.KPI_HISTORICAL_WINDOW
    )

    config.BALANCE_LIFE_DISTRIBUTION = json.loads(st.sidebar.text_input(
        "Balanced life distribution: [life, personal, career, hobby, society, health]",
        config.BALANCE_LIFE_DISTRIBUTION)
    )


sidebar()

creds = authenticate()
if creds:
    raw_data = load_data(creds)
    weekly_stats = compute_weekly_stats(raw_data)
    overall_stats = compute_overall_stats(raw_data)
    weekly_done_kpi = WeeklyDoneKPI(weekly_stats, raw_data)

    print_current_kpi(weekly_done_kpi)
    print_suggested_action(weekly_done_kpi)

    left_column, right_column = st.beta_columns(2)

    with left_column:
        red_green_pomodoros_bar_chart(weekly_stats)
        done_planned_pomodoros_bar_chart(weekly_stats)
        projects_pie_chart(raw_data)

    with right_column:
        do_learn_pomodoros_bar_chart(weekly_stats)
        balance_coef_line_chart(weekly_stats)
        overall_stats_table(overall_stats)

    historical_data_table(weekly_stats)
