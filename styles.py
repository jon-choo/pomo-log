"""Shared page styles."""

import streamlit as st

CSS = """
:root {
  --ink: #0F172A;
  --muted: #4B5563;
  --panel: #FFFFFF;
  --ground: #EEF0F3;
  --rule: #D5D9E0;
  --alert: #FFB000;
}

.stApp, .stApp button, .stApp input, .stApp select, .stApp textarea {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
  font-variant-numeric: tabular-nums;
}

.stApp h1 { font-size: 1.75rem; font-weight: 650; line-height: 1.2; letter-spacing: -0.01em; }
.stApp h2, .stApp h3 { font-size: 1.25rem; font-weight: 650; line-height: 1.3; }
.stApp h2 { margin-top: 2rem; }

.block-container { padding-top: 2.5rem; }

.board-head {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
}
.muted { color: var(--muted); font-size: 0.875rem; }
.row-note { color: var(--muted); font-size: 0.875rem; padding-top: 0.55rem; }

[data-testid="stForm"] {
  border-radius: 0;
  border-bottom: 1px solid var(--rule);
  padding: 0.35rem 0;
}

@media (max-width: 640px) {
  [data-testid="stHorizontalBlock"]:has(.board-head) { display: none; }
}

[data-testid="stSidebar"] { border-right: 1px solid var(--rule); }

:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
::selection { background: #C9D0DB; color: var(--ink); }
* { scrollbar-color: #AEB6C2 transparent; }
"""

NARROW_CSS = """
.block-container { max-width: 62rem; }
"""


def inject_styles() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def narrow_page() -> None:
    """Cap content width."""
    st.markdown(f"<style>{NARROW_CSS}</style>", unsafe_allow_html=True)
