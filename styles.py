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

.strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
  background: var(--panel);
  border: 1px solid var(--rule);
  border-radius: 12px;
  overflow: hidden;
  margin: 0.5rem 0 1.25rem;
}
.strip .cell {
  padding: 0.75rem 1.25rem;
  min-width: 0;
  box-shadow: 1px 0 0 var(--rule), 0 1px 0 var(--rule);
}
.strip .label {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
}
.strip .value { font-size: 1.25rem; font-weight: 650; }

.chip {
  display: inline-block;
  background: var(--alert);
  color: var(--ink);
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  vertical-align: middle;
}

.banner {
  display: flex;
  align-items: flex-end;
  min-height: 5rem;
  padding: 0.75rem 1rem;
  color: #FFFFFF;
  border-radius: 12px 12px 0 0;
}
.banner-name { font-size: 1.125rem; font-weight: 650; line-height: 1.25; }
.banner-large {
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-end;
  min-height: 8rem;
  border-radius: 12px;
  margin-bottom: 0.75rem;
}
.banner-large .banner-name { font-size: 1.75rem; }
.banner-sub { font-size: 0.875rem; font-weight: 500; }
.card-body { display: flex; flex-direction: column; gap: 0.25rem; padding: 0.75rem 1rem 1rem; }
.card-row { display: flex; justify-content: space-between; align-items: center; min-height: 1.5rem; }
.card-time { font-weight: 650; }
.swatch { display: block; width: 1.5rem; height: 1.5rem; border-radius: 6px; margin-top: 0.5rem; }

table.board {
  width: 100%;
  border-collapse: collapse;
  background: var(--panel);
  border: 1px solid var(--rule);
  margin-top: 0.5rem;
}
table.board th, table.board td {
  text-align: left;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--rule);
  font-size: 0.9375rem;
}
table.board th {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
}
table.board .num { text-align: right; }
table.board tr:last-child td { border-bottom: 0; }

[class*="st-key-subject-card-"] {
  position: relative;
  padding: 0;
  overflow: hidden;
  border-radius: 12px;
  background: var(--panel);
  border: 1px solid var(--rule);
}
[class*="st-key-subject-card-"]:hover { border-color: var(--ink); }
[class*="st-key-subject-card-"]:has(button:focus-visible) { outline: 2px solid var(--ink); outline-offset: 2px; }
[class*="st-key-subject-card-"] [data-testid="stElementContainer"]:has(button) {
  position: absolute;
  inset: 0;
  width: 100% !important;
  height: 100% !important;
  z-index: 2;
}
[class*="st-key-subject-card-"] [data-testid="stButton"] { width: 100%; height: 100%; }
[class*="st-key-subject-card-"] button { width: 100%; height: 100%; opacity: 0; cursor: pointer; }

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
