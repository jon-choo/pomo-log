"""Small shared UI helpers."""

import html

import streamlit as st


def show_flash() -> None:
    message = st.session_state.pop("flash", None)
    if message:
        st.success(message)


def strip(cells: list[tuple]) -> str:
    """Labelled segments in one row. A third item of True marks a cell as live."""
    parts = []
    for label, value, *flags in cells:
        live = ' <span class="chip">Live</span>' if flags and flags[0] else ""
        parts.append(
            f'<div class="cell"><div class="label">{html.escape(label)}</div>'
            f'<div class="value">{html.escape(value)}{live}</div></div>'
        )
    return f'<div class="strip">{"".join(parts)}</div>'
