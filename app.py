# suggested actions
# currents KPIs: values, zones, targets
# historical stats

from typing import Optional

import streamlit as st
from st_aggrid import AgGrid

import dashboard.config as config
from dashboard.gheets import Credentials, ManualFlow
from dashboard.load import PomodorosProcessed, load


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


creds = authenticate()
if creds:
    st.write("All the app logic is here")
    data = load_data(creds)
    AgGrid(data.df)
