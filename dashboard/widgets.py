import datetime
from math import floor
from typing import List
import json

import streamlit as st
from streamlit_echarts import st_echarts
import plotly.express as px
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from dashboard.config import Config
from dashboard.kpi.rotten import build_rotten_projects_table
from dashboard.monthly import MonthlyPercentageKPI, MonthlyGoalsData
from dashboard.process import ActivityPomodorosData
from dashboard.load import PomodorosProcessed
from dashboard.process import WeeklyStats, PomodoroStats
from dashboard.kpi import WeeklyDoneKPI, KpiZone


class ProjectDataFrameColorStyler:

    def __init__(self, data: ActivityPomodorosData, colormap: List[str]):
        df = data.df.sort_values('Pomodoros_With_Subprojects', ascending=False)
        colors = {}
        idx = 0
        for _, row in df.iterrows():
            if row['Root_Project'] not in colors and idx < len(colormap):
                colors[row['Root_Project']] = colormap[idx]
                idx += 1
        self.colormap = colors

    def __call__(self, row):
        color = self.colormap.get(row['Root_Project'], 'white')
        return [f"background-color: {color}"] + ['']*(len(row) - 1)


def print_projects_pomodoros(data: ActivityPomodorosData):
    colormap = px.colors.qualitative.Pastel + px.colors.qualitative.D3
    df = data.df[['Activity', 'Fraction', 'Pomodoros_With_Subprojects', 'Pomodoros', 'Parent', 'Root_Project']]
    df.rename(columns={'Pomodoros_With_Subprojects': 'All Pomodoros'}, inplace=True)

    float_cols = [x for x in df.columns if df.dtypes[x] == np.float64]
    style = {col: "{:.2f}" for col in float_cols}

    df = (df.reset_index(drop=True).style
          .apply(ProjectDataFrameColorStyler(data, colormap), axis=1)
          .format(style).set_table_styles('styles'))
    st.dataframe(df)


def projects_bar_chart(weeks: PomodorosProcessed, projects: ActivityPomodorosData):
    st.subheader("Projects Weekly Done History:")
    df = pd.merge(weeks.df, projects.df[['Activity', 'Pomodoros_With_Subprojects', 'Root_Project']], on='Activity')
    df.sort_values(by='Pomodoros_With_Subprojects', ascending=False, inplace=True)
    fig = px.bar(df, x='Week', y='Pomodoros', color='Root_Project', hover_name='Activity',
                 color_discrete_sequence=px.colors.qualitative.Pastel + px.colors.qualitative.D3)
    st.plotly_chart(fig, use_container_width=True)


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
    df = weekly_stats.df.copy()
    df.planned.fillna(0, inplace=True)
    df.loc[:, 'not done'] = np.maximum(0, df.planned - df.done)
    st.bar_chart(df[['Week', 'done', 'not done']].set_index('Week'))


def pomodoros_bar_chart(weekly_stats: WeeklyStats):
    st.subheader("Pomodoros Weekly History:")
    st.bar_chart(weekly_stats.df[['Week', 'done']].rename(columns={'done': '# pom.'}).set_index('Week'))


def projects_pie_chart(raw_data: PomodorosProcessed):
    st.subheader("Projects:")
    fig = px.pie(raw_data.df, values='Pomodoros', names='Activity',
                 color_discrete_sequence=px.colors.qualitative.Pastel + px.colors.qualitative.D3)
    fig.update_traces(textposition='inside')
    st.plotly_chart(fig, use_container_width=True)


def projects_sunburst_chart(raw_data: PomodorosProcessed):
    st.subheader("Projects:")
    data = raw_data.df.groupby('Activity').agg({
        'Pomodoros': 'sum',
        'Parent': 'max'
    })

    fig = px.sunburst(
        data.reset_index(),
        values='Pomodoros',
        names='Activity',
        parents='Parent',
        color_discrete_sequence=px.colors.qualitative.Pastel + px.colors.qualitative.D3)
    st.plotly_chart(fig, use_container_width=True)


def projects_treemap_chart(raw_data: PomodorosProcessed):
    data = raw_data.df.groupby('Activity').agg({
        'Pomodoros': 'sum',
        'Parent': 'max'
    })

    fig = px.treemap(
        data.reset_index(),
        values='Pomodoros',
        names='Activity',
        parents='Parent',
        color_discrete_sequence=px.colors.qualitative.Pastel + px.colors.qualitative.D3)
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


def print_current_pomodoros_kpi(weekly_done_kpi: WeeklyDoneKPI):
    value = _text(weekly_done_kpi.value, color=zone_color(weekly_done_kpi.zone), size=2)
    target = _text(weekly_done_kpi.target, color=zone_color(weekly_done_kpi.zone), size=2)
    st.markdown(value + " of " + target + " pomodoros done this week.", unsafe_allow_html=True)


def print_pomodoros_suggested_action(weekly_done_kpi: WeeklyDoneKPI):
    formatter = lambda x: _text(x, color=zone_color(weekly_done_kpi.zone), size=2)
    st.markdown(weekly_done_kpi.suggested_action(formatter=formatter), unsafe_allow_html=True)


def print_current_monthly_kpi(kpi: MonthlyPercentageKPI):
    kpi_data = kpi.get_current_kpi()
    gp_to_finish, next_deadline = kpi.gp_to_finish_this_week()
    kpi_value = _text(str(round(kpi_data['kpi'], 2)), color=zone_color(kpi_data['zone']), size=2)
    kpi_target = _text(str(round(kpi_data['target'], 2)), color=zone_color(kpi_data['zone']), size=2)
    goals_planned = _text(str(kpi_data['goals_planned']), color=zone_color(kpi_data['zone']), size=1.5)
    goals_achieved = _text(str(kpi_data['goals_done']), color=zone_color(kpi_data['zone']), size=1.5)
    gp_to_finish = _text(gp_to_finish, color=zone_color(kpi_data['zone']), size=2)

    def deadline(dt: datetime.datetime) -> str:
        dows = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow = dows[dt.date().weekday()]
        return f"{dow}"

    st.markdown(f"{kpi_value} monthly goal points achieved. Target value: {kpi_target}. You have achieved {goals_achieved} goals of {goals_planned} planned.", unsafe_allow_html=True)
    st.markdown(f"Achieve {gp_to_finish} goal points till {deadline(next_deadline)}.", unsafe_allow_html=True)


def monthly_kpi_bar_chart(kpi: MonthlyPercentageKPI):
    st.subheader("Monthly KPI History:")
    df = kpi.df[['month', 'kpi']]
    df.month = df.month.dt.date
    df['a'] = 1 - df.kpi
    st.bar_chart(df.rename(columns={'kpi': 'gp %'}).set_index('month'))

def monthly_kpi_bar_chart_2(kpi: MonthlyPercentageKPI):
    import altair as alt

    df = kpi.df[['month', 'kpi']]
    df.month = df.month.map(lambda x: f"{x.year}-{x.month}")
    df['type'] = 'done'
    df2 = df.copy()
    df2['type'] = 'undone'
    df2.kpi = 1 - df2.kpi
    df = pd.concat([df, df2])

    c = alt.Chart(df).mark_bar().encode(
        y=alt.Y('sum(kpi)', stack="normalize", axis=alt.Axis(title=None)),
        x=alt.X('month', axis=alt.Axis(title=None)),
        color='type',
        order=alt.Order(
            'type',
            sort='ascending'
        )
    )
    st.subheader("Monthly KPI History:")
    st.altair_chart(c, use_container_width=True)


def monthly_goals_tree(goals: MonthlyGoalsData):

    cmap = plt.get_cmap('viridis')

    def float2int(c):
        f2 = max(0.0, min(1.0, c))
        return floor(255 if f2 == 1.0 else f2 * 256.0)

    def colorize(node):
        r, g, b, a = cmap(float(node['done']))
        return {**node, **{
            'itemStyle': {
                'color': '#%02x%02x%02x' % (float2int(r), float2int(g), float2int(b))
            }
        }}

    data = goals.as_tree(node_formatter=colorize)
    options = {
        'tooltip': {
            'trigger': 'item',
            'triggerOn': 'mousemove'
        },
        'series': [
            {
                'type': 'tree',
                'id': 0,
                'name': 'tree1',
                'data': [data],
                # 'top': '10%',
                'left': '5%',
                # 'bottom': '1%',
                # 'right': '20%',
                'symbolSize': 7,
                'edgeShape': 'polyline',
                'edgeForkPosition': '50%',
                'initialTreeDepth': 3,
                'lineStyle': {
                    'width': 2
                },
                'label': {
                    'backgroundColor': '#fff',
                    'position': 'left',
                    'verticalAlign': 'middle',
                    'align': 'right'
                },
                'leaves': {
                    'label': {
                        'position': 'right',
                        'verticalAlign': 'middle',
                        'align': 'left'
                    }
                },
                'emphasis': {
                    'focus': 'descendant'
                },
                'expandAndCollapse': True
            }
        ]
    }

    st_echarts(options=options, height=Config().MONTHLY_GOALS_TREE_CHART_HEIGHT)


def print_monthly_goals(goals: MonthlyGoalsData):
    goals = goals.get_current_goals()
    st.dataframe(goals.df)

    def format_subgoal(row) -> str:
        result = row['Subgoal']
        if row['Done'] == 1:
            result = f"~~*{result}*~~"
        return f"  - {result}"

    def format_goal(row) -> str:
        result = row['Goal']
        if row['Done'] == 1:
            result = f"~~*{result}*~~"
        return f"- {result}"

        text = "\n".join([format_subgoal(row) for _, row in x.iterrows() if len(row['Subgoal']) > 0 and row['Subgoal'] != 'None'])
        return pd.DataFrame({'subgoal_text': text, 'Done': (x['Done'] == 1).all()}, index=[x.index[0]])

    def collect_goals(x):
        text = "\n".join([f"{format_goal(row)}\n{row['subgoal_text']}" for _, row in x.iterrows()])
        return pd.DataFrame({'text': text}, index=[x.index[0]])

    df = goals.df.groupby(['Strategic Track', 'Goal']).apply(collect_subgoals)
    df = df.reset_index().groupby('Strategic Track').apply(collect_goals).reset_index()
    text = "\n".join([f"### {row['Strategic Track']}\n{row['text']}" for _, row in df.iterrows()])
    st.markdown(text)


def sidebar(config: Config):
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


def rotten_projects_table(raw_data: PomodorosProcessed):
    data = build_rotten_projects_table(raw_data)
    config = Config()
    green_threshold = config.ROTTEN_PROJECT_GREEN_THRESHOLD
    yellow_threshold = config.ROTTEN_PROJECT_YELLOW_THRESHOLD

    def colorize(row):
        days = row['Inactive Days']
        if days < 0:
            color = 'white'
        elif days <= green_threshold:
            color = 'rgb(210, 229, 158)'
        elif days <= yellow_threshold:
            color = 'rgb(252, 231, 128)'
        else:
            color = 'rgb(255, 143, 102)'
        return [f"background-color: {color}"] * len(row)

    st.subheader("Current Active Project Rotten Table:")
    df = data.df.sort_values(by='Inactive Days', ascending=False).reset_index(drop=True).style.apply(colorize, axis=1)
    st.dataframe(df)
