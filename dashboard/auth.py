
from typing import Optional

import streamlit as st

from dashboard.gheets import Credentials, ManualFlow


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
