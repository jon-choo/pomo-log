"""Focus screen and the running line shown on other pages."""

from __future__ import annotations

import base64
import html
import math

import streamlit as st

import db
import timer
from formatting import format_clock, format_duration

TIDE_WIDTH = 640
TIDE_HEIGHT = 110
TIDE_PAD = 10
TIDE_STEPS = 160
PHASE_WORDS = {"free": "Free", "work": "Work", "break": "Break"}
INK = "#1B2733"
RULE = "#C7D0D9"
TIDE = "#2F6B88"
TIDE_SOFT = "#B7C8D3"


def in_focus(active: timer.TimerState | None) -> bool:
    return active is not None and not st.session_state.get("focus_left", False)


def numeral_html(seconds: int) -> str:
    cells = "".join(
        '<span class="c">:</span>' if char == ":" else f'<span class="d">{char}</span>'
        for char in format_clock(seconds)
    )
    return f'<div class="numeral">{cells}</div>'


def tide_level(second: float, work: int, rest: int) -> float:
    if second <= work:
        return (1 - math.cos(math.pi * second / work)) / 2
    return (1 + math.cos(math.pi * (second - work) / rest)) / 2


def tide_svg(state: timer.TimerState, elapsed: int) -> str:
    work, rest = state.work_seconds, state.break_seconds
    cycle = work + rest
    position = elapsed % cycle
    span = TIDE_WIDTH - 2 * TIDE_PAD
    base = TIDE_HEIGHT - TIDE_PAD

    def point(second: float) -> tuple[float, float]:
        x = TIDE_PAD + span * second / cycle
        y = base - tide_level(second, work, rest) * (TIDE_HEIGHT - 2 * TIDE_PAD)
        return x, y

    def path(start: float, end: float) -> str:
        steps = max(2, int(TIDE_STEPS * (end - start) / cycle))
        points = [point(start + (end - start) * i / steps) for i in range(steps + 1)]
        return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points)

    now_x, now_y = point(position)
    boundary_x = point(work)[0]
    elapsed_path = path(0, position) if position > 0 else f"M{now_x:.1f} {now_y:.1f}"
    stroke = 'fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TIDE_WIDTH} {TIDE_HEIGHT}">'
        f'<line x1="{TIDE_PAD}" y1="{base}" x2="{TIDE_WIDTH - TIDE_PAD}" y2="{base}" stroke="{RULE}"/>'
        f'<line x1="{boundary_x:.1f}" y1="{TIDE_PAD}" x2="{boundary_x:.1f}" y2="{base}" stroke="{RULE}"/>'
        f'<path class="remaining" d="{path(position, cycle)}" {stroke} stroke="{TIDE_SOFT}"/>'
        f'<path class="elapsed" d="{elapsed_path}" {stroke} stroke="{INK}"/>'
        f'<circle cx="{now_x:.1f}" cy="{now_y:.1f}" r="5" fill="{TIDE}"/>'
        f"</svg>"
    )


def tide_html(state: timer.TimerState, elapsed: int) -> str:
    uri = "data:image/svg+xml;base64," + base64.b64encode(tide_svg(state, elapsed).encode()).decode()
    return (
        '<div class="tide-wrap">'
        f'<img class="tide" src="{uri}" alt="Position in the current work and break cycle">'
        '<div class="tide-labels">'
        f"<span>Work {format_clock(state.work_seconds)}</span>"
        f"<span>Break {format_clock(state.break_seconds)}</span>"
        "</div></div>"
    )


def phase_caption(state: timer.TimerState, info: dict) -> str:
    if info["phase"] == "free":
        return "Free, counting up"
    if info["phase"] == "work":
        return f"Work, interval {info['completed_work_intervals'] + 1}"
    return f"Break, after interval {info['completed_work_intervals']}"


def stop_session(subject: dict) -> None:
    ids = timer.stop_timer()
    logged = sum(db.get_session(i)["duration_seconds"] for i in ids)
    if ids:
        st.session_state["flash"] = f"Logged {format_duration(logged)} to {subject['name']}."
    else:
        st.session_state["flash"] = "Timer stopped. Nothing to log."
    st.session_state["focus_left"] = False
    st.rerun()


@st.fragment(run_every="1s")
def focus_screen() -> None:
    state = timer.get_active_timer()
    if state is None:
        st.rerun()
    if timer.tick():
        st.toast("Work interval logged")

    info = timer.phase_info(state)
    subject = db.get_subject(state.subject_id)
    seconds = info["phase_remaining_seconds"]
    if seconds is None:
        seconds = info["elapsed_seconds"]

    with st.container(key="focus"):
        st.html(
            f'<div><span class="focus-subject">{html.escape(subject["name"])}</span>'
            f'<span class="caption focus-phase">{html.escape(phase_caption(state, info))}</span></div>'
        )
        st.html(numeral_html(seconds))
        if state.mode == "pomodoro":
            st.html(tide_html(state, info["elapsed_seconds"]))
        else:
            st.html('<hr class="focus-rule">')
        if st.button("Stop", key="stop-timer"):
            stop_session(subject)
        if st.button("Leave focus", key="leave-focus"):
            st.session_state["focus_left"] = True
            st.rerun()


@st.fragment(run_every="1s")
def running_line() -> None:
    state = timer.get_active_timer()
    if state is None:
        st.rerun()
    timer.tick()

    info = timer.phase_info(state)
    subject = db.get_subject(state.subject_id)
    seconds = info["phase_remaining_seconds"]
    if seconds is None:
        seconds = info["elapsed_seconds"]

    with st.container(key="runline"):
        text_col, action_col = st.columns([5, 2], vertical_alignment="center")
        text_col.html(
            f'<span class="runline-text"><b>{html.escape(subject["name"])}</b>'
            f'{PHASE_WORDS[info["phase"]]} <span class="runline-time">{format_clock(seconds)}</span></span>'
        )
        if action_col.button("Return to focus", key="return-focus"):
            st.session_state["focus_left"] = False
            st.switch_page("views/today.py")
