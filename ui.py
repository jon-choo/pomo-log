"""Small shared UI helpers."""

import html
from typing import Callable

import streamlit as st


def show_flash() -> None:
    message = st.session_state.pop("flash", None)
    if message:
        st.markdown(f'<p class="flash">{html.escape(message)}</p>', unsafe_allow_html=True)


def run_action(action: Callable[[], object], success_message: str) -> None:
    try:
        action()
    except ValueError as error:
        st.error(str(error))
        return
    st.session_state["flash"] = success_message
    st.rerun()
