"""Weekly goal and Pomodoro lengths."""

import streamlit as st

import stats
import timer
from styles import narrow_page
from ui import run_action, show_flash

narrow_page()

st.title("Settings")

show_flash()

# Weekly goal

st.header("Weekly goal")
st.markdown(
    '<p class="muted">Hours of study per week, counted from Sunday. Set to 0 for no goal.</p>',
    unsafe_allow_html=True,
)

goal_minutes = stats.weekly_goal_progress()["goal_minutes"] or 0
with st.form("weekly_goal", border=False):
    hours_col, button_col = st.columns([3, 2], vertical_alignment="bottom")
    hours = hours_col.number_input("Hours per week", min_value=0.0, max_value=168.0, step=0.5, value=goal_minutes / 60)
    if button_col.form_submit_button("Save goal", type="primary", use_container_width=True):
        run_action(lambda: stats.set_weekly_goal(round(hours * 60)), "Weekly goal saved.")

# Pomodoro

st.header("Pomodoro")
st.markdown('<p class="muted">Applies to sessions you start from now on.</p>', unsafe_allow_html=True)

work_minutes, break_minutes = timer.get_pomodoro_lengths()
with st.form("pomodoro_lengths", border=False):
    work_col, break_col, button_col = st.columns([2, 2, 2], vertical_alignment="bottom")
    work = work_col.number_input("Work minutes", min_value=1, max_value=240, step=1, value=work_minutes)
    rest = break_col.number_input("Break minutes", min_value=1, max_value=120, step=1, value=break_minutes)
    if button_col.form_submit_button("Save lengths", type="primary", use_container_width=True):
        run_action(lambda: timer.set_pomodoro_lengths(int(work), int(rest)), "Pomodoro lengths saved.")
