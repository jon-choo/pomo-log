"""Today: the focus screen while timing, otherwise the day at a glance."""

from __future__ import annotations

import html
from datetime import datetime

import streamlit as st

import db
import stats
import timer
from focus import focus_screen, in_focus
from formatting import format_duration
from timeutil import day_bounds_utc, sgt_date, to_sgt, week_bounds_utc
from ui import show_flash

MODE_LABELS = {"pomodoro": "Pomodoro", "freeform": "Free", "manual": "Manual"}


def plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def start_session(subject_id: int, mode_label: str) -> None:
    mode = "freeform" if mode_label == "Free" else "pomodoro"
    try:
        timer.start_timer(subject_id, mode)
    except ValueError as error:
        st.error(str(error))
        return
    st.session_state["focus_left"] = False
    st.rerun()


def render_facts() -> None:
    today = sgt_date()
    goal = stats.weekly_goal_progress(today)
    week_seconds = goal["actual_seconds"]
    week_value = format_duration(week_seconds)
    if goal["goal_minutes"]:
        week_value += f" of {format_duration(goal['goal_minutes'] * 60)}"

    def fact(label: str, value: str) -> str:
        return f'<div><span class="caption">{label}</span><span class="value">{html.escape(value)}</span></div>'

    st.html(
        '<div class="facts">'
        + fact("This week", week_value)
        + fact("Today", format_duration(stats.today_total(today)))
        + fact("Streak", plural(stats.current_streak(today), "day"))
        + "</div>"
    )
    if goal["percent"] is not None:
        st.html(f'<div class="goal-rule"><span style="width:{goal["percent"]:.1f}%"></span></div>')
    else:
        st.html('<div class="goal-rule"></div>')
        st.page_link("views/settings.py", label="Set a weekly goal")


def render_sessions() -> None:
    st.header("Today")
    today = sgt_date()
    start, end = day_bounds_utc(today)
    sessions = db.list_sessions(start=start, end=end, newest_first=False)
    if not sessions:
        st.markdown('<p class="muted">Nothing logged yet today.</p>', unsafe_allow_html=True)
        return

    names = {s["id"]: s["name"] for s in db.list_subjects(include_archived=True)}
    rows = ""
    for session in sessions:
        at = "–" if session["mode"] == "manual" else to_sgt(datetime.fromisoformat(session["start_time"])).strftime("%H:%M")
        rows += (
            f"<tr><td>{at}</td><td>{html.escape(names[session['subject_id']])}</td>"
            f"<td class='num'>{format_duration(session['duration_seconds'])}</td>"
            f"<td>{MODE_LABELS[session['mode']]}</td></tr>"
        )
    st.html(
        '<table class="ruled"><thead><tr><th>Start</th><th>Subject</th>'
        f'<th class="num">Length</th><th>Mode</th></tr></thead><tbody>{rows}</tbody></table>'
    )


def render_start_list(active: timer.TimerState | None) -> None:
    st.header("Start")
    subjects = db.list_subjects()
    if not subjects:
        st.markdown('<p class="muted">No subjects yet.</p>', unsafe_allow_html=True)
        st.page_link("views/manage.py", label="Add your first subject")
        return

    if active is not None:
        st.markdown(
            '<p class="muted">A session is running. Return to focus to stop it before starting another.</p>',
            unsafe_allow_html=True,
        )
    else:
        work, rest = timer.get_pomodoro_lengths()
        mode = st.radio(
            "Mode", ["Pomodoro", "Free"], horizontal=True, key="start-mode", label_visibility="collapsed"
        )
        note = f"{work} min work, {rest} min break" if mode == "Pomodoro" else "Counts up until you stop"
        st.markdown(f'<p class="muted">{note}</p>', unsafe_allow_html=True)

    categories = {c["id"]: c["name"] for c in db.list_categories(include_archived=True)}
    week_start, week_end = week_bounds_utc(sgt_date())
    week_seconds = {
        row["subject_id"]: row["total_seconds"] for row in stats.breakdown_by_subject(week_start, week_end)
    }
    ordered = sorted(subjects, key=lambda s: (categories[s["category_id"]].lower(), s["name"].lower()))
    for subject in ordered:
        with st.container(key=f"row-{subject['id']}"):
            name_col, time_col, action_col = st.columns([5, 3, 2], vertical_alignment="center")
            name_col.html(
                f'<span class="subject">{html.escape(subject["name"])}</span>'
                f'<span class="sub">{html.escape(categories[subject["category_id"]])}</span>'
            )
            time_col.html(f'<span class="num">{format_duration(week_seconds.get(subject["id"], 0))}</span>')
            if active is None and action_col.button("Start", key=f"start-{subject['id']}"):
                start_session(subject["id"], mode)


def render_today(active: timer.TimerState | None) -> None:
    st.title(sgt_date().strftime("%A %d %B"))
    show_flash()
    render_facts()
    sessions_col, start_col = st.columns([5, 4], gap="large")
    with sessions_col:
        render_sessions()
    with start_col:
        render_start_list(active)


active = timer.get_active_timer()
if in_focus(active):
    focus_screen()
else:
    render_today(active)
