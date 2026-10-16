import streamlit as st

import db
from styles import inject_styles

st.set_page_config(page_title="Pomo Log", layout="wide")

db.init_db()
inject_styles()

pages = [
    st.Page("views/manage.py", title="Manage", default=True),
]
st.navigation(pages).run()
