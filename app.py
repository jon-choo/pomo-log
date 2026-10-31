import streamlit as st

import db
import timer
from focus import in_focus, running_line
from styles import inject_styles

st.set_page_config(page_title="Pomo Log", layout="wide", initial_sidebar_state="collapsed")

db.init_db()
inject_styles()

today = st.Page("views/today.py", title="Today", default=True)
manage = st.Page("views/manage.py", title="Manage")
settings = st.Page("views/settings.py", title="Settings")
pages = [today, manage, settings]
current = st.navigation(pages, position="hidden")
active = timer.get_active_timer()

if not (current.title == today.title and in_focus(active)):
    with st.container(key="topnav"):
        columns = st.columns([2, 1, 1, 1, 7], vertical_alignment="center")
        columns[0].markdown('<span class="wordmark">Pomo Log</span>', unsafe_allow_html=True)
        for column, page in zip(columns[1:], pages):
            if page.title == current.title:
                column.markdown(f'<span class="nav-current">{page.title}</span>', unsafe_allow_html=True)
            else:
                column.page_link(page, label=page.title)
    if active is not None:
        running_line()

current.run()
