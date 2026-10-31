"""Small shared UI helpers."""

import html

import streamlit as st


def show_flash() -> None:
    message = st.session_state.pop("flash", None)
    if message:
        st.markdown(f'<p class="flash">{html.escape(message)}</p>', unsafe_allow_html=True)
