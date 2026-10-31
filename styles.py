"""Shared page styles."""

import streamlit as st

FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2"
    "?family=Hanken+Grotesk:wght@200;300;400;500;600&display=swap');"
)

CSS = FONT_IMPORT + """
:root {
  --paper: #F4F6F8;
  --ink: #1B2733;
  --muted: #4F5B67;
  --rule: #C7D0D9;
  --tide: #2F6B88;
  --tide-soft: #B7C8D3;
}

.stApp, .stApp *:not([data-testid="stIconMaterial"]) {
  font-family: "Hanken Grotesk", system-ui, -apple-system, "Segoe UI", sans-serif !important;
}
.stApp { font-variant-numeric: tabular-nums; color: var(--ink); }

[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stToolbar"], footer { display: none; }

.block-container { max-width: 72rem; padding: 2rem 2rem 5rem; }

.stApp h1 { font-size: 2rem; font-weight: 300; line-height: 1.15; letter-spacing: -0.01em; padding: 0 0 0.5rem; }
.stApp h2, .stApp h3 { font-size: 1.25rem; font-weight: 500; line-height: 1.3; }
.stApp h2 { margin-top: 0.75rem; }

.muted { color: var(--muted); font-size: 0.9375rem; }
.caption {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}
.flash { color: var(--tide); font-size: 0.9375rem; margin: 0 0 1rem; }

/* Navigation */
.st-key-topnav { border-bottom: 1px solid var(--rule); padding-bottom: 0.75rem; margin-bottom: 2rem; }
.wordmark { font-weight: 600; letter-spacing: 0.02em; }
.st-key-topnav a {
  background: transparent !important;
  color: var(--muted);
  text-decoration: none;
  font-size: 0.9375rem;
  padding: 0.25rem 0;
}
.st-key-topnav a:hover { color: var(--ink); }
.nav-current { font-size: 0.9375rem; padding: 0.25rem 0; border-bottom: 1px solid var(--ink); }

.st-key-runline { border-bottom: 1px solid var(--rule); padding-bottom: 0.75rem; margin: -1rem 0 2rem; }
.runline-text { font-size: 0.9375rem; }
.runline-text b { font-weight: 500; margin-right: 0.75rem; }
.runline-time { font-weight: 500; }

/* Buttons: text actions, with one outlined primary */
[data-testid^="stBaseButton-secondary"] {
  background: transparent;
  border: 0;
  border-bottom: 1px solid var(--ink);
  border-radius: 0;
  min-height: 0;
  padding: 0.1rem 0;
  color: var(--ink);
  font-weight: 500;
}
[data-testid^="stBaseButton-secondary"]:hover { background: transparent; color: var(--tide); border-bottom-color: var(--tide); }
[data-testid^="stBaseButton-secondary"]:disabled { color: var(--muted); border-bottom-color: var(--rule); }
[data-testid^="stBaseButton-primary"] {
  background: transparent;
  color: var(--ink);
  border: 1px solid var(--ink);
  border-radius: 2px;
}
[data-testid^="stBaseButton-primary"]:hover { background: var(--ink); color: var(--paper); border-color: var(--ink); }
[data-testid^="stBaseButton-secondary"] p, [data-testid^="stBaseButton-primary"] p { color: inherit; }

[data-testid="stAlert"] { background: transparent; border: 1px solid var(--rule); border-radius: 2px; color: var(--ink); }

/* Mode tabs: a horizontal radio shown as text */
[data-testid="stRadio"] [role="radiogroup"] { gap: 1.75rem; }
[data-testid="stRadio"] label { padding: 0; }
[data-testid="stRadio"] label > div:first-child { display: none; }
[data-testid="stRadio"] label p { color: var(--muted); border-bottom: 1px solid transparent; padding-bottom: 0.1rem; }
[data-testid="stRadio"] label:has(input:checked) p { color: var(--ink); font-weight: 500; border-bottom-color: var(--ink); }

/* Focus */
.st-key-focus {
  align-items: center;
  justify-content: center;
  min-height: 78vh;
  gap: 1.75rem;
  text-align: center;
}
.st-key-focus .stButton { display: flex; justify-content: center; }
.focus-subject { display: block; font-size: 1.25rem; font-weight: 500; }
.focus-phase { display: block; margin-top: 0.35rem; }
.numeral {
  font-size: clamp(6rem, 18vw, 13rem);
  font-weight: 200;
  line-height: 1;
  white-space: nowrap;
  text-align: center;
}
.numeral .d { display: inline-block; width: 0.58em; text-align: center; }
.numeral .c { display: inline-block; width: 0.3em; text-align: center; transform: translateY(-0.05em); }
.tide-wrap { width: min(100%, 42rem); margin: 0 auto; }
.tide { width: 100%; height: auto; display: block; }
.tide-labels { display: flex; justify-content: space-between; padding: 0.35rem 1.6% 0; }
.tide-labels span {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  white-space: nowrap;
}
.focus-rule { width: min(100%, 42rem); border: 0; border-top: 1px solid var(--rule); margin: 0 auto; }

/* Facts and goal */
.facts { display: flex; flex-wrap: wrap; gap: 0.5rem 3.5rem; }
.facts .value { display: block; font-size: 1.25rem; font-weight: 500; margin-top: 0.15rem; }
.goal-rule { height: 2px; background: var(--rule); margin: 0.9rem 0 1.5rem; }
.goal-rule span { display: block; height: 100%; background: var(--tide); }

/* Ruled rows and tables */
table.ruled { width: 100%; border-collapse: collapse; }
table.ruled th, table.ruled td {
  text-align: left;
  padding: 0.6rem 0.75rem 0.6rem 0;
  border-bottom: 1px solid var(--rule);
  font-size: 0.9375rem;
}
table.ruled th {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}
table.ruled .num { text-align: right; }

[class*="st-key-row-"] { border-bottom: 1px solid var(--rule); padding: 0.5rem 0; }
.subject { display: block; font-weight: 500; }
.sub { display: block; font-size: 0.75rem; color: var(--muted); }
.num { text-align: right; display: block; }

/* Manage page rows */
.board-head {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}
.row-note { color: var(--muted); font-size: 0.9375rem; padding-top: 0.55rem; }
[data-testid="stForm"] { border-radius: 0; border-bottom: 1px solid var(--rule); padding: 0.35rem 0; }

.st-key-topnav [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 1.75rem; }
.st-key-topnav [data-testid="stColumn"] { flex: 0 0 auto !important; width: auto !important; min-width: 0 !important; }

@media (max-width: 640px) {
  [data-testid="stHorizontalBlock"]:has(.board-head) { display: none; }
  .block-container { padding: 1.25rem 1rem 4rem; }
  [class*="st-key-row-"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0.75rem; }
  [class*="st-key-row-"] [data-testid="stColumn"] { flex: 0 0 auto !important; width: auto !important; min-width: 0 !important; }
  [class*="st-key-row-"] [data-testid="stColumn"]:first-child { flex: 1 1 0 !important; }
}

:focus-visible { outline: 2px solid var(--tide); outline-offset: 2px; }
::selection { background: #C9D6DF; color: var(--ink); }
* { scrollbar-color: #AEB9C4 transparent; }
"""

NARROW_CSS = """
.block-container { max-width: 62rem; }
"""


def inject_styles() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def narrow_page() -> None:
    """Cap content width."""
    st.markdown(f"<style>{NARROW_CSS}</style>", unsafe_allow_html=True)
