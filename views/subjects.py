"""Subjects home: card grid, and a page for each subject."""

from __future__ import annotations

import html
from datetime import datetime

import streamlit as st

import db
import stats
import timer
from formatting import format_duration
from timeutil import day_bounds_utc, sgt_date, to_sgt, week_bounds_utc
from timer_ui import timer_controls
from ui import show_flash, strip

CARDS_PER_ROW = 3
RECENT_LIMIT = 10
MODE_LABELS = {"pomodoro": "Pomodoro", "freeform": "Free", "manual": "Manual"}


def selected_subject_id() -> int | None:
    raw = st.query_params.get("subject")
    return int(raw) if raw and raw.isdigit() else None


def plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


# Grid

def render_card(subject: dict, category_name: str, week_seconds: int, is_running: bool) -> None:
    name = html.escape(subject["name"])
    chip = '<span class="chip">Running</span>' if is_running else ""
    with st.container(border=True, key=f"subject-card-{subject['id']}"):
        st.markdown(
            f'<div class="banner" style="background:{subject["color"]}">'
            f'<span class="banner-name">{name}</span></div>'
            f'<div class="card-body"><div class="card-row"><span class="muted">{html.escape(category_name)}</span>'
            f'{chip}</div><span class="card-time">{format_duration(week_seconds)} '
            f'<span class="muted">this week</span></span></div>',
            unsafe_allow_html=True,
        )
        if st.button(f"Open {subject['name']}", key=f"open-{subject['id']}"):
            st.query_params["subject"] = str(subject["id"])
            st.rerun()


def render_grid() -> None:
    st.title("Subjects")
    show_flash()

    today = sgt_date()
    week_start, week_end = week_bounds_utc(today)
    week_value = format_duration(stats.week_total(today))
    goal = stats.weekly_goal_progress(today)["goal_minutes"]
    if goal:
        week_value += f" of {format_duration(goal * 60)}"
    st.markdown(
        strip(
            [
                ("This week", week_value),
                ("Today", format_duration(stats.today_total(today))),
                ("Streak", plural(stats.current_streak(today), "day")),
            ]
        ),
        unsafe_allow_html=True,
    )

    subjects = db.list_subjects()
    if not subjects:
        st.markdown('<p class="muted">No subjects yet.</p>', unsafe_allow_html=True)
        st.page_link("views/manage.py", label="Add your first subject")
        return

    categories = {c["id"]: c["name"] for c in db.list_categories(include_archived=True)}
    week_seconds = {
        row["subject_id"]: row["total_seconds"]
        for row in stats.breakdown_by_subject(week_start, week_end)
    }
    active = timer.get_active_timer()
    ordered = sorted(subjects, key=lambda s: (categories[s["category_id"]].lower(), s["name"].lower()))

    for start in range(0, len(ordered), CARDS_PER_ROW):
        columns = st.columns(CARDS_PER_ROW)
        for column, subject in zip(columns, ordered[start : start + CARDS_PER_ROW]):
            with column:
                render_card(
                    subject,
                    categories[subject["category_id"]],
                    week_seconds.get(subject["id"], 0),
                    active is not None and active.subject_id == subject["id"],
                )


# Subject page

def render_recent_sessions(subject_id: int) -> None:
    st.header("Recent sessions")
    sessions = db.list_sessions(subject_id=subject_id)
    if not sessions:
        st.markdown('<p class="muted">No sessions yet.</p>', unsafe_allow_html=True)
        return

    rows = ""
    for session in sessions[:RECENT_LIMIT]:
        start = to_sgt(datetime.fromisoformat(session["start_time"]))
        at = "–" if session["mode"] == "manual" else start.strftime("%H:%M")
        rows += (
            f"<tr><td>{start.strftime('%a %d %b')}</td><td>{at}</td>"
            f"<td class='num'>{format_duration(session['duration_seconds'])}</td>"
            f"<td>{MODE_LABELS[session['mode']]}</td></tr>"
        )
    st.markdown(
        '<table class="board"><thead><tr><th>Date</th><th>Start</th>'
        f'<th class="num">Length</th><th>Mode</th></tr></thead><tbody>{rows}</tbody></table>',
        unsafe_allow_html=True,
    )
    if len(sessions) > RECENT_LIMIT:
        st.markdown(
            f'<p class="muted">Showing the latest {RECENT_LIMIT} of {len(sessions)}.</p>',
            unsafe_allow_html=True,
        )


def render_subject(subject_id: int) -> None:
    subject = db.get_subject(subject_id)
    if subject is None or subject["archived"]:
        st.query_params.clear()
        st.rerun()

    if st.button("All subjects", key="back"):
        st.query_params.clear()
        st.rerun()
    show_flash()

    category = db.get_category(subject["category_id"])
    st.markdown(
        f'<div class="banner banner-large" style="background:{subject["color"]}">'
        f'<span class="banner-name">{html.escape(subject["name"])}</span>'
        f'<span class="banner-sub">{html.escape(category["name"])}</span></div>',
        unsafe_allow_html=True,
    )

    today = sgt_date()
    week_start, week_end = week_bounds_utc(today)
    day_start, day_end = day_bounds_utc(today)
    totals = {
        "This week": stats.total_seconds(week_start, week_end, subject_id=subject_id),
        "Today": stats.total_seconds(day_start, day_end, subject_id=subject_id),
        "All time": stats.total_seconds(subject_id=subject_id),
    }
    st.markdown(
        strip([(label, format_duration(seconds)) for label, seconds in totals.items()]),
        unsafe_allow_html=True,
    )

    timer_controls(subject_id)
    render_recent_sessions(subject_id)


subject_id = selected_subject_id()
if subject_id is None:
    render_grid()
else:
    render_subject(subject_id)
