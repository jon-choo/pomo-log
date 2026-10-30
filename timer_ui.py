"""Start and stop controls with a live timer display."""

import streamlit as st

import db
import timer
from formatting import format_clock, format_duration
from ui import strip

PHASE_LABELS = {"free": "Free", "work": "Work", "break": "Break"}


def timer_controls(subject_id: int) -> None:
    if timer.get_active_timer() is None:
        start_controls(subject_id)
    else:
        running_panel()


def start_controls(subject_id: int) -> None:
    work, rest = timer.get_pomodoro_lengths()
    mode = st.radio("Mode", ["Pomodoro", "Free"], horizontal=True, key="timer-mode")
    note = f"{work} min work, {rest} min break, repeating" if mode == "Pomodoro" else "Counts up until you stop"
    st.markdown(f'<p class="muted">{note}</p>', unsafe_allow_html=True)
    if st.button("Start", type="primary", key="start-timer"):
        try:
            timer.start_timer(subject_id, "pomodoro" if mode == "Pomodoro" else "freeform")
        except ValueError as error:
            st.error(str(error))
            return
        st.rerun()


@st.fragment(run_every="1s")
def running_panel() -> None:
    state = timer.get_active_timer()
    if state is None:
        st.rerun()
    if timer.tick():
        st.toast("Work interval logged")

    info = timer.phase_info(state)
    subject = db.get_subject(state.subject_id)
    cells = [("Tracking", subject["name"]), ("Phase", PHASE_LABELS[info["phase"]], True)]
    if info["phase_remaining_seconds"] is not None:
        cells.append(("Remaining", format_clock(info["phase_remaining_seconds"])))
    cells.append(("Elapsed", format_clock(info["elapsed_seconds"])))
    st.markdown(strip(cells), unsafe_allow_html=True)

    if st.button("Stop", type="primary", key="stop-timer"):
        ids = timer.stop_timer()
        logged = sum(db.get_session(i)["duration_seconds"] for i in ids)
        if ids:
            st.session_state["flash"] = f"Logged {format_duration(logged)} to {subject['name']}."
        else:
            st.session_state["flash"] = "Timer stopped. Nothing to log."
        st.rerun()
